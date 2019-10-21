{
    'name': 'Cheque Printing Module',
    'version': '1.0',
    'sequence': 0,
    'author': "Allion Technologies PVT Ltd",
    'summary': 'Cheque Printing',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': ['account', 'account_check_printing'],
    'data': [
        'report/cheque_print_paperformat.xml',
        'report/cheque_ac_payee_only_without_20.xml',
        'report/cheque_ac_payee_only_with_20.xml',
        'report/cheque_cash_with_20.xml',
        'report/cheque_cash_without_20.xml'],
    'summary': 'Cheque Printing Module',
}
