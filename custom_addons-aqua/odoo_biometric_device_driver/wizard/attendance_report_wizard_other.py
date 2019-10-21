from odoo import api, fields, models, _
from datetime import datetime, timedelta, time
import xlsxwriter
import math
import os
import calendar

def float_to_time(float_hour):
    if float_hour >= 0 and float_hour <=23.99:
        res = time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)
        return str(res)[0:5]
    elif float_hour < 0:
        float_hour = float_hour * -1
        res = time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)
        return '-' + str(res)[0:5]


class AttendanceReportWizard(models.TransientModel):
    _inherit = 'attendance.report.wizard'

    report_from = fields.Selection(selection_add=[('att_details', 'Attendance Details'),
                                                  ('att_summary','Attendance Summary'),
                                                  ('monthly_late_attendance', 'Monthly Late Attendance'),
                                                  ('weekly_overtime', 'Weekly Over Time'),
                                                  ('monthly_overtime', 'Monthly Over Time')])
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_id = fields.Many2one('hr.department', string='Department')
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], string='Month')
    year = fields.Selection([(2017, '2017'),
                             (2018, '2018'),
                             (2019, '2019'),
                             (2020, '2020')], string='Year')

    @api.multi
    def export_attendance_xlsx(self, fl=None):
        self.env['attendance.calc.wizard'].calculate_attendance()
        if self.report_from == 'att_details':
            fl = self.print_attendance_details()
        elif self.report_from == 'att_summary':
            fl = self.print_attendance_summary()
        elif self.report_from == 'monthly_late_attendance':
            fl = self.print_monthly_late_attendance()
        elif self.report_from == 'weekly_overtime':
            fl = self.print_weekly_overtime()
        elif self.report_from == 'monthly_overtime':
            fl = self.print_monthly_overtime()
        res = super(AttendanceReportWizard, self).export_attendance_xlsx(fl)
        return res

    @api.multi
    def _get_attendance(self, date_from, date_to):
        domain = [('check_in','>=', date_from),('check_out','>=', date_from),
                  ('check_in','<=', date_to),('check_out','<=', date_to)]
        attendances = self.env['hr.attendance'].search(domain, order='emp_code')
        return attendances

    @api.multi
    def print_attendance_details(self):
        str_date1 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)))
        str_date2 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)))
        date1 = datetime.strptime(str_date1,'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str_date2,'%Y-%m-%d %H:%M:%S').date()
        fl = os.path.join(os.path.dirname(__file__),'Attendance Details from '+date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y')+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True,'border':1,
                                    'align':'center'})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_left_bold = workbook.add_format({'align':'left',
                                              'border':1,
                                              'font_size':10,
                                              'bold': True})
        font_left_grey = workbook.add_format({'align':'left',
                                              'border':1,
                                              'font_size':10,
                                              'bold': True,
                                              'bg_color': '#E8E8E8'})
        font_center = workbook.add_format({'align':'center',
                                           'border':1,
                                           'valign':'vcenter',
                                           'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                                'border':1,
                                                'valign':'vcenter',
                                                'font_size':12,
                                                'bold': True,
                                                'bg_color': '#B0B0B0'})
        border = workbook.add_format({'border':1})
        #         date_format = workbook.add_format({'num_format': 'dd-mm-yy hh:mm:ss'})

        worksheet.set_column('N:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:O', 20,border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:O1', "Attendance Details from "+date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y'), bold)

        row = 2
        col = 0
        worksheet.merge_range(row,col,row+1,col, "EMP NO", font_bold_center)
        worksheet.merge_range(row,col+1,row+1,col+1, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row,col+2,row+1,col+2, "DATE", font_bold_center)
        worksheet.merge_range(row,col+3,row+1,col+3, "SHIFT", font_bold_center)
        worksheet.merge_range(row,col+4,row+1,col+4, "ON DUTY", font_bold_center)
        worksheet.merge_range(row,col+5,row+1,col+5, "OFF DUTY", font_bold_center)
        worksheet.merge_range(row,col+6,row+1,col+6, "IN TIME", font_bold_center)
        worksheet.merge_range(row,col+7,row+1,col+7, "OUT TIME", font_bold_center)
        worksheet.merge_range(row,col+8,row+1,col+8, "WORKED HRS", font_bold_center)
        worksheet.merge_range(row,col+9,row+1,col+9, "LATE IN", font_bold_center)
        worksheet.merge_range(row,col+10,row+1,col+10, "LATE OUT", font_bold_center)
        worksheet.merge_range(row,col+11,row+1,col+11, "LATE HOURS", font_bold_center)
        worksheet.merge_range(row,col+12,row+1,col+12, "OT HOURS", font_bold_center)
        # worksheet.merge_range(row,col+11,row+1,col+11, "OT", font_bold_center)
        worksheet.merge_range(row,col+13,row+1,col+13, "ABSENT", font_bold_center)

        row += 2
        day = timedelta(days=1)
        employees = self.env['hr.employee'].search([], order='employee_code')
        self._cr.execute('SELECT DISTINCT(dayofweek) from resource_calendar_attendance')
        working_days = [int(workday[0]) for workday in self._cr.fetchall()]
        while date1 <= date2:
            att_employees = []
            date_from = datetime.combine(date1, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
            date_to = datetime.combine(date1, datetime.max.time()).strftime("%Y-%m-%d %H:%M:%S")
            worksheet.merge_range(row,col,row,col+13, date1.strftime('%d-%B-%Y'), font_left_grey)
            row += 1

            holiday_domain = [('date_from','>=', date_from),('date_to','>=', date_from),
                              ('date_from','<=', date_to),('date_to','<=', date_to),('state','=','validate')]
            holidays = self.env['hr.holidays'].search(holiday_domain)
            holiday_emp_ids = []
            if holidays:
                holiday_emp_ids = [leave.employee_id.id for leave in holidays]
            attendances = self._get_attendance(date_from, date_to)
            if date1.weekday() not in working_days and not attendances:
                date1 = date1 + day
                continue

            for att in attendances:
                worksheet.write(row,col, att.employee_id.employee_code, font_center)
                worksheet.write(row,col+1, att.employee_id.name, font_left)
                worksheet.write(row,col+2, date1.strftime('%d/%m/%Y'), font_center)
                worksheet.write(row,col+3, att.resource_calendar_id and att.resource_calendar_id.name or '', font_center)
                worksheet.write(row,col+4, float_to_time(att.on_duty), font_center)
                worksheet.write(row,col+5, float_to_time(att.off_duty), font_center)
                worksheet.write(row,col+6, float_to_time(att.in_time), font_center)
                worksheet.write(row,col+7, float_to_time(att.out_time), font_center)
                worksheet.write(row,col+8, float_to_time(att.worked_hours), font_center)
                worksheet.write(row,col+9, float_to_time(att.late_in), font_center)
                worksheet.write(row,col+10, float_to_time(att.late_out), font_center)
                worksheet.write(row,col+11, float_to_time(att.late_time_store_value), font_center)
                worksheet.write(row,col+12, float_to_time(att.ot_hour), font_center)
                # worksheet.write(row,col+11, 'Yes' if att.ot_applicable else 'No', font_center)
                worksheet.write(row,col+13, 'Present', font_center)

                att_employees.append(att.employee_id.id)
                row += 1

            if holiday_emp_ids:
                worksheet.merge_range(row,col,row,col+13, "Leave Employees", font_left_bold)
                row += 1
                for emp in self.env['hr.employee'].search([('id','in',holiday_emp_ids)], order='employee_code'):
                    worksheet.write(row,col, emp.employee_code, font_center)
                    worksheet.write(row,col+1, emp.name, font_left)
                    worksheet.write(row,col+2, date1.strftime('%d/%m/%Y'), font_center)
                    worksheet.write(row,col+3, emp.resource_calendar_id and emp.resource_calendar_id.name or '', font_center)
                    worksheet.write(row,col+4, '', font_center)
                    worksheet.write(row,col+5, '', font_center)
                    worksheet.write(row,col+6, '', font_center)
                    worksheet.write(row,col+7, '', font_center)
                    worksheet.write(row,col+8, '', font_center)
                    worksheet.write(row,col+9, '', font_center)
                    worksheet.write(row,col+10, '', font_center)
                    worksheet.write(row,col+11, '', font_center)
                    worksheet.write(row,col+12, '', font_center)
                    # worksheet.write(row,col+11, '', font_center)
                    worksheet.write(row,col+13, emp.current_leave_id.display_name, font_center)
                    row += 1


            if date1.weekday() not in working_days:
                date1 = date1 + day
                continue
            absent_employees = list(set(employees.ids)-set(att_employees)-set(holiday_emp_ids))
            if absent_employees:
                worksheet.merge_range(row,col,row,col+13, "Absent Employees", font_left_bold)
                row += 1
                for emp in self.env['hr.employee'].search([('id','in',absent_employees)], order='employee_code'):
                    worksheet.write(row,col, emp.employee_code, font_center)
                    worksheet.write(row,col+1, emp.name, font_left)
                    worksheet.write(row,col+2, date1.strftime('%d/%m/%Y'), font_center)
                    worksheet.write(row,col+3, emp.resource_calendar_id and emp.resource_calendar_id.name or '', font_center)
                    worksheet.write(row,col+4, '', font_center)
                    worksheet.write(row,col+5, '', font_center)
                    worksheet.write(row,col+6, '', font_center)
                    worksheet.write(row,col+7, '', font_center)
                    worksheet.write(row,col+8, '', font_center)
                    worksheet.write(row,col+9, '', font_center)
                    worksheet.write(row,col+10, '', font_center)
                    worksheet.write(row,col+11, '', font_center)
                    worksheet.write(row,col+12, '', font_center)
                    # worksheet.write(row,col+11, '', font_center)
                    worksheet.write(row,col+13, 'Absent', font_center)
                    row += 1
            date1 = date1 + day

        workbook.close()
        return fl

    @api.multi
    def _get_global_leave_days(self, working_hrs, from_date, to_date):
        global_leaves = 0
        self._cr.execute('SELECT DISTINCT(dayofweek) FROM resource_calendar_attendance WHERE calendar_id=%s',(working_hrs.resource_calendar_id.id,))
        working_days = [int(workday[0]) for workday in self._cr.fetchall()]
        start = datetime.strptime(from_date,'%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(to_date,'%Y-%m-%d %H:%M:%S')
        day = timedelta(days=1)
        while start <= end:
            if start.weekday() not in working_days:
                global_leaves += 1
            start = start + day

        for leave in working_hrs.resource_calendar_id.global_leave_ids:
            date1 = fields.Datetime.to_string(fields.Datetime.context_timestamp(leave, fields.Datetime.from_string(leave.date_from)))
            date2 = fields.Datetime.to_string(fields.Datetime.context_timestamp(leave, fields.Datetime.from_string(leave.date_to)))
            if date1 >= from_date and date2 >= from_date and date1 <= to_date and date2 <= to_date:
                date1 = datetime.strptime(date1,'%Y-%m-%d %H:%M:%S').date()
                date2 = datetime.strptime(date2,'%Y-%m-%d %H:%M:%S').date()
                if (date2 - date1).days == 0:
                    global_leaves += 1
                else:
                    global_leaves += (date2 - date1).days
        return global_leaves

    @api.multi
    def _get_days(self, employee_id):
        result = []
        employee = self.env['hr.employee'].browse(employee_id)
        str_date1 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)))
        str_date2 = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)))
        #leave days calculation
        leave_days = 0
        holiday_domain = [('date_from','>=', str_date1),('date_to','>=', str_date1),
                          ('date_from','<=', str_date2),('date_to','<=', str_date2),
                          ('state','=','validate'),('employee_id','=',employee_id)]
        holidays = self.env['hr.holidays'].search(holiday_domain)
        for leave in holidays:
            leave_days += leave.number_of_days_temp
        result.append(leave_days)
        #present days calculation
        where_condn = "employee_id=%s AND check_in >=%s::Date AND check_out >=%s::Date AND check_in <=%s::Date AND check_out <=%s::Date"
        self._cr.execute('SELECT COUNT(DISTINCT(check_in::Date)) FROM hr_attendance WHERE '+where_condn,(employee_id,self.date_from,self.date_from,
                                                                                                         self.date_to, self.date_to))
        res = self._cr.fetchall()

        where_condn_new = "employee_id=%s AND check_in >=%s AND check_out <=%s"
        self._cr.execute('select count(id) from hr_attendance where ' + where_condn_new,
                         (employee_id, self.date_from, self.date_to))
        res2 = self._cr.fetchall()
        present_days = int(res2[0][0])
        result.append(present_days)
        #absent days calculation
        date1 = datetime.strptime(str_date1,'%Y-%m-%d %H:%M:%S').date()
        date2 = datetime.strptime(str_date2,'%Y-%m-%d %H:%M:%S').date()
        total_days = (date2 - date1).days + 1

        working_hrs = employee.working_history_ids
        global_leaves = 0
        if working_hrs and len(working_hrs.ids) == 1 and not working_hrs.to_date:
            global_leaves = self._get_global_leave_days(working_hrs, str_date1, str_date2)
        else:
            for schedule in working_hrs:
                if schedule.to_date:
                    if self.date_from >= schedule.from_date and self.date_to >= schedule.from_date and \
                            self.date_from <= schedule.to_date and self.date_to <= schedule.to_date:
                        global_leaves = self._get_global_leave_days(schedule, str_date1, str_date2)
                        break
                    elif self.date_from >= schedule.from_date and self.date_from <= schedule.to_date and \
                            self.date_to > schedule.to_date:
                        end_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(schedule, fields.Datetime.from_string(schedule.to_date)))
                        global_leaves += self._get_global_leave_days(schedule, str_date1, end_date)
                    elif self.date_to >= schedule.from_date and self.date_to <= schedule.to_date and \
                            self.date_from < schedule.from_date:
                        begin_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(schedule, fields.Datetime.from_string(schedule.from_date)))
                        global_leaves += self._get_global_leave_days(schedule, begin_date, str_date2)
                else:
                    if self.date_from >= schedule.from_date and self.date_to >= schedule.from_date:
                        global_leaves = self._get_global_leave_days(schedule, str_date1, str_date2)
                        break
                    elif self.date_from < schedule.from_date and self.date_to >=schedule.from_date:
                        begin_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(schedule, fields.Datetime.from_string(schedule.from_date)))
                        global_leaves += self._get_global_leave_days(schedule, begin_date, str_date2)

        absent_days = total_days - leave_days - present_days - global_leaves
        result.append(abs(absent_days))
        return result

    @api.one
    def _get_ot_hours(self, employee_id):
        ot_hrs = 0.0
        domain = [('employee_id','=',employee_id),('ot_applicable','=',True),
                  ('check_in','>=', self.date_from),('check_out','>=', self.date_from),
                  ('check_in','<=', self.date_to),('check_out','<=', self.date_to)]
        attendances = self.env['hr.attendance'].search(domain)
        for att in attendances:
            if att.ot_applicable:
                ot_hrs += att.ot_hour
        return str(float_to_time(ot_hrs))

    @api.one
    def _get_late_hours(self, employee_id):
        late_hrs = 0.0
        domain = [('employee_id','=',employee_id),
                  ('check_in','>=', self.date_from),('check_out','>=', self.date_from),
                  ('check_in','<=', self.date_to),('check_out','<=', self.date_to)]
        attendances = self.env['hr.attendance'].search(domain)
        for att in attendances:
            late_hrs += att.late_time_store_value
        return str(float_to_time(late_hrs))

    @api.multi
    def print_attendance_summary(self):
        str_date1 = str(self.date_from)
        date1 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)).date()
        str_date2 = str(self.date_to)
        date2 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)).date()
        fl = os.path.join(os.path.dirname(__file__),'Attendance Summary from '+date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y')+'('+str(datetime.today())+')'+'.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True,'border':1,
                                    'align':'center'})
        font_left = workbook.add_format({'align':'left',
                                         'border':1,
                                         'font_size':12})
        font_center = workbook.add_format({'align':'center',
                                           'border':1,
                                           'valign':'vcenter',
                                           'font_size':12})
        font_bold_center = workbook.add_format({'align':'center',
                                                'border':1,
                                                'valign':'vcenter',
                                                'font_size':12,
                                                'bold': True,
                                                'bg_color': '#B0B0B0'})
        border = workbook.add_format({'border':1})
        #         date_format = workbook.add_format({'num_format': 'dd-mm-yy hh:mm:ss'})

        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:G', 20,border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:G1', "Attendance Summary from "+date1.strftime('%d-%B-%Y')+' to '+date2.strftime('%d-%B-%Y'), bold)

        row = 2
        col = 0
        worksheet.merge_range(row,col,row+1,col, "DATE RANGE", font_bold_center)
        worksheet.merge_range(row,col+1,row+1,col+1, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row,col+2,row+1,col+2, "NO OF DAYS ABSENT", font_bold_center)
        worksheet.merge_range(row,col+3,row+1,col+3, "NO OF DAYS LEAVE", font_bold_center)
        worksheet.merge_range(row,col+4,row+1,col+4, "NO OF DAYS PRESENT", font_bold_center)
        worksheet.merge_range(row,col+5,row+1,col+5, "OT HRS", font_bold_center)
        worksheet.merge_range(row,col+6,row+1,col+6, "LATE", font_bold_center)

        row += 2
        if self.employee_ids:
            employees = self.employee_ids
        elif self.department_id and self.department_id.member_ids:
            employees = self.department_id.member_ids
        else:
            employees = self.env['hr.employee'].search([], order='employee_code')
        for emp in employees:
            no_of_days = self._get_days(emp.id)
            worksheet.write(row,col, date1.strftime('%Y-%m-%d') + ' - ' + date2.strftime('%Y-%m-%d'), font_center)
            worksheet.write(row,col+1, emp.name, font_left)
            worksheet.write(row,col+2, no_of_days[2], font_center)
            worksheet.write(row,col+3, no_of_days[0], font_center)
            worksheet.write(row,col+4, no_of_days[1], font_center)
            worksheet.write(row,col+5, self._get_ot_hours(emp.id)[0], font_center)
            worksheet.write(row,col+6, self._get_late_hours(emp.id)[0], font_center)
            row += 1

        workbook.close()
        return fl

    @api.multi
    def print_monthly_late_attendance(self):
        date1 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)).date()
        date2 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)).date()
        string_of_month = dict(self.fields_get(allfields=['month'])['month']['selection'])[str(self.month)]
        fl = os.path.join(os.path.dirname(__file__), 'Monthly Late Time Of ' + string_of_month + ' - ' + str(self.year) + '.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#B0B0B0'})
        border = workbook.add_format({'border': 1})

        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:G', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:G1', 'Monthly Late Time Of ' + string_of_month + ' - ' + str(self.year), bold)

        row = 2
        col = 0
        worksheet.merge_range(row, col, row + 1, col, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "TOTAL DURATION OF LATE ATTENDANCE", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "MONTH", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "YEAR", font_bold_center)

        row += 2
        employee_obj = self.env['hr.employee'].search([])
        for employee in employee_obj:
            duration = 0

            for line in employee.late_list:
                month = int(line.month)
                year = int(line.year)
                if month == int(self.month) and year == self.year:
                    duration = line.duration
                    duration = str(float_to_time(duration))
            worksheet.write(row, col, employee.name, font_left)
            worksheet.write(row, col + 1, duration, font_center)
            worksheet.write(row, col + 2, self.month, font_center)
            worksheet.write(row, col + 3, self.year, font_center)
            row += 1

        workbook.close()
        return fl

    @api.multi
    def print_weekly_overtime(self):
        date1 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)).date()
        date2 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)).date()
        string_of_month = dict(self.fields_get(allfields=['month'])['month']['selection'])[str(self.month)]
        fl = os.path.join(os.path.dirname(__file__), 'Weekly Overtime Of ' + string_of_month + ' - ' + str(self.year) + '.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#B0B0B0'})
        border = workbook.add_format({'border': 1})

        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:G', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:G1', 'Weekly Overtime Of ' + string_of_month + ' - ' + str(self.year), bold)

        row = 2
        col = 0
        worksheet.merge_range(row, col, row + 1, col, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "TOTAL DURATION OF OVERTIME/WEEK", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "WEEK", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "MONTH", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "YEAR", font_bold_center)

        row += 2
        employee_obj = self.env['hr.employee'].search([])
        for employee in employee_obj:
            domain = [('month', '=', self.month), ('year', '=', self.year), ('employee_id', '=', employee.id)]
            for records in employee._over_time_per_week_list.search(domain):
                duration = str(float_to_time(float(records.duration)))
                worksheet.write(row, col, employee.name, font_left)
                worksheet.write(row, col + 1, duration, font_center)
                worksheet.write(row, col + 2, records.week, font_center)
                worksheet.write(row, col + 3, self.month, font_center)
                worksheet.write(row, col + 4, self.year, font_center)
                row += 1

        workbook.close()
        return fl

    @api.multi
    def print_monthly_overtime(self):
        date1 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from)).date()
        date2 = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to)).date()
        string_of_month = dict(self.fields_get(allfields=['month'])['month']['selection'])[str(self.month)]
        fl = os.path.join(os.path.dirname(__file__),
                          'Monthly Overtime Of ' + string_of_month + ' - ' + str(self.year) + '.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#B0B0B0'})
        border = workbook.add_format({'border': 1})

        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:E', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:E1', 'Monthly Overtime Of ' + string_of_month + ' - ' + str(self.year), bold)

        row = 2
        col = 0
        worksheet.merge_range(row, col, row + 1, col, "EMPLOYEE NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "TOTAL DURATION OF OVERTIME", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "MONTH", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "YEAR", font_bold_center)

        row += 2
        employee_obj = self.env['hr.employee'].search([])
        for employee in employee_obj:
            month = calendar.month_name[int(self.month)]
            domain = [('month', '=', month), ('year', '=', self.year), ('employee_id', '=', employee.id)]
            for records in employee.monthly_overtime_list.search(domain):
                if float(records.duration) >= 24.00:
                    total_days = str(int((float(records.duration) / 24))) + ' Days '
                    balance_hours = str(float_to_time(float(records.duration) % 24))
                    duration = total_days + balance_hours
                else:
                    duration = str(float_to_time(float(records.duration)))
                worksheet.write(row, col, employee.name, font_left)
                worksheet.write(row, col + 1, duration, font_center)
                worksheet.write(row, col + 2, self.month, font_center)
                worksheet.write(row, col + 3, self.year, font_center)
                row += 1

        workbook.close()
        return fl







