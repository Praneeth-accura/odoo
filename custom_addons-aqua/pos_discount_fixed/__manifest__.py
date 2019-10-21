# -*- coding: utf-8 -*-
# Copyright (C) 2018-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
{
    'name': 'POS Global Discounts - Fixed/Percentage(Cash Discount)',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'Fixed/Percentage Global Discounts(Cash Discount) in the Point of Sale ',
    'description': """
This module allows the cashier to quickly give a fixed/percentage
sale discount(cash discount) to a customer.
""",
    'website': 'http://www.technaureus.com',
    'author': 'Technaureus Info Solutions',
    'price': 35,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['pos_discount'],
    'data': [
        'data/point_of_sale_data.xml',
        'views/pos_discount_views.xml',
        'views/pos_discount_templates.xml'
    ],
    'qweb': [
        'static/src/xml/discount_templates.xml',
    ],
    'images': ['images/pos_global_discount_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
