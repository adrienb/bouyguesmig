# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    active = fields.Boolean(default=True)

    @api.constrains('product_code')
    def _check_product_code(self):
        for rec in self:
            if rec.product_code:
                self.env.cr.execute("SELECT COUNT(*) FROM product_supplierinfo WHERE lower(product_code) = %s", (rec.product_code.lower(),))
                count = self.env.cr.fetchone()[0]
                if count > 1:
                    raise ValidationError('Product reference must be unique')
