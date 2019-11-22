# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order.line'
    gross_weight = fields.Float("Gross Weight", store=True)
    deduction = fields.Float("Deduction %", store=True)
    gross_mul_ded = fields.Float("gross*deduction", compute='_compute_deduction', store=True)

    @api.onchange('gross_weight', 'deduction')
    @api.depends('state', 'gross_weight', 'deduction', 'product_qty')
    def _compute_deduction(self):
        for record in self:
            if record.deduction == 0:
                record.product_qty = record.gross_weight
            else:
                record.product_qty = ((100 - record.deduction) * record.gross_weight) / 100


PurchaseOrderInherit()



