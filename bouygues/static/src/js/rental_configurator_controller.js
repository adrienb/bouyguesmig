odoo.define('bouygues.RentalConfiguratorFormController', function (require) {
"use strict";

var RentalConfiguratorFormController = require('sale_renting.RentalConfiguratorFormController');

/**
 * This controller is overridden to allow configuring sale_order_lines through a popup
 * window when a product with 'rent_ok' is selected.
 *
 */

RentalConfiguratorFormController.include({

    _getRentalInfo: function (state) {
        var infos = this._super.apply(this, arguments);
        infos['rental_unit']= state.rental_unit
        infos['rental_price']= state.rental_price
        infos['duration']= state.duration
        return infos;
    },


});
return RentalConfiguratorFormController;

});
