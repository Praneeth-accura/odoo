# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo.tools import misc
import os


class ReportXlsx(models.TransientModel):
    _inherit = 'report.xlsx.wizard'
    
    report_type = fields.Selection([('epf','EPF Contribution'),('etf','ETF Contribution'),
                                    ('etf2','ETF Form II'),('payroll','Payroll Report')], default='payroll')
    month = fields.Date('Date', default=datetime.now().replace(day=1))
    paysheet_type = fields.Selection([('all','All'),('selected','Selected'),('batch','Batch')], default='all')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    batch_id = fields.Many2one('hr.payslip.run', string="Batches")
    previous_batch_id = fields.Many2one('hr.payslip.run', string="Previous Batch")

    def print_xlsx_reports(self,fl):
        if self.report_type == 'payroll':
            fl = self.print_payroll_report()
        return super(ReportXlsx, self).print_xlsx_reports(fl)

    def print_payroll_report(self):
        current_str_date_to = str(self.month)
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_date_from = current_date1 + relativedelta(day=1)
        current_date_to = current_date1 + relativedelta(day=31)
        month = int(current_date1.strftime('%-m'))
        previous_date_from = current_date1 + relativedelta(month=month-1, day=1)
        previous_date_to = current_date1 + relativedelta(month=month-1, day=31)
        current_domain = [('state','=','done')]
        current_domain1 = []
        previous_domain = [('state','=','done')]
        previous_domain1 = []
        current_payslips = previous_payslips = {}
        if self.paysheet_type == 'selected':
            fl = os.path.join(os.path.dirname(__file__), 'Payroll Report ('+self.employee_id.employee_code+')('+str(datetime.today())+')'+'.xlsx')
            current_domain.append(('employee_id','=',self.employee_id.id))
            previous_domain.append(('employee_id','=',self.employee_id.id))
            current_domain.append(('date_from','>=',current_date_from))
            current_domain.append(('date_to','<=',current_date_to))
            previous_domain.append(('date_from','>=',previous_date_from))
            previous_domain.append(('date_to','<=',previous_date_to))
            current_payslips = self.env['hr.payslip'].search(current_domain)
            previous_payslips = self.env['hr.payslip'].search(previous_domain)
            
        elif self.paysheet_type == 'batch':
            fl = os.path.join(os.path.dirname(__file__), 'Payroll Report ('+self.batch_id.name+')('+str(datetime.today())+')'+'.xlsx')
            current_domain1.append(('id','=',self.batch_id.id))
            current_batch = self.env['hr.payslip.run'].search(current_domain1)
            current_payslips = current_batch.slip_ids
            current_str_date_to = str(self.batch_id.date_start)
            current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
            month = int(current_date1.strftime('%-m'))
            current_date_to = current_date1 + relativedelta(day=31)
            previous_date_from = current_date1 + relativedelta(month=month-1, day=1)
            previous_date_to = current_date1 + relativedelta(month=month-1, day=31)
            previous_domain1.append(('date_start','>=',previous_date_from))
            previous_domain1.append(('date_end','<=',previous_date_to))
            previous_batch = self.previous_batch_id
            previous_payslips = previous_batch.slip_ids
            
        else:
            fl = os.path.join(os.path.dirname(__file__), 'Payroll Report (All)'+'('+str(datetime.today())+')'+'.xlsx')
            current_domain.append(('date_from','>=',current_date_from))
            current_domain.append(('date_to','<=',current_date_to))
            previous_domain.append(('date_from','>=',previous_date_from))
            previous_domain.append(('date_to','<=',previous_date_to))
            current_payslips = self.env['hr.payslip'].search(current_domain)
            previous_payslips = self.env['hr.payslip'].search(previous_domain)
            
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        
        bold = workbook.add_format({'bold': True,'border':1})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12})
        font_bold_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'bold': True,
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy','border':1})
        border = workbook.add_format({'border':1})
        worksheet.set_column('A:A', 15,border)
        worksheet.set_column('B:B', 25,border)
        worksheet.set_column('C:C',2,border)
        worksheet.set_column('D:S', 20,border)
        worksheet.set_row(4, 50)
        
        #Pay Sheet For Current Month 
        current_month = current_date1.strftime('%b')
        current_year = current_date1.strftime('%Y')
        
        row = 0
        col = 0
        worksheet.merge_range(row,col,row,col+1, self.env.user.company_id.name, bold)
        row += 1
        worksheet.merge_range(row,col,row,col+1, "PAY SHEET FOR "+current_month+"-"+current_year, bold)
        
        row += 3 
        col = 0
        
        worksheet.write(row, col, "EPF No.", font_bold_center)
        worksheet.write(row, col+1, "NAME", font_bold_center)
        
        row = 3
        col = 3
        rule_dict = {}
        salary_rule = self.env['hr.salary.rule'].search([], order='sequence')
        ind = 1
        for rule in salary_rule:
            worksheet.write(row, col, ind, font_bold_center)
            if rule.code == 'PF':
                worksheet.write(row+1, col, "EPF (8%)", font_bold_center)
            elif len(rule.name) > 18:
                data = (rule.name).split()
                name = '\n'
                for temp in data:
                    name += temp+"\n"
                worksheet.write(row+1, col, name, font_bold_center)
            else:
                worksheet.write(row+1, col, rule.name, font_bold_center)
            if rule.code == 'NET':
                rule_dict[ind] = 'TD'
                worksheet.write(row+1, col, 'Total Deductions', font_bold_center)
                col += 1
                ind += 1
                worksheet.set_column(col,col, 20, border)
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, rule.name, font_bold_center)
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
                worksheet.set_column(col,col, 20, border)
                rule_dict[ind] = 'EPF2'
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, 'EPF (20%)', font_bold_center)
                col += 1
                ind += 1
            else:
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
            worksheet.set_column(col,col, 20, border)
        worksheet.set_column(col,col, 1, border)
        row += 2
        current_tot_rule = {}
        tot_employees = 0
        current_emp_dict = {}
        for payslip in current_payslips:
            current_emp_dict[payslip.employee_id.id] = {}
            tot_ded = 0
            col = 2
            epf1 = epf2 = epf3 = 0
            worksheet.write(row, 0, payslip.employee_id.contract_id.member_no, font_center)
            worksheet.write(row, 1, payslip.employee_id.name, font_left)
            for line in payslip.line_ids:
                if line.code in current_tot_rule:
                    if payslip.credit_note == True:
                        current_tot_rule[line.code] -= line.total
                    else:
                        current_tot_rule[line.code] += line.total
                else:
                    current_tot_rule[line.code] = line.total
                #adding the employee's salary rule values
                if line.code in current_emp_dict[payslip.employee_id.id]:
                    current_emp_dict[payslip.employee_id.id][line.code] -= line.total
                else:
                    current_emp_dict[payslip.employee_id.id][line.code] = line.total

                key = 0
                if line.code in rule_dict.itervalues():
                    key = [key for key, value in rule_dict.iteritems() if value == line.code][0]
                    worksheet.write(row, col+key, line.total, font_right)
                if line.category_id.code == 'DED':
                    if payslip.credit_note == True:
                        tot_ded -= line.total
                    else:
                        tot_ded += line.total
                key = [key for key, value in rule_dict.iteritems() if value == 'TD'][0]
                worksheet.write(row, col+key, tot_ded, font_right)
                key = [key for key, value in rule_dict.iteritems() if value == 'EPF2'][0]
                if line.code == 'PF':
                    if payslip.credit_note == True:
                        epf1 -= line.total
                    else:
                        epf1 += line.total
                if line.code == 'EPF':
                    if payslip.credit_note == True:
                        epf2 -= line.total
                    else:
                        epf2 += line.total
                if line.code == 'PFE':
                    if payslip.credit_note == True:
                        epf3 -= line.total
                    else:
                        epf3 += line.total
                worksheet.write(row, col+key, epf1 + epf2 + epf3, font_right)
            if 'TD' in current_tot_rule:
                current_tot_rule['TD'] += tot_ded
            else:
                current_tot_rule['TD'] = tot_ded
            if 'EPF2' in current_tot_rule:
                current_tot_rule['EPF2'] += (epf1 + epf2 + epf3)
            else:
                current_tot_rule['EPF2'] = (epf1 + epf2 + epf3)
            tot_employees += 1
            row += 1
        row += 1
        col = 0
        worksheet.write(row, col, tot_employees, font_bold_center)
        worksheet.write(row, col+1, "TOTAL", font_bold_center)
        col = 2
        for key1 in current_tot_rule:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            worksheet.write(row, col+key2, current_tot_rule[key1], font_bold_right)
        row += 2
        col = 18
        worksheet.merge_range(row, col, row, col+1, "CHEQUE NO.", font_bold_center)
        worksheet.merge_range(row, col+2, row, col+3, "DATE DUE ON", font_bold_center)
        row += 1
        col = 16
        worksheet.write(row, col, "PAYE", font_bold_center)
        for key in current_tot_rule:
            if key == 'PAYE':
                worksheet.write(row, col+1, current_tot_rule[key], font_right)
        row += 1
        worksheet.write(row, col, "EPF", font_bold_center)
        for key in current_tot_rule:
            if key == 'EPF2':
                worksheet.write(row, col+1, current_tot_rule[key], font_right)
        row += 1
        worksheet.write(row, col, "ETF", font_bold_center)
        for key in current_tot_rule:
            if key == 'ETF':
                worksheet.write(row, col+1, current_tot_rule[key], font_right)
        
        row += 2
        col = 1
        worksheet.merge_range(row, col, row, col+1, "..............................", font_left)
        worksheet.merge_range(row, col+2, row, col+3, "..............................", font_left)
        row += 1
        worksheet.write(row, col, "Prepared by", font_left)
        worksheet.write(row, col+2, "Authorised by", font_left)
        row += 1
        worksheet.write(row, col, date.today(), date_format)
        current_month = current_date1.strftime('%m')
        current_year = current_date1.strftime('%Y')
        worksheet.merge_range(row, col+2, row, col+3, self.env.user.company_id.name +" - "+current_month+"/"+current_year, font_left)
        
        
        #Pay Sheet For Previous Month 
        previous_str_date_to = str(previous_date_from)
        previous_date_1 = datetime.strptime(previous_str_date_to,'%Y-%m-%d').date()
        previous_month = previous_date_1.strftime('%b')
        previous_year = previous_date_1.strftime('%Y')
        
        row += 2
        col = 0
        worksheet.merge_range(row,col,row,col+1, "PAY SHEET FOR "+previous_month+"-"+previous_year, bold)
        
        row += 3 
        col = 0
        
        worksheet.set_row(row, 50)
        worksheet.write(row, col, "EPF No.", font_bold_center)
        worksheet.write(row, col+1, "NAME", font_bold_center)
        
        row -= 1
        col = 3
        rule_dict = {}
        salary_rule = self.env['hr.salary.rule'].search([], order='sequence')
        ind = 1
        for rule in salary_rule:
            worksheet.write(row, col, ind, font_bold_center)
            if rule.code == 'PF':
                worksheet.write(row+1, col, "EPF (8%)", font_bold_center)
            elif len(rule.name) > 18:
                data = (rule.name).split()
                name = '\n'
                for temp in data:
                    name += temp+"\n"
                worksheet.write(row+1, col, name, font_bold_center)
            else:
                worksheet.write(row+1, col, rule.name, font_bold_center)
            if rule.code == 'NET':
                rule_dict[ind] = 'TD'
                worksheet.write(row+1, col, 'Total Deductions', font_bold_center)
                col += 1
                ind += 1
                worksheet.set_column(col,col, 20, border)
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, rule.name, font_bold_center)
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
                worksheet.set_column(col,col, 20, border)
                rule_dict[ind] = 'EPF2'
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, 'EPF (20%)', font_bold_center)
                col += 1
                ind += 1
            else:
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
            worksheet.set_column(col,col, 20, border)
        worksheet.set_column(col,col, 1, border)
        row += 2
        previous_tot_rule = {}
        tot_employees = 0
        previous_emp_dict = {}
        for payslip in previous_payslips:
            previous_emp_dict[payslip.employee_id.id] = {}
            tot_ded = 0
            col = 2
            epf1 = epf2 = epf3 = 0
            worksheet.write(row, 0, payslip.employee_id.contract_id.member_no, font_center)
            worksheet.write(row, 1, payslip.employee_id.name, font_left)
            for line in payslip.line_ids:
                if line.code in previous_tot_rule:
                    if payslip.credit_note == True:
                        previous_tot_rule[line.code] -= line.total
                    else:
                        previous_tot_rule[line.code] += line.total
                else:
                    previous_tot_rule[line.code] = line.total
                if line.code in previous_emp_dict[payslip.employee_id.id]:
                    previous_emp_dict[payslip.employee_id.id][line.code] -= line.total
                else:
                    previous_emp_dict[payslip.employee_id.id][line.code] = line.total
                key = 0
                if line.code in rule_dict.itervalues():
                    key = [key for key, value in rule_dict.iteritems() if value == line.code][0]
                    worksheet.write(row, col+key, line.total, font_right)
                if line.category_id.code == 'DED':
                    if payslip.credit_note == True:
                        tot_ded -= line.total
                    else:
                        tot_ded += line.total
                key = [key for key, value in rule_dict.iteritems() if value == 'TD'][0]
                worksheet.write(row, col+key, tot_ded, font_right)
                key = [key for key, value in rule_dict.iteritems() if value == 'EPF2'][0]
                if line.code == 'PF':
                    if payslip.credit_note == True:
                        epf1 -= line.total
                    else:
                        epf1 += line.total
                if line.code == 'EPF':
                    if payslip.credit_note == True:
                        epf2 -= line.total
                    else:
                        epf2 += line.total
                if line.code == 'PFE':
                    if payslip.credit_note == True:
                        epf3 -= line.total
                    else:
                        epf3 += line.total
                worksheet.write(row, col+key, epf1 + epf2 + epf3, font_right)
            if 'TD' in previous_tot_rule:
                previous_tot_rule['TD'] += tot_ded
            else:
                previous_tot_rule['TD'] = tot_ded
            if 'EPF2' in previous_tot_rule:
                previous_tot_rule['EPF2'] += (epf1 + epf2 + epf3)
            else:
                previous_tot_rule['EPF2'] = (epf1 + epf2 + epf3)
            tot_employees += 1
            row += 1
        row += 1
        col = 0
        worksheet.write(row, col, tot_employees, font_bold_center)
        worksheet.write(row, col+1, "TOTAL", font_bold_center)
        col = 2
        for key1 in previous_tot_rule:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            worksheet.write(row, col+key2, previous_tot_rule[key1], font_bold_right)
            
        #Reconciliation Creation
        current_month = current_date1.strftime('%b')
        current_year = current_date1.strftime('%Y')
        row += 2
        col = 0
        worksheet.merge_range(row,col,row,col+1, self.env.user.company_id.name, bold)
        row += 1    
        worksheet.merge_range(row,col,row,col+1, "RECONCILIATION FOR "+current_month+"-"+current_year, bold)
        
        row += 3 
        col = 0
        
        worksheet.set_row(row, 50)
        worksheet.write(row, col, "EPF No.", font_bold_center)
        worksheet.write(row, col+1, "NAME", font_bold_center)
        
        row -= 1
        col = 3
        rule_dict = {}
        salary_rule = self.env['hr.salary.rule'].search([], order='sequence')
        ind = 1
        column_of_epf20 = 0
        column_of_total_deductions = 0
        for rule in salary_rule:
            worksheet.write(row, col, ind, font_bold_center)
            if rule.code == 'PF':
                worksheet.write(row+1, col, "EPF (8%)", font_bold_center)
            elif len(rule.name) > 18:
                data = (rule.name).split()
                name = '\n'
                for temp in data:
                    name += temp+"\n"
                worksheet.write(row+1, col, name, font_bold_center)
            else:
                worksheet.write(row+1, col, rule.name, font_bold_center)
            if rule.code == 'NET':
                rule_dict[ind] = 'TD'
                column_of_total_deductions = col
                worksheet.write(row+1, col, 'Total Deductions', font_bold_center)
                col += 1
                ind += 1
                worksheet.set_column(col,col, 20, border)
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, rule.name, font_bold_center)
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
                worksheet.set_column(col,col, 20, border)
                rule_dict[ind] = 'EPF2'
                worksheet.write(row, col, ind, font_bold_center)
                worksheet.write(row+1, col, 'EPF (20%)', font_bold_center)
                column_of_epf20 = col
                col += 1
                ind += 1
            else:
                col += 1
                rule_dict[ind] = rule.code 
                ind += 1
            worksheet.set_column(col,col, 20, border)
        worksheet.set_column(col,col, 1, border)
        row += 2
        col = 1
        worksheet.write(row, col, "PAY SHEET FOR "+current_month+"-"+current_year, font_bold_center)
        col = 2
        for key1 in current_tot_rule:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            worksheet.write(row, col+key2, current_tot_rule[key1], font_right)
            
        row += 1
        col = 1
        worksheet.write(row, col, "PAY SHEET FOR "+previous_month+"-"+previous_year, font_bold_center)
        col = 2
        for key1 in previous_tot_rule:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            worksheet.write(row, col+key2, previous_tot_rule[key1], font_right)
        
        row += 2
        col = 2
        differ = 0
        for key1 in previous_tot_rule:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            if key1 in previous_tot_rule:
                differ = current_tot_rule[key1] - previous_tot_rule[key1]
            else:
                differ = current_tot_rule[key1]
            worksheet.write(row, col+key2, differ, font_bold_right)
        
        row += 2
        total_employee_dict = {}
        total_of_every_employee = 0
        total_deduction_of_every_employee = 0
        for key1 in current_emp_dict:
            employee = self.env['hr.employee'].search([('id','=',key1)])
            worksheet.write(row, 0, employee.contract_id.member_no, font_center)
            worksheet.write(row, 1, employee.name, font_left)
            epf_12 = 0
            epf_8 = 0
            previous_month_total_deductions = 0
            current_month_total_deductions = 0
            for key2 in current_emp_dict[key1]:
                key3 = [key for key, value in rule_dict.iteritems() if value == key2][0]
                if key1 in previous_emp_dict and key2 in previous_emp_dict[key1]:
                    rule_obj = self.env['hr.salary.rule'].search([('code', '=', str(key2))])
                    if rule_obj.category_id.code == 'DED':
                        previous_month_total_deductions += previous_emp_dict[key1][key2]
                        current_month_total_deductions += current_emp_dict[key1][key2]
                    if current_emp_dict[key1][key2] - previous_emp_dict[key1][key2] == 0:
                        worksheet.write(row, col+key3, 0, font_right)
                        total_employee_dict[key2] = 0
                    else:
                        total = current_emp_dict[key1][key2] - previous_emp_dict[key1][key2]
                        if key2 == 'PFE':
                            epf_12 = total
                        if key2 == 'EPF':
                            epf_8 = total
                        if key2 in total_employee_dict:
                            total_employee_dict[key2] += total
                        else:
                            total_employee_dict[key2] = total
                        worksheet.write(row, col+key3, total, font_right)
                else:
                    total = current_emp_dict[key1][key2]
                    rule_obj = self.env['hr.salary.rule'].search([('code', '=', str(key2))])
                    if rule_obj.category_id.code == 'DED':
                        current_month_total_deductions += current_emp_dict[key1][key2]
                    if key2 == 'PFE':
                        epf_12 = total
                    if key2 == 'EPF':
                        epf_8 = total
                    if key2 in total_employee_dict:
                        total_employee_dict[key2] += total
                    else:
                        total_employee_dict[key2] = total
                    worksheet.write(row, col+key3, total, font_right)
            if column_of_epf20 > 0:
                total_epf_20 = epf_12 + epf_8
                total_of_every_employee += total_epf_20
                worksheet.write(row, column_of_epf20, total_epf_20, font_right)
            if column_of_total_deductions > 0:
                total_deduction = current_month_total_deductions - previous_month_total_deductions
                total_deduction_of_every_employee += total_deduction
                worksheet.write(row, column_of_total_deductions, total_deduction, font_right)
            row += 1
        col = 0
        worksheet.write(row+1, col+1, "TOTAL", font_bold_center)
        col = 2
        differ = 0
        for key1 in total_employee_dict:
            key2 = [key for key, value in rule_dict.iteritems() if value == key1][0]
            differ = total_employee_dict[key1] 
            worksheet.write(row+1, col+key2, differ, font_bold_right)
        worksheet.write(row+1, column_of_epf20, total_of_every_employee, font_bold_right)
        worksheet.write(row+1, column_of_total_deductions, total_deduction_of_every_employee, font_bold_right)
        workbook.close()
        return fl
        
