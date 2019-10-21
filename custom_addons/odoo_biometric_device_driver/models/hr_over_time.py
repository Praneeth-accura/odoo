from odoo import api, fields, models
from datetime import datetime, timedelta, time
import math

def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)

def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class HrWeeklyOverTime(models.Model):
    _name = 'hr.weekly.over.time'

    employee_id = fields.Char('Employee ID')
    week = fields.Char('Week')
    duration = fields.Char('Duration')
    month = fields.Char('Month')
    year = fields.Char('Year')

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    _over_time_per_week_list = fields.One2many('hr.weekly.over.time', 'employee_id', string="Weeky Over Time Summary")

    # functions works every 30 days according to the server action
    def weekly_overtime_calculation_server_action(self):
        try:
            now = datetime.now()
            year = now.year
            month = now.month
            week = int(now.strftime("%W"))
            employee_obj = self.env['hr.employee']
            attendance_obj = self.env['hr.attendance']
            over_time_config_obj = self.env['hr.over.time.configuration']
            over_time_config = over_time_config_obj.search([])

            # works if over time configuration is set to weekly work time
            if over_time_config.over_time == 'yes':
                if over_time_config.criteria == 'weekly_work_time':
                    biometric_obj = self.env['biometric.config'].search([])
                    for device in biometric_obj:
                        self.env['biometric.config'].download_attendance_log_for_monthly_ot(device)
                    self.env['attendance.calc.wizard'].calculate_attendance()
                    for employees in employee_obj.search([]):
                        sum = 0.0
                        diff = 0.0
                        weekly_over_time = 0.0
                        attendances = attendance_obj.search([('employee_id', '=', employees.id)])
                        w_attendance = None
                        for attendance in attendance_obj.search([('employee_id', '=', employees.id)]):
                            employee = attendance.employee_id
                            worked_hours = attendance.worked_hours
                            if attendance.check_in and attendance.check_out:
                                check_in_time = fields.Datetime.to_string(
                                    fields.Datetime.from_string(attendance.check_in) + timedelta(hours=5, minutes=30))
                                check_out_time = fields.Datetime.to_string(
                                    fields.Datetime.from_string(attendance.check_out) + timedelta(hours=5, minutes=30))
                                check_in_month = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').month
                                check_in_year = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').year
                                check_in_week = int(datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').strftime("%W"))
                                check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
                                check_out_date = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').date()
                                if year == check_in_year and week == check_in_week:
                                    w_attendance = attendance.check_in
                                    self._cr.execute(
                                        "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (attendance.date, employee.id))
                                    morning = self._cr.fetchall()
                                    # works morning

                                    self._cr.execute(
                                        "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (attendance.date, employee.id))
                                    evening = self._cr.fetchall()

                                    if morning and evening:
                                        from_date = evening[0][6]
                                        to_date = evening[0][7]
                                        from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                            hours=5,
                                            minutes=30)
                                        from_date = convert_to_float(str(from_date))
                                        to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                              minutes=30)
                                        to_date = convert_to_float(str(to_date))
                                        if to_date < from_date:
                                            holiday_duration = (to_date + 24) - from_date
                                        else:
                                            holiday_duration = to_date - from_date
                                        worked_hours = worked_hours + holiday_duration
                                        sum = sum + worked_hours

                                    elif morning:
                                        from_date = morning[0][6]
                                        to_date = morning[0][7]
                                        from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                            hours=5,
                                            minutes=30)
                                        from_date = convert_to_float(str(from_date))
                                        to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                              minutes=30)
                                        to_date = convert_to_float(str(to_date))
                                        if to_date < from_date:
                                            holiday_duration = (to_date + 24) - from_date
                                        else:
                                            holiday_duration = to_date - from_date
                                        worked_hours = worked_hours + holiday_duration
                                        sum = sum + worked_hours

                                    elif evening:
                                        from_date = evening[0][6]
                                        to_date = evening[0][7]
                                        from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                            hours=5,
                                            minutes=30)
                                        from_date = convert_to_float(str(from_date))
                                        to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                              minutes=30)
                                        to_date = convert_to_float(str(to_date))
                                        if to_date < from_date:
                                            holiday_duration = (to_date + 24) - from_date
                                        else:
                                            holiday_duration = to_date - from_date
                                        worked_hours = worked_hours + holiday_duration
                                        sum = sum + worked_hours

                                    else:
                                        sum = sum + worked_hours

                        if w_attendance:
                            for ids in self.env['schedule.history'].search(
                                    [('from_date', '<=', w_attendance),
                                     ('to_date', '>=', w_attendance),
                                     ('emp_id', '=', employee.id)]):
                                for id in self.env['resource.calendar.attendance'].search(
                                        [('calendar_id', '=', ids.resource_calendar_id.id)]):

                                    w_check_in_time = fields.Datetime.to_string(
                                        fields.Datetime.from_string(w_attendance) + timedelta(hours=5,
                                                                                                     minutes=30))
                                    w_check_out_time = fields.Datetime.to_string(
                                        fields.Datetime.from_string(w_attendance) + timedelta(hours=5,
                                                                                                      minutes=30))
                                    check_in_date = datetime.strptime(w_check_in_time, '%Y-%m-%d %H:%M:%S').date()
                                    check_out_date = datetime.strptime(w_check_out_time, '%Y-%m-%d %H:%M:%S').date()

                                    if ids.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    elif ids.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    else:
                                        diff = id.hour_to - id.hour_from

                                    weekly_over_time = weekly_over_time + diff

                        # works if total weekly work time is greater than the company allocated work time for each month
                            if weekly_over_time < sum:
                                result = sum - weekly_over_time
                                if over_time_config.criteria_two == 'buffer_hours':
                                    if sum > over_time_config.time:
                                        result = result
                                    else:
                                        result = 0.0
                                elif over_time_config.criteria_two == 'every_min':
                                    result = result
                                elif over_time_config.criteria_two == 'hourly':
                                    if over_time_config.time_period == 'hour':
                                        converted = float_to_time(result)
                                        result = converted.hour
                                    elif over_time_config.time_period == 'half_hour':
                                        over_time = result / 0.5
                                        time = float_to_time(over_time)
                                        half_hour = float_to_time(time.hour)
                                        half_hour = datetime.strptime(str(half_hour), '%H:%M:%S')
                                        half_hour = convert_to_float(str(half_hour))
                                        result = half_hour / 2
                                    elif over_time_config.time_period == 'quarter_hour':
                                        over_time = result / 0.25
                                        time = float_to_time(over_time)
                                        quarter_hours = float_to_time(time.hour)
                                        quarter_hour = datetime.strptime(str(quarter_hours), '%H:%M:%S')
                                        quarter_hour = convert_to_float(str(quarter_hour))
                                        result = quarter_hour / 4
                                hr_weekly_overtime = self.env['hr.weekly.over.time']
                                year_month_validation = hr_weekly_overtime.search([('month', '=', month), ('year', '=', year),
                                                                                   ('employee_id', '=', employee.id),
                                                                                   ('week', '=', week)])
                                vals = {
                                    'employee_id': employee.id,
                                    'week': week,
                                    'month': month,
                                    'duration': result,
                                    'year': year
                                }
                                # if there's a record existing with the same month,year,week for the employee => update
                                if year_month_validation:
                                    year_month_validation.write(vals)
                                # if no => create
                                else:
                                    hr_weekly_overtime.create(vals)
                            else:
                                result = 0.0
                                hr_weekly_overtime = self.env['hr.weekly.over.time']
                                vals = {
                                    'employee_id': employee.id,
                                    'week': week,
                                    'month': month,
                                    'duration': result,
                                    'year': year
                                }
                                year_month_validation = hr_weekly_overtime.search([('month', '=', month), ('year', '=', year),
                                                                                   ('employee_id', '=', employee.id),
                                                                                   ('week', '=', week)])
                                if year_month_validation:
                                    year_month_validation.write(vals)
                                # if no => create
                                else:
                                    hr_weekly_overtime.create(vals)

        except Exception as e:
            print(str(e))
