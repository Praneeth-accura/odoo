# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError

class EmployeeAdvanceSalary(models.Model):
    _name = 'advance.salary.request'
    _rec_name = 'reference_no'

    @api.model
    def create(self, vals):
        if vals.get('advance_amount') == 0:
            raise ValidationError('Please Enter Valid Amount')
        else:
            if 'company_id' in vals:
                vals['reference_no'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('advance.salary.request')
            else:
                vals['reference_no'] = self.env['ir.sequence'].next_by_code('advance.salary.request')

            result = super(EmployeeAdvanceSalary, self).create(vals)
            return result

    reference_no = fields.Char(string="Reference No", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    emp_code = fields.Char(string="Employee Code")
    #created_date = fields.Date(string="Date", required=True, readonly=True, default = date.today().strftime('%Y-%m-%d') )
    #created_date = fields.Date(string="Date", required=True, readonly=True, default=datetime.now().strftime('%Y-%m-%d') )
    created_date = fields.Date(string="Date", required=True, readonly=False)
    advance_amount = fields.Float(String="Advance Amount", required=True)
    previous_advances_ids = fields.One2many('previous.advances','previous_advance_id', string="Previous Advances", ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                             ('reject', 'Rejected')],default='draft', string='State')

    deduct_from_salary = fields.Boolean(string="Auto Deduct From Salary", default=True, readonly=True)
    repaid = fields.Boolean(string="Repaid", default=False, readonly=True)
    comments = fields.Text(string="Comments")
    id = fields.Integer('ID', readonly=True)
    contracts_count = fields.Integer(related='employee_id.contracts_count', string='Contracts')


    @api.multi
    def unlink(self):
        if any(self.filtered(lambda advance_salary: advance_salary.state not in ('draft', 'cancel'))):
            raise UserError(('You cannot delete a Record which is not draft or cancelled!'))
        return super(EmployeeAdvanceSalary, self).unlink()

    @api.depends('state')
    def confirm_salary_request(self):
        self.state = 'confirm'
        self.previous_advances_ids = False
        context = []
        previous = self.search([('employee_id','=',self.employee_id.id),('id','!=',self.id),('repaid','=',False),('state','=','approve')])
        for record in previous:
                context.append({'ref_no':record.reference_no,'create_date':record.created_date,
                          'amount':record.advance_amount,'repaid':record.repaid,'state':record.state})
        self.update({'previous_advances_ids':context})

    @api.depends('state')
    def approve_salary_request(self):
        status = 0
        if self.advance_amount <= self.employee_id.contract_id.advance_salary_limit:
            for rule in self.employee_id.contract_id.struct_id.rule_ids:
                if rule.code == 'ASD':
                    status = 1
            if status == 1:
                self.state = 'approve'
            else:
                raise ValidationError("Please Upgrade Employee's Salary Structure")
        else:
            raise ValidationError('Advance Amount is Exceeding the limit')


    @api.depends('state')
    def reset_salary_request(self):
        self.previous_advances_ids = False
        self.state = 'draft'

    @api.depends('state')
    def cancel_salary_request(self):
        self.state = 'cancel'

    @api.depends('state')
    def reject_salary_request(self):
        self.state = 'reject'

    @api.onchange('employee_id')
    def load_employee_details(self):
        self.previous_advances_ids = []
        if self.employee_id:
            self.emp_code = self.employee_id.employee_code

class PreviousAdvances(models.Model):
    _name = 'previous.advances'

    ref_no = fields.Char(string="Reference No", required=True)
    create_date = fields.Date(string="Date", required=True)
    amount = fields.Float(string="Amount", required=True)
    state = fields.Char(string="State", required=True)
    repaid = fields.Boolean(string="Repaid")
    previous_advance_id = fields.Many2one('advance.salary.request', string="Previous Advances")


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    advance_salary = fields.Boolean(string='Advance Salary Request', default=False)

class Contract(models.Model):
    _inherit = 'hr.contract'

    advance_salary_limit = fields.Float(string="Advance Salary Limit", required=True, compute="salary_limit_compute")

    @api.one
    def salary_limit_compute(self):
        if self.advance_salary_limit == 0:
            self.advance_salary_limit = self.wage
        else:
            return


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    advance_salary_ids = fields.Many2many('advance.salary.request', string="Advance Salary Requests", domain=[('repaid','=',False)], compute='onchange_employee', store=True)

    @api.one
    @api.depends('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        for line in self:
            salary_requests = self.env['advance.salary.request'].search([('employee_id','=',line.employee_id.id),
                                                                         ('created_date','>=',line.date_from),
                                                                         ('created_date','<=',line.date_to),
                                                                         ('state','=','approve'),
                                                                         ('repaid','=',False),
                                                                         ('deduct_from_salary','=',True)])
            line.advance_salary_ids = salary_requests.ids
        return super(HrPayslip, self).onchange_employee()

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                }
                res += [input_data]

            salary_requests = self.env['advance.salary.request'].search([('employee_id', '=', contract.employee_id.id),
                                                                         ('created_date', '>=', date_from),
                                                                         ('created_date', '<=', date_to),
                                                                         ('state', '=', 'approve'),
                                                                         ('repaid', '=', False),
                                                                         ('deduct_from_salary', '=', True)])

            total = 0
            for line in salary_requests:
                total += line.advance_amount

            for rule in contract.struct_id.rule_ids:
                if rule.code == 'ASD':
                    input_data = {
                        'name': 'Advance Salary Deduction',
                        'code': 'ASD',
                        'amount': total,
                        'contract_id': contract.id
                    }

                    res += [input_data]

            domain = [('loan_id.employee_id', '=', contract.employee_id.id),
                      ('installment_date', '>=', date_from),
                      ('installment_date', '<=', date_to),
                      ('loan_id.state', '=', 'approve'),
                      ('loan_id.state', '!=', 'closed'),
                      ('status', '=', 'unpaid'),
                      ('loan_id.loan_payment', '=', 'salary')]

            installments = self.env['loan.installment'].search(domain)
            total = 0
            for line in installments:
                total += line.amount

            for rule in contract.struct_id.rule_ids:
                if rule.code == 'LR':
                    input_data = {
                        'name': 'Loan Repayment',
                        'code': 'LR',
                        'amount': total,
                        'contract_id': contract.id
                    }

                    res += [input_data]

        return res

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for salary_requests in self.advance_salary_ids:
            salary_requests.repaid = True
        return res
