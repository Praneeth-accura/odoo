# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Employee EPF & ETF",
    "category": 'Human Resources',
    'summary': 'Employee EPF & ETF',
    "description": """
        Employee's Provident Fund and Trust Fund. 
    """,
    "sequence": 1,
    "author": "Technaureus Info Solutions",
    "website": "http://www.technaureus.com/",
    "version": '1.0',
    "depends": ['os_hr_lk','os_hr_contract_lk','hr_payroll','report_xlsx'],
    "data": [
        'security/ir.model.access.csv',
        'views/epf_view.xml',
        'views/res_config_view.xml',
        'views/etf_view.xml',
        'views/hr_contract_view.xml',
        'report/epf_etf_reports.xml',
        'wizard/xlsx_report_wizard_view.xml',
        'views/hr_job_view.xml',
    ],
    'qweb': [],
    'images': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}