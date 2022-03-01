# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    final_location_id = fields.Many2one('stock.location', compute='_compute_final_location_id')
    components_move_line_ids = fields.Many2many('stock.move.line', compute='_compute_components_move_line_ids')
    picking_type_warehouse_id = fields.Many2one('stock.warehouse', related='picking_type_id.warehouse_id')

    @api.depends('move_raw_ids')
    def _compute_components_move_line_ids(self):
        for rec in self:
            rec.components_move_line_ids = self.env['stock.move.line'].search([('move_id', 'in', rec.move_raw_ids.ids)])

    @api.depends('product_id', 'location_dest_id')
    def _compute_final_location_id(self):
        for rec in self:
            final_location_id = self.env['stock.putaway.rule'].search([('product_id', '=', rec.product_id.id), ('location_in_id', '=', rec.location_dest_id.id)], limit=1).location_out_id
            if final_location_id:
                rec.final_location_id = final_location_id
            else:
                rec.final_location_id = rec.location_dest_id

