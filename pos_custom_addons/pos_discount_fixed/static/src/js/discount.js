odoo.define('pos_discount_fixed.pos_discount', function (require) {
"use strict";

var screens = require('point_of_sale.screens');

var DiscountButtonFixed = screens.ActionButtonWidget.extend({
    template: 'DiscountButtonFixed',
    button_click: function(){
        var self = this;
        this.gui.show_popup('number',{
            'title': 'Cash Discount',
            'value': this.pos.config.discount_fixed,
            'confirm': function(val) {
                //val = Math.round(Math.max(0,Math.min(10000,val)));
                val = Math.max(0,Math.min(10000,val));
                self.apply_discount_fixed(val);
            },
        });
    },
    apply_discount_fixed: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - pc;

        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },
});

screens.define_action_button({
    'name': 'discount',
    'widget': DiscountButtonFixed,
    'condition': function(){
        return this.pos.config.module_pos_discount && this.pos.config.discount_product_id;
    },
});


});
