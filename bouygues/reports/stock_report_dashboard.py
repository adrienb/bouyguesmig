# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class StockReportDashboard(models.Model):
    _name = 'stock.report.dashboard'
    _description = "Stock Report Dashboard"
    _rec_name = 'id'
    _auto = False

    id = fields.Integer("", readonly=True)
    date_done = fields.Datetime("Transfer Date", readonly=True)
    creation_date = fields.Datetime("Creation Date", readonly=True)
    scheduled_date = fields.Datetime("Expected Date", readonly=True)
    delay = fields.Float("Delay (Days)", readonly=True)
    cycle_time = fields.Float("Cycle Time (Days)", readonly=True)
    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], string="Type", readonly=True)
    operation_type = fields.Char("Operation Type", readonly=True)
    picking_name = fields.Char("Picking Name", readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    is_backorder = fields.Boolean("Is a Backorder", readonly=True)
    is_late = fields.Boolean("Is Late", readonly=True)
    location_id = fields.Many2one('stock.location', "Source Location", readonly=True)
    location_dest_id = fields.Many2one('stock.location', "Destination Location", readonly=True)
    number_of_backorder = fields.Integer(string='# of Backroders')
    # number_of_out_pickings = fields.Integer(string='# of Out Pickings')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    nbr = fields.Integer('# of Stock Pickings', readonly=True)

    def _select(self):
        select_str = """
            count(*) as nbr,
            sp.id as id,
            sp.name as picking_name,
            sp.date_done as date_done,
            sp.date as creation_date,
            sp.scheduled_date as scheduled_date,
            sp.partner_id as partner_id,
            sp.backorder_id IS NOT NULL as is_backorder,
            (extract(epoch from avg(date_done-scheduled_date))/(24*60*60))::decimal(16,2) as delay,
            (extract(epoch from avg(date_done-sp.date))/(24*60*60))::decimal(16,2) as cycle_time,
            (extract(epoch from avg(date_done-scheduled_date))/(24*60*60))::decimal(16,2) > 0 as is_late,
            case when sp.state='done' and sp.backorder_id IS NOT NULL then 1 else 0 end as number_of_backorder,
            sp.location_id as location_id,
            sp.location_dest_id as location_dest_id,
            sp.state as state,
            spt.code as picking_type_code,
            spt.name as operation_type
        """

        return select_str

    def _from(self):
        from_str = """
            stock_picking sp
            LEFT JOIN stock_move sm ON sm.picking_id = sp.id
            LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
            sp.id,
            sp.name,
            sp.date_done,
            sp.date,
            sp.scheduled_date,
            sp.partner_id,
            is_backorder,
            sp.location_id,
            sp.location_dest_id,
            sp.state,
            spt.code,
            spt.name
        """

        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                            SELECT
                                %s
                            FROM
                                %s
                            GROUP BY
                                %s
            )""" % (self._table, self._select(), self._from(), self._group_by(),))
