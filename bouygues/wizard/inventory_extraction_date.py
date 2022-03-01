# -*- coding: utf-8 -*-

from odoo import fields, models


class InventoryExtractionDate(models.TransientModel):
    _name = 'inventory.extraction.date'
    _description = 'Inventory Extraction Date'

    inventory_date = fields.Date(string="Inventory Date", required=True)

    def action_apply(self):
        self.env['product.product'].extract_inventory_at_date(self.inventory_date)
