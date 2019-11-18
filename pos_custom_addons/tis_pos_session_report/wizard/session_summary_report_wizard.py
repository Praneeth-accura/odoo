# -- coding: utf-8 --
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
import xlsxwriter
from datetime import datetime, date, time
import base64
from odoo.tools import misc
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import os


class PosSession(models.Model):
    _inherit = 'pos.session'
   
    @api.multi
    def session_order_summary(self):
        orders = self.env['pos.order'].search([],order="date_order")
        return orders
    

class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard' 
    
    report = fields.Selection([('daily','Daily'),('monthly','Monthly'),('date_range','Date Range')])
    sales_person = fields.Boolean(string="Sales Person" ,default=False)
    products = fields.Boolean(string="Products")
    
    @api.onchange('report')
    def onchange_report(self):
        if self.report == 'daily':
            self.start_date = datetime.combine(date.today(), time(00,00,00))
            self.end_date = datetime.combine(date.today(), time(23,59,59))
           
        if self.report == 'monthly':
            self.start_date = date.today() + relativedelta(day=1,hour=00,minute=00,second=00)
            self.end_date = date.today() + relativedelta(day=31,hour=23,minute=59,second=59)
            
        if self.report == 'date_range':
            self.start_date = datetime.combine(date.today(), time(00,00,00))
    
    @api.depends('start_date','end_date','report')
    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.report == 'daily':
            date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S')
            self.start_date = datetime.combine(date1, time(00,00,00))
            self.end_date = datetime.combine(date1, time(23,59,59))
           
    def sales_report_xlsx(self):
        fl = ''
        if self.report == "date_range" and  self.sales_person == True:
            fl = self.daterange_by_salesperson()        #done
        elif self.report == "date_range" and  self.products == True:
            fl = self.daily_daterange_sale_by_items()   #done
        elif self.report == "daily" and self.sales_person == True:
            fl = self.daily_sale_by_salesperson()       #done
        elif self.report == "daily"  and self.products == True:
            fl = self.daily_daterange_sale_by_items()   #done
        elif self.report == "monthly"  and self.products == True:
            fl = self.monthly_item_wise_sales()         #done
        elif self.report == "monthly" and self.sales_person == True:
            fl = self.monthly_salesby_salesman()        #done
        elif self.report == "date_range" or self.report == "daily" or self.report == "monthly":
            fl = self.order_summary()                   #done
            
        if len(fl) > 0:
            my_report_data = open(fl,'rb+') 
            f = my_report_data.read()
            output = base64.encodestring(f)
            cr, uid, context = self.env.args
            ctx = dict(context)
            ctx.update({'report_file': output})
            ctx.update({'file': fl})
            self.env.args = cr, uid, misc.frozendict(context)
            ## To remove those previous saved report data from table. To avoid unwanted storage
            self._cr.execute("TRUNCATE pos_excel_export CASCADE")
            wizard_id = self.env['pos.excel.export'].create(vals={'name': fl,'report_file': ctx['report_file']})
            result = {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.excel.export',
                    'target': 'new',
                    'context': ctx,
                    'res_id': wizard_id.id,
            }
            os.remove(fl)
            return result
        else:
            raise ValidationError('There is no reports to print')
          
    def daterange_by_salesperson(self):
        date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        day1 = date1.strftime('%d')
        month1 = date1.strftime('%m')
        year1 = date1.strftime('%Y')
        day2 = date2.strftime('%d')
        month2 = date2.strftime('%m')
        year2 = date2.strftime('%Y')
        # Create an new Excel file and add a worksheet.
        valid = 0
        fl = os.path.join(os.path.dirname(__file__), 'Sales(from '+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2+')by salesperson.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 30)
        # Create a format to use in the merged range.
        font_left = workbook.add_format({'align':'left',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'bold': True})
        heading = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':20,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
        
        payment_methods = self.find_payment_methods(self.start_date, self.end_date)
        payment_methods_dict1 = {}
        payment_methods_dict2 = {}
        for method in payment_methods:
            payment_methods_dict1[method['id']] = 0
            payment_methods_dict2[method['id']] = method['name']
        
        sales_persons  = self.find_sales_persons(self.start_date, self.end_date)  
        sales_persons_dict1 = {}
        
        row = 5
        col = 1
        worksheet.write(row, col, 'Salesperson', font_bold_center)    
        for person in sales_persons:
            sales_persons_dict1[person['user_id']] = payment_methods_dict1.copy()
            
        col1 = col2 = col + 1
        for key in payment_methods_dict2:
            worksheet.set_column(row, col+1, 20)
            worksheet.write(row, col+1, payment_methods_dict2[key], font_bold_center)
            col += 1
        worksheet.write(row, col+1, "Total", font_bold_center)
        
        row += 1
        row1 = row
        for sales_person in sales_persons_dict1:
            for payment in payment_methods_dict1:
                payment_methods_dict1[payment] = 0
            user = self.env['res.users'].search([('id','=',sales_person)])
            worksheet.write(row, 1, user.name, font_left)
            row += 1
            orders = self.find_order_by_range_and_sales_man(self.start_date, self.end_date, sales_person)
            for order in orders:
                valid += 1
                payment_methods_dict1[order['journal_id']] += order['sum']
            sales_persons_dict1[sales_person] = payment_methods_dict1.copy()
        total_dict = {}
        for sales_person in sales_persons_dict1:
            total = 0
            for method in sales_persons_dict1[sales_person]:
                total += sales_persons_dict1[sales_person][method]
            total_dict[sales_person] = total
    
        for sales_person in sales_persons_dict1:
            col1 = col2
            for method in sales_persons_dict1[sales_person]:
                worksheet.write(row1, col1, sales_persons_dict1[sales_person][method], font_right)
                col1 += 1
            worksheet.write(row1, col1, total_dict[sales_person], font_right)
            row1 += 1
                
        month3 = date1.strftime('%b')
        month4 = date2.strftime('%b')
        worksheet.write(1, col, 'From', font_bold_center)
        worksheet.write(1, col+1, day1+'-'+month3+'-'+year1, date_format)     
        worksheet.write(2, col, 'To', font_bold_center)     
        worksheet.write(2, col+1,  day2+'-'+month4+'-'+year2, date_format)            
        worksheet.merge_range(3, 1, 4, col+1, 'Date Range Sales by SalesPerson', heading)            
        workbook.close()
        if valid == 0:
            raise ValidationError('There is no values to print')
        else:
            return fl
          
    def order_summary(self):
        date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        day1 = date1.strftime('%d')
        month1 = date1.strftime('%b')
        year1 = date1.strftime('%Y')
        day2 = date2.strftime('%d')
        month2 = date2.strftime('%b')
        year2 = date2.strftime('%Y')
        
        pos = []
        for config in self.pos_config_ids:
            pos.append(config.id)
        
        domain = [('session_id.config_id','in',pos),('date_order','>=', self.start_date),('date_order','<=', self.end_date)]
        orders = self.env['pos.order'].search(domain)
        if len(orders) == 0:
            raise ValidationError('There is no values to print')
        else:
        # Create an new Excel file and add a worksheet.
            if self.report == 'daily':
                fl = os.path.join(os.path.dirname(__file__), 'Order Summary ('+day1+'-'+month1+'-'+year1+').xlsx')
            elif self.report == 'monthly':
                fl = os.path.join(os.path.dirname(__file__), 'Order Summary ('+month1+'-'+year1+' to '+month2+'-'+year2+').xlsx')
            else:
                fl = os.path.join(os.path.dirname(__file__), 'Order Summary ('+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2+').xlsx')
                
            workbook = xlsxwriter.Workbook(fl)
            worksheet = workbook.add_worksheet()
            # Create a format to use in the merged range.
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
            font_bold_right = workbook.add_format({'num_format': '#,##0.00',
                                            'align':'right',
                                             'valign':'right',
                                             'font_size':12,
                                             'bold': True})
            date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
            heading = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':20,
                                             'bold': True})
            
            # Widen the first column to make the text clearer.
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:D', 25)
            worksheet.set_column('E:G', 20)
            
            row = 1
            col = 4
            if self.report == 'daily':
                worksheet.write(row,col+1, 'Date', font_bold_center)
                worksheet.write(row, col+2, day1+'-'+month1+'-'+year1)
            else:
                worksheet.write(row,col+1, 'From', font_bold_center)
                worksheet.write(row+1,col+1, 'To', font_bold_center)
                worksheet.write(row, col+2, day1+'-'+month1+'-'+year1)
                worksheet.write(row+1, col+2, day2+'-'+month2+'-'+year2)
                
            # Merge 3 cells.
            worksheet.merge_range('B4:G5', "Order Summary", heading)
            
            # Write some simple text.
            row = 6
            col = 1
            worksheet.write(row, col, 'Order Ref', font_bold_center)
            worksheet.write(row, col+1, 'Date', font_bold_center)
            worksheet.write(row, col+2, 'SalesMan', font_bold_center)
            worksheet.write(row, col+3, 'Untaxed Amount', font_bold_center)
            worksheet.write(row, col+4, 'Tax Amount', font_bold_center)
            worksheet.write(row, col+5, 'Total', font_bold_center)
            row = 7
            col = 0
            total = tax = wtax = 0
            for order in orders:
                worksheet.write(row+1, col+1,order.name, font_center)
                worksheet.write(row+1, col+2,order.date_order, date_format)
                worksheet.write(row+1, col+3,order.user_id.name, font_left)
                worksheet.write(row+1, col+4,order.amount_total - order.amount_tax, font_right)
                worksheet.write(row+1, col+5,order.amount_tax, font_right)
                worksheet.write(row+1, col+6,order.amount_total, font_right)
                wtax += (order.amount_total - order.amount_tax)
                tax += order.amount_tax
                total += order.amount_total
                row += 1
                
            worksheet.write(row+2, col+3, 'Net Total', font_bold_center)
            worksheet.write(row+2, col+4, wtax, font_bold_right)
            worksheet.write(row+2, col+5, tax, font_bold_right)
            worksheet.write(row+2, col+6, total, font_bold_right)
            workbook.close()
            return fl
        
    def daily_daterange_sale_by_items(self):
        date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        day1 = date1.strftime('%d')
        month1 = date1.strftime('%m')
        year1 = date1.strftime('%Y')
        day2 = date2.strftime('%d')
        month2 = date2.strftime('%m')
        year2 = date2.strftime('%Y')  
        
        pos = []
        for config in self.pos_config_ids:
            pos.append(config.id)
        
        domain = [('session_id.config_id','in',pos),('date_order','>=', self.start_date),('date_order','<=', self.end_date)]
        orders = self.env['pos.order'].search(domain)
        if self.report == 'daily':
        # Create an new Excel file and add a worksheet.
            fl = os.path.join(os.path.dirname(__file__), 'Daily ('+day1+'-'+month1+'-'+year1+') sales by item.xlsx')
        else:
            fl = os.path.join(os.path.dirname(__file__), 'DateRange ('+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2+') sales by item.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet("1")
        # Create a format to use in the merged range.
        # Merge 3 cells.
        # Widen the first column to make the text clearer.
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:J', 15)
        # Add a bold format to use to highlight cells.
        font_left = workbook.add_format({'align':'left',
                                         'font_size':12})
        font_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'font_size':12})
        heading = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':20,
                                             'bold': True})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
        # Write some simple text.
        
        if self.report == 'daily':
            worksheet.merge_range('B3:K4',"Daily Item wise Sales Summary",heading)
            worksheet.write('I2', 'Date', font_bold_center)
        else:
            worksheet.merge_range('B4:K5',"DateRange Item wise Sales Summary",heading)
            worksheet.write('I2', 'From', font_bold_center)
            worksheet.write('I3', 'To', font_bold_center)
            
        worksheet.write('B6', 'SI No', font_bold_center)
        worksheet.write('C6', 'Product Ref', font_bold_center)
        worksheet.write('D6', 'Product', font_bold_center)
        worksheet.write('E6', 'Qty', font_bold_center)
        worksheet.write('F6', 'Selling Price', font_bold_center)
        worksheet.write('G6', 'Cost Price', font_bold_center)
        worksheet.write('H6', 'Discount', font_bold_center)
        worksheet.write('I6', 'Subtotal', font_bold_center)
        worksheet.write('J6', 'Tax', font_bold_center)
        worksheet.write('K6', 'Total', font_bold_center)
        if self.report == 'daily':
            worksheet.merge_range('J2:K2',day1+'-'+month1+'-'+year1, date_format)
        else:
            worksheet.merge_range('J2:K2',day1+'-'+month1+'-'+year1, date_format)
            worksheet.merge_range('J3:K3',day2+'-'+month2+'-'+year2, date_format)
        
        i = 1   
        row = 7
        col = 0
        total = 0
        tax = 0
        for order in orders:
            for line in order.lines:
                worksheet.write(row, col+1, i, font_center)
                worksheet.write(row, col+2, line.product_id.default_code, font_center)
                worksheet.write(row, col+3, line.product_id.name, font_left) 
                worksheet.write(row, col+4, line.qty, font_center) 
                worksheet.write(row, col+5, line.price_unit, font_right)
                worksheet.write(row, col+6, line.product_id.standard_price, font_right) 
                worksheet.write(row, col+7, str(line.discount)+'%', font_right) 
                worksheet.write(row, col+8, line.price_subtotal, font_right)  
                worksheet.write(row, col+9, line.tax_ids_after_fiscal_position.name, font_center)  
                worksheet.write(row, col+10, line.price_subtotal_incl, font_right)
                row += 1
                i += 1
            total += order.amount_total
            tax += order.amount_tax
        worksheet.write(row+1, col+9, "Total Tax", font_bold_center)
        worksheet.write(row+2, col+9, "Net Total", font_bold_center)
        worksheet.write(row+1, col+10, tax, font_right)
        worksheet.write(row+2, col+10, total, font_right)
        
        workbook.close()
        if len(orders) == 0:
            raise ValidationError('There is no values to print')
        else:
            return fl
        
    def daily_sale_by_salesperson(self):  
        pos = []
        for config in self.pos_config_ids:
            pos.append(config.id)
        
        domain = [('session_id.config_id','in',pos),('date_order','>=', self.start_date),('date_order','<=', self.end_date)]
        orders = self.env['pos.order'].search(domain)
        current_date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        year = current_date1.strftime('%Y')
        month = current_date1.strftime('%b')
        day = current_date1.strftime('%d')
        date_today = day+'-'+month+'-'+year
        if len(orders) == 0:
            raise ValidationError('There is no values to print')
        else:
            # Create an new Excel file and add a worksheet.
            fl = os.path.join(os.path.dirname(__file__), 'Daily sales by salesperson ('+date_today+').xlsx')
            workbook = xlsxwriter.Workbook(fl)
            worksheet = workbook.add_worksheet()
           
            # Widen the first column to make the text clearer.
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:C', 25)
            worksheet.set_column('D:E', 20)
            # Add a bold format to use to highlight cells.
            font_left = workbook.add_format({'align':'left',
                                             'font_size':12})
            font_right = workbook.add_format({'num_format': '#,##0.00',
                                            'align':'right',
                                             'valign':'right',
                                             'font_size':12})
            font_bold_center = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':12,
                                             'bold': True})
            heading = workbook.add_format({'align':'center',
                                             'valign':'vcenter',
                                             'font_size':20,
                                             'bold': True})
            date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'bold':True})
            # Write some simple text.
            
            net_total_without_tax = 0
            sales_person_dict = {}
            payment_dict = {}
            journal_dict = {}
            journal_index = {}
            payment_methods = self.find_payment_methods(self.start_date, self.end_date)
            i = 1
            for method in payment_methods:
                journal_index[method['name']] = i
                journal_dict[method['name']] = 0
                i += 1
            
            for order in orders:
                if order.user_id.id in payment_dict:
                    for statement in order.statement_ids:
                        if statement.journal_id.name in journal_dict:
                            payment_dict[order.user_id.id][statement.journal_id.name] += statement.amount
                else:
                    for key in journal_dict:
                        journal_dict[key] = 0
                    for statement in order.statement_ids:
                        if statement.journal_id.name in journal_dict:
                            journal_dict[statement.journal_id.name] += statement.amount
                    payment_dict[order.user_id.id] = journal_dict.copy()
                    
                net_total_without_tax = (order.amount_total - order.amount_tax)
                list_order = [net_total_without_tax,order.amount_tax,order.amount_total]
                if order.user_id.id in sales_person_dict:
                    sales_person_dict[order.user_id.id][0] += (order.amount_total - order.amount_tax)
                    sales_person_dict[order.user_id.id][1] += order.amount_tax
                    sales_person_dict[order.user_id.id][2] += order.amount_total
                else:
                    sales_person_dict[order.user_id.id] = list_order
            
            row = 5
            col = 1
            worksheet.write(row, col, 'Sales Person', font_bold_center)
            worksheet.write(row, col+1, 'Untaxed Amount', font_bold_center)
            worksheet.write(row, col+2, 'Tax', font_bold_center)
            worksheet.write(row, col+3, 'Total Amount', font_bold_center)
            
            col = 4
            for key in journal_dict:
                ind = journal_index[key]
                worksheet.write(row, col+ind, key, font_bold_center)
                
            row = 6
            col = 0
            tot_untax = 0
            tot_tax = 0
            tot_amount = 0
            journal_tot = {}    
            for key in sales_person_dict:
                col = 0
                user = self.env['res.users'].search([('id','=',key)])
                worksheet.write(row, col+1,user.name, font_left)
                worksheet.write(row, col+2,sales_person_dict[key][0], font_right)
                worksheet.write(row, col+3,sales_person_dict[key][1], font_right)
                worksheet.write(row, col+4,sales_person_dict[key][2], font_right)
                for key1 in payment_dict[key]:
                    ind = journal_index[key1]
                    worksheet.set_column(row, col+5, 20)
                    worksheet.write(row, col+4+ind,payment_dict[key][key1], font_right)
                    if key1 in journal_tot:
                        journal_tot[key1] += payment_dict[key][key1]
                    else:
                        journal_tot[key1] = payment_dict[key][key1]
                        
                tot_untax += sales_person_dict[key][0]
                tot_tax += sales_person_dict[key][1]
                tot_amount += sales_person_dict[key][2]
                row += 1
            col = 0 
            worksheet.write(row+1,col+1,"Total", font_bold_center)
            worksheet.write(row+1,col+2,tot_untax, font_right)
            worksheet.write(row+1,col+3,tot_tax, font_right)
            worksheet.write(row+1,col+4,tot_amount, font_right)
            for key in journal_tot:
                ind = journal_index[key]
                worksheet.write(row+1,col+4+ind,journal_tot[key], font_right)
                
            worksheet.write(1, len(journal_tot)+3, 'Date', font_bold_center)
            worksheet.write(1, len(journal_tot)+4, date_today, date_format)
            worksheet.merge_range(2,1,3,len(journal_tot)+4,"Daily Sales by Salesperson",heading)
            workbook.close()
            return fl
       
    def monthly_item_wise_sales(self):
        date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        month1 = date1.strftime('%B')
        year1 = date1.strftime('%Y')
        date2 = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        month2 = date2.strftime('%B')
        year2 = date2.strftime('%Y')
        # Create an new Excel file and add a worksheet.
        fl = os.path.join(os.path.dirname(__file__), 'Monthly ('+month1+'-'+year1+' to '+month2+'-'+year2+') item wise sales summary.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        # Create a format to use in the merged range.
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
        heading = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':20,
                                         'bold': True})
        
        current_str_date_to = str(date.today())
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_year = int(current_year)
        year_end = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        previous_yr = (datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()).strftime('%Y')
        
        year_start2 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        current_month = int(year_start2.strftime('%-m'))
        current_year2 = int(previous_yr)
        
        col1 = 6
        row1 = 5
        status = 0
        while year_start2 < year_end:
            month_start = year_start2 + relativedelta(year=current_year2, month=current_month, day=1, hours=00, minutes=00, seconds=00)
            month_end = year_start2 + relativedelta(year=current_year2, month=current_month, day=31, hours=23, minutes=59, seconds=59)
            year = month_start.strftime('%Y')
            month = month_start.strftime('%b')
            
            worksheet = workbook.add_worksheet(month+'-'+year)
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 10)
            worksheet.set_column('C:D', 25)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:G', 20)
            
            # Write some simple text.
            worksheet.write('B6', 'SI No', font_bold_center)
            worksheet.write('C6', 'Product Ref', font_bold_center)
            worksheet.write('D6', 'Product', font_bold_center)
            worksheet.write('E6', 'Unit Price', font_bold_center)
            worksheet.write('F6', 'Disc (%)', font_bold_center)
            worksheet.write(row1,col1, "Quantity", font_bold_center)
            
            #printing months
            if current_month == 13:
                current_month = 1
                current_year2 += 1
            pos = ()
            for config in self.pos_config_ids:
                pos += (config.id,)
                
            sql_query = """ select pt.name,pos.product_id,pos.price_unit,pp.default_code,pos.discount,sum(pos.qty) from pos_order_line pos
                            left join product_product pp
                            on pos.product_id =  pp.id 
                            left join pos_order po
                            on pos.order_id= po.id
                            left join product_template pt on pp.product_tmpl_id = pt.id
                            left join pos_session ps on po.session_id = ps.id 
                            left join pos_config pc on ps.config_id = pc.id
                            where date_order >= %s and  date_order <= %s and pc.id in %s
                            group by pos.product_id,pos.price_unit,pos.discount,pp.default_code, pt.name
                            order by pos.product_id;"""
            params = (month_start,month_end, pos)
            self.env.cr.execute(sql_query,params)
            results = self.env.cr.dictfetchall()
            i=1   
            row = 7
            col = 0 
            for line in results: 
                status += 1
                worksheet.write(row,col+1,i, font_center)
                worksheet.write(row, col+2,line['default_code'], font_left) 
                worksheet.write(row, col+3,line['name'], font_left) 
                worksheet.write(row, col+4,line['price_unit'], font_right)
                worksheet.write(row, col+5,line['discount'], font_right)
                worksheet.write(row,col1,line['sum'], font_right) 
                row += 1
                i += 1
            
            pos1 = []
            for config in self.pos_config_ids:
                pos1.append(config.id)
            domain = [('session_id.config_id','in',pos1),('date_order','>=',str(month_start)),('date_order','<=',str(month_end))]
            orders = self.env['pos.order'].search(domain)
            tax = 0
            total = 0
            for order in orders:
                tax += order.amount_tax
                total += order.amount_total
            worksheet.write(row+1, col1-1, "Tax", font_bold_center)
            worksheet.write(row+2, col1-1, "Total", font_bold_center)
            worksheet.write(row+1, col1, tax, font_right)
            worksheet.write(row+2, col1, total, font_right)
                
            year_start2 += relativedelta(year=current_year2, month=current_month, day=31, hours=00, minutes=00, seconds=00)
            current_month += 1
            
            worksheet.write(1, col1-1, "Month", font_bold_center)
            worksheet.write(1, col1, month+'-'+year)
            worksheet.merge_range(2, 1, 3, col1,"Monthly Itemwise Sales Summary",heading)
        workbook.close()
        if status == 0:
            raise ValidationError('There is no values to print')
        else:
            return fl
    
    def find_payment_methods(self, date_from, date_to):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """ select distinct aj.id, aj.name from account_bank_statement_line abs
                        left join pos_order po on abs.pos_statement_id = po.id 
                        left join pos_session ps on po.session_id = ps.id 
                        left join pos_config pc on ps.config_id = pc.id  
                        left join account_journal aj on abs.journal_id = aj.id 
                        where po.date_order >= %s and  po.date_order <= %s and pc.id in %s
                        group by aj.id, aj.name;"""
        params = (date_from, date_to, pos)
        self.env.cr.execute(sql_query,params)
        results = self.env.cr.dictfetchall()
        return results
    
    def find_sales_persons(self, date_from, date_to):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """ select distinct pos.user_id, rp.name from pos_order pos 
                        left join res_users res on pos.user_id = res.id 
                        left join res_partner rp on res.partner_id = rp.id
                        left join pos_session ps on pos.session_id = ps.id 
                        left join pos_config pc on ps.config_id = pc.id
                        where pos.date_order >= %s and  pos.date_order <= %s and pc.id in %s
                        group by pos.user_id, rp.name
                        order by pos.user_id;"""
        params = (date_from, date_to, pos)
        self.env.cr.execute(sql_query,params)
        results = self.env.cr.dictfetchall()
        return results
    
    def find_order_by_range_and_sales_man(self, date_from, date_to, sales_man):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """ select pos.user_id, abs.journal_id, sum(abs.amount) 
                        from account_bank_statement_line abs
                        left join pos_order pos on abs.pos_statement_id = pos.id
                        left join pos_session ps on pos.session_id = ps.id 
                        left join pos_config pc on ps.config_id = pc.id
                        where pos.date_order >= %s and  pos.date_order <= %s
                        and pos.user_id = %s and pc.id in %s
                        group by pos.id,abs.journal_id;"""
        params = (date_from, date_to, sales_man, pos)
        self.env.cr.execute(sql_query,params)
        results = self.env.cr.dictfetchall()
        return results
                
    def monthly_salesby_salesman(self):
        date1 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        month1 = date1.strftime('%B')
        year1 = date1.strftime('%Y')
        month2 = date2.strftime('%B')
        year2 = date2.strftime('%Y')
        # Create an new Excel file and add a worksheet.
        valid = 0
        fl = os.path.join(os.path.dirname(__file__), 'Monthly sales by salesman (from '+month1+'-'+year1+' to '+month2+'-'+year2+').xlsx')
        workbook = xlsxwriter.Workbook(fl)
        
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 25)
        # Create a format to use in the merged range.
        font_left = workbook.add_format({'align':'left',
                                         'font_size':12})
        font_right = workbook.add_format({'num_format': '#,##0.00',
                                        'align':'right',
                                         'valign':'right',
                                         'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':12,
                                         'bold': True})
        heading = workbook.add_format({'align':'center',
                                         'valign':'vcenter',
                                         'font_size':20,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
        
        payment_methods = self.find_payment_methods(self.start_date, self.end_date)
        payment_methods_dict1 = {}
        payment_methods_dict2 = {}
        
        for method in payment_methods:
            payment_methods_dict1[method['id']] = 0
            payment_methods_dict2[method['id']] = method['name']
        
        sales_persons  = self.find_sales_persons(self.start_date, self.end_date)  
        sales_persons_dict1 = {}
        
        current_str_date_to = str(date.today())
        current_date1 = datetime.strptime(current_str_date_to,'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_year = int(current_year)
        year_end = datetime.strptime(str(self.end_date),'%Y-%m-%d %H:%M:%S').date()
        previous_yr = (datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()).strftime('%Y')
        
        year_start2 = datetime.strptime(str(self.start_date),'%Y-%m-%d %H:%M:%S').date()
        current_month = int(year_start2.strftime('%-m'))
        current_year2 = int(previous_yr)
        
        row = 5
        col = 1
        worksheet.merge_range(row, col, row+1, col, 'Salesperson', font_bold_center)    
        while year_start2 < year_end:
            row = 5
            for person in sales_persons:
                sales_persons_dict1[person['user_id']] = payment_methods_dict1.copy()
            if current_month == 13:
                current_month = 1
                current_year2 += 1
            month_start = year_start2 + relativedelta(year=current_year2, month=current_month, day=1, hours=00, minutes=00, seconds=00)
            month_end = year_start2 + relativedelta(year=current_year2, month=current_month, day=31, hours=23, minutes=59, seconds=59)
            year = month_start.strftime('%Y')
            month = month_start.strftime('%b')
            
            col1 = col2 = col + 1
            worksheet.merge_range(row, col+1, row, col+len(payment_methods)+1, month+'-'+year, font_bold_center)
            for key in payment_methods_dict2:
                worksheet.set_column(row, col+1, 20)
                worksheet.write(row+1, col+1, payment_methods_dict2[key], font_bold_center)
                col += 1
            worksheet.set_column(row, col+1, 20)
            worksheet.write(row+1, col+1, "Total", font_bold_center)
            col += 1
            
            row += 2
            row1 = row
            for sales_person in sales_persons_dict1:
                for payment in payment_methods_dict1:
                    payment_methods_dict1[payment] = 0
                user = self.env['res.users'].search([('id','=',sales_person)])
                worksheet.write(row, 1, user.name, font_left)
                row += 1
                orders = self.find_order_by_range_and_sales_man(str(month_start), str(month_end), sales_person)
                for order in orders:
                    valid += 1
                    payment_methods_dict1[order['journal_id']] += order['sum']
                sales_persons_dict1[sales_person] = payment_methods_dict1.copy()
            year_start2 += relativedelta(year=current_year2, month=current_month, day=31, hours=00, minutes=00, seconds=00)
            current_month += 1
            total_dict = {}
            for sales_person in sales_persons_dict1:
                total = 0
                for method in sales_persons_dict1[sales_person]:
                    total += sales_persons_dict1[sales_person][method]
                total_dict[sales_person] = total
        
            for sales_person in sales_persons_dict1:
                col1 = col2
                for method in sales_persons_dict1[sales_person]:
                    worksheet.write(row1, col1, sales_persons_dict1[sales_person][method], font_right)
                    col1 += 1
                worksheet.write(row1, col1, total_dict[sales_person], font_right)
                row1 += 1
        
        worksheet.write(1, col-1, 'From', font_bold_center)
        worksheet.write(1, col, month1+'-'+year1, date_format)     
        worksheet.write(2, col-1, 'To', font_bold_center)     
        worksheet.write(2, col,  month2+'-'+year2, date_format)            
        worksheet.merge_range(3, 1, 4, col, "Monthly Sales By SalesPerson", heading)            
        workbook.close()
        if valid == 0:
            raise ValidationError('There is no values to print')
        else:
            return fl
    
 
class pos_excel_export(models.TransientModel):
    _name = 'pos.excel.export'
    
    report_file = fields.Binary('File', readonly=True)
    name = fields.Text(string='File Name')

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        return {
            'type' : 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.details.wizard',
            'target' : 'new',
               }
                
   
