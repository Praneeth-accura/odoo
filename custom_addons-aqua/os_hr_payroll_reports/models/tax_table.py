# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class TaxTable(models.Model):
    _name = 'tax.table'
    
    name = fields.Char('Name')
    remuneration_range_ids = fields.One2many('remuneration.range', 'tax_table_id', string='Remuneration Range')
    
    
class RemunerationRange(models.Model):
    _name = 'remuneration.range'
    
    range_from = fields.Float('From')
    range_to = fields.Float('To')
    amount_tax = fields.Float('Tax')
    tax_table_id =fields.Many2one('tax.table', string='Tax Table')
    
