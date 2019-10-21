# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models
from ast import literal_eval

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_discount_sales_account_id = fields.Many2one('account.account', string='Default Discount Account')
    default_discount_purchase_account_id = fields.Many2one('account.account', string='Default Discount Account')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        default_discount_sales_account_id = literal_eval(ICPSudo.get_param('tis_sales_purchase_global_discount.default_discount_sales_account_id', default='False'))
        default_discount_purchase_account_id = literal_eval(ICPSudo.get_param('tis_sales_purchase_global_discount.default_discount_purchase_account_id', default='False'))
        if default_discount_sales_account_id and not self.env['account.account'].browse(default_discount_sales_account_id).exists():
            default_discount_sales_account_id = False
        if default_discount_purchase_account_id and not self.env['account.account'].browse(default_discount_purchase_account_id).exists():
            default_discount_purchase_account_id = False
        res.update(
             default_discount_sales_account_id=default_discount_sales_account_id,
             default_discount_purchase_account_id=default_discount_purchase_account_id
             )
        return res
         
    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("tis_sales_purchase_global_discount.default_discount_sales_account_id", self.default_discount_sales_account_id.id)
        ICPSudo.set_param("tis_sales_purchase_global_discount.default_discount_purchase_account_id", self.default_discount_purchase_account_id.id)
