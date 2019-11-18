from odoo import api, fields, models, tools
from datetime import datetime, timedelta


class PosOrder(models.Model):
    _inherit = "pos.order"

    order_date_with_tz = fields.Datetime(string='Order Date with TZ', compute='_set_date_time')
    total_discount = fields.Float(compute='_total_discount', string='Discount')

    @api.multi
    @api.depends('date_order')
    def _set_date_time(self):
        self.order_date_with_tz = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)


    @api.multi
    @api.depends('amount_total')
    def _total_discount(self):
        discount = 0
        if self.lines:
            for line in self.lines:
                discount += (line.discount / 100) * (line.price_unit * line.qty)

            self.total_discount = discount

