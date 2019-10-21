# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api

class TaxTable(models.Model):
    _name = 'revenue.taxtable'
    
    name = fields.Selection([('M - 0','M - 0'),('M - 0.5','M - 0.5'),('M - 1','M - 1'),('M - 1.5','M - 1.5'),
                             ('M - 2','M - 2'),('M - 2.5','M - 2.5'),('M - 3','M - 3'),('M - 3.5','M - 3.5'),
                             ('M - 4','M - 4'),('M - 4.5','M - 4.5'),('M - 5','M - 5'),('M - 5.5','M - 5.5'),
                             ('M - 6','M - 6'),('M - 6.5','M - 6.5'),('M - 7','M - 7'),('M - 7.5','M - 7.5'),
                             ('M - 8','M - 8'),('M - 8.5','M - 8.5'),('M - 9','M - 9'),('M - 9.5','M - 9.5'),
                             ('M - 10','M - 10'),('M - 10.5','M - 10.5'),('M - 11','M - 11'),
                             ('M - 11.5','M - 11.5'),('M - 12','M - 12')], required=True, string="Name")

    monthly_income_ids = fields.One2many('gross.income', 'gross_income_id', string="Monthly Income ids")
    
class GrossMonthlyIncome(models.Model):
    _name = 'gross.income'
    
    gross_income_id = fields.Many2one('revenue.taxtable', string="Gross Income Id")
    income_from = fields.Float(string="From", required=True)
    income_to = fields.Float(string="To", required=True)
    rate = fields.Float(string="Rate %", required=True)