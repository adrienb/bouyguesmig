from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderMultipleProduct(models.TransientModel):
    _name = 'sale.order.multiple.product'
    _description = 'Add multiple products'

    product_ids = fields.Many2many('product.product', string="Product")

    def add_product(self):
        for line in self.product_ids:
            self.env['sale.order.line'].create({
                'product_id': line.id,
                'name': line.name,
                'product_uom_qty': 1,
                'price_unit': line.lst_price,
                'order_id': self._context.get('active_id'),
            })

