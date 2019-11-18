# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import models, api, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    module_pos_return = fields.Boolean('Return Order')
    days_return = fields.Integer('Return Days', default=15)
    refund_order = fields.Boolean('Refund Orders')