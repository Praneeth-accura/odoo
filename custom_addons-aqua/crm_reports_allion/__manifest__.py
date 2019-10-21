{
    'name': 'Allion CRM Reports',
    'summary': 'Reports of CRM module',
    'sequence': '1',
    'description': """
Reports of CRM module
=============
        """,
    'data': [
        'wizards/kpi_report_wizard_view.xml',
        'wizards/assignment_report_wizard_view.xml',
        'data/project_stage.xml',
        'data/schedule_activity.xml',
    ],
    'depends': ['crm_base_allion'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
