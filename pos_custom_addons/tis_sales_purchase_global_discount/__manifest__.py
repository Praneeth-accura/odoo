# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Sales, Purchase & Invoice Global Discount',
    'version': '1.0',
    'sequence': 1,
    'category': 'Accounting',
    'summary': 'Sales, Purchase and Invoice Global Discount ',
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
   
    'description': """
This module is for adding global discount to sales, purchase and invoice
        """,
    'price': 36,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['account_invoicing','sale_management', 'purchase'],
    'data': [
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/account_invoice_view.xml',
        'views/res_config_settings_views.xml'
       
    ],
    'images': ['images/main_screenshot.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}