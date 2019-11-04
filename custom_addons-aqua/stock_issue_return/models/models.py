# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_utils
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ChargeType(models.Model):
    _name = 'charge.type'

    name = fields.Char(string="Charge Type", required=True)
    account_control_ids = fields.Many2one('account.account', column1='journal_id', column2='account_id',
                                          string="Account Allowed")


class ItemIssueReturn(models.Model):
    _name = 'item.issue.return'

    # def _get_default_scrap_location_id(self):
    #     return self.env['stock.location'].search([('scrap_location', '=', True),('name', '=', 'scrape1')], limit=1).id
    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search(
            [('scrap_location', '=', True), ('company_id', 'in', [self.env.user.company_id.id, False])], limit=1).id


    def _get_default_location_id(self):
        return self.env['stock.location'].search(
            [('usage', '=', 'internal'), ('company_id', 'in', [self.env.user.company_id.id, False])], limit=1).id

    name = fields.Char('Issuance Number', required=True, index=True, copy=False, default='New', readonly=True)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id)
    legacy_ref_no = fields.Char('Legacy reference no.')
    location_id = fields.Many2one(
        'stock.location', 'Location', required=True, default=_get_default_location_id)
    date = fields.Date(string='Date', default=fields.Datetime.now, required=True)
    type = fields.Selection(selection=[('issue', 'Issue'), ('return', 'Return'),
                                       ('transfer_in', 'Transfer IN'), ('transfer_out', 'Transfer Out')], default='issue', required=True)
    state = fields.Selection([('draft', 'New'), ('confirm', 'Done')], string='Status', default='draft')
    itemlines = fields.One2many('item.issue.return.lines', 'item_issuance_return_Id', string="Item Lines")



    @api.model
    def create(self, vals):
        current_time = datetime.datetime.now()
        year = current_time.year    
        month = datetime.datetime.strptime(vals['date'], '%Y-%m-%d')
        if vals.get('name', 'New') == 'New':
            get_seq = self.env['ir.sequence'].next_by_code('item.issue.return')
            vals['name'] = str(get_seq) + '-' + str(month.month) + '-' + str(year)
            # vals['issuance_no'] = get_seq
        return super(ItemIssueReturn, self).create(vals)

    @api.multi
    def action_confirm(self):
        print("controle entered")
        for record in self:
            if record.type in ('return', 'transfer_in'):
                for line in record.itemlines:
                    price_history_ids = self.env['product.price.history'].search([('product_id','=',line.product_id.id),
                                                                                  ('datetime', '<=', record.date)
                                                                                  ],order="datetime desc",limit=1)
                    if price_history_ids:
                        cost_price = price_history_ids.cost
                        print('cost computed')
                    else:
                        raise ValidationError(_('No product price at date!'))
                    # s = self.env['stock.move'].search([])[0]
                    move = self.env['stock.move'].create({
                        'name': record.name,
                        'product_id': line.product_id.id,
                        'issuance_date': record.date,
                        'is_issuance': True,
                        'date_expected': record.date,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.scrap_quantity,
                        'location_id': record.scrap_location_id.id,
                        'location_dest_id': record.location_id.id,
                        'price_unit': cost_price,
                    })
                    analytic_account_id = line.analytic_account_id.id
                    analytic_tag_ids = line.analytic_tag_ids.ids
                    if line.charge_type.name == 'Default' or line.charge_type.name == 'default':

                        if line.product_id.property_account_expense_id:
                            credit_account_id = line.product_id.property_account_expense_id.id
                        else:
                            credit_account_id = line.product_id.categ_id.property_account_expense_categ_id.id
                    else:
                        credit_account_id = line.charge_type.account_control_ids.id
                    debit_account_id = line.product_id.categ_id.property_stock_valuation_account_id.id

                    move._action_confirm()
                    move._action_assign()
                    for mlids in move.move_line_ids:
                        mlids.qty_done = line.scrap_quantity
                    # move.move_line_ids.qty_done = line.scrap_quantity
                    move._action_done()
                    move.write({'date': record.date, })
                    # search_account_ids = self.env['account.move'].search([])
                    # last_id = search_account_ids and max(search_account_ids.ids)
                    move_id = self.env['account.move'].search([('stock_move_id', '=', move.id)], limit=1)
                    if move_id:
                        move_id.write({'state': 'draft',
                                       'date': record.date,
                                       })
                        for val in move_id.line_ids:
                            if val.debit == False or 0.00:
                                val.write({'account_id': credit_account_id,
                                           'analytic_account_id': analytic_account_id,
                                           'analytic_tag_ids': analytic_tag_ids,
                                           })
                            if val.credit == False or 0.00:
                                val.write({'account_id': debit_account_id,
                                           'analytic_account_id': analytic_account_id,
                                           'analytic_tag_ids': analytic_tag_ids,
                                           })
                        move_id.write({'state': 'posted', })
                        print(move_id.name)
                    record.state = 'confirm'
            if record.type in ('issue', 'transfer_out'):
                print("record type", record.type)
                for line in record.itemlines:
                    price_history_ids = self.env['product.price.history'].search(
                        [('product_id', '=', line.product_id.id),
                         ('datetime', '<=', record.date)
                         ], order="datetime desc", limit=1)
                    if price_history_ids:
                        cost_price = price_history_ids.cost
                        print('cost computed')
                    else:
                        raise ValidationError(_('No product price at date!'))
                    move = self.env['stock.move'].create({
                        'name': record.name,
                        'product_id': line.product_id.id,
                        'issuance_date': record.date,
                        'is_issuance': True,
                        'date': record.date,
                        'date_expected': record.date,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.scrap_quantity,
                        'location_id': record.location_id.id,
                        'location_dest_id': record.scrap_location_id.id,
                        'price_unit': cost_price,
                    })

                    analytic_account_id = line.analytic_account_id.id
                    analytic_tag_ids = line.analytic_tag_ids.ids
                    credit_account_id = line.product_id.categ_id.property_stock_valuation_account_id.id
                    if line.charge_type.name == 'Default' or line.charge_type.name == 'default':
                        if line.product_id.property_account_expense_id:
                            debit_account_id = line.product_id.property_account_expense_id.id
                        else:
                            debit_account_id = line.product_id.categ_id.property_account_expense_categ_id.id
                    else:
                        debit_account_id = line.charge_type.account_control_ids.id
                    move._action_confirm()
                    move._action_assign()
                    for mlids in move.move_line_ids:
                        mlids.qty_done = line.scrap_quantity
                    move._action_done()
                    move.write({'date': record.date, })
                    # search_account_ids = self.env['account.move'].search([])
                    # last_id = search_account_ids and max(search_account_ids.ids)
                    move_id = self.env['account.move'].search([('stock_move_id', '=', move.id)], limit=1)
                    if move_id:
                        move_id.write({'state': 'draft',
                                       'date': record.date,
                                       })
                        for val in move_id.line_ids:
                            if val.debit == False or 0.00:
                                # print(analytic_tag_ids)
                                val.write({'account_id': credit_account_id,
                                           'analytic_account_id': analytic_account_id,
                                           'analytic_tag_ids': [(6, 0, analytic_tag_ids)],
                                           })
                            if val.credit == False or 0.00:
                                # print(analytic_tag_ids)
                                val.write({'account_id': debit_account_id,
                                           'analytic_account_id': analytic_account_id,
                                           'analytic_tag_ids': [(6, 0, analytic_tag_ids)],
                                           })
                        move_id.write({'state': 'posted', })
                    # print(move_id.name)
                    record.state = 'confirm'


