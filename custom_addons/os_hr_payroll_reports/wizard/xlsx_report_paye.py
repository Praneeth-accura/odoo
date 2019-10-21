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
                                    ('paye3','PAYE T-9A'),('paye4','PAYE T-10')], default='epf')
    year_start = fields.Date('From', default=date.today())
    year_end = fields.Date('To', default=date.today())
    
    @api.onchange('year_start')
    def onchange_year_start(self):
        current_date1 = datetime.strptime(str(self.year_start),'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_month = current_date1.strftime('%-m')
        month = int(current_month)
        year = int(current_year)
        if month == 1 or month == 2 or month == 3:
            self.year_start = current_date1 + relativedelta(year=year-1,month=4,day=1)
            self.year_end = current_date1 + relativedelta(year=year,month=3,day=31)
        else:
            self.year_start = current_date1 + relativedelta(year=year,month=4,day=1)
            self.year_end = current_date1 + relativedelta(year=year+1,month=3,day=31)
        
    def print_xlsx_reports(self,fl):
        if self.report_type == 'paye1':
            fl = self.print_paye1_report()
        elif self.report_type == 'paye2':
            fl = self.print_paye2_report()
        elif self.report_type == 'paye3':
            fl = self.print_paye3_report()
        return super(ReportXlsx, self).print_xlsx_reports(fl)
    
    def print_paye1_report(self):
        current_str_date_to = str(date.today())
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_year = int(current_year)
        year_start = self.year_start
        year_end = self.year_end
        previous_yr = (datetime.strptime(str(year_start),'%Y-%m-%d').date()).strftime('%Y')
        current_yr = (datetime.strptime(str(year_end),'%Y-%m-%d').date()).strftime('%Y')
        
        fl = os.path.join(os.path.dirname(__file__), 'PAYE 94 PART 1 for '+previous_yr+"-"+current_yr+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        bold = workbook.add_format({'bold': True,'border':1})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True,
                                         'bg_color': '#9fa1a3'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy','border':1,'bg_color': '#9fa1a3'})
        border = workbook.add_format({'border':1})
        worksheet.set_column('A:A', 5,border)
        worksheet.set_column('B:B', 30,border)
        worksheet.set_column('C:C', 25,border)
        worksheet.set_column('D:E',10,border)
        worksheet.set_column('F:H', 25,border)
        worksheet.set_row(0, 25)
        worksheet.set_row(2, 50)
        worksheet.set_row(4, 40)
        row = 0
        col = 0
        worksheet.merge_range(row, col+6, row, col+7, "Part 01 of Form No PAYE 94 (1)", font_bold_center)
        
        row += 2
        col = 1
        worksheet.write(row, col, "PAYE Registration No.(TIN)", font_bold_center)
        worksheet.write(row, col+1, self.env.user.company_id.vat, font_bold_center)
        col += 4
        worksheet.write(row, col, "PAYE/GOV/", font_bold_center)
        worksheet.merge_range(row, col+1, row, col+2,"---", font_bold_center)
        
        row += 2
        col = 1
        worksheet.merge_range(row, col, row, col+3, "Range of Annual Gross Remuneration\n LKR", font_bold_center)
        col += 4
        worksheet.write(row, col, "No. of Employees (Count)", font_bold_center)
        worksheet.write(row, col+1, "Total Gross Remuneration\n LKR", font_bold_center)
        worksheet.write(row, col+2, "Tax Deductions LKR", font_bold_center)
        
        row += 1
        col = 1
        worksheet.merge_range(row, col, row, col+2, "( 0 -750,000) Tax not Deducted", font_left)
        worksheet.write(row, col+3, "A", font_center)
        count = self.count_employees('114', 0 ,750000, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 0, 750000, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 0, 750000, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col+3, row+4, col+3, "", font_center)
        worksheet.merge_range(row, col, row, col+1, "0 -750,000", font_left)
        worksheet.write(row, col+2,"i", font_center)
        count = self.count_employees('114', 0 ,750000, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 0, 750000, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 0 , 750000, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+1, "750,001 - 1,250,000", font_left)
        worksheet.write(row, col+2,"ii", font_center)
        count = self.count_employees('114', 750000, 1250000, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 750000, 1250000, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 750000, 1250000, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+1, "1,250,001 - 1,750,000", font_left)
        worksheet.write(row, col+2,"iii", font_center)
        count = self.count_employees('114', 1250000, 1750000, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 1250000,1750000, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 1250000, 1750000, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+1, "1,750,001 - 2,250,000", font_left)
        worksheet.write(row, col+2,"iv", font_center)
        count = self.count_employees('114', 1750000,2250000, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 1750000,2250000, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 1750000, 2250000, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+1, "Above 2,250,000", font_left)
        worksheet.write(row, col+2,"v", font_center)
        count = self.count_employees('114', 2250001, 0, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('114', 2250001, 0, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('114', 2250001, 0, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+2, "Total (i to v)", font_left)
        worksheet.write(row, col+3, "B", font_center)
        worksheet.write_formula(row, col+4, 'SUM(F7:F11)', font_center, "")
        worksheet.write_formula(row, col+5, 'SUM(G7:G11)', font_right, "")
        worksheet.write_formula(row, col+6, 'SUM(H7:H11)', font_right, "")
        
        row += 1
        worksheet.merge_range(row, col, row, col+2, "Employees Under Sec. 117 & 117A", font_left)
        worksheet.write(row, col+3, "C", font_center)
        count = self.count_employees('117', 0, 0, year_start, year_end)
        worksheet.write(row, col+4, count, font_center)
        annual_gross = self.find_total_gross('117', 0, 0, year_start, year_end)
        worksheet.write(row, col+5, annual_gross, font_right)
        tot_tax = self.find_tax_deduction('117', 0, 0, year_start, year_end)
        worksheet.write(row, col+6, tot_tax, font_right)
        
        row += 1
        worksheet.merge_range(row, col, row, col+2, "Total (A+B+C)", font_left)
        worksheet.write(row, col+3, "D", font_center)
        worksheet.write_formula(row, col+4, 'SUM(F6+F12+F13)', font_center, "")
        worksheet.write_formula(row, col+5, 'SUM(G6+G12+G13)', font_right, "")
        worksheet.write_formula(row, col+6, 'SUM(H6+H12+H13)', font_right, "")
        
        workbook.close()
        return fl
    
    def find_annual_gross(self,sec,year_start,year_end):
        domain = [('state','=','done'),('date_from','>=',year_start),('date_to','<=',year_end)]
        domain.append(('employee_id.paye_section','=',sec))
        payslips = self.env['hr.payslip'].search(domain)
        annual_gross = {}
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code == 'GROSS':
                        if payslip.employee_id.id in annual_gross:
                            annual_gross[payslip.employee_id.id] -= line.total
                        else:
                            annual_gross[payslip.employee_id.id] = line.total
                else:
                    if line.code == 'GROSS':
                        if payslip.employee_id.id in annual_gross:
                            annual_gross[payslip.employee_id.id] += line.total
                        else:
                            annual_gross[payslip.employee_id.id] = line.total
        return annual_gross
    
    def find_annual_tax(self,sec,year_start,year_end):
        domain = [('state','=','done'),('date_from','>=',year_start),('date_to','<=',year_end)]
        domain.append(('employee_id.paye_section','=',sec))
        payslips = self.env['hr.payslip'].search(domain)
        annual_tax = {}
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code in ['PAYE','PTAX']:
                        if payslip.employee_id.id in annual_tax:
                            annual_tax[payslip.employee_id.id] -= line.total
                        else:
                            annual_tax[payslip.employee_id.id] = line.total
                else:
                    if line.code in ['PAYE','PTAX']:
                        if payslip.employee_id.id in annual_tax:
                            annual_tax[payslip.employee_id.id] += line.total
                        else:
                            annual_tax[payslip.employee_id.id] = line.total
        return annual_tax
        
    def count_employees(self,sec,range1,range2,year_start,year_end):
        annual_gross = self.find_annual_gross(sec, year_start, year_end)
        count = 0
        if sec == '114':
            for key in annual_gross:
                if range1 == 2250001:
                    if annual_gross[key] >= range1:
                        count += 1
                else:
                    if annual_gross[key] > range1 and annual_gross[key] <= range2:
                        count += 1
        else:
            count = len(annual_gross)
        return count
    
    def find_total_gross(self,sec,range1,range2,year_start,year_end):
        annual_gross = self.find_annual_gross(sec, year_start, year_end)
        tot_gross = 0
        if sec == '114':
            for key in annual_gross:
                if range1 == 2250001:
                    if annual_gross[key] >= range1:
                        tot_gross += annual_gross[key]
                else:
                    if annual_gross[key] > range1 and annual_gross[key] <= range2:
                        tot_gross += annual_gross[key]
        else:
            for key in annual_gross:
                    tot_gross += annual_gross[key]   
        return tot_gross
        
    def find_tax_deduction(self,sec,range1,range2,year_start,year_end):
        annual_gross = self.find_annual_gross(sec, year_start, year_end)
        annual_tax = self.find_annual_tax(sec, year_start, year_end)
        tot_tax = 0
        if sec == '114':
            for key in annual_gross:
                if key in annual_tax:
                    if range1 == 2250001:
                        if annual_gross[key] >= range1:
                            tot_tax += annual_tax[key]
                    else:
                        if annual_gross[key] > range1 and annual_gross[key] <= range2:
                            tot_tax += annual_tax[key]
        else:
            for key in annual_gross:
                if key in annual_tax:
                    tot_tax += annual_tax[key]
        return tot_tax
        
        
    def print_paye2_report(self):
        current_str_date_to = str(date.today())
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_year = int(current_year)
        year_start = datetime.strptime(str(self.year_start),'%Y-%m-%d').date()
        year_end = datetime.strptime(str(self.year_end),'%Y-%m-%d').date()
        previous_yr = (datetime.strptime(str(year_start),'%Y-%m-%d').date()).strftime('%Y')
        current_yr = (datetime.strptime(str(year_end),'%Y-%m-%d').date()).strftime('%Y')
        
        fl = os.path.join(os.path.dirname(__file__), 'PAYE 94 PART 2 for '+previous_yr+"-"+current_yr+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        bold = workbook.add_format({'bold': True,'border':1,'bg_color': '#9fa1a3'})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_color_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True,
                                         'bg_color': '#9fa1a3'})
        date_format = workbook.add_format({'num_format': 'mm/yy','border':1,'bg_color': '#9fa1a3'})
        border = workbook.add_format({'border':1})
        worksheet.set_column('A:A', 1,border)
        worksheet.set_column('B:G', 20,border)
        worksheet.set_column('H:L', 25,border)
        worksheet.set_row(2, 25)
        worksheet.set_row(3, 50)
        worksheet.set_row(4, 50)
        
        row = 0
        col = 1
        worksheet.merge_range(row, col, row, col+1, "Part 02 of Form No PAYE 94 (1)", bold)
        
        row += 2
        worksheet.write(row, col, "TIN", font_bold_center)
        worksheet.write(row, col+1, self.env.user.company_id.vat, font_center)
        worksheet.write(row, col+2, "Sub Code", font_bold_center)
        worksheet.write(row, col+3, "-----", font_center)
        worksheet.write(row, col+4, "PAYE/GOV/", font_bold_center)
        worksheet.write(row, col+5, "-----", font_center)
        worksheet.write(row, col+6, "Unit / Branch", font_bold_center)
        worksheet.write(row, col+7, "-----", font_center)
        worksheet.write(row, col+8, "Name of the Employer", font_bold_center)
        worksheet.merge_range(row, col+9, row, col+10, self.env.user.company_id.name, font_center)
        
        row += 1
        worksheet.merge_range(row, col, row+2, col, "Y/A:\n"+previous_yr+"/"+current_yr, font_bold_center)
        
        worksheet.merge_range(row, col+1, row+1, col+1, "Exempt\n Remuneration\n (Travelling\n allowance etc.)", font_bold_center)
        worksheet.write(row+2, col+1, "A", font_bold_center)
        
        worksheet.merge_range(row, col+2, row, col+3, "Gross Remuneration Below LKR\n  750,000 or below but liable for\n  P.A.Y.E (During the Y/A)", font_bold_center)
        worksheet.write(row+1, col+2, "Total Gross\n  Remuneration\n LKR", font_bold_center)
        worksheet.write(row+1, col+3, "Tax Deducted\n LKR", font_bold_center)
        worksheet.write(row+2, col+2, "B", font_bold_center)
        worksheet.write(row+2, col+3, "C", font_bold_center)
        
        worksheet.merge_range(row, col+4, row, col+5, "Gross Remuneration Above\n LKR 750,000 (During the Y/A)", font_bold_center)
        worksheet.write(row+1, col+4, "Total Gross\n  Remuneration\n LKR", font_bold_center)
        worksheet.write(row+1, col+5, "Tax Deducted\n LKR", font_bold_center)
        worksheet.write(row+2, col+4, "D", font_bold_center)
        worksheet.write(row+2, col+5, "E", font_bold_center)
        
        worksheet.merge_range(row, col+6, row, col+7, "P.A.Y.E deducted under Sec. 117&117A\n (Tax deducted at 10% or 16%) (During the Y/A)", font_bold_center)
        worksheet.write(row+1, col+6, "Total Gross\n  Remuneration\n LKR", font_bold_center)
        worksheet.write(row+1, col+7, "Tax Deducted\n LKR", font_bold_center)
        worksheet.write(row+2, col+6, "F", font_bold_center)
        worksheet.write(row+2, col+7, "G", font_bold_center)
        
        worksheet.merge_range(row, col+8, row, col+9, "P.A.Y.E deducted under Sec.\n  114,117&117A (During the Y/A)", font_bold_center)
        worksheet.write(row+1, col+8, "Total Gross\n  Remuneration\n LKR", font_bold_center)
        worksheet.write(row+1, col+9, "Tax Deducted\n LKR", font_bold_center)
        worksheet.write(row+2, col+8, "H=B+D+F", font_bold_center)
        worksheet.write(row+2, col+9, "I=C+E+G", font_bold_center)
        
        worksheet.merge_range(row, col+10, row+1, col+10, "Remittances\n  Made (Excluding\n Penalty) LKR", font_bold_center)
        worksheet.write(row+2, col+10, "J", font_bold_center)
        
        row += 3
        col = 1
        year_start2 = datetime.strptime(str(year_start),'%Y-%m-%d').date()
        current_month = int(year_start2.strftime('%-m'))
        current_year2 = int(previous_yr)
        while year_start2 < year_end:
            if current_month == 13:
                current_month = 1
                current_year2 += 1
            month_start = year_start2 + relativedelta(year=current_year2, month=current_month, day=1)
            month_end = year_start2 + relativedelta(year=current_year2, month=current_month, day=31)
            year = month_start.strftime('%Y')
            month = month_start.strftime('%m')
            worksheet.write(row, col, month+"/"+year, date_format)
            excempt_total = self.find_excempt_rules(month_start, month_end)
            worksheet.write(row, col+1, excempt_total, font_right)

            gross_total1 = self.find_total_gross_a('114','A',month_start,month_end)
            worksheet.write(row, col+2, gross_total1, font_right)
            tax_total1 = self.find_total_tax('114','A',month_start,month_end)
            worksheet.write(row, col+3, tax_total1, font_right)

            gross_total2 = self.find_total_gross_a('114','B',month_start,month_end)
            worksheet.write(row, col+4, gross_total2, font_right)
            tax_total2 = self.find_total_tax('114','B',month_start,month_end)
            worksheet.write(row, col+5, tax_total2, font_right)

            gross_total3 = self.find_total_gross_a('117','A',month_start,month_end)
            worksheet.write(row, col+6, gross_total3, font_right)
            tax_total3 = self.find_total_tax('117','A',month_start,month_end)
            worksheet.write(row, col+7, tax_total3, font_right)

            gross_total_sum = gross_total1 + gross_total2 + gross_total3
            worksheet.write(row, col+8, gross_total_sum, font_right)
            tax_total_sum = tax_total1 + tax_total2 + tax_total3
            worksheet.write(row, col+9, tax_total_sum, font_right)

            year_start2 += relativedelta(year=current_year2, month=current_month, day=31)
            current_month += 1
            row += 1

        workbook.close()
        return fl
    
    def find_payslips_period(self,date_from,date_to):
        payslips = self.env['hr.payslip'].search([('state','=','done'),('date_from','=',date_from),('date_to','=',date_to)])
        return payslips

    def find_excempt_rules(self,date_from,date_to):
        payslips = self.find_payslips_period(date_from, date_to)
        excempt_total = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.salary_rule_id.excempt_remuneration == True:
                        excempt_total -= line.total
                else:
                    if line.salary_rule_id.excempt_remuneration == True:
                        excempt_total += line.total
        return excempt_total

    def find_total_gross_a(self,sec,ranges,date_from,date_to):
        domain = [('state','=','done'),('date_from','=',date_from),('date_to','=',date_to)]
        annual_gross = self.find_annual_gross(sec,date_from,date_to)
        employees = []
        if sec == '114':
            if ranges == 'A':
                for key in annual_gross:
                    if annual_gross[key] <= 750000:
                        employees.append(key)
                domain.append(('employee_id','in',employees))
            else:
                for key in annual_gross:
                    if annual_gross[key] > 750000:
                        employees.append(key)
                domain.append(('employee_id','in',employees))
        else:
            for key in annual_gross:
                employees.append(key)
            domain.append(('employee_id','in',employees))

        payslips = self.env['hr.payslip'].search(domain)
        tot_gross = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code == 'GROSS':
                        tot_gross -= line.total
                else:
                    if line.code == 'GROSS':
                        tot_gross += line.total    
        return tot_gross

    def find_total_tax(self,sec,ranges,date_from,date_to):
        domain = [('state','=','done'),('date_from','=',date_from),('date_to','=',date_to)]
        annual_gross = self.find_annual_gross(sec,date_from,date_to)
        employees = []
        if sec == '114':
            if ranges == 'A':
                for key in annual_gross:
                    if annual_gross[key] <= 750000:
                        employees.append(key)
                domain.append(('employee_id','in',employees))
            else:
                for key in annual_gross:
                    if annual_gross[key] > 750000:
                        employees.append(key)
                domain.append(('employee_id','in',employees))
        else:
            for key in annual_gross:
                employees.append(key)
            domain.append(('employee_id','in',employees))

        payslips = self.env['hr.payslip'].search(domain)
        tot_tax= 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code in ['PAYE','PTAX']:
                        tot_tax -= line.total
                else:
                    if line.code in ['PAYE','PTAX']:
                        tot_tax += line.total
        return tot_tax
        
    def print_paye3_report(self):
        current_str_date_to = str(self.year_end)
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_year = int(current_year)
        year_start = self.year_start
        year_end = self.year_end
        previous_yr = (datetime.strptime(str(year_start),'%Y-%m-%d').date()).strftime('%Y')
        current_yr = (datetime.strptime(str(year_end),'%Y-%m-%d').date()).strftime('%Y')
        fl = os.path.join(os.path.dirname(__file__), 'PAYE T-9A ('+previous_yr+"-"+current_yr+')('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        bold = workbook.add_format({'bold': True,'border':1,'bg_color': '#9fa1a3'})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_color_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12,
                                         'bg_color': '#9fa1a3'})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'border':1,
                                         'bold': True,
                                         'bg_color': '#9fa1a3'})
        date_format = workbook.add_format({'num_format': 'mm/yy','border':1,'bg_color': '#9fa1a3'})
        border = workbook.add_format({'border':1})
        worksheet.set_column('A:A', 1,border)
        worksheet.set_column('B:B', 15,border)
        worksheet.set_column('C:C', 40,border)
        worksheet.set_column('D:D', 40,border)
        worksheet.set_column('E:M', 25,border)
        worksheet.set_column('N:N', 5,border)
        worksheet.set_column('O:O', 25,border)
        worksheet.set_row(4, 20)
        worksheet.set_row(5, 30)
        worksheet.set_row(6, 50)
        
        row = 1
        col = 1
        worksheet.merge_range(row, col, row, col+2, "SCHEDULE - 01   Form No: PAYE/T-9A", bold)
        row += 1
        worksheet.merge_range(row, col, row+1, col+2, "For Remuneration Other than and Once and for  all\n payments( Terminal Benefits)", bold)
        row += 2
        worksheet.merge_range(row, col, row, col+1, "PAYE Registration No.(TIN)", font_bold_center)
        worksheet.write(row, col+2, self.env.user.company_id.vat, font_center)
        worksheet.write(row, col+3, "Subcode", font_bold_center)
        worksheet.write(row, col+4, "---", font_center)
        worksheet.write(row, col+5, "PAYE/GOV/", font_bold_center)
        worksheet.merge_range(row, col+6, row, col+7, "---", font_center)
        worksheet.merge_range(row, col+8, row, col+9, "Name of the Employer", font_bold_center)
        worksheet.merge_range(row, col+10, row, col+13, self.env.user.company_id.name, font_center)
        
        row += 1
        worksheet.merge_range(row, col, row+2, col, "Serial\n No.of\n PAYE\n Pay\n Sheet", font_bold_center)
        worksheet.merge_range(row, col+1, row+1, col+1, "Name of Employee with initials", font_bold_center)
        worksheet.write(row+2, col+1, "eg. De Silva D C I U", font_bold_center)
        worksheet.merge_range(row, col+2, row+2, col+2, "Designation", font_bold_center)
        worksheet.merge_range(row, col+3, row, col+4, "Period of Employment during\n the Year of Assessment", font_bold_center)
        worksheet.write(row+1, col+3, "From MM/DD/YY\n ................\n eg. 10-18-13", font_bold_center)
        worksheet.write(row+1, col+4, "To MM/DD/YY\n ................\n eg. 10-18-13", font_bold_center)
        worksheet.write(row+2, col+3, "MM/DD/YY", font_bold_center)
        worksheet.write(row+2, col+4, "MM/DD/YY", font_bold_center)
        worksheet.merge_range(row, col+5, row, col+7, "Gross Remuneration as per Pay Sheet/ Director Allowance (Taxable)", font_bold_center)
        worksheet.write(row+1, col+5, "Cash Payments (LKR)", font_bold_center)
        worksheet.write(row+1, col+6, "Non-Cash (LKR)", font_bold_center)
        worksheet.write(row+1, col+7, "Total (LKR)", font_bold_center)
        worksheet.write(row+2, col+5, "0.00", font_bold_center)
        worksheet.write(row+2, col+6, "0.00", font_bold_center)
        worksheet.write(row+2, col+7, "0.00", font_bold_center)
        worksheet.merge_range(row, col+8, row+1, col+8, "Total Tax  Exempt\n Income   (LKR)", font_bold_center)
        worksheet.write(row+2, col+8, "0.00", font_bold_center)
        worksheet.merge_range(row, col+9, row, col+10, "Tax deducted as per PAYE Pay sheet", font_bold_center)
        worksheet.write(row+1, col+9, "Tax deducted under\n Section 114\n (LKR)", font_bold_center)
        worksheet.write(row+2, col+9, "0.00", font_bold_center)
        worksheet.write(row+1, col+10, "Tax deducted under\n Section 117\n and 117A (LKR)", font_bold_center)
        worksheet.write(row+2, col+10, "0.00", font_bold_center)
        worksheet.merge_range(row, col+11, row+1, col+12, "NIC Number", font_bold_center)
        worksheet.write(row+2, col+11, "0.00", font_bold_center)
        worksheet.write(row+2, col+12, "X/V", font_bold_center)
        worksheet.merge_range(row, col+13, row+1, col+13, "Income Tax File No.\n (if any) /  ( If Non-\nCitizen, Passport\n, No.)", font_bold_center)
        worksheet.write(row+2, col+13, "0.00", font_bold_center)
        
        employees = self.env['hr.employee'].search([])
        row += 3
        for employee in employees:
            worksheet.write(row, col, employee.contract_id.member_no, font_color_center)
            worksheet.write(row, col+1, employee.name, font_left)
            worksheet.write(row, col+2, employee.job_id.name, font_left)
            worksheet.write(row, col+3, self.year_start, date_format)
            worksheet.write(row, col+4, self.year_end, date_format)
            cash_remu = self.find_cash_remuneration(employee.id,1)
            worksheet.write(row, col+5, cash_remu, font_right)
            non_cash_remu = self.find_cash_remuneration(employee.id,2)
            worksheet.write(row, col+6, non_cash_remu, font_right)
            worksheet.write(row, col+7, cash_remu + non_cash_remu, font_right)
            tot_excempt = self.find_total_excempt_employee(employee.id)
            worksheet.write(row, col+8, tot_excempt, font_right)
            if employee.paye_section == '114':
                tax_total = self.find_tax_dedudction(employee.id)
                worksheet.write(row, col+9, tax_total, font_right)
                worksheet.write(row, col+10, 0, font_right)
            else:
                worksheet.write(row, col+9, 0, font_right)
                tax_total = self.find_tax_dedudction(employee.id)
                worksheet.write(row, col+10, tax_total, font_right)
            worksheet.write(row, col+11, employee.identification_id, font_color_center)
            worksheet.write(row, col+12, "V", font_color_center)
            worksheet.write(row, col+13, employee.incometax_or_passport, font_color_center)
            row += 1
        
        workbook.close()
        return fl
        
    def find_employee_payslips(self,emp_id):
        domain = [('state','=','done'),('date_from','>=',self.year_start),('date_to','<=',self.year_end)]
        domain.append(('employee_id','=',emp_id))
        payslips = self.env['hr.payslip'].search(domain)
        return payslips
    
    def find_cash_remuneration(self,emp_id,no):
        payslips = self.find_employee_payslips(emp_id)
        cash = non_cash = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code == 'NCA':
                        non_cash -= line.total
                    elif line.code == 'GROSS':
                        cash -= line.total
                else:
                    if line.code == 'NCA':
                        non_cash += line.total
                    elif line.code == 'GROSS':
                        cash += line.total
        if no == 1 :
            return cash - non_cash
        else:
            return non_cash            
    
    def find_total_excempt_employee(self,emp_id):
        payslips = self.find_employee_payslips(emp_id)
        tot_tax_exmp = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.salary_rule_id.excempt_remuneration == True:
                        tot_tax_exmp -= line.total
                else:
                    if line.salary_rule_id.excempt_remuneration == True:
                        tot_tax_exmp += line.total
        return tot_tax_exmp
    
    def find_tax_dedudction(self,emp_id):
        payslips = self.find_employee_payslips(emp_id)
        tot_tax_ded = 0
        for payslip in payslips:
            for line in payslip.line_ids:
                if payslip.credit_note == True:
                    if line.code in ['PAYE','PTAX']:
                        tot_tax_ded -= line.total
                else:
                    if line.code in ['PAYE','PTAX']:
                        tot_tax_ded += line.total
        return tot_tax_ded
    
    
    
        
        