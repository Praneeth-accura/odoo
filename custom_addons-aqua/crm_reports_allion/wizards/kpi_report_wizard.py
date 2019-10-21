from odoo import fields, models, api
from datetime import datetime, date, time, timedelta
import xlsxwriter
import base64
from odoo.tools import misc
import os
import math

class KpiReportsWizard(models.TransientModel):
    _name = 'kpi.reports.wizard'

    def _get_id(self):
        if self.env['project.project'].browse(1):
            id = self.env['project.project'].browse(1)
            return id

    report_type = fields.Selection([('project_status', 'Status of Each Project'),
                                    ('quotation_status', 'Quotation Status (Won and Loss)'),
                                    ('loss_reason', 'Reason for Loss'),
                                    ('projects_by_employee', 'Number of new projects handled per Employee'),
                                    ('visits_by_employee', 'Number of Visits handled per Employee'),
                                    ('calls_by_employee', 'Number of Calls handled per Employee'),
                                    ('employee_rating', 'Employee Rating')], string="Report Type", required=True,
                                   default='project_status')
    user_id = fields.Many2one('res.users', string='Project Manager', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    employee_action_by = fields.Selection([('crm', 'By CRM'),
                                           ('helpdesk', 'By HelpDesk')])
    project_id = fields.Many2one('project.project', string='Project', required=False, default=_get_id)
    date_from = fields.Datetime(string="Date From", default=datetime.now())
    date_to = fields.Datetime(string="Date To", default=datetime.now())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)

    @api.multi
    def export_kpi_report(self, fl=None):
        if fl == None:
            fl = ''
        if self.report_type == 'project_status':
            fl = self.print_project_status_report()
        elif self.report_type == 'quotation_status':
            fl = self.print_quotation_status_report()
        elif self.report_type == 'loss_reason':
            fl = self.print_loss_reason_report()
        elif self.report_type == 'projects_by_employee':
            fl = self.print_projects_by_employee_report()
        elif self.report_type == 'visits_by_employee' and self.employee_action_by == 'crm':
            fl = self.print_visits_by_employee_report_crm()
        elif self.report_type == 'calls_by_employee' and self.employee_action_by == 'crm':
            fl = self.print_calls_by_employee_report_crm()
        elif self.report_type == 'visits_by_employee'and self.employee_action_by == 'helpdesk':
            fl = self.print_visits_by_employee_report_helpdesk()
        elif self.report_type == 'calls_by_employee' and self.employee_action_by == 'helpdesk':
            fl = self.print_calls_by_employee_report_helpdesk()
        elif self.report_type == 'employee_rating':
            fl = self.print_employee_rating_report()

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
            'res_model': 'kpi.reports.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(fl)
        return result

    @api.multi
    def print_project_status_report(self):
        fl = os.path.join(os.path.dirname(__file__), 'Status of Each Project' + '.xlsx')
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
        worksheet.set_column('A:H', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:H1', 'Status of Each Project', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "PROJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "PROJECT MANAGER", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "WORKING TIME", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "STATUS", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "STAGE", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "CREATE DATE", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "DONE DATE", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "DEADLINE DATE", font_bold_center)

        row += 2

        projects_obj = self.env['project.project']

        for projects in projects_obj.search(['|', ('active', '=', True), ('active', '=', False)]):
            if projects.active == True:
                status = 'Active'
            else:
                status = 'Inactive'
            worksheet.write(row, col, projects.name, font_left)
            worksheet.write(row, col + 1, projects.user_id.name, font_left)
            worksheet.write(row, col + 2, projects.resource_calendar_id.name, font_left)
            worksheet.write(row, col + 3, status, font_left)
            worksheet.write(row, col + 4, projects.stage_id.name, font_left)
            worksheet.write(row, col + 5, projects.create_date, font_left)
            worksheet.write(row, col + 6, projects.done_date, font_left)
            worksheet.write(row, col + 7, projects.date_deadline, font_left)

            row += 1

        workbook.close()
        return fl

    @api.multi
    def print_quotation_status_report(self):
        fl = os.path.join(os.path.dirname(__file__), 'Quotation Status( Won or Loss )' + '.xlsx')
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
        worksheet.set_column('A:I', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:I1', 'Quotation Status( Won or Loss )', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "LEAD NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "SALES PERSON", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "SALES TEAM", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "CUSTOMER", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "DEPARTMENT", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "PRODUCT", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "STATUS", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "DATE", font_bold_center)

        row += 2

        crm_lead_obj = self.env['crm.lead']
        for leads in crm_lead_obj.search([('stage_id', 'in', [4, 5])]):
            worksheet.write(row, col, leads.name, font_left)
            worksheet.write(row, col + 1, leads.user_id.name, font_left)
            worksheet.write(row, col + 2, leads.team_id.name, font_left)
            worksheet.write(row, col + 3, leads.partner_id.name, font_left)
            worksheet.write(row, col + 4, leads.department_id.name, font_left)
            worksheet.write(row, col + 5, leads.product_id.name, font_left)
            worksheet.write(row, col + 6, leads.stage_id.name, font_left)
            worksheet.write(row, col + 7, leads.date, font_left)

            row += 1

        workbook.close()
        return fl

    @api.multi
    def print_loss_reason_report(self):
        fl = os.path.join(os.path.dirname(__file__), 'Quotation Status( Won or Loss )' + '.xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        font_left_bold = workbook.add_format({'align': 'left',
                                              'border': 1,
                                              'font_size': 10,
                                              'bold': True})
        font_left_grey = workbook.add_format({'align': 'left',
                                              'border': 1,
                                              'font_size': 10,
                                              'bold': True,
                                              'bg_color': '#E8E8E8'})
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True})
        border = workbook.add_format({'border': 1})
        #         date_format = workbook.add_format({'num_format': 'dd-mm-yy hh:mm:ss'})

        worksheet.set_column('N:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:J', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:J1', 'Quotation Status( Won or Loss )', bold)

        row = 2
        col = 0
        worksheet.merge_range(row, col, row + 1, col, "LEAD NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "SALES PERSON", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "SALES TEAM", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "CUSTOMER", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "DEPARTMENT", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "PRODUCT", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "STATUS", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "DATE", font_bold_center)
        worksheet.merge_range(row, col + 8, row + 1, col + 8, "LOSS REASON", font_bold_center)

        row += 2

        crm_lead_obj = self.env['crm.lead']
        for leads in crm_lead_obj.search([('stage_id', '=', 5)]):
            worksheet.write(row, col, leads.name, font_center)
            worksheet.write(row, col + 1, leads.user_id.name, font_left)
            worksheet.write(row, col + 2, leads.team_id.name, font_center)
            worksheet.write(row, col + 3, leads.partner_id.name, font_center)
            worksheet.write(row, col + 4, leads.department_id.name, font_center)
            worksheet.write(row, col + 5, leads.product_id.name, font_center)
            worksheet.write(row, col + 6, leads.stage_id.name, font_center)
            worksheet.write(row, col + 7, leads.date, font_center)
            worksheet.write(row, col + 8, leads.lost_reason.name, font_center)
            row += 1

        workbook.close()
        return fl

    @api.multi
    def print_projects_by_employee_report(self):

        fl = os.path.join(os.path.dirname(__file__), 'Number of new projects handled per Employee' + '.xlsx')
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
        worksheet.set_column('A:G', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:G1', 'Number of new projects handled per Employee', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "PROJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "PROJECT MANAGER", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "WORKING TIME", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "STATUS", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "STAGE", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "CREATE DATE", font_bold_center)

        row += 2

        projects_obj = self.env['project.project']

        for projects in projects_obj.search(['|', ('active', '=', True), ('active', '=', False)]):
            if self.user_id == projects.user_id:
                if projects.active == True:
                    status = 'Active'
                else:
                    status = 'Inactive'
                worksheet.write(row, col, projects.name, font_left)
                worksheet.write(row, col + 1, projects.user_id.name, font_left)
                worksheet.write(row, col + 2, projects.resource_calendar_id.name, font_left)
                worksheet.write(row, col + 3, status, font_left)
                worksheet.write(row, col + 4, projects.stage_id.name, font_left)
                worksheet.write(row, col + 5, projects.create_date, font_left)

                row += 1

        workbook.close()
        return fl

    @api.multi
    def print_visits_by_employee_report_crm(self):
        fl = os.path.join(os.path.dirname(__file__), 'Number of Visits handled per Employee (CRM) from '
                          + str(self.date_from) + ' to ' + str(self.date_to) + '.xlsx')
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
        worksheet.merge_range('A1:E1', 'Number of Visits handled per Employee (CRM)', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "PROJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "RESPONSIBLE", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "PROJECT TASK NAME", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "CREATE DATE", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "DEADLINE DATE", font_bold_center)

        row += 2

        schedule_obj = self.env['mail.activity']
        project_task_obj = self.env['project.task']

        for activities in schedule_obj.search([('res_model', '=', 'project.task'), ('activity_type_id', '=', 3),
                                               ('create_date', '>=', self.date_from), ('create_date', '<=', self.date_to),
                                               ('user_id', '=', self.user_id.id)]):
            task = project_task_obj.browse([(activities.res_id)])
            if task.project_id == self.project_id:
                worksheet.write(row, col, task.project_id.name, font_left)
                worksheet.write(row, col + 1, activities.user_id.name, font_left)
                worksheet.write(row, col + 2, activities.res_name, font_left)
                worksheet.write(row, col + 3, str(datetime.strptime(activities.create_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)), font_left)
                worksheet.write(row, col + 4, activities.date_deadline, font_left)

                row += 1

        workbook.close()
        return fl

    @api.multi
    def print_calls_by_employee_report_crm(self):
        fl = os.path.join(os.path.dirname(__file__), 'Number of Calls handled per Employee (CRM) from '
                          + str(self.date_from) + ' to ' + str(self.date_to) + '.xlsx')
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
        worksheet.merge_range('A1:E1', 'Number of Calls handled per Employee (CRM)', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "PROJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "RESPONSIBLE", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "PROJECT TASK NAME", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "CREATE DATE", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "DEADLINE DATE", font_bold_center)

        row += 2

        schedule_obj = self.env['mail.activity']
        project_task_obj = self.env['project.task']

        for activities in schedule_obj.search([('res_model', '=', 'project.task'), ('activity_type_id', '=', 2),
                                               ('create_date', '>=', self.date_from), ('create_date', '<=', self.date_to),
                                               ('user_id', '=', self.user_id.id)]):
            task = project_task_obj.browse([(activities.res_id)])
            if task.project_id == self.project_id:
                worksheet.write(row, col, task.project_id.name, font_left)
                worksheet.write(row, col + 1, activities.user_id.name, font_left)
                worksheet.write(row, col + 2, activities.res_name, font_left)
                worksheet.write(row, col + 3, str(datetime.strptime(activities.create_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)), font_left)
                worksheet.write(row, col + 4, activities.date_deadline, font_left)

                row += 1

        workbook.close()
        return fl

    @api.multi
    def print_calls_by_employee_report_helpdesk(self):
        fl = os.path.join(os.path.dirname(__file__), 'Number of Calls handled Visits Employee (Helpdesk) from '
                          + str(self.date_from) + ' to ' + str(self.date_to) + '.xlsx')
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
        worksheet.merge_range('A1:E1', 'Number of Calls handled Visits Employee (Helpdesk)', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "SUBJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "DATE", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "SUMMARY", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "CONTACT", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "RESPONSIBLE", font_bold_center)

        row += 2

        crm_phone_obj = self.env['crm.phone.calls']

        date_from = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').date()
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').date()

        for calls in crm_phone_obj.search([('date', '>=', str(date_from)), ('date', '<=', str(date_to)), ('user_id', '=', self.user_id.id)]):
            if calls.crm_helpdesk_id:
                crm_help_desk_obj = self.env['crm.helpdesk'].browse(calls.crm_helpdesk_id.id)
                worksheet.write(row, col, crm_help_desk_obj.name, font_left)
                worksheet.write(row, col + 1, str(datetime.strptime(calls.date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5, minutes=30)), font_left)
                worksheet.write(row, col + 2, calls.name, font_left)
                worksheet.write(row, col + 3, calls.partner_id.name, font_left)
                worksheet.write(row, col + 4, calls.user_id.name, font_left)
                row += 1

        workbook.close()
        return fl

    @api.multi
    def print_visits_by_employee_report_helpdesk(self):
        fl = os.path.join(os.path.dirname(__file__), 'Number of Calls handled Visits Employee (Helpdesk) from '
                          + str(self.date_from) + ' to ' + str(self.date_to) + '.xlsx')
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
        worksheet.merge_range('A1:E1', 'Number of Calls handled Visits Employee (Helpdesk)', bold)

        row = 2
        col = 0

        worksheet.merge_range(row, col, row + 1, col, "SUBJECT NAME", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "DATE", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "TOKEN NO.", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "DEADLINE", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "RESPONSIBLE", font_bold_center)

        row += 2

        crm_help_desk_obj = self.env['crm.helpdesk']

        date_from = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').date()
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').date()

        for calls in crm_help_desk_obj.search(
                [('date', '>=', str(date_from)), ('date', '<=', str(date_to)), ('user_id', '=', self.user_id.id), ('job_type', '=', 'visit')]):
                worksheet.write(row, col, calls.name, font_left)
                worksheet.write(row, col + 1, calls.date, font_left)
                worksheet.write(row, col + 2, str(calls.token_no), font_left)
                worksheet.write(row, col + 3, calls.date_deadline, font_left)
                worksheet.write(row, col + 4, calls.user_id.name, font_left)
                row += 1

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
            'res_model': 'kpi.reports.wizard',
            'target': 'new',
        }
        return result

