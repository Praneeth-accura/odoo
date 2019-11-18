# -*- coding: utf-8 -*-
# Copyright (C) 2018-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    discount_fixed = fields.Float(string='Cash Discount', default=5, help='The default fixed cash discount')

    @api.onchange('module_pos_discount')
    def _onchange_module_pos_discount(self):
        res = super(PosConfig, self)._onchange_module_pos_discount()
        if self.module_pos_discount:
            self.discount_product_id = self.env['product.product'].search([('available_in_pos', '=', True)], limit=1)
            self.discount_fixed = 5
        else:
            self.discount_product_id = False
            self.discount_fixed = 0.0
        return res
