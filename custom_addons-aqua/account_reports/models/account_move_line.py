# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    expected_pay_date = fields.Date('Expected Payment Date', help="Expected payment date as manually set through the customer statement (e.g: if you had the customer on the phone and want to remember the date he promised he would pay)")
    internal_note = fields.Text('Internal Note', help="Note you can set through the customer statement about a receivable journal item")
    next_action_date = fields.Date('Next Action Date', help="Date where the next action should be taken for a receivable item. Usually, automatically set when sending reminders through the customer statement.")

    @api.multi
    def ooa_write_blocked(self, blocked):
        # when checked lines in followup report, need to save it in db
        return self.with_context(check_move_validity=False).write({'blocked': blocked})
