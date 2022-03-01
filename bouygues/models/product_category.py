# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char(string='Code')
    hs_or_fc = fields.Boolean(compute='_compute_hs_or_fc', store=True, recursive=True)
    type = fields.Selection([('product', 'Storable Product'), ('consu', 'Consumable'), ('service', 'Service')])
    purchase_family_id = fields.Many2one('purchase.family', 'Purchase Family')
    public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category')

    @api.depends('code', 'parent_id', 'parent_id.hs_or_fc')
    def _compute_hs_or_fc(self):
        for cat in self:
            if cat.code in ("HS", "FC"):
                cat.hs_or_fc = True
            else:
                cat.hs_or_fc = cat.parent_id and cat.parent_id.hs_or_fc
