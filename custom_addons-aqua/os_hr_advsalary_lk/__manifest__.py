# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).


{
    'name': 'Advance Salary Request',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 1,
    'author':'Technaureus Info Solutions',
    'summary': 'Employee Advance Salary Request Management',
    'website': 'http://www.technaureus.com/',
    'description': """
Employee Advance Salary Request Management ...""",
    'depends': ['hr_payroll','os_hr_contract_lk','os_hr_lk'],
    'data': [
        'security/module_data.xml',
        'views/employee_advance_salary_view.xml',
        'views/contract_inherit_view.xml',
        'views/hr_payslip_view.xml',
        'data/ir_sequence_data.xml',
        'data/salary_rule.xml',
        'security/ir.model.access.csv',
        
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
