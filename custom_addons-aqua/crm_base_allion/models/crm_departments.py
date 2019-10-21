from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time


class CrmDepartments(models.Model):

    _name = "crm.departments"
    _description = "Departments for CRM use"
    _inherit = ['mail.thread']

    name = fields.Char(string='Department Name', required=True)
    active = fields.Boolean(string='Active', required=False, default=True)
    description = fields.Text(string='Description')
    user_id = fields.Many2one('res.users', string='Department Leader', index=True,
                              default=lambda self: self.env.user, required=True)

    @api.multi
    def unlink(self):
        for x in self:
            self.env.cr.execute('SELECT partner_id FROM crm_departments_res_partner_rel WHERE '
                                'department_id = %s ', [x.id])
            data = self.env.cr.fetchall()
            if data:
                raise UserError(_('You are trying to delete a record that is still referenced!'))
        return super(CrmDepartments, self).unlink()