# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from odoo.tools.misc import xlwt
import io
import base64
from xlwt import easyxf
import datetime

class PaymentSummary(models.TransientModel):
    _name = "print.payment.summary"
    
    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date
    
    from_date = fields.Date(string='From Date', default=_get_from_date)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today)
    payment_summary_file = fields.Binary('Payment Summary Report')
    file_name = fields.Char('File Name')
    payment_report_printed = fields.Boolean('Payment Report Printed')
    currency_id = fields.Many2one('res.currency','Currency', default=lambda self: self.env.user.company_id.currency_id)
    type = fields.Selection([('in_invoice','Vendor'),('out_invoice','Customer')], default='in_invoice', string="Type")
    report_base = fields.Selection([('invoice','Invoice'),('payment','Payment')], required=True, default='payment', string="Based On")
    payment_mode = fields.Selection([('bank','Bank'),('cash','Cash')], string="Payment Mode")
    payment_type = fields.Selection([('outbound','Send Money'),('inbound','Receive Money'),('transfer','Internal Transfer')],
                                     string="Payment Type", default='outbound')
    
    
    @api.multi
    def action_print_payment_summary(self,):
        
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Payment Summary')
        money_format = xlwt.XFStyle()
        money_format.num_format_str = '#,##0.00'
        head_style = xlwt.easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;')
        total_money_style = xlwt.easyxf('font:height 200;align: horiz right;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;',num_format_str = '#,##0.00')
        total_style = xlwt.easyxf('font:height 200; align: horiz right;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;')
            
        if(self.report_base=='invoice'):
            str_type = str(self.type)
            invoice_type = ()
            if(str_type=='in_invoice'):
                str_type = 'Vendor'
                invoice_type = ('in_invoice','in_refund')
            else:
                str_type = 'Customer'
                invoice_type = ('out_invoice','out_refund')
                
            worksheet.write(1, 0, _('Invoice Date'), column_heading_style)
            worksheet.write(1, 1, _('Invoice Number'), column_heading_style) 
            worksheet.write(1, 2, _(str_type), column_heading_style)
            worksheet.write(1, 3, _('Invoice Amount'), column_heading_style)
            worksheet.write(1, 4, _('Invoice Currency'), column_heading_style)
            worksheet.write(1, 5, _('Paid Amount'), column_heading_style)
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            worksheet.col(5).height = 5000
              
            worksheet2 = workbook.add_sheet(str_type+' wise Payment Summary')
            worksheet2.write(1, 0, _(str_type), column_heading_style)
            worksheet2.write(1, 1, _('Paid Amount'), column_heading_style)
            worksheet2.col(0).width = 5000
            worksheet2.col(1).width = 5000
            row = 2
            customer_row = 2
            for wizard in self:
                heading =  'Payment Summary Report (' + str(wizard.currency_id.name) + ')'
                worksheet.write_merge(0, 0, 0, 5, heading, head_style)
                customer_payment_data = {}
                invoice_objs = self.env['account.invoice'].search([('date_invoice','>=',wizard.from_date),
                                                                   ('date_invoice','<=',wizard.to_date),
                                                                   ('type','in',invoice_type),
                                                                   ('payment_ids','!=',False)])
                for invoice in invoice_objs:
                    invoice_date = datetime.datetime.strptime(invoice.date_invoice, '%Y-%m-%d')
                    invoice_date = invoice_date.strftime("%d-%m-%Y")
                    worksheet.write(row, 0, invoice_date)
                    worksheet.write(row, 1, invoice.number)
                    worksheet.write(row, 2, invoice.partner_id.name)
                    worksheet.write(row, 3, invoice.amount_total, money_format)
                    worksheet.write(row, 4, invoice.currency_id.symbol)
                    paid_amount = 0
                    for payment in invoice.payment_ids:
                        if payment.state != 'draft' and payment.currency_id == wizard.currency_id:
                            paid_amount += payment.amount
                    worksheet.write(row, 5, paid_amount, money_format)
                    if invoice.partner_id.name not in customer_payment_data:
                        customer_payment_data.update({invoice.partner_id.name: paid_amount})
                    else:
                        paid_amount_data = customer_payment_data[invoice.partner_id.name] + paid_amount
                        customer_payment_data.update({invoice.partner_id.name: paid_amount_data})
                    row += 1
                for customer in customer_payment_data:
                    worksheet2.write(customer_row, 0, customer)
                    worksheet2.write(customer_row, 1, customer_payment_data[customer], money_format)
                    customer_row += 1
              
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                wizard.payment_summary_file = excel_file
                wizard.file_name = 'Payment Summary Report.xls'
                wizard.payment_report_printed = True
                fp.close()
                return {
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'res_model': 'print.payment.summary',
                        'view_type': 'form',
                        'type': 'ir.actions.act_window',
                        'context': self.env.context,
                        'target': 'new',
                    }
        if(self.report_base=='payment'):
            str_type = str(self.payment_type)
            if(str_type=='outbound'):
                str_type = 'Vendor'
            elif(str_type=='inbound'):
                str_type = 'Customer'
            else:
                str_type = 'Transfer To'
            worksheet.write(1, 0, _('Date'), column_heading_style)
            worksheet.write(1, 1, _('Number'), column_heading_style) 
            worksheet.write(1, 2, _('Payment Mode'), column_heading_style)
            worksheet.write(1, 3, _(str_type), column_heading_style)
            worksheet.write(1, 4, _('Amount'), column_heading_style)
            worksheet.write(1, 5, _('Currency'), column_heading_style)
            worksheet.write(1, 6, _('Memo'), column_heading_style)
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5000
            
            row = 2
            for wizard in self:
                date_from = datetime.datetime.strptime(wizard.from_date, '%Y-%m-%d')
                date_from = date_from.strftime("%d-%m-%Y")
                date_to = datetime.datetime.strptime(wizard.to_date, '%Y-%m-%d')
                date_to = date_to.strftime("%d-%m-%Y")
                heading =  'Payment Summary From  ' + str(date_from) + ' to ' +str(date_to)
                worksheet.write_merge(0, 0, 0, 6, heading, head_style)
                customer_payment_data = {}
                payment_state = ('draft','cancelled')
                domain = [('payment_date','>=',wizard.from_date), ('payment_date','<=',wizard.to_date), 
                          ('payment_type','=',wizard.payment_type), ('state','not in',payment_state)]
                if(wizard.payment_mode):
                    domain.append(('journal_id.type','=',wizard.payment_mode))
                payment_objs = self.env['account.payment'].search(domain)
                total_amount = 0
                for payment in payment_objs:
                    date_payment = datetime.datetime.strptime(payment.payment_date, '%Y-%m-%d')
                    date_payment = date_payment.strftime("%d-%m-%Y")
                    worksheet.write(row, 0, date_payment)
                    worksheet.write(row, 1, payment.name)
                    worksheet.write(row, 2, payment.journal_id.name)
                    if(payment.payment_type=='transfer'):
                        worksheet.write(row, 3, payment.destination_journal_id.name)
                    else:
                        worksheet.write(row, 3, payment.partner_id.name)
                    worksheet.write(row, 4, payment.amount, money_format)
                    worksheet.write(row, 5, payment.currency_id.symbol)
                    worksheet.write(row, 6, payment.communication)
                    if payment.partner_id.name not in customer_payment_data:
                        customer_payment_data.update({payment.partner_id.name: payment.amount})
                    else:
                        amount_data = customer_payment_data[payment.partner_id.name] + payment.amount
                        customer_payment_data.update({payment.partner_id.name: amount_data})
                    row += 1
                    total_amount += payment.amount
                    
                row += 1
                for i in range (0,3):
                    worksheet.write(row, i,'', head_style)
                worksheet.write(row, 3,'Total', total_style)
                worksheet.write(row, 4,total_amount, total_money_style)
                worksheet.write(row, 5,'', head_style)
                worksheet.write(row, 6,'', head_style)
               
                if(str(self.payment_type)!='transfer'):
                    worksheet2 = workbook.add_sheet(str_type+' wise Payment Summary')
                    worksheet2.write(1, 0, _(str_type), column_heading_style)
                    worksheet2.write(1, 1, _('Paid Amount'), column_heading_style)
                    worksheet2.col(0).width = 5000
                    worksheet2.col(1).width = 5000
                    customer_row = 2
                    
                    for customer in customer_payment_data:
                        worksheet2.write(customer_row, 0, customer)
                        worksheet2.write(customer_row, 1, customer_payment_data[customer], money_format)
                        customer_row += 1
                
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                wizard.payment_summary_file = excel_file
                wizard.file_name = 'Payment Summary.xls'
                wizard.payment_report_printed = True
                fp.close()
                return {
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'res_model': 'print.payment.summary',
                        'view_type': 'form',
                        'type': 'ir.actions.act_window',
                        'context': self.env.context,
                        'target': 'new',
                    }
