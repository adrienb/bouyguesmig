# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type')

    def _prepare_move_default_values(self, return_line, new_picking, lot_dic):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
            'return_lots': lot_dic.get(return_line.product_id.id)
        }
        return vals