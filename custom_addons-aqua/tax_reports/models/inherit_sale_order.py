from odoo import api, fields, models
from num2words import num2words


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.depends('order_line', 'amount_untaxed')
    def _compute_nbt_tax(self):
        if self.order_line:
            first_record = self.order_line[0]  # getting first line of invoice lines
            if first_record.tax_id:  # if there are any records
                for tax in first_record.tax_id:  # getting taxes in each line
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
    spell_total = fields.Char(string='New Price', compute='_compute_spell_price')

    @api.one
    @api.depends('amount_total')
    def _compute_spell_price(self):
        self.spell_total = num2words(self.amount_total).capitalize()

