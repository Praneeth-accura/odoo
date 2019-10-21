from odoo import fields, models, api
from datetime import datetime, date, time, timedelta
import xlsxwriter
import base64
from odoo.tools import misc
import os
import math

class AssignmentReportWizard(models.TransientModel):
    _name = 'assignment.report.wizard'

    report_type = fields.Selection([('number_of_projects', 'Number of Projects completed on time')], string="Report Type", required=True)
    date_from = fields.Datetime(string="Date From", default=datetime.now())
    date_to = fields.Datetime(string="Date To", default=datetime.now())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)

    def export_assignment_report(self, fl=None):
        if fl == None:
            fl = ''
        if self.report_type == 'number_of_projects':
            fl = self.print_number_of_projects()

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
            'res_model': 'assignment.report.wizard',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(fl)
        return result

    @api.multi
    def print_number_of_projects(self):
        fl = os.path.join(os.path.dirname(__file__), 'Number of Projects completed on time from '
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
        worksheet.set_column('A:H', 20, border)
        worksheet.set_row(0, 20)
        worksheet.merge_range('A1:H1', 'Number of Projects completed on time', bold)

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
            if projects.stage_id.id == 3:
                if projects.done_date <= projects.date_deadline and projects.date_deadline >= self.date_from and projects.date_deadline <= self.date_to:
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
    def action_back(self):
        if self._context is None:
            self._context = {}
        self.is_printed = False
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'assignment.report.wizard',
            'target': 'new',
        }
        return result


