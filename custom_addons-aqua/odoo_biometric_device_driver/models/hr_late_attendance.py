from odoo import api, models, fields
from datetime import datetime, time, timedelta
import math

def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)

def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class HrLateAttendance(models.Model):
    _name = 'hr.late.attendance'

    employee_id = fields.Char('Employee ID')
    month = fields.Char('Month')
    duration = fields.Float('Duration')
    year = fields.Char('Year')

class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    late_list = fields.One2many('hr.late.attendance', 'employee_id', string="Monthly Late Summary")

    # functions works every 30 days according to the server action
    def late_attendance_server_actions(self):
        try:
            attendance = None
            now = datetime.now()
            year = now.year
            month = now.month
            employee_obj = self.env['hr.employee']
            attendance_obj = self.env['hr.attendance']
            late_attendance_config_obj = self.env['hr.late.configuration']
            late_attendance_config = late_attendance_config_obj.search([])

            if late_attendance_config.is_late == 'yes':
            # works if late attendance configuration is set to monthly late
                if late_attendance_config.case_one == 'monthly_late':
                    self.env['biometric.config'].download_attendance_log()
                    self.env['attendance.calc.wizard'].calculate_attendance()
                    monthly_late_time = late_attendance_config.time
                    # create or update records for each employee
                    for employees in employee_obj.search([]):
                        sum = 0.0
                        for attendance in attendance_obj.search([('employee_id', '=', employees.id)]):
                            employee = attendance.employee_id
                            if attendance.check_in and attendance.check_out:
                                check_in_time = fields.Datetime.to_string(
                                    fields.Datetime.from_string(attendance.check_in) + timedelta(hours=5, minutes=30))
                                check_out_time = fields.Datetime.to_string(
                                    fields.Datetime.from_string(attendance.check_out) + timedelta(hours=5, minutes=30))
                                check_in_month = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').month
                                check_in_year = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').year
                                check_in_day = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').weekday()
                                check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
                                check_out_date = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').date()

                                if month == check_in_month and year == check_in_year:
                                    for ids in self.env['schedule.history'].search(
                                            [('from_date', '<=', attendance.check_in), ('to_date', '>=', attendance.check_in),
                                             ('emp_id', '=', employee.id)]):
                                        id = self.env['resource.calendar.attendance'].search(
                                            [('calendar_id', '=', ids.resource_calendar_id.id), ('dayofweek', '=', check_in_day)])

                                        if ids.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                            diff = (id.hour_to + 24) - id.hour_from
                                        elif ids.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                            diff = (id.hour_to + 24) - id.hour_from
                                        else:
                                            diff = id.hour_to - id.hour_from

                                        self._cr.execute(
                                            "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                            (attendance.date, employee.id))
                                        morning = self._cr.fetchall()
                                        # works morning

                                        self._cr.execute(
                                            "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                            (attendance.date, employee.id))
                                        evening = self._cr.fetchall()

                                        if evening and morning:
                                            from_date = evening[0][6]
                                            to_date = evening[0][7]
                                            if (ids.from_date <= from_date and ids.to_date >= from_date) or (
                                                    ids.from_date <= to_date and ids.to_date >= to_date):

                                                margin = diff / 2
                                                margin_time = id.hour_from + margin
                                                from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                from_date = convert_to_float(str(from_date))
                                                to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                to_date = convert_to_float(str(to_date))
                                                if from_date < margin_time:
                                                    check_in = check_in_time
                                                    check_in = convert_to_float(check_in)
                                                    if check_in > to_date:
                                                        difference = check_in - to_date
                                                        sum = sum + difference
                                                    else:
                                                        sum = sum + 0
                                                else:
                                                    time_with_grace = id.hour_from
                                                    check_in = check_in_time
                                                    check_in = convert_to_float(check_in)
                                                    if check_in > time_with_grace:
                                                        difference = check_in - time_with_grace
                                                        sum = sum + difference
                                                    else:
                                                        sum = sum + 0
                                            else:
                                                hour_from = id.hour_from
                                                check_in = check_in_time
                                                check_in = convert_to_float(check_in)
                                                difference = check_in - hour_from
                                                if difference > 0:
                                                    sum = sum + difference

                                        elif evening:
                                            to_date = evening[0][7]
                                            if (ids.from_date <= to_date and ids.to_date >= to_date):
                                                to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                to_date = convert_to_float(str(to_date))
                                                check_in = check_in_time
                                                check_in = convert_to_float(check_in)
                                                if check_in > to_date:
                                                    difference = check_in - to_date
                                                    sum = sum + difference
                                                else:
                                                    sum = sum + 0
                                            else:
                                                hour_from = id.hour_from
                                                check_in = check_in_time
                                                check_in = convert_to_float(check_in)
                                                difference = check_in - hour_from
                                                if difference > 0:
                                                    sum = sum + difference

                                        elif morning:
                                            time_with_grace = id.hour_from
                                            check_in = check_in_time
                                            check_in = convert_to_float(check_in)
                                            if check_in > time_with_grace:
                                                difference = check_in - time_with_grace
                                                sum = sum + difference
                                            else:
                                                sum = sum + 0

                                        else:
                                            hour_from = id.hour_from
                                            check_in = check_in_time
                                            check_in = convert_to_float(check_in)
                                            difference = check_in - hour_from
                                            if difference > 0:
                                                sum = sum + difference

                        # works if total late time is greater than the company allocated late time for each month
                        if attendance:
                            if sum > 0:
                                total = employees.deduct_from_leaves(employees, sum, diff)
                                if total > 0:
                                    if monthly_late_time < sum:
                                        result = total - monthly_late_time
                                        hr_late_attendance = self.env['hr.late.attendance']
                                        year_month_validation = hr_late_attendance.search([('month', '=', month), ('year', '=', year), ('employee_id', '=', employee.id)])
                                        vals = {
                                            'employee_id': employee.id,
                                            'month': month,
                                            'duration': result,
                                            'year': year
                                        }
                                        # if there's a record existing with the same month and year for the employee => update
                                        if year_month_validation:
                                            year_month_validation.write(vals)
                                        # if no => create
                                        else:
                                            hr_late_attendance.create(vals)
                                    else:
                                        result = 0.0
                                        hr_late_attendance = self.env['hr.late.attendance']
                                        vals = {
                                            'employee_id': employee.id,
                                            'month': month,
                                            'duration': result,
                                            'year': year
                                        }
                                        hr_late_attendance.create(vals)

                else:
                    pass

        except Exception as e:
            print str(e)


    @api.multi
    def deduct_from_leaves(self, lines, total, diff):

        # get remaining sort leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.id) + "'AND s.name = 'Short Leaves' GROUP BY h.holiday_status_name, h.holiday_status_id, h.employee_id")
        short_leaves = lines._cr.fetchall()

        # get remaining annual leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.id) + "'AND s.name = 'Annual Leaves' GROUP BY h.holiday_status_name, h.holiday_status_id, h.employee_id")
        annual_leaves = lines._cr.fetchall()

        # get remaining casual leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.id) + "'AND s.name = 'Casual Leaves' GROUP BY h.holiday_status_name,h.holiday_status_id, h.employee_id")
        casual_leaves = lines._cr.fetchall()

        # get remaining sick leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name,h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.id) + "'AND s.name = 'Sick Leaves' GROUP BY h.holiday_status_name,h.holiday_status_id, h.employee_id")
        sick_leaves = lines._cr.fetchall()

        number_of_annual_leaves = number_of_sick_leaves = number_of_casual_leaves = number_of_short_leaves = 0

        if annual_leaves:
            number_of_annual_leaves = annual_leaves[0][0]
        if short_leaves:
            number_of_short_leaves = short_leaves[0][0]
        if casual_leaves:
            number_of_casual_leaves = casual_leaves[0][0]
        if sick_leaves:
            number_of_sick_leaves = sick_leaves[0][0]

        quarter_hour = diff / 4

        if short_leaves:
            short_leave_obj = self.env['hr.holidays'].search([('holiday_status_name', '=', 'Short Leaves'), ('employee_id', '=', lines.id), ('state', '=', 'validate'), ('number_of_days', '>', 0), ('number_of_days_temp', '>', 0)])
            count = 1
            if short_leave_obj:
                for leave in range(0, int(number_of_short_leaves)):
                    if total > 0 and number_of_short_leaves != 0:
                        short_leave_obj.write({
                            'number_of_days_temp': number_of_short_leaves - 1,
                            'number_of_days': number_of_short_leaves - 1,
                        })

                        short_leave_obj.leave_allocation_log.create({
                            'allocation_id': short_leave_obj.id,
                            'holiday_status_id': short_leave_obj.holiday_status_id.id,
                            'employee_id': lines.id,
                            'reason': '%s short leaves deduct due to late attendance' % count,
                        })

                        number_of_short_leaves -= 1
                        total -= quarter_hour
                        if total < 0:
                            break

        if casual_leaves:
            casual_leave_obj = self.env['hr.holidays'].search([('holiday_status_name', '=', 'Casual Leaves'), ('employee_id', '=', lines.id), ('state', '=', 'validate'), ('number_of_days', '>', 0), ('number_of_days_temp', '>', 0)])
            count = 0.5
            if casual_leave_obj:
                for leave in range(0, int((number_of_casual_leaves * 2))):
                    if total > 0 and number_of_casual_leaves >= 0.5:
                        casual_leave_obj.write({
                            'number_of_days_temp': number_of_casual_leaves - 0.5,
                            'number_of_days': number_of_casual_leaves - 0.5,
                        })

                        casual_leave_obj.leave_allocation_log.create({
                            'allocation_id': casual_leave_obj.id,
                            'holiday_status_id': casual_leave_obj.holiday_status_id.id,
                            'employee_id': lines.id,
                            'reason': '%s casual leaves deduct due to late attendance' % count,
                        })

                        number_of_casual_leaves -= 0.5
                        total -= quarter_hour
                        if total < 0:
                            break

        if annual_leaves:
            annual_leave_obj = self.env['hr.holidays'].search([('holiday_status_name', '=', 'Annual Leaves'), ('employee_id', '=', lines.id), ('state', '=', 'validate'), ('number_of_days', '>', 0), ('number_of_days_temp', '>', 0)])
            count = 0.5
            if annual_leave_obj:
                for leave in range(0, int((number_of_annual_leaves * 2))):
                    if total > 0 and number_of_annual_leaves >= 0.5:
                        annual_leave_obj.write({
                            'number_of_days_temp': number_of_annual_leaves - 0.5,
                            'number_of_days': number_of_annual_leaves - 0.5,
                        })

                        annual_leave_obj.leave_allocation_log.create({
                            'allocation_id': annual_leave_obj.id,
                            'holiday_status_id': annual_leave_obj.holiday_status_id.id,
                            'employee_id': lines.id,
                            'reason': '%s annual leaves deduct due to late attendance' % count,
                        })

                        number_of_annual_leaves -= 0.5
                        total -= quarter_hour
                        if total < 0:
                            break

        if sick_leaves:
            sick_leave_obj = self.env['hr.holidays'].search([('holiday_status_name', '=', 'Sick Leaves'), ('employee_id', '=', lines.id), ('state', '=', 'validate'), ('number_of_days', '>', 0), ('number_of_days_temp', '>', 0)])
            count = 0.5
            if sick_leave_obj:
                for leave in range(0, int((number_of_sick_leaves * 2))):
                    if total > 0 and number_of_sick_leaves >= 0.5:
                        sick_leave_obj.write({
                            'number_of_days_temp': number_of_sick_leaves - 0.5,
                            'number_of_days': number_of_sick_leaves - 0.5,
                        })

                        sick_leave_obj.leave_allocation_log.create({
                            'allocation_id': sick_leave_obj.id,
                            'holiday_status_id': sick_leave_obj.holiday_status_id.id,
                            'employee_id': lines.id,
                            'reason': '%s sick leaves deduct due to late attendance' % count,
                        })

                        number_of_sick_leaves -= 0.5
                        total -= quarter_hour
                        if total < 0:
                            break

        return total







