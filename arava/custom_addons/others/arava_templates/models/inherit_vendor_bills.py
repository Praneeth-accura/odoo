# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class VendorBillsInherit(models.Model):
    _inherit = 'account.invoice.line'
    gross = fields.Char(string='Gross', compute='_product_weight', readonly=True)

    @api.onchange('product_id')
    @api.depends('product_id')
    def _product_weight(self):
        for record in self:
            record.gross = record.product_id.name


VendorBillsInherit()
