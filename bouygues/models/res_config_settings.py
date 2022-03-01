# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    block_default_product_id = fields.Many2one(
        'product.product',
        'Block sale.order',
        domain="[('sale_ok', '=', True)]",
        config_parameter='bouygues.default_product_id_block',
        help='Product that blocks sale.order when chosen as a sale.order.line'
    )
