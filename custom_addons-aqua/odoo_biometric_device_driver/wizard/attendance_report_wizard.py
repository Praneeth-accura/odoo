from odoo import api, fields, models, _
import sys
from datetime import datetime, timedelta
import xlsxwriter
import base64
from odoo.tools import misc
import os
import pytz
import math
from dateutil.relativedelta import relativedelta

class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'

    report_from = fields.Selection([('attend','From Attendance'),
                                    ('log','From Log')],
                                   string='Report', required=True, default='attend')
    date_from = fields.Datetime('From', required=True, default=datetime.today())
    date_to = fields.Datetime('To', required=True, default=datetime.today())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)

    @api.onchange('report_from')
    def onchange_report(self):
        day = int(datetime.today().strftime('%-d'))
        date_from = datetime.today() + relativedelta(day=day-1, hour=00, minute=00, second=00)
        date_to = datetime.today() + relativedelta(day=day-1, hour=23, minute=59, second=59)
        self.date_from = date_from.strftime("%Y-%m-%d %H:%M:%S")
        self.date_to = date_to.strftime("%Y-%m-%d %H:%M:%S")

    @api.multi
    def export_attendance_xlsx(self, fl=None):
        if fl == None:
            fl = ''
        if self.report_from == 'log':
            date_from = self.convert_timezone_report(self.date_from)
            date_to = self.convert_timezone_report(self.date_to)
            domain = [('punching_time','>=', date_from[0]),
                      ('punching_time','<=', date_to[0])]
            attendance_logs = self.env['attendance.log'].search(domain)
            fl = self.print_attendance_logs(attendance_logs)
        elif self.report_from == 'attend':
            date_from = self.convert_timezone_report(self.date_from)
            date_to = self.convert_timezone_report(self.date_to)
            domain = [
                ('check_in','>=', date_from[0]),
                ('check_out','<=', date_to[0])]
            attendances = self.env['hr.attendance'].search(domain)
            fl = self.print_attendance_records(attendances)

        my_report_data = open(fl,'rb+')
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        # To remove those previous saved report data from table. To avoid unwanted storage
        #         self._cr.execute("TRUNCATE attendance_report_wizard CASCADE")
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True

        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(fl)
        return result

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        self.is_printed = False
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report.wizard',
            'target': 'new',
        }
        return result

    @api.multi
    def print_attendance_records(self, attendances):
        str_date1 = str(datetime.strptime(str(self.date_from),'%Y-%m-%d %H:%M:%S')  + timedelta(hours=5, minutes=30))
        date1 = datetime.strptime(str_date1,'%Y-%m-%d %H:%M:%S').date()
        day1 = date1.strftime('%d')
        month1 = date1.strftime('%B')
        year1 = date1.strftime('%Y')
        str_date2 = str(datetime.strptime(str(self.date_to),'%Y-%m-%d %H:%M:%S')  + timedelta(hours=5, minutes=30))
        date2 = datetime.strptime(str_date2,'%Y-%m-%d %H:%M:%S').date()
        day2 = date2.strftime('%d')
        month2 = date2.strftime('%B')
        year2 = date2.strftime('%Y')
        fl = os.path.join(os.path.dirname(__file__),
                          'Attendance from '+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2+'('+str(datetime.today())+')'+'.xlsx')
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
                                                'bold': True})
        border = workbook.add_format({'border':1})
        #         date_format = workbook.add_format({'num_format': 'dd-mm-yy hh:mm:ss'})

        worksheet.set_column('G:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:G', 20,border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:G1', "Attendance sheet from "+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2, bold)

        row = 2
        col = 0
        worksheet.merge_range(row,col,row+1,col+1, "Name of Employee", font_bold_center)
        worksheet.merge_range(row,col+2,row+1,col+2, "Check In", font_bold_center)
        worksheet.merge_range(row,col+3,row+1,col+3, "Check_out", font_bold_center)
        worksheet.merge_range(row,col+4,row+1,col+4, "Difference", font_bold_center)

        row += 2
        for attendance in attendances:
            worksheet.merge_range(row,col,row,col+1, attendance.employee_id.name, font_left)
            if attendance.check_in:
                check_in = self.convert_timezone(attendance.check_in)
            else:
                check_in = ['***No Check In***']
            worksheet.write(row,col+2, check_in[0], font_center)
            if attendance.check_out:
                check_out = self.convert_timezone(attendance.check_out)
            else:
                check_out = ['***No Check Out***']

            worksheet.write(row,col+3, check_out[0], font_center)

            factor = attendance.worked_hours < 0 and -1 or 1
            val = abs(attendance.worked_hours)
            hour, minute = (factor * int(math.floor(val)), int(round((val % 1) * 60)))
            if minute == 60:
                hour += 1
                minute = 0
            diff = ''
            str_min = ''
            if minute <= 9:
                str_min = '0'+str(minute)
            else:
                str_min = str(minute)
            if hour <= 9:
                diff = '0'+str(hour)+':'+str_min
            else:
                diff = str(hour)+':'+str_min

            worksheet.write(row,col+4, diff, font_center)
            row += 1

        workbook.close()
        return fl

    @api.one
    def convert_timezone_report(self, time):
        atten_time = datetime.strptime(time , '%Y-%m-%d %H:%M:%S')
        atten_time = datetime.strptime(
            atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(
            self.env.user.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time = datetime.strptime(
            utc_dt, "%Y-%m-%d %H:%M:%S")
        atten_time = fields.Datetime.to_string(atten_time)
        return atten_time

    @api.one
    def convert_timezone(self, time):
        atten_time = datetime.strptime(time , '%Y-%m-%d %H:%M:%S')
        atten_time = datetime.strptime(
            atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(
            self.env.user.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        atten_time = fields.Datetime.to_string(atten_time + local_dt.tzinfo._utcoffset)
        return atten_time

    @api.multi
    def print_attendance_logs(self, logs):
        str_date1 = str(datetime.strptime(str(self.date_from),'%Y-%m-%d %H:%M:%S')  + timedelta(hours=5, minutes=30))
        date1 = datetime.strptime(str_date1,'%Y-%m-%d %H:%M:%S').date()
        day1 = date1.strftime('%d')
        month1 = date1.strftime('%B')
        year1 = date1.strftime('%Y')
        str_date2 = str(datetime.strptime(str(self.date_to),'%Y-%m-%d %H:%M:%S')  + timedelta(hours=5, minutes=30))
        date2 = datetime.strptime(str_date2,'%Y-%m-%d %H:%M:%S').date()
        day2 = date2.strftime('%d')
        month2 = date2.strftime('%B')
        year2 = date2.strftime('%Y')
        fl = os.path.join(os.path.dirname(__file__),'Attendance Log from '+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2+'('+str(datetime.today())+')'+'.xlsx')
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
                                                'bold': True})
        border = workbook.add_format({'border':1})
        #         date_format = workbook.add_format({'num_format': 'dd-mm-yy hh:mm:ss'})

        worksheet.set_column('E:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:E', 20,border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:E1', "Attendance Log from "+day1+'-'+month1+'-'+year1+' to '+day2+'-'+month2+'-'+year2, bold)

        row = 2
        col = 0
        worksheet.merge_range(row,col,row+1,col+1, "Name of Employee", font_bold_center)
        worksheet.merge_range(row,col+2,row+1,col+2, "Punching Time", font_bold_center)
        worksheet.merge_range(row,col+3,row+1,col+3, "Status", font_bold_center)
        worksheet.merge_range(row,col+4,row+1,col+4, "Device", font_bold_center)

        row += 2
        for log in logs:
            self._cr.execute(
                " select * from hr_holidays where (((date_from + INTERVAL '5 hours' + INTERVAL '30 minutes')::date <=" + "'" + punching_time + "' and" + "'" + punching_time + "'<=(date_to + INTERVAL '5 hours' + INTERVAL '30 minutes')::date ) and state='validate' and employee_id= '" + str(
                    log.employee_id.id))
            unique_leave_result = self.env.cr.fetchall()

            worksheet.merge_range(row,col,row,col+1, log.employee_id.name, font_left)
            if log.punching_time:
                punching_time = self.convert_timezone(log.punching_time)
            else:
                punching_time = ['***No Status***']
            worksheet.write(row,col+2, punching_time[0], font_center)
            if log.status == "0":
                status = 'Check In'
            elif log.status == "1":
                status = 'Check Out'
            else:
                status = 'Undefined'
            worksheet.write(row,col+3, status, font_center)
            worksheet.write(row,col+4, log.device.name, font_center)
            row += 1

        workbook.close()
        return fl