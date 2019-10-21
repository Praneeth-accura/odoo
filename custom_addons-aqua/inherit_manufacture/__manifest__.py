{
    'name': 'Inherit Manufacture Orders',
    'version': '1.0',
    'sequence': 0,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Inherit Manufacture Orders',
    'description': """This module add additional features to manufacturing orders to Sales Order""",
    'depends': [
        'mrp',
        'sale',
        'stock',
    ],
    'data': [
        'views/inherit_stock_move_view.xml',
        'wizards/mrp_reports_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}