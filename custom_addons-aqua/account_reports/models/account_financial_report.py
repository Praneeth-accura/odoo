# -*- coding: utf-8 -*-
import copy
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, ustr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ReportAccountFinancialReport(models.Model):
    _name = "account.financial.html.report"
    _description = "Account Report"
    _inherit = "account.report"

    name = fields.Char(translate=True)
    debit_credit = fields.Boolean('Show Credit and Debit Columns')
    line_ids = fields.One2many('account.financial.html.report.line', 'financial_report_id', string='Lines')
    date_range = fields.Boolean('Based on date ranges', default=True, help='specify if the report use date_range or single date')
    comparison = fields.Boolean('Allow comparison', default=True, help='display the comparison filter')
    cash_basis = fields.Boolean('Use cash basis', help='if true, report will always use cash basis, if false, user can choose from filter inside the report')
    analytic = fields.Boolean('Allow analytic filter', help='display the analytic filter')
    hierarchy_option = fields.Boolean('Enable the hierarchy option', help='Display the hierarchy choice in the report options')
    show_journal_filter = fields.Boolean('Allow filtering by journals', help='display the journal filter in the report')
    unfold_all_filter = fields.Boolean('Show unfold all filter', help='display the unfold all options in report')
    company_id = fields.Many2one('res.company', string='Company')
    generated_menu_id = fields.Many2one(
        string='Menu Item', comodel_name='ir.ui.menu', copy=False,
        help="The menu item generated for this report, or None if there isn't any."
    )
    parent_id = fields.Many2one('ir.ui.menu', related="generated_menu_id.parent_id")
    tax_report = fields.Boolean('Tax Report', help="Set to True to automatically filter out journal items that have the boolean field 'tax_exigible' set to False")

    def ooa_get_columns_name(self, options):
        """
        return account financial reports main columns
        """
        columns = [{'name': ''}]
        if self.debit_credit and not options.get('comparison', {}).get('periods', False):
            columns += [{'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}]
        dt_to = options['date'].get('date_to') or options['date'].get('date')
        columns += [{'name': self.ooa_format_date(dt_to, options['date'].get('date_from', False), options), 'class': 'number'}]
        # if user enable comparison with periods need to change columns
        if options.get('comparison') and options['comparison'].get('periods'):
            for period in options['comparison']['periods']:
                columns += [{'name': period.get('string'), 'class': 'number'}]
            if options['comparison'].get('number_period') == 1:
                columns += [{'name': '%', 'class': 'number'}]
        return columns

    @api.model
    def ooa_get_options(self, previous_options=None):
        """
        get options for financial reports
        """
        # if report is for date range, initialize filter for date range
        if self.date_range:
            self.filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
            # if report is enabled for comparison, initialize filter
            if self.comparison:
                self.filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
        # if report is for specific date, initialize filter for date
        else:
            self.filter_date = {'date': '', 'filter': 'today'}
            # if report is enabled for comparison, initialize filter
            if self.comparison:
                self.filter_comparison = {'date': '', 'filter': 'no_comparison', 'number_period': 1}
        # check for other filters
        self.filter_cash_basis = False
        if self.cash_basis:
            self.filter_cash_basis = None
        if self.unfold_all_filter:
            self.filter_unfold_all = False
        if self.show_journal_filter:
            self.filter_journals = True
        self.filter_all_entries = False
        self.filter_analytic = True if self.analytic else None
        self.filter_hierarchy = True if self.hierarchy_option else None
        return super(ReportAccountFinancialReport, self).ooa_get_options(previous_options)

    def ooa_create_action_and_menu(self, parent_id):
        # create menu items and actions related to financial reports
        user_created = self._context.get('user_created')
        module = self._context.get('install_mode_data', {}).get('module', 'account_reports')
        IMD = self.env['ir.model.data']
        for report in self:
            if not report.generated_menu_id:
                action_vals = {
                    'name': report.ooa_get_report_name(),
                    'tag': 'account_report',
                    'context': {
                        'model': 'account.financial.html.report',
                        'id': report.id,
                    },
                }
                action_id = IMD._update('ir.actions.client', module, action_vals,
                                    xml_id='account_financial_html_report_action_' + str(report.id), noupdate=True)
                menu_vals = {
                    'name': report.ooa_get_report_name(),
                    'parent_id': parent_id or IMD.xmlid_to_res_id('account.menu_finance_reports'),
                    'action': 'ir.actions.client,%s' % (action_id,),
                }

                new_menu = IMD._update('ir.ui.menu', module, menu_vals,
                            xml_id='account_financial_html_report_menu_' + str(report.id), noupdate=True)
                self.write({'generated_menu_id': new_menu})

    @api.model
    def create(self, vals):
        """
        if not exist menu item for this report, create it
        """
        parent_id = vals.pop('parent_id', False)
        res = super(ReportAccountFinancialReport, self).create(vals)
        res.ooa_create_action_and_menu(parent_id)
        return res

    @api.multi
    def write(self, vals):
        """
        update menu items related to this report
        """
        parent_id = vals.pop('parent_id', False)
        res = super(ReportAccountFinancialReport, self).write(vals)
        if parent_id:
            # if above created menu items were modified, then update them
            for report in self:
                report.ooa_create_action_and_menu(parent_id)
        return res

    @api.multi
    def unlink(self):
        """
        when unlink this report need to unlink related menu items
        """
        for report in self:
            default_parent_id = self.env['ir.model.data'].xmlid_to_res_id('account.menu_finance_reports')
            menu = self.env['ir.ui.menu'].search([('parent_id', '=', default_parent_id), ('name', '=', report.name)])
            if menu:
                menu.action.unlink()
                menu.unlink()
        return super(ReportAccountFinancialReport, self).unlink()

    def ooa__get_currency_table(self):
        """
        prepare currency table for all companies
        """
        used_currency = self.env.user.company_id.currency_id.with_context(company_id=self.env.user.company_id.id)
        currency_table = {}
        for company in self.env['res.company'].search([]):
            if company.currency_id != used_currency:
                currency_table[company.currency_id.id] = used_currency.rate / company.currency_id.rate
        return currency_table

    @api.multi
    def ooa_get_lines(self, options, line_id=None):
        """
        return report rows data lines
        """
        # get mapped financial report lines
        line_obj = self.line_ids
        # if need data for specific row, get only that report line
        if line_id:
            line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
        # if comparison and periods are enabled, get data according to periods
        if options.get('comparison') and options.get('comparison').get('periods'):
            line_obj = line_obj.with_context(periods=options['comparison']['periods'])
        currency_table = self.ooa__get_currency_table()
        linesDicts = [{} for _ in range(0, len((options.get('comparison') or {}).get('periods') or []) + 2)]
        # check for cash basis or accrual basis
        res = line_obj.with_context(
            cash_basis=options.get('cash_basis') or self.cash_basis,
        ).ooa_get_lines(self, currency_table, options, linesDicts)
        return res

    def ooa_get_report_name(self):
        """
        return the stored name for financial report
        """
        return self.name

    @api.multi
    def ooa__get_copied_name(self):
        # return unique name for duplicated report
        self.ensure_one()
        name = self.name + ' ' + _('(copy)')
        while self.search_count([('name', '=', name)]) > 0:
            name += ' ' + _('(copy)')
        return name

    @api.multi
    def copy(self, default=None):
        # duplicate the report by creating new report lines recursively
        self.ensure_one()
        if default is None:
            default = {}
        default.update({'name': self.ooa__get_copied_name()})
        copied_report_id = super(ReportAccountFinancialReport, self).copy(default=default)
        for line in self.line_ids:
            line.ooa_copy_hierarchy(report_id=self, copied_report_id=copied_report_id)
        return copied_report_id


class AccountFinancialReportLine(models.Model):
    _name = "account.financial.html.report.line"
    _description = "Account Report Line"
    _order = "sequence"

    name = fields.Char('Section Name', translate=True)
    code = fields.Char('Code')
    financial_report_id = fields.Many2one('account.financial.html.report', 'Financial Report')
    parent_id = fields.Many2one('account.financial.html.report.line', string='Parent')
    children_ids = fields.One2many('account.financial.html.report.line', 'parent_id', string='Children')
    sequence = fields.Integer()

    domain = fields.Char(default=None)
    formulas = fields.Char()
    groupby = fields.Char("Group by", default=False)
    figure_type = fields.Selection([('float', 'Float'), ('percents', 'Percents'), ('no_unit', 'No Unit')],
                                   'Type', default='float', required=True)
    green_on_positive = fields.Boolean('Is growth good when positive', default=True)
    level = fields.Integer(required=True)
    special_date_changer = fields.Selection([
        ('from_beginning', 'From the beginning'),
        ('to_beginning_of_period', 'At the beginning of the period'),
        ('normal', 'Use given dates'),
        ('strict_range', 'Force given dates for all accounts and account types'),
        ('from_fiscalyear', 'From the beginning of the fiscal year'),
    ], default='normal')
    show_domain = fields.Selection([('always', 'Always'), ('never', 'Never'), ('foldable', 'Foldable')], default='foldable')
    hide_if_zero = fields.Boolean(default=False)
    action_id = fields.Many2one('ir.actions.actions')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "A report line with the same code already exists."),
    ]

    @api.constrains('code')
    def ooa__code_constrains(self):
        """
        the code should be unique and not within builtins
        """
        if self.code and self.code.strip().lower() in __builtins__.keys():
            raise ValidationError('The code "%s" is invalid on line with name "%s"' % (self.code, self.name))

    @api.multi
    def ooa__get_copied_code(self):
        # return unique code for duplicated report line
        self.ensure_one()
        code = self.code + '_COPY'
        while self.search_count([('code', '=', code)]) > 0:
            code += '_COPY'
        return code

    @api.multi
    def ooa_copy_hierarchy(self, report_id=None, copied_report_id=None, parent_id=None, code_mapping=None):
        # copy current line and child lines recursively
        self.ensure_one()
        if code_mapping is None:
            code_mapping = {}
        # map current line with relevant report
        if report_id and copied_report_id and self.financial_report_id.id == report_id.id:
            financial_report_id = copied_report_id.id
        else:
            financial_report_id = None
        copy_line_id = self.copy({
            'financial_report_id': financial_report_id,
            'parent_id': parent_id and parent_id.id,
            'code': self.code and self.ooa__get_copied_code(),
        })
        # to create formulas for new line, need previous and new code. so we keep codes as mutable dict
        if self.code:
            code_mapping[self.code] = copy_line_id.code
        # recursively duplicate child lines
        for line in self.children_ids:
            line.ooa_copy_hierarchy(parent_id=copy_line_id, code_mapping=code_mapping)
        # by using above created code_mapping dict, update new line's code
        if self.formulas:
            copied_formulas = self.formulas
            for k, v in code_mapping.items():
                for field in ['debit', 'credit', 'balance', 'amount_residual']:
                    suffix = '.' + field
                    copied_formulas = copied_formulas.replace(k + suffix, v + suffix)
            copy_line_id.formulas = copied_formulas

    def ooa__query_get_select_sum(self, currency_table):
        # when compute the report lines, this function can use to build SELECT statements
        extra_params = []
        select = '''
            COALESCE(SUM(\"account_move_line\".balance), 0) AS balance,
            COALESCE(SUM(\"account_move_line\".amount_residual), 0) AS amount_residual,
            COALESCE(SUM(\"account_move_line\".debit), 0) AS debit,
            COALESCE(SUM(\"account_move_line\".credit), 0) AS credit
        '''
        # compare currency table for generate the query
        if currency_table:
            select = 'COALESCE(SUM(CASE '
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id, rate]
                select += 'WHEN \"account_move_line\".company_currency_id = %s THEN \"account_move_line\".balance * %s '
            select += 'ELSE \"account_move_line\".balance END), 0) AS balance, COALESCE(SUM(CASE '
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id, rate]
                select += 'WHEN \"account_move_line\".company_currency_id = %s THEN \"account_move_line\".amount_residual * %s '
            select += 'ELSE \"account_move_line\".amount_residual END), 0) AS amount_residual, COALESCE(SUM(CASE '
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id, rate]
                select += 'WHEN \"account_move_line\".company_currency_id = %s THEN \"account_move_line\".debit * %s '
            select += 'ELSE \"account_move_line\".debit END), 0) AS debit, COALESCE(SUM(CASE '
            for currency_id, rate in currency_table.items():
                extra_params += [currency_id, rate]
                select += 'WHEN \"account_move_line\".company_currency_id = %s THEN \"account_move_line\".credit * %s '
            select += 'ELSE \"account_move_line\".credit END), 0) AS credit'

        if self.env.context.get('cash_basis'):
            for field in ['debit', 'credit', 'balance']:
                # selected columns are updated with '_cash_basis' except final column
                number_of_occurence = len(select.split(field)) - 1
                select = select.replace(field, field + '_cash_basis', number_of_occurence - 1)
        return select, extra_params

    def ooa__get_with_statement(self, financial_report):
        # create with statement to prepend to the sql query
        sql = ''
        params = []

        # Cash flow Statement
        # need special query to make WITH statement for sql query
        if financial_report == self.env.ref('account_reports.ooa_account_financial_report_cashsummary0'):
            # to build the SELECT part of the query, get all available fields in account.move.line
            replace_columns = {
                'date': 'ref.date',
                'debit_cash_basis': 'CASE WHEN \"account_move_line\".debit > 0 THEN ref.matched_percentage * \"account_move_line\".debit ELSE 0 END AS debit_cash_basis',
                'credit_cash_basis': 'CASE WHEN \"account_move_line\".credit > 0 THEN ref.matched_percentage * \"account_move_line\".credit ELSE 0 END AS credit_cash_basis',
                'balance_cash_basis': 'ref.matched_percentage * \"account_move_line\".balance AS balance_cash_basis'
            }
            columns = []
            columns_2 = []
            for name, field in self.env['account.move.line']._fields.items():
                if not(field.store and field.type not in ('one2many', 'many2many')):
                    continue
                columns.append('\"account_move_line\".%s' % name)
                if name in replace_columns:
                    columns_2.append(replace_columns.get(name))
                else:
                    columns_2.append('\"account_move_line\".%s' % name)
            select_clause_1 = ', '.join(columns)
            select_clause_2 = ', '.join(columns_2)

            # joining account_move_line with move
            fake_domain = [('move_id.id', '!=', None)]
            sub_tables, sub_where_clause, sub_where_params = self.env['account.move.line']._query_get(domain=fake_domain)
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=fake_domain + safe_eval(self.domain))

            # get moves related to bank accounts
            bank_journals = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))])
            bank_accounts = bank_journals.mapped('default_debit_account_id') + bank_journals.mapped('default_credit_account_id')
            q = '''SELECT DISTINCT(\"account_move_line\".move_id)
                    FROM ''' + tables + '''
                    WHERE account_id IN %s
                    AND ''' + sub_where_clause
            p = [tuple(bank_accounts.ids)] + sub_where_params
            self._cr.execute(q, p)
            bank_move_ids = tuple([r[0] for r in self.env.cr.fetchall()])

            # skip all liquidity accounts and get only accounts related to bank/cash journal
            if self.code in ('CASHEND', 'CASHSTART'):
                return '''
                WITH account_move_line AS (
                    SELECT ''' + select_clause_1 + '''
                    FROM account_move_line
                    WHERE account_id in %s)''', [tuple(bank_accounts.ids)]

            # if not bank moves, skip
            if not bank_move_ids:
                return '''
                WITH account_move_line AS (
                    SELECT ''' + select_clause_1 + '''
                    FROM account_move_line
                    WHERE False)''', []

            sql = '''
                WITH account_move_line AS (

                    -- Part for the reconciled journal items
                    -- payment_table will give the reconciliation rate per account per move to consider
                    -- (so that an invoice with multiple payment terms would correctly display the income
                    -- accounts at the prorata of what hass really been paid)
                    WITH payment_table AS (
                        SELECT
                            aml2.move_id AS matching_move_id,
                            aml2.account_id,
                            aml.date AS date,
                            SUM(CASE WHEN (aml.balance = 0 OR sub.total_per_account = 0)
                                THEN 0
                                ELSE part.amount / sub.total_per_account
                            END) AS matched_percentage
                        FROM account_partial_reconcile part
                        LEFT JOIN account_move_line aml ON aml.id = part.debit_move_id
                        LEFT JOIN account_move_line aml2 ON aml2.id = part.credit_move_id
                        RIGHT JOIN (SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account FROM account_move_line GROUP BY move_id, account_id) sub ON (aml2.account_id = sub.account_id AND sub.move_id=aml2.move_id)
                        LEFT JOIN account_account acc ON aml.account_id = acc.id
                        WHERE part.credit_move_id = aml2.id
                        AND acc.reconcile
                        AND aml.move_id IN %s
                        GROUP BY aml2.move_id, aml2.account_id, aml.date

                        UNION ALL

                        SELECT
                            aml2.move_id AS matching_move_id,
                            aml2.account_id,
                            aml.date AS date,
                            SUM(CASE WHEN (aml.balance = 0 OR sub.total_per_account = 0)
                                THEN 0
                                ELSE part.amount / sub.total_per_account
                            END) AS matched_percentage
                        FROM account_partial_reconcile part
                        LEFT JOIN account_move_line aml ON aml.id = part.credit_move_id
                        LEFT JOIN account_move_line aml2 ON aml2.id = part.debit_move_id
                        RIGHT JOIN (SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account FROM account_move_line GROUP BY move_id, account_id) sub ON (aml2.account_id = sub.account_id AND sub.move_id=aml2.move_id)
                        LEFT JOIN account_account acc ON aml.account_id = acc.id
                        WHERE part.debit_move_id = aml2.id
                        AND acc.reconcile
                        AND aml.move_id IN %s
                        GROUP BY aml2.move_id, aml2.account_id, aml.date
                    )

                    SELECT ''' + select_clause_2 + '''
                    FROM account_move_line "account_move_line"
                    RIGHT JOIN payment_table ref ON ("account_move_line".move_id = ref.matching_move_id)
                    WHERE "account_move_line".account_id NOT IN (SELECT account_id FROM payment_table)
                    AND "account_move_line".move_id NOT IN %s

                    UNION ALL

                    -- Part for the unreconciled journal items.
                    -- Using amount_residual if the account is reconciliable is needed in case of partial reconciliation

                    SELECT ''' + select_clause_1.replace('"account_move_line".balance_cash_basis', 'CASE WHEN acc.reconcile THEN  "account_move_line".amount_residual ELSE "account_move_line".balance END AS balance_cash_basis') + '''
                    FROM account_move_line "account_move_line"
                    LEFT JOIN account_account acc ON "account_move_line".account_id = acc.id
                    WHERE "account_move_line".move_id IN %s
                    AND "account_move_line".account_id NOT IN %s
                )
            '''
            params = [tuple(bank_move_ids)] + [tuple(bank_move_ids)] + [tuple(bank_move_ids)] + [tuple(bank_move_ids)] + [tuple(bank_accounts.ids)]
        elif self.env.context.get('cash_basis'):
            # Cash basis option
            # we need to filter only income/expense accounts which paid under the payment date
            # so we need to generate WITH statement by joining invoice/aml/payments
            user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
            if not user_types:
                return sql, params

            # using psql metadata table, we need to get all columns from account_move_line and need to make sure all columns are fetched
            sql = "SELECT column_name FROM information_schema.columns WHERE table_name='account_move_line'";
            self.env.cr.execute(sql)
            columns = []
            columns_2 = []
            replace_columns = {
                'date': 'ref.date',
                'debit_cash_basis': 'CASE WHEN aml.debit > 0 THEN ref.matched_percentage * aml.debit ELSE 0 END AS debit_cash_basis',
                'credit_cash_basis': 'CASE WHEN aml.credit > 0 THEN ref.matched_percentage * aml.credit ELSE 0 END AS credit_cash_basis',
                'balance_cash_basis': 'ref.matched_percentage * aml.balance AS balance_cash_basis'}
            for field in self.env.cr.fetchall():
                field = field[0]
                columns.append("\"account_move_line\".\"%s\"" % (field,))
                if field in replace_columns:
                    columns_2.append(replace_columns.get(field))
                else:
                    columns_2.append('aml.\"%s\"' % (field,))
            select_clause_1 = ', '.join(columns);
            select_clause_2 = ', '.join(columns_2);

            # get default account.move.line query
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            sql = """WITH account_move_line AS (
              SELECT """ + select_clause_1 + """
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
               SELECT """ + select_clause_2 + """
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params

    def ooa__compute_line(self, currency_table, financial_report, group_by=None, domain=[]):
        # calculate values for unfolded line
        domain = domain and safe_eval(ustr(domain))
        for index, condition in enumerate(domain):
            if condition[0].startswith('tax_ids.'):
                new_condition = (condition[0].partition('.')[2], condition[1], condition[2])
                taxes = self.env['account.tax'].with_context(active_test=False).search([new_condition])
                domain[index] = ('tax_ids', 'in', taxes.ids)
        # get default query from account move line
        tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
        if financial_report.tax_report:
            where_clause += ''' AND "account_move_line".tax_exigible = 't' '''

        line = self
        financial_report = False

        while not financial_report:
            financial_report = line.financial_report_id
            if not line.parent_id:
                break
            line = line.parent_id

        # get with statement to prepend to the sql query
        sql, params = self.ooa__get_with_statement(financial_report)

        select, select_params = self.ooa__query_get_select_sum(currency_table)
        where_params = params + select_params + where_params

        if (self.env.context.get('sum_if_pos') or self.env.context.get('sum_if_neg')) and group_by:
            sql = sql + "SELECT account_move_line." + group_by + " as " + group_by + "," + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY account_move_line." + group_by
            self.env.cr.execute(sql, where_params)
            res = {'balance': 0, 'debit': 0, 'credit': 0, 'amount_residual': 0}
            for row in self.env.cr.dictfetchall():
                if (row['balance'] > 0 and self.env.context.get('sum_if_pos')) or (row['balance'] < 0 and self.env.context.get('sum_if_neg')):
                    for field in ['debit', 'credit', 'balance', 'amount_residual']:
                        res[field] += row[field]
            res['currency_id'] = self.env.user.company_id.currency_id.id
            return res

        # create sql by adding separate parts
        sql = sql + "SELECT " + select + " FROM " + tables + " WHERE " + where_clause
        self.env.cr.execute(sql, where_params)
        results = self.env.cr.dictfetchall()[0]
        results['currency_id'] = self.env.user.company_id.currency_id.id
        return results

    @api.multi
    def ooa__compute_date_range(self):
        # compute dates according to context and line.special_date_changer
        date_from = self._context.get('date_from', False)
        date_to = self._context.get('date_to', False)

        strict_range = self.special_date_changer == 'strict_range'
        if self.special_date_changer == 'from_beginning':
            date_from = False
        if self.special_date_changer == 'to_beginning_of_period' and date_from:
            date_tmp = datetime.strptime(self._context['date_from'], "%Y-%m-%d") - relativedelta(days=1)
            date_to = date_tmp.strftime('%Y-%m-%d')
            date_from = False
        if self.special_date_changer == 'from_fiscalyear' and date_to:
            date_tmp = datetime.strptime(date_to, '%Y-%m-%d')
            date_tmp = self.env.user.company_id.compute_fiscalyear_dates(date_tmp)['date_from']
            date_from = date_tmp.strftime('%Y-%m-%d')
            strict_range = True
        return date_from, date_to, strict_range

    @api.multi
    def ooa_report_move_lines_action(self):
        """
        return necessary action to reach journal items
        when user click sub lines in the report, user will be able to go to the relevant journal item
        """
        domain = safe_eval(self.domain)
        if 'date_from' in self.env.context.get('context', {}):
            if self.env.context['context'].get('date_from'):
                domain = expression.AND([domain, [('date', '>=', self.env.context['context']['date_from'])]])
            if self.env.context['context'].get('date_to'):
                domain = expression.AND([domain, [('date', '<=', self.env.context['context']['date_to'])]])
            if self.env.context['context'].get('state', 'all') == 'posted':
                domain = expression.AND([domain, [('move_id.state', '=', 'posted')]])
            if self.env.context['context'].get('company_ids'):
                domain = expression.AND([domain, [('company_id', 'in', self.env.context['context']['company_ids'])]])
        return {'type': 'ir.actions.act_window',
                'name': 'Journal Items (%s)' % self.name,
                'res_model': 'account.move.line',
                'view_mode': 'tree,form',
                'domain': domain,
                }

    @api.one
    @api.constrains('groupby')
    def ooa__check_same_journal(self):
        """
        check groupby field is contained with account.move.line object
        """
        if self.groupby and self.groupby not in self.env['account.move.line']:
            raise ValidationError(_("Groupby should be a journal item field"))

    def ooa__get_sum(self, currency_table, financial_report, field_names=None):
        # under the given domain, calculate sum of amls
        if not field_names:
            field_names = ['debit', 'credit', 'balance', 'amount_residual']
        res = dict((fn, 0.0) for fn in field_names)
        if self.domain:
            date_from, date_to, strict_range = \
                self.ooa__compute_date_range()
            res = self.with_context(strict_range=strict_range, date_from=date_from, date_to=date_to).ooa__compute_line(currency_table, financial_report, group_by=self.groupby, domain=self.domain)
        return res

    @api.one
    def ooa_get_balance(self, linesDict, currency_table, financial_report, field_names=None):
        """
        compute the balances for the given fields using formulas
        """
        if not field_names:
            field_names = ['debit', 'credit', 'balance']
        res = dict((fn, 0.0) for fn in field_names)
        c = FormulaContext(self.env['account.financial.html.report.line'], linesDict, currency_table, financial_report, self)
        if self.formulas:
            for f in self.formulas.split(';'):
                [field, formula] = f.split('=')
                field = field.strip()
                if field in field_names:
                    try:
                        res[field] = safe_eval(formula, c, nocopy=True)
                    except ValueError as err:
                        if 'division by zero' in err.args[0]:
                            res[field] = 0
                        else:
                            raise err
        return res

    def ooa_get_rows_count(self):
        """
        compute rows count within the date range
        """
        groupby = self.groupby or 'id'
        if groupby not in self.env['account.move.line']:
            raise ValueError(_('Groupby should be a field from account.move.line'))

        # compute date range and send it to default query_get function to get sql query
        date_from, date_to, strict_range = self.ooa__compute_date_range()
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=strict_range, date_from=date_from, date_to=date_to)._query_get(domain=self.domain)

        # combine queries and execure
        query = 'SELECT count(distinct(account_move_line.' + groupby + ')) FROM ' + tables + 'WHERE' + where_clause
        self.env.cr.execute(query, where_params)
        return self.env.cr.dictfetchall()[0]['count']

    def ooa_get_value_from_context(self):
        """
        extract code from the context
        """
        if self.env.context.get('financial_report_line_values'):
            return self.env.context.get('financial_report_line_values').get(self.code, 0)
        return 0

    def ooa__format(self, value):
        """
        return given value with adding relevant format
        """
        if self.env.context.get('no_format'):
            return value
        value['no_format_name'] = value['name']
        if self.figure_type == 'float':
            currency_id = self.env.user.company_id.currency_id
            if currency_id.is_zero(value['name']):
                # don't print -0.0 in reports
                value['name'] = abs(value['name'])
            value['name'] = formatLang(self.env, value['name'], currency_obj=currency_id)
            return value
        if self.figure_type == 'percents':
            value['name'] = str(round(value['name'] * 100, 1)) + '%'
            return value
        value['name'] = round(value['name'], 1)
        return value

    def ooa__get_gb_name(self, gb_id):
        """
        find the related groupby field string
        """
        if self.groupby and self.env['account.move.line']._fields[self.groupby].relational:
            relation = self.env['account.move.line']._fields[self.groupby].comodel_name
            gb = self.env[relation].browse(gb_id)
            return gb.name_get()[0][1] if gb and gb.exists() else _('Undefined')
        return gb_id

    def ooa__build_cmp(self, balance, comp):
        """
         add colors to comparison columns
        """
        if comp != 0:
            res = round((balance - comp) / comp * 100, 1)
            if (res > 0) != (self.green_on_positive and comp > 0):
                return {'name': str(res) + '%', 'class': 'number color-red'}
            else:
                return {'name': str(res) + '%', 'class': 'number color-green'}
        else:
            return {'name': _('n/a')}

    def ooa__split_formulas(self):
        """
         if exist multiple formulas to one line, need to get formulas separately
        """
        result = {}
        if self.formulas:
            for f in self.formulas.split(';'):
                [column, formula] = f.split('=')
                column = column.strip()
                result.update({column: formula})
        return result

    def ooa__eval_formula(self, financial_report, debit_credit, currency_table, linesDict):
        """
         evaluate the formula given in the line and return balances
        """
        debit_credit = debit_credit and financial_report.debit_credit
        # if formula is created by multiple formulas, get those separately
        formulas = self.ooa__split_formulas()
        if self.code and self.code in linesDict:
            res = linesDict[self.code]
        elif formulas and formulas['balance'].strip() == 'count_rows' and self.groupby:
            return {'line': {'balance': self.ooa_get_rows_count()}}
        elif formulas and formulas['balance'].strip() == 'from_context':
            return {'line': {'balance': self.ooa_get_value_from_context()}}
        else:
            res = FormulaLine(self, currency_table, financial_report, linesDict=linesDict)
        vals = {}
        vals['balance'] = res.balance
        if debit_credit:
            vals['credit'] = res.credit
            vals['debit'] = res.debit

        results = {}
        # if exist domain to the line, it means this line is ending line, so we need to calculate account move lines
        # with the given domain
        if self.domain and self.groupby and self.show_domain != 'never':
            aml_obj = self.env['account.move.line']
            tables, where_clause, where_params = aml_obj._query_get(domain=self.domain)
            sql, params = self.ooa__get_with_statement(financial_report)
            if financial_report.tax_report:
                where_clause += ''' AND "account_move_line".tax_exigible = 't' '''

            groupby = self.groupby or 'id'
            if groupby not in self.env['account.move.line']:
                raise ValueError(_('Groupby should be a field from account.move.line'))
            select, select_params = self.ooa__query_get_select_sum(currency_table)
            params += select_params
            sql = sql + "SELECT \"account_move_line\"." + groupby + ", " + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY \"account_move_line\"." + groupby

            params += where_params
            self.env.cr.execute(sql, params)
            results = self.env.cr.fetchall()
            results = dict([(k[0], {'balance': k[1], 'amount_residual': k[2], 'debit': k[3], 'credit': k[4]}) for k in results])
            # get formula context
            c = FormulaContext(self.env['account.financial.html.report.line'], linesDict, currency_table, financial_report, only_sum=True)
            if formulas:
                for key in results:
                    c['sum'] = FormulaLine(results[key], currency_table, financial_report, type='not_computed')
                    c['sum_if_pos'] = FormulaLine(results[key]['balance'] >= 0.0 and results[key] or {'balance': 0.0}, currency_table, financial_report, type='not_computed')
                    c['sum_if_neg'] = FormulaLine(results[key]['balance'] <= 0.0 and results[key] or {'balance': 0.0}, currency_table, financial_report, type='not_computed')
                    for col, formula in formulas.items():
                        if col in results[key]:
                            results[key][col] = safe_eval(formula, c, nocopy=True)
            to_del = []
            for key in results:
                if self.env.user.company_id.currency_id.is_zero(results[key]['balance']):
                    to_del.append(key)
            for key in to_del:
                del results[key]

        results.update({'line': vals})
        return results

    def ooa__put_columns_together(self, data, domain_ids):
        """
         map given data with given domain ids
        """
        res = dict((domain_id, []) for domain_id in domain_ids)
        for period in data:
            debit_credit = False
            if 'debit' in period['line']:
                debit_credit = True
            for domain_id in domain_ids:
                if debit_credit:
                    res[domain_id].append(period.get(domain_id, {'debit': 0})['debit'])
                    res[domain_id].append(period.get(domain_id, {'credit': 0})['credit'])
                res[domain_id].append(period.get(domain_id, {'balance': 0})['balance'])
        return res

    def ooa__divide_line(self, line):
        """
         create two lines from one line
        """
        line1 = {
            'id': line['id'],
            'name': line['name'],
            'level': line['level'],
            'columns': [{'name': ''}] * len(line['columns']),
            'unfoldable': line['unfoldable'],
            'unfolded': line['unfolded'],
        }
        line2 = {
            'id': line['id'],
            'name': _('Total') + ' ' + line['name'],
            'class': 'total',
            'level': line['level'] + 1,
            'columns': line['columns'],
        }
        return [line1, line2]

    @api.multi
    def ooa_get_lines(self, financial_report, currency_table, options, linesDicts):
        """
        return report rows data lines
        """
        final_result_table = []
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods', []) or []
        currency_precision = self.env.user.company_id.currency_id.rounding
        # according to the line hierarchy, create main and sub lines
        for line in self:
            res = []
            debit_credit = len(comparison_table) == 1
            domain_ids = {'line'}
            k = 0
            # build comparison table
            for period in comparison_table:
                date_from = period.get('date_from', False)
                date_to = period.get('date_to', False) or period.get('date', False)
                date_from, date_to, strict_range = line.with_context(date_from=date_from, date_to=date_to).ooa__compute_date_range()
                r = line.with_context(date_from=date_from, date_to=date_to, strict_range=strict_range).ooa__eval_formula(financial_report, debit_credit, currency_table, linesDicts[k])
                debit_credit = False
                res.append(r)
                domain_ids.update(r)
                k += 1
            res = line.ooa__put_columns_together(res, domain_ids)

            if line.hide_if_zero and all([float_is_zero(k, precision_rounding=currency_precision) for k in res['line']]):
                continue

            # get line values and create lines hierarchy with child lines
            vals = {
                'id': line.id,
                'name': line.name,
                'level': line.level,
                'columns': [{'name': l} for l in res['line']],
                'unfoldable': len(domain_ids) > 1 and line.show_domain != 'always',
                'unfolded': line.id in options.get('unfolded_lines', []) or line.show_domain == 'always',
            }

            if line.action_id:
                vals['action_id'] = line.action_id.id
            domain_ids.remove('line')
            lines = [vals]
            groupby = line.groupby or 'aml'
            # set total value by computing lines
            if line.id in options.get('unfolded_lines', []) or line.show_domain == 'always':
                if line.groupby:
                    domain_ids = sorted(list(domain_ids), key=lambda k: line.ooa__get_gb_name(k))
                for domain_id in domain_ids:
                    name = line.ooa__get_gb_name(domain_id)
                    vals = {
                        'id': domain_id,
                        'name': name and len(name) >= 45 and name[0:40] + '...' or name,
                        'level': 4,
                        'parent_id': line.id,
                        'columns': [{'name': l} for l in res[domain_id]],
                        'caret_options': groupby == 'account_id' and 'account.account' or groupby,
                    }
                    if line.financial_report_id.name == 'Aged Receivable':
                        vals['trust'] = self.env['res.partner'].browse([domain_id]).trust
                    lines.append(vals)
                if domain_ids:
                    lines.append({
                        'id': 'total_'+str(line.id),
                        'name': _('Total') + ' ' + line.name,
                        'class': 'o_account_reports_domain_total',
                        'parent_id': line.id,
                        'columns': copy.deepcopy(lines[0]['columns']),
                    })

            for vals in lines:
                if len(comparison_table) == 2:
                    vals['columns'].append(line.ooa__build_cmp(vals['columns'][0]['name'], vals['columns'][1]['name']))
                    for i in [0, 1]:
                        vals['columns'][i] = line.ooa__format(vals['columns'][i])
                else:
                    vals['columns'] = [line.ooa__format(v) for v in vals['columns']]
                if not line.formulas:
                    vals['columns'] = [{'name': ''} for k in vals['columns']]

            # get child lines
            if len(lines) == 1:
                new_lines = line.children_ids.ooa_get_lines(financial_report, currency_table, options, linesDicts)
                if new_lines and line.level > 0 and line.formulas:
                    divided_lines = self.ooa__divide_line(lines[0])
                    result = [divided_lines[0]] + new_lines + [divided_lines[1]]
                else:
                    # append lines according to the main line level
                    result = []
                    if line.level > 0:
                        result += lines
                    result += new_lines
                    if line.level <= 0:
                        result += lines
            else:
                result = lines
            final_result_table += result

        return final_result_table


class FormulaLine(object):
    """
    this class will be used to derive account balances from given object
    """
    def __init__(self, obj, currency_table, financial_report, type='balance', linesDict=None):
        if linesDict is None:
            linesDict = {}
        fields = dict((fn, 0.0) for fn in ['debit', 'credit', 'balance'])
        if type == 'balance':
            fields = obj.ooa_get_balance(linesDict, currency_table, financial_report)[0]
            linesDict[obj.code] = self
        elif type in ['sum', 'sum_if_pos', 'sum_if_neg']:
            if type == 'sum_if_neg':
                obj = obj.with_context(sum_if_neg=True)
            if type == 'sum_if_pos':
                obj = obj.with_context(sum_if_pos=True)
            if obj._name == 'account.financial.html.report.line':
                fields = obj.ooa__get_sum(currency_table, financial_report)
                self.amount_residual = fields['amount_residual']
            elif obj._name == 'account.move.line':
                self.amount_residual = 0.0
                field_names = ['debit', 'credit', 'balance', 'amount_residual']
                res = obj.env['account.financial.html.report.line'].ooa__compute_line(currency_table, financial_report)
                for field in field_names:
                    fields[field] = res[field]
                self.amount_residual = fields['amount_residual']
        elif type == 'not_computed':
            for field in fields:
                fields[field] = obj.get(field, 0)
            self.amount_residual = obj.get('amount_residual', 0)
        elif type == 'null':
            self.amount_residual = 0.0
        self.balance = fields['balance']
        self.credit = fields['credit']
        self.debit = fields['debit']


class FormulaContext(dict):
    """
    report lines are composed with different levels.
    compute account balances according to the line level by using FormulaContext
    """
    def __init__(self, reportLineObj, linesDict, currency_table, financial_report, curObj=None, only_sum=False, *data):
        self.reportLineObj = reportLineObj
        self.curObj = curObj
        self.linesDict = linesDict
        self.currency_table = currency_table
        self.only_sum = only_sum
        self.financial_report = financial_report
        return super(FormulaContext, self).__init__(data)

    def __getitem__(self, item):
        """
        send necessary details to get account balances to the FormulaContext
        """
        formula_items = ['sum', 'sum_if_pos', 'sum_if_neg']
        if item in set(__builtins__.keys()) - set(formula_items):
            return super(FormulaContext, self).__getitem__(item)

        if self.only_sum and item not in formula_items:
            return FormulaLine(self.curObj, self.currency_table, self.financial_report, type='null')
        if self.get(item):
            return super(FormulaContext, self).__getitem__(item)
        if self.linesDict.get(item):
            return self.linesDict[item]
        if item == 'sum':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum')
            self['sum'] = res
            return res
        if item == 'sum_if_pos':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_pos')
            self['sum_if_pos'] = res
            return res
        if item == 'sum_if_neg':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_neg')
            self['sum_if_neg'] = res
            return res
        if item == 'NDays':
            d1 = datetime.strptime(self.curObj.env.context['date_from'], "%Y-%m-%d")
            d2 = datetime.strptime(self.curObj.env.context['date_to'], "%Y-%m-%d")
            res = (d2 - d1).days
            self['NDays'] = res
            return res
        if item == 'count_rows':
            return self.curObj.ooa_get_rows_count()
        if item == 'from_context':
            return self.curObj.ooa_get_value_from_context()
        line_id = self.reportLineObj.search([('code', '=', item)], limit=1)
        if line_id:
            date_from, date_to, strict_range = line_id.ooa__compute_date_range()
            res = FormulaLine(line_id.with_context(strict_range=strict_range, date_from=date_from, date_to=date_to), self.currency_table, self.financial_report, linesDict=self.linesDict)
            self.linesDict[item] = res
            return res
        return super(FormulaContext, self).__getitem__(item)


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.multi
    def _update_translations(self, filter_lang=None):
        # create translations for newly created menu items and actions
        res = super(IrModuleModule, self)._update_translations(filter_lang=filter_lang)

        # create translation for action
        self.env.cr.execute("""
           INSERT INTO ir_translation (lang, type, name, res_id, src, value, module, state)
           SELECT l.code, 'model', 'ir.actions.client,name', a.id, t.src, t.value, t.module, t.state
             FROM account_financial_html_report r
             JOIN ir_act_client a ON (r.name = a.name)
             JOIN ir_translation t ON (t.res_id = r.id AND t.name = 'account.financial.html.report,name')
             JOIN res_lang l on  (l.code = t.lang)
            WHERE NOT EXISTS (
                  SELECT 1 FROM ir_translation tt
                  WHERE (tt.name = 'ir.actions.client,name'
                    AND tt.lang = l.code
                    AND type='model'
                    AND tt.res_id = a.id)
                  )
        """)

        # create translation for menu items
        self.env.cr.execute("""
           INSERT INTO ir_translation (lang, type, name, res_id, src, value, module, state)
           SELECT l.code, 'model', 'ir.ui.menu,name', m.id, t.src, t.value, t.module, t.state
             FROM account_financial_html_report r
             JOIN ir_ui_menu m ON (r.name = m.name)
             JOIN ir_translation t ON (t.res_id = r.id AND t.name = 'account.financial.html.report,name')
             JOIN res_lang l on  (l.code = t.lang)
            WHERE NOT EXISTS (
                  SELECT 1 FROM ir_translation tt
                  WHERE (tt.name = 'ir.ui.menu,name'
                    AND tt.lang = l.code
                    AND type='model'
                    AND tt.res_id = m.id)
                  )
        """)

        return res
