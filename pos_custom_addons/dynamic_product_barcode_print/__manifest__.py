# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

{
    'name': " Dynamic Product Barcode Print",
    'version': '1.1',
    'sequence': 1,
    'category': 'Product',
    'description': """Dynamic Product Page Label.""",
    'summary': 'Create custom barcode template by frontend and print dynamic barcode.',
    'author': 'Technaureus Info Solutions',
    'website': 'http://www.technaureus.com/',
    "depends": ['sale', 'base', 'purchase', 'stock', 'account'],
    "data": [
        'views/wizard_product_page_report_view.xml',
        'page_reports.xml',
        'security/ir.model.access.csv',
        'views/dynamic_prod_page_rpt.xml',
        'data/design_data.xml'
    ],
    "installable": True,
    'auto_install': False,
    'application': True,
}

