from odoo import models, fields, api, exceptions, _
import math
from datetime import datetime, time, timedelta
from time import mktime


def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)


def convert_date_to_float(date_obj):
    obj = datetime.datetime.strptime(str(date_obj), '%H:%M:%S')
    float_value = float(0.00)

    float_value += float(obj.hour) * 3600
    float_value += float(obj.minute) * 60
    float_value += float(obj.second)
    return float(float_value)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    date = fields.Date('Date')
    resource_calendar_id = fields.Many2one('resource.calendar', compute='_get_resource_and_hrs',
                                           readonly=True, string='Working Hrs')
    on_duty = fields.Float('On Duty', compute='_get_resource_and_hrs', readonly=True, default=0.0)
    off_duty = fields.Float('Off Duty', compute='_get_resource_and_hrs', readonly=True, default=0.0)
    late_time = fields.Float('Late Hours', compute='_get_late_time', readonly=True, default=0.0)
    ot_time = fields.Float('OT Hours', compute='_get_ot_time', readonly=True, default=0.0)
    ot_hour = fields.Float('OT Time', readonly=True, default=0.0)
    in_time = fields.Float('In Time', compute='_get_in_time', readonly=True)
    out_time = fields.Float('Out Time', compute='_get_out_time', readonly=True)
    late_in = fields.Float('Late In', compute='_get_in_time', readonly=True)
    late_out = fields.Float('Late Out', compute='_get_out_time', readonly=True)
    ot_applicable = fields.Boolean('OT Eligible', default=False, compute='_check_ot', readonly=True, store=True)
    emp_code = fields.Char('Employee Code', related='employee_id.employee_code', store=True)
    is_calculated = fields.Boolean(string='Is Calculated', default=False)
    late_time_store_value = fields.Float(string='Late Time', invisible=True)
    is_deduct = fields.Boolean(string='is deduct', default=False)
    number_of_shift = fields.Integer(string='Number of shift')


    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                pass
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    pass


    @api.multi
    @api.depends('check_in', 'check_out')
    def _check_ot(self):
        for att in self:
            if att.check_in and att.check_out:
                check_in = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(att, fields.Datetime.from_string(att.check_in)))
                check_out = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(att, fields.Datetime.from_string(att.check_out)))
                check_in = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
                check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
                if check_in.weekday() == 6 or check_out.weekday() == 6:
                    att.ot_applicable = True

    @api.multi
    @api.depends('check_out')
    def _get_out_time(self):
        for att in self:
            if att.check_out:
                check_out = fields.Datetime.to_string(fields.Datetime.from_string(att.check_out) + timedelta(hours=5, minutes=30))
                att.out_time = convert_to_float(check_out)
                att.late_out = att.out_time - att.off_duty

    @api.multi
    @api.depends('check_in')
    def _get_in_time(self):
        if self:
            for att in self:
                if att.check_in:
                    check_in = fields.Datetime.to_string(fields.Datetime.from_string(att.check_in) + timedelta(hours=5, minutes=30))
                    att.in_time = convert_to_float(check_in)
                    att.late_in = att.in_time - att.on_duty

    @api.multi
    @api.depends('check_in', 'check_out', 'employee_id', 'employee_id.working_history_ids')
    def _get_resource_and_hrs(self):
        if self:
            for attendance in self:
                if attendance.employee_id.working_history_ids:
                    for schedule in attendance.employee_id.working_history_ids:
                        if schedule.from_date and schedule.to_date:
                            if attendance.check_in >= schedule.from_date and attendance.check_in <= schedule.to_date:
                                attendance.resource_calendar_id = schedule.resource_calendar_id.id
                                working_time = self.get_working_time(schedule.resource_calendar_id.id, attendance)
                                if working_time:
                                    attendance.on_duty = working_time[0]
                                    attendance.off_duty = working_time[1]
                                break
                        elif attendance.check_in >= schedule.from_date:
                            attendance.resource_calendar_id = schedule.resource_calendar_id.id
                            working_time = self.get_working_time(schedule.resource_calendar_id.id, attendance)
                            if working_time:
                                attendance.on_duty = working_time[0]
                                attendance.off_duty = working_time[1]
                            break

    def get_working_time(self, working_hrs_id, attendance):
        if attendance.check_in and attendance.check_out:
            check_in = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in)))
            check_out = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out)))
            check_in = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
            domain = [('dayofweek', '=', check_in.weekday()), ('calendar_id', '=', working_hrs_id)]
            weekdays = self.env['resource.calendar.attendance'].search(domain)

            if len(weekdays) > 1:
                for weekday in weekdays:
                    hour_from = str(float_to_time(weekday.hour_from))
                    hour_to = str(float_to_time(weekday.hour_to))

                    from_time = check_in.replace(hour=int(hour_from[0:2]), minute=int(hour_from[3:5]), second=00)
                    to_time = check_out.replace(hour=int(hour_to[0:2]), minute=int(hour_to[3:5]), second=00)
                    # case 1: Late come and early going
                    if (check_in >= from_time and check_out <= to_time):
                        return (weekday.hour_from, weekday.hour_to)
                    # case 2: Early come and late going
                    elif (check_in <= from_time and check_out >= to_time):
                        return (weekday.hour_from, weekday.hour_to)
                    # case 3: Early come and early going
                    elif (check_in <= from_time and check_out <= to_time and check_out > from_time):
                        return (weekday.hour_from, weekday.hour_to)
                    # case 4: Late come and late going
                    elif (check_in >= from_time and check_out >= to_time and check_in < to_time):
                        return (weekday.hour_from, weekday.hour_to)

            else:
                return (weekdays.hour_from, weekdays.hour_to)

    # late time calculation according to the configuration
    @api.multi
    @api.depends('check_in', 'check_out', 'employee_id')
    def _get_late_time(self):
        for lines in self:
            if lines.check_in and lines.check_out:
                try:
                    company_late_policy = self.env['hr.late.configuration']
                    procedure = company_late_policy.search([])
                    case_one = procedure.case_one
                    sum = 0.0
                    late_time = 0.0
                    diff = 0.0
                    check_in_time = fields.Datetime.to_string(
                        fields.Datetime.from_string(lines.check_in) + timedelta(hours=5, minutes=30))
                    check_out_time = fields.Datetime.to_string(
                        fields.Datetime.from_string(lines.check_out) + timedelta(hours=5, minutes=30))
                    check_in = convert_to_float(check_in_time)
                    check_out = convert_to_float(check_out_time)
                    day = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').weekday()
                    check_in_time_only = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').time()
                    check_out_time_only = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').time()
                    day = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').weekday()
                    check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
                    check_out_date = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').date()
                    month = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').strftime("%m")
                    year = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').strftime("%Y")
                    day_name = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').strftime("%A")

                    # if late covered in the evening
                    if procedure.is_late == 'yes':
                        if case_one == 'late_covered':
                            if lines.check_in and lines.check_out:
                                for ids in self.env['schedule.history'].search([
                                    ('from_date', '<=', lines.check_in), ('to_date', '>=', lines.check_in),
                                    ('emp_id', '=', lines.employee_id.id)]):
                                    id = self.env['resource.calendar.attendance'].search([
                                        ('calendar_id', '=', ids.resource_calendar_id.id), ('dayofweek', '=', day)])

                                    if ids.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    elif ids.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    else:
                                        diff = id.hour_to - id.hour_from

                                    lines._cr.execute(
                                        "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (lines.date, lines.employee_id.id))
                                    morning = lines._cr.fetchall()
                                    # works morning

                                    lines._cr.execute(
                                        "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (lines.date, lines.employee_id.id))
                                    evening = lines._cr.fetchall()

                                    if morning and evening:
                                        from_date = evening[0][6]
                                        to_date = evening[0][7]
                                        if(ids.from_date <= from_date and ids.to_date >= from_date) or (ids.from_date <= to_date and ids.to_date >= to_date):
                                            date_from = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                hours=5, minutes=30)
                                            date_to = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                                  minutes=30)
                                            date_from = datetime.strptime(str(date_from), '%Y-%m-%d %H:%M:%S').time()
                                            date_to = datetime.strptime(str(date_to), '%Y-%m-%d %H:%M:%S').time()
                                            margin = diff / 2
                                            margin_time = id.hour_from + margin
                                            margin_time = float_to_time(margin_time)
                                            id_hour_to = float_to_time(id.hour_to)
                                            if margin_time > date_from:
                                                if check_in_time_only > date_to:
                                                    check_in_difference = datetime.strptime(str(check_in_time_only),
                                                                                            '%H:%M:%S') - datetime.strptime(
                                                        str(date_to), '%H:%M:%S')
                                                    check_in_difference_float = datetime.strptime(str(check_in_difference),
                                                                                                  '%H:%M:%S')
                                                    check_in_difference_float = convert_to_float(
                                                        str(check_in_difference_float))
                                                    check_out_difference = check_out - id.hour_to
                                                    if check_in_difference_float > check_out_difference:

                                                        if not lines.is_deduct:
                                                            late_time = late_time + check_in_difference_float
                                                            lines.deduct_from_leaves(lines, late_time, diff, id)
                                                            if not lines.is_deduct:
                                                                lines.late_time = late_time
                                                                lines.write({
                                                                    'late_time_store_value': late_time,
                                                                    'latetime': late_time
                                                                })
                                                            else:
                                                                lines.late_time = 0.0
                                                                lines.write({'late_time_store_value': 0.0})
                                                        else:
                                                            lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0
                                                        lines.write({'late_time_store_value': 0})


                                            elif margin_time <= date_from:
                                                check_in_time_only = datetime.strptime(str(check_in_time_only), '%H:%M:%S')
                                                check_in_time_only = convert_to_float(str(check_in_time_only))
                                                if check_in_time_only > id.hour_from:
                                                    check_in_time_only = check_in - id.hour_from
                                                    check_out_time_only = datetime.strptime(str(check_out_time_only),
                                                                                            '%H:%M:%S')
                                                    check_out_time_only = convert_to_float(str(check_out_time_only))
                                                    date_from = datetime.strptime(str(date_from), '%H:%M:%S')
                                                    date_from = convert_to_float(str(date_from))
                                                    check_out_differences = check_out_time_only - date_from
                                                    if check_in_time_only > check_out_differences:

                                                        if not lines.is_deduct:
                                                            late_time = late_time + check_in_time_only
                                                            lines.deduct_from_leaves(lines, late_time, diff, id)
                                                            if not lines.is_deduct:
                                                                lines.late_time = late_time
                                                                lines.write({
                                                                    'late_time_store_value': late_time,
                                                                    'late_time': late_time
                                                                })
                                                            else:
                                                                lines.late_time = 0.0
                                                                lines.write({'late_time_store_value': 0.0})
                                                        else:
                                                            lines.late_time = 0.0
                                                            lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0
                                                        lines.write({'late_time_store_value': 0})

                                        else:
                                            sum = sum + diff
                                            out_time = convert_to_float(check_out_time)
                                            in_time = convert_to_float(check_in_time)
                                            late_time = late_time + (out_time - in_time)
                                            # if working hours is greater than worked hours
                                            if diff > lines.worked_hours:

                                                if not lines.is_deduct:
                                                    late_time = check_in - id.hour_from
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                    elif morning:
                                        from_date = morning[0][6]
                                        if (ids.from_date <= from_date and ids.to_date >= from_date):
                                            date_from = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                hours=5,
                                                minutes=30)
                                            date_from = convert_to_float(str(date_from))
                                            check_in_time_only = datetime.strptime(str(check_in_time_only), '%H:%M:%S')
                                            check_in_time_only = convert_to_float(str(check_in_time_only))
                                            if check_in_time_only > id.hour_from:
                                                check_in_difference_float = check_in_time_only - id.hour_from
                                                check_out_difference_float = check_out - date_from
                                                if check_in_difference_float > check_out_difference_float:

                                                    if not lines.is_deduct:
                                                        late_time = late_time + check_in_difference_float
                                                        lines.deduct_from_leaves(lines, late_time, diff, id)
                                                        if not lines.is_deduct:
                                                            lines.late_time = late_time
                                                            lines.write({
                                                                'late_time_store_value': late_time,
                                                                'late_time': late_time
                                                            })
                                                        else:
                                                            lines.late_time = 0.0
                                                            lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0
                                                    lines.write({'late_time_store_value': 0})

                                        else:
                                            sum = sum + diff
                                            out_time = convert_to_float(check_out_time)
                                            in_time = convert_to_float(check_in_time)
                                            late_time = late_time + (out_time - in_time)
                                            # if working hours is greater than worked hours
                                            if diff > lines.worked_hours:

                                                if not lines.is_deduct:
                                                    late_time = check_in - id.hour_from
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                    elif evening:
                                        to_date = evening[0][7]
                                        if (ids.from_date <= to_date and ids.to_date >= to_date):
                                            to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                                  minutes=30)
                                            to_date = convert_to_float(str(to_date))
                                            check_in_time_only = datetime.strptime(str(check_in_time_only), '%H:%M:%S')
                                            check_in_time_only = convert_to_float(str(check_in_time_only))
                                            if check_in_time_only > to_date:
                                                check_in_difference = check_in_time_only - to_date
                                                check_out_difference = check_out - id.hour_to
                                                if check_in_difference > check_out_difference:

                                                    if not lines.is_deduct:
                                                        late_time = late_time + check_in_difference
                                                        lines.deduct_from_leaves(lines, late_time, diff, id)
                                                        if not lines.is_deduct:
                                                            lines.late_time = late_time
                                                            lines.write({
                                                                'late_time_store_value': late_time,
                                                                'late_time': late_time
                                                            })
                                                        else:
                                                            lines.late_time = 0.0
                                                            lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0
                                                    lines.write({'late_time_store_value': 0})

                                        else:
                                            sum = sum + diff
                                            out_time = convert_to_float(check_out_time)
                                            in_time = convert_to_float(check_in_time)
                                            late_time = late_time + (out_time - in_time)
                                            # if working hours is greater than worked hours
                                            if diff > lines.worked_hours:

                                                if not lines.is_deduct:
                                                    late_time = check_in - id.hour_from
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                    else:
                                        sum = sum + diff
                                        out_time = convert_to_float(check_out_time)
                                        in_time = convert_to_float(check_in_time)
                                        late_time = late_time + (out_time - in_time)
                                        # if working hours is greater than worked hours
                                        if diff > lines.worked_hours:

                                                if not lines.is_deduct:
                                                    late_time = check_in - id.hour_from
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                        else:
                                            lines.late_time = 0.0
                                            lines.write({'late_time_store_value': 0.0})

                        # if check_in in time range allocated by company
                        elif case_one == 'time_range':
                            time_period = procedure.time
                            if lines.check_in and lines.check_out:
                                for ids in self.env['schedule.history'].search(
                                        [('from_date', '<=', lines.check_in), ('to_date', '>=', lines.check_in),
                                         ('emp_id', '=', lines.employee_id.id)]):
                                    id = self.env['resource.calendar.attendance'].search(
                                        [('calendar_id', '=', ids.resource_calendar_id.id), ('dayofweek', '=', day)])

                                    if ids.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    elif ids.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                        diff = (id.hour_to + 24) - id.hour_from
                                    else:
                                        diff = id.hour_to - id.hour_from

                                    lines._cr.execute(
                                        "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (lines.date, lines.employee_id.id))
                                    morning = lines._cr.fetchall()
                                    # works morning

                                    lines._cr.execute(
                                        "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                        (lines.date, lines.employee_id.id))
                                    evening = lines._cr.fetchall()

                                    if evening and morning:
                                        from_date = evening[0][6]
                                        to_date = evening[0][7]
                                        if(ids.from_date <= from_date and ids.to_date >= from_date) or (ids.from_date <= to_date and ids.to_date >= to_date):
                                            margin = diff / 2
                                            margin_time = id.hour_from + margin
                                            from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                                hours=5,
                                                minutes=30)
                                            from_date = convert_to_float(str(from_date))
                                            to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                                  minutes=30)
                                            to_date = convert_to_float(str(to_date))
                                            if from_date < margin_time:
                                                time_with_grace = to_date + time_period
                                                if check_in > time_with_grace:

                                                    if not lines.is_deduct:
                                                        late_time = check_in - time_with_grace
                                                        lines.deduct_from_leaves(lines, late_time, diff, id)
                                                        if not lines.is_deduct:
                                                            lines.late_time = late_time
                                                            lines.write({
                                                                'late_time_store_value': late_time,
                                                                'late_time': late_time
                                                            })
                                                        else:
                                                            lines.late_time = 0.0
                                                            lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0
                                                    lines.write({'late_time_store_value': 0})
                                            else:
                                                time_with_grace = id.hour_from + time_period
                                                if check_in > time_with_grace:

                                                    if not lines.is_deduct:
                                                        late_time = check_in - time_with_grace
                                                        lines.deduct_from_leaves(lines, late_time, diff, id)
                                                        if not lines.is_deduct:
                                                            lines.late_time = late_time
                                                            lines.write({
                                                                'late_time_store_value': late_time,
                                                                'late_time': late_time
                                                            })
                                                        else:
                                                            lines.late_time = 0.0
                                                            lines.write({'late_time_store_value': 0.0})
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0
                                                    lines.write({'late_time_store_value': 0})
                                        else:
                                            sum = sum + diff
                                            out_time = convert_to_float(lines.check_out)
                                            in_time = convert_to_float(lines.check_in)
                                            late_time = late_time + (out_time - in_time)

                                            # if work time is equal or less than working_hours
                                            check_in_with_time_period = id.hour_from + time_period
                                            if check_in > check_in_with_time_period:

                                                if not lines.is_deduct:
                                                    late_time = check_in - check_in_with_time_period
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})

                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                    elif evening:
                                        to_date = evening[0][7]
                                        to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5,
                                                                                                              minutes=30)
                                        if(ids.from_date <= to_date and ids.to_date >= to_date):
                                            to_date = convert_to_float(str(to_date))
                                            time_with_grace = to_date + time_period
                                            if check_in > time_with_grace:
                                                if not lines.is_deduct:
                                                    late_time = check_in - time_with_grace
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0
                                                lines.write({'late_time_store_value': 0})
                                        else:
                                            sum = sum + diff
                                            out_time = convert_to_float(lines.check_out)
                                            in_time = convert_to_float(lines.check_in)
                                            late_time = late_time + (out_time - in_time)

                                            # if work time is equal or less than working_hours
                                            check_in_with_time_period = id.hour_from + time_period
                                            if check_in > check_in_with_time_period:

                                                if not lines.is_deduct:
                                                    late_time = check_in - check_in_with_time_period
                                                    lines.deduct_from_leaves(lines, late_time, diff, id)
                                                    if not lines.is_deduct:
                                                        lines.late_time = late_time
                                                        lines.write({
                                                            'late_time_store_value': late_time,
                                                            'late_time': late_time
                                                        })
                                                    else:
                                                        lines.late_time = 0.0
                                                        lines.write({'late_time_store_value': 0.0})
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})

                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                    elif morning:
                                        time_with_grace = id.hour_from + time_period
                                        if check_in > time_with_grace:

                                            if not lines.is_deduct:
                                                late_time = check_in - time_with_grace
                                                lines.deduct_from_leaves(lines, late_time, diff, id)
                                                if not lines.is_deduct:
                                                    lines.late_time = late_time
                                                    lines.write({
                                                        'late_time_store_value': late_time,
                                                        'late_time': late_time
                                                    })
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})
                                        else:
                                            lines.late_time = 0
                                            lines.write({'late_time_store_value': 0})

                                    else:
                                        sum = sum + diff
                                        out_time = convert_to_float(lines.check_out)
                                        in_time = convert_to_float(lines.check_in)
                                        late_time = late_time + (out_time - in_time)

                                        # if work time is equal or less than working_hours
                                        check_in_with_time_period = id.hour_from + time_period
                                        if check_in > check_in_with_time_period:

                                            if not lines.is_deduct:
                                                late_time = check_in - check_in_with_time_period
                                                lines.deduct_from_leaves(lines, late_time, diff, id)
                                                if not lines.is_deduct:
                                                    lines.late_time = late_time
                                                    lines.write({
                                                        'late_time_store_value': late_time,
                                                        'late_time': late_time
                                                    })
                                                else:
                                                    lines.late_time = 0.0
                                                    lines.write({'late_time_store_value': 0.0})
                                            else:
                                                lines.late_time = 0.0
                                                lines.write({'late_time_store_value': 0.0})

                                        else:
                                            lines.late_time = 0.0
                                            lines.write({'late_time_store_value': 0.0})

                        # if check_in in the late day for month
                        elif case_one == 'late_days_for_month':
                            if lines.check_in and lines.check_out:
                                for working_schedule_history in self.env['schedule.history'].search(
                                    [('from_date', '<=', lines.check_in),
                                     ('to_date', '>=', lines.check_in),
                                     ('emp_id', '=', lines.employee_id.id)]):
                                    late_policy = self.env['hr.late.configuration'].search([], limit=1)

                                    # from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)

                                    for days in working_schedule_history.resource_calendar_id.attendance_ids:

                                        if working_schedule_history.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                            diff = (days.hour_to + 24) - days.hour_from
                                        elif working_schedule_history.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                            diff = (days.hour_to + 24) - days.hour_from
                                        else:
                                            diff = days.hour_to - days.hour_from

                                        lines._cr.execute(
                                            "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                            (lines.date, lines.employee_id.id))
                                        morning = lines._cr.fetchall()
                                        # works morning

                                        lines._cr.execute(
                                            "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                            (lines.date, lines.employee_id.id))
                                        evening = lines._cr.fetchall()

                                        # check equality of the working schedule day and checking day
                                        if str(days.dayofweek) == str(day):
                                            # if checking time is grater than given checking time

                                            # check employee have any leave on given day
                                            if morning and evening:
                                                from_date = evening[0][6]
                                                to_date = evening[0][7]
                                                margin = diff / 2
                                                margin_time = days.hour_from + margin
                                                from_date = datetime.strptime(from_date,
                                                                              '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                from_date = convert_to_float(str(from_date))
                                                to_date = datetime.strptime(to_date,
                                                                            '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                to_date = convert_to_float(str(to_date))
                                                if days.hour_from <= from_date < margin_time:
                                                    if to_date <= check_in <= to_date + late_policy.grace_time:
                                                        if len(
                                                                lines.employee_id.monthly_late_attendance_lines) > 0:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    # check if employee has number of days per months lines
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                # check the equality of checking month and late day month
                                                                if num_days.number == int(month):
                                                                    # if new year reset number of days per months to default
                                                                    if not lines.is_calculated:
                                                                        if num_days.year != int(year):
                                                                            lines.late_time = check_in - to_date
                                                                            num_days.write({
                                                                                'year': year,
                                                                                'late_days_per_month': late_policy.late_days_per_month
                                                                            })
                                                                    # employee has no late attendance dates per month
                                                                    if num_days.late_days_per_month == 0:
                                                                        if not lines.is_calculated:
                                                                            if not lines.is_deduct:
                                                                                total_late_time = check_in - to_date
                                                                                lines.deduct_from_leaves(lines,
                                                                                                         total_late_time,
                                                                                                         diff, days)
                                                                                if not lines.is_deduct:
                                                                                    lines.late_time = check_in - to_date
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - to_date,
                                                                                        'late_time': check_in - to_date
                                                                                    })
                                                                                else:
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': 0,
                                                                                        'late_time': 0
                                                                                    })
                                                                                    lines.late_time = 0
                                                                            else:
                                                                                lines.late_time = check_in - to_date
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - to_date,
                                                                                    'late_time': check_in - to_date
                                                                                })
                                                                    # employee has late attendance days
                                                                    else:
                                                                        if not lines.is_calculated and num_days.number == int(month):
                                                                            if num_days.late_days_per_month != 0:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                num_days.write({
                                                                                    'late_days_per_month': num_days.late_days_per_month - 1
                                                                                })
                                                                            else:
                                                                                if not lines.is_deduct:
                                                                                    total_late_time = check_in - to_date
                                                                                    lines.deduct_from_leaves(lines,
                                                                                                             total_late_time,
                                                                                                             diff, days)
                                                                                    if not lines.is_deduct:
                                                                                        lines.late_time = check_in - to_date
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': check_in - to_date,
                                                                                            'late_time': check_in - to_date
                                                                                        })
                                                                                    else:
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': 0,
                                                                                            'late_time': 0
                                                                                        })
                                                                                        lines.late_time = 0
                                                                                else:
                                                                                    lines.late_time = check_in - to_date
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - to_date,
                                                                                        'late_time': check_in - to_date
                                                                                    })

                                                    elif to_date > check_in:
                                                        lines.late_time = 0.0
                                                        lines.late_time_store_value = 0.0

                                                    else:
                                                        if lines.employee_id.monthly_late_attendance_lines:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                if not lines.is_calculated:
                                                                    if num_days.year != int(year):
                                                                        num_days.write({
                                                                            'year': year,
                                                                        })

                                                                if not lines.is_calculated and num_days.number == int(month):
                                                                    if num_days.late_days_per_month != 0:
                                                                        lines.write({
                                                                            'is_calculated': True,
                                                                            'late_time_store_value': check_in - to_date,
                                                                            'late_time': check_in - to_date
                                                                        })
                                                                        lines.late_time = check_in - to_date
                                                                        num_days.write({
                                                                            'late_days_per_month': num_days.late_days_per_month - 1
                                                                        })
                                                                    else:
                                                                        if not lines.is_deduct:
                                                                            total_late_time = check_in - to_date
                                                                            lines.deduct_from_leaves(lines,
                                                                                                     total_late_time,
                                                                                                     diff, days)
                                                                            if not lines.is_deduct:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - to_date,
                                                                                    'late_time': check_in - to_date
                                                                                })
                                                                                lines.late_time = check_in - to_date
                                                                            else:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                lines.late_time = 0
                                                                        else:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - to_date,
                                                                                'late_time': check_in - to_date
                                                                            })
                                                                            lines.late_time = check_in - to_date

                                                else:
                                                    if days.hour_from <= check_in <= days.hour_from + late_policy.grace_time:
                                                        if len(lines.employee_id.monthly_late_attendance_lines) > 0:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    # check if employee has number of days per months lines
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                # check the equality of checking month and late day month
                                                                if num_days.number == int(month):
                                                                    # if new year reset number of days per months to default
                                                                    if not lines.is_calculated:
                                                                        if num_days.year != int(year):
                                                                            lines.late_time = check_in - days.hour_from
                                                                            num_days.write({
                                                                                'year': year,
                                                                                'late_days_per_month': late_policy.late_days_per_month
                                                                            })
                                                                    # employee has no late attendance dates per month
                                                                    if num_days.late_days_per_month == 0:
                                                                        if not lines.is_calculated:
                                                                            if not lines.is_deduct:
                                                                                total_late_time = check_in - days.hour_from
                                                                                lines.deduct_from_leaves(lines,
                                                                                                         total_late_time,
                                                                                                         diff, days)
                                                                                if not lines.is_deduct:
                                                                                    lines.late_time = check_in - days.hour_from
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - days.hour_from,
                                                                                        'late_time': check_in - days.hour_from
                                                                                    })
                                                                                else:
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': 0,
                                                                                        'late_time': 0
                                                                                    })
                                                                                    lines.late_time = 0
                                                                            else:
                                                                                lines.late_time = check_in - days.hour_from
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    'late_time': check_in - days.hour_from
                                                                                })
                                                                    # employee has late attendance days
                                                                    else:
                                                                        if not lines.is_calculated and num_days.number == int(month):
                                                                            if num_days.late_days_per_month != 0:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                num_days.write({
                                                                                    'late_days_per_month': num_days.late_days_per_month - 1
                                                                                })
                                                                            else:
                                                                                if not lines.is_deduct:
                                                                                    total_late_time = check_in - days.hour_from
                                                                                    lines.deduct_from_leaves(lines,
                                                                                                             total_late_time,
                                                                                                             diff, days)
                                                                                    if not lines.is_deduct:
                                                                                        lines.late_time = check_in - days.hour_from
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': check_in - days.hour_from,
                                                                                            'late_time': check_in - days.hour_from
                                                                                        })
                                                                                    else:
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': 0,
                                                                                            'late_time': 0
                                                                                        })
                                                                                        lines.late_time = 0
                                                                                else:
                                                                                    lines.late_time = check_in - days.hour_from
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - days.hour_from,
                                                                                        'late_time': check_in - days.hour_from
                                                                                    })

                                                    elif days.hour_from > check_in:
                                                        lines.late_time = 0.0
                                                        lines.late_time_store_value = 0.0

                                                    else:
                                                        if lines.employee_id.monthly_late_attendance_lines:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                if not lines.is_calculated:
                                                                    if num_days.year != int(year):
                                                                        num_days.write({
                                                                            'year': year,
                                                                        })

                                                                if not lines.is_calculated and num_days.number == int(month):
                                                                    if num_days.late_days_per_month != 0:
                                                                        lines.write({
                                                                            'is_calculated': True,
                                                                            'late_time_store_value': check_in - days.hour_from,
                                                                            'late_time': check_in - days.hour_from
                                                                        })
                                                                        lines.late_time = check_in - days.hour_from
                                                                        num_days.write({
                                                                            'late_days_per_month': num_days.late_days_per_month - 1
                                                                        })
                                                                    else:
                                                                        if not lines.is_deduct:
                                                                            total_late_time = check_in - days.hour_from
                                                                            lines.deduct_from_leaves(lines,
                                                                                                     total_late_time,
                                                                                                     diff, days)
                                                                            if not lines.is_deduct:
                                                                                lines.late_time = check_in - days.hour_from
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    'late_time': check_in - days.hour_from
                                                                                })
                                                                            else:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                lines.late_time = 0
                                                                        else:
                                                                            lines.late_time = check_in - days.hour_from
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - days.hour_from,
                                                                                'late_time': check_in - days.hour_from
                                                                            })



                                            elif evening:
                                                to_date = evening[0][7]
                                                to_date = datetime.strptime(to_date,
                                                                            '%Y-%m-%d %H:%M:%S') + timedelta(
                                                    hours=5,
                                                    minutes=30)
                                                to_date = convert_to_float(str(to_date))

                                                if days.hour_from <= to_date >= days.hour_to:
                                                    if to_date <= check_in <= to_date + late_policy.grace_time:
                                                        if len(lines.employee_id.monthly_late_attendance_lines) > 0:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    # check if employee has number of days per months lines
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                # check the equality of checking month and late day month
                                                                if num_days.number == int(month):
                                                                    # if new year reset number of days per months to default
                                                                    if not lines.is_calculated:
                                                                        if num_days.year != int(year):
                                                                            lines.late_time = check_in - to_date
                                                                            num_days.write({
                                                                                'year': year,
                                                                                'late_days_per_month': late_policy.late_days_per_month
                                                                            })
                                                                    # employee has no late attendance dates per month
                                                                    if num_days.late_days_per_month == 0:
                                                                        if not lines.is_calculated:
                                                                            if not lines.is_deduct:
                                                                                total_late_time = check_in - to_date
                                                                                lines.deduct_from_leaves(lines,
                                                                                                         total_late_time,
                                                                                                         diff, days)
                                                                                if not lines.is_deduct:
                                                                                    lines.late_time = check_in - to_date
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - to_date,
                                                                                        'late_time': check_in - to_date
                                                                                    })
                                                                                else:
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': 0,
                                                                                        'late_time': 0
                                                                                    })
                                                                                    lines.late_time = 0
                                                                            else:
                                                                                lines.late_time = check_in - to_date
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - to_date,
                                                                                    'late_time': check_in - to_date
                                                                                })
                                                                    # employee has late attendance days
                                                                    else:
                                                                        if not lines.is_calculated and num_days.number == int(month):
                                                                            if num_days.late_days_per_month != 0:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                num_days.write({
                                                                                    'late_days_per_month': num_days.late_days_per_month - 1
                                                                                })
                                                                            else:
                                                                                if not lines.is_deduct:
                                                                                    total_late_time = check_in - to_date
                                                                                    lines.deduct_from_leaves(lines,
                                                                                                             total_late_time,
                                                                                                             diff, days)
                                                                                    if not lines.is_deduct:
                                                                                        lines.late_time = check_in - to_date
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': check_in - to_date,
                                                                                            'late_time': check_in - to_date
                                                                                        })
                                                                                    else:
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': 0,
                                                                                            'late_time': 0
                                                                                        })
                                                                                        lines.late_time = 0
                                                                                else:
                                                                                    lines.late_time = check_in - to_date
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - to_date,
                                                                                        'late_time': check_in - to_date
                                                                                    })

                                                    elif to_date > check_in:
                                                        lines.late_time = 0.0
                                                        lines.late_time_store_value = 0.0

                                                    else:
                                                        if lines.employee_id.monthly_late_attendance_lines:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                if not lines.is_calculated:
                                                                    if num_days.year != int(year):
                                                                        num_days.write({
                                                                            'year': year,
                                                                        })

                                                                if not lines.is_calculated and num_days.number == int(month):
                                                                    if num_days.late_days_per_month != 0:
                                                                        lines.write({
                                                                            'is_calculated': True,
                                                                            'late_time_store_value': check_in - to_date,
                                                                            'late_time': check_in - to_date
                                                                        })
                                                                        lines.late_time = check_in - to_date
                                                                        num_days.write({
                                                                            'late_days_per_month': num_days.late_days_per_month - 1
                                                                        })
                                                                    else:
                                                                        if not lines.is_deduct:
                                                                            total_late_time = check_in - to_date
                                                                            lines.deduct_from_leaves(lines,
                                                                                                     total_late_time,
                                                                                                     diff, days)
                                                                            if not lines.is_deduct:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - to_date,
                                                                                    'late_time': check_in - to_date
                                                                                })
                                                                                lines.late_time = check_in - to_date
                                                                            else:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                lines.late_time = 0
                                                                        else:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - to_date,
                                                                                'late_time': check_in - to_date
                                                                            })
                                                                            lines.late_time = check_in - to_date

                                                else:
                                                    if days.hour_from <= check_in <= days.hour_from + late_policy.grace_time:
                                                        if len(lines.employee_id.monthly_late_attendance_lines) > 0:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    # check if employee has number of days per months lines
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                # check the equality of checking month and late day month
                                                                if num_days.number == int(month):
                                                                    # if new year reset number of days per months to default
                                                                    if not lines.is_calculated:
                                                                        if num_days.year != int(year):
                                                                            lines.late_time = check_in - days.hour_from
                                                                            num_days.write({
                                                                                'year': year,
                                                                                'late_days_per_month': late_policy.late_days_per_month
                                                                            })
                                                                    # employee has no late attendance dates per month
                                                                    if num_days.late_days_per_month == 0:
                                                                        if not lines.is_calculated:
                                                                            if not lines.is_deduct:
                                                                                total_late_time = check_in - days.hour_from
                                                                                lines.deduct_from_leaves(lines,
                                                                                                         total_late_time,
                                                                                                         diff, days)
                                                                                if not lines.is_deduct:
                                                                                    lines.late_time = check_in - days.hour_from
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - days.hour_from,
                                                                                        "late_time": check_in - days.hour_from
                                                                                    })
                                                                                else:
                                                                                    lines.late_time = 0
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': 0,
                                                                                        "late_time": 0
                                                                                    })
                                                                            else:
                                                                                lines.late_time = check_in - days.hour_from
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    "late_time": check_in - days.hour_from
                                                                                })
                                                                    # employee has late attendance days
                                                                    else:
                                                                        if not lines.is_calculated and num_days.number == int(month):
                                                                            if num_days.late_days_per_month != 0:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                num_days.write({
                                                                                    'late_days_per_month': num_days.late_days_per_month - 1
                                                                                })
                                                                            else:
                                                                                if not lines.is_deduct:
                                                                                    total_late_time = check_in - days.hour_from
                                                                                    lines.deduct_from_leaves(lines, total_late_time,
                                                                                                             diff, days)
                                                                                    if not lines.is_deduct:
                                                                                        lines.late_time = check_in - days.hour_from
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': check_in - days.hour_from,
                                                                                            "late_time": check_in - days.hour_from
                                                                                        })
                                                                                    else:
                                                                                        lines.late_time = 0
                                                                                        lines.write({
                                                                                            'is_calculated': True,
                                                                                            'late_time_store_value': 0,
                                                                                            "late_time": 0
                                                                                        })
                                                                                else:
                                                                                    lines.late_time = check_in - days.hour_from
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - days.hour_from,
                                                                                        "late_time": check_in - days.hour_from
                                                                                    })

                                                    elif days.hour_from > check_in:
                                                        lines.late_time = 0.0
                                                        lines.late_time_store_value = 0.0

                                                    else:
                                                        if lines.employee_id.monthly_late_attendance_lines:
                                                            for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                                if not lines.is_calculated:
                                                                    if len(
                                                                            lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                        if not num_days.year:
                                                                            num_days.write({'year': year})

                                                                if not lines.is_calculated:
                                                                    if num_days.year != int(year):
                                                                        num_days.write({
                                                                            'year': year,
                                                                        })

                                                                if not lines.is_calculated and num_days.number == int(
                                                                        month):
                                                                    if num_days.late_days_per_month != 0:
                                                                        lines.write({
                                                                            'is_calculated': True,
                                                                            'late_time_store_value': check_in - days.hour_from,
                                                                            'late_time': check_in - days.hour_from
                                                                        })
                                                                        lines.late_time = check_in - days.hour_from
                                                                        num_days.write({
                                                                            'late_days_per_month': num_days.late_days_per_month - 1
                                                                        })
                                                                    else:
                                                                        if not lines.is_deduct:
                                                                            total_late_time = check_in - days.hour_from
                                                                            lines.deduct_from_leaves(lines,
                                                                                                     total_late_time,
                                                                                                     diff, days)
                                                                            if not lines.is_deduct:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    'late_time': check_in - days.hour_from
                                                                                })
                                                                                lines.late_time = check_in - days.hour_from
                                                                            else:
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                                lines.late_time = 0
                                                                        else:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - days.hour_from,
                                                                                'late_time': check_in - days.hour_from
                                                                            })
                                                                            lines.late_time = check_in - days.hour_from

                                            else:
                                                if days.hour_from <= check_in <= days.hour_from + late_policy.grace_time:
                                                    if len(lines.employee_id.monthly_late_attendance_lines) > 0:
                                                        for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                            if not lines.is_calculated:
                                                                # check if employee has number of days per months lines
                                                                if len(
                                                                        lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                    if not num_days.year:
                                                                        num_days.write({'year': year})

                                                            # check the equality of checking month and late day month
                                                            if num_days.number == int(month):
                                                                # if new year reset number of days per months to default
                                                                if not lines.is_calculated:
                                                                    if num_days.year != int(year):
                                                                        lines.late_time = check_in - days.hour_from
                                                                        num_days.write({
                                                                            'year': year,
                                                                            'late_days_per_month': late_policy.late_days_per_month
                                                                        })
                                                                # employee has no late attendance dates per month
                                                                if num_days.late_days_per_month == 0:
                                                                    if not lines.is_calculated:
                                                                        if not lines.is_deduct:
                                                                            total_late_time = check_in - days.hour_from
                                                                            lines.deduct_from_leaves(lines, total_late_time, diff, days)
                                                                            if not lines.is_deduct:
                                                                                lines.late_time = check_in - days.hour_from
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    'late_time': check_in - days.hour_from
                                                                                })
                                                                            else:
                                                                                lines.late_time = 0
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': 0,
                                                                                    'late_time': 0
                                                                                })
                                                                        else:
                                                                            lines.late_time = check_in - days.hour_from
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - days.hour_from,
                                                                                'late_time': check_in - days.hour_from
                                                                            })
                                                                # employee has late attendance days
                                                                else:
                                                                    if not lines.is_calculated and num_days.number == int(month):
                                                                        if num_days.late_days_per_month != 0:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': 0,
                                                                                'late_time': 0
                                                                            })
                                                                            num_days.write({
                                                                                'late_days_per_month': num_days.late_days_per_month - 1
                                                                            })
                                                                        else:
                                                                            if not lines.is_deduct:
                                                                                total_late_time = check_in - days.hour_from
                                                                                lines.deduct_from_leaves(lines,
                                                                                                         total_late_time,
                                                                                                         diff, days)
                                                                                if not lines.is_deduct:
                                                                                    lines.late_time = check_in - days.hour_from
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': check_in - days.hour_from,
                                                                                        'late_time': check_in - days.hour_from
                                                                                    })
                                                                                else:
                                                                                    lines.write({
                                                                                        'is_calculated': True,
                                                                                        'late_time_store_value': 0,
                                                                                        'late_time': 0
                                                                                    })
                                                                                    lines.late_time = 0
                                                                            else:
                                                                                lines.late_time = check_in - days.hour_from
                                                                                lines.write({
                                                                                    'is_calculated': True,
                                                                                    'late_time_store_value': check_in - days.hour_from,
                                                                                    'late_time': check_in - days.hour_from
                                                                                })

                                                elif days.hour_from > check_in:
                                                    lines.late_time = 0.0
                                                    lines.late_time_store_value = 0.0

                                                else:
                                                    if lines.employee_id.monthly_late_attendance_lines:
                                                        for num_days in lines.employee_id.monthly_late_attendance_lines:
                                                            if not lines.is_calculated:
                                                                if len(
                                                                        lines.employee_id.monthly_late_attendance_lines) > 0:
                                                                    if not num_days.year:
                                                                        num_days.write({'year': year})

                                                            if not lines.is_calculated:
                                                                if num_days.year != int(year):
                                                                    num_days.write({
                                                                        'year': year,
                                                                    })

                                                            if not lines.is_calculated and num_days.number == int(month):
                                                                if num_days.late_days_per_month != 0:
                                                                    lines.write({
                                                                        'is_calculated': True,
                                                                        'late_time_store_value': check_in - days.hour_from ,
                                                                        'late_time': check_in - days.hour_from
                                                                    })
                                                                    lines.late_time = check_in - days.hour_from
                                                                    num_days.write({
                                                                        'late_days_per_month': num_days.late_days_per_month - 1
                                                                    })
                                                                else:
                                                                    if not lines.is_deduct:
                                                                        total_late_time = check_in - days.hour_from
                                                                        lines.deduct_from_leaves(lines, total_late_time, diff, days)
                                                                        if not lines.is_deduct:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': check_in - days.hour_from,
                                                                                'late_time': check_in - days.hour_from
                                                                            })
                                                                            lines.late_time = check_in - days.hour_from
                                                                        else:
                                                                            lines.write({
                                                                                'is_calculated': True,
                                                                                'late_time_store_value': 0,
                                                                                'late_time': 0
                                                                            })
                                                                            lines.late_time = 0
                                                                    else:
                                                                        lines.write({
                                                                            'is_calculated': True,
                                                                            'late_time_store_value': check_in - days.hour_from,
                                                                            'late_time': check_in - days.hour_from
                                                                        })
                                                                        lines.late_time = check_in - days.hour_from
                    else:
                        lines.late_time = 0.0

                except Exception as e:
                    print(str(e))

    # over time calculation according to the configuration
    @api.multi
    @api.depends('check_in', 'check_out', 'employee_id')
    def _get_ot_time(self):
        for lines in self:
            if lines.check_in and lines.check_out:
                try:
                    company_nopay_policy = self.env['hr.over.time.configuration']
                    procedure = company_nopay_policy.search([])
                    criteria = procedure.criteria
                    criteria_two = procedure.criteria_two
                    day = datetime.strptime(lines.check_in, '%Y-%m-%d %H:%M:%S').weekday()
                    worked_hours = lines.worked_hours
                    check_in_time = fields.Datetime.to_string(
                        fields.Datetime.from_string(lines.check_in) + timedelta(hours=5, minutes=30))
                    check_in = convert_to_float(check_in_time)
                    check_out_time = fields.Datetime.to_string(
                        fields.Datetime.from_string(lines.check_out) + timedelta(hours=5, minutes=30))
                    check_out = convert_to_float(check_out_time)
                    check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
                    check_out_date = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S').date()
                    over_time = 0
                    # if shift is selected
                    if procedure.over_time == 'yes':
                        if criteria == 'shift':
                            for schedule_history in self.env['schedule.history'].search(
                                    [('from_date', '<=', lines.check_in),
                                     ('to_date', '>=', lines.check_in),
                                     ('emp_id', '=', lines.employee_id.id)]):
                                shift_period = self.env['resource.calendar.attendance'].search([
                                    ('calendar_id', '=', schedule_history.resource_calendar_id.id),
                                    ('dayofweek', '=', day)])
                                if schedule_history.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                    shift_time_period = (shift_period.hour_to + 24) - shift_period.hour_from
                                elif schedule_history.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                    shift_time_period = (shift_period.hour_to + 24) - shift_period.hour_from
                                else:
                                    shift_time_period = shift_period.hour_to - shift_period.hour_from

                                lines._cr.execute(
                                    "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (lines.date, lines.employee_id.id))
                                morning = lines._cr.fetchall()
                                # works morning

                                lines._cr.execute(
                                    "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (lines.date, lines.employee_id.id))
                                evening = lines._cr.fetchall()

                                if morning and evening:
                                    from_date = evening[0][6]
                                    to_date = evening[0][7]
                                    if (schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):

                                        margin = shift_time_period / 2
                                        margin_time = shift_period.hour_from + margin
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration:
                                            if from_date < margin_time:
                                                if (check_in < to_date and check_out > shift_period.hour_to) or \
                                                        (check_in == to_date and check_out == shift_period.hour_to):
                                                    if check_out < shift_period.hour_to:
                                                        over_time = (check_out + 24) - shift_period.hour_to
                                                    else:
                                                        over_time = check_out - shift_period.hour_to
                                                elif check_in > to_date and check_out > shift_period.hour_to:
                                                    estimated = check_in + work_duration
                                                    if check_out < estimated:
                                                        over_time = (check_out + 24) - estimated
                                                    else:
                                                        over_time = check_out - estimated
                                                else:
                                                    over_time = 0
                                            else:
                                                if (check_in < shift_period.hour_from and check_out > from_date) or \
                                                        (check_in == shift_period.hour_from and check_out == from_date):
                                                    if check_out < from_date:
                                                        over_time = (check_out + 24) - from_date
                                                    else:
                                                        over_time = check_out - from_date
                                                elif check_in > shift_period.hour_from and check_out > from_date:
                                                    estimated = check_in + work_duration
                                                    if check_out < estimated:
                                                        over_time = (check_out + 24) - estimated
                                                    else:
                                                        over_time = check_out - estimated
                                                else:
                                                    over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = check_out - shift_period.hour_to
                                elif morning:
                                    from_date = morning[0][6]
                                    to_date = morning[0][7]
                                    if (schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration:
                                            if (check_in < shift_period.hour_from and check_out > from_date) or \
                                                    (check_in == shift_period.hour_from and check_out == from_date):
                                                if check_out < from_date:
                                                    over_time = (check_out + 24) - from_date
                                                else:
                                                    over_time = over_time - from_date
                                            elif check_in > shift_period.hour_from and check_out > from_date:
                                                estimated = check_in + work_duration
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            else:
                                                over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = check_out - shift_period.hour_to

                                elif evening:
                                    from_date = evening[0][6]
                                    to_date = evening[0][7]
                                    if (schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration:
                                            if (check_in < to_date and check_out > shift_period.hour_to) or \
                                                    (check_in == to_date and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            elif check_in > to_date and check_out > shift_period.hour_to:
                                                estimated = check_in + work_duration
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            else:
                                                over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = check_out - shift_period.hour_to
                                else:
                                    if worked_hours >= shift_time_period:
                                        # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                        if (check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                (check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                            if check_out < shift_period.hour_to:
                                                over_time = (check_out + 24) - shift_period.hour_to
                                            else:
                                                over_time = check_out - shift_period.hour_to
                                        # case two => comes late and leaves late
                                        elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                            estimated = check_in + shift_time_period
                                            if check_out < estimated:
                                                over_time = (check_out + 24) - estimated
                                            else:
                                                over_time = check_out - estimated
                                        # case three else part returns 00
                                        else:
                                            over_time = check_out - shift_period.hour_to

                            if criteria_two == 'buffer_hours':
                                if over_time > procedure.time:
                                    lines.ot_time = over_time
                                    lines.write({'ot_hour': over_time})
                                else:
                                    lines.ot_time = 0.0
                                    lines.write({'ot_hour': 0.0})
                            elif criteria_two == 'every_min':
                                lines.write({'ot_hour': over_time})
                                lines.ot_time = over_time
                                # print "yes"
                            elif criteria_two == 'hourly':
                                ot_time = over_time
                                if procedure.time_period == 'hour':
                                    time = float_to_time(ot_time)
                                    hour = time.hour
                                    lines.ot_time = hour
                                    lines.write({'ot_hour': hour})
                                elif procedure.time_period == 'half_hour':
                                    over_time = ot_time / 0.5
                                    time = float_to_time(over_time)
                                    half_hour = float_to_time(time.hour)
                                    half_hour = datetime.strptime(str(half_hour), '%H:%M:%S')
                                    half_hour = convert_to_float(str(half_hour))
                                    half_hour = half_hour / 2
                                    lines.ot_time = half_hour
                                    lines.write({'ot_hour': half_hour})
                                elif procedure.time_period == 'quarter_hour':
                                    over_time = ot_time / 0.25
                                    time = float_to_time(over_time)
                                    quarter_hours = float_to_time(time.hour)
                                    quarter_hour = datetime.strptime(str(quarter_hours), '%H:%M:%S')
                                    quarter_hour = convert_to_float(str(quarter_hour))
                                    quarter_hour = quarter_hour / 4
                                    lines.ot_time = quarter_hour
                                    lines.write({'ot_hour': quarter_hour})
                                else:
                                    pass
                            else:
                                lines.ot_time = 0.0
                                lines.write({'ot_hour': over_time})

                        # if specific day is selected
                        elif criteria == 'specific_day':
                            allocated_day = int(procedure.days)
                            for schedule_history in self.env['schedule.history'].search(
                                    [('from_date', '<=', lines.check_in),
                                     ('to_date', '>=', lines.check_in),
                                     ('emp_id', '=', lines.employee_id.id)]):
                                shift_period = self.env['resource.calendar.attendance'].search([
                                    ('calendar_id', '=', schedule_history.resource_calendar_id.id),
                                    ('dayofweek', '=', day)])
                                if schedule_history.resource_calendar_id.is_swing_shift and check_in_date < check_out_date:
                                    shift_time_period = (shift_period.hour_to + 24) - shift_period.hour_from
                                elif schedule_history.resource_calendar_id.is_swing_shift and check_in_date == check_out_date:
                                    shift_time_period = (shift_period.hour_to + 24) - shift_period.hour_from
                                else:
                                    shift_time_period = shift_period.hour_to - shift_period.hour_from

                                lines._cr.execute(
                                    "select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (lines.date, lines.employee_id.id))
                                morning = lines._cr.fetchall()
                                # works morning

                                lines._cr.execute(
                                    "select * from hr_holidays where (date_to + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (lines.date, lines.employee_id.id))
                                evening = lines._cr.fetchall()

                                if morning and evening:
                                    from_date = evening[0][6]
                                    to_date = evening[0][7]
                                    if (
                                            schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):
                                        margin = shift_time_period / 2
                                        margin_time = shift_period.hour_from + margin
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration and allocated_day == day:
                                            if from_date < margin_time:
                                                if (check_in < to_date and check_out > shift_period.hour_to) or \
                                                        (check_in == to_date and check_out == shift_period.hour_to):
                                                    if check_out < shift_period.hour_to:
                                                        over_time = (check_out + 24) - shift_period.hour_to
                                                    else:
                                                        over_time = check_out - shift_period.hour_to
                                                elif check_in > to_date and check_out > shift_period.hour_to:
                                                    estimated = check_in + work_duration
                                                    if check_out < estimated:
                                                        over_time = (check_out + 24) - estimated
                                                    else:
                                                        over_time = check_out - estimated
                                                else:
                                                    over_time = 0
                                            else:
                                                if (check_in < shift_period.hour_from and check_out > from_date) or \
                                                        (check_in == shift_period.hour_from and check_out == from_date):
                                                    if check_out < from_date:
                                                        over_time = (check_out + 24) - from_date
                                                    else:
                                                        over_time = check_out - from_date
                                                elif check_in > shift_period.hour_from and check_out > from_date:
                                                    estimated = check_in + work_duration
                                                    if check_out < estimated:
                                                        over_time = (check_out + 24) - estimated
                                                    else:
                                                        over_time = check_out - estimated
                                                else:
                                                    over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period and allocated_day == day:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = 0.0

                                elif morning:
                                    from_date = morning[0][6]
                                    to_date = morning[0][7]
                                    if (
                                            schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration  and allocated_day == day:
                                            if (check_in < shift_period.hour_from and check_out > from_date) or \
                                                    (check_in == shift_period.hour_from and check_out == from_date):
                                                if check_out < from_date:
                                                    over_time = (check_out + 24) - from_date
                                                else:
                                                    over_time = check_out - from_date
                                            elif check_in > shift_period.hour_from and check_out > from_date:
                                                estimated = check_in + work_duration
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            else:
                                                over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period and allocated_day == day:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = 0.0

                                elif evening:
                                    from_date = evening[0][6]
                                    to_date = evening[0][7]
                                    if (
                                            schedule_history.from_date <= from_date and schedule_history.to_date >= from_date) or (
                                            schedule_history.from_date <= to_date and schedule_history.to_date >= to_date):
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
                                        work_duration = shift_time_period - holiday_duration
                                        if worked_hours > work_duration  and allocated_day == day:
                                            if (check_in < to_date and check_out > shift_period.hour_to) or \
                                                    (check_in == to_date and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            elif check_in > to_date and check_out > shift_period.hour_to:
                                                estimated = check_in + work_duration
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            else:
                                                over_time = 0
                                    else:
                                        if worked_hours >= shift_time_period and allocated_day == day:
                                            # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                            if (
                                                    check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                    (
                                                            check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                                if check_out < shift_period.hour_to:
                                                    over_time = (check_out + 24) - shift_period.hour_to
                                                else:
                                                    over_time = check_out - shift_period.hour_to
                                            # case two => comes late and leaves late
                                            elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                                estimated = check_in + shift_time_period
                                                if check_out < estimated:
                                                    over_time = (check_out + 24) - estimated
                                                else:
                                                    over_time = check_out - estimated
                                            # case three else part returns 00
                                            else:
                                                over_time = 0.0
                                else:
                                    if worked_hours >= shift_time_period and allocated_day == day:
                                        # case one => comes early and leave late or comes correctly at shift and leave correctly at shift
                                        if (check_in < shift_period.hour_from and check_out > shift_period.hour_to) or \
                                                (check_in == shift_period.hour_from and check_out == shift_period.hour_to):
                                            if check_out < shift_period.hour_to:
                                                over_time = (check_out + 24) - shift_period.hour_to
                                            else:
                                                over_time = check_out - shift_period.hour_to
                                        # case two => comes late and leaves late
                                        elif check_in > shift_period.hour_from and check_out > shift_period.hour_to:
                                            estimated = check_in + shift_time_period
                                            if check_out < estimated:
                                                over_time = (check_out + 24) - estimated
                                            else:
                                                over_time = check_out - estimated
                                        # case three else part returns 00
                                        else:
                                            over_time = 0.0

                            if criteria_two == 'buffer_hours':
                                if over_time > procedure.time:
                                    lines.ot_time = over_time
                                    lines.write({'ot_hour': over_time})
                                else:
                                    lines.ot_time = 0.0
                            elif criteria_two == 'every_min':
                                lines.ot_time = over_time
                                lines.write({'ot_hour': over_time})
                            elif criteria_two == 'hourly':
                                ot_time = over_time
                                if procedure.time_period == 'hour':
                                    time = float_to_time(ot_time)
                                    hour = time.hour
                                    lines.ot_time = hour
                                    lines.write({'ot_hour': hour})

                                elif procedure.time_period == 'half_hour':
                                    over_time = ot_time / 0.5
                                    time = float_to_time(over_time)
                                    half_hour = float_to_time(time.hour)
                                    half_hour = datetime.strptime(str(half_hour), '%H:%M:%S')
                                    half_hour = convert_to_float(str(half_hour))
                                    half_hour = half_hour / 2
                                    lines.ot_time = half_hour
                                    lines.write({'ot_hour': half_hour})

                                elif procedure.time_period == 'quarter_hour':
                                    over_time = ot_time / 0.25
                                    time = float_to_time(over_time)
                                    quarter_hours = float_to_time(time.hour)
                                    quarter_hour = datetime.strptime(str(quarter_hours), '%H:%M:%S')
                                    quarter_hour = convert_to_float(str(quarter_hour))
                                    quarter_hour = quarter_hour / 4
                                    lines.ot_time = quarter_hour
                                    lines.write({'ot_hour': quarter_hour})
                                else:
                                    pass
                            else:
                                lines.ot_time = 0.0
                                lines.write({'ot_hour': over_time})

                except Exception as e:
                    print (str(e))


    @api.multi
    def deduct_from_leaves(self, lines, late_time, diff, shift):
        # get remaining sort leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.employee_id.id) + "'AND s.name = 'Short Leaves' GROUP BY h.holiday_status_name, h.holiday_status_id, h.employee_id")
        short_leaves = lines._cr.fetchall()

        # get remaining annual leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.employee_id.id) + "'AND s.name = 'Annual Leaves' GROUP BY h.holiday_status_name, h.holiday_status_id, h.employee_id")
        annual_leaves = lines._cr.fetchall()

        # get remaining casual leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name, h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.employee_id.id) + "'AND s.name = 'Casual Leaves' GROUP BY h.holiday_status_name,h.holiday_status_id, h.employee_id")
        casual_leaves = lines._cr.fetchall()

        # get remaining sick leaves
        lines._cr.execute(
            "SELECT sum(h.number_of_days) AS days, h.employee_id, h.holiday_status_name,h.holiday_status_id FROM hr_holidays h join hr_holidays_status s ON (s.name=h.holiday_status_name) WHERE h.state='validate' AND s.limit=False AND h.employee_id='" + str(
                lines.employee_id.id) + "'AND s.name = 'Sick Leaves' GROUP BY h.holiday_status_name,h.holiday_status_id, h.employee_id")
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

        lines._cr.execute("select * from hr_holidays where (date_from + INTERVAL '5 hours' + INTERVAL '30 minutes'):: date = %s and employee_id = %s and state = 'validate'",
                                    (lines.date, lines.employee_id.id))
        hr_holiday = lines._cr.fetchall()

        if not hr_holiday:
            # if late -> deduct from short leaves
            if number_of_short_leaves:
                if number_of_short_leaves >= 0:
                    self.env['hr.holidays'].create({
                        'name': _('Late attendance Short Leave Allocation for %s') % lines.employee_id.name,
                        'employee_id': lines.employee_id.id,
                        'holiday_status_id': short_leaves[0][3],
                        'type': 'remove',
                        'date_from': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=(shift.hour_from)) - timedelta(hours=5, minutes=30)),
                        'date_to': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=(shift.hour_from + (diff / 4)) - float(5)) - timedelta(minutes=30)),
                        'holiday_type': 'employee',
                        'number_of_days_temp': 1,
                        'number_of_days': -1,
                        'state': 'validate'
                    })
                    lines.write({'is_deduct': True})

            # if late -> no remaining short leaves deduct from casual leaves
            if number_of_casual_leaves:
                if number_of_short_leaves <= 0 and number_of_casual_leaves >= 0:
                    if late_time <= (diff / 4) and number_of_casual_leaves >= 0.5:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Half Day Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': casual_leaves[0][3],
                            'type': 'remove',
                            'date_from': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=shift.hour_from) - timedelta(hours=5, minutes=30)),
                            'date_to': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=(shift.hour_from + (diff / 2)) - float(5)) - timedelta(minutes=30)),
                            'holiday_type': 'employee',
                            'number_of_days_temp': 0.5,
                            'number_of_days': -0.5,
                            'state': 'validate'
                        })
                        lines.write({'is_deduct': True})

                    elif late_time > (diff / 4) and number_of_casual_leaves >= 1:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Casual Leave Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': casual_leaves[0][3],
                            'type': 'remove',
                            'date_from': lines.check_in,
                            'date_to': lines.check_out,
                            'holiday_type': 'employee',
                            'number_of_days_temp': 1,
                            'number_of_days': -1,
                            'state': 'validate',
                        })
                        lines.write({'is_deduct': True})

            # if late -> no remaining short leaves and casual leaves deduct from annual leaves
            if number_of_annual_leaves:
                if number_of_short_leaves <= 0 and number_of_casual_leaves <= 0 and number_of_annual_leaves >= 0:
                    if late_time <= (diff / 4) and number_of_annual_leaves >= 0.5:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Half Day Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': annual_leaves[0][3],
                            'type': 'remove',
                            'date_from': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=shift.hour_from) - timedelta(hours=5, minutes=30)),
                            'date_to': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=(shift.hour_from + (diff / 2)) - float(5)) - timedelta(minutes=30)),
                            'holiday_type': 'employee',
                            'number_of_days_temp': 0.5,
                            'number_of_days': -0.5,
                            'state': 'validate'
                        })
                        lines.write({'is_deduct': True})

                    elif late_time > (diff / 4) and number_of_annual_leaves >= 1:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Annual Leave Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': annual_leaves[0][3],
                            'type': 'remove',
                            'date_from': lines.check_in,
                            'date_to': lines.check_out,
                            'holiday_type': 'employee',
                            'number_of_days_temp': 1,
                            'number_of_days': -1,
                            'state': 'validate'
                        })
                        lines.write({'is_deduct': True})

            # if late -> no remaining half days, short leaves and casual leaves deduct from sick leaves
            if number_of_sick_leaves:
                if number_of_short_leaves <= 0 and number_of_casual_leaves <= 0 and number_of_annual_leaves <= 0 and number_of_sick_leaves >= 0:
                    if late_time <= (diff / 4) and number_of_sick_leaves >= 0.5:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Half Day Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': sick_leaves[0][3],
                            'type': 'remove',
                            'date_from': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=shift.hour_from) - timedelta(hours=5, minutes=30)),
                            'date_to': fields.Datetime.to_string(fields.Datetime.from_string(lines.date) + timedelta(hours=(shift.hour_from + (diff / 2)) - float(5)) - timedelta(minutes=30)),
                            'holiday_type': 'employee',
                            'number_of_days_temp': 0.5,
                            'number_of_days': -0.5,
                            'state': 'validate',
                        })
                        lines.write({'is_deduct': True})

                    elif late_time > (diff / 4) and number_of_sick_leaves >= 1:
                        self.env['hr.holidays'].create({
                            'name': _('Late attendance Sick Leave Allocation for %s') % lines.employee_id.name,
                            'employee_id': lines.employee_id.id,
                            'holiday_status_id': sick_leaves[0][3],
                            'type': 'remove',
                            'date_from': lines.check_in,
                            'date_to': lines.check_out,
                            'holiday_type': 'employee',
                            'number_of_days_temp': 1,
                            'number_of_days': -1,
                            'state': 'validate',
                        })
                        lines.write({'is_deduct': True})
        return True


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    is_swing_shift = fields.Boolean(string='Swing Shift', default=False)


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    holiday_status_name = fields.Char(related='holiday_status_id.name', string="Holiday Name", store=True)
    leave_allocation_log = fields.One2many('leave.allocation.log', 'allocation_id', string='Leave Allocation Log')


class LeaveAllocationLog(models.Model):
    _name = 'leave.allocation.log'
    _order = 'date_time desc'

    allocation_id = fields.Many2one('hr.holidays', string='Allocation Id')
    holiday_status_id = fields.Many2one('hr.holidays.status', string='Leave Type')
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    reason = fields.Char(string='Reason')
    date_time = fields.Datetime(string='Date Time', default=lambda self: fields.Datetime.now())
