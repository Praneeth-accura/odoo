# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, fields, api, _
import datetime
from odoo.tools.misc import xlwt
import io
import base64
from xlwt import easyxf

class JournalDaybook(models.TransientModel):
    _name = 'journal.daybook'
    
    @api.model
    def _get_current_date(self):
        return datetime.date.today()
    
    from_date = fields.Date('Date From', default=_get_current_date, required=True)
    to_date = fields.Date('Date To', default=_get_current_date, required=True)
    amount_filter = fields.Selection([('equal','Equals to'), ('less','Less than'), ('greater','Greater than'), ('range','Range')],'Amount Filter')
    amount_from = fields.Float('Amount')
    amount_to = fields.Float('Amount to')
    partner_ids = fields.Many2many('res.partner', string="Partners")
    type = fields.Char('Invoice Type')
    journal_id = fields.Many2one('account.journal')
    daybook_file = fields.Binary('Daybook')
    file_name = fields.Char('File Name')
    daybook_printed = fields.Boolean('Daybook Printed')
    
    @api.multi
    def action_daybook(self):
        journal_id = self._context.get('active_id', False)
        journal = self.env['account.journal'].browse(journal_id)
        for wizard in self:
            action_name = journal._context.get('action_name', False)
            if not action_name:
                if journal.type == 'bank':
                    action_name = 'action_account_payments'
                elif journal.type == 'cash':
                    action_name = 'action_account_payments'
                elif journal.type == 'sale':
                    action_name = 'action_invoice_tree1'
                elif journal.type == 'purchase':
                    action_name = 'action_invoice_tree2'
            _journal_invoice_type_map = {
                ('sale', None): 'out_invoice',
                ('purchase', None): 'in_invoice',
                ('sale', 'refund'): 'out_refund',
                ('purchase', 'refund'): 'in_refund',
                ('bank', None): 'bank',
                ('cash', None): 'cash',
            }
            invoice_type = _journal_invoice_type_map[(journal.type, journal._context.get('invoice_type'))]
    
            ctx = journal._context.copy()
            ctx.pop('group_by', None)
            ctx.update({
                'journal_type': journal.type,
                'default_journal_id': journal.id,
                'search_default_journal_id': journal.id,
                'default_type': invoice_type,
                'type': invoice_type,
        
            })
    
            [action] = journal.env.ref('account.%s' % action_name).read()
            action['context'] = ctx
            
            if invoice_type == 'bank' or invoice_type == 'cash':
                domain_date = 'payment_date'
                domain_amount = 'amount'
                wizard.type = 'payment'
                status = ('posted','sent','reconciled')
            else:
                domain_amount = 'amount_total_signed'
                domain_date = 'date'
                wizard.type = 'invoice'
                status = ('open','paid')
                
            domain = [(domain_date ,'>=', wizard.from_date),(domain_date ,'<=', wizard.to_date),('state','in',status)]
            if wizard.amount_filter == 'equal':
                domain.append((domain_amount, '=', wizard.amount_from))
            elif wizard.amount_filter == 'greater':
                domain.append((domain_amount, '>=', wizard.amount_from))
            elif wizard.amount_filter == 'less':
                domain.append((domain_amount, '<=', wizard.amount_from))
            elif wizard.amount_filter == 'range':
                domain.append((domain_amount, '>=', wizard.amount_from))
                domain.append((domain_amount, '<=', wizard.amount_to))
            if wizard.partner_ids:
                partner_id = []
                for partner in wizard.partner_ids:
                    partner_id.append(partner.id)
                domain.append(('partner_id', 'in', partner_id))
            action['domain'] = domain
            account_invoice_filter = journal.env.ref('account.view_account_invoice_filter', False)
            if action_name in ['action_invoice_tree1', 'action_invoice_tree2']:
                action['search_view_id'] = account_invoice_filter and account_invoice_filter.id or False
            if action_name in ['action_bank_statement_tree', 'action_view_bank_statement_tree']:
                action['views'] = False
                action['view_id'] = False
        return action
    
    @api.multi
    def daybook_lines(self):
        journal_id = self.env.context.get('active_id', [])
        journal = self.env['account.journal'].browse(journal_id)

        for wizard in self:
            if wizard.type == 'bank' or wizard.type == 'cash':
                domain_date = 'payment_date'
                domain_amount = 'amount'
                status = ('posted','sent','reconciled')
            else:
                domain_amount = 'amount_total_signed'
                domain_date = 'date'
                status = ('open','paid')
                
            domain = [(domain_date ,'>=', wizard.from_date),(domain_date ,'<=', wizard.to_date),('state','in',status)]
            if wizard.amount_filter == 'equal':
                domain.append((domain_amount, '=', wizard.amount_from))
            elif wizard.amount_filter == 'greater':
                domain.append((domain_amount, '>=', wizard.amount_from))
            elif wizard.amount_filter == 'less':
                domain.append((domain_amount, '<=', wizard.amount_from))
            elif wizard.amount_filter == 'range':
                domain.append((domain_amount, '>=', wizard.amount_from))
                domain.append((domain_amount, '<=', wizard.amount_to))
            if wizard.partner_ids:
                partner_id = []
                for partner in wizard.partner_ids:
                    partner_id.append(partner.id)
                domain.append(('partner_id', 'in', partner_id))
            domain.append(('journal_id', '=', wizard.journal_id.id))
            if wizard.type == 'bank' or wizard.type == 'cash':
                invoice_objs = self.env['account.payment'].search(domain)
            else:
                invoice_objs = self.env['account.invoice'].search(domain)
            return invoice_objs
    
    @api.multi
    def export_daybook(self):
        journal = self._context.get('active_id', False)
        journal = self.env['account.journal'].browse(journal)
        self.journal_id = journal
        self.type = journal.type
        lines = self.daybook_lines();
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Daybook')
        money_format = xlwt.XFStyle()
        money_format.num_format_str = '#,##0.00'
        head_style = xlwt.easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;')
        total_money_style = xlwt.easyxf('font:height 200;align: horiz right;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;',num_format_str = '#,##0.00')
        total_style = xlwt.easyxf('font:height 200; align: horiz right;pattern: pattern solid, fore_colour gray25; font: color black; font:bold True;')
        
        heading = str(self.journal_id.type) + ' Daybook '
        if self.type == 'bank' or self.type == 'cash':
            worksheet.write(1, 0, _('Payment Date'), column_heading_style)
            worksheet.write(1, 1, _('Name'), column_heading_style) 
            worksheet.write(1, 2, _('Payment Journal'), column_heading_style)
            worksheet.write(1, 3, _('Customer'), column_heading_style)
            worksheet.write(1, 4, _('Payment Amount'), column_heading_style)
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            
            row = 2
            
            for wizard in self:
                if wizard.from_date == wizard.to_date :
                    heading += "for "+str(wizard.format_date(wizard.from_date))
                else:
                    heading += str(wizard.format_date(wizard.from_date))+" - "+str(wizard.format_date(wizard.to_date))
                worksheet.write_merge(0, 0, 0, 4, heading.title(), head_style)
                total = 0
                for line in lines:
                    worksheet.write(row, 0, wizard.format_line_date(line.payment_date))
                    worksheet.write(row, 1, line.name)
                    worksheet.write(row, 2, line.journal_id.name)
                    worksheet.write(row, 3, line.partner_id.name)
                    worksheet.write(row, 4, line.amount, money_format)
                    total += line.amount 
                    row += 1
                row += 1
                for i in range (0,4):
                    worksheet.write(row, i,'', head_style)
                worksheet.write(row, 4, total, total_money_style)
            
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                wizard.daybook_file = excel_file
                wizard.file_name = 'Daybook Report.xls'
                wizard.daybook_printed = True
                fp.close()
                return {
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'res_model': 'journal.daybook',
                        'view_type': 'form',
                        'type': 'ir.actions.act_window',
                        'context': self.env.context,
                        'target': 'new',
                    }
        else:
            if self.type == 'sale':
                worksheet.write(1, 0, _('Invoice Date'), column_heading_style)
                worksheet.write(1, 2, _('Customer'), column_heading_style)
                worksheet.write(1, 5, _('Amount Due'), column_heading_style)
            else:
                worksheet.write(1, 0, _('Bill Date'), column_heading_style)
                worksheet.write(1, 2, _('Vendor'), column_heading_style)
                worksheet.write(1, 5, _('To Pay'), column_heading_style)
            worksheet.write(1, 1, _('Number'), column_heading_style) 
            worksheet.write(1, 3, _('Due Date'), column_heading_style)
            worksheet.write(1, 4, _('Total'), column_heading_style)
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            worksheet.col(5).width = 5000
            row = 2
            
            for wizard in self:
                if wizard.from_date == wizard.to_date :
                    heading += "for "+str(wizard.format_date(wizard.from_date))
                else:
                    heading += str(wizard.format_date(wizard.from_date))+" - "+str(wizard.format_date(wizard.to_date))
                worksheet.write_merge(0, 0, 0, 5, heading.title(), head_style)
                total = 0
                total_residual = 0
                for line in lines:
                    worksheet.write(row, 0, wizard.format_line_date(line.date_invoice))
                    worksheet.write(row, 1, line.number)
                    worksheet.write(row, 2, line.partner_id.name)
                    worksheet.write(row, 3, wizard.format_line_date(line.date_due))
                    worksheet.write(row, 4, line.amount_total_signed, money_format)
                    worksheet.write(row, 5, line.residual_signed, money_format)
                    total += line.amount_total_signed
                    total_residual += line.residual_signed
                    row += 1
                row += 1
                for i in range (0,4):
                    worksheet.write(row, i,'', head_style)
                worksheet.write(row, 4, total, total_money_style)
                worksheet.write(row, 5, total_residual, total_money_style)
            
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                wizard.daybook_file = excel_file
                wizard.file_name = 'Daybook Report.xls'
                wizard.daybook_printed = True
                fp.close()
                return {
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'res_model': 'journal.daybook',
                        'view_type': 'form',
                        'type': 'ir.actions.act_window',
                        'context': self.env.context,
                        'target': 'new',
                    }
                
    @api.multi
    def print_daybook(self):
        journal = self._context.get('active_id', False)
        journal = self.env['account.journal'].browse(journal)
        self.journal_id = journal
        self.type = journal.type
        return self.env.ref('tis_daybook.action_report_daybook').report_action(self.id)
    
    def format_date(self,date):
        if date:
            date = datetime.datetime.strptime(date,"%Y-%m-%d")
            return date.strftime("%B %d, %Y")
        else:
            return ''
    
    def format_line_date(self,date):
        if date:
            date = datetime.datetime.strptime(date,"%Y-%m-%d")
            return date.strftime("%d/%m/%Y")
        else:
            return ''
         
