# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models


class PartnerXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.etf_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, etf):
        for record in etf:
            worksheet = workbook.add_worksheet('ETF ('+record.name+')')
            worksheet.set_landscape()
    #         worksheet.set_font_name('Times New Roman')
            bold_left = workbook.add_format({'bold': True,'align':'left'})
            bold_right = workbook.add_format({'bold': True,
                                              'align':'right'})
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
            font_bold_right = workbook.add_format({'num_format': '#,##0.00',
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
            worksheet.set_column('I:XFD', None, None, {'hidden': True})
            worksheet.set_column('A:D', 20)
            worksheet.set_column('E:E', 10)
            worksheet.set_column('F:G', 20)
            worksheet.set_column('H:H', 1)
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
                
            worksheet.set_row(1, 20)
            worksheet.merge_range('A2:G2', "EMPLOYEES' TRUST FUND BOARD", large)
            worksheet.merge_range('D4:F4', 'ADVICE OF REMITANCE FORM', bold_left)
            worksheet.write('G4', 'G4', bold_right)
            worksheet.merge_range('A6:B6', self.env.user.company_id.name, bold_left)
            worksheet.merge_range('A7:B9', address, font_left)
            
            row = 5
            col = 3
            worksheet.merge_range(row,col,row,col+1, 'ETF Registration No ', font_left)
            worksheet.merge_range(row,col+2,row,col+3, record.etf_reg_no, font_left)
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
            worksheet.merge_range(row,col+4,row+1,col+5, "Contribution (Rs. Cts.)", font_bold_center)
            
            row = 17
            col = 0
            for line in record.etf_ids:
                worksheet.merge_range(row,col,row,col+1, line.employee_id.name, font_left)
                worksheet.write(row,col+2, line.nic_no, font_center)
                worksheet.write(row,col+3, line.member_no, font_center)
                worksheet.merge_range(row,col+4,row,col+5, line.contribution, font_right)
                row += 1
            worksheet.merge_range(row,col,row,col+3, 'Total', double_border)
            worksheet.merge_range(row,col+4,row,col+5, record.contribution, font_bold_right)
            worksheet.conditional_format( 0,0,row+1,7 , { 'type' : 'no_blanks' , 'format' : border} )
            row += 2
            worksheet.merge_range(row,col,row,col+3, 'I certify that the information given above is correct.', font_left)
            row += 2
            worksheet.merge_range(row,col,row,col+1, '.............................', font_left)
            worksheet.write(row,col+2, 'Telephone ', font_left)
            worksheet.write(row,col+3, record.telephone, font_left)
            row += 1
            worksheet.merge_range(row,col,row,col+1, 'Signature of Employer', font_left)
            worksheet.write(row,col+2, 'Fax', font_left)
            worksheet.write(row,col+3, record.fax, font_left)
            row += 1
            worksheet.write(row,col+2, 'E-mail', font_left)
            worksheet.write(row,col+3, record.email, font_left)
        