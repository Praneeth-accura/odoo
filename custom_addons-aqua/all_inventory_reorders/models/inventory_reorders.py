from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError


class InventoryReorders(models.Model):
    _name = 'inventory.reorders'

    po_number = fields.Char(string='PO Number')
    item = fields.Many2one('product.product', string='Item')
    current_quantity = fields.Float(string='Current Quantity')
    reorder_quantity = fields.Float(string='Reorder Quantity')
    status = fields.Char(string='Status')
    date = fields.Date(string='Date')


class InventoryReordersMail(models.Model):
    _name = 'inventory.reorders.mail'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='Reorder Emails')
    employee_ids = fields.Many2many('hr.employee', 'inventory_reorders_mail_rel')
    mail_addresses = fields.Char(string="Mail addresses")

    # get individual employees email addresses when is change
    @api.onchange('employee_ids')
    def get_mail_addresses(self):
        if self.employee_ids:
            self.mail_addresses = (','.join(e.work_email for e in self.employee_ids))
        else:
            self.mail_addresses = []

    # eliminate multiple record creation
    @api.model
    def create(self, vals):
        records = self.search([])
        if len(records) == 0:
            return super(InventoryReordersMail, self).create(vals)
        else:
            raise UserError('You cannot create another record')

    # eliminate record deletion
    @api.multi
    def unlink(self):
        raise UserError('You cannot delete a Record')
        return super(InventoryReordersMail, self).unlink()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_collect = fields.Boolean(string='Is Reported', default=False)


class ReorderLines(models.Model):
    _name = 'reorder.lines'

    po_number = fields.Char(string='PO Number')
    item = fields.Many2one('product.product', string='Item')
    current_quantity = fields.Float(string='Current Quantity')
    reorder_quantity = fields.Float(string='Reorder Quantity')
    status = fields.Char(string='Status')
    date = fields.Date(string='Date')
    line_id = fields.Many2one('reorder')
    reorder_min = fields.Float(string='Reorder Min')
    reorder_max = fields.Float(string='Reorder Max')


class Reorder(models.Model):
    _name = 'reorder'

    emails = fields.Char(string='emails')
    reorder_lines = fields.One2many('reorder.lines', 'line_id')


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    # get reordering lines
    @api.multi
    def get_all_reorders(self):
        purchase_orders = self.env['purchase.order'].search([('origin', '!=', 'false')], order='id asc')
        emails = self.env['inventory.reorders.mail'].search([('id', '=', 1)], limit=1).mail_addresses

        # delete previous reordering_lines from database
        for reorder_lines in self.env['reorder.lines'].search([]):
            reorder_lines.unlink()

        # delete previous reorders from database
        for reorder in self.env['reorder'].search([]):
            reorder.unlink()

        # create new reorder
        obj = self.env['reorder'].create({
            'emails': emails
        })

        for order in purchase_orders:
            for order_line in order.order_line:
                if order_line.product_id.orderpoint_ids:
                    if not order_line.is_collect:
                        line = {
                            'po_number': order.name,
                            'status': order.state,
                            'date': datetime.strptime(order_line.date_order, '%Y-%m-%d %H:%M:%S').date(),
                            'item': order_line.product_id.id,
                            'current_quantity': order_line.product_id.qty_available,
                            'reorder_quantity': order_line.product_qty,
                        }
                        # create new inventory_reorder
                        self.env['inventory.reorders'].create(line)

                        data = {
                            'line_id': obj.id,
                            'po_number': order.name,
                            'status': order.state,
                            'date': datetime.strptime(order_line.date_order, '%Y-%m-%d %H:%M:%S').date(),
                            'item': order_line.product_id.id,
                            'current_quantity': order_line.product_id.qty_available,
                            'reorder_quantity': order_line.product_qty,
                            'reorder_min': order_line.product_id.product_tmpl_id.reordering_min_qty,
                            'reorder_max': order_line.product_id.product_tmpl_id.reordering_max_qty,
                        }
                        # create new reorder_line
                        self.env['reorder.lines'].create(data)

                        # if record is hit to inventory_reorders set value true
                        order_line.write({'is_collect': True})

        try:
            # get all reorder lines
            data = self.env['reorder.lines'].search([])

            # check if there any new reorder_lines then send a mail
            if len(data) > 0:
                template_id = self.env.ref('all_inventory_reorders.email_template_daily_reorders')
                self.env['mail.template'].browse(template_id.id).send_mail(obj.id, True)

        except Exception as error:
            print(error)



