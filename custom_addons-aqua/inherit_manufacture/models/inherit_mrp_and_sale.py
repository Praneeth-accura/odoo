from odoo import api, fields, models


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    is_done = fields.Boolean(string="Done", default=False)


class InheritMrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    def button_mark_done(self):
        """When a manufacture order is done using MARK AS DONE button, according to the cost it has taken to produce the
        particular item it's cost is updated. In here the super method is called and function is changed"""
        result = super(InheritMrpProduction, self).button_mark_done()  # calling the super method and assigned to result
        total_cost = 0  # total_cost variable is used to hold raw materials cost
        # checking whether the product is eligible for stock automated valuation
        if self.bom_id.product_tmpl_id.categ_id.property_cost_method == 'average' and self.bom_id.product_tmpl_id.categ_id.property_valuation == 'real_time':
            for line in self.move_raw_ids:  # looping all raw materials line
                # assigning the cost of each raw material per product
                total_cost += (line.product_id.standard_price * line.quantity_done) / self.product_qty

        # checking if quantity of product is greater than 0
        if self.bom_id.product_tmpl_id.qty_available > 0:
            # average cost is calculated by. Formula is provided by client (Lahiru Fernando)
            total_standard_price = (total_cost + (self.bom_id.product_tmpl_id.standard_price * self.bom_id.product_tmpl_id.qty_available)) / (self.product_qty + self.bom_id.product_tmpl_id.qty_available)
            # updating the cost of the product
            self.bom_id.product_tmpl_id.write({
                'standard_price': total_standard_price
            })
        else:
            # updating the cost of the product
            self.bom_id.product_tmpl_id.write({
                'standard_price': total_cost
            })
            # returning the function
        return result
