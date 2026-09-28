# -*- coding: utf-8 -*-
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MOOD_SELECTION = [
    ('happy', 'Happy'),
    ('sad', 'Sad'),
    ('angry', 'Angry'),
    ('fearful', 'Fearful'),
    ('disgusted', 'Disgusted'),
    ('surprised', 'Surprised'),
    ('neutral', 'Neutral'),
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # -- Consent -----------------------------------------------------
    mood_consent = fields.Boolean(
        string='Consents to Face ID & Mood Detection', tracking=True,
        help="The employee has explicitly agreed to have their face used "
             "for attendance recognition and to have their facial "
             "expression read at check-in/out to estimate mood. No face "
             "data is captured, matched or scored until this is checked.")
    mood_consent_date = fields.Datetime(
        string='Consent Given On', readonly=True, copy=False)

    # -- Face enrollment ----------------------------------------------
    face_descriptor = fields.Text(
        string='Face Descriptor', copy=False, groups='hr.group_hr_user',
        help="Mathematical representation (128-d vector, JSON encoded) of "
             "the employee's face, computed in the browser. This is NOT a "
             "photo and cannot be used to reconstruct one, but it is still "
             "biometric data - treat it as sensitive.")
    face_enrolled_on = fields.Datetime(
        string='Face Enrolled On', readonly=True, copy=False)
    face_is_enrolled = fields.Boolean(
        string='Face Enrolled', compute='_compute_face_is_enrolled', store=True)

    # -- Mood streak tracking ------------------------------------------
    mood_consecutive_sad_days = fields.Integer(
        string='Consecutive Sad Days', readonly=True, copy=False, default=0,
        help="Number of consecutive attended days, ending on the most "
             "recent attendance, whose dominant recorded mood was 'sad'.")
    mood_streak_action_taken = fields.Boolean(
        string='Wellbeing Workflow Already Triggered', readonly=True,
        copy=False, default=False,
        help="Prevents the wellbeing workflow (notification / draft leave / "
             "incentive) from firing again every day once the threshold has "
             "been reached; it resets automatically once the streak breaks.")
    mood_last_action_date = fields.Date(
        string='Wellbeing Workflow Last Triggered On', readonly=True, copy=False)

    @api.depends('face_descriptor')
    def _compute_face_is_enrolled(self):
        for employee in self:
            employee.face_is_enrolled = bool(employee.face_descriptor)

    def write(self, vals):
        if 'mood_consent' in vals:
            for employee in self:
                if vals['mood_consent'] and not employee.mood_consent:
                    vals.setdefault('mood_consent_date', fields.Datetime.now())
                elif not vals['mood_consent'] and employee.mood_consent:
                    # Consent withdrawn: immediately drop the stored
                    # biometric template, don't just hide it.
                    vals.setdefault('face_descriptor', False)
                    vals.setdefault('face_enrolled_on', False)
        return super().write(vals)

    def _mood_enroll_face(self, descriptor):
        """Save a freshly captured face descriptor for this employee.
        Called from the self-service enrollment controller only - always
        for the logged-in user's own employee record."""
        self.ensure_one()
        if not self.mood_consent:
            raise UserError(_(
                "You need to give your consent to face recognition and mood "
                "detection before enrolling your face."))
        if not descriptor or not isinstance(descriptor, list):
            raise UserError(_("No valid face descriptor was captured."))
        self.write({
            'face_descriptor': json.dumps(descriptor),
            'face_enrolled_on': fields.Datetime.now(),
        })

    def _mood_attendance_action(self, mood, confidence):
        """Toggle check-in/check-out for this employee and stamp the mood
        that was read at that exact moment. Returns 'check_in' or
        'check_out'."""
        self.ensure_one()
        attendance_obj = self.env['hr.attendance'].sudo()
        now = fields.Datetime.now()
        open_attendance = attendance_obj.search([
            ('employee_id', '=', self.id),
            ('check_out', '=', False),
        ], limit=1)
        if open_attendance:
            open_attendance.write({
                'check_out': now,
                'mood_check_out': mood,
                'mood_check_out_confidence': confidence,
            })
            return 'check_out'
        attendance_obj.create({
            'employee_id': self.id,
            'check_in': now,
            'mood_check_in': mood,
            'mood_check_in_confidence': confidence,
        })
        return 'check_in'

    def _cron_check_mood_streaks(self, lookback_days=60):
        """Daily job: recompute each consenting employee's consecutive
        'sad' day streak and trigger the wellbeing workflow once it
        crosses the configured threshold."""
        employees = self.search([('mood_consent', '=', True), ('active', '=', True)])
        for employee in employees:
            employee._mood_recompute_streak(lookback_days=lookback_days)

    def _mood_recompute_streak(self, lookback_days=60):
        self.ensure_one()
        company = self.company_id or self.env.company
        threshold = company.mood_sad_threshold_days or 20
        confidence_min = company.mood_confidence_threshold or 0.55

        from datetime import timedelta
        since_dt = fields.Datetime.now() - timedelta(days=lookback_days)

        attendances = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', since_dt),
        ], order='check_in desc')

        # Group by calendar date, a day counts as "sad" if any check-in or
        # check-out that day was dominantly sad above the confidence floor.
        day_is_sad = {}
        day_order = []
        for att in attendances:
            day = fields.Datetime.context_timestamp(self, att.check_in).date()
            if day not in day_is_sad:
                day_is_sad[day] = False
                day_order.append(day)
            sad_hit = (
                (att.mood_check_in == 'sad' and att.mood_check_in_confidence >= confidence_min)
                or (att.mood_check_out == 'sad' and att.mood_check_out_confidence >= confidence_min)
            )
            if sad_hit:
                day_is_sad[day] = True

        day_order.sort(reverse=True)
        streak = 0
        for day in day_order:
            if day_is_sad.get(day):
                streak += 1
            else:
                break

        vals = {'mood_consecutive_sad_days': streak}
        if streak < threshold:
            vals['mood_streak_action_taken'] = False
            self.write(vals)
            return

        self.write(vals)
        if not self.mood_streak_action_taken:
            self._mood_trigger_wellbeing_workflow(streak)
            self.write({
                'mood_streak_action_taken': True,
                'mood_last_action_date': fields.Date.today(),
            })

    def _mood_trigger_wellbeing_workflow(self, streak):
        """Human-in-the-loop wellbeing workflow: notify HR/manager, propose
        a draft leave request, and log a proposed incentive. Nothing here
        is auto-approved - everything lands as a draft/activity for a
        person to review."""
        self.ensure_one()
        company = self.company_id or self.env.company
        _logger.info(
            "Mood wellbeing workflow triggered for employee %s after %s "
            "consecutive sad days.", self.name, streak)

        leave = self.env['hr.leave']
        if company.mood_leave_type_id:
            try:
                leave = self.env['hr.leave'].sudo().create({
                    'employee_id': self.id,
                    'holiday_status_id': company.mood_leave_type_id.id,
                    'request_date_from': fields.Date.today(),
                    'request_date_to': fields.Date.today(),
                    'name': _("Wellbeing support - suggested after %s consecutive "
                              "days of low mood. Please review with the "
                              "employee before confirming.") % streak,
                })
            except Exception:
                _logger.exception(
                    "Could not auto-create a draft wellbeing leave for %s", self.name)

        incentive = self.env['hr.mood.incentive'].sudo().create({
            'employee_id': self.id,
            'trigger_date': fields.Date.today(),
            'streak_days': streak,
            'leave_id': leave.id if leave else False,
            'incentive_amount': company.mood_incentive_amount,
            'company_id': company.id,
        })

        # Notify HR officers and the employee's manager - a person decides
        # what happens next, this module never acts unattended on pay or
        # time off.
        recipients = self.env['res.users'].sudo().search([
            ('groups_id', 'in', [self.env.ref('hr.group_hr_user').id]),
        ])
        if self.parent_id and self.parent_id.user_id:
            recipients |= self.parent_id.user_id

        note = _(
            "%(name)s has had a dominantly low/sad mood at check-in or "
            "check-out for %(streak)s consecutive attended days.\n"
            "Please check in with them. A draft wellbeing leave %(leave)s "
            "and a suggested incentive have been prepared for your review; "
            "nothing has been confirmed automatically."
        ) % {
            'name': self.name,
            'streak': streak,
            'leave': leave.display_name if leave else _("(not created - no "
                                                          "wellbeing leave type configured)"),
        }
        for user in recipients:
            incentive.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Wellbeing check-in needed: %s", self.name),
                note=note,
                user_id=user.id,
            )
        if recipients:
            incentive.message_post(body=note, partner_ids=recipients.mapped('partner_id.id'))
