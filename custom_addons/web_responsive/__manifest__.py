# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Web Responsive",
    "summary": "It provides a mobile compliant interface for Odoo Community "
               "web",
    "version": "1.0",
    "sequence": 1,
    "category": "Website",
    "author": "Technaureus Info Solutions",
    "website": "http://www.technaureus.com/",
    "license": "LGPL-3",
    "depends": [
        'web',
    ],
    "data": [
        'views/assets.xml',
        'views/web.xml',
    ],
    'qweb': [
        'static/src/xml/form_view.xml',
        'static/src/xml/navbar.xml',
    ],
    'installable': True,
    'application' :True,
}
