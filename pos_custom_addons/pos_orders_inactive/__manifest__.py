{
    'name': 'POS Order Active/Inactive',
    'version': '1.0',
    'sequence': 1,
    'category': 'Point Of Sale',
    'summary': 'POS Order Active/Inactive',
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['point_of_sale', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_inactive.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}