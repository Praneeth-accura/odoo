# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

{
    'name': 'Srilankan HR',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 1,
    'author':'Technaureus Info Solutions',
    'summary': 'Employee Management',
    'website': 'http://www.technaureus.com/',
    'description': """
Employees, Contracts, Departmetnts...""",
    'depends': ['hr_recruitment'],
    'data': [
        'views/hr_view.xml',
        'views/religion_view.xml',
        'views/prof_qualification_view.xml',
        'views/job_view.xml',
        'views/banks_view.xml',
        'data/emp_religion_data.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'wizard/employee_master_wizard_view.xml',
        'report/employee_master_template.xml',
        'report/employee_master.xml',
        'report/leave_details_template.xml',
        'report/leave_details.xml',
        'views/res_config_view.xml',
        
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
