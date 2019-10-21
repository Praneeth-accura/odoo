from odoo import api, fields, models, tools
from datetime import datetime, timedelta


class PosOrder(models.Model):
    _inherit = "pos.order"

    order_date_with_tz = fields.Datetime(string='Order Date with TZ', compute='_set_date_time')

    @api.multi
    @api.depends('date_order')
    def _set_date_time(self):
        self.order_date_with_tz = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)

