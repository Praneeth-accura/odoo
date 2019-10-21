# -*- coding: utf-8 -*-
# Copyright (C)2017 -present Technaureus Info Solutions(<http://technaureus.com/>).

{
    'name': 'Employee Document Preview (Thumbnail View)',
    'version': '1.0',
    'category': 'Human Resource',
    'sequence': 1,
    'summary': 'Human Resource',
    'description': """
Employee Document
    """,
    'website': 'http://technaureus.com/',
    'author': 'Technaureus Info Solutions',
    'depends': ['hr','document'],
    'price': 20,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'data': [
        'views/employee_view.xml'
        ],
    "qweb" : [],
    'demo': [],
    'css': [],
    'images': ['images/employee_documents_screenshot.png'],
    'installable': True,
    'auto_install': True,
    'application': True,
}
