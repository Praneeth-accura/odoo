{
    'name': 'HR Processes Configuration',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 1,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Contains basic submodules of Human Resources',
    'description': """This module contains comfiguration of Nopay, Late, and over time processes""",
    'depends': [
        'hr',
        'hr_attendance'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_late_configuration_view.xml',
        'views/hr_nopay_configuration_view.xml',
        'views/hr_ot_configuration_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
