from odoo import api, fields, models
from datetime import datetime, timedelta, time, date
import math
import calendar

def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)

def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class HrWeeklyOverTime(models.Model):
    _name = 'hr.monthly.over.time'

    employee_id = fields.Char('Employee ID')
    duration = fields.Char('Duration')
    month = fields.Char('Month')
    year = fields.Char('Year')

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    monthly_overtime_list = fields.One2many('hr.monthly.over.time', 'employee_id', string="Weeky Over Time Summary")

    def monthly_overtime_calculation_server_action(self):
        employee_obj = self.env['hr.employee']
        attendance_obj = self.env['hr.attendance']
        over_time_config_obj = self.env['hr.over.time.configuration'].search([])
        hr_monthly_overtime = self.env['hr.monthly.over.time']
        # if monthly_ot is selected and overtime is applicable
        if over_time_config_obj.over_time == 'yes' and over_time_config_obj.criteria == 'monthly_work_time':
            monthly_allocated_over_time = over_time_config_obj.time_for_month_ot
            current_date_time = datetime.now()
            current_year = current_date_time.year
            current_month = current_date_time.month
            current_date = current_date_time.date()
            first_day_of_current_month = 1
            last_day_of_current_month = calendar.monthrange(current_year, current_month)[1]
            first_day = date(year=current_year, month=current_month, day=first_day_of_current_month)
            last_day = date(year=current_year, month=current_month, day=last_day_of_current_month)
            biometric_obj = self.env['biometric.config'].search([])
            for device in biometric_obj:
                self.env['biometric.config'].download_attendance_log_for_monthly_ot(device)
            self.env['attendance.calc.wizard'].calculate_attendance()
            if current_month != 1:
                last_month = current_month - 1
                year = current_year
                first_day_of_last_month = 1
                last_day_of_last_month = calendar.monthrange(year, last_month)[1]
                first_date_of_last_month = date(year=year, month=last_month, day=first_day_of_last_month)
                last_date_of_last_month = date(year=year, month=last_month, day=last_day_of_last_month)
                current_month_name = first_date_of_last_month.strftime("%B")
            elif current_month == 1:
                last_month = 12
                year = current_year - 1
                first_day_of_last_month = 1
                last_day_of_last_month = calendar.monthrange(year, last_month)[1]
                first_date_of_last_month = date(year=year, month=last_month, day=first_day_of_last_month)
                last_date_of_last_month = date(year=year, month=last_month, day=last_day_of_last_month)
                current_month_name = first_date_of_last_month.strftime("%B")
            for employee in employee_obj.search([]):
                total_worked_hours = 0
                total_leave_duration = 0
                domain = [('date', '>=', first_date_of_last_month), ('date', '<=', last_date_of_last_month), ('employee_id', '=', employee.id)]
                # calculating all working hours of each employee of the month
                for attendance in attendance_obj.search(domain):
                    if attendance.check_in and attendance.check_out:
                        total_worked_hours = total_worked_hours + attendance.worked_hours
                # calculating all leave duration of each employee of the month
                self._cr.execute(
                    "select * from hr_holidays left join hr_holidays_status as hhs on hr_holidays.holiday_status_id = hhs.id where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s and (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and employee_id = %s and state = 'validate' and hhs.name in ('Short Leaves', 'Annual Leaves', 'Casual Leaves', 'Sick Leaves')",
                    (first_date_of_last_month, last_date_of_last_month, employee.id))
                leaves = self._cr.fetchall()
                for leave in leaves:
                    leave_start = leave[6]
                    leave_end = leave[7]
                    leave_start = datetime.strptime(leave_start, '%Y-%m-%d %H:%M:%S')
                    leave_end = datetime.strptime(leave_end, '%Y-%m-%d %H:%M:%S')
                    duration_of_leave = leave_end - leave_start
                    duration_of_leave_days = duration_of_leave.days
                    remaining_time = duration_of_leave - timedelta(duration_of_leave_days)
                    duration_of_leave = datetime.strptime(str(remaining_time), '%H:%M:%S')
                    duration_of_leave_as_float = convert_to_float(str(duration_of_leave))
                    total_leave_duration = total_leave_duration + duration_of_leave_as_float + (24 * duration_of_leave_days)
                # sum of all leaves and worked hours
                total_of_worked_hours_and_leave_duration = total_worked_hours + total_leave_duration
                # if sum of all leaves and worked hours are greater than monthly allocated time
                if total_of_worked_hours_and_leave_duration > monthly_allocated_over_time:
                    total_over_time = total_of_worked_hours_and_leave_duration - monthly_allocated_over_time
                    # checking if there's record of the month
                    year_month_validation = hr_monthly_overtime.search([('month', '=', current_month_name),
                                                                        ('year', '=', year),
                                                                        ('employee_id', '=', employee.id)])
                    vals = {
                        'employee_id': employee.id,
                        'month': current_month_name,
                        'duration': float(total_over_time),
                        'year': year
                    }
                    # if there's record from same month
                    if year_month_validation:
                        year_month_validation.write(vals)
                    # if there's no record from same month
                    else:
                        hr_monthly_overtime.create(vals)
                # else ot is 0
                else:
                    total_over_time = 0
                    year_month_validation = hr_monthly_overtime.search([('month', '=', current_month_name),
                                                                        ('year', '=', year),
                                                                        ('employee_id', '=', employee.id)])
                    vals = {
                        'employee_id': employee.id,
                        'month': current_month_name,
                        'duration': float(total_over_time),
                        'year': year
                    }
                    if year_month_validation:
                        year_month_validation.write(vals)
                    else:
                        hr_monthly_overtime.create(vals)



