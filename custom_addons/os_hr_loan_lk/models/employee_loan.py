# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, fields, models
from odoo.osv import expression
from datetime import date,datetime
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError

class LoanType(models.Model):
    _name='loan.type'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Loan Code', required=True)
    
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = '[' + str(record.code) + ']' + ' ' + record.name
            result.append((record.id, code))
        return result
    

class LoanDetails(models.Model):
    _name='loan.details'
    
    @api.onchange('employee_id')
    def load_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.job_position_id = self.employee_id.job_id
            self.employee_code = self.employee_id.employee_code
            self.joining_date= self.employee_id.joining_date
            
    @api.model
    def create(self, vals):
        if vals.get('loan_amount') == 0:
            raise ValidationError('Please Enter Valid Loan Amount')
        elif vals.get('no_of_installments') == 0:
            raise ValidationError('Please Enter the No.of Installments')
        elif vals.get('interest') == 'interest' and vals.get('interest_rate') == 0:
            raise ValidationError('Please set the Interest Rate(%)')
        else:
            if 'employee_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['employee_id']).next_by_code('loan.details')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('loan.details')
                
            result = super(LoanDetails, self).create(vals)
            return result
        
    @api.multi
    def total_payment_amount(self):
        for record in self:
            if record.interest == 'interest':
                record.amount_to_paid = record.loan_amount + (record.loan_amount * record.interest_rate / 100)
            else:
                record.amount_to_paid = record.loan_amount
            
    @api.multi
    def installment_amount(self):
        if self.no_of_installments:
            self.amount_per_install = self.amount_to_paid / self.no_of_installments
        else:
            self.amount_per_install = self.amount_to_paid
    
    @api.multi
    def compute_loan_counts(self):
        for record in self:
            total_loans = self.search([('employee_id','=',record.employee_id.id),('state','=','approve')])
            active_loans = self.search([('employee_id','=',record.employee_id.id),('create_date','<',record.create_date),('state','=','approve')])
            for loan in active_loans:
                record.active_loan_amount += loan['balance_amount']
            total = 0
            for loan in total_loans:
                total += loan['balance_amount']
            record.total_loan_amount = round(total)
        record.active_loans = len(active_loans)
        record.total_loans = len(total_loans)
    
    @api.one
    def loan_paid_amount(self):
        total = 0
        for installment in self.installment_ids:
            if installment.status == 'paid':
                total = total + installment.amount
        self.paid_amount = total
        
    @api.multi
    def loan_balance_amount(self):
        for record in self:
            total = 0
            for installment in record.installment_ids:
                if installment.status == 'unpaid':
                    total = total + installment.amount
            record.balance_amount = total
            
    @api.one
    def compute_witness(self):
        self.witness_count = len(self.witness_ids) 
    
    @api.one
    def compute_pending_installments(self):
        installments = self.env['loan.installment'].search([('loan_id','=',self.id),('status','=','unpaid')])
        self.pending_installments = int(len(installments))
           
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department',)
    job_position_id =  fields.Many2one('hr.job', string='Job Position')
    employee_code = fields.Char(string='Employee Code')
    name = fields.Char(string='Name', required=True, readonly=True, default=lambda self: ('New'))
    state = fields.Selection([('draft', 'Draft'),
                              ('awaiting', 'Awaiting Approval'),
                              ('approve', 'Approved'),
                              ('cancelled', 'Cancelled'),
                             ('closed', 'Closed')],default='draft', string='State')
    create_date = fields.Datetime(string='Created Date', readonly=True, default = date.today().strftime('%Y-%m-%d'))
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On', readonly=True)
    closed_on = fields.Date(string='Closed On', readonly=True)
    loan_type_id = fields.Many2one('loan.type', string='Loan Type', required=True)
    loan_amount = fields.Float(string='Loan Amount', required=True, store=True)
    interest = fields.Selection([('interest','With Interest'),('nointerest','Without Interest')], default='nointerest', required=True)
    interest_rate =fields.Float(string='Interest Rate(%)', required=True)
    loan_date = fields.Date(string='Loan Date', required=True, default=lambda self: date.today())
    amount_to_paid = fields.Float(string='Amount to Paid', compute='total_payment_amount')
    no_of_installments = fields.Integer(string='No.of Installments', required=True)
    amount_per_install = fields.Float(string='Amount/Installment', compute='installment_amount')
    loan_payment = fields.Selection([('salary','From Salary'),('witness','From Witness')], string='Loan Payment', default="salary", required=True)
    paid_amount = fields.Float(string='Paid', compute='loan_paid_amount')
    balance_amount =fields.Float(string='Balance', compute='loan_balance_amount')
    comments = fields.Text(string='Comments')
    witness_ids = fields.One2many('loan.witness','emp_witness', string='Witness')
    active_loans = fields.Integer(string='Old Loans', compute='compute_loan_counts')
    total_loans = fields.Integer(string='Total Loans', compute='compute_loan_counts')
    active_loan_amount = fields.Float(string='Old Bal', compute='compute_loan_counts')
    total_loan_amount = fields.Float(string='Total', compute='compute_loan_counts')
    current_date = fields.Date('Date current action', default = date.today().strftime('%Y-%m-%d'))
    installment_ids = fields.One2many('loan.installment','loan_id', string='Installments', ondelete='cascade')
    contracts_count = fields.Integer(related='employee_id.contracts_count', string='Contracts')
    witness_count = fields.Integer(string='Witness', compute='compute_witness')
    installment_start_date =  fields.Date('Installment Starts', required=True, default=lambda self: date.today()+relativedelta.relativedelta(months=1, day=1))
    pending_installments = fields.Integer(string='Pending Installments', compute='compute_pending_installments')
    
    @api.multi
    def unlink(self):
        if any(self.filtered(lambda loan: loan.state not in ('draft', 'cancelled'))):
            raise UserError(('You cannot delete a Loan which is not draft or cancelled!'))
        return super(LoanDetails, self).unlink()
    
    @api.multi
    def action_view_witness(self):
        witnesses = []
        for witness in self.witness_ids:
            witnesses.append(witness.employee_id.id)
        action = self.env.ref('os_hr_loan_lk.act_employee_loan_5_hr_employee').read()[0]
        if len(witnesses):
            action['domain'] = [('id', 'in', witnesses)]
