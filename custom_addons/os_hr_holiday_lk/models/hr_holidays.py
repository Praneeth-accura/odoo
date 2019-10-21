# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.translate import _

class Holidays(models.Model):
    _inherit = "hr.holidays"
    
    @api.multi
    def action_approve(self):
        for holiday in self:
            if holiday.holiday_type == 'employee' and holiday.type == 'remove' and not holiday.employee_id.parent_id:
                raise UserError(_('Please define Reporting Manager in Employee Master.'))
            else:
                if holiday.employee_id.parent_id and holiday.employee_id.parent_id.user_id:
                    if holiday._uid == holiday.employee_id.parent_id.user_id.id:
                        return super(Holidays, self).action_approve()
                    else:
                        raise UserError(_('Only respective managers can approve the leave.'))
                else:
                    raise UserError(_('Please define related User for Manager.'))
                
    @api.multi
    def action_validate(self):
        for holiday in self:
            if holiday.holiday_type == 'employee' and holiday.type == 'remove' and not holiday.employee_id.coach_id:
                raise UserError(_('Please define Coach/ Second Reporting Manager in Employee Master.'))
            else:
                if holiday.employee_id.coach_id and holiday.employee_id.coach_id.user_id:
                    if holiday._uid == holiday.employee_id.coach_id.user_id.id:
                        return super(Holidays, self).action_validate()
                    else:
                        raise UserError(_('Only respective managers can approve the leave.'))
                else:
                    raise UserError(_('Please define related User for Coach/ Second Manager.'))
                
    @api.multi
    def add_follower(self, employee_id):
        res = super(Holidays, self).add_follower(employee_id)
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.parent_id and employee.parent_id.user_id:
            self.message_subscribe_users(user_ids=employee.parent_id.user_id.ids)
        if employee.coach_id and employee.coach_id.user_id:
            self.message_subscribe_users(user_ids=employee.coach_id.user_id.ids)
        return res
    
