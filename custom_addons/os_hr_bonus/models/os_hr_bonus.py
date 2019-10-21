# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from datetime import date,datetime
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from lxml import etree
from dateutil.relativedelta import relativedelta

class EmployeeBonus(models.Model):
    _name = 'bonus.payslip'
    
    @api.depends('gross_for_tax','tax_rate')
    def _compute_paye(self):
        for bonus in self:
            bonus.paye = bonus.gross_for_tax * (bonus.tax_rate/100) * (-1)
        
    @api.depends('gross_for_tax')
    def _compute_stamp_duty(self):
        for bonus in self:
            if bonus.gross_for_tax <= 25000:
                bonus.stamp_duty = 0
            else:
                bonus.stamp_duty = -25
            
    @api.depends('stamp_duty','paye','other_deduction')
    def _compute_total_deduction(self):
        for bonus in self:
            bonus.total_deduction = bonus.paye_payable + bonus.stamp_duty + ( -(bonus.other_deduction))
    
    @api.depends('gross_bonus','total_deduction')
    def _compute_net_bonus(self):
        for bonus in self:
            bonus.net_bonus = bonus.gross_bonus - (-(bonus.total_deduction))
            
    @api.depends('date_from','date_to','employee_id')
    def _compute_average(self):
        for bonus in self:
            if bonus.batch_id:
                bonus.date_from = bonus.batch_id.period_from
                bonus.date_to = bonus.batch_id.period_to
        for bonus in self:
            domain = [('state','=','done'),('date_from','>=',bonus.date_from),('date_to','<=',bonus.date_to),('employee_id','=',bonus.employee_id.id)]
            payslips = bonus.env['hr.payslip'].search(domain)
            gross_total = 0
            for payslip in payslips:
                for line in payslip.line_ids:
                    if line.code == 'PYS':
                        if payslip.credit_note == True:
                            gross_total -= line.total
                        else:
                            gross_total += line.total
            if len(payslips) > 0:
                bonus.average_salary = gross_total / len(payslips)
    
    @api.multi
    @api.depends('tax_table','average_salary')
    def _compute_gross_taxtable(self):
        for record in self:
            for table in record.tax_table:
                for income in table.monthly_income_ids:
                    if record.average_salary >= income.income_from and record.average_salary <= income.income_to:
                        record.tax_rate = income.rate
    
    @api.depends('gross_bonus','previous_bonus')
    def compute_total_bonus(self):
        for record in self:
            record.total_bonus = record.gross_bonus + record.previous_bonus
            
    @api.depends('total_bonus')
    def _compute_gross(self):
        for record in self:
            record.gross_for_tax = record.total_bonus
            
    @api.depends('paye','paye_deducted')
    def compute_paye_payable(self):
        for record in self: 
            if record.paye_deducted != 0:
                paye = record.paye * -1
                paye_ded = record.paye_deducted * -1
                record.paye_payable = (paye - paye_ded)
                if record.paye_payable > 0:
                    record.paye_payable = record.paye_payable * -1
            else:
                record.paye_payable = (record.paye)
                        
    name = fields.Char(string="Name for Bonus Slip")
    month_year = fields.Char(string="Month and Year")
    employee_id = fields.Many2one('hr.employee', 
        string="Employee", required=True)
    epf_no = fields.Char(string="EPF Number", required=True, store=True)
    date_from = fields.Date(string="Date From", default=date.today(), required=True)
    date_to = fields.Date(string="Date To", default=date.today(), required=True)
    gross_bonus = fields.Float(string="Current Bonus", required=True)
    tax_table = fields.Many2one('revenue.taxtable',string="Tax Table")
    tax_rate = fields.Float(string="Tax Rate", compute='_compute_gross_taxtable')
    gross_for_tax = fields.Float(string="Gross for Tax", compute='_compute_gross')
    average_salary = fields.Float(compute='_compute_average', string="Average Salary")
    paye = fields.Float(compute='_compute_paye', string="PAYE Tax")
    other_deduction = fields.Float(string="Other Deduction")
    stamp_duty = fields.Float(compute='_compute_stamp_duty', string="Stamp Duty")
    total_deduction = fields.Float(compute='_compute_total_deduction', string="Total Deduction")
    net_bonus = fields.Float(compute='_compute_net_bonus', string="Net Bonus")
    batch_id = fields.Many2one('bonus.batch', string="Batch ID")
    bonus_salary_ratio = fields.Float("Bonus Average Salary Ratio")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('cancel','Cancel')],
                             default='draft', String='States')
    previous_bonus = fields.Float(string='Previous Bonus')
    total_bonus = fields.Float(compute="compute_total_bonus", string='Total Bonus')
    paye_deducted = fields.Float('PAYE Deducted')
    paye_payable = fields.Float('PAYE Payable', compute="compute_paye_payable")
    
    
    @api.multi
    def unlink(self):
        if any(self.filtered(lambda bonus: bonus.state not in ('draft', 'cancel'))):
            raise UserError(('You cannot delete a Record which is not draft or cancelled!'))
        return super(EmployeeBonus, self).unlink()
    
    @api.one
    def confirm_bonus(self):
        self.state = 'confirm'
    
    @api.one
    def cancel_bonus(self):
        self.state = 'cancel'
        
    @api.one
    def set_to_draft(self):
        self.state = 'draft'
        
    @api.onchange('date_from')
    @api.depends('date_from')
    def onchange_date(self):
        for bonus in self:
            if bonus.date_from:
                current_date1 = datetime.strptime(str(bonus.date_from),'%Y-%m-%d').date()
                current_year = current_date1.strftime('%Y')
                current_month = current_date1.strftime('%-m')
                month = int(current_month)
                year = int(current_year)
                if month == 1 or month == 2 or month == 3:
                    bonus.date_from = current_date1 + relativedelta(year=year-1,month=4,day=1)
                    bonus.date_to = current_date1 + relativedelta(year=year,month=3,day=31)
                else:
                    bonus.date_from = current_date1 + relativedelta(year=year,month=4,day=1)
                    bonus.date_to = current_date1 + relativedelta(year=year+1,month=3,day=31)
                
                date_from = datetime.strptime(bonus.date_from,"%Y-%m-%d")
                date_to = datetime.strptime(bonus.date_to,"%Y-%m-%d")
                year1 =  int(date_from.strftime("%Y"))
                year2 =  int(date_to.strftime("%Y"))
                bonus.name = "Financial Year "+str(year1)+" - "+str(year2)
    
    def get_current_date(self):
        current_date = datetime.now().date()
        current_date = current_date.strftime("%d %b %Y")
        return current_date
    
    @api.multi
    @api.onchange('employee_id')
    @api.depends('employee_id')
    def _onchange_employee(self):
        self._compute_average()
        if self.employee_id and self.employee_id.contract_id:
            for bonus in self:
                bonus.epf_no = bonus.employee_id.contract_id.member_no or ''
                bonus.gross_bonus = 0
                previous = bonus.find_previous_bonus(bonus.date_from,bonus.date_to)
                bonus.previous_bonus = previous[0]
                bonus.paye_deducted = previous[1]
    
    def find_previous_bonus(self, date_from, date_to):
        bonus_slips = {}
        for bonus in self:
            domain = [('employee_id','=',bonus.employee_id.id),
                      ('state','=','confirm'),
                      ('date_from','=',date_from),
                      ('date_to','=',date_to)]
            bonus_slips = bonus.search(domain)
        previous_bonus = 0
        paye_deducted = 0
        for bonus in bonus_slips:
            previous_bonus += bonus.gross_bonus
            paye_deducted += bonus.paye
        return [previous_bonus,paye_deducted]     
       
    @api.onchange('average_salary','gross_bonus')
    def _onchange_average_salary(self):
        if self.batch_id:
            self.date_from = self.batch_id.period_from
            self.date_to = self.batch_id.period_to
        self._compute_average()
        self.tax_table = False
        ratio = ""
        if self.average_salary > 0:
            self.bonus_salary_ratio = round(self.total_bonus/self.average_salary,2)
            if self.bonus_salary_ratio <= 0.24:
                ratio = "M - 0"
            elif self.bonus_salary_ratio >= 0.25 and self.bonus_salary_ratio <= 0.74:
                ratio = "M - 0.5"
            elif self.bonus_salary_ratio >= 0.75 and self.bonus_salary_ratio <= 1.24:
                ratio = "M - 1"
            elif self.bonus_salary_ratio >= 1.25 and self.bonus_salary_ratio <= 1.74:
                ratio = "M - 1.5"
            elif self.bonus_salary_ratio >= 1.75 and self.bonus_salary_ratio <= 2.24:
                ratio = "M - 2"
            elif self.bonus_salary_ratio >= 2.25 and self.bonus_salary_ratio <= 2.74:
                ratio = "M - 2.5"
            elif self.bonus_salary_ratio >= 2.75 and self.bonus_salary_ratio <= 3.24:
                ratio = "M - 3"
            elif self.bonus_salary_ratio >= 3.25 and self.bonus_salary_ratio <= 3.74:
                ratio = "M - 3.5"
            elif self.bonus_salary_ratio >= 3.75 and self.bonus_salary_ratio <= 4.24:
                ratio = "M - 4"
            elif self.bonus_salary_ratio >= 4.25 and self.bonus_salary_ratio <= 4.74:
                ratio = "M - 4.5"
        
        domain = [('name','=',ratio)]
        tax_table = self.env['revenue.taxtable'].search(domain)
        if len(tax_table) > 0:
            self.tax_table = tax_table[0]
           

