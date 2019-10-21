# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
import string

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'   
    
    amount_python_compute = fields.Text(string='Python Code',
        default='''
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
                    # worked_days: object containing the computed worked days.
                    # inputs: object containing the computed inputs.
                    
                    #contract.paye_salary_rule_ids , sum of all rules containing that field
                    #contract.pf_salary_rule_ids , sum of all rules containing that field

                    # Note: returned value have to be set in the variable 'result'

                    result = contract.wage * 0.10''')
    
    @api.model
    def create(self, vals):
        if 'slip_id' not in vals:
            if 'code' in vals:
                code = vals['code']
                rules = self.search([])
                for rule in rules:
                    if rule.code == code:
                        raise UserError(_('Code must be unique per Salary rule'))
        return super(HrSalaryRule, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'slip_id' not in vals:
            if 'code' in vals:
                code = vals['code']
                rules = self.search([])
                for rule in rules:
                    if rule.code == code:
                        raise UserError(_('Code must be unique per Salary rule'))
        return super(HrSalaryRule, self).write(vals)

    
    @api.multi
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(safe_eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).') % (self.name, self.code))
        else:
            try:
                if 'contract.paye_salary_rule_ids' in self.amount_python_compute:
                    python_compute = self.define_python_compute(localdict['contract'].paye_salary_rule_ids)
                    self.amount_python_compute = string.replace(self.amount_python_compute, 'contract.paye_salary_rule_ids', python_compute)
                elif 'contract.pf_salary_rule_ids' in self.amount_python_compute:
                    python_compute = self.define_python_compute(localdict['contract'].pf_salary_rule_ids)
                    self.amount_python_compute = string.replace(self.amount_python_compute, 'contract.pf_salary_rule_ids', python_compute)
                else:
                    self.amount_python_compute = self.amount_python_compute
                safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            except:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))
            
  
    @api.multi
    def define_python_compute(self, rules_ids):
        python_compute = '('
        flag = 0
        for rule in rules_ids:
            flag += 1
            if flag == 1:
                python_compute += rule.code
            else:
                python_compute += ' + '
                python_compute += rule.code
        python_compute += ')'
        return python_compute
    
    
class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    
    _sql_constraints = [
        ('code_uniq', 'unique(code, slip_id)', 'Code must be unique per Payslip line'),
    ]
    

class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    sequence = fields.Integer('Sequence')
    
    _sql_constraints = [
        ('sequence_uniq', 'unique(sequence)', 'Sequence must be unique per Category'),
    ]
        
    