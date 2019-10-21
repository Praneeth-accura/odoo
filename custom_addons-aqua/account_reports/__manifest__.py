# -*- coding: utf-8 -*-
{
    'name': 'Accounting Reports',
    'version': '1.0',
    'sequence': 0,
    'summary': 'Facility for view and download accounting reports',
    'category': 'Accounting',
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'description': """
Accounting Reports
==================
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_financial_report_data.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
        'views/search_template_view.xml',
        'views/report_followup.xml',
        'views/partner_view.xml',
        'views/account_journal_dashboard_view.xml',
        'views/res_config_settings_views.xml'
    ],
    'qweb': [
        'static/src/xml/account_report_template.xml',
    ],
    'auto_install': True,
    'installable': True,
    'license': '',
}
