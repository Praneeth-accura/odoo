# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from datetime import date,datetime
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    paye_section = fields.Selection([('114','114'),('117','117'),('117A','117A')], required=True, default='114')
    income_tax_payer = fields.Selection([('not','Not Eligible'),('citizen','Citizen'),
                                         ('non','Non Citizen')], default='not')
    incometax_or_passport = fields.Char('No')
    
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    paye_tax = fields.Float('PAYE', compute='compute_paye_rule')
    
    def compute_paye_rule(self):
        year_start = datetime.strptime(str(self.date_from),'%Y-%m-%d').date()
        current_yr = int((datetime.strptime(str(year_start),'%Y-%m-%d').date()).strftime('%Y'))
        previous_yr = current_yr
        current_month = int(year_start.strftime('%-m'))
        if current_month in [1,2,3]:
            previous_yr = current_yr - 1
        if current_month == 1:
            current_yr -= 1
            current_month = 12
        elif current_month == 4:
            previous_yr = current_yr - 1
            current_month -= 1
        elif current_month > 4:
            previous_yr = current_yr
            current_month -= 1
        else:
            previous_yr = current_yr - 1
            current_month -= 1
        month_start = year_start + relativedelta(year=previous_yr, month=4, day=1)
        month_end = year_start + relativedelta(year=current_yr, month=current_month, day=31)
        
        domain = [('state','=','done'),('employee_id','=',self.employee_id.id),
                  ('date_from','>=',month_start),('date_to','<=',month_end)]
        payslips = self.search(domain)
        cumulative_profits = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                    if line.code == 'GROSS':
                        if payslip.credit_note == True:
                            cumulative_profits -= line.total
                        else:
                            cumulative_profits += line.total
                        
        domain = [('range_from','<=',cumulative_profits),('range_to','>=',cumulative_profits)]
        range_id = self.env['remuneration.range'].search(domain)
        self.paye_tax = range_id.amount_tax
        
    
