# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models


class PartnerXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.epf_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, epf):
        for record in epf:
            worksheet = workbook.add_worksheet('EPF ('+record.name+')')
            worksheet.set_landscape()
            bold = workbook.add_format({'bold': True})
            large = workbook.add_format({'font_size':20,'bold':True,
                                         'align':'center','valign':'vcenter',})
            font_left = workbook.add_format({'align':'left',
                                             'font_size':12})
            font_center = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':12})
            font_right = workbook.add_format({'num_format': '#,##0.00',
                                            'align':'right',
                                             'valign':'right',
                                             'font_size':12})
            font__bold_right = workbook.add_format({'num_format': '#,##0.00',
                                            'align':'right',
                                             'valign':'right',
                                             'font_size':12,
                                             'bold': True})
            font_bold_center = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':12,
                                             'bold': True})
            border = workbook.add_format({'border':1})
            double_border = workbook.add_format({'top':6,'bold': True,
                                                 'align':'right',
                                                 'valign':'vright',})
            worksheet.set_column('J:XFD', None, None, {'hidden': True})
            worksheet.set_column('A:G', 15)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 1)
            worksheet.merge_range('A2:D2', self.env.user.company_id.name, bold)
            address = ''
            if record.street:
                address += record.street+', '
            if record.street2:
                address += record.street2+',\n'
            if record.city:
                address += record.city+'. '
            if record.state_id:
                address += record.state_id.name+' - '
            if record.zip:
                address += record.zip+', \n'
            if record.country_id:
                address += record.country_id.name
                
            worksheet.merge_range('A3:D5', address, font_left)
            worksheet.merge_range('E2:E3', 'C', large)
            worksheet.merge_range('F3:H3', 'FORM EPF Act. No: 15 of 1958', font_center)
            
            worksheet.merge_range('A7:D7', 'The Superintendent,', font_left)
            worksheet.merge_range('A8:D8', 'Employee Provident Fund, ', font_left)
            worksheet.merge_range('A9:D9', 'Central Bank, ', font_left)
            worksheet.merge_range('A10:D10', 'P.O. Box 1299, ', font_left)
            worksheet.merge_range('A11:D11', 'Colombo 1.', font_left)
            worksheet.merge_range('A12:B12', 'Telephone  ', font_left)
            worksheet.merge_range('A13:B13', 'Fax', font_left)
            worksheet.merge_range('A14:B14', 'E-mail', font_left)
    
            row = 11
            col = 2
            worksheet.merge_range(row,col,row,col+1, record.telephone, font_left)
            worksheet.merge_range(row+1,col,row+1,col+1, record.fax, font_left)
            worksheet.merge_range(row+2,col,row+2,col+1, record.email, font_left)
            
            row = 6
            col = 4
            worksheet.merge_range(row,col,row,col+1, 'EPF Registration No ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.epf_reg_no, font_left)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Contribution for the month of ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.name, font_left)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Contribution  ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.contribution, font_right)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Surcharges ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.surcharges, font_right)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Total Remittance ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.total_remittance, font_right)
            row += 2
            worksheet.merge_range(row,col,row,col+1, 'Cheque No. ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.cheque_no, font_left)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Bank name and Branch Name ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.bank_id.name+'-'+record.branch_id.name, font_left)
            
            row = 15
            col = 0
            worksheet.set_row(row+1, 20)
            worksheet.merge_range(row,col,row+1,col+1, "Employee's Name", font_bold_center)
            worksheet.merge_range(row,col+2,row+1,col+2, "National ID. NO", font_bold_center)
            worksheet.merge_range(row,col+3,row+1,col+3, "Member No.", font_bold_center)
            worksheet.merge_range(row,col+4,row,col+6, "Contributions (Rs.)", font_bold_center)
            worksheet.write(row+1,col+4, "Total", font_bold_center)
            worksheet.write(row+1,col+5, "Employer", font_bold_center)
            worksheet.write(row+1,col+6, "Employee", font_bold_center)
            worksheet.merge_range(row,col+7,row+1,col+7, "(Total Earnings(Rs.)", font_bold_center)
            
            row = 17
            col = 0
            
            sum_total = sum_employer = sum_employee = sum_earning = 0
            for line in record.epf_ids:
                worksheet.merge_range(row,col,row,col+1, line.employee_id.name, font_left)
                worksheet.write(row,col+2, line.nic_no, font_center)
                worksheet.write(row,col+3, line.member_no, font_center)
                worksheet.write(row,col+4, line.total, font_right)
                worksheet.write(row,col+5, line.epf_employer, font_right)
                worksheet.write(row,col+6, line.epf_employee, font_right)
                worksheet.write(row,col+7, line.total_earning, font_right)
                sum_total += line.total
                sum_employer += line.epf_employer
                sum_employee += line.epf_employee
                sum_earning += line.total_earning
                row += 1
            worksheet.merge_range(row,col,row,col+3, 'Total', double_border)
            worksheet.write(row,col+4, sum_total, font__bold_right)
            worksheet.write(row,col+5, sum_employer, font__bold_right)
            worksheet.write(row,col+6, sum_employee, font__bold_right)
            worksheet.write(row,col+7, sum_earning, font__bold_right)
            worksheet.conditional_format( 0,0,row+1,7 , { 'type' : 'no_blanks' , 'format' : border} )
            
            row += 2
            worksheet.merge_range(row,col,row,col+3, 'I certify that the information given above is correct.', font_left)
            row += 1
            worksheet.merge_range(row,col+3,row,col+7, 'Please write employers EPF Registration Number on the reverse of the cheque.', font_left)
            row += 2
            worksheet.merge_range(row,col,row,col+2, '.............................', font_left)
            worksheet.merge_range(row,col+3,row,col+4, 'Telephone  ', font_left)
            worksheet.merge_range(row,col+5,row,col+6, record.telephone, font_left)
            
            row += 1
            worksheet.merge_range(row,col,row,col+2, 'Signature of Employer', font_left)
            worksheet.merge_range(row,col+3,row,col+4, 'Fax', font_left)
            worksheet.merge_range(row,col+5,row,col+6, record.fax, font_left)
            
            row += 1
            worksheet.merge_range(row,col+3,row,col+4, 'E-mail', font_left)
            worksheet.merge_range(row,col+5,row,col+6, record.email, font_left)
        
        
        
        