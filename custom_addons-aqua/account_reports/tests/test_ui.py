# -*- coding: utf-8 -*-

import odoo.tests

@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_ui(self):
        """this will be used to test followup reports"""
        self.phantom_js("/web", "odoo.__DEBUG__.services['web_tour.tour'].run('account_followup_reports_widgets', 'test')", "odoo.__DEBUG__.services['web_tour.tour'].tours.account_followup_reports_widgets", login='admin')
