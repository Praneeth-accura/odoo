# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import api, fields, models


class InheritCustomWebsite(models.TransientModel):
    _inherit = 'res.config.settings'
    test_field = fields.Char('Test', required=False, translate=True)


InheritCustomWebsite()