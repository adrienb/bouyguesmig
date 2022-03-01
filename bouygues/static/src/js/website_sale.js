odoo.define('bouygues.cart', function (require) {
'use strict';

let publicWidget = require('web.public.widget');
let core = require('web.core');
let qweb = core.qweb;

publicWidget.registry.productsSearchBar = publicWidget.registry.productsSearchBar.extend({
    xmlDependencies: [
        '/bouygues/static/src/xml/productsSearchBar_autocomplete.xml',
    ],
    /**
     * @private
     */
    _render: function (res) {
        var $prevMenu = this.$menu;
        this.$el.toggleClass('dropdown show', !!res);
        if (res) {
            var products = res['products'];
            this.$menu = $(qweb.render('bouygues.productsSearchBar.autocomplete', {
                products: products,
                hasMoreProducts: products.length < res['products_count'],
                currency: res['currency'],
                widget: this,
            }));
            this.$menu.css('min-width', this.autocompleteMinWidth);
            this.$el.append(this.$menu);
        }
        if ($prevMenu) {
            $prevMenu.remove();
        }
    },
});
});
