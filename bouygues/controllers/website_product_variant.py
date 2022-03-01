# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class WebsiteSaleBouyguesVariantController(WebsiteSaleVariantController):
    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):

        res = super(WebsiteSaleBouyguesVariantController, self).get_combination_info_website(product_template_id, product_id, combination, add_qty, **kw)

        Product = request.env['product.product'].browse(res['product_id'])

        res['eco_taxe'] = Product.eco_tax_id.name
        res['storage_cost'] = Product.storage_cost_id.name
        res['art_eanu'] = Product.art_eanu
        res['art_eanc'] = Product.art_eanc
        res['art_eanp'] = Product.art_eanp
        res['art_lonu'] = Product.art_lonu
        res['art_laru' ] = Product.art_laru
        res['art_hauu' ] = Product.art_hauu
        res['art_clas'] = Product.art_clas
        res['art_qtec'] = Product.art_qtec
        res['art_qtep'] = Product.art_qtep
        res['art_stat'] = Product.art_stat
        res['art_code'] = Product.art_code
        res['class_code'] = Product.class_code
        res['packing_code'] = Product.packing_code
        res['customs_code'] = Product.customs_code
        res['ICPE_code'] = Product.ICPE_code
        res['native_country_id'] = Product.native_country_id.name
        res['weight'] = Product.weight
        res['weight_uom_name'] = Product.weight_uom_name

        return res