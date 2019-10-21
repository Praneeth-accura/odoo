from odoo import models, api, fields
from odoo.exceptions import UserError
import num2words


class AccountExpense(models.Model):
    _name = 'account.expense'

    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    journal = fields.Many2one('account.journal', string="Bank")
    reference = fields.Char(string="Reference")
    line_ids = fields.One2many('expense.lines', 'line_id')
    state = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default='draft')
    journal_entry_id = fields.Many2one('account.move', string="Journal Entry")
    code = fields.Char(related='journal.code')
    partner_id = fields.Many2one('res.partner', string="Vendor", domain=[('supplier', '=', True)])
    check_no = fields.Char(string="Check Number")
    amount_in_words = fields.Char(string="Amount in words", compute='get_amount_in_words', store=True)
    total_amount = fields.Float(string="Total", compute='get_total', store=True)

    @api.one
    @api.depends('line_ids.debit')
    def get_total(self):
        total = 0
        for line in self.line_ids:
            total += line.debit
        self.total_amount = total

    @api.one
    @api.depends('total_amount')
    def get_amount_in_words(self):
        total = 0
        for line in self.line_ids:
            total += line.debit
        self.amount_in_words = str(num2words.num2words(total)).capitalize()


    @api.model
    def create(self, vals):
        """set ae.no code to the name field and return super class"""
        vals['name'] = vals['code'] + '/' + str(self.env['ir.sequence'].next_by_code('ae.no'))  # assigning next sequence number to name
        return super(AccountExpense, self).create(vals)  # calling super function

    def post_expense(self):
        if not self.line_ids:
            raise UserError("You cannot POST this without adding any Items")

        """Once this function is triggered a journal entry is created for the expense and the journal entry is posted"""
        journal_entry = self.env['account.move'].create({  # creating journal entry
            'date': self.date,
            'journal_id': self.journal.id,
            'reference': self.name,
        })

        # collecting all the debit amount
        total_debited = 0

        # creating a journal entry line for each line
        for line in self.line_ids:
            total_debited += line.debit  # adding all debit amount to the above variable
            # calling the below function to create lines. Here all accounts are debited.
            self.create_journal_lines(journal_entry, line.account_id.id, self.partner_id.id, line.analytic_account_id.id, line.analytic_tag_ids, type='debit', amount=line.debit)

        # calling the below function to create lines. Here all accounts are credited.
        self.create_journal_lines(journal_entry, self.journal.default_credit_account_id.id, partner=None, analytic_account=None, analytic_tags=None, type='credit', amount=total_debited)

        # posting the journal entry
        journal_entry.post()

        # updating the record and moving it to the post stage
        self.write({
            'state': 'post',
            'journal_entry_id': journal_entry.id
        })

    # This function is used to create lines. this function will be called when ever a journal entry line is created in
    # this class.
    def create_journal_lines(self, journal_entry, account, partner, analytic_account, analytic_tags, type, amount):
        journal_entry.line_ids.create({
            'account_id': account,
            'partner_id': partner,
            'analytic_account_id': analytic_account,
            'analytic_tag_ids': [(6, 0, analytic_tags.ids)] if analytic_tags else None,
            'debit': amount if type == 'debit' else 0,
            'credit': amount if type == 'credit' else 0,
            'move_id': journal_entry.id,
            'state': 'posted'
        })

    @api.multi
    def action_view_journal_entry(self):
        """This function redirects to the journal entries view and shows only records that are equal to the record"""
        # getting the action of transfers view
        journal_entry_action = self.env.ref('account.action_move_journal_line')
        action = journal_entry_action.read()[0]
        # adding a domain to the view to filter records
        action['domain'] = [('id', '=', self.journal_entry_id.id)]
        return action


class ExpenseLines(models.Model):
    _name = 'expense.lines'

    name = fields.Char(string="Description")
    account_id = fields.Many2one('account.account', string="Account")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")
    debit = fields.Float(string="Amount")
    line_id = fields.Many2one('account.expense')
