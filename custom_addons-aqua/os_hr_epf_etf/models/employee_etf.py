# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class EmployeeETF(models.Model):
    _name = 'employee.etf'
    
    def compute_etf_calculations(self):
        for record in self:
            total = 0
            for line in record.etf_ids:
                total += line.contribution
            record.contribution = total
            record.total_remittance = record.contribution + record.surcharges
            
    title = fields.Char('Title', readonly=True, default='ADVICE OF REMITANCE FORM - R4')
    name = fields.Char('For the month')
    etf_date = fields.Date('Date', default=date.today())
    etf_reg_no = fields.Char('ETF Registration No.', default=lambda self: self.env['ir.config_parameter'].get_param('reg_no'), readonly=True)
    contribution = fields.Float('Contribution', compute='compute_etf_calculations')
    surcharges = fields.Float('Surcharges', required=True)
    total_remittance = fields.Float('Total Remittance', compute='compute_etf_calculations')
    street = fields.Char('Street', required=True)
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', required=True)
    city = fields.Char('City', required=True)
    state_id = fields.Many2one('res.country.state', string="State", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    cheque_no = fields.Char('Cheque No.', required=True)
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
    branch_id = fields.Many2one('bank.branch', string='Branch', required=True)
    etf_ids = fields.One2many('etf.line','etf_id', string='ETF Lines')
    telephone = fields.Char('Telephone', required=True)
    fax = fields.Char('Fax', required=True)
    email = fields.Char('Email')
    state =  fields.Selection([('draft','Draft'),('confirm', 'Confirm'),('cancel','Cancel')],
                               default='draft', string="Status")
    
    @api.multi
    def unlink(self):
        if any(self.filtered(lambda etf: etf.state not in ('draft', 'cancel'))):
            raise UserError(('You cannot delete a Record which is not draft or cancelled!'))
        return super(EmployeeETF, self).unlink()
    
    @api.onchange('state_id')
    def onchange_state(self):
        self.country_id = self.state_id.country_id
        
    @api.onchange('branch_id')
    def onchange_branch(self):
        self.bank_id = self.branch_id.bank_id
    
    @api.one
    def set_to_draft(self):
        self.state = 'draft'
        
    @api.one
    def confirm_etf(self):
        if self.env['ir.config_parameter'].get_param('reg_no'):
            self.etf_reg_no = self.env['ir.config_parameter'].get_param('reg_no')
            self.state = 'confirm'
        else:
            raise ValidationError('Set your Company ETF Reg.No at Payroll configuration Settings')
    
    @api.one
    def cancel_etf(self):
        self.state = 'cancel'
        
    @api.onchange('etf_date')
    def onchange_etf_date(self):
        for record in self:
            str_date = str(record.etf_date)
            date1 = datetime.strptime(str_date, '%Y-%m-%d')
            year = datetime.strftime(date1,'%Y')
            month = datetime.strftime(date1,'%b')
            record.name = month + '-' + year
        
        year_start = datetime.strptime(str(self.etf_date),'%Y-%m-%d').date()
        current_year = int(year_start.strftime('%Y'))
        current_month = int(year_start.strftime('%-m'))
        month_start = year_start + relativedelta(year=current_year, month=current_month, day=1)
        month_end = year_start + relativedelta(year=current_year, month=current_month, day=31)
        domain = [('state','=','done'),('date_from','=',month_start),('date_to','=',month_end)]
        payslips = self.env['hr.payslip'].search(domain)
        employee_dict = {}
        etf_dict = {}
        lines = []
        for payslip in payslips:
            if payslip.employee_id.id in employee_dict:
                for line in payslip.line_ids:
                    if payslip.credit_note == True:
                        if line.code == 'ETF':
                            employee_dict[payslip.employee_id.id]['etf'] -= ((line.total) * -1)
                    else:
                        if line.code == 'ETF':
                            employee_dict[payslip.employee_id.id]['etf'] += ((line.total) * -1)
            else:
                etf_dict = {'etf':0,'nic':'','member':''}
                for line in payslip.line_ids:
                    if line.code == 'ETF':
                        etf_dict['etf'] = ((line.total) * -1)
                etf_dict['member'] = payslip.contract_id.member_no
                etf_dict['nic'] = payslip.employee_id.identification_id
                employee_dict[payslip.employee_id.id] = etf_dict
        for employee in employee_dict:
            res = {
                'employee_id': employee,
                'nic_no':employee_dict[employee]['nic'] or '',
                'member_no': employee_dict[employee]['member'] or '',
                'contribution': employee_dict[employee]['etf'] or 0,
            }
            lines.append((0, 0, res))
        self.update({'etf_ids':lines})
        

class ETFLines(models.Model):   
    _name = 'etf.line'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    nic_no = fields.Char('NIC No.', required=True)
    member_no = fields.Char('Member No.', required=True)
    contribution = fields.Float('Contribution')
    etf_id = fields.Many2one('employee.etf', string="ETF")
    
    @api.depends('employee_id')
    @api.onchange('employee_id')
    def onchange_employee(self):
        self.nic_no = self.employee_id.identification_id
        self.member_no = self.employee_id.contract_id.member_no
        

