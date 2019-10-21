# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from datetime import datetime, date
from datetime import timedelta
from odoo.exceptions import UserError
import pytz


class ScheduleHistory(models.Model):
    _name = 'schedule.history'
    _rec_name = 'from_date'
    _order = 'to_date desc'
    
    from_date = fields.Datetime('From', required=1)
    to_date = fields.Datetime('To', required=1)
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Hrs', required=1)
    ot_approve = fields.Boolean('OT Approve', default=False)
    emp_id = fields.Many2one('hr.employee', 'Employee')

    # @api.model
    # def create(self, vals):
    #     if 'from_date' in vals and 'to_date' in vals:
    #         from_date = datetime.strptime(vals.get('from_date'), '%Y-%m-%d %H:%M:%S')
    #         to_date = datetime.strptime(vals.get('to_date'), '%Y-%m-%d %H:%M:%S')
    #         if to_date < from_date:
    #             raise UserError(_('To Date cannot be a backdate against the From Date.'))
    #     # get related work schedule ids
    #     ids = self.search([('emp_id', '=', vals['emp_id'])])
    #     if ids:
    #         for id in ids:
    #             to_date = datetime.strptime(id.to_date, '%Y-%m-%d %H:%M:%S')
    #             from_date = datetime.strptime(vals.get('from_date'), '%Y-%m-%d %H:%M:%S')
    #             if from_date < to_date:
    #                 raise UserError(_('To Date cannot be a backdate against the previous scheduled From Date.'))
    #     return super(ScheduleHistory, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     # Validations
    #     if 'to_date' in vals:
    #         to_date = datetime.strptime(vals.get('to_date'), '%Y-%m-%d %H:%M:%S')
    #         current_from_date = datetime.strptime(self.from_date, '%Y-%m-%d %H:%M:%S')
    #         if to_date < current_from_date:
    #             raise UserError(_('To Date cannot be a backdate against the From Date.'))
    #         ids = self.search([('emp_id', '=', self.emp_id.id)])
    #         if ids:
    #             for id in ids:
    #                 from_date = datetime.strptime(id.from_date, '%Y-%m-%d %H:%M:%S')
    #                 if to_date < from_date:
    #                     raise UserError(_('To Date cannot be a backdate against the previous scheduled From Date.'))
    #     if 'from_date' in vals:
    #         from_date = datetime.strptime(vals.get('from_date'), '%Y-%m-%d %H:%M:%S')
    #         ids = self.search([('emp_id', '=', self.emp_id.id)])
    #         if ids:
    #             for id in ids:
    #                 to_date_eql = datetime.strptime(id.to_date, '%Y-%m-%d %H:%M:%S')
    #                 if id.id != self.id and from_date < to_date_eql:
    #                     raise UserError(_('To Date cannot be a backdate against the previous scheduled From Date.'))
    #     return super(ScheduleHistory, self).write(vals)
    
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    working_history_ids = fields.One2many('schedule.history', 'emp_id', 'Working History', required=1)