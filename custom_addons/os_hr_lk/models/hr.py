# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from odoo.osv import expression

class Employee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee','mail.activity.mixin']
    _order = 'employee_code'
    
    @api.model
    def create(self, vals):
        prefix = self.env['ir.config_parameter'].get_param('prefix')
        config = self.env['ir.config_parameter'].get_param('config_emp_code')
        if config == 'auto':
            seq_obj = self.env['ir.sequence'].search([('code','=','hr.employee')])
            seq_obj.write({'prefix': prefix})
            if 'company_id' in vals:
                vals['employee_code'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('hr.employee')
            else:
                vals['employee_code'] = self.env['ir.sequence'].next_by_code('hr.employee')
                
            result = super(Employee, self).create(vals)
            return result
        else:
            result = super(Employee, self).create(vals)
            return result
            
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', ('name', operator, name), ('employee_code', operator, name)]
            ])
            return self.search(domain, limit=limit).name_get()
        return super(Employee, self).name_search(name, args, operator, limit)
    
    surname = fields.Char('Surname')
    surnames = fields.Char('Surname', required=False)
    initial = fields.Char('Initial', required=False)
    employee_code = fields.Char(string='Employee Code', copy=False,index=True, default=lambda self: ('New') )
    card_number = fields.Char(string='Card Number')
    joining_date = fields.Date(string='Joining Date')
    confirm_date = fields.Date(string='Confirm Date')
    terminate_date = fields.Date(string='Terminate Date')
    bank = fields.Many2one('res.bank', related='bank_account_id.bank_id', string="Bank", readonly=True)
    branch = fields.Many2one(related='bank_account_id.branch_id', string='Branch', readonly=True)
    licence_number = fields.Char(string='Driving Licence Number')
    religion_id = fields.Many2one('employee.religion', string="Religion")
    language_ids = fields.Many2many('res.lang', string='Communication Language')
    temp_address_id = fields.Many2one('res.partner', string="Temporary Address")
    is_temp_address_a_company = fields.Boolean('Employee temp address', compute='_compute_is_temp_address_a_company')
    personal_email =fields.Char(string='Personal Email')
    telephone_number = fields.Char(string='Telephone')
    mobile_number = fields.Char(string='Mobile')
    near_police_station = fields.Char(string='Nearest Police Station')
    emp_qualification_ids = fields.One2many('emp.qualifications','emp_id', string='Qualifications')
    prof_qualification_ids = fields.One2many('prof.qualifications','emp_id', string='Qualifications')
    promotion_ids  = fields.One2many('promotion.details','emp_id', string='Promotions')
    allowance_ids = fields.One2many('emp.allowances','emp_id', string='Allowances')
    employment_ids = fields.One2many('emp.employment','emp_id', string='Employments')
    family_ids = fields.One2many('emp.family','emp_id', string="Family Details")
    emp_code_config = fields.Selection([('manual','Manual'),('auto','Automated')],
                                         string='Employee code Config',
                                         default=lambda self: self.env['ir.config_parameter'].get_param('config_emp_code'))
    monthly_late_attendance_lines = fields.One2many('monthly.late.days', 'monthly_late_id', string='Number Of Days Monthly Late Attendance')

    _sql_constraints = [
        ('emp_code_uniq', 'unique(employee_code)', 'Employee Code must be unique!'),
    ]
    
    @api.depends('temp_address_id.parent_id')
    def _compute_is_temp_address_a_company(self):
        for employee in self:
            employee.is_temp_address_a_company = employee.temp_address_id.parent_id.id is not False
    
    
class Department(models.Model):
    _inherit = "hr.department"

    code = fields.Char(string='Department code')
    description = fields.Text(string='Description')
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', ('name', operator, name), ('code', operator, name)]
            ])
            return self.search(domain, limit=limit).name_get()
        return super(Department, self).name_search(name, args, operator, limit)
  
  
