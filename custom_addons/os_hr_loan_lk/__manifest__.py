# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

{
    'name': 'Employee Loans',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 4,
    'author':'Technaureus Info Solutions',
    'summary': 'Employee Loan Management',
    'website': 'http://www.technaureus.com/',
    'description': """
Employee Loan Management """,
    'depends': ['hr_payroll','os_hr_lk'],
    'data': [
        'security/module_data.xml',
        'views/loan_view.xml',
        'views/hr_payslip_view.xml',
        'wizard/loan_payment_view.xml',
        'data/ir_sequence_data.xml',
        'data/salary_rule.xml',
        'report/loan_details.xml',
        'report/loan_details_template.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
