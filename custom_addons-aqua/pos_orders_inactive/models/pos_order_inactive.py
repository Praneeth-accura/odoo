# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


class PosOrder(models.Model):
    _inherit = 'pos.order'

    active = fields.Boolean('Active', default=True)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    active = fields.Boolean('Active', default=True)


class PosOrdersInactive(models.TransientModel):
    _name = 'pos.orders.inactive'

    @api.multi
    def inactive_orders(self):
        # get all pos orders
        pos_orders = self.env['pos.order'].search([])
        today_date = datetime.datetime.now().date()

        for order in pos_orders:
            order_date = datetime.datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()
            difference = (today_date - order_date).days
            if difference > 7:
                for line in order.lines:
                    line.write({'active': False}) # inactive pos order lines in per pos order
                order.write({'active': False}) # inactive pos order

        return True

    @api.multi
    def restore_orders(self):
        # active all pos orders to default
        pos_orders = self.env['pos.order'].search([('active', '=', False)])
        if pos_orders:
            for order in pos_orders:
                order.write({'active': True})

        # active all pos order lines to default
        pos_orders_lines = self.env['pos.order.line'].search([('active', '=', False)])
        if pos_orders_lines:
            for line in pos_orders_lines:
                line.write({'active': True})

        return True

