# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    config_emp_code = fields.Selection([('manual','Manual'),('auto','Automated')],
                                         string='Employee Code Configuration', default='manual')
    prefix = fields.Char('Prefix')
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('config_emp_code', (self.config_emp_code))
        set_param('prefix', (self.prefix))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            config_emp_code=get_param('config_emp_code', default=''),
            prefix=get_param('prefix', default=''),
        )
        return res
