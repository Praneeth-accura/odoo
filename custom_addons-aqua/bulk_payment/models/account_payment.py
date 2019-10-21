# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

MAP_INVOICE_TYPE_PAYMENT_TYPE = {
    'out_invoice': 'inbound',
    'out_refund': 'outbound',
    'in_invoice': 'outbound',
    'in_refund': 'inbound',
}


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.register.payments"

    name = fields.Char(readonly=True, copy=False, default="New Bulk Payment")
    payment_mode = fields.Selection(string='Payment Mode', selection=[
        ('full', 'Full'),
        ('partial', 'Partial'),
    ], default='full', required=True)

    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ])

    payment_lines = fields.One2many(string='Payment Lines', comodel_name='account.register.payment.line',
                                    inverse_name='acc_reg_payment_id')
    lines_total_amount = fields.Monetary(string='Payment Amount', compute='update_lines_total_amount')
    lines_total_amount_in_words = fields.Char(string="Amount in Words")

    manual_check_number = fields.Char(string="Check Number")

    @api.model
    def default_get(self, fields):
        """
        if user select invoices before bulk payment,
        need to load relevant invoices and their amounts with the form view
        """
        rec = super(AccountRegisterPayment, self).default_get(fields)
        active_ids = self._context.get('active_ids')

        # validate for only one partner
        if rec.get('multi', False):
            raise ValidationError('Cannot execute payments for different partners !')

        if active_ids:
            # load payment lines to the form view
            invoices = self.env['account.invoice'].browse(active_ids)
            payment_lines = self._default_payment_lines(invoices)
            invoice_type = invoices[0].type
            rec.update({
                'payment_mode': 'partial',
                'payment_lines': payment_lines,
                'invoice_type': invoice_type,
            })
        return rec

    def _default_payment_lines(self, invoices):
        """
        need to return payment lines by adding given invoice data
        """
        new_payment_lines = []
        for invoice in invoices:
            amount = self._compute_payment_amount([invoice])
            new_payment_lines.append((0, 0, {
                'invoice_id': invoice.id,
                'amount': abs(amount),
            }))
        return new_payment_lines

    def create_partial_payments(self):
        """
        when user click payment button, need to create payments individually
        """

        # need to exist at least one payment line to create bulk payment
        if len(self.payment_lines) == 0:
            raise ValidationError('Please add payment lines')

        # get relevant sequence
        if not self.partner_type:
            self.partner_type = MAP_INVOICE_TYPE_PARTNER_TYPE[self.payment_lines[0].invoice_id.type]
        if self.partner_type == 'customer':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.customer.invoice'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.customer.refund'
        if self.partner_type == 'supplier':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.supplier.refund'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.supplier.invoice'

        self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(sequence_code)

        # create bulk payment
        BulkPayment = self.env['account.bulk.payment'].create({
            'name': self.name,
            'invoice_type': self.invoice_type,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'journal_id': self.journal_id.id,
            'lines_total_amount': self.lines_total_amount,
            'lines_total_amount_in_words': self.lines_total_amount_in_words,
            'check_number': self.journal_id.check_sequence_id.next_by_id() if self.payment_method_code == 'check_printing' and self.check_manual_sequencing is True else 0,
            'manual_check_number': self.manual_check_number,
            'partner_type': self.partner_type,
            'partner_id': self.partner_id.id,
            'payment_type': self.payment_type,
            'payment_method_id': self.payment_method_id.id,
        })

        Payment = self.env['account.payment']
        BulkPaymentLine = self.env['account.bulk.payment.line']
        payments = Payment
        for line in self.payment_lines:
            # create odoo payment
            payment = Payment.create(line.prepare_payment_vals())
            payment.bulk_payment_id = BulkPayment.id
            payments += payment
            # create bulk payment line
            BulkPaymentLine.create({
                'bulk_payment_id': BulkPayment.id,
                'invoice_id': line.invoice_id.id,
                'currency_id': line.currency_id.id,
                'amount': line.amount,
            })

        # post odoo payments
        payments.post()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': BulkPayment.id,
            'res_model': 'account.bulk.payment',
            'target': 'current',
        }

    @api.depends('payment_lines', 'payment_lines.amount')
    def update_lines_total_amount(self):
        """
        update total line amounts
        """
        for payment in self:
            payment.lines_total_amount = sum([line.amount for line in payment.payment_lines if line.amount])

    @api.onchange('journal_id')
    def update_payment_lines_amounts(self):
        """
        if user change journal, need to compute line amounts according to journal currency
        """
        for line in self.payment_lines:
            line.amount = abs(self._compute_payment_amount([line.invoice_id]))

    @api.onchange('lines_total_amount')
    def update_lines_total_amount_in_words(self):
        """
        compute lines total amount in words
        """
        self.lines_total_amount_in_words = self.currency_id.amount_to_text(self.lines_total_amount)


