# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://technaureus.com/>)

from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def _get_attachment_number(self):
        for employee in self:
            data = self.env['ir.attachment'].search([('res_model', '=', 'hr.employee'),('res_id', '=', employee.id)])
            employee.attachment_number = len(data)

    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")

    @api.multi
    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('employee_document_preview.ir_attachment_view_search_inherit_hr_employee').id, )
        return action

