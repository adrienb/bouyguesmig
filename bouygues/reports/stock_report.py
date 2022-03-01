# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockReport(models.Model):
    _inherit = 'stock.report'

    location_id = fields.Many2one('stock.location', "Source Location", readonly=True)
    location_dest_id = fields.Many2one('stock.location', "Destination Location", readonly=True)

    def _select(self):
        select_str = super(StockReport, self)._select()
        select_str += ', stock_p.location_id as location_id, stock_p.location_dest_id as location_dest_id'
        return select_str

    def _from(self):
        from_str = super(StockReport, self)._from()

        first_join = 'stock_move sm'
        index = from_str.find(first_join) + len(first_join)

        new_join = ' LEFT JOIN (SELECT id, location_id, location_dest_id FROM stock_picking GROUP BY id, location_id, location_dest_id) stock_p ON sm.picking_id = stock_p.id '

        return from_str[:index] + new_join + from_str[index:]

    def _group_by(self):
        groupby_str = super(StockReport, self)._group_by()
        groupby_str += ', stock_p.location_id, stock_p.location_dest_id'
        return groupby_str

