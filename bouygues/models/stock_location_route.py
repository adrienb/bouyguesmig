# -*- coding: utf-8 -*-

from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    manual_resupply = fields.Boolean(string='Intersite Manuel', default=False, copy=False)