class ItemIssueReturnLines(models.Model):
    _name = 'item.issue.return.lines'

    def _get_default_charge_type(self):
        return self.env['charge.type'].search(
            [('name', 'in', ('default','Default'))], limit=1).id


    item_issuance_return_Id = fields.Many2one('item.issue.return', string="Issuance Return Id", ondelete='cascade')
    memo_text = fields.Char(string="Memo", required=True)
    legacy_ref_no = fields.Char('Legacy reference no.')
    charge_type = fields.Many2one('charge.type', string="Charge Type", required=True, default=_get_default_charge_type)
    product_id = fields.Many2one(
        'product.product', 'Product', required=True)
    scrap_quantity = fields.Float('Quantity', default=1.0, required=True)
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True)
    onhand_quantity = fields.Float('On-hand Quantity', compute='compute_onhand_quantity', store=True)
    # account_id = fields.Many2one('account.account', string="Account")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    # location_id = fields.Many2one('stock.location', 'Location', required=True)

    @api.onchange('product_id')
    def _onchange_product_uom(self):
        self.product_uoms_id = self.product_id.uom_id.id

    @api.depends('product_id')
    def compute_onhand_quantity(self):
        for line in self:
            if line.product_id and line.item_issuance_return_Id.location_id:
                if line.item_issuance_return_Id.type in ('issue', 'transfer_out'):
                    quant_obj = line.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                ('location_id', '=',
                                                                 line.item_issuance_return_Id.location_id.id)])
                    if quant_obj:
                        line.onhand_quantity = quant_obj.quantity
                    else:
                        raise ValidationError(
                            _("Product stock not available at selected stock location."))
                if line.item_issuance_return_Id.type in ('return', 'transfer_in'):
                    quant_obj = line.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                ('location_id', '=',
                                                                 line.item_issuance_return_Id.location_id.id)])
                    if quant_obj:
                        line.onhand_quantity = quant_obj.quantity


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
#
#     is_shipment_done = fields.Boolean(string='Is Shipment Done', compute='compute_picking_status', default=False)
#
#     @api.depends('picking_ids')
#     def compute_picking_status(self):
#         for order in self:
#             if order.picking_ids:
#                 count_p = 0
#                 ids_length = len(order.picking_ids)
#                 for pick in order.picking_ids:
#                     if pick.state == 'done':
#                         count_p += 1
#                 if count_p == ids_length:
#                     order.is_shipment_done = True

    # @api.multi
    # def _inverse_picking_status(self):
    #     for order in self:
    #         if order.picking_ids:
    #             count_p = 0
    #             # ids_length = len(order.picking_ids)
    #             for pick in order.picking_ids:
    #                 if pick.state != 'done':
    #                     count_p += 1
    #             if count_p > 0:
    #                 order.is_shipment_done = False

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'scheduled_date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }


