from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class AttendanceLog(models.Model):
    _name = 'attendance.log'
    _order = 'punching_time'
    _rec_name = 'punching_time'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    status = fields.Selection([('0', 'Check In'),
                               ('1', 'Check Out'),
                               ('255', 'Undefined')], string='Status', required=True)
    punching_time = fields.Datetime('Punching Time', required=True)
    date = fields.Date('Date', required=True)
    is_calculated = fields.Boolean('Calculated', default=False)
    device = fields.Many2one('biometric.config', string='Device', required=True)
    
    @api.multi
    def unlink(self):
        if any(self.filtered(lambda log: log.is_calculated == True)):
            raise UserError(('You cannot delete a Record which is already Calculated !!!'))
        return super(AttendanceLog, self).unlink()