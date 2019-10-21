# -*- coding: utf-8 -*-
{
    'name': 'Accounting and Finance',
    'version': '1.1',
    'category': 'Accounting',
    'sequence': 0,
    'summary': 'Facility for Financial and Analytic Accounting',
    'description': """
""",
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['account_invoicing', 'web_tour', 'account_reports'],
    'data': [
        'data/account_accountant_data.xml',
        'security/account_accountant_security.xml',
        'views/account_accountant_templates.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'wizard/account_change_lock_date.xml',
    ],
    'demo': ['data/account_accountant_demo.xml'],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': "uninstall_hook",
}
