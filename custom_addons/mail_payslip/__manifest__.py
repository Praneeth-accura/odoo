# -*- coding: utf-8 -*-

{
    'name': "Send Password Protected Payslips via mail.",
    'summary': """Send password protected Payslips to the employees via mail.""",
    'description': """
        Send password protected payslips to the employees via mail
        Secure odoo
        Secure Payslips
        Send payslip by mail
        Mail Payslip
        Employee Payslip
        Password Protection
        Send Payslip
    """,
    'author': "Almighty Consulting Services",
    'website': "http://www.almightycs.com",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['base', 'hr_payroll'],
    'data': [
        'views/mail_payslip.xml',
    ],
    'images': [
        'static/description/mail_payslip_cover_odoo_by_turkesh_patel.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 20,
    'currency': 'EUR',
}