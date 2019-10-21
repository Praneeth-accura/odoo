# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from datetime import date,datetime
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class EmployeeEPF(models.Model):
    _name = 'employee.epf'
    
    def compute_epf_calculations(self):
        for record in self:
            total = 0
            for line in record.epf_ids:
                total += line.total
            record.contribution = total
            record.total_remittance = record.contribution + record.surcharges
        
    title = fields.Char('Title', readonly=True, default='C FORM EPF Act. No: 15 of 1958')
    name = fields.Char('For the month')
    epf_date = fields.Date('Date', default=date.today())
    epf_reg_no = fields.Char('EPF Registration No.', default=lambda self: self.env['ir.config_parameter'].get_param('reg_no'), readonly=True)
    contribution = fields.Float('Contribution', compute='compute_epf_calculations')
    surcharges = fields.Float('Surcharges', required=True)
    total_remittance = fields.Float('Total Remittance', compute='compute_epf_calculations')
    street = fields.Char('Street', required=True)
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', required=True)
    city = fields.Char('City', required=True)
    state_id = fields.Many2one('res.country.state', string="State", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    cheque_no = fields.Char('Cheque No.', required=True)
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
    branch_id = fields.Many2one('bank.branch', string='Branch', required=True)
    epf_ids = fields.One2many('epf.line','epf_id', string='EPF Lines')
    telephone = fields.Char('Telephone', required=True)
    fax = fields.Char('Fax', required=True)
    email = fields.Char('Email', required=True)
    state =  fields.Selection([('draft','Draft'),('confirm', 'Confirm'),('cancel','Cancel')],
                               default='draft', string="Status")
    
    
    @api.multi
    def unlink(self):
        if any(self.filtered(lambda epf: epf.state not in ('draft', 'cancel'))):
            raise UserError(('You cannot delete a Record which is not draft or cancelled!'))
        return super(EmployeeEPF, self).unlink()
    
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
    def confirm_epf(self):
        if self.env['ir.config_parameter'].get_param('reg_no'):
            self.epf_reg_no = self.env['ir.config_parameter'].get_param('reg_no')
            self.state = 'confirm'
        else:
            raise ValidationError('Set your Company EPF Reg.No at Payroll configuration Settings')
    
    @api.one
    def cancel_epf(self):
        self.state = 'cancel'
        
    @api.onchange('epf_date')
    def onchange_epf_date(self):
        for record in self:
            str_date = str(record.epf_date)
            date1 = datetime.strptime(str_date, '%Y-%m-%d')
            year = datetime.strftime(date1,'%Y')
            month = datetime.strftime(date1,'%b')
            record.name = month + '-' + year
        year_start = datetime.strptime(str(self.epf_date),'%Y-%m-%d').date()
        current_year = int(year_start.strftime('%Y'))
        current_month = int(year_start.strftime('%-m'))
        month_start = year_start + relativedelta(year=current_year, month=current_month, day=1)
        month_end = year_start + relativedelta(year=current_year, month=current_month, day=31)
        domain = [('state','=','done'),('date_from','=',month_start),('date_to','=',month_end)]
        payslips = self.env['hr.payslip'].search(domain)
        employee_dict = {}
        epf_dict = {}
        lines = []
        for payslip in payslips:
            if payslip.employee_id.id in employee_dict:
                for line in payslip.line_ids:
                    if payslip.credit_note == True:
                        if line.code == 'PF':
                            employee_dict[payslip.employee_id.id]['epfe'] -= ((line.total) * -1)
                        if line.code == 'EPF':
                            employee_dict[payslip.employee_id.id]['epfr'] -= ((line.total) * -1)
                        if line.code == 'PFE':
                            employee_dict[payslip.employee_id.id]['epfteight'] -= ((line.total) * -1)
                        if line.code == 'PFS':
                            employee_dict[payslip.employee_id.id]['tot_ear'] -= line.total
                    else:
                        if line.code == 'PF':
                            employee_dict[payslip.employee_id.id]['epfe'] += ((line.total) * -1)
                        if line.code == 'EPF':
                            employee_dict[payslip.employee_id.id]['epfr'] += ((line.total) * -1)
                        if line.code == 'PFE':
                            employee_dict[payslip.employee_id.id]['epfteight'] += ((line.total) * -1)
                        if line.code == 'PFS':
                            employee_dict[payslip.employee_id.id]['tot_ear'] += line.total
                employee_dict[payslip.employee_id.id]['total'] = employee_dict[payslip.employee_id.id]['epfe'] + employee_dict[payslip.employee_id.id]['epfr'] + employee_dict[payslip.employee_id.id]['epfteight']
            else:
                epf_dict = {'epfe':0,'epfr':0,'epfteight':0,'nic':'','member':'','total':0,'tot_ear':0}
                for line in payslip.line_ids:
                    if line.code == 'PF':
                        epf_dict['epfe'] = ((line.total) * -1)
                    if line.code == 'PFE':
                        epf_dict['epfteight'] = ((line.total) * -1)
                    if line.code == 'EPF':
                        epf_dict['epfr'] = ((line.total) * -1)
                    if line.code == 'PFS':
                        epf_dict['tot_ear'] = line.total
                epf_dict['total'] = epf_dict['epfe'] + epf_dict['epfr'] + epf_dict['epfteight']
                epf_dict['member'] = payslip.contract_id.member_no
                epf_dict['nic'] = payslip.employee_id.identification_id
                employee_dict[payslip.employee_id.id] = epf_dict
            
        for employee in employee_dict:
            res = {
                'employee_id': employee,
                'nic_no':employee_dict[employee]['nic'] or '',
                'member_no': employee_dict[employee]['member'] or '',
                'epf_employer': employee_dict[employee]['epfr'] or 0,
                'epf_employee': (employee_dict[employee]['epfe'] + employee_dict[employee]['epfteight']) or 0,
                'total': employee_dict[employee]['total'] or 0,
                'total_earning': employee_dict[employee]['tot_ear'] or 0,
            }
            lines.append((0, 0, res))
        self.update({'epf_ids':lines})
            
class EPFLines(models.Model):   
    _name = 'epf.line'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    nic_no = fields.Char('NIC No.', required=True)
    member_no = fields.Char('Member No.', required=True)
    total = fields.Float('Total')
    epf_employer = fields.Float('Employer', required=True)
    epf_employee = fields.Float('Employee', required=True)
    total_earning = fields.Float('Total Earnings', required=True)
    epf_id = fields.Many2one('employee.epf', string="EPF")
    
