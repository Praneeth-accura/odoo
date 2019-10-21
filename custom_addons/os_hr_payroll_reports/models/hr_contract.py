# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from datetime import date,datetime
from dateutil.relativedelta import relativedelta


class Contract(models.Model):
    _inherit = 'hr.contract'
    
    paye_salary_rule_ids = fields.Many2many('hr.salary.rule', 'paye_rule_rel', string='PAYE Rules',
                                             domain=lambda self: [("id", "in", self.search([]).find_paye_salary_rules())])
    allowance_rule_ids = fields.One2many('allowance.rules','contract_id', string="Allowances")
    deduction_rule_ids = fields.One2many('deduction.rules','contract_id', string="Deductions")
    opening_ytd_ids = fields.One2many('opening.ytd', 'contract_id', string='Opening YTD')
    
    @api.multi
    def find_paye_salary_rules(self):
        structure_ids = self.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        rules = []
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for rule in sorted_rules:
            if rule.code not in ['NET','GROSS','PYS','PFS','PAYE']:
                rules.append(rule.id)
        return rules
    
    @api.multi
    def find_allowance_rules(self):
        structure_ids = self.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        rules = []
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for rule in sorted_rules:
            if rule.category_id.code == 'ALW':
                rules.append(rule.id)
        return rules
    
    @api.multi
    def find_deduction_rules(self):
        structure_ids = self.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        rules = []
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for rule in sorted_rules:
            if rule.category_id.code == 'DED':
                rules.append(rule.id)
        return rules
    
    @api.depends('struct_id','wage')
    @api.onchange('struct_id','wage')
    def onchange_struct_id(self):
        self.find_pf_salary_rules()
        self.find_paye_salary_rules()
        self.find_allowance_rules()
        self.find_deduction_rules()
        domain = {'paye_salary_rule_ids':[('id','in',self.find_paye_salary_rules())],
                  'pf_salary_rule_ids':[('id','in',self.find_pf_salary_rules())],
                  'allowance_rule_ids':[('id','in',self.find_allowance_rules())],
                  'deduction_rule_ids':[('id','in',self.find_deduction_rules())]}
        value = {'paye_salary_rule_ids': False,'pf_salary_rule_ids': False,
                 'allowance_rule_ids': False,'deduction_rule_ids': False}
        return {'value':value,'domain':domain}
    

class OpeningYTD(models.Model):
    _name = 'opening.ytd'
    
    from_date = fields.Date('From', default=date.today())
    to_date = fields.Date('To', default=date.today())
    ytd_gross = fields.Float('YTD Gross')
    ytd_net = fields.Float('YTD Net')
    ytd_paye_tax = fields.Float('YTD PAYE')
    ytd_emp_epf = fields.Float('YTD Employee PF')
    ytd_comp_epf = fields.Float('YTD Employer PF')
    ytd_etf = fields.Float('YTD ETF')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    
    @api.model
    def create(self, vals):
        if 'from_date' in vals and 'to_date' in vals:
            from_date = vals['from_date']
            to_date = vals['to_date']
            domain = [('from_date','=',from_date),
                      ('to_date','=',to_date)]
            dups = self.env['opening.ytd'].search(domain)
            if dups:
                raise UserError('Duplicate Record')
            else:
                return super(OpeningYTD, self).create(vals)
        else:
            return super(OpeningYTD, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if 'from_date' in vals and 'to_date' in vals:
            from_date = vals['from_date']
            to_date = vals['to_date']
            domain = [('from_date','=',from_date),
                      ('to_date','=',to_date)]
            dups = self.env['opening.ytd'].search(domain)
            if dups:
                raise UserError('Duplicate Record')
            else:
                return super(OpeningYTD, self).write(vals)
        else:
            return super(OpeningYTD, self).write(vals)
        
        
    @api.onchange('from_date')
    def onchange_year_start(self):
        current_date1 = datetime.strptime(str(self.from_date),'%Y-%m-%d').date()
        current_year = current_date1.strftime('%Y')
        current_month = current_date1.strftime('%-m')
        month = int(current_month)
        year = int(current_year)
        if month == 1 or month == 2 or month == 3:
            self.from_date = current_date1 + relativedelta(year=year-1,month=4,day=1)
            self.to_date = current_date1 + relativedelta(year=year,month=3,day=31)
        else:
            self.from_date = current_date1 + relativedelta(year=year,month=4,day=1)
            self.to_date = current_date1 + relativedelta(year=year+1,month=3,day=31)
            
    
class AllowanceRules(models.Model):
    _name = 'allowance.rules'
    
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule',
                                     domain=[('category_id.code', '=', 'ALW')], required=True)
    code = fields.Char('Code')
    amount = fields.Float('Amount')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    
    @api.depends('salary_rule_id')
    @api.onchange('salary_rule_id')
    def onchange_salary_rule_id(self):
        for record in self:
            record.code = record.salary_rule_id.code
    

class DeductionRules(models.Model):
    _name = 'deduction.rules'
    
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule',
                                     domain=[('category_id.code', '=', 'DED')], required=True)
    code = fields.Char('Code')
    amount = fields.Float('Amount')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    
    
    @api.depends('salary_rule_id')
    @api.onchange('salary_rule_id')
    def onchange_salary_rule_id(self):
        for record in self:
            record.code = record.salary_rule_id.code
