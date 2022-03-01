# -*- coding: utf-8 -*-

from datetime import time, timedelta
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from datetime import datetime
import base64


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variant_display_name = fields.Char(compute='_compute_variant_display_name')
    hs_or_fc = fields.Boolean(compute='_compute_hs_or_fc', store=True)
    default_code = fields.Char('Internal Reference', compute='_compute_default_code', store=True)
    uom_uom_id = fields.Many2one('uom.uom', string='UOM')
    product_sale_line_warn_msg = fields.Text('Message for sales order line')
    product_sale_line_warn = fields.Selection([('no-message', "No Message"), ('warning', "Warning"), ('block', "Blocking Message")], 'Sales order line', required=True, default="no-message")
    main_supplier_id = fields.Many2one('res.partner', string="Main supplier", compute='_compute_main_supplier_id', readonly=False, store=True)
    product_purchase_line_warn_msg = fields.Text('Message for purchase order line')
    product_purchase_line_warn = fields.Selection([('no-message', "No Message"), ('warning', "Warning"), ('block', "Blocking Message")], 'Purchase order line', required=True, default="no-message")
    art_eanu = fields.Char(string='Product EAN n°')
    art_eanc = fields.Char(string='Colis EAN n°')
    art_eanp = fields.Char(string='Palette EAN n°')
    art_lonu = fields.Float(string='Length')
    art_laru = fields.Float(string='Width')
    art_hauu = fields.Float(string='Height')
    art_clas = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ], string='Class')
    art_qtec = fields.Integer(string='Qty by Colis')
    art_qtep = fields.Integer(string='Qty by Palette')
    art_stat = fields.Selection([
        ('draft', 'New'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('eof', 'End of life'),
    ], string='Status')
    art_code = fields.Char(string='Code')
    class_code = fields.Char(string='Class Code')
    packing_code = fields.Char(string='Packing code')
    customs_code = fields.Char(string='Customs Code')
    ICPE_code = fields.Char(string='ICPE Code')
    native_country_id = fields.Many2one('res.country', string='Native Country')
    qty_available_distriplus = fields.Float(compute='_compute_quantities_distriplus')
    qty_available_paquetage = fields.Float(compute='_compute_quantities_paquetage')
    qty_available_tourville = fields.Float(compute='_compute_quantities_tourville')
    qty_available_tourville_casse = fields.Float(compute='_compute_quantities_tourville_casse')
    qty_available_tourville_dep = fields.Float(compute='_compute_quantities_tourville_dep')
    qty_available_tourville_hom = fields.Float(compute='_compute_quantities_tourville_hom')
    qty_available_tourville_mqt = fields.Float(compute='_compute_quantities_tourville_mqt')
    qty_available_tourville_nc = fields.Float(compute='_compute_quantities_tourville_nc')
    qty_available_tourville_ns = fields.Float(compute='_compute_quantities_tourville_ns')
    qty_available_tourville_ret = fields.Float(compute='_compute_quantities_tourville_ret')
    qty_available_tourville_sav = fields.Float(compute='_compute_quantities_tourville_sav')
    qty_available_chilly = fields.Float(compute='_compute_quantities_chilly')
    qty_available_chilly_casse = fields.Float(compute='_compute_quantities_chilly_casse')
    qty_available_chilly_dep = fields.Float(compute='_compute_quantities_chilly_dep')
    qty_available_chilly_hom = fields.Float(compute='_compute_quantities_chilly_hom')
    qty_available_chilly_mqt = fields.Float(compute='_compute_quantities_chilly_mqt')
    qty_available_chilly_nc = fields.Float(compute='_compute_quantities_chilly_nc')
    qty_available_chilly_ns = fields.Float(compute='_compute_quantities_chilly_ns')
    qty_available_chilly_ret = fields.Float(compute='_compute_quantities_chilly_ret')
    qty_available_chilly_sav = fields.Float(compute='_compute_quantities_chilly_sav')
    native_country_code = fields.Char(related='native_country_id.code')
    wms_exported = fields.Boolean(default=False, copy=False)
    eco_product = fields.Boolean(default=False, copy=False)
    eco_product_id = fields.Many2one('product.product', string='Eco participation')
    code_v12 = fields.Char(string='Product code V12')
    main_supplier_id_name = fields.Char(related='main_supplier_id.name')
    main_supplier_price = fields.Float(compute='_compute_main_supplier_price')
    categ_id_name = fields.Char(related='categ_id.name')
    end_life = fields.Boolean(string='Fin de vie', default=False, copy=False)
    finish_stock = fields.Boolean(string='Finir stock', default=False, copy=False)
    substitution_product_product_id = fields.Many2one('product.product', string="Substitution product ")
    end_life_message = fields.Text(string='End of life message')
    eco_tax_id = fields.Many2one('account.tax', string='Eco Taxe', related='product_tmpl_id.eco_tax_id')
    storage_cost_id = fields.Many2one('account.tax', string='Frais de stockage', related='product_tmpl_id.storage_cost_id')

    def update_name(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Update name'),
            'res_model': 'product.product.update.name',
            'view_id': self.env.ref("bouygues.bouygues_product_product_update_name_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    def _compute_main_supplier_price(self):
        for rec in self:
            rec.main_supplier_price = 0.0
            if self._context.get('from_date') and self._context.get('to_date'):
                start_date = self._context.get('from_date').date()
                end_date = self._context.get('to_date').date()
                seller_id = rec.seller_ids.filtered(lambda l: l.name == rec.main_supplier_id and l.date_start and l.date_end and l.date_start <= start_date and l.date_end >= end_date)
                if len(seller_id) > 0:
                    rec.main_supplier_price = seller_id[0].price

    def _compute_quantities_distriplus(self):
        location = self.env['stock.warehouse'].search([('name', '=', 'DISTRIPLUS')], limit=1)
        res = self.with_context(warehouse=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_distriplus = res[product.id]['qty_available']

    def _compute_quantities_paquetage(self):
        location = self.env['stock.warehouse'].search([('name', 'ilike', 'Paquetage')], limit=1)
        res = self.with_context(warehouse=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_paquetage =  res[product.id]['qty_available']

    def _compute_quantities_tourville(self):
        warehouse_tourville = self.env['stock.warehouse'].search([('id', '=', 2)], limit=1)
        res = self.with_context(warehouse=warehouse_tourville.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville = res[product.id]['qty_available']

    def _compute_quantities_tourville_casse(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-CASSE')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_casse = res[product.id]['qty_available']

    def _compute_quantities_tourville_dep(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-DEP')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_dep = res[product.id]['qty_available']

    def _compute_quantities_tourville_hom(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-HOM')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_hom = res[product.id]['qty_available']

    def _compute_quantities_tourville_mqt(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-MQT')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_mqt = res[product.id]['qty_available']

    def _compute_quantities_tourville_nc(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-NC')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_nc = res[product.id]['qty_available']

    def _compute_quantities_tourville_ns(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-NS')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_ns = res[product.id]['qty_available']

    def _compute_quantities_tourville_ret(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-RET')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_ret = res[product.id]['qty_available']

    def _compute_quantities_tourville_sav(self):
        location = self.env['stock.location'].search([('name', '=', 'DITLR-SAV')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_tourville_sav = res[product.id]['qty_available']

    def _compute_quantities_chilly(self):
        warehouse_chilly = self.env['stock.warehouse'].search([('name', '=', 'Distrimo Chilly Mazarin')], limit=1)
        res = self.with_context(warehouse=warehouse_chilly.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly = res[product.id]['qty_available']

    def _compute_quantities_chilly_casse(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-CASSE')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_casse = res[product.id]['qty_available']

    def _compute_quantities_chilly_dep(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-DEP')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_dep = res[product.id]['qty_available']

    def _compute_quantities_chilly_hom(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-HOM')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_hom = res[product.id]['qty_available']

    def _compute_quantities_chilly_mqt(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-MQT')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_mqt = res[product.id]['qty_available']

    def _compute_quantities_chilly_nc(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-NC')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_nc = res[product.id]['qty_available']

    def _compute_quantities_chilly_ns(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-NS')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_ns = res[product.id]['qty_available']

    def _compute_quantities_chilly_ret(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-RET')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_ret = res[product.id]['qty_available']

    def _compute_quantities_chilly_sav(self):
        location = self.env['stock.location'].search([('name', '=', 'DICHM-SAV')], limit=1)
        res = self.with_context(location=location.name)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available_chilly_sav = res[product.id]['qty_available']

    def _compute_sales_count(self):
        """ Override computation of sales_count to edit be able to correctly display the sales_count """
        r = {}
        self.sales_count = 0
        if not self.user_has_groups('sales_team.group_sale_salesman,bouygues.bouygues_base_group'):
            return r
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365),
                                                                      time.min))

        done_states = self.env['sale.report']._get_done_states()

        domain = [
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids),
            ('date', '>=', date_from),
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            if not product.id:
                product.sales_count = 0.0
                continue
            product.sales_count = float_round(r.get(product.id, 0), precision_rounding=product.uom_id.rounding)
        return r

    def action_view_ready_stock_move(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['context'] = {'create': 0}
        action['domain'] = [('product_id', 'in', [self.id]), ('state', 'not in', ['done', 'cancel'])]
        return action

    @api.depends('name', 'product_template_attribute_value_ids')
    def _compute_variant_display_name(self):
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()
            product.variant_display_name = variant and "%s (%s)" % (product.name, variant) or product.name

    @api.depends('product_tmpl_id', 'product_tmpl_id.hs_or_fc')
    def _compute_hs_or_fc(self):
        """
        Check if a parent of this product template is either "HS" or "FC"
        """
        for product in self:
            product.hs_or_fc = product.product_tmpl_id.hs_or_fc

    def action_view_free_qty(self):
        self.ensure_one()
        action = {'type': 'ir.actions.act_window',
                  'name': _('View Quant'),
                  'view_mode': 'tree',
                  'view_type': 'list',
                  'view_id': self.env.ref('stock.view_stock_quant_tree').id,
                  'res_model': 'stock.quant',
                  'domain': [('product_id', '=', self.id)],
                  'context': {'search_default_internal_loc': 1},
                }
        return action

    @api.depends('product_tmpl_id', 'product_template_attribute_value_ids', 'product_template_attribute_value_ids.product_attribute_value_id', 'product_template_attribute_value_ids.product_attribute_value_id.code', 'product_tmpl_id.default_code')
    def _compute_default_code(self):
        for rec in self:
            code = rec.product_tmpl_id.default_code if rec.product_tmpl_id and rec.product_tmpl_id.default_code else ''

            for attribute_value in rec.product_template_attribute_value_ids:
                if attribute_value.product_attribute_value_id.code:
                    code += attribute_value.product_attribute_value_id.code

            rec.default_code = code

    def write(self, values):
        if not values.get('wms_exported'):
            values['wms_exported'] = False
        return super(ProductProduct, self).write(values)

    def extract_inventory_at_date(self, date):
        filename = 'inventory_at_date_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Code article;Désignation;Cout;Qté Tourville;Qté Chilly;Qté Distriplus;Qté paquetages'

        fields = [
            'default_code',
            'name',
            'standard_price',
            'qty_available_tourville',
            'qty_available_chilly',
            'qty_available_distriplus',
            'qty_available_paquetage'
        ]

        all_products = self.env['product.product'].with_context(from_date=date, to_date=date).search_read([('company_id', '=', self.env.company.id), ('type', '=', 'product')], ['default_code',
                                                                                                                                       'name',
                                                                                                                                       'standard_price',
                                                                                                                                       'qty_available_tourville',
                                                                                                                                       'qty_available_chilly',
                                                                                                                                       'qty_available_distriplus',
                                                                                                                                       'qty_available_paquetage'])

        row_data = ''

        for product in all_products:
            for field in fields:
                if field not in ['default_code', 'name']:
                    row_data += format(product.get(field), '.2f')
                else:
                    row_data += str(product.get(field)) if product.get(field) is not False else ''
                row_data += ';'
            row_data += '\n'
        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Inventory at date - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def extract_product_margin(self, start_date, end_date):
        filename = 'product_margin - ' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Fournisseur principal;Date de création;Code article;Désignation;Prix achat fournisseur principal;Prix vente;Prix public;Qté vendue;Marge calculée'

        fields = [
            'main_supplier_id_name',
            'create_date',
            'default_code',
            'name',
            'main_supplier_price',
            'main_pricelist_price',
            'lst_price',
            'sales_count',
            'margin',
        ]

        all_products = self.env['product.product'].with_context(from_date=start_date, to_date=end_date).search_read([('company_id', '=', self.env.company.id), ('main_supplier_id', '!=', False)], ['id',
                                                                                                                                                          'main_supplier_id_name',
                                                                                                                                                          'create_date',
                                                                                                                                                          'default_code',
                                                                                                                                                          'name',
                                                                                                                                                          'main_supplier_price',
                                                                                                                                                          'lst_price',
                                                                                                                                                          ])

        price_dic = {}
        main_pricelist_prices = self.env['product.pricelist.item'].search_read([('pricelist_id', '=', 6), ('date_start', '<=', start_date.date()), ('date_end', '>=', end_date.date())], ['product_id', 'fixed_price'])
        for price in main_pricelist_prices:
            if price.get('product_id') and price.get('product_id')[0] and price.get('fixed_price'):
                price_dic[str(price.get('product_id')[0])] = price.get('fixed_price')

        done_states = self.env['sale.report']._get_done_states()

        domain = [
            ('state', 'in', done_states),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ]

        r = {}

        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']

        row_data = ''

        for product in all_products:
            for field in fields:
                main_pricelist_price = price_dic.get(str(product.get('id')))
                if field == 'main_pricelist_price':
                    row_data += str(main_pricelist_price)
                elif field == 'margin' and main_pricelist_price and main_pricelist_price and product.get('main_supplier_price') is not False:
                    row_data += str((main_pricelist_price - product.get('main_supplier_price')) / main_pricelist_price)
                elif field == 'sales_count':
                    row_data += str(r.get(product.get('id'), 0))
                else:
                    row_data += str(product.get(field)) if product.get(field) is not False else ''
                row_data += ';'
            row_data += '\n'
        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Product Margin - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def extract_pr_analysis(self, start_date, end_date):
        filename = 'PR Analysis - ' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Product;Qté achetée;Cout total;Qté vendue;CA total;'

        all_products = self.env['product.product'].search_read([('company_id', '=', self.env.company.id), ('type', '=', 'service')], ['id', 'name', 'standard_price'])
        product_id_list = [product.get('id') for product in all_products]

        # /// PRICELIST PRICE ///
        price_dic = {}
        if start_date and end_date:
            main_pricelist_prices = self.env['product.pricelist.item'].search_read(
                [('pricelist_id', '=', 6), ('date_start', '<=', start_date.date()), ('date_end', '>=', end_date.date())], ['product_id', 'fixed_price'])
        else:
            main_pricelist_prices = self.env['product.pricelist.item'].search_read(
                [('pricelist_id', '=', 6), ('date_end', '>', fields.datetime.now().date())], ['product_id', 'fixed_price'])
        for price in main_pricelist_prices:
            if price.get('product_id') and price.get('product_id')[0] and price.get('fixed_price'):
                price_dic[str(price.get('product_id')[0])] = price.get('fixed_price')
        # ///////

        # /// SALES COUNT ///
        done_states = self.env['sale.report']._get_done_states()
        domain = [
            ('state', 'in', done_states),
        ]
        if start_date and end_date:
            domain.append(('date', '>=', start_date))
            domain.append(('date', '<=', end_date))
        r = {}
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        # //////

        # /// PURCHASE COUNT ///
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('product_id', 'in', product_id_list),
        ]
        if start_date and end_date:
            domain.append(('date_order', '>=', start_date))
            domain.append(('date_order', '<=', end_date))
        order_lines = self.env['purchase.order.line'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
        purchased_data = dict([(data['product_id'][0], data['product_uom_qty']) for data in order_lines])
        # //////

        row_data = ''

        for product in all_products:
            product_name = product.get('name') if product.get('name') else ''
            sales_count = float(r.get(product.get('id'), 0))
            purchased_count = float(purchased_data.get(product.get('id'), 0))
            pricelist_price = price_dic.get(str(product.get('id')))
            standard_price = product.get('standard_price')

            if isinstance(pricelist_price, float) and isinstance(standard_price, float):
                row_data += product_name + ';' + str(purchased_count) + ';' + str(purchased_count * standard_price) + ';' + str(sales_count) + ';' + str(sales_count * pricelist_price) + ';' + '\n'

        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : PR Analysis - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def _archive_end_of_life(self):
        end_product_ids = self.env['product.product'].search([('end_life', '=', True)])
        product_ids = end_product_ids.filtered(lambda l: l.free_qty == 0)
        for product in product_ids:
            product.active = False

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        for rec in self:
            if rec.categ_id.type:
                rec['type'] = rec.categ_id.type
            rec['public_categ_ids'] = [(6, 0, rec.categ_id.public_categ_ids.ids)] if rec.categ_id.public_categ_ids else [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            categ_id = self.env['product.category'].browse(val['categ_id']) if val.get('categ_id') else self.categ_id
            if categ_id:
                if categ_id.type:
                    val['type'] = categ_id.type
                val['public_categ_ids'] = [(6, 0, categ_id.public_categ_ids.ids)] if categ_id.public_categ_ids else [(5, 0, 0)]
        return super(ProductProduct, self).create(vals_list)

    @api.depends('variant_seller_ids')
    def _compute_main_supplier_id(self):
        for rec in self:
            rec.main_supplier_id = rec.variant_seller_ids[0].name if rec.variant_seller_ids else False

    def extract_product_rotation_rate(self):
        filename = 'product_rotation_rate - ' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = "Catégorie;Fournisseur principal;Date de création de l'article;Code article;Désignation;Qté vendue (OUT) sur l'anne en cours;Qté en stock à aujourd'hui;Taux de rotation calculé N en cours;Qté vendue (OUT) sur l'année N-1;Qté en stock à aujourd'hui N-1;Taux de rotation calculé N-1;"

        fields = [
            'categ_id_name',
            'main_supplier_id_name',
            'create_date',
            'default_code',
            'name',
            'sold_qty_current_year',
            'free_qty',
            'current_rotation_cycle',
            'sold_qty_previous_year',
            'qty_last_year',
            'previous_rotation_cycle',
        ]

        all_products = self.env['product.product'].search_read(
            [('company_id', '=', self.env.company.id), ('type', '=', 'product')], ['id',
                                                                                   'categ_id_name',
                                                                                   'main_supplier_id_name',
                                                                                   'create_date',
                                                                                   'default_code',
                                                                                   'name',
                                                                                   'free_qty',
                                                                                   ])

        # Getting the sales information of this year and the previous year
        start_of_current_year = datetime(datetime.today().year, 1, 1)
        start_of_previous_year = datetime(datetime.today().year - 1, 1, 1)
        end_of_previous_year = datetime(datetime.today().year - 1, datetime.today().month, datetime.today().day)

        done_states = self.env['sale.report']._get_done_states()

        domain = [
            ('state', 'in', done_states),
            ('date', '>=', start_of_current_year),
            ('date', '<=', datetime.today()),
        ]
        current_year_sales = {}
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            current_year_sales[group['product_id'][0]] = group['product_uom_qty']

        domain = [
            ('state', 'in', done_states),
            ('date', '>=', start_of_previous_year),
            ('date', '<=', end_of_previous_year),
        ]
        previous_year_sales = {}
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            previous_year_sales[group['product_id'][0]] = group['product_uom_qty']

        # Getting the quantity of the previous year
        all_products_previous_qty = self.env['product.product'].with_context(from_date=start_of_previous_year, to_date=end_of_previous_year).search_read(
            [('company_id', '=', self.env.company.id), ('type', '=', 'product')], ['id', 'free_qty'])
        qty_last_year_dict = dict([(product['id'], product['free_qty']) for product in all_products_previous_qty])

        row_data = ''

        for product in all_products:
            for field in fields:
                if field == 'sold_qty_current_year':
                    row_data += str(current_year_sales.get(product.get('id'), 0))
                elif field == 'current_rotation_cycle':
                    if product.get('free_qty'):
                        row_data += str(current_year_sales.get(product.get('id'), 0) / product.get('free_qty'))
                    else:
                        row_data += ''
                elif field == 'sold_qty_previous_year':
                    row_data += str(previous_year_sales.get(product.get('id'), 0))
                elif field == 'qty_last_year':
                    row_data += str(qty_last_year_dict.get(product.get('id'), 0))
                elif field == 'previous_rotation_cycle':
                    if qty_last_year_dict.get(product.get('id'), 0):
                        row_data += str(previous_year_sales.get(product.get('id'), 0) / qty_last_year_dict.get(product.get('id')))
                    else:
                        row_data += ''
                elif field == 'free_qty':
                    row_data += str(product.get(field)) if product.get(field) is not False else 0
                else:
                    row_data += str(product.get(field)) if product.get(field) is not False else ''
                row_data += ';'
            row_data += '\n'
        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Product Rotation Rate - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })
