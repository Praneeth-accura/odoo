# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api

class Job(models.Model):
    _inherit = 'hr.job'

    grade = fields.Char(string='Classification Grade')