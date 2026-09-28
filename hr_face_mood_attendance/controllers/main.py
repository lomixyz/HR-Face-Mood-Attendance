# -*- coding: utf-8 -*-
import json
import logging

import werkzeug.exceptions

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class HrFaceMoodController(http.Controller):

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    @http.route('/hr_face_mood/kiosk', type='http', auth='user')
    def kiosk_page(self, **kw):
        """Shared-device page: recognizes whoever stands in front of the
        camera among consenting, enrolled employees and toggles their
        check-in/check-out, tagging the mood read at that moment.
        The browser session must be logged in as a user with the
        'Mood Attendance Kiosk Device' group (or an HR officer)."""
        if not self._is_kiosk_allowed():
            raise werkzeug.exceptions.NotFound()
        company = request.env.company
        return request.render('hr_face_mood_attendance.kiosk_page', {
            'model_url': company.mood_kiosk_model_url,
        })

    @http.route('/hr_face_mood/enroll_page', type='http', auth='user')
    def enroll_page(self, **kw):
        """Self-service page: an employee enrolls their own face, only
        after ticking consent on their employee record."""
        employee = request.env.user.employee_id
        company = request.env.company
        return request.render('hr_face_mood_attendance.enroll_page', {
            'model_url': company.mood_kiosk_model_url,
            'employee': employee,
        })

    # ------------------------------------------------------------------
    # JSON endpoints
    # ------------------------------------------------------------------

    def _is_kiosk_allowed(self):
        user = request.env.user
        return (
            user.has_group('hr_face_mood_attendance.group_mood_kiosk_user')
            or user.has_group('hr.group_hr_user')
        )

    @http.route('/hr_face_mood/descriptors', type='json', auth='user')
    def get_descriptors(self):
        """Returns face descriptors for consenting, enrolled, active
        employees of the current company - only to a logged-in kiosk
        device or HR officer, never publicly."""
        if not self._is_kiosk_allowed():
            raise AccessError("Not allowed.")
        employees = request.env['hr.employee'].sudo().search([
            ('mood_consent', '=', True),
            ('face_descriptor', '!=', False),
            ('active', '=', True),
            ('company_id', '=', request.env.company.id),
        ])
        result = []
        for employee in employees:
            try:
                descriptor = json.loads(employee.face_descriptor)
            except (ValueError, TypeError):
                continue
            result.append({'id': employee.id, 'name': employee.name, 'descriptor': descriptor})
        return result

    @http.route('/hr_face_mood/enroll', type='json', auth='user')
    def enroll(self, descriptor=None):
        """The logged-in user enrolls their OWN face only - this endpoint
        never accepts an employee_id from the client on purpose."""
        employee = request.env.user.employee_id
        if not employee:
            raise UserError("No employee record is linked to your user account.")
        employee._mood_enroll_face(descriptor)
        return {'success': True}

    @http.route('/hr_face_mood/attendance', type='json', auth='user')
    def mark_attendance(self, employee_id=None, mood=None, confidence=None, match_distance=None):
        if not self._is_kiosk_allowed():
            raise AccessError("Not allowed.")
        if match_distance is not None and float(match_distance) > 0.5:
            return {'success': False, 'error': 'Face not recognized with enough confidence.'}
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'success': False, 'error': 'Unknown employee.'}
        if not employee.mood_consent:
            return {'success': False, 'error': 'Employee has not consented to this workflow.'}
        confidence = float(confidence or 0.0)
        action = employee._mood_attendance_action(mood, confidence)
        return {'success': True, 'action': action, 'employee_name': employee.name}
