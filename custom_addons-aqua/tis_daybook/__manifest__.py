# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Day book(Sales,Purchase,Cash,Bank-PDF & Excel/XLS)',
    'version': '1.0',
    'sequence': 1,
    'category': 'Accounting & Finance',
    'summary': 'Daybook',
    'description': """
    This module is for activating Daybook
""",
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'price': 75,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['account_invoicing','board'],
    'data': [
        'views/account_journal_dashboard_view.xml',
        'wizard/daybook_view.xml',
        'report/report_daybook.xml',
        'report/report_daybook_templates.xml'
    ],
    'images': ['images/main_screenshot.png'],
    "installable": True,
    "application": True,
    "auto_install": False,
}

