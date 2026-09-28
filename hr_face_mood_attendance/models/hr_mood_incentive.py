# -*- coding: utf-8 -*-
from odoo import fields, models


class HrMoodIncentive(models.Model):
    _name = 'hr.mood.incentive'
    _description = 'Wellbeing Workflow Trigger (Mood Streak)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'trigger_date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, ondelete='cascade',
        tracking=True)
    trigger_date = fields.Date(
        string='Triggered On', required=True, default=fields.Date.today,
        tracking=True)
    streak_days = fields.Integer(string='Consecutive Sad Days', tracking=True)
    leave_id = fields.Many2one(
        'hr.leave', string='Linked Leave', copy=False,
        help="Optional: if HR/the manager decides time off is appropriate, "
             "create the leave yourself (any leave type) and link it here "
             "for traceability. This module does not create or confirm any "
             "leave automatically.")
    incentive_amount = fields.Float(
        string='Suggested Incentive Amount',
        help="Proposed amount for HR/payroll to review - not posted to "
             "payroll automatically.")
    incentive_note = fields.Char(string='Incentive Note')
    state = fields.Selection([
        ('new', 'Needs Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ], string='Status', default='new', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    def action_mark_reviewed(self):
        self.write({'state': 'reviewed'})

    def action_dismiss(self):
        self.write({'state': 'dismissed'})
