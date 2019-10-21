{
    'name': 'All Inventory Reorders',
    'version': '1.0',
    'sequence': 1,
    'category': 'Inventory',
    'summary': 'All Inventory Reorders',
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['purchase', 'stock', 'sale_management', 'base', 'hr'],
    'data': [
        'data/default_data_run_scheduler.xml',
        'data/reorder_email_template.xml',
        'security/ir.model.access.csv',
        'views/inventory_reorder_view.xml',
        'views/email_setting_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}