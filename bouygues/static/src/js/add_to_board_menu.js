odoo.define('bouygues.AddToBoardMenu', function (require) {
"use strict";

var AddToBoardMenu = require('board.AddToBoardMenu');
var ActionManager = require('web.ActionManager');
var Context = require('web.Context');
var core = require('web.core');
var Domain = require('web.Domain');
var favorites_submenus_registry = require('web.favorites_submenus_registry');
var pyUtils = require('web.py_utils');
var Widget = require('web.Widget');

var _t = core._t;
var QWeb = core.qweb;


AddToBoardMenu.include({

    events: _.extend({}, AddToBoardMenu.prototype.events, {
        'click .o_add_to_board_sale_confirm_button': '_onAddToBoardSaleConfirmButtonClick',
        'click .o_add_to_board_purchase_confirm_button': '_onAddToBoardPurchaseConfirmButtonClick',
        'click .o_add_to_board_stock_confirm_button': '_onAddToBoardStockConfirmButtonClick',
    }),

    _onAddToBoardSaleConfirmButtonClick: function (event) {
        event.preventDefault();
        event.stopPropagation();
        this._addToBoard('/board_sale/add_to_dashboard_sale');
    },

    _onAddToBoardPurchaseConfirmButtonClick: function (event) {
        event.preventDefault();
        event.stopPropagation();
        this._addToBoard('/board_purchase/add_to_dashboard_purchase');
    },

    _onAddToBoardStockConfirmButtonClick: function (event) {
        event.preventDefault();
        event.stopPropagation();
        this._addToBoard('/board_stock/add_to_dashboard_stock');
    },

    _addToBoard: function (routeRpc) {
        var self = this;
        var searchQuery;
        // TO DO: for now the domains in query are evaluated.
        // This should be changed I think.
        this.trigger_up('get_search_query', {
            callback: function (query) {
                searchQuery = query;
            }
        });
        // TO DO: replace direct reference to action manager, controller, and currentAction in code below

        // AAB: trigger_up an event that will be intercepted by the controller,
        // as soon as the controller is the parent of the control panel
        var actionManager = this.findAncestor(function (ancestor) {
            return ancestor instanceof ActionManager;
        });
        var controller = actionManager.getCurrentController();

        var context = new Context(this.action.context);
        context.add(searchQuery.context);
        context.add({
            group_by: searchQuery.groupBy,
            orderedBy: searchQuery.orderedBy,
        });

        this.trigger_up('get_controller_query_params', {
            callback: function (controllerQueryParams) {
                var queryContext = controllerQueryParams.context;
                var allContext = _.extend(
                    _.omit(controllerQueryParams, ['context']),
                    queryContext
                );
                context.add(allContext);
            }
        });

        var domain = new Domain(this.action.domain || []);
        domain = Domain.prototype.normalizeArray(domain.toArray().concat(searchQuery.domain));

        var evalutatedContext = pyUtils.eval('context', context);
        for (var key in evalutatedContext) {
            if (evalutatedContext.hasOwnProperty(key) && /^search_default_/.test(key)) {
                delete evalutatedContext[key];
            }
        }
        evalutatedContext.dashboard_merge_domains_contexts = false;

        var name = this.$input.val();

        this.closeMenu();

        return self._rpc({
                route: routeRpc,
                params: {
                    action_id: self.action.id || false,
                    context_to_save: evalutatedContext,
                    domain: domain,
                    view_mode: controller.viewType,
                    name: name,
                },
            })
            .then(function (r) {
                if (r) {
                    self.do_notify(
                        _.str.sprintf(_t("'%s' added to dashboard"), name),
                        _t('Please refresh your browser for the changes to take effect.')
                    );
                } else {
                    self.do_warn(_t("Could not add filter to dashboard"));
                }
            });
},


});

});
