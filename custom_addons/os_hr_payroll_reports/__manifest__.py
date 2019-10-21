# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Payroll Reports",
    "category": 'Payroll',
    'summary': 'Payroll Reports',
    "description": """
        Payroll Reports. 
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
    "depends": ['os_hr_epf_etf'],
    "data": [
        'data/tax_table_config.xml',
        'data/remuneration.range.csv',
        'views/hr_view.xml',
        'data/salary_rule.xml',
        'views/salary_rule_view.xml',
        'report/salary_payslip_report.xml',
        'report/salary_payslip_template.xml',
        'report/payslip_batch_report.xml',
        'wizard/xlsx_report_wizard_view.xml',
        'wizard/xlsx_report_paye_view.xml',
        'views/hr_contract_view.xml',
        'views/tax_table_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    'images': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}