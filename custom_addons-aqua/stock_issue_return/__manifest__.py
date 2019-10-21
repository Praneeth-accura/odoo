# -*- coding: utf-8 -*-
{
    'name': "Stock Issue Return",

    'summary': """
        Inventory Issuance and receipt transactions with charge types.""",

    'description': """
        This module allows you to enter inventory issuances and receipts. 
        It also lets you define charge types that are specified against an issuance/receipt.
    """,

    'author': "Qwexer",
    'website': "http://www.qwexer.com",
    'support': 'info@qwexer.com',
    'category': 'Warehouse',
    'version': '0.1',
    'price': 99.0,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': ['static/description/logo.png'],
    'depends': ['base','account','stock','purchase','stock_account'],

    'data': [
        'views/views.xml',
        'data/issue_return_seq.xml',
        'security/ir.model.access.csv',
        'report/stock_issue.xml',
    ],

}