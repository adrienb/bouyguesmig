# -*- coding: utf-8 -*-

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_pick = fields.Boolean(string='Pick', default=False)
    is_out = fields.Boolean(string='Out', default=False)
    is_resupply = fields.Boolean(string='Resupply', default=False)
    resupply_contact_id = fields.Many2one('res.partner', string='Resupply Contact')
    warning_user_id = fields.Many2one('res.users', string='Warning Contact')
