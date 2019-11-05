from odoo import api, fields, models


class InheritAccounts(models.Model):
    _inherit = 'account.invoice'

    type_of_customer = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string="Type")
    crusdec_id = fields.Integer(string="Cusdec Serial ID")
    crusdec_date = fields.Date(string="Cusdec Reg Date")
    crusdec_office_id = fields.Char(string="Cusdec Office ID")
    vat_disallowed = fields.Char(string="Cusdec Office ID")

    @api.one
    @api.depends('invoice_line_ids', 'amount_untaxed')
    def _compute_nbt_tax(self):
        """Computing nbt tax"""
        if self.invoice_line_ids:
            first_record = self.invoice_line_ids[0]  # getting first line of invoice lines
            if first_record.invoice_line_tax_ids:  # if there are any records
                for tax in first_record.invoice_line_tax_ids:  # getting taxes in each line
                    if tax.is_nbt:  # if the tax is nbt
                        if tax.amount_type == 'fixed':  # if the value is fixed
                            amount = tax.amount
                            self.nbt_tax = amount
                        elif tax.amount_type == 'percent':  # if the value is percentage
                            amount = tax.amount / 100  # tax amount is divided by 100
                            self.nbt_tax = self.amount_untaxed * amount
                        break  # breaking loop

    @api.one
    @api.depends('nbt_tax', 'amount_untaxed', 'amount_tax')
    def _compute_normal_tax(self):
        """computing normal tax excluding nbt_tax from overall tax"""
        self.normal_tax = self.amount_tax - self.nbt_tax

    nbt_tax = fields.Float(string='NBT', compute='_compute_nbt_tax')
    normal_tax = fields.Float(string='VAT', compute='_compute_normal_tax')


class InheritAccountTax(models.Model):
    _inherit = 'account.tax'

    is_nbt = fields.Boolean(string='NBT', default=False)