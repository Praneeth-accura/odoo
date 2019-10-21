# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Payment Summary Report',
    'version': '1.0',
    'sequence': 1,
    'category': 'Accounting',
    'summary': 'Payment Summary Report',
    'description': """
    Payment Summary Report
""",
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'price': 49,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['account_invoicing'],
    'data': [
        'wizard/payment_summary_view.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
