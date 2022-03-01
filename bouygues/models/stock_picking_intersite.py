# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPickingIntersite(models.Model):
    _name = 'stock.picking.intersite'
    _description = 'Stock Picking Intersite'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(StockPickingIntersite, self).default_get(fields)
        warehouse = None
        if 'warehouse_id' not in res and res.get('company_id'):
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', res['company_id']), ('name', 'ilike', 'Chilly')], limit=1)
        if warehouse:
            res['warehouse_id'] = warehouse.id
            res['location_id'] = warehouse.lot_stock_id.id
        return res

    name = fields.Char(string='Name', copy=False, readonly=True, default=lambda self: _('New'))
    state = fields.Selection(readonly=True, selection=[('draft', "Draft"), ('done', "Done")], copy=False, default='draft', tracking=True)
    validation_date = fields.Datetime(string='Validation Date', readonly=True, copy=False)
    stock_picking_count = fields.Integer(string='Transfers', compute='_compute_stock_picking_count')
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the type.type without removing it.")
    product_line_ids = fields.One2many('stock.picking.intersite.line', 'intersite_id', string='Product lines', copy=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', check_company=True, ondelete="cascade", required=True)
    location_id = fields.Many2one('stock.location', 'Location', ondelete="cascade", required=True, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    route_id = fields.Many2one('stock.location.route', string='Route', required=True, domain=[('manual_resupply', '=', True)])

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        """ Finds location id for changed warehouse. """
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id.id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id), ('name', 'ilike', 'Chilly')], limit=1)

    def action_view_stock_pickings(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        picking_ids = self.env['stock.picking'].search([('intersite_ids', 'in', [self.id])])
        action['domain'] = [('id', 'in', picking_ids.ids)]
        return action

    def _compute_stock_picking_count(self):
        for rec in self:
            picking_ids = self.env['stock.picking'].search([('intersite_ids', 'in', [rec.id])])
            rec.stock_picking_count = len(picking_ids)

    @api.model
    def create(self, vals):
        vals['name'] = 'Intersite ' + self.env['ir.sequence'].next_by_code('stock.picking.intersite.sequence')
        return super(StockPickingIntersite, self).create(vals)

    def validate_intersite(self):
        for rec in self:
            for product_line in rec.product_line_ids:
                if not product_line.product_qty > 0:
                    raise UserError(_("Product lines must have a quantity over 0."))

                values = {
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'group_d': False,
                    'orderpoint_id': False,
                    'warehouse_id': product_line.intersite_id.warehouse_id,
                    'route_ids': rec.route_id
                }

                self.env['procurement.group'].with_context(intersite_id=rec.id).run([self.env['procurement.group'].Procurement(
                    product_line.product_id, product_line.product_qty, product_line.product_id.uom_id,
                    product_line.intersite_id.location_id, product_line.intersite_id.name, product_line.intersite_id.name,
                    product_line.intersite_id.company_id, values)])

            # Find the created PICK to assign his moves
            picking_ids = self.env['stock.picking'].search([('intersite_ids', 'in', [rec.id]), ('is_pick', '=', True)])
            for picking in picking_ids:
                picking.action_assign()

            rec.state = 'done'
            rec.validation_date = datetime.now()

