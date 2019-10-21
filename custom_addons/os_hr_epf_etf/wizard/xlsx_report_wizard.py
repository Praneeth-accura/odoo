# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import base64
from odoo.tools import misc
import os


class ReportXlsx(models.TransientModel):
    _name = 'report.xlsx.wizard'
    
    report_type = fields.Selection([('epf','EPF Contribution'),('etf','ETF Contribution'),('etf2','ETF Form II')], default='etf')
    date_from = fields.Date('From', default=datetime.now().replace(day=1))
    date_to = fields.Date('To', default=datetime.now().replace(month=+7,day=1))
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Is Printed', default=False)
    
    @api.onchange('date_from')
    def onchange_date(self):
        str_date = str(self.date_from)
        date1 = datetime.strptime(str_date,'%Y-%m-%d').date()
        month = date1.strftime('%-m')
        month = int(month)
        if month == 8:
            month = 1
        elif month == 9:
            month = 2
        elif month == 10:
            month = 3
        elif month == 11:
            month = 4
        elif month == 12:
            month = 5
        else:
            month = month + 5   
        self.date_to = date1 + relativedelta(month=month, day=31)
        
    def print_xlsx_reports(self, fl):
        if self.report_type == 'etf2':
            fl = self.print_etf2_report()
        elif self.report_type == 'etf':
            fl = self.print_etf_report()
        elif self.report_type == 'epf':
            fl = self.print_epf_report()
        my_report_data = open(fl,'rb+') 
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
#         self._cr.execute("TRUNCATE report_export_xlsx CASCADE")
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True
        
        result = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'report.xlsx.wizard',
                'target': 'new',
                'context': ctx,
                'res_id': self.id,
        }
        os.remove(fl)
        return result
    
    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        self.is_printed = False
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.xlsx.wizard',
            'target': 'new',
        }
        return result
    
    def print_etf2_report(self):
        str_date1 = str(self.date_from)
        date1 = datetime.strptime(str_date1,'%Y-%m-%d')
        month1 = date1.strftime('%B')
        year1 = date1.strftime('%Y')
        str_date2 = str(self.date_to)
        date2 = datetime.strptime(str_date2,'%Y-%m-%d')
        month2 = date2.strftime('%B')
        year2 = date2.strftime('%Y')
        fl = os.path.join(os.path.dirname(__file__), 'ETF Form II '+month1+'-'+year1+' to '+month2+'-'+year2+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        
        bold = workbook.add_format({'bold': True,'border':1})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_center = workbook.add_format({'align':'center',
                                           'border':1,
                                         'valign':'vcenter',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                        'border':1,
                                         'valign':'right',
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                                'border':1,
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'bold': True})
        border = workbook.add_format({'border':1})
        worksheet.set_column('Q:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:E', 20,border)
        worksheet.set_column('F:Q', 15,border)
        worksheet.set_row(0, 20)
        worksheet.set_row(1, 20)
        worksheet.set_row(2, 20)
        worksheet.merge_range('A1:B1', "EMPLOYEE'S TRUST FUND", bold)
        worksheet.write('E1', "Form C (3)", bold)
        worksheet.merge_range('A2:B2', "FORM II RETURN", bold)
        worksheet.merge_range('A3:D3', "RETURN FOR THE HALF YEAR - "+month1+'-'+year1+' / '+month2+'-'+year2, bold)
        
        row = 5
        col = 0
        worksheet.merge_range(row,col,row+3,col+1, "Name of Member", font_bold_center)
        worksheet.merge_range(row,col+2,row+3,col+2, "Members No:", font_bold_center)
        worksheet.merge_range(row,col+3,row+3,col+3, "NIC Number", font_bold_center)
        worksheet.merge_range(row,col+4,row+3,col+4, "Total Contribution", font_bold_center)
        worksheet.merge_range(row,col+5,row,col+16, "Total Gross Wages and Contribution", font_bold_center)
        
        col = 5
        row = 6
        row1 = 8
        month_start1 = datetime.strptime(str(self.date_from),'%Y-%m-%d').date()
        month_start2 = datetime.strptime(str(self.date_to),'%Y-%m-%d').date()
        current_month = int(month_start1.strftime('%-m'))
        current_year = int(month_start1.strftime('%Y'))
        emp_dic = {}
        total_dict = {}
        while month_start1 < month_start2:
            if current_month == 13:
                current_month = 1
                current_year += 1
            month_start = month_start1 + relativedelta(year=current_year, month=current_month, day=1)
            month_end = month_start1 + relativedelta(year=current_year, month=current_month, day=31)
            month_start1 += relativedelta(year=current_year, month=current_month, day=31)
            year = month_start1.strftime('%Y')
            month = month_start1.strftime('%m')
            worksheet.merge_range(row,col,row,col+1, month+'/'+year, font_bold_center)
            worksheet.write(row+1,col, "Total Earnings", font_bold_center)
            worksheet.write(row+2,col, "Rs.", font_bold_center)
            worksheet.write(row+1,col+1, "Contributions", font_bold_center)
            worksheet.write(row+2,col+1, "Rs.", font_bold_center)
            etfs = self.find_etf_period(month_start, month_end)
            ind = 1
            for etf in etfs:
                for line in etf.etf_ids:
                    if line.employee_id.id in emp_dic:
                        emp_dic[line.employee_id.id] = emp_dic[line.employee_id.id]
                    else:
                        ind = (len(emp_dic) + 1)
                        emp_dic[line.employee_id.id] = ind
                        ind += 1
                    if line.employee_id.id in total_dict:
                        total_dict[line.employee_id.id] += line.contribution
                    else:
                        total_dict[line.employee_id.id] = line.contribution
            for etf in etfs:
                col1 = 0
                for line in etf.etf_ids:
                    worksheet.merge_range(row1+emp_dic[line.employee_id.id],col1,row1+emp_dic[line.employee_id.id],col1+1, line.employee_id.name, font_left)
                    worksheet.write(row1+emp_dic[line.employee_id.id],col1+2, line.nic_no, font_center)
                    worksheet.write(row1+emp_dic[line.employee_id.id],col1+3, line.member_no, font_center)
                    worksheet.write(row1+emp_dic[line.employee_id.id],col1+4, total_dict[line.employee_id.id], font_right)
                    worksheet.write(row1+emp_dic[line.employee_id.id],col, self.find_total_earning(line.employee_id.id, month_start, month_end), font_right)
                    worksheet.write(row1+emp_dic[line.employee_id.id],col+1, line.contribution, font_right)
            current_month += 1
            col += 2
        workbook.close()
        return fl

    def find_total_earning(self, employee, date_from, date_to):
        tot_earning = 0
        domain = [('state','=','done'),
                  ('employee_id','=', employee),
                  ('date_from','=',date_from),
                  ('date_to','=',date_to)]
        payslips = self.env['hr.payslip'].search(domain)
        for payslip in payslips:
            for line in payslip.line_ids:
                if line.code == 'PFS':
                    tot_earning += line.total
        return tot_earning
        
        
    def find_etf_period(self,date_from,date_to):
        etfs = self.env['employee.etf'].search([('etf_date','>=',date_from),('etf_date','<=',date_to)])
        return etfs
           
    def print_epf_report(self):
        domain = [('epf_date','>=',self.date_from),('epf_date','<',self.date_to)]
        epf_lines = self.env['employee.epf'].search(domain)
        str_date1 = str(self.date_from)
        str_date2 = str(self.date_to)
        date1 = datetime.strptime(str_date1,'%Y-%m-%d')
        date2 = datetime.strptime(str_date2,'%Y-%m-%d')
        month1 = date1.strftime('%b')
        month2 = date2.strftime('%b')
        year1  = date1.strftime('%Y')
        year2  = date2.strftime('%Y')
        
        fl = os.path.join(os.path.dirname(__file__), 'EPF Contribution '+month1+'-'+year1+' to '+month2+'-'+year2+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        bold = workbook.add_format({'bold': True,'border':1,
                                    'font_size':20,
                                    'align':'center',
                                    'valign':'vcenter'})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_center = workbook.add_format({'align':'center',
                                           'border':1,
                                         'valign':'vcenter',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                          'border':1,
                                        'align':'right',
                                         'valign':'right',
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy','border':1})
        worksheet.set_column('O:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:A',20)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:O', 20)
        worksheet.set_row(2, 40)
        row = col =0
        worksheet.merge_range(row, col, row+1, col+14, "EPF Contribution for "+month1+'-'+year1+' to '+month2+'-'+year2, bold)
        row += 2
        col = 0
        worksheet.write(row,col, "NIC Number", font_bold_center)
        worksheet.write(row,col+1, "Surname", font_bold_center)
        worksheet.write(row,col+2, "Initials", font_bold_center)
        worksheet.write(row,col+3, "Member No.", font_bold_center)
        worksheet.write(row,col+4, "Total Contribution", font_bold_center)
        worksheet.write(row,col+5, "Employer \nContribution", font_bold_center)
        worksheet.write(row,col+6, "Member \nContribution", font_bold_center)
        worksheet.write(row,col+7, "Total Earnings", font_bold_center)
        worksheet.write(row,col+8, "Member Status\n E=Extg.  \nN=New V=Vacated", font_bold_center)
        worksheet.write(row,col+9, "Zone", font_bold_center)
        worksheet.write(row,col+10, "Employer Number", font_bold_center)
        worksheet.write(row,col+11, "Contribution Period \n(YYYYMM)", font_bold_center)
        worksheet.write(row,col+12, "Data Submission \nNumber", font_bold_center)
        worksheet.write(row,col+13, "No.of days worked", font_bold_center)
        worksheet.write(row,col+14, "Occupation \nClassification \nGrade", font_bold_center)

        row += 1
        for epf in epf_lines:
            for line in epf.epf_ids:
                worksheet.write(row,col, line.nic_no, font_center)
                worksheet.write(row,col+1, line.employee_id.surnames, font_left)
                worksheet.write(row,col+2, line.employee_id.initial, font_left)
                worksheet.write(row,col+3, line.member_no, font_center)
                worksheet.write(row,col+4, line.total, font_right)
                worksheet.write(row,col+5, line.epf_employer, font_right)
                worksheet.write(row,col+6, line.epf_employee, font_right)
                worksheet.write(row,col+7, line.total_earning, font_right)
                worksheet.write(row,col+8, "E", font_center)
                worksheet.write(row,col+9, line.employee_id.contract_id.zone, font_center)
                worksheet.write(row,col+10, epf.epf_reg_no, font_center)
                str_date = str(epf.epf_date)
                date1 = datetime.strptime(str_date,'%Y-%m-%d')
                month = date1.strftime('%m')
                year  = date1.strftime('%Y')
                worksheet.write(row,col+11, year+"-"+month, date_format)
                worksheet.write(row,col+12, "1", font_center)
                worksheet.write(row,col+13, "30 Days", font_right)
                worksheet.write(row,col+14, line.employee_id.job_id.grade, font_center)
                row += 1
        workbook.close()
        return fl
    
    def print_etf_report(self):
        domain = [('etf_date','>=',self.date_from),('etf_date','<',self.date_to)]
        etf_lines = self.env['employee.etf'].search(domain)
        str_date1 = str(self.date_from)
        str_date2 = str(self.date_to)
        date1 = datetime.strptime(str_date1,'%Y-%m-%d')
        date2 = datetime.strptime(str_date2,'%Y-%m-%d')
        month1 = date1.strftime('%b')
        month2 = date2.strftime('%b')
        year1  = date1.strftime('%Y')
        year2  = date2.strftime('%Y')
        fl = os.path.join(os.path.dirname(__file__), 'ETF Contribution for '+month1+'-'+year1+' to '+month2+'-'+year2+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        bold = workbook.add_format({'bold': True,'align':'center',
                                    'font_size':20,
                                    'valign':'vcenter', 'border':1})
        font_left = workbook.add_format({'align':'left',
                                         'font_size':12,
                                         'border':1})
        font_center = workbook.add_format({'align':'center',
                                           'border':1,
                                         'valign':'vcenter',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                        'border':1,
                                         'valign':'right',
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'border':1,
                                         'font_size':12,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy','border':1})
        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:A',20)
        worksheet.set_column('B:H', 25)
        worksheet.set_row(2, 40)
        row = col =0
        worksheet.merge_range(row, col, row+1, col+7, "ETF Contribution for "+month1+'-'+year1+' to '+month2+'-'+year2, bold)
        row += 2
        col = 0
        worksheet.write(row,col, "NIC/Passport \nNumber", font_bold_center)
        worksheet.write(row,col+1, "Surname", font_bold_center)
        worksheet.write(row,col+2, "Initials", font_bold_center)
        worksheet.write(row,col+3, "Member Number", font_bold_center)
        worksheet.write(row,col+4, "Total Contribution", font_bold_center)
        worksheet.write(row,col+5, "Employer Number", font_bold_center)
        worksheet.write(row,col+6, "Contribution \nFrom Period \n(YYYY/MM/DD)", font_bold_center)
        worksheet.write(row,col+7, "Contribution \nTo Period \n(YYYY/MM/DD)", font_bold_center)

        emp__dict = {}
        etf_reg_no = {}
        for etf in etf_lines:
            for line in etf.etf_ids:
                if line.employee_id.id in etf_reg_no:
                    etf_reg_no[line.employee_id.id] = etf.etf_reg_no
                else:
                    etf_reg_no[line.employee_id.id] = etf.etf_reg_no
                if line.employee_id.id in emp__dict:
                    emp__dict[line.employee_id.id] += line.contribution
                else:
                    emp__dict[line.employee_id.id] = line.contribution
        row += 1
        for key in emp__dict:
            employee_data = self.env['hr.employee'].search([('id','=',key)])
            worksheet.write(row,col, employee_data.identification_id, font_center)
            worksheet.write(row,col+1, employee_data.name, font_left)
            worksheet.write(row,col+2, employee_data.surname, font_left)
            worksheet.write(row,col+3, employee_data.contract_id.member_no, font_center)
            worksheet.write(row,col+4, emp__dict[key], font_right)
            worksheet.write(row,col+5, etf_reg_no[key], font_center)
            worksheet.write(row,col+6, self.date_from, date_format)
            worksheet.write(row,col+7, self.date_to, date_format)
            row += 1
        workbook.close()
        return fl