# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class account_bank_reconciliation_report(models.AbstractModel):
    _name = 'account.bank.reconciliation.report'
    _description = 'Bank reconciliation report'
    _inherit = "account.report"

    # define the filters here
    filter_date = {'date': '', 'filter': 'today'}

    # maintain line number globally
    line_number = 0

    def ooa_get_columns_name(self, options):
        """
        bank reconciliation report main columns
        """
        return [
            {'name': ''},
            {'name': _("Date")},
            {'name': _("Reference")},
            {'name': _("Amount"), 'class': 'number'},
        ]

    def ooa_add_title_line(self, options, title, amount):
        """
        return level 0 title line with including given values
        """
        self.line_number += 1
        line_currency = self.env.context.get('line_currency', False)
        return {
            'id': 'line_' + str(self.line_number),
            'name': title,
            'columns': [{'name': v} for v in [options['date']['date'], '', self.ooa_format_value(amount, line_currency)]],
            'level': 0,
        }

    def ooa_add_subtitle_line(self, title, amount=None):
        """
        return level 1 sub title line with including given values
        """
        self.line_number += 1
        line_currency = self.env.context.get('line_currency', False)
        return {
            'id': 'line_' + str(self.line_number),
            'name': title,
            'columns': [{'name': v} for v in ['', '', amount and self.ooa_format_value(amount, line_currency) or '']],
            'level': 1,
        }

    def ooa_add_total_line(self, amount):
        """
        return level 2 total line with including given amount
        """
        self.line_number += 1
        line_currency = self.env.context.get('line_currency', False)
        return {
            'id': 'line_' + str(self.line_number),
            'name': '',
            'columns': [{'name': v} for v in ["", "", self.ooa_format_value(amount, line_currency)]],
            'level': 2,
        }

    def ooa_add_bank_statement_line(self, line, amount):
        """
        return level 1 unreconciled plus or minus line with given amount
        """
        name = line.name
        line_currency = self.env.context.get('line_currency', False)
        return {
            'id': str(line.id),
            'caret_options': True,
            'name': len(name) >= 85 and name[0:80] + '...' or name,
            'columns': [{'name': v} for v in [line.date, line.ref, self.ooa_format_value(amount, line_currency)]],
            'level': 1,
        }

    def ooa_print_pdf(self, options):
        """
        return bank reconciliation report in pdf mode
        """
        options['active_id'] = self.env.context.get('active_id')
        return super(account_bank_reconciliation_report, self).ooa_print_pdf(options)

    def ooa_print_xlsx(self, options):
        """
        return bank reconciliation report as excel file
        """
        options['active_id'] = self.env.context.get('active_id')
        return super(account_bank_reconciliation_report, self).ooa_print_xlsx(options)

    @api.model
    def ooa_get_lines(self, options, line_id=None):
        """
        return report lines data to render the view
        """
        journal_id = self._context.get('active_id') or options.get('active_id')
        journal = self.env['account.journal'].browse(journal_id)
        lines = []
        # compute current balance in GL
        use_foreign_currency = \
                journal.currency_id != journal.company_id.currency_id \
                if journal.currency_id else False
        account_ids = list(set([journal.default_debit_account_id.id, journal.default_credit_account_id.id]))
        line_currency = journal.currency_id if use_foreign_currency else False
        self = self.with_context(line_currency=line_currency)
        lines_already_accounted = self.env['account.move.line'].search(
                [
                    ('account_id', 'in', account_ids),
                    ('date', '<=', self.env.context['date_to']),
                    ('company_id', 'in', self.env.context['company_ids'])
                    ])
        start_amount = sum(
                [
                    line.amount_currency if use_foreign_currency else line.balance 
                    for line in lines_already_accounted
                ])
        # add current balance in GL to the lines
        lines.append(self.ooa_add_title_line(options, _("Current Balance in GL"), start_amount))

        # compute unreconciled payments
        move_lines = self.env['account.move.line'].search(
                [
                    ('move_id.journal_id', '=', journal_id),
                    '|', ('statement_line_id', '=', False), 
                    ('statement_line_id.date', '>', self.env.context['date_to']),
                    ('user_type_id.type', '=', 'liquidity'),
                    ('full_reconcile_id', '=', False),
                    ('date', '<=', self.env.context['date_to']),
                    ('company_id', 'in', self.env.context['company_ids'])
                ])
        unrec_tot = 0
        if move_lines:
            tmp_lines = []
            for line in move_lines:
                self.line_number += 1
                # create temporary list for unreconciled payments data
                tmp_lines.append({
                    'id': str(line.id),
                    'name': line.name,
                    'columns': [
                        {'name': v} for v in [
                            line.date, 
                            line.ref, 
                            self.ooa_format_value(
                                 -line.amount_currency
                                 if use_foreign_currency else -line.balance,
                                 line_currency)
                            ]],
                    'level': 1,
                })
                unrec_tot -= line.amount_currency if use_foreign_currency else line.balance
            # check for the Plus or Minus value to show
            if unrec_tot > 0:
                title = _("Plus Unreconciled Payments")
            else:
                title = _("Minus Unreconciled Payments")
            # append unreconciled payment lines to the main lines
            lines.append(self.ooa_add_subtitle_line(title))
            lines += tmp_lines
            lines.append(self.ooa_add_total_line(unrec_tot))

        # compute plus unreconciled statement lines
        not_reconcile_plus = self.env['account.bank.statement.line'].search(
                [
                    ('statement_id.journal_id', '=', journal_id),
                    ('date', '<=', self.env.context['date_to']),
                    ('journal_entry_ids', '=', False),
                    ('amount', '>', 0),
                    ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_plus_tot = 0
        if not_reconcile_plus:
            # append the title
            lines.append(self.ooa_add_subtitle_line(_("Plus Unreconciled Statement Lines")))
            # append the rest lines
            for line in not_reconcile_plus:
                lines.append(self.ooa_add_bank_statement_line(line, line.amount))
                outstanding_plus_tot += line.amount
            # append the total value
            lines.append(self.ooa_add_total_line(outstanding_plus_tot))

        # compute minus unreconciled statement lines
        not_reconcile_less = self.env['account.bank.statement.line'].search(
                [
                    ('statement_id.journal_id', '=', journal_id),
                    ('date', '<=', self.env.context['date_to']),
                    ('journal_entry_ids', '=', False),
                    ('amount', '<', 0),
                    ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_less_tot = 0
        if not_reconcile_less:
            # append the title
            lines.append(self.ooa_add_subtitle_line(_("Minus Unreconciled Statement Lines")))
            # append the rest lines
            for line in not_reconcile_less:
                lines.append(self.ooa_add_bank_statement_line(line, line.amount))
                outstanding_less_tot += line.amount
            # append the total value
            lines.append(self.ooa_add_total_line(outstanding_less_tot))

        # compute equal last statement balance
        computed_stmt_balance = start_amount + outstanding_plus_tot + outstanding_less_tot + unrec_tot
        last_statement = self.env['account.bank.statement'].search(
                [
                    ('journal_id', '=', journal_id),
                    ('date', '<=', self.env.context['date_to']), 
                    ('company_id', 'in', self.env.context['company_ids'])
                ], order="date desc, id desc", limit=1)
        real_last_stmt_balance = last_statement.balance_end
        # check for computed balance and last statement balance
        if computed_stmt_balance != real_last_stmt_balance:
            if real_last_stmt_balance - computed_stmt_balance > 0:
                title = _("Plus Missing Statements")
            else:
                title = _("Minus Missing Statements")
            # append the rest lines
            lines.append(self.ooa_add_subtitle_line(title, real_last_stmt_balance - computed_stmt_balance))
        # append the total value
        lines.append(self.ooa_add_title_line(options, _("Equal Last Statement Balance"), real_last_stmt_balance))
        return lines

    @api.model
    def ooa_get_report_name(self):
        """
        return the name for bank reconciliation report according to the journal
        """
        journal_id = self._context.get('active_id')
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            return _("Bank Reconciliation") + ': ' + journal.name
        return _("Bank Reconciliation")
