# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

{
    "name": "Employee Bonus",
    "version": "1.0",
    "sequence": 1,
    "category": "Human Resources",
    "summary": "Employee Bonus",
    "author": "Technaureus Info Solutions",
    "website": "http://www.technaureus.com/",
    "description": """
This module contain employee bonus pay slips and batches
    """,
    "depends": ['os_hr_epf_etf'],
    
    "data": [
        "views/os_hr_bonus_views.xml",
         "views/revenue_tax_views.xml",
         "views/bonus_batch_views.xml",
         "report/bonus_report.xml",
         "report/bonus_report_template.xml",
         "report/bonus_batch_report_xlsx.xml",
         "data/paye_bonus_taxtable.xml",
        "data/gross.income.csv"
         ],
             
    "installable": True,
    "application": True,
    "auto_install": False,
}