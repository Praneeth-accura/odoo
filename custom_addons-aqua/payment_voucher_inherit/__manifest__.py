{
    'name': 'Paymnent Voucher Inherit',
    'version': '1.0',
    'sequence': 0,
    'author': "Allion Technologies PVT Ltd",
    'summary': 'Payment Voucher',
    'depends': [
        'account',
        'account_invoicing',
    ],
    'data': [
        'data/payment_voucher_paperformat.xml',
        'data/payment_voucher_report.xml',
        'data/action_payment_voucher_report.xml',
        'views/account_payment_inherit_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

