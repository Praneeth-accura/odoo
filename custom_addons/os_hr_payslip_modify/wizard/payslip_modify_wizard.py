# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api

class HrPayslipModify(models.TransientModel):
    _name= 'payslip.modify.wizard'
    
    
    def set_payslip_draft(self):
        slip_id = self._context['payslip_id']
        payslip = self.env['hr.payslip'].search([('id','=',slip_id)])
        payslip.action_payslip_draft()
    
    
    
    
    