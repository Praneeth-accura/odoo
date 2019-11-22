{
    'name': 'Arava Template',
    'version': '1.0',
    'sequence': 0,
    'author': "OneStep Solutions",
    'website': 'https://onestep.lk/',
    'summary': 'Inherit Templates',
    'description': """Inherit By OneStep""",
    'depends': [
        'sale',
        'account',
        'purchase'
    ],
    'data': [
        'views/inherit_invoice.xml',
        'views/inherit_purchase_order.xml',
        'report/customer_invoice.xml',
        'report/customer_invoice_template.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
