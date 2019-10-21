# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models

class Contract(models.Model):
    _inherit = "hr.contract"

    payment_method = fields.Many2one('payment.method', string='Payment Method')
    epf = fields.Boolean(string='EPF')
    etf = fields.Boolean(string='ETF')
    ot_liable = fields.Boolean(string='OT Liable')
    pay_attendance = fields.Boolean(string='Pay Attendance')
   
   
class PaymentMethod(models.Model):
    _name='payment.method'
    
    name = fields.Char(string='Name', required=True)