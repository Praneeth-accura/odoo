# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
import csv
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import io
import base64
import datetime
from datetime import datetime, timedelta

class QBReport(models.TransientModel):
    _name = 'qb.report'
    
    date_from = fields.Date('From Date', default=datetime.today()-timedelta(days=30))
    date_to = fields.Date('To Date', default=datetime.today())
    journal_ids = fields.Many2many('account.journal', string='Journals', domain=[('type', 'in', ['sale','purchase'])])
    qb_printed = fields.Boolean('QB Printed')
    qb_file = fields.Binary('Payment Summary Report')
    file_name = fields.Char('File Name')
    type = fields.Selection([('purchase','Purchase Order'),('sale','Sale Order')], string='Journal Entries On', default='sale', required=True)

    @api.multi
    def action_export_csv(self):
        for wizard in self:
            fp = io.BytesIO()
            writer = csv.writer(fp)
            domain = [('partner_id', '!=', False),
                      ('date','>=',wizard.date_from),
                      ('date','<=',wizard.date_to)]
            journal_ids = []
            for journal_id in wizard.journal_ids:
                journal_ids.append(journal_id.id)
            if wizard.journal_ids:
                domain.append(('journal_id', 'in', journal_ids))
            domain.append(('line_ids', '!=', False))
            journal_entries = wizard.env['account.move'].search(domain)
            if not journal_entries:
                raise UserError("No Records")
            if wizard.type == 'purchase':
                head = ['!VEND','NAME','PRINTAS','ADDR1','ADDR2','ADDR3','ADDR4','ADDR5','VTYPE',
                    'CONT1','CONT2','PHONE1','PHONE2','FAXNUM','EMAIL','NOTE','TAXID','LIMIT',
                    'NOTEPAD','SALUTATION','COMPANYNAME','FIRSTNAME','MIDINIT','LASTNAME']
            else:
                head = ['!CUST','NAME','BADDR1','BADDR2','BADDR3','BADDR4','BADDR5',
                    'SADDR1','SADDR2','SADDR3','SADDR4','SADDR5','PHONE1','PHONE2',
                    'FAXNUM','EMAIL','NOTE','CONT1','CONT2','CTYPE','TERMS','TAXABLE',
                    'LIMIT','RESALENUM','REP','TAXITEM','NOTEPAD','SALUTATION',
                    'COMPANYNAME','FIRSTNAME','MIDINIT','LASTNAME']
            
            partners = []
            trans_lines = []
            for entry in journal_entries:
                if wizard.type == 'pos' and any(line.statement_line_id.pos_statement_id for line in entry.line_ids):
                    customer =  entry.line_ids[0].statement_line_id.pos_statement_id.partner_id or ''
                    partner_details = ['CUST',
                                       customer.name,
                                       customer.street or '',
                                       customer.street2 or '',
                                       customer.city or '',
                                       customer.state_id.name or '',
                                       customer.country_id.name or '',
                                       '','','','','',
                                       customer.phone or '',
                                       customer.mobile or '','',
                                       customer.email or '',
                                       '','','','','','','','','','','','',
                                       customer.parent_id.name or '',
                                       '','','']
                    if partner_details not in partners:
                        partners.append(partner_details)
                    
                    trans_entry = []
                    for line in entry.line_ids:
                        if line.debit > line.credit:
                            trans = ['TRNS', 
                                     'Invoice',
                                     self.format_date(entry.date) or '',
                                     line.account_id.name or '',
                                     customer.name or '',
                                     line.debit - line.credit or '',
                                     entry.name or '',
                                     line.statement_line_id.pos_statement_id.pos_reference or '',]
                            trans_entry.append(trans)
                        if line.credit > line.debit:
                            trans = ['SPL', 
                                     'Invoice',
                                     self.format_date(entry.date) or '',
                                     line.account_id.name or '',
                                     customer.name or '',
                                     line.debit - line.credit or '',
                                     entry.name or '',
                                     line.statement_line_id.pos_statement_id.pos_reference or '',]
                            trans_entry.append(trans)
                    trans_lines.append(trans_entry)
                    
                if wizard.type == 'purchase' and not any(line.statement_line_id.pos_statement_id for line in entry.line_ids):
                    if (entry.journal_id.type == 'purchase'):
                        vendor = entry.line_ids[0].partner_id
                        partner_details = ['VEND',
                                           vendor.name or '','',
                                           vendor.street or '',
                                           vendor.street2 or '',
                                           vendor.city or '',
                                           vendor.state_id.name or '',
                                           vendor.country_id.name or '',
                                           '','','',
                                           vendor.phone or '',
                                           vendor.mobile or '','',
                                           vendor.email or '',
                                           '','','','','',
                                           vendor.parent_id.name or '',
                                           '','','']
                        if partner_details not in partners:
                            partners.append(partner_details)
                         
                        trans_entry = []
                        for line in entry.line_ids:
                            if line.debit > line.credit:
                                trans = ['SPL', 
                                         'BILL',
                                         self.format_date(entry.date) or '',
                                         line.account_id.name or '',
                                         '',
                                         line.debit - line.credit or '',
                                         entry.name or '',
                                         line.invoice_id and line.invoice_id.name or '',]
                                trans_entry.append(trans)
                            if line.credit > line.debit:
                                trans = ['TRNS', 
                                         'BILL',
                                         self.format_date(entry.date) or '',
                                         line.account_id.name or '',
                                         vendor.name or '',
                                         line.debit - line.credit or '',
                                         entry.name or '',
                                         line.invoice_id and line.invoice_id.name or '',]
                                trans_entry.append(trans)
                        trans_lines.append(trans_entry)
                        
                if wizard.type == 'sale' and not any(line.statement_line_id.pos_statement_id for line in entry.line_ids):
                    if (entry.journal_id.type == 'sale'):
                        customer = entry.line_ids[0].partner_id or ''
                        if customer == '':
                            partner_details = ['CUST',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '', '', '', '', '',
                                               '',
                                               '', '',
                                               '',
                                               '', '', '', '', '', '', '', '', '', '', '', '',
                                               '',
                                               '', '', '']
                        else:
                            partner_details = ['CUST',
                                               customer.name or '',
                                               customer.street or '',
                                               customer.street2 or '',
                                               customer.city or '',
                                               customer.state_id.name or '',
                                               customer.country_id.name or '',
                                               '','','','','',
                                               customer.phone or '',
                                               customer.mobile or '','',
                                               customer.email or '',
                                               '','','','','','','','','','','','',
                                               customer.parent_id.name or '',
                                               '','','']
                        if partner_details not in partners:
                            partners.append(partner_details)
                        
                        trans_entry = []
                        for line in entry.line_ids:
                            if line.debit > line.credit:
                                if customer == '':
                                    trans = ['TRNS',
                                             'Invoice',
                                             self.format_date(entry.date) or '',
                                             line.account_id.name or '',
                                             '',
                                             line.debit - line.credit or '',
                                             entry.name or '',
                                             line.invoice_id and line.invoice_id.name or '',]
                                else:
                                    trans = ['TRNS',
                                             'Invoice',
                                             self.format_date(entry.date) or '',
                                             line.account_id.name or '',
                                             customer.name or '',
                                             line.debit - line.credit or '',
                                             entry.name or '',
                                             line.invoice_id and line.invoice_id.name or '',]
                                trans_entry.append(trans)
                            if line.credit > line.debit:
                                if customer == '':
                                    trans = ['SPL',
                                             'Invoice',
                                             self.format_date(entry.date) or '',
                                             line.account_id.name or '',
                                             '',
                                             line.debit - line.credit or '',
                                             entry.name or '',
                                             line.invoice_id and line.invoice_id.name or '',]
                                else:
                                    trans = ['SPL',
                                             'Invoice',
                                             self.format_date(entry.date) or '',
                                             line.account_id.name or '',
                                             customer.name or '',
                                             line.debit - line.credit or '',
                                             entry.name or '',
                                             line.invoice_id and line.invoice_id.name or '',]
                                trans_entry.append(trans)
                        trans_lines.append(trans_entry)
            
            writer.writerow(head)
            if not partners:
                raise UserError("No Records")
            for partner in partners:
                writer.writerow(partner)
            writer.writerow(['!TRNS','TRNSTYPE','DATE','ACCNT','NAME','AMOUNT','DOCNUM','MEMO'])
            writer.writerow(['!SPL','TRNSTYPE','DATE','ACCNT','NAME','AMOUNT','DOCNUM','MEMO'])
            for trans_entry in trans_lines:
                if trans_entry:
                    writer.writerow(['!ENDTRNS'])
                for trans in trans_entry:
                    writer.writerow(trans)
                if trans_entry:    
                    writer.writerow(['ENDTRNS'])
            excel_file = base64.encodestring(fp.getvalue())
            wizard.qb_file = excel_file
            wizard.file_name = 'QB Report.csv'
            wizard.qb_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'qb.report',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                }
            
    def format_date(self,date):
        date = datetime.strptime(date,"%Y-%m-%d")
        return date.strftime("%m/%d/%Y")
