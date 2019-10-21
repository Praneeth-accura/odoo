{
    'name': 'Tax Reports',
    'version': '1.0',
    'sequence': 0,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Tax Reports',
    'description': """This module contains four different tax reports""",
    'depends': [
        'account',
        'account_invoicing',
        'sale',
        'purchase',
    ],
    'data': [
        'wizards/tax_reports_wizard_view.xml',
        'views/inherit_account_invoice_view.xml',
        'views/inherit_sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}