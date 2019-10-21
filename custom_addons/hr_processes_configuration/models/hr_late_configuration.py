from odoo import api, models, fields
from odoo.exceptions import UserError


class HrLateConfigurations(models.Model):

    _name = 'hr.late.configuration'
    name = fields.Char('Name')
    is_late = fields.Selection([('yes', 'Yes'),
                                ('no', 'No')], string="Late Calculation")
    case_one = fields.Selection([('late_covered', "Late can be Covered in evening"),
                                 ('time_range', 'Time range for late'),
                                 ('monthly_late', 'Monthly late period'),
                                 ('late_days_for_month', 'Late days for a month (Late for specific days)')], string="Criteria 1")
    salary_deduction = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')], string="Salary Deduction")
    days = fields.Integer('Days')
    rate = fields.Boolean(string="Fix Rate")
    percentage = fields.Boolean(string="Percentage")
    time = fields.Float(string="Time")
    late_days_per_month = fields.Integer(string='Number of late days per month')
    grace_time = fields.Float(string='Grace Time')

    @api.model
    def create(self, vals):
        num_of_days = vals['late_days_per_month']
        records = self.search([])
        if len(records) == 0:
            if vals['case_one'] == 'late_days_for_month':
                emp_obj = self.env['hr.employee'].search([])
                if emp_obj:
                    for employee in emp_obj:
                        for month in range(1, 13):
                            if month == 1:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'January',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 2:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'February',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 3:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'March',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 4:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'April',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 5:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'May',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 6:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'June',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 7:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'July',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 8:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'August',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 9:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'September',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 10:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'October',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 11:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'November',
                                    'late_days_per_month': num_of_days
                                })
                            elif month == 12:
                                employee.monthly_late_attendance_lines.create({
                                    'monthly_late_id': employee.id,
                                    'employee_name': employee.id,
                                    'number': month,
                                    'month': 'December',
                                    'late_days_per_month': num_of_days
                                })

            return super(HrLateConfigurations, self).create(vals)
        else:
            raise UserError('You cannot create another record')

    @api.multi
    def write(self, vals):
        if 'late_days_per_month' in vals:
            if self.late_days_per_month != vals['late_days_per_month']:
                employee_obj = self.env['hr.employee'].search([])
                if employee_obj:
                    for employee in employee_obj:
                        if len(employee.monthly_late_attendance_lines) > 0:
                            for lines in employee.monthly_late_attendance_lines:
                                lines.write({'late_days_per_month': vals['late_days_per_month']})
                        else:
                            for month in range(1, 13):
                                if month == 1:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'January',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 2:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'February',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 3:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'March',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 4:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'April',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 5:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'May',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 6:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'June',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 7:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'July',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 8:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'August',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 9:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'September',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 10:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'October',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 11:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'November',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })
                                elif month == 12:
                                    employee.monthly_late_attendance_lines.create({
                                        'monthly_late_id': employee.id,
                                        'employee_name': employee.id,
                                        'number': month,
                                        'month': 'December',
                                        'late_days_per_month': vals['late_days_per_month']
                                    })

        return super(HrLateConfigurations, self).write(vals)

    @api.multi
    def unlink(self):
        raise UserError('You cannot delete a Record')
        return super(AttendanceLog, self).unlink()
