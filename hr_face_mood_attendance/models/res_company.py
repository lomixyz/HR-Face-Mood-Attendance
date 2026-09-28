# -*- coding: utf-8 -*-
from odoo import fields, models

DEFAULT_MODEL_URL = "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights"


class ResCompany(models.Model):
    _inherit = 'res.company'

    mood_sad_threshold_days = fields.Integer(
        string='Consecutive Sad Days Threshold', default=20,
        help="Number of consecutive attended days with a dominant 'sad' mood "
             "before the wellbeing workflow (notification / draft leave / "
             "incentive) is triggered for an employee.")
    mood_confidence_threshold = fields.Float(
        string='Mood Confidence Threshold', default=0.55,
        help="Minimum confidence (0 to 1) the browser's expression model must "
             "report before a mood reading counts towards the streak.")
    mood_incentive_amount = fields.Float(
        string='Wellbeing Incentive Amount',
        help="Suggested amount to log on the wellbeing incentive record when "
             "the threshold is hit. This does NOT post anything to payroll "
             "automatically - it is a proposal for HR/payroll to review and "
             "apply manually (e.g. as a payslip input).")
    mood_kiosk_model_url = fields.Char(
        string='Face/Mood Model URL', default=DEFAULT_MODEL_URL,
        help="Base URL the kiosk page loads the face-api.js AI model weights "
             "from. Defaults to a public CDN. For an offline/on-premise "
             "deployment, host the weights yourself (see module README) and "
             "point this at that URL instead.")
