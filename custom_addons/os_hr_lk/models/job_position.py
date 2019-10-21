# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from odoo.osv import expression

class Job(models.Model):
    _inherit = "hr.job"
    
    code = fields.Char(string='Job Code')
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', ('name', operator, name), ('code', operator, name)]
            ])
            return self.search(domain, limit=limit).name_get()
        return super(Job, self).name_search(name, args, operator, limit)
    