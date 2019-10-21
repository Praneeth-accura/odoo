from datetime import datetime, timedelta
from odoo import api, fields, models, _
import time


class ResPartner(models.Model):

    _description = "Adding new fields to the contact form"
    _inherit = 'res.partner'

    assigned_technicians = fields.Many2many('crm.helpdesk.technician', 'crm_helpdesk_technician_res_partner_rel',
                                            'partner_id', 'technician_id', string='Assigned Person')
