from odoo import api, models, fields
from odoo.exceptions import UserError

class HrNopayConfiguration(models.Model):
    _name = 'hr.nopay.configuration'

    name = fields.Char(string="Name", required=True)
    is_nopay = fields.Selection([('yes', 'Yes'),
                                 ('no', 'No')], string="Nopay")
    salary_deduction = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')], string="Salary Deduction")
    payroll = fields.Selection([('auto', 'Auto'),
                                ('manual', 'Manual')], string="Payroll")
    rate = fields.Boolean(string="Fix Rate")
    percentage = fields.Boolean(string="Percentage")
    one_finger = fields.Boolean('Only One Finger', default=False)
    no_leave = fields.Boolean('No leave but absent', default=False)
    probation = fields.Boolean('Probationary', default=False)
    leave_not_approved = fields.Boolean('Leave Not Approved', default=False)
    no_leaves = fields.Boolean('No remaining Leaves', default=False)
    no_pay = fields.Boolean('No pay Category Selected', default=False)
    less_working_hours = fields.Boolean('Less Working hours per day', default=False)
    manual_selection = fields.Boolean('Manual Selection', default=False)

    @api.model
    def create(self, vals):
        records = self.search([])
        if len(records) == 0:
            return super(HrNopayConfiguration, self).create(vals)
        else:
            raise UserError('You cannot create more than one record.')

    @api.multi
    def unlink(self):
        raise UserError('You cannot delete this record.')
        return super(AttendanceLog, self).unlink()