# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'QB Import',
    'version': '1.0',
    'sequence': 1,
    'category': 'Account',
    'summary': 'Quick Book Import',
    'description': """
    This module is for exporting csv for QB 
""",
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'depends': [
        'account_invoicing',
        'sale', 
        'purchase',
    ],
    'data': [
             'views/qb_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

