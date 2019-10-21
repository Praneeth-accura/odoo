# -*- coding: utf-8 -*-
# Copyright (C) 2016-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
{
    'name': 'POS Cashier and Salesperson',
    'category': 'Point Of Sale',
    'summary': '''
        Show POS Cashier and salesperson separately.
    ''',
    'sequence': 1,
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'version': '1.0',
    'price': 30,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['point_of_sale'],
    'data': [
        'views/point_of_sale_view.xml',
        'views/point_of_sale.xml',
    ],
    'qweb': ['static/src/xml/cashier.xml'],
    'images': ['images/pos_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
