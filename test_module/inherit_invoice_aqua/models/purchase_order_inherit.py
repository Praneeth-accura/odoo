# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'
    mode_of_shipping = fields.Selection([
        ('air', 'Air'),
        ('sea', 'Sea')], string='Mode Of Shipping')

    pricing_method = fields.Selection([
        ('fob', 'FOB'),
        ('cif', 'CIF')], string='Pricing Method')


PurchaseOrderInherit()
