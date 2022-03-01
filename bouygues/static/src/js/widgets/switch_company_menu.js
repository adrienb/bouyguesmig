odoo.define('bouygues.SwitchCompanyMenu', function (require) {
'use strict';

let session = require('web.session');
let SwitchCompanyMenu = require('web.SwitchCompanyMenu');

SwitchCompanyMenu.include({
    template: 'bouygues.SwitchCompanyMenu',

    willStart: function() {
        this.view_company_switch_button = session.view_company_switch_button;
        return this._super.apply(this, arguments);
    }
});
});
