# -*- coding: utf-8 -*-

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    zip_ids = fields.One2many('res.zip', 'warehouse_id', string='ZIP')
