# -*- coding: utf-8 -*-
# Copyright (C) 2019-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class StockInventoryLineInherit(models.Model):
    _inherit = 'stock.inventory.line'
    different_qty = fields.Float("Difference Qty", compute='_compute_diff1', store=True)
    standard_prices = fields.Float(strore=True, compute='_product_cost')
    cost_prices = fields.Float("Value Difference", compute='_compute_cost', store=True)

    @api.one
    @api.depends('product_qty', 'theoretical_qty')
    def _compute_diff1(self):
        for record in self:
            record.different_qty = record.product_qty - record.theoretical_qty

    @api.one
    @api.depends('product_id', 'state')
    def _product_cost(self):
        for record in self:
            record.standard_prices = record.product_id.standard_price

    @api.one
    @api.depends('standard_prices', 'different_qty', 'state')
    def _compute_cost(self):
        for record in self:
            record.cost_prices = record.standard_prices * record.different_qty


StockInventoryLineInherit()




