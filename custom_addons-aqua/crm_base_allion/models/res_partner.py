from datetime import datetime, timedelta
from odoo import api, fields, models, _
import time


class ResPartner(models.Model):

    _description = "Adding new fields to the contact form"
    _inherit = 'res.partner'

    assigned_departments = fields.Many2many('crm.departments', 'crm_departments_res_partner_rel', 'partner_id',
                                            'department_id', string='Assigned Department')
    other_name = fields.Char(string="Other Name")


