# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api
import xlsxwriter
import base64
from odoo.tools import misc
import os
from datetime import datetime
import pytz

class PurchaseReportWizard(models.Model):
    _name = 'purchase.report.wizard'
    
    report_type = fields.Selection([(0,'Summary'),(1,'Detailed')], default=0)
    date_from = fields.Datetime('From')
    date_to = fields.Datetime('To', default=datetime.today())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Is Printed', default=False)
    
    def export_vendor_report(self):
        if self.report_type:
            fl = self.export_vendor_detailed_report()
        else:
            fl = self.export_vendor_summary_report()
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
        os.remove(fl)
        result = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.report.wizard',
                'target': 'new',
                'context': ctx,
                'res_id': self.id,
        }
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
            'res_model': 'purchase.report.wizard',
            'target': 'new',
        }
        return result    
    
    def check_invoice_status(self, invoice_ids, state):
        for invoice in invoice_ids:
            if invoice.state in state:
                return True
            else:
                return False
            
    def check_picking_status(self, picking_ids, state):
        for picking in picking_ids:
            if picking.state == state:
                return True
            else:
                return False
    
    def find_state(self, st):
        state = {'draft':'RFQ',
                 'sent':'RFQ Sent',
                 'to approve':'To Approve',
                 'purchase':'Purchase Order',
                 'done':'Locked',
                 'cancel':'Cancelled'}
        return state[st]
        
    def export_vendor_summary_report(self):
        if self.date_from:
            fl = os.path.join(os.path.dirname(__file__), 'Purchases Summary Report('+self.date_from+' - '+self.date_to+').xlsx')
        else:
            fl = os.path.join(os.path.dirname(__file__), 'Purchases Summary Report(till '+self.date_to+').xlsx')
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
        font_bold_right = workbook.add_format({'bg_color':'#8f9399',
                                          'num_format': '#,##0.00',
                                          'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy',
                                           'border':1,
                                           'align':'center',
                                           'valign':'vcenter',
                                           'font_size':12})
        worksheet.set_column('J:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 16)
        worksheet.set_column('E:J', 15)
        row = col =0
        worksheet.merge_range(row, col, row+1, col+9, "Purchase by vendor summary report", bold)
        row += 2
        col = 0
        worksheet.write(row,col, "Date", font_bold_center)
        worksheet.write(row,col+1, "Reference", font_bold_center)
        worksheet.write(row,col+2, "Vendor Name", font_bold_center)
        worksheet.write(row,col+3, "Untaxed Amount", font_bold_center)
        worksheet.write(row,col+4, "Tax", font_bold_center)
        worksheet.write(row,col+5, "Total", font_bold_center)
        worksheet.write(row,col+6, "Status", font_bold_center)
        worksheet.write(row,col+7, "Shipped or Not", font_bold_center)
        worksheet.write(row,col+8, "Invoiced Or Not", font_bold_center)
        worksheet.write(row,col+9, "Paid or Not", font_bold_center)
        
        row += 1
        domain = [('date_order','<=', self.date_to)]
        if self.date_from:
            domain.append(('date_order','>=', self.date_from))
        orders = self.env['purchase.order'].search(domain, order='id')
        total_untax = 0
        total_tax = 0
        total_total = 0
        for order in orders:
            date_order = datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()
            worksheet.write(row,col, date_order, date_format)
            worksheet.write(row,col+1, order.name, font_center)
            worksheet.write(row,col+2, order.partner_id.name, font_left)
            worksheet.write(row,col+3, order.amount_untaxed, font_right)
            total_untax += order.amount_untaxed
            worksheet.write(row,col+4, order.amount_tax, font_right)
            total_tax += order.amount_tax
            worksheet.write(row,col+5, order.amount_total, font_right)
            total_total += order.amount_total
            state = self.find_state(order.state)
            worksheet.write(row,col+6, state, font_center)
            picking = self.check_picking_status(order.picking_ids, 'done')
            if picking:
                worksheet.write(row,col+7, "Shipped", font_center)
            else:
                worksheet.write(row,col+7, "Not", font_center)
            invoice = self.check_invoice_status(order.invoice_ids, ['open','paid'])
            if invoice:
                worksheet.write(row,col+8, "Invoiced", font_center)
            else:
                worksheet.write(row,col+8, "Not", font_center)
            paid = self.check_invoice_status(order.invoice_ids, ['paid'])
            if paid:
                worksheet.write(row,col+9, "Paid", font_center)
            else:
                worksheet.write(row,col+9, "Not", font_center)
            row += 1
        worksheet.write(row,col+2, 'Total', font_bold_right)
        worksheet.write(row,col+3, total_untax, font_bold_right)
        worksheet.write(row,col+4, total_tax, font_bold_right)
        worksheet.write(row,col+5, total_total, font_bold_right)
        
        workbook.close()
        return fl

    def export_vendor_detailed_report(self):
        if self.date_from:
            fl = os.path.join(os.path.dirname(__file__),'Purchases Detailed Report('+self.date_from+' - '+self.date_to+').xlsx')
        else:
            fl = os.path.join(os.path.dirname(__file__),'Purchases Detailed Report(till '+self.date_to+').xlsx')
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
        font_bold_right = workbook.add_format({'bg_color':'#8f9399',
                                          'num_format': '#,##0.00',
                                          'align':'right',
                                         'valign':'right',
                                         'border':1,
                                         'font_size':12,
                                         'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy',
                                           'border':1,
                                           'align':'center',
                                           'valign':'vcenter',
                                           'font_size':12})
        worksheet.set_column('N:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:H', 25)
        worksheet.set_column('I:N', 15)
        row = col =0
        worksheet.merge_range(row, col, row+1, col+13, "Purchase by vendor detailed report", bold)
        row += 2
        col = 0
        worksheet.merge_range(row,col,row+1,col, "Date", font_bold_center)
        worksheet.merge_range(row,col+1,row+1,col+1, "Reference", font_bold_center)
        worksheet.merge_range(row,col+2,row+1,col+2, "Vendor Name", font_bold_center)
        worksheet.merge_range(row,col+3,row+1,col+3, "Status", font_bold_center)
        worksheet.merge_range(row,col+4,row,col+13, "Order Details", font_bold_center)
        worksheet.write(row+1,col+4, "Product", font_bold_center)
        worksheet.write(row+1,col+5, "Internal Ref.", font_bold_center)
        worksheet.write(row+1,col+6, "Description", font_bold_center)
        worksheet.write(row+1,col+7, "Scheduled Date", font_bold_center)
        worksheet.write(row+1,col+8, "Quantity", font_bold_center)
        worksheet.write(row+1,col+9, "Qty Available", font_bold_center)
        worksheet.write(row+1,col+10, "Unit Price", font_bold_center)
        worksheet.write(row+1,col+11, "Taxes", font_bold_center)
        worksheet.write(row+1,col+12, "Sub Total", font_bold_center)
        worksheet.write(row+1,col+13, "Total", font_bold_center)
        
        row += 2
        domain = [('date_order','<=', self.date_to)]
        if self.date_from:
            domain.append(('date_order','>=', self.date_from))
        orders = self.env['purchase.order'].search(domain, order='id')
        for order in orders:
            date_order = datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()
            worksheet.write(row,col, date_order, date_format)
            worksheet.write(row,col+1, order.name, font_center)
            worksheet.write(row,col+2, order.partner_id.name, font_left)
            state = self.find_state(order.state)
            worksheet.write(row,col+3, state, font_center)
            row1 = row
            for line in order.order_line:
                res = line.product_id._product_available_done()
                worksheet.write(row1,col+4, line.product_id.name, font_left)
                worksheet.write(row1,col+5, line.product_id.default_code, font_left)
                worksheet.write(row1,col+6, line.name, font_left)
                date_planned = datetime.strptime(line.date_planned, '%Y-%m-%d %H:%M:%S').date()
                worksheet.write(row1,col+7, date_planned, date_format)
                worksheet.write(row1,col+8, line.product_qty, font_center)
                worksheet.write(row1,col+9, res[line.product_id.id]['qty_available'], font_center)
                worksheet.write(row1,col+10, line.price_unit, font_right)
                worksheet.write(row1,col+11, self.calculate_tax(line), font_right)
                worksheet.write(row1,col+12, line.price_subtotal, font_right)
                worksheet.write(row1,col+13, line.price_total, font_right)
                row1 += 1
            worksheet.write(row1,col+10, 'Total', font_bold_right)
            worksheet.write(row1,col+11, order.amount_tax, font_bold_right)
            worksheet.write(row1,col+12, order.amount_untaxed, font_bold_right)
            worksheet.write(row1,col+13, order.amount_total, font_bold_right)
            row += (len(order.order_line) + 1)
        
        workbook.close()
        return fl
    
    def calculate_tax(self, line):
        taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
        price_tax =  sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        return price_tax
