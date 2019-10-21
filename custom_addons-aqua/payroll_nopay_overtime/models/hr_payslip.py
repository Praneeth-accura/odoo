# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from datetime import datetime, timedelta, time
from dateutil import relativedelta
from odoo import api, fields, models
from odoo.tools import float_compare
import math
import calendar

def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        date_from_late = datetime.strptime(date_from, '%Y-%m-%d')
        date_from_late = datetime.combine(date_from_late, datetime.min.time())
        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        total_hours = 0
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            normal_hours = 0
            ot_time = 0
            late_time = 0
            days = 0
            ot_days = 0
            while from_date <= to_date:
                per_day_hour = contract.employee_id.get_day_work_hours_count(from_date.date(),calendar=contract.resource_calendar_id)
                normal_hours += per_day_hour
                if per_day_hour > 0:
                    days += 1
                from_date = from_date + relativedelta.relativedelta(days=1)
            ot_policy_obj = self.env['hr.over.time.configuration'].search([])
            criteria = ot_policy_obj.criteria
            hr_attendance_obj = self.env['hr.attendance'].search([])
            hr_weekly_ot_obj = self.env['hr.weekly.over.time'].search([])
            hr_monthly_ot_obj = self.env['hr.monthly.over.time'].search([])
            if ot_policy_obj.over_time == 'yes':
                if criteria == 'shift' or criteria == 'specific_day':
                    for attn_lines in hr_attendance_obj.search([('date', '>=', date_from),
                                                                ('date', '<=', date_to),
                                                                ('employee_id', '=', contract.employee_id.id)]):
                        ot_time = ot_time + attn_lines.ot_hour
                        # late_time = late_time + attn_lines.late_time_store_value
                        if attn_lines.ot_hour > 0:
                            ot_days += 1
                elif criteria == 'weekly_work_time':
                    to_date_month = datetime.strptime(date_to, '%Y-%m-%d').month
                    to_date_year = datetime.strptime(date_to, '%Y-%m-%d').year
                    if to_date_month > 1:
                        previous_month = to_date_month - 1
                        for records in hr_weekly_ot_obj.search([('month', '=', previous_month),
                                                                ('year', '=', to_date_year),
                                                                ('employee_id', '=', contract.employee_id.id)]):
                            ot_time = ot_time + float(records.duration)
                            if records.duration > 0:
                                ot_days += 1
                    elif to_date_month == 1:
                        previous_month = 12
                        previous_year = to_date_year - 1
                        for records in hr_weekly_ot_obj.search([('month', '=', previous_month),
                                                                ('year', '=', previous_year),
                                                                ('employee_id', '=', contract.employee_id.id)]):
                            ot_time = ot_time + records.duration
                            if records.duration > 0:
                                ot_days += 1
                elif criteria == 'monthly_work_time':
                    to_date_month = datetime.strptime(date_to, '%Y-%m-%d').month
                    to_date_year = datetime.strptime(date_to, '%Y-%m-%d').year
                    if to_date_month > 1:
                        previous_month = to_date_month - 1
                        current_month_name = calendar.month_name[int(previous_month)]
                        for records in hr_monthly_ot_obj.search([('month', '=', current_month_name),
                                                                 ('year', '=', to_date_year),
                                                                 ('employee_id', '=', contract.employee_id.id)]):
                            ot_time = ot_time + float(records.duration)
                            if records.duration > 0:
                                ot_days += 1
                    elif to_date_month == 1:
                        previous_month = 12
                        current_month_name = calendar.month_name[int(previous_month)]
                        previous_year = to_date_year - 1
                        for records in hr_monthly_ot_obj.search([('month', '=', current_month_name),
                                                                 ('year', '=', previous_year),
                                                                 ('employee_id', '=', contract.employee_id.id)]):
                            ot_time = ot_time + records.duration
                            if records.duration > 0:
                                ot_days += 1

            if ot_time > 0:
                # print'//////////'
                hr_per_day = normal_hours / days
                ot_days = ot_time / hr_per_day
                ot_line = {
                    'code': 'OT',
                    'contract_id': contract.id,
                    'number_of_days': ot_days,
                    'number_of_hours': ot_time,
                    'name': 'Overtime Hours',
                }
                res.append(ot_line)

            # no pay calculation
            no_pay_obj = self.env['hr.nopay.configuration'].search([], limit=1)
            hr_holidays_obj = self.env['hr.holidays'].search([])
            employee_obj = self.env['hr.employee']
            day = datetime.strptime(date_from, '%Y-%m-%d').weekday()
            date_to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            date_from_date_for_range = datetime.strptime(date_from, '%Y-%m-%d').date()
            no_pay_time = 0
            no_pay_hrs_ = 0
            day_start = date_from
            day_end = date_to
            attendance_obj = self.env['hr.attendance'].search(
                [('check_in', '>=', date_from), ('check_out', '<=', date_to)])
            total = fields.Datetime.to_string(fields.Datetime.from_string(date_to) + timedelta(days=1))
            date_range_difference = (date_to_date - date_from_date_for_range).days
            days = 0
            if no_pay_obj.salary_deduction and no_pay_obj.is_nopay:
                for emp in contract.employee_id:
                    date_from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    for days in range(0, date_range_difference + 1):
                        attendance_obj = self.env['hr.attendance'].search([('date', '=', date_from_date), ('employee_id', '=', emp.id)],
                                                                          order="id asc")
                        if attendance_obj:
                            for attendance in attendance_obj:
                                self._cr.execute(
                                    "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (attendance.date, emp.id))
                                morning = self._cr.fetchall()
                                # works morning

                                self._cr.execute(
                                    "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (attendance.date, emp.id))
                                evening = self._cr.fetchall()

                                if attendance.check_in and attendance.check_out:
                                    shift_obj = self.env['schedule.history'].search(
                                        [('from_date', '<=', attendance.check_in),
                                         ('to_date', '>=', attendance.check_in),
                                         ('emp_id', '=', emp.id)])
                                    for schedule_history in shift_obj:
                                        shift_period = self.env['resource.calendar.attendance'].search([
                                            ('calendar_id', '=', schedule_history.resource_calendar_id.id),
                                            ('dayofweek', '=', date_from_date.weekday())])

                                        if shift_period:
                                            check_in_time = fields.Datetime.to_string(
                                                fields.Datetime.from_string(attendance.check_in) + timedelta(hours=5,
                                                                                                             minutes=30))
                                            check_out_time = fields.Datetime.to_string(
                                                fields.Datetime.from_string(attendance.check_out) + timedelta(hours=5,
                                                                                                              minutes=30))
                                            check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
                                            check_out_date = datetime.strptime(check_out_time,
                                                                               '%Y-%m-%d %H:%M:%S').date()

                                            if schedule_history.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                                diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                            elif schedule_history.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                                diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                            else:
                                                diff = shift_period.hour_to - shift_period.hour_from

                                            if no_pay_obj.less_working_hours:
                                                if attendance.worked_hours < diff:
                                                    if morning and evening:
                                                        from_date_time = evening[0][6]
                                                        to_date_time = evening[0][7]
                                                        from_dates = convert_to_float(evening[0][6])
                                                        to_dates = convert_to_float(evening[0][7])
                                                        if (
                                                                schedule_history.from_date <= from_date_time and schedule_history.to_date >= from_date_time) or (
                                                                schedule_history.from_date <= to_date_time and schedule_history.to_date >= to_date_time):
                                                            if ((to_dates - from_dates) + attendance.worked_hours) < diff:
                                                                no_pay_time = no_pay_time + (diff - ((to_dates - from_dates) + attendance.worked_hours))
                                                            else:
                                                                no_pay_time = no_pay_time + 0
                                                        else:
                                                            no_pay_time = no_pay_time + (diff - attendance.worked_hours)

                                                    elif evening:
                                                        to_dates = evening[0][7]
                                                        if (
                                                                schedule_history.from_date <= to_dates and schedule_history.to_date >= to_dates):
                                                            date_tos = datetime.strptime(to_dates,
                                                                                         '%Y-%m-%d %H:%M:%S') + timedelta(
                                                                hours=5, minutes=30)
                                                            date_tos = convert_to_float(str(date_tos))
                                                            difference = date_tos - shift_period.hour_from + attendance.worked_hours
                                                            if difference < diff:
                                                                no_pay_time = no_pay_time + (diff - difference)
                                                            else:
                                                                no_pay_time = no_pay_time + 0
                                                        else:
                                                            no_pay_time = no_pay_time + (diff - attendance.worked_hours)

                                                    elif morning:
                                                        from_dates = morning[0][6]
                                                        if (
                                                                schedule_history.from_date <= from_dates and schedule_history.to_date >= from_dates):
                                                            date_froms = datetime.strptime(from_dates,
                                                                                           '%Y-%m-%d %H:%M:%S') + timedelta(
                                                                hours=5,
                                                                minutes=30)
                                                            date_froms = convert_to_float(str(date_froms))
                                                            difference = shift_period.hour_to - date_froms + attendance.worked_hours
                                                            if difference < diff:
                                                                no_pay_time = no_pay_time + (diff - difference)
                                                            else:
                                                                no_pay_time = no_pay_time + 0
                                                        else:
                                                            no_pay_time = no_pay_time + (diff - attendance.worked_hours)

                                                    else:
                                                        no_pay_time = no_pay_time + (diff - attendance.worked_hours)

                                                else:
                                                    no_pay_time = no_pay_time + 0

                                elif attendance.check_in and not attendance.check_out or not attendance.check_in and attendance.check_out:
                                    if no_pay_obj.one_finger:
                                        self._cr.execute(
                                            "select * from schedule_history where (from_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and (to_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s and emp_id = %s",
                                            (date_from_date, date_from_date, emp.id)
                                        )
                                        schedule_history = self._cr.fetchall()
                                        if schedule_history:
                                            for schedules in range(0, len(schedule_history)):
                                                shift_period = self.env['resource.calendar.attendance'].search([
                                                    ('calendar_id', '=', schedule_history[schedules][3]),
                                                    ('dayofweek', '=', date_from_date.weekday())])

                                                if schedule_history:
                                                    if shift_period.calendar_id.is_swing_shift:
                                                        diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                                    else:
                                                        diff = shift_period.hour_to - shift_period.hour_from

                                                    no_pay_time = no_pay_time + diff
                                    else:
                                        no_pay_time = no_pay_time + 0

                        else:
                            if no_pay_obj.no_leave == True or no_pay_obj.probation == True or no_pay_obj.leave_not_approved == True or no_pay_obj.no_leaves == True:
                                self._cr.execute(
                                    "select * from schedule_history where (from_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and (to_date + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s and emp_id = %s",
                                    (date_from_date, date_from_date, emp.id)
                                )
                                schedule_history = self._cr.fetchall()
                                if schedule_history:
                                    for schedules in range(0, len(schedule_history)):
                                        shift_period = self.env['resource.calendar.attendance'].search([
                                            ('calendar_id', '=', schedule_history[schedules][3]),
                                            ('dayofweek', '=', date_from_date.weekday())])

                                        if schedule_history:
                                            if shift_period.calendar_id.is_swing_shift:
                                                diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                            else:
                                                diff = shift_period.hour_to - shift_period.hour_from

                                            if diff == 0:
                                                no_pay_time = no_pay_time + 0
                                            else:
                                                date_start = datetime.combine(date_from_date, datetime.min.time())
                                                date_end = date_start + timedelta(hours=23, minutes=59, seconds=59)
                                                # unique_leave = self.env['hr.holidays'].search(
                                                #     [('employee_id', '=', emp.id), ('date_from', '>=', date_start),
                                                #      ('type', '=', 'remove'), ('date_to', '<=', date_end),
                                                #      ('state', '=', 'validate')])
                                                self._cr.execute(
                                                    "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date >= %s and (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date <= %s and employee_id = %s and state = 'validate'",
                                                    (date_start, date_end, emp.id))
                                                unique_leave = self._cr.fetchall()
                                                if unique_leave:
                                                    no_pay_time = no_pay_time + 0
                                                else:
                                                    no_pay_time = no_pay_time + diff

                                else:
                                    no_pay_time = no_pay_time + 0

                        date_from_date = date_from_date + timedelta(days=1)

            if no_pay_time > 0:
                nopay_line = {
                    'code': 'NOPAY',
                    'contract_id': contract.id,
                    'number_of_days': no_pay_hrs_,
                    'number_of_hours': no_pay_time,
                    'name': 'Total No Pay Hours'
                }
                res.append(nopay_line)

            # calculate late in

            late_policy_obj = self.env['hr.late.configuration'].search([])
            monthly_late_obj = self.env['hr.late.attendance'].search([])

            if late_policy_obj.is_late == 'yes':
                # start_year = date_from_late.strftime("%Y")
                # start_month = date_from_late.month
                # end_month = datetime.strptime(date_to, '%Y-%m-%d').strftime("%B")
                # end_year = datetime.strptime(date_to, '%Y-%m-%d').strftime("%Y")
                end_month = datetime.strptime(date_to, '%Y-%m-%d').month
                end_year = datetime.strptime(date_to, '%Y-%m-%d').year

                if late_policy_obj.case_one == 'late_covered' or late_policy_obj.case_one == 'time_range' or late_policy_obj.case_one == 'late_days_for_month':
                    if late_policy_obj.salary_deduction:
                        for line in hr_attendance_obj.search(
                                [('date', '>=', date_from), ('date', '<=', date_to),
                                 ('employee_id', '=', contract.employee_id.id)]):
                            late_time = late_time + line.late_time_store_value

                elif late_policy_obj.case_one == 'monthly_late':
                    if late_policy_obj.salary_deduction:
                        if end_month > 1:
                            month = end_month - 1
                            for line in monthly_late_obj.search([('month', '=', str(month)),
                                                                 ('year', '=', str(end_year)),
                                                                 ('employee_id', '=', contract.employee_id.id)]):
                                late_time = late_time + line.duration
                        elif end_month == 1:
                            month = 12
                            year = end_year - 1
                            for line in monthly_late_obj.search([('month', '=', str(month)),
                                                                 ('year', '=', str(year)),
                                                                 ('employee_id', '=', contract.employee_id.id)]):
                                late_time = late_time + line.duration

                if late_time > 0:
                    late_hrs_per_day = normal_hours / days
                    num_of_late_days = late_time / late_hrs_per_day
                    late_line = {
                        'code': 'LATE',
                        'contract_id': contract.id,
                        'number_of_days': num_of_late_days,
                        'number_of_hours': late_time,
                        'name': 'Total Late Hours'
                    }
                    res.append(late_line)

            # calculate remaining late days for a month
            if late_policy_obj.is_late == 'yes' and late_policy_obj.case_one == 'late_days_for_month':

                month = datetime.strptime(date_to, '%Y-%m-%d').month
                month = calendar.month_name[month]
                year = datetime.strptime(date_to, '%Y-%m-%d').year

                employee_obj = self.env['monthly.late.days'].search([('employee_name', '=', contract.employee_id.id),
                                                                     ('month', '=', str(month))], limit=1)
                late_line_for_days_remaining_leaves = {
                    'code': 'LATE_REM',
                    'contract_id': contract.id,
                    'number_of_days': 0,
                    'number_of_hours': employee_obj.late_days_per_month,
                    'name': 'Total Remaining Days'
                }
                res.append(late_line_for_days_remaining_leaves)

        return res

