# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Payslip Modify",
    "category": 'Payroll',
    'summary': 'Modify the confirmed payslips',
    "description": """
        Modify the confirmed payslips. 
    """,
    "sequence": 1,
    "author": "Technaureus Info Solutions",
    "website": "http://www.technaureus.com/",
    "version": '1.0',
    "depends": ['os_hr_payroll_reports'],
    "data": [
        'views/res_config_view.xml',
        'wizard/payslip_modify_wizard_view.xml',
        'views/hr_payslip_view.xml',
        
    ],
    'qweb': [],
    'images': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}