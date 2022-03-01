# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductMargin(models.TransientModel):
    _name = 'product.margin'
    _description = 'Product Margin'

    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)

    def action_apply(self):
        self.env['product.product'].extract_product_margin(self.start_date, self.end_date)
