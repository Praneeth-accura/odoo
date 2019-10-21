# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.tools.misc import format_date


class report_account_aged_partner(models.AbstractModel):
    _name = "account.aged.partner"
    _description = "Aged Partner Balances"
    _inherit = 'account.report'

    filter_date = {'date': '', 'filter': 'today'}
    filter_unfold_all = False

    def ooa_get_columns_name(self, options):
        """
        return main columns for partner aged receivable and partner aged payable reports
        """
        columns = [{}]
        columns += [{'name': v, 'class': 'number', 'style': 'white-space:nowrap;'} for v in [
            _("Not&nbsp;due&nbsp;on %s").replace('&nbsp;', ' ') % format_date(self.env, options['date']['date']), 
            _("0&nbsp;-&nbsp;30").replace('&nbsp;', ' '), 
            _("30&nbsp;-&nbsp;60").replace('&nbsp;', ' '), 
            _("60&nbsp;-&nbsp;90").replace('&nbsp;', ' '), 
            _("90&nbsp;-&nbsp;120").replace('&nbsp;', ' '), 
            _("Older"), _("Total")]]
        return columns

    def ooa_get_templates(self):
        """
        return templates for render the report
        """
        templates = super(report_account_aged_partner, self).ooa_get_templates()
        templates['main_template'] = 'account_reports.ooa_template_aged_partner_balance_report'
        try:
            self.env['ir.ui.view'].get_view_id('account_reports.ooa_template_aged_partner_balance_line_report')
            templates['line_template'] = 'account_reports.ooa_template_aged_partner_balance_line_report'
        except ValueError:
            pass
        return templates

    @api.model
    def ooa_get_lines(self, options, line_id=None):
        """
        return report rows data lines
        """
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        # get necessary data to compute report lines
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            # process partner data and append partner to the lines
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': self.ooa_format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            # process partner account move lines
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    # append invoice/bill data to lines
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [line['period'] == 6-i and self.ooa_format_value(sign * line['amount']) or '' for i in range(7)]],
                    }
                    lines.append(vals)
                # process total values for the partner and append to lines
                vals = {
                    'id': values['partner_id'],
                    'class': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'parent_id': 'partner_%s' % (values['partner_id'],),
                    'columns': [{'name': self.ooa_format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                }
                lines.append(vals)
        # process total values for all partners and append it to lines
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 'None',
                'columns': [{'name': self.ooa_format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines


class report_account_aged_receivable(models.AbstractModel):
    _name = "account.aged.receivable"
    _description = "Aged Receivable"
    _inherit = "account.aged.partner"

    def ooa_set_context(self, options):
        """return updated context"""
        ctx = super(report_account_aged_receivable, self).ooa_set_context(options)
        ctx['account_type'] = 'receivable'
        return ctx

    def ooa_get_report_name(self):
        """
        return the name for partner aged receivable report
        """
        return _("Aged Receivable")

    def ooa_get_templates(self):
        """
        return templates for render the report
        """
        templates = super(report_account_aged_receivable, self).ooa_get_templates()
        templates['main_template'] = 'account_reports.ooa_template_aged_receivable_report'
        templates['line_template'] = 'account_reports.ooa_line_template_aged_receivable_report'
        return templates


class report_account_aged_payable(models.AbstractModel):
    _name = "account.aged.payable"
    _description = "Aged Payable"
    _inherit = "account.aged.partner"

    def ooa_set_context(self, options):
        """return updated context"""
        ctx = super(report_account_aged_payable, self).ooa_set_context(options)
        ctx['account_type'] = 'payable'
        ctx['aged_balance'] = True
        return ctx

    def ooa_get_report_name(self):
        """
        return the name for partner aged payable report
        """
        return _("Aged Payable")

    def ooa_get_templates(self):
        """
        return templates for render the report
        """
        templates = super(report_account_aged_payable, self).ooa_get_templates()
        templates['main_template'] = 'account_reports.ooa_template_aged_payable_report'
        templates['line_template'] = 'account_reports.ooa_line_template_aged_payable_report'
        return templates
