# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class AccountsInvoiceInherit(models.Model):
    _inherit = 'account.invoice'
    invoice_type = fields.Selection([
        ('tax_invoice', 'Tax Invoice'),
        ('non_tax_invoice', 'Non Tax Invoice')], default="non_tax_invoice", required=True,
        string='Tax Invoice/ Non Tax Invoice')


AccountsInvoiceInherit()
