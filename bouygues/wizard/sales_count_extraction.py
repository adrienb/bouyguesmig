# -*- coding: utf-8 -*-

from odoo import fields, models


class SalesCountExtraction(models.TransientModel):
    _name = 'sales.count.extraction'
    _description = 'Sales Count Extraction'

    minimum_amount = fields.Float(string="Minimum Amount", required=True)
    maximum_amount = fields.Float(string="Maximum Amount", required=True)

    def action_apply(self):
        self.env['sale.order'].extract_sales_count(self.minimum_amount, self.maximum_amount)
