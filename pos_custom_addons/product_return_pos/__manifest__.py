# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

{
    'name': 'Product Return in POS',
    'version': '1.0',
    'sequence': 1,
    'category': 'Point of Sale',
    'summary': 'POS Order Return',
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'depends': ['point_of_sale'],
    'data': [
             'views/pos_config_views.xml',
             'views/return.xml',
             'views/pos_template.xml',
            ],
    'qweb': ['static/src/xml/pos_return.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,

}
