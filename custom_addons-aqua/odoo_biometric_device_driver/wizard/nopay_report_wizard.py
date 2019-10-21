from __future__ import division
from odoo import fields, api, models
from datetime import datetime, date, time, timedelta
import xlsxwriter
import base64
from odoo.tools import misc
import os
import math


def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)

def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)

class NopayWizard(models.TransientModel):
    _name = 'nopay.report.wizard'

    report_type = fields.Selection([('employee', 'Employee'),
                                    ('department', 'Department')])
    date_from = fields.Datetime('From', required=True, default=datetime.today())
    date_to = fields.Datetime('To', required=True, default=datetime.today())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_id = fields.Many2one('hr.department', string='Department')

    @api.multi
    def export_nopay_xlsx(self, fl = None):
        if fl == None:
            fl = ''
        if self.report_type == 'employee':
            fl = self.print_nopay_records()
        elif self.report_type == 'department':
            fl = self.print_nopay_records()

        my_report_data = open(fl, 'rb+')
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True

        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'nopay.report.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(fl)
        return result

    @api.multi
    def print_nopay_records(self):
        str_date1 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)))
        str_date2 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)))
        date1 = datetime.strptime(str_date1,'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str_date2,'%Y-%m-%d %H:%M:%S').date()
        fl = os.path.join(os.path.dirname(__file__), 'Nopay Details from ' +date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y')+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        border = workbook.add_format({'border': 1})
        bold = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        font_left = workbook.add_format({'align': 'left', 'border': 1, 'font_size': 12})
        font_center = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12})
        font_bold_center = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12,
                                                'bold': True})
        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:E', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:E1', 'Nopay Details from ' +date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y')+'('+str(datetime.today())+')', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "HOURS", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "DAYS", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "STATUS", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "DATE", font_bold_center)

        row += 2
        nopay_policy_obj = self.env['hr.nopay.configuration'].search([])
        attendance_obj = self.env['hr.attendance'].search(
            [('check_in', '>=', self.date_from), ('check_out', '<=', self.date_to)])
        employee_obj = self.env['hr.employee']
        schedule_history_obj = self.env['schedule.history']

        if self.report_type == 'employee':
            if self.employee_ids:
                employees = self.employee_ids
            else:
                employees = employee_obj.search([])
        elif self.report_type == 'department':
            employees = employee_obj.search([('department_id', '=', self.department_id.id)])

        if employees:
            date_from = self.date_from
            date_from = date_from
            day = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').weekday()
            from_date_day = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').weekday()
            day_start = self.date_from
            day_end = self.date_to

            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').date()
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').date()
            date_range_difference = (to_date - from_date).days
            days = 0
            status = ""
            nopay_hours = 0
            nopay_days = 0

            for emp in employees:
                date_from_date = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
                for days in range(0, date_range_difference + 1):
                    attendance_obj = self.env['hr.attendance'].search([('date', '=', date_from_date), ('employee_id', '=', emp.id)], order="id asc")
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
                                shift_obj = self.env['schedule.history'].search([('from_date', '<=',  attendance.check_in),
                                                                     ('to_date', '>=',  attendance.check_in),
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
                                        check_out_date = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').date()

                                        if schedule_history.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                            diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                        elif schedule_history.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                            diff = (shift_period.hour_to + 24) - shift_period.hour_from
                                        else:
                                            diff = shift_period.hour_to - shift_period.hour_from

                                        if nopay_policy_obj.less_working_hours:
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
                                                            nopay_hours = float_to_time(diff - ((to_dates - from_dates) + attendance.worked_hours))
                                                            status = "Half day or short leave"
                                                            nopay_hours_as_float = diff - ((to_dates - from_dates) + attendance.worked_hours)
                                                            nopay_days = nopay_hours_as_float / diff
                                                        else:
                                                            nopay_days = 0
                                                            nopay_hours = 0
                                                            status = "Present"
                                                    else:
                                                        nopay_hours = float_to_time(diff - attendance.worked_hours)
                                                        nopay_hours_as_float = diff - attendance.worked_hours
                                                        nopay_days = nopay_hours_as_float / diff
                                                        status = "Less Working Hours"

                                                elif evening:
                                                    to_dates = evening[0][7]
                                                    if (schedule_history.from_date <= to_dates and schedule_history.to_date >= to_dates):
                                                        date_tos = datetime.strptime(to_dates, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                            hours=5, minutes=30)
                                                        date_tos = convert_to_float(str(date_tos))
                                                        difference = date_tos - shift_period.hour_from + attendance.worked_hours
                                                        if difference < diff:
                                                            nopay_hours = float_to_time(diff - difference)
                                                            nopay_hours_as_float = diff - difference
                                                            nopay_days = nopay_hours_as_float / diff
                                                            status = "Half day or short leave"
                                                        else:
                                                            nopay_days = 0
                                                            nopay_hours = 0
                                                            status = "Present"
                                                    else:
                                                        nopay_hours = float_to_time(diff - attendance.worked_hours)
                                                        nopay_hours_as_float = diff - attendance.worked_hours
                                                        nopay_days = nopay_hours_as_float / diff
                                                        status = "Less Working Hours"

                                                elif morning:
                                                    from_dates = morning[0][6]
                                                    if (
                                                            schedule_history.from_date <= from_dates and schedule_history.to_date >= from_dates):
                                                        date_froms = datetime.strptime(from_dates,
                                                                                       '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                                        minutes=30)
                                                        date_froms = convert_to_float(str(date_froms))
                                                        difference = shift_period.hour_to - date_froms + attendance.worked_hours
                                                        if difference < diff:
                                                            nopay_hours = float_to_time(diff - difference)
                                                            nopay_hours_as_float = diff - difference
                                                            status = "Half day or short leave"
                                                            nopay_days = nopay_hours_as_float / diff
                                                        else:
                                                            nopay_days = 0
                                                            nopay_hours = 0
                                                            status = "Present"
                                                    else:
                                                        nopay_hours = float_to_time(diff - attendance.worked_hours)
                                                        nopay_hours_as_float = diff - attendance.worked_hours
                                                        nopay_days = nopay_hours_as_float / diff
                                                        status = "Less Working Hours"

                                                else:
                                                    nopay_hours = float_to_time(diff - attendance.worked_hours)
                                                    nopay_hours_as_float = diff - attendance.worked_hours
                                                    nopay_days = nopay_hours_as_float / diff
                                                    status = "Less Working Hours"

                                            else:
                                                nopay_days = 0
                                                nopay_hours = 0
                                                status = "Present"

                                worksheet.write(row, col, emp.name, font_left)
                                worksheet.write(row, col + 1, str(nopay_hours), font_left)
                                worksheet.write(row, col + 2, nopay_days, font_left)
                                worksheet.write(row, col + 3, status, font_left)
                                worksheet.write(row, col + 4, str(date_from_date), font_left)
                                row += 1

                            elif attendance.check_in and not attendance.check_out or not attendance.check_in and attendance.check_out:
                                if nopay_policy_obj.one_finger:
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

                                                nopay_hours = float_to_time(diff)
                                                nopay_hours_as_float = diff
                                                nopay_days = nopay_hours_as_float /diff
                                                status = "Present - Only One Finger"
                                    else:
                                        nopay_hours = 0


                                worksheet.write(row, col, emp.name, font_left)
                                worksheet.write(row, col + 1, str(nopay_hours), font_left)
                                worksheet.write(row, col + 2, nopay_days, font_left)
                                worksheet.write(row, col + 3, status, font_left)
                                worksheet.write(row, col + 4, str(date_from_date), font_left)
                                row += 1

                    else:
                        if nopay_policy_obj.no_leave == True or nopay_policy_obj.probation == True or nopay_policy_obj.leave_not_approved == True or nopay_policy_obj.no_leaves == True:
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
                                            nopay_hours = 0
                                            nopay_days = 0
                                            status = "Day not in schedule"
                                        else:
                                            unique_leave = self.env['hr.holidays'].search(
                                                [('employee_id', '=', emp.id), ('date_from', '<=', date_from),
                                                 ('type', '=', 'remove'), ('date_to', '>=', date_from),
                                                 ('state', '=', 'validate')])
                                            if unique_leave:
                                                nopay_hours = 0
                                                nopay_days = 0
                                                status = "Full Day Leave"
                                            else:
                                                nopay_hours = float_to_time(diff)
                                                nopay_hours_as_float = diff
                                                nopay_days = nopay_hours_as_float / diff
                                                status = "Absent"
                                worksheet.write(row, col, emp.name, font_left)
                                worksheet.write(row, col + 1, str(nopay_hours), font_left)
                                worksheet.write(row, col + 2, nopay_days, font_left)
                                worksheet.write(row, col + 3, status, font_left)
                                worksheet.write(row, col + 4, str(date_from_date), font_left)
                                row += 1

                            else:
                                nopay_hours = 0
                                nopay_days = 0
                                status = "Not Scheduled"

                                worksheet.write(row, col, emp.name, font_left)
                                worksheet.write(row, col + 1, str(nopay_hours), font_left)
                                worksheet.write(row, col + 2, nopay_days, font_left)
                                worksheet.write(row, col + 3, status, font_left)
                                worksheet.write(row, col + 4, str(date_from_date), font_left)
                                row += 1


                    date_from_date = date_from_date + timedelta(days=1)

        workbook.close()
        return fl

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        self.is_printed = False
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'nopay.report.wizard',
            'target': 'new',
        }
        return result









