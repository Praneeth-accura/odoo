# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models, _


class StockInventoryLineInherit(models.Model):
    _inherit = 'stock.inventory.line'
    different_qty = fields.Float("Difference Qty", compute='_compute_diff1', store=True)

    @api.one
    @api.depends('product_qty', 'theoretical_qty')
    def _compute_diff1(self):
        for record in self:
            record.different_qty = record.product_qty - record.theoretical_qty


StockInventoryLineInherit()