class AccountRegisterPaymentLine(models.TransientModel):
    _name = "account.register.payment.line"

    acc_reg_payment_id = fields.Many2one(string='Account Register Payment', comodel_name='account.register.payments')
    invoice_id = fields.Many2one(string='Invoice/Vendor Bill', comodel_name='account.invoice', required=True)
    currency_id = fields.Many2one(related='acc_reg_payment_id.currency_id')
    amount = fields.Monetary(string='Payment Amount', required=True)

    @api.onchange('invoice_id')
    def update_amount(self):
        """
        if user change invoice in the payment line, need to update the payment amount
        """
        if self.invoice_id:
            self.amount = abs(self.acc_reg_payment_id._compute_payment_amount([self.invoice_id]))

    def create_ref(self):
        """
        return a name with concat bulk payment name and relevant invoice sequence
        """
        bulk_payment_name = self.acc_reg_payment_id.name
        given_ref = self.acc_reg_payment_id.communication
        invoice_seq = self.invoice_id.display_name

        return bulk_payment_name + ' ' + invoice_seq

    def prepare_payment_vals(self):
        """
        return dictionary with including payment line details
        """
        return {
            'journal_id': self.acc_reg_payment_id.journal_id.id,
            'payment_method_id': self.acc_reg_payment_id.payment_method_id.id,
            'payment_date': self.acc_reg_payment_id.payment_date,
            'communication': self.create_ref(),
            'invoice_ids': [(6, 0, [self.invoice_id.id])],
            'payment_type': MAP_INVOICE_TYPE_PAYMENT_TYPE[self.invoice_id.type],
            'amount': abs(self.amount),
            'currency_id': self.currency_id.id,
            'partner_id': self.invoice_id.commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[self.invoice_id.type],
            'check_amount_in_words': self.currency_id.amount_to_text(self.amount)
        }


class BulkPayment(models.Model):
    _name = "account.bulk.payment"

    bulk_payment_lines = fields.One2many(string='Payment Lines', comodel_name='account.bulk.payment.line',
                                         inverse_name='bulk_payment_id')
    payment_ids = fields.One2many(string='Payments', comodel_name='account.payment',
                                  inverse_name='bulk_payment_id')

    name = fields.Char(readonly=True, copy=False)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type',
                                    readonly=True, copy=False)
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ])
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, copy=False)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], readonly=True, copy=False)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', readonly=True, copy=False)
    payment_method_code = fields.Char(related='payment_method_id.code', readonly=True, copy=False)
    check_manual_sequencing = fields.Boolean(related='journal_id.check_manual_sequencing', readonly=True, copy=False)
    manual_check_number = fields.Char(string="Check Number", readonly=True, copy=False)
    check_number = fields.Integer(string="Check Number", readonly=True, copy=False)

    lines_total_amount = fields.Monetary(string='Payment Amount', readonly=True, copy=False)
    lines_total_amount_in_words = fields.Char(string="Amount in Words", readonly=True, copy=False)

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, copy=False)
    payment_date = fields.Date(string='Payment Date', readonly=True, copy=False)
    communication = fields.Char(string='Memo')
    journal_id = fields.Many2one(comodel_name='account.journal', string='Payment Journal', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)


class BulkPaymentLine(models.Model):
    _name = "account.bulk.payment.line"

    bulk_payment_id = fields.Many2one(string='Bulk Payment', comodel_name='account.bulk.payment', readonly=True, copy=False)
    invoice_id = fields.Many2one(string='Invoice/Vendor Bill', comodel_name='account.invoice', readonly=True, copy=False)
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency',  readonly=True, copy=False)
    amount = fields.Monetary(string='Payment Amount', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', related='bulk_payment_id.journal_id.company_id', string='Company', readonly=True, store=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bulk_payment_id = fields.Many2one(string='Bulk Payment', comodel_name='account.bulk.payment')

    def open_bulk_payment(self):
        """
        return action for open relevant bulk payment form view
        """
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.bulk_payment_id.id,
            'res_model': 'account.bulk.payment',
            'target': 'current',
        }


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _enable_check_printing_inbound_on_bank_journals(self):
        """ Enables check printing payment method .
            Called upon module installation via data file.
        """
        check_printing = self.env.ref('bulk_payment.account_payment_method_check_bulk')
        bank_journals = self.search([('type', '=', 'bank')])
        for bank_journal in bank_journals:
            bank_journal.write({
                'inbound_payment_method_ids': [(4, check_printing.id, None)],
            })
