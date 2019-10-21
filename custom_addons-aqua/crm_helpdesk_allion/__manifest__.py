# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CRM Help Desk Management',
    'version': '11.0.0.0',
    'category': 'Sales',
    'author': "Allion Technologies PVT Ltd",
    'website': 'www.alliontechnologies.com',
    'sequence': 5,
    'summary': 'This plugin helps to manage after services as crm help desk',
    'description': "Help Desk system for your product, claim management, submit claim, claim form, Ticket claim, support ticket, issue, website project issue, crm management, ticket handling,support management, project support, crm support, online support management, online claim, claim product, claim services, issue claim, fix claim, raise ticket, raise issue, view claim, display claim, list claim on website ",
    'depends': [
        'crm',
        'crm_base_allion',
        'crm_task_allion',
        'crm_phonecall_allion',
        'sale',
        'sale_management',
        'mail',
        'base',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/crm_helpdesk_menu.xml',
        'views/crm_helpdesk_data.xml',
        'views/res_partner_view.xml',
        'views/menuitem.xml'
],
'installable': True,
'application': True,
'auto_install': False,
}
