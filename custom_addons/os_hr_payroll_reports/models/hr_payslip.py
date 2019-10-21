# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
from dateutil.relativedelta import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
 
    @api.multi
    def compute_sheet(self):
        for payslip in self:
            contract = self.env['hr.contract'].search([('id','=',payslip.contract_id.id)])
            rules = {}
            for rule in contract.allowance_rule_ids:
                if rule.code in rules:
                    rules[rule.code] += rule.amount
                else:
                    rules[rule.code] = rule.amount
            for rule in contract.deduction_rule_ids:
                if rule.code in rules:
                    rules[rule.code] += rule.amount
                else:
                    rules[rule.code] = rule.amount
            for inputs in payslip.input_line_ids:
                if inputs.code in rules:
                    inputs.amount = rules[inputs.code]
        return super(HrPayslip,self).compute_sheet()
    
    @api.multi
    def find_range_payslips(self, payslip):
        year_start = datetime.strptime(str(payslip.date_to),'%Y-%m-%d').date()
        current_yr = int((datetime.strptime(str(year_start),'%Y-%m-%d').date()).strftime('%Y'))
        previous_yr = current_yr
        current_month = int(year_start.strftime('%-m'))
        if current_month in [1,2,3]:
            previous_yr = current_yr - 1
        if current_month == 1:
            current_yr -= 1
            current_month = 12
        elif current_month == 4:
            previous_yr = current_yr
            current_month -= 1
        elif current_month > 4:
            previous_yr = current_yr
            current_month -= 1
        else:
            previous_yr = current_yr - 1
            current_month -= 1
        month_start = year_start + relativedelta(year=previous_yr, month=4, day=1)
        domain = [('state','=','done'),('employee_id','=',payslip.employee_id.id),
                  ('date_from','>=',month_start),('date_to','<=',year_start)]
        payslips = self.search(domain)
        return payslips
        
    @api.multi
    def find_sum_of_ytd(self, payslip, rule):
        ytd_amount = 0
        payslip = self.env['hr.payslip'].search([('id','=',payslip)])
        payslips = self.find_range_payslips(payslip)
        for slip in payslips:
            for line in slip.line_ids:
                if line.code == rule:
                    ytd_amount += line.total
        for line in payslip.contract_id.opening_ytd_ids:
            if payslip.date_from >= line.from_date and payslip.date_to <= line.to_date:
                if rule == 'GROSS':
                    ytd_amount += line.ytd_gross
                elif rule == 'NET':
                    ytd_amount += line.ytd_net
                elif rule == 'PF':
                    ytd_amount += (-(line.ytd_emp_epf))
                elif rule == 'EPF':
                    ytd_amount += (-(line.ytd_comp_epf))
                elif rule == 'PAYE':
                    ytd_amount += (-(line.ytd_paye_tax))
                elif rule == 'ETF':
                    ytd_amount += (-(line.ytd_etf))
        if ytd_amount < 0:
            return (ytd_amount * -1)
        else:
            return ytd_amount
        
