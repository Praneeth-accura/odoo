odoo.define('pos_cashier.cashier', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var core = require('web.core');

var QWeb = core.qweb;
var _t = core._t;

// Overwrite click username function to change the title of the pop up
chrome.UsernameWidget.include({
	click_username: function(){
		console.log(this.session);
        var self = this;
        this.gui.select_user({
            'security':     true,
            'current_user': this.pos.get_cashier(),
            'title':      _t('Change Salesperson'),
        }).then(function(user){
            self.pos.set_cashier(user);
            self.renderElement();
        });
    }
});

/*---------- Cashier Widget-------------- */
var CashierWidget = PosBaseWidget.extend({
    template: 'CashierWidget',
    init: function(parent, options){
        options = options || {};
        this._super(parent,options);
    },
    renderElement: function(){
        var self = this;
        this._super();

//        this.$el.click(function(){
//            self.click_cashier();
//        });
    },
    click_cashier: function(){
        var self = this;
        this.gui.select_user({
            'security':     true,
            'current_user': this.pos.get_cashier(),
            'title':      _t('Change Cashier'),
        }).then(function(user){
            self.pos.set_cashier(user);
            self.renderElement();
        });
    },
    get_cashier_name: function(){
        var user = this.pos.cashier || this.pos.user;
        if(user){
            return user.name;
        }else{
            return "";
        }
    },
});

chrome.Chrome.include({
	build_widgets: function(){
		chrome.Chrome.prototype.widgets.push({
	        'name':   'pos_cashier',
	        'widget': CashierWidget,
	        'replace':  '.placeholder-CashierWidget',
	        'append':  '.pos-rightheader',
	    	});
        this._super();
    },
});

return {
    CashierWidget: CashierWidget
};
});