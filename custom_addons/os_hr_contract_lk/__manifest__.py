# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).


{
    'name': 'Srilankan Contract',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 2,
    'author':'Technaureus Info Solutions',
    'summary': 'Employee Contract Management',
    'website': 'http://www.technaureus.com/',
    'description': """
  Employee  Contracts Management """,
    'depends': ['hr_contract'],
    'data': [
        'views/hr_contract_view.xml',
        'views/payment_method_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
