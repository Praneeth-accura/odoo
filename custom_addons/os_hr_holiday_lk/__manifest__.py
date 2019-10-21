# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).


{
    'name': 'Employee Holiday',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 3,
    'author':'Technaureus Info Solutions',
    'summary': 'Employee Holiday Management',
    'website': 'http://www.technaureus.com/',
    'description': """
Emplyee leaves, holiday ...""",
    'depends': ['hr_holidays'],
    'data': [
        'data/hr_leaves_data.xml',
        'security/module_data.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
