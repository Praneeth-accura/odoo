from odoo import api, fields, models
import sys
from datetime import datetime, timedelta
import math
from datetime import datetime, timedelta, time


def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class AttendanceWizard(models.TransientModel):
    _name = 'attendance.calc.wizard'


    @api.multi
    def calculate_attendance(self):
        hr_attendance = self.env['hr.attendance']
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yesterday = datetime.strptime(today,"%Y-%m-%d %H:%M:%S") - timedelta(1)
        domain_time = yesterday.replace(hour=23, minute=59, second=59)
        employee_list = self.env['hr.employee'].search([])
        for employee in employee_list:
            check_in = False
            date = False
            domain = [('employee_id', '=', employee.id), ('punching_time', '<=', str(domain_time)), ('is_calculated', '=', False), ('status', '=', '0')]
            attendance_log = self.env['attendance.log'].search(domain)
            for attendance in attendance_log:
                self._cr.execute(
                    "select id from schedule_history where ( (from_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and (to_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s) and emp_id = %s",
                    (attendance.date, attendance.date, str(attendance.employee_id.id)))
                result = self._cr.fetchall()

                check_in_date = datetime.strptime(attendance.punching_time,"%Y-%m-%d %H:%M:%S").date()
                check_in_date_time = datetime.strptime(attendance.punching_time,"%Y-%m-%d %H:%M:%S").time()
                standard_check_in_time = datetime.strptime(attendance.punching_time,"%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)
                total_records = attendance_log.search([('date', '=', check_in_date), ('status', '=', 0)])
                number_of_shift = 1

                if len(result) > 1:
                    j = 0
                    num = 0
                    is_hit = False
                    for x in range(0, len(result)):
                        working_history_objects = self.env['schedule.history'].browse(result[j][0])
                        for days in working_history_objects.resource_calendar_id.attendance_ids:
                            shift_end_datetime = datetime.strptime(str(check_in_date), "%Y-%m-%d") + timedelta(hours=days.hour_to) - timedelta(hours=5, minutes=30)
                            shift_start_datetime = datetime.strptime(str(check_in_date), "%Y-%m-%d") + timedelta(hours=days.hour_from) - timedelta(hours=5, minutes=30)
                            standard_start_datetime = datetime.strptime(str(check_in_date), "%Y-%m-%d") + timedelta(hours=days.hour_from)
                            standard_end_time = datetime.strptime(str(check_in_date), "%Y-%m-%d") + timedelta(hours=days.hour_to)
                            is_record_available = hr_attendance.search([('employee_id', '=', employee.id), ('date', '=', check_in_date), ('check_in', '<', str(shift_end_datetime)), ('number_of_shift', '=', number_of_shift)])

                            if number_of_shift > 1:
                                if standard_start_datetime.time() > standard_check_in_time.time():
                                    attendance.is_calculated = True
                                    break

                            if int(days.dayofweek) == 0:
                                num = 1
                            elif int(days.dayofweek) == 1:
                                num = 2
                            elif int(days.dayofweek) == 2:
                                num = 3
                            elif int(days.dayofweek) == 3:
                                num = 4
                            elif int(days.dayofweek) == 4:
                                num = 5
                            elif int(days.dayofweek) == 5:
                                num = 6
                            else:
                                num = 0

                            if not is_record_available and not attendance.is_calculated and not is_hit:
                                if check_in_date.strftime("%w") == str(num):
                                    if check_in_date_time < float_to_time(days.hour_to):
                                        vals = {
                                                'employee_id': attendance.employee_id.id,
                                                'check_in': attendance.punching_time,
                                                'date': attendance.date,
                                                'number_of_shift': number_of_shift,
                                        }
                                        hr_attendance.create(vals)
                                        check_in = True
                                        is_hit = True
                                        attendance.is_calculated = True
                                        break
                                    elif float_to_time(days.hour_from) <= check_in_date.time < float_to_time(days.hour_to) and not is_hit:
                                        vals = {
                                                'employee_id': attendance.employee_id.id,
                                                'check_in': attendance.punching_time,
                                                'date': attendance.date ,
                                                'number_of_shift': number_of_shift
                                        }
                                        hr_attendance.create(vals)
                                        check_in = True
                                        is_hit = True
                                        attendance.is_calculated = True
                                        break

                        j += 1
                        number_of_shift += 1
                    attendance.is_calculated = True

                else:
                    if not attendance.is_calculated:
                        vals = {
                                'employee_id': attendance.employee_id.id, 'check_in': attendance.punching_time,
                                'date': attendance.date,
                                'number_of_shift': number_of_shift
                        }
                        hr_attendance.create(vals)
                        check_in = True
                        date = attendance.date
                        attendance.is_calculated = True

        for employee in employee_list:
            check_out = False
            domain = [('employee_id', '=', employee.id), ('punching_time', '<=', str(domain_time)), ('is_calculated', '=', False), ('status', '=', '1')]
            attendance_log = self.env['attendance.log'].search(domain, order="punching_time asc")
            for attendance in attendance_log:
                print attendance
                if check_out == False:
                    for ids in self.env['schedule.history'].search([
                        ('from_date', '<=', attendance.punching_time), ('to_date', '>=', attendance.punching_time),
                        ('emp_id', '=', employee.id)]):
                        if ids.resource_calendar_id.is_swing_shift:
                            hr_attendence_check = hr_attendance.search([('date', '<=', attendance.date), ('employee_id', '=', attendance.employee_id.id)], order="date asc")
                            for lines in hr_attendence_check:
                                if lines.check_in and not lines.check_out:
                                    if lines.check_in > attendance.punching_time:
                                        pass
                                    else:
                                         self._cr.execute("select id from schedule_history where ( (from_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and (to_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s) and emp_id = %s",
                                           (attendance.date, attendance.date, str(attendance.employee_id.id)))
                                         result = self._cr.fetchall()

                                         number_of_shift = 1
                                         if result:
                                             if not attendance.is_calculated:
                                                 for x in range(0, len(result)):
                                                     if lines.number_of_shift == number_of_shift:
                                                         vals = {'check_out': attendance.punching_time}
                                                         lines.write(vals)
                                                         vals = {
                                                             'ot_hour': lines.ot_time,
                                                             'late_time': lines.late_time,
                                                             'late_time_store_value': lines.late_time_store_value,
                                                             'is_calculated': True,
                                                             'ot_applicable': True
                                                         }
                                                         lines.write(vals)
                                                         attendance.is_calculated = True
                                                     number_of_shift += 1

                        else:
                            hr_attendence_check = hr_attendance.search([('date', '=', attendance.date), ('employee_id', '=', attendance.employee_id.id)], order="date asc")
                            if hr_attendence_check:
                                for lines in hr_attendence_check:
                                    self._cr.execute("select id from schedule_history where ( (from_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and (to_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s) and emp_id = %s",
                                      (attendance.date, attendance.date, str(attendance.employee_id.id)))
                                    result = self._cr.fetchall()

                                    number_of_shift = 1
                                    if result:
                                        if not attendance.is_calculated:
                                            if lines.check_in > attendance.punching_time:
                                                pass
                                            else:
                                                for x in range(0, len(result)):
                                                    if lines.number_of_shift == number_of_shift:
                                                        vals = {'check_out': attendance.punching_time}
                                                        lines.write(vals)
                                                        vals = {
                                                            'ot_hour': lines.ot_time,
                                                            'late_time': lines.late_time,
                                                            'late_time_store_value': lines.late_time_store_value,
                                                            'is_calculated': True,
                                                            'ot_applicable': True
                                                        }
                                                        lines.write(vals)
                                                        attendance.is_calculated = True
                                                    number_of_shift += 1
