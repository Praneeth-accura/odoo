from datetime import datetime, timedelta
from odoo import api, fields, models, _
import time


class Lead(models.Model):

    _name = "crm.lead"
    _description = "Adding new fields to the lead form"
    _inherit = ['crm.lead']

    department_id = fields.Many2one(comodel_name='crm.departments', string='Department', required=True)
    date = fields.Date(string='Date', required=True,
                       default=lambda self: self._context.get('date', fields.Date.context_today(self)))
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)
    requirements = fields.Text(string='Requirements')
    additional_info = fields.Text(string='Additional Info')

    @api.multi
    def action_set_lost(self):
        """ Lost semantic: probability = 0, active = False """
        return self.write({'probability': 0, 'active': True})