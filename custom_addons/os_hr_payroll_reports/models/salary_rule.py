# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    excempt_remuneration = fields.Boolean('Excempt', default=False)
    
    