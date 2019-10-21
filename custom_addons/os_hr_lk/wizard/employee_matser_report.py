# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).


from odoo import api, fields, models
from datetime import date
import xlsxwriter

class EmployeeMasterReport(models.TransientModel):
    _name = "employee.master.report"
    
    employee_id = fields.Many2one('hr.employee', string='Employee')
    dept_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    joining_date_from = fields.Date(string='From')
    joining_date_to = fields.Date(string='To')
    basic_salary_from = fields.Float(string='From', digits=(16, 2))
    basic_salary_to = fields.Float(string='To', digits=(16, 2))
    current_date = fields.Date('Date current action', default = date.today())
    leave_date_from = fields.Datetime(string='From')
    leave_date_to = fields.Datetime(string='To')
    report_type = fields.Selection([('master','Employee Details'),('leave','Leave Details')],string="Report Type", default='master')

    @api.multi
    def print_employee_report(self):
        if self.report_type == 'master':
            return self.env.ref('os_hr_lk.action_employee_master').report_action(self.id)
        if self.report_type == 'leave':
            return self.env.ref('os_hr_lk.action_leave_details').report_action(self.id)
        
    @api.multi
    def load_selected_details(self):
        domain = []
        if self.report_type == 'master':
            if self.employee_id:
                domain.append(('id','=',self.employee_id.id))
            if self.dept_id:
                domain.append(('department_id','=',self.dept_id.id))
            if self.job_id:
                domain.append(('job_id','=',self.job_id.id))
            if self.joining_date_from:
                domain.append(('joining_date','>=',self.joining_date_from))
            if self.joining_date_to:
                domain.append(('joining_date','<=',self.joining_date_to))
            if domain != []:
                employees  = self.env['hr.employee'].search(domain,order="employee_code")
                return employees
            else:
                employees  = self.env['hr.employee'].search([],order="employee_code")
                return employees
        if self.report_type == 'leave':
            if self.employee_id:
                domain.append(('employee_id','=',self.employee_id.id))
            if self.dept_id:
                domain.append(('department_id','=',self.dept_id.id))
            if self.leave_date_from:
                domain.append(('date_from','>=',self.leave_date_from))
            if self.leave_date_to:
                domain.append(('date_to','<=',self.leave_date_to))
            domain.append(('state','=','validate'))
            leaves  = self.env['hr.holidays'].search(domain,order="employee_id")
            return leaves
        
        