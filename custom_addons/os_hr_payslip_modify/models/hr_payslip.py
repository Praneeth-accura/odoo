# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    modify_payslip = fields.Boolean('Enable Payslip Modification',
                                    default=lambda self: self.env['ir.config_parameter'].get_param('payslip_modify'))

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        self.modify_payslip = self.env['ir.config_parameter'].get_param('payslip_modify')
        return res
    
    @api.multi
    def refund_sheet(self):
        res = super(HrPayslip, self).refund_sheet()
        for payslip in self:
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.input_line_ids = payslip.input_line_ids.ids
            copied_payslip.action_payslip_done()
        res.update({'domain': "[('id', 'in', %s)]" % copied_payslip.ids})
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
        ('confirm', 'Confirm')
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    @api.multi
    def generate_batch_payslip(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                slip.action_payslip_done()
            return self.write({'state': 'confirm'})
        else:
            raise ValidationError("There are no Payslips")

