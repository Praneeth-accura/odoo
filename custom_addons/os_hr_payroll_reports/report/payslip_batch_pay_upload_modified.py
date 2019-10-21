# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models
import math

class PartnerXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.pay_upload_xlsx_modified'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, batches):
        for batch in batches:
            worksheet = workbook.add_worksheet('Pay Upload File ('+batch.name+')')
            worksheet.set_landscape()
            
            font_left = workbook.add_format({'align':'left',
                                             'font_size':12})
            font_center = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':12})
            font_right = workbook.add_format({'num_format': '#,##0.00',
                                            'align':'right',
                                             'valign':'right',
                                             'font_size':12})
            font_bold_center = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':12,
                                             'bold': True})
            border = workbook.add_format({'border':1})
            
            worksheet.set_column('A:B', 15)
            worksheet.set_column('C:D', 25)
            worksheet.set_column('E:F', 25)
            worksheet.set_row(0, 15)
            
            row = 0
            col = 0
            worksheet.write(row+1, col, 'Bank Code', font_bold_center)
            worksheet.write(row+1, col+1, 'Branch Code', font_bold_center)
            worksheet.write(row+1, col+2, 'Account Number', font_bold_center)
            worksheet.write(row+1, col+3, 'Employee Name', font_bold_center)
            worksheet.write(row+1, col+4, 'Employee EPF No.', font_bold_center)
            worksheet.write(row+1, col+5, 'Amount ', font_bold_center)
            for payslips in batch.slip_ids:
                for payslip in payslips:
                    worksheet.write(row+2, col, payslip.employee_id.bank_account_id.bank_id.bic, font_center)
                    worksheet.write(row+2, col+1, payslip.employee_id.bank_account_id.branch_id.code, font_center)
                    worksheet.write(row+2, col+2, str(payslip.employee_id.bank_account_id.acc_number).zfill(12), font_center)
                    worksheet.write(row+2, col+3, payslip.employee_id.name, font_left)
                    worksheet.write(row+2, col+4, payslip.employee_id.contract_id.member_no, font_left)
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            round_value = math.ceil(line.total)
                            total = int(round_value * 100)
                            value = float(total)
                            worksheet.write(row+2, col+5, value, font_right)
                row += 1
                
            worksheet.set_column('G:XFD', None, None, {'hidden': True})
            worksheet.conditional_format(0, 0, row + 1,5, {'type':'no_blanks', 'format': border})
        
