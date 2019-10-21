# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api
import datetime

class ReportBonusBatch(models.Model):
    _name = 'report.report_xlsx.bonus.batch'
    _inherit = 'report.report_xlsx.abstract'
     
    def generate_xlsx_report(self, workbook, data, objs):
        for obj in objs:
            worksheet = workbook.add_worksheet("Bonus ("+obj.name+")")
            worksheet.set_column('B:B',20)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:K', 15)
#             worksheet.set_column('M:XFD', None, None, {'hidden': True})
            
            worksheet.write('B2', 'Bonus Sheet for '+obj.name,
                            workbook.add_format({'bold':True}))
            worksheet.merge_range('B4:B7', 'PF NO', 
                                  workbook.add_format({'bottom':2, 'valign':'vcenter', 'bold':True, 'align':'center'}))
            worksheet.merge_range('C4:C7', 'NAME', 
                                  workbook.add_format({'bottom':2, 'valign':'vcenter','bold':True, 'align':'center'}))
    
            row = 3
            for col in range(3,11):
                worksheet.write(row,col,col-2,
                                 workbook.add_format({'bold':True, 'border':1 }))
            worksheet.merge_range('D5:D7', 'Average\nSALARY\nRs. Cts', 
                                  workbook.add_format({'bottom':2, 'valign':'vcenter', 'align':'right', 'bold':True}))
            worksheet.merge_range('E5:E7', 'BONUS\nTAXABLE', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'right', 'bold':True}))
            worksheet.merge_range('F5:F7', 'BON/SAL\nRATIO', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'center', 'bold':True}))
            worksheet.merge_range('G5:G7', 'TAX\nTABLE', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'center', 'bold':True}))
            worksheet.merge_range('H5:H7', 'TAX\n%', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'center', 'bold':True}))
            worksheet.merge_range('I5:I7', 'PAYE TAX\nRs', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'right', 'bold':True}))
            worksheet.merge_range('J5:J7', 'STAMP\nDUTY', 
                                  workbook.add_format({'bottom':2, 'valign':'vbottom', 'align':'right', 'bold':True}))
            worksheet.merge_range('K5:K7', 'NET\nBONUS\nRs. Cts', 
                                  workbook.add_format({'bottom':2, 'valign':'vcenter', 'align':'right', 'bold':True}))
            worksheet.merge_range('B8:K8', ' ',
                                   workbook.add_format({'border':1}))
            sum_bonus = 0
            sum_paye = 0
            sum_stamp = 0
            sum_net = 0
            
            row += 5
            col = 1
            for employee in obj.slip_ids:
                worksheet.write('B1',employee.employee_id.company_id.name,
                            workbook.add_format({'bold':True}))
                worksheet.write(row,col,employee.epf_no,
                            workbook.add_format({'align':'center',
                                                'border':1}))
                worksheet.write(row,col+1,employee.employee_id.name,
                            workbook.add_format({'align':'left',
                                                'border':1}))
                worksheet.write(row,col+2,employee.average_salary,
                            workbook.add_format({'align':'right',
                                                'border':1,
                                                'num_format': '#,##0.00'}))
                worksheet.write(row,col+3,employee.gross_bonus,
                            workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'border':1,}))
                if employee.average_salary > 0:
                    bon_sal_ratio = round(employee.gross_bonus/employee.average_salary,2)
                else:
                    bon_sal_ratio = 0 
                worksheet.write(row,col+4,bon_sal_ratio,
                            workbook.add_format({'align':'right',
                                                'border':1}))
                worksheet.write(row,col+5,employee.tax_table.name,
                            workbook.add_format({'align':'center',
                                                'border':1}))
                worksheet.write(row,col+6,employee.tax_rate,
                            workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'border':1}))
                worksheet.write(row,col+7,employee.paye,
                            workbook.add_format({'align':'right',
                                                 'num_format': '#,##0.00',
                                                'border':1}))
                worksheet.write(row,col+8,employee.stamp_duty,
                            workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'border':1}))
                worksheet.write(row,col+9,employee.net_bonus,
                                 workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'border':1}))
                row += 1
                sum_bonus += employee.gross_bonus
                sum_paye += employee.paye
                sum_stamp += employee.stamp_duty
                sum_net += employee.net_bonus
                
            worksheet.merge_range(row,1,row,10, ' ',
                                   workbook.add_format({'border':1}))
            worksheet.merge_range(row+1,1,row+1,2, 'TOTAL ',
                                   workbook.add_format({'border':1, 'align':'right', 
                                                        'valign':'vcenter','bold':True}))
        
            row += 1
            worksheet.merge_range(row,3,row,4, sum_bonus,
                                  workbook.add_format({'num_format': '#,##0.00',
                                                'bold':True, 'valign':'vcenter'}))
            worksheet.merge_range(row,5,row,8, sum_paye,
                                  workbook.add_format({'bold':True,'num_format': '#,##0.00',
                                                       'valign':'vcenter'}))
            worksheet.write(row,9,sum_stamp,
                                  workbook.add_format({'bold':True,'num_format': '#,##0.00',
                                                       'valign':'vcenter'}))
            worksheet.write(row,10,sum_net,
                                  workbook.add_format({'num_format': '#,##0.00',
                                                'bold':True,'valign':'vcenter'})) 
            row += 1
            
            worksheet.merge_range(row,1,row,10,' ',
                                  workbook.add_format({'num_format': '#,##0.00',
                                                'bold':True,'border':1})) 
            row +=1
            
            worksheet.merge_range(row,1,row,7,'PAYE',
                                  workbook.add_format({'bold':True,'align':'right'})) 
            
            worksheet.write(row,8,-sum_paye,
                            workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'bold':True}))
            sum = sum_net-sum_paye-sum_bonus-sum_stamp
            
            worksheet.merge_range(row,9,row,10,sum,
                                  workbook.add_format({'bold':True,'align':'right',
                                                       'num_format': '#,##0.00'})) 
            row += 1
            worksheet.merge_range(row,1,row,7,'TOTAL TAX',
                                  workbook.add_format({'bold':True,'align':'right'})) 
            worksheet.write(row,8,-sum_paye,
                            workbook.add_format({'align':'right',
                                                'num_format': '#,##0.00',
                                                'bold':True}))
            worksheet.merge_range(row,9,row,10,' ',
                                  workbook.add_format({'border':1})) 
            
            row += 1
            
            worksheet.merge_range(row,1,row,10,' ')
            
            worksheet.merge_range(row+1, 2, row+1, 3,'....................................')
            worksheet.merge_range(row+1, 4, row+1, 5,'.....................................')
            
            row += 2
            
            
            border = workbook.add_format({'border':1})
            worksheet.conditional_format(3,1,row,10, {'type': 'no_blanks',
                                             'format': border})
            worksheet.merge_range(row ,2, row, 3,'Prepared By',
                                  workbook.add_format({'bold':True}))
            worksheet.merge_range(row, 4, row, 5,'Approved By',
                                  workbook.add_format({'bold':True}))
            date = datetime.datetime.now().date()
            date = datetime.datetime.strftime(date,"%d %b %Y")
            worksheet.merge_range(row+1, 2, row+1, 3, date,
                                  workbook.add_format({'border':1}))
            worksheet.merge_range(row+1, 4, row+1, 5, ' ',
                                  workbook.add_format({'border':1}))
            
            border_bottom = workbook.add_format({'bottom':3})
            worksheet.conditional_format('B7:L7', {'type': 'no_blanks',
                                             'format': border_bottom})
            
