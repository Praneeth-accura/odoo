{
    'name': 'CRM Phone Call Log',
    'version': '11.0.0.0',
    'category': 'Sales',
    'author': "Allion Technologies PVT Ltd",
    'website': 'www.alliontechnologies.com',
    'summary': 'This plugin helps to track every phone calls',
    'description': "This plugin helps to log any kind of phone calls, Phone numbers, Lead just came from phone calls and Schedule meetings",
    'depends': [
        'mail',
        'crm',
        'base'
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/crm_phonecalls_view.xml',
        'views/crm_phonecalls_menu.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
