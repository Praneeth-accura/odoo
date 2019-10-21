# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools.translate import _


class generic_tax_report(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'account.generic.tax.report'

    # define the filters here
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_cash_basis = False
    filter_all_entries = False
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}

    def ooa_get_columns_name(self, options):
        """
        generic tax report main columns
        """
        dt_to = options['date'].get('date_to') or options['date'].get('date')
        dt_from = options['date'].get('date_from', False)
        # main columns for no comparison
        columns_header = [{}, {'name': '%s \n %s' % (_('NET'), self.ooa_format_date(dt_to, dt_from, options)), 'class': 'number', 'style': 'white-space: pre;'}, {'name': _('TAX'), 'class': 'number'}]
        if options.get('comparison') and options['comparison'].get('periods'):
            # main columns for comparison periods
            for p in options['comparison']['periods']:
                columns_header += [{'name': '%s \n %s' % (_('NET'), p.get('string')), 'class': 'number', 'style': 'white-space: pre;'}, {'name': _('TAX'), 'class': 'number'}]
        return columns_header

    def ooa_set_context(self, options):
        """return updated context, based on given options"""
        ctx = super(generic_tax_report, self).ooa_set_context(options)
        ctx['strict_range'] = True
        return ctx

    def ooa__get_with_statement(self, user_types, domain=None):
        # create with statement to prepend to the sql query
        sql = ''
        params = []

        # Cash basis option
        # we need to filter only income/expense accounts which paid under the payment date
        # so we need to generate WITH statement by joining invoice/aml/payments
        if self.env.context.get('cash_basis'):
            if not user_types:
                return sql, params
            # get default account.move.line query
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            sql = """WITH account_move_line AS (
              SELECT \"account_move_line\".id, \"account_move_line\".date, \"account_move_line\".name, \"account_move_line\".debit_cash_basis, \"account_move_line\".credit_cash_basis, \"account_move_line\".move_id, \"account_move_line\".account_id, \"account_move_line\".journal_id, \"account_move_line\".balance_cash_basis, \"account_move_line\".amount_residual, \"account_move_line\".partner_id, \"account_move_line\".reconciled, \"account_move_line\".company_id, \"account_move_line\".company_currency_id, \"account_move_line\".amount_currency, \"account_move_line\".balance, \"account_move_line\".user_type_id, \"account_move_line\".tax_line_id, \"account_move_line\".tax_exigible
               FROM """ + tables + """
               WHERE (\"account_move_line\".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR \"account_move_line\".move_id NOT IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s))
                 AND """ + where_clause + """
              UNION ALL
              (
               WITH payment_table AS (
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(am.amount) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.debit_move_id LEFT JOIN account_move am ON aml.move_id = am.id, """ + tables + """
                   WHERE part.credit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
                 UNION ALL
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(am.amount) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.credit_move_id LEFT JOIN account_move am ON aml.move_id = am.id, """ + tables + """
                   WHERE part.debit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
               )
               SELECT aml.id, ref.date, aml.name,
                 CASE WHEN aml.debit > 0 THEN ref.matched_percentage * aml.debit ELSE 0 END AS debit_cash_basis,
                 CASE WHEN aml.credit > 0 THEN ref.matched_percentage * aml.credit ELSE 0 END AS credit_cash_basis,
                 aml.move_id, aml.account_id, aml.journal_id,
                 ref.matched_percentage * aml.balance AS balance_cash_basis,
                 aml.amount_residual, aml.partner_id, aml.reconciled, aml.company_id, aml.company_currency_id, aml.amount_currency, aml.balance, aml.user_type_id, aml.tax_line_id, aml.tax_exigible
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params

    def ooa__sql_from_amls_one(self):
        sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                    FROM %s
                    WHERE %s AND "account_move_line".tax_exigible GROUP BY "account_move_line".tax_line_id"""
        return sql

    def ooa__sql_from_amls_two(self):
        sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                 FROM %s
                 INNER JOIN account_move_line_account_tax_rel r ON ("account_move_line".id = r.account_move_line_id)
                 INNER JOIN account_tax t ON (r.account_tax_id = t.id)
                 WHERE %s AND "account_move_line".tax_exigible GROUP BY r.account_tax_id"""
        return sql

    def ooa__compute_from_amls(self, options, taxes, period_number):
        sql = self.ooa__sql_from_amls_one()
        if options.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self.ooa__get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['periods'][period_number]['tax'] = result[1]
                taxes[result[0]]['show'] = True
        sql = self.ooa__sql_from_amls_two()
        if options.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['periods'][period_number]['net'] = result[1]
                taxes[result[0]]['show'] = True

    @api.model
    def ooa_get_lines(self, options, line_id=None):
        """
        return report lines data to render the view
        """
        taxes = {}
        # create tax dictionary by considering comparison periods
        for tax in self.env['account.tax'].with_context(active_test=False).search([]):
            taxes[tax.id] = {'obj': tax, 'show': False, 'periods': [{'net': 0, 'tax': 0}]}
            for period in options['comparison'].get('periods'):
                taxes[tax.id]['periods'].append({'net': 0, 'tax': 0})
        period_number = 0
        # compute tax values
        self.ooa__compute_from_amls(options, taxes, period_number)
        for period in options['comparison'].get('periods'):
            period_number += 1
            self.with_context(date_from=period.get('date_from'), date_to=period.get('date_to')).ooa__compute_from_amls(options, taxes, period_number)
        lines = []
        types = ['sale', 'purchase']
        groups = dict((tp, {}) for tp in types)
        for key, tax in taxes.items():
            if tax['obj'].type_tax_use == 'none':
                continue
            if tax['obj'].children_tax_ids:
                tax['children'] = []
                for child in tax['obj'].children_tax_ids:
                    if child.type_tax_use != 'none':
                        continue
                    tax['children'].append(taxes[child.id])
            if tax['obj'].children_tax_ids and not tax.get('children'):
                continue
            groups[tax['obj'].type_tax_use][key] = tax
        line_id = 0
        for tp in types:
            sign = tp == 'sale' and -1 or 1
            # add tax main section row
            lines.append({
                    'id': tp,
                    'name': tp == 'sale' and _('Sale') or _('Purchase'),
                    'unfoldable': False,
                    'columns': [{} for k in range(0, 2*(period_number+1) or 2)],
                    'level': 1,
                })
            for key, tax in sorted(groups[tp].items(), key=lambda k: k[1]['obj'].sequence):
                if tax['show']:
                    columns = []
                    for period in tax['periods']:
                        columns += [{'name': self.ooa_format_value(period['net'] * sign), 'style': 'white-space:nowrap;'},{'name': self.ooa_format_value(period['tax'] * sign), 'style': 'white-space:nowrap;'}]
                    # append tax row inside of the main tax section
                    lines.append({
                        'id': tax['obj'].id,
                        'name': tax['obj'].name + ' (' + str(tax['obj'].amount) + ')',
                        'unfoldable': False,
                        'columns': columns,
                        'level': 4,
                        'caret_options': 'account.tax',
                    })
                    # if exist child taxes, then append
                    for child in tax.get('children', []):
                        columns = []
                        for period in child['periods']:
                            columns += [{'name': self.ooa_format_value(period['net'] * sign), 'style': 'white-space:nowrap;'},{'name': self.ooa_format_value(period['tax'] * sign), 'style': 'white-space:nowrap;'}]
                        lines.append({
                            'id': child['obj'].id,
                            'name': '   ' + child['obj'].name + ' (' + str(child['obj'].amount) + ')',
                            'unfoldable': False,
                            'columns': columns,
                            'level': 4,
                            'caret_options': 'account.tax',
                        })
            line_id += 1
        return lines

    @api.model
    def ooa_get_report_name(self):
        """
        return the name for tax report
        """
        return _('Tax Report')
