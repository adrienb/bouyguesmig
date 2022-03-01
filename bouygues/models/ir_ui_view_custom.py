# -*- coding: utf-8 -*-

from odoo import fields, models


class IrUiViewCustom(models.Model):
    _inherit = 'ir.ui.view.custom'

    board_sale = fields.Boolean(string='Board Sale', default=False, copy=False)
    board_purchase = fields.Boolean(string='Board Purchase', default=False, copy=False)
    board_stock = fields.Boolean(string='Board Stock', default=False, copy=False)
