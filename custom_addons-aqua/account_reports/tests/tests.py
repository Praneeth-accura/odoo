# -*- coding: utf-8 -*-

from odoo.tests import common


class TestAccountReports(common.TransactionCase):

    def test_00_financial_reports(self):
        """test generic financial reports"""
        for report in self.env['account.financial.html.report'].search([]):
            context_data = self.env['account.report.context.common'].return_context('account.financial.html.report', {}, report.id)
            self.env[context_data[0]].browse(context_data[1]).get_html_and_data()

    def test_01_custom_reports(self):
        """test other financial reports"""
        report_models = [
            'account.bank.reconciliation.report',
            'account.general.ledger',
            'account.generic.tax.report',
        ]
        for report_model in report_models:
            context_data = self.env['account.report.context.common'].return_context(report_model, {})
            self.env[context_data[0]].browse(context_data[1]).get_html_and_data()

    def test_02_followup_reports(self):
        """test customer followup reports"""
        self.env['account.report.context.followup.all'].create({}).ooa_get_html({'page': 1})
        self.env['account.report.context.followup'].create({'partner_id': self.env.ref('base.res_partner_2').id}).ooa_get_html()

    def test_03_general_ledger(self):
        """test general ledger"""
        context = self.env['account.context.general.ledger'].create({})
        self.env['account.general.ledger'].ooa_get_lines(context.id)
