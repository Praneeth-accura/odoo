# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class InheritInvoice(models.Model):
    _inherit = 'account.invoice'
    arava_vessel = fields.Char('Name of the Vessel', required=False, translate=True)
    arava_freight = fields.Char('Freight', required=False, translate=True)
    arava_shipping_mark = fields.Char('Shipping Mark', required=False, translate=True)
    arava_shipment = fields.Char('Port Of Shipment', required=False, translate=True)
    arava_discharge = fields.Char('Port Of Discharge', required=False, translate=True)
    arava_shipping_payment = fields.Char('Payment Term Of Shipment', required=False, translate=True)


InheritInvoice()
