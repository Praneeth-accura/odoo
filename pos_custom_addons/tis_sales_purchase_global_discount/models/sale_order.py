# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.depends('amount_untaxed','amount_tax','discount_type','discount_rate')
    def _amount_all(self):
        res = super(SaleOrder, self)._amount_all()
        for order in self:
            order.amount_grand = order.amount_total
            if(order.discount_type=='percent'):
                order.amount_discount = round((order.amount_grand * order.discount_rate / 100),2)
            elif(order.discount_type=='amount'):
                order.amount_discount = order.discount_rate
            if(order.amount_grand > order.amount_discount):
                order.amount_total = order.amount_grand - order.amount_discount
        return res
    
    discount_type = fields.Selection([('percent', 'Percentage'),('amount', 'Amount')], 'Discount Type',
                        readonly=True, states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', 
                        readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_grand = fields.Float(string='Total', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_total = fields.Float(string='Net Total', digits=dp.get_precision('Account'),
                        store=True, readonly=True, compute='_amount_all')
    
    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'discount_type': self.discount_type or '',
            'discount_rate': self.discount_rate or '',
            'discount_narration': self.discount_narration or '',
            'analytic_id': self.analytic_id.id or '',
            })
        return res
