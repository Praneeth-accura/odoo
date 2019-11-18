# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

{
    'name': 'Purchase By Vendor Report',
    'version': '1.0',
    'sequence': 1,
    'category': 'Inventory',
    'summary': 'Purchase by vendor report',
    'author':'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    'depends': ['purchase'],
    'data': [
        'wizard/purchase_vendor_report_wizard_view.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
