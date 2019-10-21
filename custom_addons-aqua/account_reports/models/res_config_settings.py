# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days_between_two_followups = fields.Integer(related='company_id.days_between_two_followups', string='Minimum days between two follow-ups')
