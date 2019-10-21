# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    payslip_modify = fields.Boolean('Enable Payslip Modification', deafult=False)
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('payslip_modify', (self.payslip_modify))
        self.onchange_payslip_modify()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            payslip_modify=get_param('payslip_modify', default=False),
        )
        return res
    
    @api.onchange('payslip_modify')
    def onchange_payslip_modify(self):
        payslips = self.env['hr.payslip'].search([])
        for payslip in payslips:
            if self.payslip_modify == True:
                payslip.modify_payslip = True
            elif self.payslip_modify == False:
                payslip.modify_payslip = False
                
                
