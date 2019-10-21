# -- coding: utf-8 --
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
{
    'name' : 'POS Report',
    'version' : '1.0',
    'category':'Point of sale',
    'sequence': 1,
    'author':'Technaureus Info solutions',
    'summary': 'POS Sale details',
    'website':'http://www.technaureus.com',
    'price': 175,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
        Session Reports
        ================
        1.POS Session Summary
        2.Session Order Summary Report.
        
        Sales Details XLSX Report.
        ========================
        3.Order Summary Report.
        4.Daily Sales by Salesperson.
        5.Daily Itemwise sales summary.
        6.Monthly Sales by salesperson.
        7.Monthly Itemwise sales summary
        8.Date range by salesperson sales summary
        9.Date range by itemwise sales summary""",
    'external_dependencies': {'python': ['xlsxwriter']},
    'depends' : ['pos_sale'],
    'data': [
       'report/session_summary_report.xml',
       'report/session_summary.xml',
       'report/session_order_summary.xml',
       'wizard/pos_report.xml',
       'wizard/xlsx_download_wizard_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
