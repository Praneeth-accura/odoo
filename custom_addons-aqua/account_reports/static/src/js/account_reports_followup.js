odoo.define('account_reports.account_report_followup', function (require) {
'use strict';

var core = require('web.core');
var Pager = require('web.Pager');
var datepicker = require('web.datepicker');
var Dialog = require('web.Dialog');
var account_report = require('account_reports.account_report');

var QWeb = core.qweb;

var account_report_followup = account_report.extend({
    // catch events and execute js functions
    events: _.defaults({
        'click .changeTrust': 'ooa_change_trust',
        'click .js_change_date': 'ooa_display_exp_note_modal',
        'click .followup-email': 'ooa_send_followup_email',
        'click .followup-letter': 'ooa_print_pdf',
        'click .o_account_reports_followup_skip': 'ooa_skip_partner',
        'click .o_account_reports_followup_done': 'ooa_done_partner',
        'click .o_account_reports_followup-auto': 'ooa_enable_auto',
        "change *[name='blocked']": 'on_change_blocked',
        'click .o_account_reports_followup-set-next-action': 'ooa_set_next_action',
    }, account_report.prototype.events),
    init: function(parent, action) {
        // update meta data related to the report
        this._super.apply(this, arguments);
        this.ignore_session = 'both';
    },
    ooa_parse_reports_informations: function(values) {
        // extract necessary data from values
        this.map_partner_manager = values.map_partner_manager;
        return this._super(values);
    },
    ooa_render: function() {
        // render full report view by using separate views
        if (this.report_options.partners_to_show){
            this.ooa_renderPager();
            this.ooa_render_searchview();
        }
        this._super();
    },
    ooa_renderPager: function() {
        // render customer report view with pagination
        var self = this;
        var pager = new Pager(this, this.report_options.total_pager, this.report_options.pager, 1);
        pager.appendTo($('<div>'));
        this.$pager = pager.$el;
        pager.on('pager_changed', this, function (state) {
            self.report_options.pager = state.current_min;
            self.ooa_reload();
        });
        return this.$pager;
    },
    ooa_render_searchview: function() {
        // render customized filtering panel to the customer statement report
        this.$searchview = $(QWeb.render("accountReports.followupProgressbar", {options: this.report_options}));
    },
    ooa_change_trust: function(e) {
        // if user select one of trust item, need to save it on related partner in db
        var partner_id = $(e.target).parents('span.dropdown').data("partner");
        var newTrust = $(e.target).data("new-trust");
        if (!newTrust) {
            newTrust = $(e.target).parents('a.changeTrust').data("new-trust");
        }
        var color = 'grey';
        switch(newTrust) {
            case 'good':
                color = 'green';
                break;
            case 'bad':
                color = 'red';
                break;
        }
        // save new partner trust data in db by calling backend write function
        return this._rpc({
                model: 'res.partner',
                method: 'write',
                args: [[parseInt(partner_id, 10)], {'trust': newTrust}],
            })
            .then(function () {
                // update new partner trust in the view
                $(e.target).parents('span.dropdown').find('i.oe-account_followup-trust').attr('style', 'color: ' + color + '; font-size: 0.8em;');
            });
    },
    ooa_display_done: function(e) {
        // remove "Do it later" button and add "Done" button
        $(e.target).parents('.o_account_reports_body').find("div.o_account_reports_page").find(".alert.alert-info.alert-dismissible").remove();
        $(e.target).parents('.o_account_reports_body').find('#action-buttons').addClass('o_account_reports_followup_clicked');
        if ($(e.target).hasClass('btn-primary')){
            $(e.target).toggleClass('btn-primary btn-default');
        }
    },
    ooa_send_followup_email: function(e) {
        // when user click "Send by email" button, execute backend function to send email
        var self = this;
        var partner_id = $(e.target).data('partner');
        this.report_options['partner_id'] = partner_id;
        return this._rpc({  // sending the email
                model: this.report_model,
                method: 'ooa_send_email',
                args: [this.report_options],
            })
            .then(function (result) { // display success message
                self.ooa_display_done(e);
                $(e.target).parents("div.o_account_reports_page").prepend(QWeb.render("emailSent"));
            });
    },
    ooa_print_pdf: function(e) {
        // when user click "Print Letter" button, show "Done" button
        this.ooa_display_done(e);
    },
    ooa_done_partner: function(e) {
        // when user click "Done" button, execute backend function to save data in the db and update the progress bar
        var partner_id = $(e.target).data("partner");
        var self = this;
        // send data to the backend
        return this._rpc({
                model: 'res.partner',
                method: 'ooa_update_next_action',
                args: [[parseInt(partner_id)]],
            })
            .then(function () { // update the progress bar
                if (self.report_options.progressbar) {
                    self.report_options.progressbar[0] += 1;
                }
                self.ooa_reload();
            });
    },
    on_change_blocked: function(e) {
        // if user tick or untick "Excluded", need to update it in the db and update it on the view
        var checkbox = $(e.target).is(":checked");
        var target_id = $(e.target).parents('tr').find('td[data-id]').data('id');
        return this._rpc({ // update the db
                model: 'account.move.line',
                method: 'ooa_write_blocked',
                args: [[parseInt(target_id)], checkbox],
            })
            .then(function(result){
                // update view
                if (checkbox) {
                    $(e.target).parents('tr').addClass('o_account_followup_blocked');
                }
                else {
                    $(e.target).parents('tr').removeClass('o_account_followup_blocked');
                }
            });
    },
    // show popup menu for select next action date
    ooa_set_next_action: function(e) {
        // if user click "Log a Note" or "Manual" button, show popup wizard for input data
        var self = this;
        var partner_id = $(e.target).data('partner');
        var $content = $(QWeb.render("nextActionForm", {target_id: partner_id}));
        var nextActionDatePicker = new datepicker.DateWidget(this);
        nextActionDatePicker.appendTo($content.find('div.o_account_reports_next_action_date_picker'));
        nextActionDatePicker.setValue(moment());

        var changeDate = function (e) {
            var dt = new Date();
            switch($(e.target).data('time')) { // select the date
                case 'one-week':
                    dt.setDate(dt.getDate() + 7);
                    break;
                case 'two-weeks':
                    dt.setDate(dt.getDate() + 14);
                    break;
                case 'one-month':
                    dt.setMonth(dt.getMonth() + 1);
                    break;
                case 'two-months':
                    dt.setMonth(dt.getMonth() + 2);
                    break;
            }
            nextActionDatePicker.setValue(moment(dt));
        };
        $content.find('.o_account_reports_followup_next_action_date_button').bind('click', changeDate);

        // extract user entered data and send them into backend for store in db
        var save = function () {
            var note = $content.find(".o_account_reports_next_action_note").val().replace(/\r?\n/g, '<br />').replace(/\s+/g, ' ');
            var date = nextActionDatePicker.getValue();
            var target_id = $content.find("#target_id").val();
            if (self.$el.find('.o_account_reports_followup-manual').hasClass('btn-default')){
                // activate "Manual" button and deactivate "Auto" button
                self.ooa_toggle_auto_manual(e);
            }
            // update db
            return this._rpc({
                model: self.report_model,
                method: 'ooa_change_next_action',
                args: [parseInt(target_id), date, note],
            });
        };
        // render dialog box
        new Dialog(this, {size: 'medium', $content: $content, buttons: [{text: 'Save', classes: 'btn-primary', close: true, click: save}, {text: 'Cancel', close: true}]}).open();
    },
    ooa_enable_auto: function(e) {
        // set today as next action date and update buttons
        var partner_id = $(e.target).data('partner');
        if ($(e.target).parents('.alert').length > 0) {
            $(e.target).hide();
        }
        if ($(e.target).parents('.o_account_reports_body').find('.o_account_reports_followup-auto:last').hasClass('btn-default')){
            // activate "Auto" button and deactivate "manual" button
            this.ooa_toggle_auto_manual(e);
            return this._rpc({
                model: this.report_model,
                method: 'ooa_change_next_action',
                args: [parseInt(partner_id), this.ooa_format_date(new moment()), ''],
            });
        }
    },
    ooa_toggle_auto_manual: function(e) {
        $(e.target).parents('.o_account_reports_body').find('.o_account_reports_followup-manual').toggleClass('btn-default btn-info'); // Change the highlighted buttons
        $(e.target).parents('.o_account_reports_body').find('.o_account_reports_followup-auto:last').toggleClass('btn-default btn-info'); // Change the highlighted buttons
    },
    ooa_display_exp_note_modal: function(e) {
        // when user click "Change expected payment date/note" show wizard
        var self = this;
        var target_id = $(e.target).data('id');
        var $content = $(QWeb.render("paymentDateForm", {target_id: target_id}));
        var paymentDatePicker = new datepicker.DateWidget(this);
        paymentDatePicker.appendTo($content.find('div.o_account_reports_payment_date_picker'));

        // extract user entered data and send them into backend for store in db
        var save = function () {
            var note = $content.find("#internalNote").val().replace(/\r?\n/g, '<br />').replace(/\s+/g, ' ');
            var date = paymentDatePicker.getValue();
            return this._rpc({
                    model: 'account.move.line',
                    method: 'write',
                    args: [[parseInt($content.find("#target_id").val())], {expected_pay_date: date, internal_note: note}],
                })
                .then(function () {
                    return self.ooa_reload();
                });
        };
        // render dialog box
        new Dialog(this, {title: 'Odoo', size: 'medium', $content: $content, buttons: [{text: 'Save', classes: 'btn-primary', close: true, click: save}, {text: 'Cancel', close: true}]}).open();
    },
    ooa_save_summary: function(e) {
        // save user entered text in the database and hide the text area
        if (this.report_options.partners_to_show){
            var partner_id = $(e.target).data('id');
            this.report_manager_id = this.map_partner_manager[partner_id];
        }
        return this._super(e);
    },
    ooa_skip_partner: function(e) {
        // when user click "Do it Later" button, current partner will be disappeared from the current customer statements
        var partner_id = $(e.target).data('id');
        this.report_options.skipped_partners.push(partner_id);
        this.ooa_reload();
    },
});
core.action_registry.add("account_report_followup", account_report_followup);
return account_report_followup;
});
