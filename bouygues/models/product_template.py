# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_dangerous = fields.Boolean(string='Dangerous Product')
    can_edit_price = fields.Boolean(string='Can Edit Price')
    native_country_id = fields.Many2one('res.country', string='Native Country')
    customs_code = fields.Char(string='Customs Code')
    ICPE_code = fields.Char(string='ICPE Code')
    default_code = fields.Char(readonly=True, compute=False, inverse=False)
    substitution_product_id = fields.Many2one('product.template', string='Substitution Product')
    bom_count_visible = fields.Boolean(compute='_compute_bom_count_visible')
    company_id = fields.Many2one('res.company', 'Company', index=1, default=lambda self: self.env.company)
    purchase_family_id = fields.Many2one('purchase.family', 'Purchase Family')
    hs_or_fc = fields.Boolean(compute='_compute_hs_or_fc', store=True)
    we_love_life = fields.Boolean(string='We Love Life')
    distrimo_plus = fields.Boolean(string='Distriplus')
    made_in_france = fields.Boolean(string='Made in France')
    sur_commande = fields.Boolean(string='Sur commande')
    description_website = fields.Text(string='Website Description')
    bouygues_free_qty = fields.Float(
        'Free To Use Quantity', compute='_compute_quantities', search='_search_bouygues_free_qty',
        compute_sudo=False, digits='Product Unit of Measure',
        store=True)
    entity_ids = fields.Many2many('partner.category', string='Entities')
    manufacturer_link = fields.Char(string='Lien Fabricant')
    review_link = fields.Char(string='Avis Produit')
    security_data_file = fields.Binary(string='Security Data file', attachment=True)
    technical_file = fields.Binary(string='Technical file', attachment=True)
    storage_cost_id = fields.Many2one('account.tax', string='Frais de stockage')
    eco_tax_id = fields.Many2one('account.tax', string='Eco Taxe')

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        for rec in self:
            if rec.categ_id.type:
                rec['type'] = rec.categ_id.type
            rec['purchase_family_id'] = rec.categ_id.purchase_family_id.id if rec.categ_id.purchase_family_id else False
            rec['public_categ_ids'] = [(6, 0, rec.categ_id.public_categ_ids.ids)] if rec.categ_id.public_categ_ids else [(5, 0, 0)]

    def update_name(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Update name'),
            'res_model': 'product.template.update.name',
            'view_id': self.env.ref("bouygues.bouygues_product_template_update_name_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        for rec in self:
            if rec.categ_id.type:
                rec['type'] = rec.categ_id.type
            rec['purchase_family_id'] = rec.categ_id.purchase_family_id.id if rec.categ_id.purchase_family_id else False
            rec['public_categ_ids'] = [(6, 0, rec.categ_id.public_categ_ids.ids)] if rec.categ_id.public_categ_ids else [(5, 0, 0)]

    def _search_bouygues_free_qty(self, operator, value):
        domain = [('free_qty', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def action_view_ready_stock_move(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['context'] = {'search_default_by_product': 1, 'create': 0}
        action['domain'] = [('product_id', 'in', self.product_variant_ids.ids), ('state', 'not in', ['done', 'cancel'])]
        return action

    def _compute_bom_count_visible(self):
        group_sale = self.env.user.has_group('sales_team.group_sale_salesman')
        mrp_user = self.env.user.has_group('mrp.group_mrp_user')
        mrp_admin = self.env.user.has_group('mrp.group_mrp_manager')

        if group_sale and not mrp_user and not mrp_admin:
            self.bom_count_visible = True
        else:
            self.bom_count_visible = False

    @api.depends('categ_id', 'categ_id.hs_or_fc')
    def _compute_hs_or_fc(self):
        """
        Check if a parent of this product template is either "HS" or "FC"
        """
        for product in self:
            product.hs_or_fc = product.categ_id and product.categ_id.hs_or_fc

    @api.depends(
        'product_variant_ids',
        'product_variant_ids.stock_move_ids.product_qty',
        'product_variant_ids.stock_move_ids.state',
    )
    @api.depends_context('company_owned', 'force_company')
    def _compute_quantities(self):
        res = self._compute_quantities_dict()
        for template in self:
            template.qty_available = res[template.id]['qty_available']
            template.virtual_available = res[template.id]['virtual_available']
            template.incoming_qty = res[template.id]['incoming_qty']
            template.outgoing_qty = res[template.id]['outgoing_qty']
            template.bouygues_free_qty = res[template.id]['bouygues_free_qty']

    def _compute_quantities_dict(self):
        variants_available = {
            p['id']: p for p in
            self.product_variant_ids.read(['qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty', 'free_qty'])
        }
        prod_available = {}
        for template in self:
            qty_available = 0
            virtual_available = 0
            incoming_qty = 0
            outgoing_qty = 0
            bouygues_free_qty = 0
            for p in template.product_variant_ids:
                qty_available += variants_available[p.id]["qty_available"]
                virtual_available += variants_available[p.id]["virtual_available"]
                incoming_qty += variants_available[p.id]["incoming_qty"]
                outgoing_qty += variants_available[p.id]["outgoing_qty"]
                bouygues_free_qty += variants_available[p.id]["free_qty"]
            prod_available[template.id] = {
                "qty_available": qty_available,
                "virtual_available": virtual_available,
                "incoming_qty": incoming_qty,
                "outgoing_qty": outgoing_qty,
                "bouygues_free_qty": bouygues_free_qty,
            }
        return prod_available

    def action_view_bouygues_free_qty(self):
        self.ensure_one()
        action = {'type': 'ir.actions.act_window',
                  'name': _('View Quant'),
                  'view_mode': 'tree',
                  'view_type': 'list',
                  'view_id': self.env.ref('stock.view_stock_quant_tree').id,
                  'res_model': 'stock.quant',
                  'domain': [('product_tmpl_id', '=', self.id)],
                  'context': {'search_default_internal_loc': 1},
                }
        return action

    @api.model
    def create(self, vals):
        categ_id = self.env['product.category'].browse(vals['categ_id']) if vals.get('categ_id') else self.categ_id
        if categ_id:
            if categ_id.code:
                category_code = categ_id.code if categ_id.code else 'NOCODE'
            if categ_id.type:
                vals['type'] = categ_id.type
            vals['purchase_family_id'] = categ_id.purchase_family_id.id if categ_id.purchase_family_id else False
            vals['public_categ_ids'] = [(6, 0, categ_id.public_categ_ids.ids)] if categ_id.public_categ_ids else [(5, 0, 0)]
        vals['default_code'] = category_code + self.env['ir.sequence'].next_by_code('product.sequence.category')

        return super(ProductTemplate, self).create(vals)

    @api.model
    def _query_get(self, domain=None):
        self.check_access_rights('read')
        return super(ProductTemplate, self)._query_get(domain)

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        if not self.env.context.get('website_sale_stock_get_quantity'):
            return combination_info

        if combination_info['product_id']:
            product = self.env['product.product'].sudo().browse(combination_info['product_id'])
            website = self.env['website'].get_current_website()
            bouygues_free_qty = product.with_context(warehouse=website.warehouse_id.id).bouygues_free_qty
            free_qty = product.free_qty
            combination_info.update({
                'bouygues_free_qty': bouygues_free_qty,
                'bouygues_free_qty_formatted': self.env['ir.qweb.field.float'].value_to_html(bouygues_free_qty, {'decimal_precision': 'Product Unit of Measure'}),
                'free_qty': free_qty
            })
        else:
            combination_info.update({
                'bouygues_free_qty': 0,
            })

        return combination_info

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            forbidden_characters = [';', '#', '"', '_', '\\']
            for character in forbidden_characters:
                if rec.name and character in rec.name:
                    raise ValidationError('You cannot use special character in the name')
