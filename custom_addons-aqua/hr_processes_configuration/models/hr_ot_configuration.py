from odoo import api, models, fields
from odoo.exceptions import UserError

class HrOverTimeConfiguration(models.Model):
    _name = 'hr.over.time.configuration'

    name = fields.Char(string="Name")
    over_time = fields.Selection([('yes', 'Yes'),
                                  ('no', 'No')], string="OT")
    criteria = fields.Selection([('specific_day', 'Specific Day'),
                                 ('shift', 'Shift'),
                                 ('monthly_work_time', 'Monthly Work Time'),
                                 ('weekly_work_time', 'Weekly Work Time')], string="Criterias")
    criteria_two = fields.Selection([('buffer_hours', 'Buffer Hours'),
                                     ('every_min', 'Every Min'),
                                     ('hourly', 'Hourly/30min/15min')], string="Duration Type")
    days = fields.Selection([('0', 'Monday'),
                             ('1', 'Tuesday'),
                             ('2', 'Wednesday'),
                             ('3', 'Thursday'),
                             ('4', 'Friday'),
                             ('5', 'Saturday'),
                             ('6', 'Sunday')], string="Days")
    time = fields.Float('Time')
    time_for_month_ot = fields.Float('Time')
    time_period = fields.Selection([('hour', 'Every Hour'),
                                    ('half_hour', 'Every 30 Minutes'),
                                    ('quarter_hour', 'Every 15 Minutes')])

    @api.model
    def create(self, vals):
        records = self.search([])
        if len(records) == 0:
            return super(HrOverTimeConfiguration, self).create(vals)
        else:
            raise UserError('You cannot create more than one record.')

    @api.multi
    def unlink(self):
        raise  UserError('You cannot delete this record.')
        return super(AttendanceLog, self).unlink()
