# -*- coding: utf-8 -*-

from odoo import fields, models


class Orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    main_supplier_id = fields.Many2one('res.partner', related='product_id.main_supplier_id')