class StockMove(models.Model):
    _inherit = "stock.move"

    issuance_date = fields.Date('Issuance Date')
    is_issuance = fields.Boolean('Issuance',default=False)
    is_adjustment = fields.Boolean('Adjustment', default=False)

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        value_tmp = self.value
        if self.is_issuance or self.is_adjustment:
            price_history_ids = self.env['product.price.history'].search([('product_id', '=', self.product_id.id),
                                                                      ('datetime', '<=', self.date_expected)
                                                                      ], order="datetime desc", limit=1)
            value_tmp = price_history_ids.cost * self.product_qty
        AccountMove = self.env['account.move']
        # self.purchase_line_id.account_analytic_id
        # self.purchase_line_id.account_analytic_tag
        move_lines = self._prepare_account_move_line(self.product_qty, abs(value_tmp), credit_account_id, debit_account_id)

        for line in move_lines:
            if self.purchase_line_id.account_analytic_id:
                line[2]["analytic_account_id"] = self.purchase_line_id.account_analytic_id.id
            if self.purchase_line_id.analytic_tag_ids:
                line[2]["analytic_tag_ids"] = [(6, 0, self.purchase_line_id.analytic_tag_ids.ids)]


        if move_lines:
            # date = self._context.get('force_period_date', fields.Date.context_today(self))
            date = self.date
            new_account_move = AccountMove.create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': self.picking_id.name,
                'stock_move_id': self.id,
            })
            new_account_move.post()


class StockMoveLine(models.Model):
    """

    """
    _inherit = "stock.inventory.line"
    cost = fields.Integer("Cost")
    date = fields.Datetime(
        'Inventory Date',
        readonly=False, required=True,
        default=fields.Datetime.now,
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")

    def _generate_moves(self):
        moves = self.env['stock.move']
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
            vals['is_adjustment'] = True
            vals['date_expected'] = line.inventory_id.date
            moves |= self.env['stock.move'].create(vals)

            if line.product_id.standard_price == 0:
                prod_obj = self.env['product.template'].search([('id', '=', line.product_id.product_tmpl_id.id)])
                prod_value = {'standard_price': line.cost}
                prod_obj.write(prod_value)
            #     line.product_id._axm_standard_price_trx_date(line.cost, line.inventory_id.date)
            # else:
            #     line.product_id._axm_standard_price_trx_date(line.cost, line.inventory_id.date)

        return moves


class StockPickingCustom(models.Model):
    """

    """
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        self.ensure_one()

        # order_date = fields.datetime.strptime(self.purchase_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
        # scheduled_date = fields.datetime.strptime(self.scheduled_date, DEFAULT_SERVER_DATETIME_FORMAT)
        #
        # if order_date > scheduled_date:
        #     raise UserError(_("Scheduled date should be equal or greater than Order date"))

        return super(StockPickingCustom, self).button_validate()