class EmployeeReligion(models.Model):
    _name = "employee.religion"
    
    name = fields.Char(string='Name', required=True)
    
    
class Qualification(models.Model):
    _name = "prof.qualification"
        
    name = fields.Char(string='Name', required=True)


class EmployeeAllowances(models.Model):
    _name = 'emp.allowances'
    
    name = fields.Char(string='Allowance', required=True)
    emp_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount')
    approved_date = fields.Date(string='Approved Date')
    
    
class Employment(models.Model):
    _name = 'emp.employment'
    _rec_name = 'emp_id'
    
    emp_id = fields.Many2one('hr.employee', string='Employee')
    company = fields.Char(string='Company', required=False)
    start_date = fields.Date(string='Start Date', required=False)
    end_date = fields.Date(string='End Date', required=False)
    address = fields.Char(string='Address')
    position = fields.Char(string='Position')
    industry = fields.Char(string='Industry')
    
    
class EmployeeQualifications(models.Model):
    _name = "emp.qualifications"
    _rec_name = 'emp_id'
    
    degree_id = fields.Many2one('hr.recruitment.degree', string='Degree', required=True)
    emp_id = fields.Many2one('hr.employee', string='Employee')
    comments = fields.Char(string='Comments')
    

class EmployeeFamily(models.Model):
    _name = "emp.family"
    
    emp_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(required=True, string='Name')
    relation = fields.Selection([('spouse', 'Spouse'), ('son', 'Son'), 
                                ('daughter', 'Daughter'), ('mother', 'Mother'), 
                                ('father', 'Father'), ('grandma', 'Grand Mother'), 
                                ('grandpa', 'Grand Father'), ('fatherinlaw', 'Father-in-Law'), 
                                ('motherinlaw', 'Mother-in-Law'), ('soninlaw', 'Son-in-Law'), 
                                ('daughterinlaw', 'Daughter-in-Law'), ('uncle', 'Unlce'), 
                                ('aunty', 'Aunty'), ('bro', 'Brother'), ('sis', 'Sister'), 
                                ('cousin', 'Cousin')], string='Relation')
    emergency_contact = fields.Char(string='Emergency Contact')
    
    
class ProfessionalQualifications(models.Model):
    _name = "prof.qualifications"
    _rec_name = 'emp_id'
    
    qualification_id = fields.Many2one('prof.qualification', required=True, string='Qualification')
    emp_id = fields.Many2one('hr.employee', string='Employee')
    comments = fields.Char(string='Comments')
    

class PromotionDetails(models.Model):
    _name = 'promotion.details'
    _rec_name = 'emp_id'
    
    job_position_id = fields.Many2one('hr.job', string='Job', required=True)
    emp_id = fields.Many2one('hr.employee', string='Employee')
    promotion_date = fields.Date(string='Promotion Date', required=True)
    comments = fields.Char(string='Comments')

    
class PartnerBank(models.Model):
    _inherit = "res.partner.bank"
    
    @api.onchange('bank_id')
    def branch_reset(self):
        self.branch_id=[]
    
    branch_id = fields.Many2one('bank.branch', string='Branch')
    

class BankBranch(models.Model):
    _name = 'bank.branch'
    
    code = fields.Char(string='Branch Code', required=True)
    name = fields.Char(string='Branch', required=True)
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
    
    _sql_constraints = [
        ('bank_branch_uniq', 'unique(name, bank_id)', 'Branch must be unique per Bank!'),
    ]


class MonthlyLateDays(models.Model):
    _name = 'monthly.late.days'

    employee_name = fields.Many2one('hr.employee', string='Employee Name')
    number = fields.Integer(string='No', min="0")
    month = fields.Char(string='Month')
    year = fields.Integer(string='Year')
    late_days_per_month = fields.Integer(string='Late Days Per Month')
    monthly_late_id = fields.Many2one('hr.employee', string='Employee')