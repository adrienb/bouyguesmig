# -*- coding: utf-8 -*-

from odoo import fields, models


class StockPickingIntersiteLine(models.Model):
    _name = 'stock.picking.intersite.line'
    _description = 'Stock Picking Intersite Line'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Product Qty')
    intersite_id = fields.Many2one('stock.picking.intersite')
