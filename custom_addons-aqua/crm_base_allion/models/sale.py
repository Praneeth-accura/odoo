import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = ['sale.order']

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)

        # get the active module
        if self._context.get('active_model') == 'crm.lead':

            # get the active_id
            if self._context.get('active_id'):
                lead_obj = self.env['crm.lead'].browse\
                    (self._context.get('active_id'))

                product_id = self.env['product.product'].search([('product_tmpl_id', '=', lead_obj.product_id.id)])

                values = [(0, 0,
                           {'product_id': product_id.id,
                            'name': product_id.name,
                            'product_uom_qty': 1,
                            'product_uom': 1,
                            'price_unit': lead_obj.product_id.lst_price})]

                res['order_line'] = values

        return res

    @api.multi
    def action_quotation2_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('crm_base_allion', 'email_template_edi_sale_new')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "crm_base_allion.mail_template_data_notification_email_sale_order_new",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
