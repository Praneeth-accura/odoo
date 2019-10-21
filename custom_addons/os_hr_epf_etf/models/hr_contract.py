# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp

class Contract(models.Model):
    _inherit = 'hr.contract'
    
    member_no = fields.Char('Member No.')
    zone = fields.Char('Zone')
    pf_salary_rule_ids = fields.Many2many('hr.salary.rule', 'pf_rule_rel', string='PF Rules', domain=lambda self: [("id", "in", self.search([]).find_pf_salary_rules())])
    
    @api.multi
    def find_pf_salary_rules(self):
        structure_ids = self.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        rules = []
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for rule in sorted_rules:
            if rule.code not in ['NET','GROSS','PYS','PFS','PF','EPF','ETF']:
                rules.append(rule.id)
        return rules
    
    @api.depends('struct_id','wage')
    @api.onchange('struct_id','wage')
    def onchange_struct_id(self):
        domain = {'pf_salary_rule_ids':[('id','in',self.find_pf_salary_rules())]}
        value = {'pf_salary_rule_ids': False}
        return {'value':value,'domain':domain}
