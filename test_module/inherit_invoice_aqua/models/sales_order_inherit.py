# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'
    tax_type = fields.Selection([
        ('tax_sale', 'Tax Sale'),
        ('non_tax_sale', 'Non Tax Sale')], string='Tax Sale/ Non Tax Sale')
    job_costing_code = fields.Char('Job Costing Code', required=False, translate=True)
    delivery_date = fields.Date(string='Delivery Date', readonly=False)
    installation_date = fields.Date(string='Installation Date', readonly=False)


SalesOrderInherit()
