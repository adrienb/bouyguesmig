# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductRotationRate(models.TransientModel):
    _name = 'product.rotation.rate'
    _description = 'Product Rotation Rate'

    def action_apply(self):
        self.env['product.product'].extract_product_rotation_rate()
