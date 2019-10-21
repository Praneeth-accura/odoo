# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from ast import literal_eval

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
     
    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'discount_type', 'discount_rate')
    def _compute_amount(self):
        res = super(AccountInvoice, self)._compute_amount()
        self.amount_grand = self.amount_untaxed + self.amount_tax
        if(self.discount_type=='percent'):
            self.amount_discount = round((self.amount_grand * self.discount_rate / 100),2)
        elif(self.discount_type=='amount'):
            self.amount_discount = self.discount_rate
        if(self.amount_grand > self.amount_discount):
            self.amount_total = self.amount_grand - self.amount_discount
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        return res

    discount_type = fields.Selection([('percent', 'Percentage'),('amount', 'Amount')], 'Discount Type',
                        readonly=True, states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', 
                        readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_grand = fields.Float(string='Total', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_total = fields.Float(string='Net Total', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_compute_amount')
         
    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self). _prepare_invoice_line_from_po_line(line)
        self.discount_type = self.purchase_id.discount_type
        self.discount_rate = self.purchase_id.discount_rate
        self.discount_narration = self.purchase_id.discount_narration
        self.analytic_id = self.purchase_id.analytic_id
        return res
    
    @api.multi
    def action_move_create(self):
        if (not self.amount_discount):
            return super(AccountInvoice, self).action_move_create()
        account_move = self.env['account.move']
        ICPSudo = self.env['ir.config_parameter'].sudo()
        discount_sales_account_id = literal_eval(ICPSudo.get_param('tis_sales_purchase_global_discount.default_discount_sales_account_id', 
                                                                           default='False'))
        discount_purchase_account_id = literal_eval(ICPSudo.get_param('tis_sales_purchase_global_discount.default_discount_purchase_account_id', 
                                                                              default='False'))
        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.with_context(ctx).write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id
            
            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)
            #modification by TIS for discount entry
            discount = inv.amount_discount
            if inv.amount_discount:
                if inv.type in ('in_invoice', 'in_refund'):
                    total = total + discount
                    total_currency = total_currency + discount
                    acc_id = discount_purchase_account_id
                    discount = - discount
                    if(not discount_purchase_account_id):
                        raise UserError(_('Please define discount purchase account on settings'))
                else:
                    total = total - discount
                    acc_id = discount_sales_account_id
                    total_currency = total_currency - discount
                    if(not discount_sales_account_id):
                        raise UserError(_('Please define discount sales account on settings'))

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = inv.date or inv.date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
                    #discount line
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': discount,
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'account_analytic_id': inv.analytic_id.id or '',
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
                    
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
                #discount line
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': discount,
                    'account_id': acc_id,
                    'account_analytic_id': inv.analytic_id.id or '',
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and amount_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
                
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True
