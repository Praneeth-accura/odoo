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
from datetime import datetime
from odoo.exceptions import Warning


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if res:
            res.update({'commission_calc': self.env[self._context.get('active_model')].browse(self._context.get('active_id')).commission_calc,
                        'commission_pay_on': self.env[self._context.get('active_model')].browse(self._context.get('active_id')).commission_pay_on})
        return res

 
class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        comm_obj = self.env['sales.commission']
        sale_obj = self.env['sale.order']
#         commission_pay_on = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission.commission_pay_on')
        commission_pay_by = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission.commission_pay_by')
        member_lst = []
        if self.commission_calc and self.commission_pay_on == 'invoice_validate':
            emp_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            sale_id = False
            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
            if emp_id and sale_id:
                if self.commission_calc == 'product':
                    for invline in self.invoice_line_ids:
                        for lineid in invline.product_id.product_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                            if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                                lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if self.user_id.id in self.job_related_users(lineid.job_id):
                                    lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                    member_lst.append(lines)
                                    break
                elif self.commission_calc == 'product_categ':
                    for invline in self.invoice_line_ids:
                        for lineid in invline.product_id.categ_id.prod_categ_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                            if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                                lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                member_lst.append(lines)
                                break
                            elif lineid.job_id and not lineid.user_ids:
                                if self.user_id.id in self.job_related_users(lineid.job_id):
                                    lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                    member_lst.append(lines)
                                    break
                elif self.commission_calc == 'customer' and self.partner_id:
                    for lineid in self.partner_id.comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                        if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                            member_lst.append(lines)
                            break
                        elif lineid.job_id and not lineid.user_ids:
                            if self.user_id.id in self.job_related_users(lineid.job_id):
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                member_lst.append(lines)
                                break
                elif self.commission_calc == 'sale_team' and self.team_id:
                    for lineid in self.team_id.sale_team_comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id}
                        if lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]:
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                            member_lst.append(lines)
                            break
                        elif lineid.job_id and not lineid.user_ids:
                            if self.user_id.id in self.job_related_users(lineid.job_id):
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                member_lst.append(lines)
                                break

            userby = {}
            for member in member_lst:
                if member['user_id'] in userby:
                    userby[member['user_id']]['commission'] += member['commission']
                else:
                    userby.update({member['user_id']: member})
            member_lst = []
            for user in userby:
                member_lst.append((0, 0, userby[user]))
            self.sale_order_comm_ids = False
            self.sale_order_comm_ids = member_lst

            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                if sale_id:
                    for commline in self.sale_order_comm_ids:
                        vals = {'name': sale_id.name,
                                'user_id': commline.user_id.id,
                                'commission_date': datetime.today().date(),
                                'amount': commline.commission,
                                'reference_invoice_id': invoice.id,
                                'sale_order_id': sale_id.id,
                                'pay_by': commission_pay_by or 'invoice'}
                        comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                    ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel'),
                                                    ('reference_invoice_id', '=', invoice.id)])
                        total_paid_amount = sum(comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                        if total_paid_amount <= commline.commission:
                            vals['amount'] = commline.commission - total_paid_amount
                        comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                        if vals['amount'] != 0.0:
                            comm_obj.create(vals)
        return res

    commission_invoice = fields.Boolean(string="Commission Invoice")
    sale_order_comm_ids = fields.One2many('sales.order.commission', 'invoice_id', string="Sale Order Commission",
                                          store=True, readonly=True)
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation", copy=False,
                                       readonly=True)
    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Commission Pay On",
                                         readonly=True, copy=False)

    @api.multi
    def action_invoice_cancel(self):
        res = super(account_invoice, self).action_invoice_cancel()
        comm_obj = self.env['sales.commission']
        for invoice in self:
            if invoice.commission_invoice:
                comm_ids = comm_obj.search([('invoice_id', '=', invoice.id), ('state', 'not in', ['cancel', 'paid'])])
                comm_ids.write({'state': 'draft', 'invoice_id': False})
        return res

    @api.multi
    def action_invoice_draft(self):
        res = super(account_invoice, self).action_invoice_draft()
        comm_obj = self.env['sales.commission']
        for invoice in self:
            if invoice.commission_invoice:
                for line in invoice.invoice_line_ids.filtered(lambda l: l.sale_commission_id):
                    if line.sale_commission_id.invoice_id:
                        raise Warning(_('Invoice cannot set as a Draft, because related commission lines assign to %s Invoice.') % (line.sale_commission_id.invoice_id.number or 'another'))
                    else:
                        if line.sale_commission_id.state == 'cancel':
                            raise Warning(_('Invoice cannot set as a Draft, because %s commission line is Cancelled.') % (line.sale_commission_id.name))
                        line.sale_commission_id.write({'state': 'invoiced', 'invoice_id': invoice.id})
        return res


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    sale_commission_id = fields.Many2one('sales.commission', string="Sale Commission", readonly=True)

    @api.multi
    def unlink(self):
        for line in self.filtered(lambda l:l.sale_commission_id):
            if line.sale_commission_id.invoice_id.id == line.invoice_id.id:
                line.sale_commission_id.write({'state': 'draft', 'invoice_id': False})
        return super(account_invoice_line, self).unlink()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        comm_obj = self.env['sales.commission']
        sale_obj = self.env['sale.order']
