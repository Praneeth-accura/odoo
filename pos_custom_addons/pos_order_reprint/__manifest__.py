{
    'name': 'POS Order Reprint',
    'version': '1.0',
    'sequence': 1,
    'category': 'Point of Sale',
    'summary': 'POS Order Reprint',
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['point_of_sale'],
    'data': [
        'data/pos_report_layout.xml',
        'report/pos_order_reprint.xml',
        'views/pos_order_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}