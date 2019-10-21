# -*- coding: utf-8 -*-
# Copyright (C) 2016-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
from openerp import api, fields, models, _

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    cashier_id = fields.Many2one('res.users', related='session_id.user_id', string='Cashier', store=True)