#         commission_pay_on = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission.commission_pay_on')
        commission_pay_by = self.env['ir.config_parameter'].sudo().get_param('aspl_sales_commission.commission_pay_by')

        for rec in self:
            for invoice in rec.invoice_ids:
                if invoice.commission_invoice and invoice.state == 'paid':
                    sale_commission = comm_obj.search([('invoice_id', '=', invoice.id)])
                    sale_commission.write({'state': 'paid'})
                elif not invoice.commission_invoice and invoice.commission_pay_on == 'invoice_pay' and invoice.state == 'paid':
                    member_lst = []
                    emp_id = self.env['hr.employee'].search([('user_id', '=', invoice.user_id.id)], limit=1)
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    if emp_id and sale_id:
                        if invoice.commission_calc == 'product':
                            for invline in invoice.invoice_line_ids:
                                for lineid in invline.product_id.product_comm_ids:
                                    lines = {'user_id': invoice.user_id.id, 'job_id': emp_id.job_id.id}
                                    if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                        lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                                    elif lineid.job_id and not lineid.user_ids:
                                        if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                            lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                            member_lst.append(lines)
                                            break
                        elif invoice.commission_calc == 'product_categ':
                            for invline in invoice.invoice_line_ids:
                                for lineid in invline.product_id.categ_id.prod_categ_comm_ids:
                                    lines = {'user_id': invoice.user_id.id, 'job_id': emp_id.job_id.id}
                                    if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                        lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                        member_lst.append(lines)
                                        break
                                    elif lineid.job_id and not lineid.user_ids:
                                        if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                            lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                            member_lst.append(lines)
                                            break
                        elif invoice.commission_calc == 'customer' and invoice.partner_id:
                            for lineid in invoice.partner_id.comm_ids:
                                lines = {'user_id': invoice.user_id.id, 'job_id': emp_id.job_id.id}
                                if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                        lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                        member_lst.append(lines)
                                        break
                        elif invoice.commission_calc == 'sale_team' and invoice.team_id:
                            for lineid in invoice.team_id.sale_team_comm_ids:
                                lines = {'user_id': invoice.user_id.id, 'job_id': emp_id.job_id.id}
                                if lineid.user_ids and invoice.user_id.id in [user.id for user in lineid.user_ids]:
                                    lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                    member_lst.append(lines)
                                    break
                                elif lineid.job_id and not lineid.user_ids:
                                    if invoice.user_id.id in self.job_related_users(lineid.job_id):
                                        lines['commission'] = invoice.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * invoice.amount_total) / sale_id.amount_total
                                        member_lst.append(lines)
                                        break

                    userby = {}
                    for member in member_lst:
                        if member['user_id'] in userby:
                            userby[member['user_id']]['commission'] += member['commission']
                        else:
                            userby.update({member['user_id']: member})
                    member_lst = []
                    for user in userby:
                        member_lst.append((0, 0, userby[user]))
                    invoice.sale_order_comm_ids = False
                    invoice.sale_order_comm_ids = member_lst

                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    if sale_id:
                        if all([inv.state == 'paid' for inv in sale_id.invoice_ids]) and sale_id.invoice_status != 'to invoice':
                            for commline in invoice.sale_order_comm_ids:
                                vals = {'name': sale_id.name,
                                        'user_id': commline.user_id.id,
                                        'commission_date': datetime.today().date(),
                                        'amount': commline.commission,
                                        'reference_invoice_id': invoice.id,
                                        'sale_order_id': sale_id.id,
                                        'pay_by': commission_pay_by or 'invoice'}
                                comm_ids = comm_obj.search([('user_id', '=', commline.user_id.id),
                                                            ('sale_order_id', '=', sale_id.id), ('state', '!=', 'cancel'),
                                                            ('reference_invoice_id', '=', invoice.id)])
                                total_paid_amount = sum(comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
                                if total_paid_amount <= commline.commission:
                                    vals['amount'] = commline.commission - total_paid_amount
                                comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
                                if vals['amount'] != 0.0:
                                    comm_obj.create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: