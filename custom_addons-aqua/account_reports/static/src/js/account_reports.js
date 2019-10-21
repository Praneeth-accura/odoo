odoo.define('account_reports.account_report', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var ControlPanelMixin = require('web.ControlPanelMixin');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');
var ActionManager = require('web.ActionManager');
var datepicker = require('web.datepicker');
var session = require('web.session');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;
var _t = core._t;


var accountReportsWidget = Widget.extend(ControlPanelMixin, {

    // catch events and execute js functions
    events: {
        'click .o_account_reports_summary': 'ooa_edit_summary',
        'click .js_account_report_save_summary': 'ooa_save_summary',
        'click .o_account_reports_footnote_icons': 'ooa_delete_footnote',
        'click .js_account_reports_add_footnote': 'ooa_add_edit_footnote',
        'click .js_account_report_foldable': 'ooa_fold_unfold',
        'click [action]': 'ooa_trigger_action',
    },

    init: function(parent, action) {
        // update meta data related to the report
        this.actionManager = parent;
        // set python model
        this.report_model = action.context.model;
        if (this.report_model === undefined) {
            this.report_model = 'account.report';
        }
        // set financial id related to the report
        this.financial_id = false;
        if (action.context.id) {
            this.financial_id = action.context.id;
        }
        // set context and available options to the report
        this.odoo_context = action.context;
        this.report_options = action.options || false;
        this.ignore_session = action.ignore_session;
        if ((action.ignore_session === 'read' || action.ignore_session === 'both') !== true) {
            var persist_key = 'report:'+this.report_model+':'+this.financial_id+':'+session.company_id;
            this.report_options = JSON.parse(sessionStorage.getItem(persist_key)) || this.report_options;
        }
        return this._super.apply(this, arguments);
    },
    start: function() {
        // load report by getting information from the backend
        var self = this;
        // execute ooa_get_report_information python function to get report data
        var extra_info = this._rpc({
                model: self.report_model,
                method: 'ooa_get_report_informations',
                args: [self.financial_id, self.report_options],
                context: self.odoo_context,
            })
            .then(function(result){
                // after get data from backend send them to extract necessary data
                return self.ooa_parse_reports_informations(result);
            });
        return $.when(extra_info, this._super.apply(this, arguments)).then(function() {
            // after get necessary data need to render the view
            self.ooa_render();
        });
    },
    ooa_parse_reports_informations: function(values) {
        // extract necessary data from values
        this.report_options = values.options;
        this.odoo_context = values.context;
        this.report_manager_id = values.report_manager_id;
        this.footnotes = values.footnotes;
        this.buttons = values.buttons;

        this.main_html = values.main_html;
        this.$searchview_buttons = $(values.searchview_html);
        this.ooa_persist_options();
    },
    ooa_persist_options: function() {
        // create persist key and store
        if ((this.ignore_session === 'write' || this.ignore_session === 'both') !== true) {
            var persist_key = 'report:'+this.report_model+':'+this.financial_id+':'+session.company_id;
            sessionStorage.setItem(persist_key, JSON.stringify(this.report_options));
        }
    },
    // when we go through breadcrumbs need to update control panel
    do_show: function() {
        this._super.apply(this, arguments);
        this.ooa_update_cp();
    },
    // Updates breadcrumbs, buttons and search panel
    ooa_update_cp: function() {
        if (!this.$buttons) {
            this.ooa_renderButtons();
        }
        var status = {
            breadcrumbs: this.actionManager.get_breadcrumbs(),
            cp_content: {$buttons: this.$buttons, $searchview_buttons: this.$searchview_buttons, $pager: this.$pager, $searchview: this.$searchview},
        };
        return this.update_control_panel(status, {clear: true});
    },
    ooa_reload: function() {
        // when reload the report, again need to get data from the backend and render the report
        var self = this;
        return this._rpc({
                model: this.report_model,
                method: 'ooa_get_report_informations',
                args: [self.financial_id, self.report_options],
                context: self.odoo_context,
            })
            .then(function(result){
                self.ooa_parse_reports_informations(result);
                return self.ooa_render();
            });
    },
    ooa_render: function() {
        // render full report view by using separate views
        this.ooa_render_template();
        this.ooa_render_footnotes();
        this.ooa_render_searchview_buttons();
        this.ooa_update_cp();
    },
    ooa_render_template: function() {
        // inject main html coming from the backend, into the this html element
        this.$el.html(this.main_html);
        this.$el.find('.o_account_reports_summary_edit').hide();
    },
    ooa_render_searchview_buttons: function() {
        // inject filter panel into the report
        var self = this;
        // get elements which need to attach datetime pickers and set options to picker
        var $datetimepickers = this.$searchview_buttons.find('.js_account_reports_datetimepicker');
        var options = {
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        // attach datetime pickers to each elements
        $datetimepickers.each(function () {
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this));
            dt.$el.find('input').attr('name', $(this).find('input').attr('name'));
            // update default value if there is one
            if($(this).data('default-value')) {
                dt.setValue(moment($(this).data('default-value')));
            }
        });
        // update date format according to user language
        _.each(this.$searchview_buttons.find('.js_format_date'), function(dt) {
            var date_value = $(dt).html();
            $(dt).html((new moment(date_value)).format('ll'));
        });
        // collapse menus
        this.$searchview_buttons.find('.js_foldable_trigger').click(function (event) {
            $(this).toggleClass('o_closed_menu o_open_menu');
            self.$searchview_buttons.find('.o_foldable_menu[data-filter="'+$(this).data('filter')+'"]').toggleClass('o_closed_menu o_open_menu');
        });
        // selected filters are marked by adding selected class into relevant options
        _.each(self.report_options, function(k) {
            if (k!== null && k.filter !== undefined) {
                self.$searchview_buttons.find('[data-filter="'+k.filter+'"]').addClass('selected');
            }
        });
        // set default values to filters
        _.each(this.$searchview_buttons.find('.js_account_report_bool_filter'), function(k) {
            $(k).toggleClass('selected', self.report_options[$(k).data('filter')]);
        });
        _.each(this.$searchview_buttons.find('.js_account_report_choice_filter'), function(k) {
            $(k).toggleClass('selected', (_.filter(self.report_options[$(k).data('filter')], function(el){return ''+el.id == ''+$(k).data('id') && el.selected === true;})).length > 0);
        });
        _.each(this.$searchview_buttons.find('.js_account_reports_one_choice_filter'), function(k) {
            $(k).toggleClass('selected', ''+self.report_options[$(k).data('filter')] === ''+$(k).data('id'));
        });
        // date filter
        this.$searchview_buttons.find('.js_account_report_date_filter').click(function (event) {
            self.report_options.date.filter = $(this).data('filter');
            var error = false;
            if ($(this).data('filter') === 'custom') {
                var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                if (date_from.length > 0){
                    error = date_from.val() === "" || date_to.val() === "";
                    self.report_options.date.date_from = field_utils.parse.date(date_from.val());
                    self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                }
                else {
                    error = date_to.val() === "";
                    self.report_options.date.date = field_utils.parse.date(date_to.val());
                }
            }
            if (error) {
                crash_manager.show_warning({data: {message: _t('Date cannot be empty')}});
            } else {
                self.ooa_reload();
            }
        });
        // options: accrual basis/cash basis, posted entries only, unfold all
        this.$searchview_buttons.find('.js_account_report_bool_filter').click(function (event) {
            var option_value = $(this).data('filter');
            self.report_options[option_value] = !self.report_options[option_value];
            if (option_value === 'unfold_all') {
                self.ooa_unfold_all(self.report_options[option_value]);
            }
            self.ooa_reload();
        });
        // journal filter
        this.$searchview_buttons.find('.js_account_report_choice_filter').click(function (event) {
            var option_value = $(this).data('filter');
            var option_id = $(this).data('id');
            _.filter(self.report_options[option_value], function(el) {
                if (''+el.id == ''+option_id){
                    if (el.selected === undefined || el.selected === null){el.selected = false;}
                    el.selected = !el.selected;
                }
                return el;
            });
            self.ooa_reload();
        });
        this.$searchview_buttons.find('.js_account_reports_one_choice_filter').click(function (event) {
            self.report_options[$(this).data('filter')] = $(this).data('id');
            self.ooa_reload();
        });
        // comparison filter
        this.$searchview_buttons.find('.js_account_report_date_cmp_filter').click(function (event){
            self.report_options.comparison.filter = $(this).data('filter');
            var error = false;
            var number_period = $(this).parent().find('input[name="periods_number"]');
            self.report_options.comparison.number_period = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
            if ($(this).data('filter') === 'custom') {
                var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from_cmp"]');
                var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to_cmp"]');
                if (date_from.length > 0){
                    error = date_from.val() === "" || date_to.val() === "";
                    self.report_options.comparison.date_from = field_utils.parse.date(date_from.val());
                    self.report_options.comparison.date_to = field_utils.parse.date(date_to.val());
                }
                else {
                    error = date_to.val() === "";
                    self.report_options.comparison.date = field_utils.parse.date(date_to.val());
                }
            }
            if (error) {
                crash_manager.show_warning({data: {message: _t('Date cannot be empty')}});
            } else {
                self.ooa_reload();
            }
        });
        // analytic accounts and analytic tags filter
        this.$searchview_buttons.find('.js_account_reports_analytic_auto_complete').select2();
        if (self.report_options.analytic) {
            self.$searchview_buttons.find('[data-filter="analytic_accounts"]').select2("val", self.report_options.analytic_accounts);
            self.$searchview_buttons.find('[data-filter="analytic_tags"]').select2("val", self.report_options.analytic_tags);
        }
        this.$searchview_buttons.find('.js_account_reports_analytic_auto_complete').on('change', function(){
            self.report_options.analytic_accounts = self.$searchview_buttons.find('[data-filter="analytic_accounts"]').val();
            self.report_options.analytic_tags = self.$searchview_buttons.find('[data-filter="analytic_tags"]').val();
            return self.ooa_reload().then(function(){
                self.$searchview_buttons.find('.account_analytic_filter').click();
            })
        });
    },
    ooa_format_date: function(moment_date) {
        // change given date's format
        var date_format = 'YYYY-MM-DD';
        return moment_date.format(date_format);
    },
    ooa_renderButtons: function() {
        // add buttons to the report
        var self = this;
        this.$buttons = $(QWeb.render("accountReports.buttons", {buttons: this.buttons}));
        // bind actions with relevant buttons
        _.each(this.$buttons.siblings('button'), function(el) {
            $(el).click(function() {
                return self._rpc({
                        model: self.report_model,
                        method: $(el).attr('action'),
                        args: [self.financial_id, self.report_options],
                        context: self.odoo_context,
                    })
                    .then(function(result){
                        return self.do_action(result);
                    });
            });
        });
        return this.$buttons;
    },
    ooa_edit_summary: function(e) {
        // render text area to add user inputs
        var $textarea = $(e.target).parents('.o_account_reports_body').find('textarea[name="summary"]');
        var height = Math.max($(e.target).parents('.o_account_reports_body').find('.o_account_report_summary').height(), 100); // get the max value from current height and 100
        var text = $textarea.val().replace(new RegExp('<br />', 'g'), '\n'); // replace unnecessary items in text
        $textarea.height(height); // update calculated height
        $textarea.val(text);
        $(e.target).parents('.o_account_reports_body').find('.o_account_reports_summary_edit').show();
        $(e.target).parents('.o_account_reports_body').find('.o_account_reports_summary').hide();
        $(e.target).parents('.o_account_reports_body').find('textarea[name="summary"]').focus();
    },
    ooa_save_summary: function(e) {
        // save user entered text in the database and hide the text area
        var self = this;
        var text = $(e.target).siblings().val().replace(/[ \t]+/g, ' ');
        // send user entered data to the backend for store in db
        return this._rpc({
                model: 'account.report.manager',
                method: 'write',
                args: [this.report_manager_id, {summary: text}],
                context: this.odoo_context,
            })
            .then(function(result){
                // hide the text area
                self.$el.find('.o_account_reports_summary_edit').hide();
                self.$el.find('.o_account_reports_summary').show();
                if (!text) {
                    var $content = $("<input type='text' class='o_input' name='summary'/>");
                    $content.attr('placeholder', _t('Click to add an introductory explanation'));
                } else {
                    var $content = $('<span />').text(text).html(function (i, value) {
                        return value.replace(/\n/g, '<br>\n');
                    });
                }
                return $(e.target).parent().siblings('.o_account_reports_summary').find('> .o_account_report_summary').html($content);
            });
    },
    ooa_render_footnotes: function() {
        // footnotes will be shown only to unfolded lines
        var self = this;
        var $dom_footnotes = self.$el.find('.js_account_report_line_footnote:not(.folded)');
        $dom_footnotes.html('');
        var number = 1;
        var footnote_to_render = [];
        _.each($dom_footnotes, function(el) {
            var line_id = $(el).data('id');
            var footnote = _.filter(self.footnotes, function(footnote) {return ''+footnote.line === ''+line_id;});
            if (footnote.length !== 0) {
                // show foot note in unfold line
                $(el).html('<sup><b class="o_account_reports_footnote_sup"><a href="#footnote'+number+'">'+number+'</a></b></sup>');
                footnote[0].number = number;
                number += 1;
                footnote_to_render.push(footnote[0]);
            }
        });
        // show all footnotes in below section
        return this._rpc({
                model: this.report_model,
                method: 'ooa_get_html_footnotes',
                args: [self.financial_id, footnote_to_render],
                context: self.odoo_context,
            })
            .then(function(result){
                return self.$el.find('.js_account_report_footnotes').html(result);
            });
    },
    ooa_add_edit_footnote: function(e) {
        // if already exists footnote for line load it to new popup window,
        // otherwise load new empty popup window
        var self = this;
        var line_id = $(e.target).data('id');
        // check existence of footnotes for current line
        var existing_footnote = _.filter(self.footnotes, function(footnote) {
            return ''+footnote.line === ''+line_id;
        })
        var text = '';
        if (existing_footnote.length !== 0) {
            text = existing_footnote[0].text;
        }
        var $content = $(QWeb.render('accountReports.footnote_dialog', {text: text, line: line_id}));
        var save = function() {
            var footnote_text = $('.js_account_reports_footnote_note').val().replace(/[ \t]+/g, ' ');
            if (!footnote_text && existing_footnote.length === 0) {return;}
            if (existing_footnote.length !== 0) {
                if (!footnote_text) {
                    return self.$el.find('.footnote[data-id="'+existing_footnote[0].id+'"] .o_account_reports_footnote_icons').click();
                }
                // update new footnote
                return this._rpc({
                        model: 'account.report.footnote',
                        method: 'write',
                        args: [existing_footnote[0].id, {text: footnote_text}],
                        context: this.odoo_context,
                    })
                    .then(function(result){
                        _.each(self.footnotes, function(footnote) {
                            if (footnote.id === existing_footnote[0].id){
                                footnote.text = footnote_text;
                            }
                        });
                        return self.ooa_render_footnotes();
                    });
            }
            else {
                // create new footnote
                return this._rpc({
                        model: 'account.report.footnote',
                        method: 'create',
                        args: [{line: line_id, text: footnote_text, manager_id: self.report_manager_id}],
                        context: this.odoo_context,
                    })
                    .then(function(result){
                        self.footnotes.push({id: result, line: line_id, text: footnote_text});
                        return self.ooa_render_footnotes();
                    });
            }
        };
        new Dialog(this, {title: 'Annotate', size: 'medium', $content: $content, buttons: [{text: 'Save', classes: 'btn-primary', close: true, click: save}, {text: 'Cancel', close: true}]}).open();
    },
    ooa_delete_footnote: function(e) {
        // if user delete footnote need to delete it from the db and re render the footnotes
        var self = this;
        var footnote_id = $(e.target).parents('.footnote').data('id');
        return this._rpc({
                model: 'account.report.footnote',
                method: 'unlink',
                args: [footnote_id],
                context: this.odoo_context,
            })
            .then(function(result){
                // remove footnote from current footnotes
                self.footnotes = _.filter(self.footnotes, function(element) {
                    return element.id !== footnote_id;
                });
                return self.ooa_render_footnotes();
            });
    },
    ooa_fold_unfold: function(e) {
        // when user click on the foldable line, this function will be executed
        // if it is already folded, execute ooa_unfold function to unfold the line
        // if it is already unfolded, execute ooa_fold function to fold the line
        var self = this;
        if ($(e.target).hasClass('caret') || $(e.target).parents('.o_account_reports_footnote_sup').length > 0){return;}
        e.stopPropagation();
        e.preventDefault();
        var line = $(e.target).parents('td');
        if (line.length === 0) {line = $(e.target);}
        var method = line.data('unfolded') === 'True' ? this.ooa_fold(line) : this.ooa_unfold(line);
        $.when(method).then(function() {
            self.ooa_render_footnotes();
            self.ooa_persist_options();
        });
    },
    ooa_fold: function(line) {
        // fold the given line and children lines
        var self = this;
        var line_id = line.data('id');
        line.find('.fa-caret-down').toggleClass('fa-caret-right fa-caret-down');
        line.toggleClass('folded');
        var $lines_to_hide = this.$el.find('tr[data-parent-id="'+line_id+'"]');
        var index = self.report_options.unfolded_lines.indexOf(line_id);
        if (index > -1) {
            self.report_options.unfolded_lines.splice(index, 1);
        }
        if ($lines_to_hide.length > 0) {
            line.data('unfolded', 'False');
            $lines_to_hide.find('.js_account_report_line_footnote').addClass('folded');
            $lines_to_hide.hide();
            _.each($lines_to_hide, function(el){
                var child = $(el).find('[data-id]:first');
                if (child) {
                    self.ooa_fold(child);
                }
            })
        }
        return false;
    },
    ooa_unfold: function(line) {
        // unfold the given line
        var self = this;
        var line_id = line.data('id');
        line.toggleClass('folded');
        self.report_options.unfolded_lines.push(line_id);
        var $lines_in_dom = this.$el.find('tr[data-parent-id="'+line_id+'"]');
        if ($lines_in_dom.length > 0) {
            $lines_in_dom.find('.js_account_report_line_footnote').removeClass('folded');
            $lines_in_dom.show();
            line.find('.fa-caret-right').toggleClass('fa-caret-right fa-caret-down');
            line.data('unfolded', 'True');
            return true;
        }
        else {
            return this._rpc({
                    model: this.report_model,
                    method: 'ooa_get_html',
                    args: [self.financial_id, self.report_options, line.data('id')],
                    context: self.odoo_context,
                })
                .then(function(result){
                    $(line).parent('tr').replaceWith(result);
                });
        }
    },
    ooa_unfold_all: function(bool) {
        // if user click unfold all in the filter panel, unfold all lines
        var self = this;
        var lines = this.$el.find('.js_account_report_foldable');
        self.report_options.unfolded_lines = [];
        if (bool) {
            _.each(lines, function(el) {
                self.report_options.unfolded_lines.push($(el).data('id'));
            });
        }
    },
    ooa_trigger_action: function(e) {
        // if user click on element with embedded action, this function will be executed
        e.stopPropagation();
        var self = this;
        var action = $(e.target).attr('action');
        var id = $(e.target).parents('td').data('id');
        var params = $(e.target).data();
        if (action) {
            // execute given python function in action attribute
            return this._rpc({
                    model: this.report_model,
                    method: action,
                    args: [this.financial_id, this.report_options, params],
                    context: this.odoo_context,
                })
                .then(function(result){
                    return self.do_action(result);
                });
        }
    },
});

ActionManager.include({
    ooa_ir_actions_account_report_download: function(action, options) {
        // new action type for download reports
        // this function will request to the given url for the report
        // if occur any error, crash manager will handle it
        var self = this;
        var c = crash_manager;
        return $.Deferred(function (d) {
            self.getSession().get_file({
                url: '/account_reports',
                data: action.data,
                complete: framework.unblockUI,
                success: function(){
                    if (!self.dialog) {
                        options.on_close();
                    }
                    self.dialog_stop();
                    d.resolve();
                },
                error: function () {
                    c.rpc_error.apply(c, arguments);
                    d.reject();
                }
            });
        });
    }
});

core.action_registry.add('account_report', accountReportsWidget);
return accountReportsWidget;
});
