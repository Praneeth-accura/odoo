# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_is_zero
from datetime import datetime, timedelta


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.report"
    _name = "account.partner.ledger"
    _description = "Partner Ledger"

    # define the filters here
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
    filter_cash_basis = False
    filter_all_entries = False
    filter_unfold_all = False
    filter_account_type = [{'id': 'receivable', 'name': _('Receivable'), 'selected': False}, {'id': 'payable', 'name': _('Payable'), 'selected': False}]
    filter_unreconciled = False
    filter_partner_id = False

    def ooa_get_templates(self):
        """
        return templates for render the report
        """
        templates = super(ReportPartnerLedger, self).ooa_get_templates()
        templates['line_template'] = 'account_reports.ooa_line_template_partner_ledger_report'
        templates['main_template'] = 'account_reports.ooa_template_partner_ledger_report'
        return templates

    def ooa_get_columns_name(self, options):
        """
        return partner ledger report main columns
        """
        return [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'},
        ]

    def ooa_set_context(self, options):
        """return updated context, based on given options"""
        ctx = super(ReportPartnerLedger, self).ooa_set_context(options)
        ctx['strict_range'] = True
        return ctx

    def ooa_do_query(self, options, line_id):
        """
        calculate partner debit, credit and balance for date range in the context
        """
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        select = ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
        if options.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        sql = "SELECT \"account_move_line\".partner_id%s FROM %s WHERE %s%s AND \"account_move_line\".partner_id IS NOT NULL GROUP BY \"account_move_line\".partner_id"
        tables, where_clause, where_params = self.env['account.move.line']._query_get([('account_id.internal_type', 'in', account_types)])
        line_clause = line_id and ' AND \"account_move_line\".partner_id = ' + str(line_id) or ''
        if options.get('unreconciled'):
            line_clause += ' AND \"account_move_line\".full_reconcile_id IS NULL'
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        results = dict([(k[0], {'balance': k[1], 'debit': k[2], 'credit': k[3]}) for k in results])
        return results

    def ooa_group_by_partner_id(self, options, line_id):
        """
        return debit, credit, balance and initial balance data with relevant partner
        """
        partners = {}
        # filter account types from options
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        date_from = options['date']['date_from']
        # get debit, credit and balance data for given period
        results = self.ooa_do_query(options, line_id)
        initial_bal_date_to = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=-1)
        # get debit, credit and balance data for before the given period
        initial_bal_results = self.with_context(date_from=False, date_to=initial_bal_date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)).ooa_do_query(options, line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids']), ('account_id.internal_type', 'in', account_types)]
        base_domain.append(('date', '>=', date_from))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if options.get('unreconciled'):
            base_domain.append(('full_reconcile_id', '=', False))
        for partner_id, result in results.items():
            domain = list(base_domain)  # get the base domain
            domain.append(('partner_id', '=', partner_id))
            partner = self.env['res.partner'].browse(partner_id)
            partners[partner] = result
            partners[partner]['initial_bal'] = initial_bal_results.get(partner.id, {'balance': 0, 'debit': 0, 'credit': 0})
            partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
            if not context.get('print_mode'):
                # display only first 80 amls in web view, not for print view
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date', limit=81)
            else:
                partners[partner]['lines'] = self.env['account.move.line'].search(domain, order='date')

        # add missing partner's data
        prec = self.env.user.company_id.currency_id.rounding
        missing_partner_ids = set(initial_bal_results.keys()) - set(results.keys())
        for partner_id in missing_partner_ids:
            if not float_is_zero(initial_bal_results[partner_id]['balance'], precision_rounding=prec):
                partner = self.env['res.partner'].browse(partner_id)
                partners[partner] = {'balance': 0, 'debit': 0, 'credit': 0}
                partners[partner]['initial_bal'] = initial_bal_results[partner_id]
                partners[partner]['balance'] += partners[partner]['initial_bal']['balance']
                partners[partner]['lines'] = self.env['account.move.line']

        return partners

    @api.model
    def ooa_get_lines(self, options, line_id=None):
        """
        return report rows data lines
        """
        lines = []
        # if exist line_id, need to return data to the specific line
        if line_id:
            line_id = line_id.replace('partner_', '')
        context = self.env.context

        # load only relevant data to given partner
        if options.get('partner_id'):
            line_id = options['partner_id']

        # get partners with grouping and sorting
        grouped_partners = self.ooa_group_by_partner_id(options, line_id)
        sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines') or options.get('partner_id')
        total_initial_balance = total_debit = total_credit = total_balance = 0.0
        for partner in sorted_partners:
            debit = grouped_partners[partner]['debit']
            credit = grouped_partners[partner]['credit']
            balance = grouped_partners[partner]['balance']
            initial_balance = grouped_partners[partner]['initial_bal']['balance']
            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            # append partner details line to main lines
            lines.append({
                'id': 'partner_' + str(partner.id),
                'name': partner.name,
                'columns': [{'name': v} for v in [self.ooa_format_value(initial_balance), self.ooa_format_value(debit), self.ooa_format_value(credit), self.ooa_format_value(balance)]],
                'level': 2,
                'trust': partner.trust,
                'unfoldable': True,
                'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
                'colspan': 5,
            })
            # if unfold partner, add rest lines
            if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
                progress = initial_balance
                domain_lines = []
                amls = grouped_partners[partner]['lines']
                too_many = False
                if len(amls) > 80 and not context.get('print_mode'):
                    amls = amls[-80:]
                    too_many = True
                for line in amls:
                    # check for cash basis or accrual basis
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    # calculate the progress
                    progress_before = progress
                    progress = progress + line_debit - line_credit
                    # create name for line
                    name = '-'.join(
                        (line.move_id.name not in ['', '/'] and [line.move_id.name] or []) +
                        (line.ref not in ['', '/', False] and [line.ref] or []) +
                        ([line.name] if line.name and line.name not in ['', '/'] else [])
                    )
                    if len(name) > 35 and not self.env.context.get('no_format'):
                        name = name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    # append sub line to the partner
                    domain_lines.append({
                        'id': line.id,
                        'parent_id': 'partner_' + str(partner.id),
                        'name': line.date,
                        'columns': [{'name': v} for v in [line.journal_id.code, line.account_id.code, name, line.full_reconcile_id.name, self.ooa_format_value(progress_before),
                                    line_debit != 0 and self.ooa_format_value(line_debit) or '',
                                    line_credit != 0 and self.ooa_format_value(line_credit) or '',
                                    self.ooa_format_value(progress)]],
                        'caret_options': caret_type,
                        'level': 4,
                    })
                # if items count > 80, collapse lines
                if too_many:
                    domain_lines.append({
                        'id': 'too_many_' + str(partner.id),
                        'parent_id': 'partner_' + str(partner.id),
                        'action': 'ooa_view_too_many',
                        'action_id': 'partner,%s' % (partner.id,),
                        'name': _('There are more than 80 items in this list, click here to see all of them'),
                        'colspan': 8,
                        'columns': [{}],
                    })
                lines += domain_lines
        # append final total line
        if not line_id:
            lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in ['', '', '', '', self.ooa_format_value(total_initial_balance), self.ooa_format_value(total_debit), self.ooa_format_value(total_credit), self.ooa_format_value(total_balance)]],
            })
        return lines

    @api.model
    def ooa_get_report_name(self):
        """
        return the name for partner ledger report
        """
        return _('Partner Ledger')
