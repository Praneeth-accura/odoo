# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime

class LoanPayment(models.TransientModel):
    _name = 'loan.payment'
    _rec_name = 'employee_id'
        
    employee_id = fields.Many2one('hr.employee', string="Employee",)
    employee_code = fields.Char(string="Employee Code")
    department_id = fields.Many2one('hr.department', string="Department")
    job_id = fields.Many2one('hr.job', string="Job Position")
    installment_ids = fields.Many2many('loan.installment', string="Loans", domain=[('status','!=','paid')])
    
    @api.onchange('employee_id')
    def view_employee_loans(self):
        self.installment_ids = []
        self.employee_code = self.employee_id.employee_code
        self.department_id = self.employee_id.department_id
        self.job_id = self.employee_id.job_id

    @api.multi       
    def process_loan_payment(self):
        for installment in self.installment_ids:
            installment.status = 'paid'
            installment.paid_amount = installment.amount
            installment.paid_date = date.today()
            paid = 0
            total = installment.loan_id.no_of_installments
            for inst in installment.loan_id.installment_ids:
                if inst.status == 'paid':
                    paid += 1
            if paid == total:
                installment.loan_id.closed_on = date.today()
                installment.loan_id.state = 'closed'
    