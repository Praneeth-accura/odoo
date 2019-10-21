# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
import xlsxwriter
from odoo.tools import misc
import os
from dateutil.relativedelta import relativedelta


class ReportXlsx(models.TransientModel):
    _inherit = 'report.xlsx.wizard'
    
    report_type = fields.Selection([('epf','EPF Contribution'),('etf','ETF Contribution'),
                                    ('etf2','ETF Form II'),('payroll','Payroll Report'),
                                    ('paye1','PAYE 94 PART 1'),('paye2','PAYE 94 PART 2'),
                                    ('paye3','PAYE T-9A'),('paye4','PAYE T-10'),
                                    ('cost','Payroll Cost')], default='cost')
    date_start = fields.Date('From', default=date.today())
    date_end = fields.Date('To', default=date.today())
    
    @api.multi
    def get_all_departments(self):
        dept_dict = {}
        for department in self.env['hr.department'].search([]):
            dept_dict[department.id] = department.name
        return dept_dict
    
    @api.multi
    def get_all_rules(self):
        rule_dict = {}
        rule_id = {}
        provident_rule = {}
        prov_rule_id = {}
        i = j = 0
        for rule in self.env['hr.salary.rule'].search([], order='sequence'):
            if rule.category_id.code == 'EPTF' and rule.code != 'PFS':
                provident_rule[j] = rule.name
                prov_rule_id[j] = rule.id
                j += 1
            elif rule.code not in ['PYS', 'PFS']:
                rule_dict[i] = rule.name
                rule_id[i] = rule.id
                i += 1
        return [rule_dict, rule_id, provident_rule, prov_rule_id]
            
    @api.multi
    def find_payslip_date_range(self, dept):
        domain = [('state', '=', 'done'),
                  ('date_from', '<=', self.date_start),
                  ('date_to', '>=', self.date_end),
                  ('employee_id.department_id', '=', dept)]
        payslips = self.env['hr.payslip'].search(domain)
        return payslips
        
    @api.multi
    def find_cost_by_dept(self, dept, rule):
        payslips = self.find_payslip_date_range(dept)
        rule_amount = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if line.salary_rule_id.id == rule:
                    rule_amount += line.total
        return rule_amount
        
    def print_xlsx_reports(self,fl):
        if self.report_type == 'cost':
            fl = self.print_payroll_cost_report()
        return super(ReportXlsx, self).print_xlsx_reports(fl)
    
    def print_payroll_cost_report(self):
        fl = os.path.join(os.path.dirname(__file__), 'Department wise cost Report('+str(datetime.now())+').xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True})
        font_bold_right = workbook.add_format({'align':'right',
                                         'valign':'right',
                                         'num_format': '#,##0.00',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True})
        bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':15,
                                         'border':1,
                                         'bold': True})
        border = workbook.add_format({'border':1})
        
        worksheet.set_column('B:B', 30, border)
        worksheet.set_row(0, 25)
        worksheet.set_row(1, 20)
        
        rule_dict = self.get_all_rules()
        dept_dict = self.get_all_departments()
        
        worksheet.set_column(2, 2+len(dept_dict), 20,border)
        
        worksheet.merge_range(0,1,0,len(dept_dict)+2, 'Department wise Salary expense Report', bold_center)
        row = 1
        col = 2
        valid_rule1 = valid_rule2 = 0
        dept_tot = {}
        rule_tot1 = {}
        rule_tot2 = {}
        for dept in dept_dict:
            row = 1
            worksheet.write(row,col, dept_dict[dept], font_bold_center)
            row += 1
            col1 = col-1  
            total = 0
            for rule in rule_dict[0]:
                if valid_rule1 == 0:
                    worksheet.write(row,col1, rule_dict[0][rule], font_left)
                amount = self.find_cost_by_dept(dept, rule_dict[1][rule])
                total += amount
                if rule in rule_tot1:
                    rule_tot1[rule] += amount
                else:
                    rule_tot1[rule] = amount
                worksheet.write(row,col1+1, amount, font_right)
                row += 1
            valid_rule1 = 1
            for rule in rule_dict[2]:
                if valid_rule2 == 0:
                    worksheet.write(row,col1, rule_dict[2][rule], font_left)
                amount = self.find_cost_by_dept(dept, rule_dict[3][rule])
                total += amount
                if rule in rule_tot2:
                    rule_tot2[rule] += amount
                else:
                    rule_tot2[rule] = amount
                worksheet.write(row,col1+1, amount, font_right)
                row += 1
            if dept in dept_tot:
                dept_tot[dept] += total
            else:
                dept_tot[dept] = total
            valid_rule2 = 1
            col += 1
        row1 = 1
        worksheet.write(row1, col, 'Total', font_bold_center)
        rule_sum = 0
        for rule in rule_tot1:
            worksheet.write(row1+1, col, rule_tot1[rule], font_bold_right)
            rule_sum += rule_tot1[rule]
            row1 += 1
        for rule in rule_tot2:
            worksheet.write(row1+1, col, rule_tot2[rule], font_bold_right)
            rule_sum += rule_tot2[rule]
            row1 += 1
        col = 1
        worksheet.write(row, 1, 'Total', font_bold_center)
        for dept in dept_tot:
            worksheet.write(row, col+1, dept_tot[dept], font_bold_right)
            col += 1
        worksheet.write(row, col+1, rule_sum, font_bold_right)
        workbook.close()
        return fl
    
    