# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    is_brand = fields.Boolean(string='Brand', copy=False, default=False)
