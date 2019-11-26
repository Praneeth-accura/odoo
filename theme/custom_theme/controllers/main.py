# -*- coding: utf-8 -*-
# Copyright 2016, 2017 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from openerp import http, _
from openerp.http import request


class Bar(http.Controller):
    @http.route('/foo', type='http', website=True, auth="public")
    def page_certificate_verification(self, **kw):
        return request.render('custom_theme.sample_view')


class SaleTheme(http.Controller):
    @http.route('/account', type='http', website=True, auth="public")
    def page_certificate_verification(self, **kw):
        return request.render('custom_theme.account_view')