class EmployeeBonusBatch(models.Model):
    _name = 'bonus.batch'
    
    name = fields.Char(string="Name", required=True)
    period_from = fields.Date(string="Period From",
                              default=lambda self: self._default_period_from(), required=True)
    period_to = fields.Date(string="Period To",
                            default=lambda self: self._default_period_to(), required=True)
    slip_ids = fields.One2many('bonus.payslip', 'batch_id', string="Bonus")
    
        
    def _default_period_from(self):
        current_date = datetime.now().date()
        year =  int(current_date.strftime("%Y"))
        month = int(current_date.strftime("%m"))
        if month < 4:
            year -= 1
        date_str = str(year)+"0401"
        return datetime.strptime(date_str,"%Y%m%d")
    
    def _default_period_to(self):
        current_date = datetime.now().date()
        year =  int(current_date.strftime("%Y"))
        month = int(current_date.strftime("%m"))
        if month > 4:
            year += 1
        date_str = str(year)+"0331"
        return datetime.strptime(date_str,"%Y%m%d")
    
class EmployeeBonusWizard(models.TransientModel):
    _name = 'bonus.employee.wizard'
    
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeBonusWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        employees = []
        active_id = self.env.context.get('active_id')
        bonus_batch = self.env['bonus.batch'].search([('id','=', active_id)])
        for record in bonus_batch:
            for line in record.slip_ids:
                employees.append(line.employee_id.id)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='employee_ids']"):
            node.set('domain', "[('id', 'not in', %s)]"%employees)
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
    
    @api.multi
    def load_bonus_details(self):
        lines = []
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        bonus = self.env['bonus.batch'].search([('id','=', active_id)])
        date_from = bonus.period_from
        date_from = datetime.strptime(date_from,"%Y-%m-%d")
        year =  int(date_from.strftime("%Y"))
        name = "Financial Year "+str(year)+" - "+str(year+1)
        if not data['employee_ids']:
            raise UserError("You must select employee(s) to proceed")
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            res = {
                'name': name,
                'employee_id': employee.id,
                'epf_no': employee.contract_id and employee.contract_id.member_no or '',
                'date_from':bonus.period_from,
                'date_to':bonus.period_to,
                'gross_bonus': 0,
            }
            lines.append((0, 0, res))
        bonus.write({'slip_ids':lines})
        return {'type': 'ir.actions.act_window_close'}
 
    
