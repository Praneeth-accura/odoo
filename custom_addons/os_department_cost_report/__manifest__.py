# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Department Cost Report",
    "category": 'Payroll',
    'summary': 'Department wise Cost Report',
    "description": """
        Department wise Cost Report. 
    """,
    "sequence": 1,
    "author": "Technaureus Info Solutions",
    "website": "http://www.technaureus.com/",
    "version": '1.0',
    'external_dependencies': {
        'python': [
            'docx',
        ],
    },
    "depends": ['os_hr_payroll_reports'],
    "data": [
        'wizard/xlsx_report_wizard_view.xml',
    ],
    'qweb': [],
    'images': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}