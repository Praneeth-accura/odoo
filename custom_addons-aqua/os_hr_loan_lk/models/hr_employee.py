# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models

class Employee(models.Model):
    _inherit = 'hr.employee'

    
    @api.one
    def compute_loan_counts(self):
        total_loans = self.env['loan.details'].search([('employee_id','=',self.id),('state','=','approve')])
        total = 0
        for loan in total_loans:
            total += loan.balance_amount
        self.total_loan_amount = round(total,2)
        self.total_loans = len(total_loans)
    
    total_loans = fields.Integer(string='Loans', compute='compute_loan_counts')
    total_loan_amount = fields.Float(string='Balance', compute='compute_loan_counts')
    
    @api.multi
    def action_view_loans(self):
        loans = self.env['loan.details'].search([('employee_id','=',self.id)])
        action = self.env.ref('os_hr_loan_lk.open_employee_loan_details').read()[0]
        if len(loans) > 1:
            action['domain'] = [('id', 'in', loans.ids)]
        elif len(loans) == 1:
            action['views'] = [(self.env.ref('os_hr_loan_lk.employee_loan_details_form_view').id, 'form')]
            action['res_id'] = loans.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    