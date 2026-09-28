# -*- coding: utf-8 -*-
from odoo import fields, models

from .hr_employee import MOOD_SELECTION


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    mood_check_in = fields.Selection(
        MOOD_SELECTION, string='Mood at Check-In', copy=False,
        help="Dominant facial expression read by the kiosk at check-in time.")
    mood_check_in_confidence = fields.Float(
        string='Check-In Mood Confidence', copy=False,
        help="Confidence (0 to 1) reported by the browser's expression model.")
    mood_check_out = fields.Selection(
        MOOD_SELECTION, string='Mood at Check-Out', copy=False)
    mood_check_out_confidence = fields.Float(
        string='Check-Out Mood Confidence', copy=False)
