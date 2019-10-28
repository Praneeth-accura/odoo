{
    'name': 'Custom Invoice Stock Templates',
    'version': '1.0',
    'sequence': 1,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Custom Invoice Stock Templates',
    'description': """Custom Invoice Stock Templates""",
    'depends': [
        'account',
        'delivery',
        'sale_stock',
        'product_expiry'
    ],
    'data': [
        # data files
        'reports/grn_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}