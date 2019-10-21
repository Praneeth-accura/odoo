from odoo import fields, api, models


class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    check_no = fields.Char(string="Check No")