#         elif len(witnesses) == 1:
#             action['views'] = [(self.env.ref('hr.view_employee_form').id, 'form')]
#             action['res_id'] = witnesses[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    @api.multi
    def action_view_loans(self):
        loans = self.search([('employee_id','=',self.employee_id.id),('create_date','<',self.create_date)])
        action = self.env.ref('os_hr_loan_lk.open_employee_loan_details').read()[0]
        if len(loans) > 1:
            action['domain'] = [('id', 'in', loans.ids)]
        elif len(loans) == 1:
            action['views'] = [(self.env.ref('os_hr_loan_lk.employee_loan_details_form_view').id, 'form')]
            action['res_id'] = loans.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    @api.depends('loan_date')
    @api.onchange('loan_date')
    def set_installment_start_date(self):
        if self.loan_date:
            dates = datetime.strptime(self.loan_date, "%Y-%m-%d").date()
            self.installment_start_date = dates + relativedelta.relativedelta(months=1, day=1)
        
    @api.depends('state')
    @api.multi
    def submit_loan(self):
        if self.loan_payment == 'witness':
            if self.witness_ids:
                self.state='awaiting'
            else:
                raise ValidationError('Please Select Atleast One Witness')
        else:
            self.state='awaiting'
        
    @api.depends('state')
    @api.multi
    def reset_to_draft(self):
        self.state='draft'
        
        
    @api.depends('state')
    @api.multi
    def cancel_loan(self):
        self.state='cancelled'
    
    @api.depends('state')
    @api.multi
    def approve_loan(self):
        status = 0
        for rule in self.employee_id.contract_id.struct_id.rule_ids:
            if rule.code == 'LR':
                status = 1
        if status == 1:
            if self.installment_ids:
                for record in self.installment_ids:
                    record.unlink()
                    self.update({'installment_ids':False})
            installments = []
            if self.no_of_installments >= 1:
                dates = datetime.strptime(self.installment_start_date, "%Y-%m-%d").date()
                for i in range(self.no_of_installments):
                    installments.append({'ref_no':self.name+'/'+str(i+1),'installment_date':dates,'amount':self.amount_per_install})
                    dates = dates + relativedelta.relativedelta(months=1)
            self.update({'installment_ids':installments})        
            self.state='approve'
            self.approved_on = date.today()
            self.approved_by_id = self.env.user.id
        else:
            raise ValidationError("Please Upgrade Employee's Salary Structure")
        
    @api.depends('state')
    @api.multi
    def close_loan(self):
        self.state='closed'
        self.closed_on = date.today()
        
    
class LoanWitness(models.Model):
    _name = 'loan.witness'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    emp_witness = fields.Many2one('loan.details', string='Witness')
    repay = fields.Boolean('Repayment', default=False)
    
    
class LoanInstallment(models.Model):
    _name = 'loan.installment'
    
    ref_no = fields.Char('Reference No.', required=True, readonly=True)
    installment_date = fields.Date(string='Installment Date', required=True, readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    paid_amount = fields.Float(string='Paid Amount', readonly=True)
    paid_date = fields.Date(string='Paid Date', readonly=True)
    status = fields.Selection([('paid', 'Paid'),('unpaid', 'Unpaid')],default='unpaid', readonly=True)
    loan_id = fields.Many2one('loan.details', string='Loan No', ondelete='cascade')
    
    
class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    loan_repayment = fields.Boolean(string='Loan Repayment', default=False)
    

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    installment_ids = fields.Many2many('loan.installment', string="Installments", domain=[('status','=','unpaid')])
    
    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee(self):
    #     domain = [('loan_id.employee_id','=',self.employee_id.id),
    #               ('installment_date','>=',self.date_from),
    #               ('installment_date','<=',self.date_to),
    #               ('loan_id.state','=','approve'),
    #               ('loan_id.state','!=','closed'),
    #               ('status','=','unpaid'),
    #               ('loan_id.loan_payment','=','salary')]
        
    #     installments = self.env['loan.installment'].search(domain)
    #     self.installment_ids = installments.ids
    #     return super(HrPayslip, self).onchange_employee()
    
    @api.multi
    def compute_sheet(self):
        for record in self:
            total = 0
            for installment in record.installment_ids:
                total += installment.amount
            for inputs in record.input_line_ids:
                if inputs.code == 'LR':
                    inputs.amount = total
        return super(HrPayslip,self).compute_sheet()

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for installment in self.installment_ids:
            installment.paid_amount = installment.amount
            installment.paid_date = date.today()
            installment.status = 'paid'
            paid = 0
            total = installment.loan_id.no_of_installments
            for inst in installment.loan_id.installment_ids:
                if inst.status == 'paid':
                    paid += 1
            if paid == total:
                installment.loan_id.closed_on = date.today()
                installment.loan_id.state = 'closed'
        return res
    
    