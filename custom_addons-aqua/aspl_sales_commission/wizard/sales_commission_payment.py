# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime


class SalesCommissionPayment(models.TransientModel):
    _name = 'sales.commission.payment'

    @api.multi
    def generate_invoice(self):
        invoice_obj = self.env['account.invoice']
        domain = [('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                  '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel')]
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning(_('End Date should be greater than Start Date.'))
            domain.append(('commission_date', '>=', self.start_date))
            domain.append(('commission_date', '<=', self.end_date))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        commission_ids = self._context.get('commission_ids')
        if not commission_ids:
            commission_ids = self.env['sales.commission'].search(domain)
        journal_id = invoice_obj.with_context({'type': 'in_invoice', 'journal_type': 'purchase',
                                               'company_id': self.env.user.company_id.id})._default_journal()
        if not journal_id:
            raise Warning(_('Account Journal not found.'))
        IrDefault = self.env['ir.default'].sudo()
        commission_account_id = IrDefault.get('res.config.settings', "commission_account_id", company_id=self.env.user.company_id.id)
        if not commission_account_id:
            raise Warning(_('Commission Account is not Found. Please go to Sales Configuration and set the Sales commission account.'))
        else:
            account_id = self.env['account.account'].search([('id', '=', commission_account_id)])
            if not account_id:
                raise Warning(_('Commission Account is not Found. Please go to Sales Configuration and set the Sales commission account.'))
        if account_id:
            inv_line_data = []
            for commid in commission_ids:
                inv_line_data.append((0, 0, {'account_id': account_id.id,
                                             'name': commid.name + " Commission",
                                             'quantity': 1,
                                             'price_unit': commid.amount,
                                             'sale_commission_id': commid.id}))
            if inv_line_data:
                invoice_vals = {'partner_id': self.user_id.partner_id.id,
                                'company_id': self.env.user.company_id.id,
                                'commission_invoice': True,
                                'type': 'in_invoice',
                                'journal_id': journal_id.id,
                                'invoice_line_ids': inv_line_data,
                                'origin': 'Commission Invoice',
                                'date_due': datetime.today().date(),
                                }
                invoice_id = invoice_obj.search(
                    [('partner_id', '=', self.user_id.partner_id.id), ('state', '=', 'draft'),
                     ('type', '=', 'in_invoice'), ('commission_invoice', '=', True),
                     ('company_id', '=', self.env.user.company_id.id)])
                if invoice_id:
                    invoice_id.write({'invoice_line_ids': inv_line_data, 'commission_invoice': True})
                else:
                    invoice_id = invoice_obj.create(invoice_vals)
                    invoice_id._onchange_partner_id()
                for commid in commission_ids:
                    commid.write({'invoice_id': invoice_id.id, 'state': 'invoiced'})

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    user_id = fields.Many2one('res.users', string="User", required=True)


class wizard_commission_summary(models.TransientModel):
    _name = 'wizard.commission.summary'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    job_ids = fields.Many2many('hr.job', string="Job")
    user_ids = fields.Many2many('res.users', string="User(s)")

    @api.onchange('job_ids')
    def onchange_job(self):
        res = {'value': {'user_ids': False}}
        if self.job_ids:
            job_lst = [job.id for job in self.job_ids]
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', 'in', job_lst)])
            user_lst = list(set([emp.user_id.id for emp in emp_ids]))
            res.update({'domain': {'user_ids': [('id', 'in', user_lst)]}})
            if self.env.context.get('ctx_job_user_report_print'):
                return user_lst
        return res

    @api.multi
    def get_users_commission(self):
        result = {}
        user_ids = [user.id for user in self.user_ids or self.env['res.users'].search([])]
        if not self.user_ids and self.job_ids:
            user_ids = self.with_context({'ctx_job_user_report_print': True}).onchange_job()
        domain = [('state', '=', 'paid'), ('user_id', 'in', user_ids)]
        if self.start_date and self.end_date:
            domain.append(('commission_date', '>=', str(self.start_date)))
            domain.append(('commission_date', '<=', str(self.end_date)))
        for commid in self.env['sales.commission'].search(domain, order="commission_date"):
            vals = {'name': commid.name,
                    'date': commid.commission_date,
                    'user_name': commid.user_id.name,
                    'amount': commid.amount,
                    'pay_by': 'Invoice' if commid.pay_by == 'invoice' else 'Salary'}
            if commid.user_id.id in result:
                result[commid.user_id.id].append(vals)
            else:
                result.update({commid.user_id.id: [vals]})
        if not result:
            raise Warning(_('Sales Commission Details not found.'))
        return result

    @api.multi
    def print_commission_report(self):
        if self.start_date > self.end_date:
            raise Warning(_('End Date should be greater than Start Date.'))
        datas = {
            'ids': self._ids,
            'model': 'wizard.commission.summary',
            'form': self.read()[0],
            'commission_details': self.get_users_commission()
        }
        return self.env.ref('aspl_sales_commission.report_print_commission_summary').report_action(self, data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: