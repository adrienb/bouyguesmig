# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    qty_to_deliver = fields.Float(string='To Deliver', compute='_compute_qty_to_deliver')
    final_location_id = fields.Many2one('stock.location', compute='_compute_final_location_id')
    subcontracting_picking_id = fields.Many2one('purchase.order')
    po_qty = fields.Float(string='Ordered Qty (PO)', related='purchase_line_id.product_qty')
    po_price_unit = fields.Float(string='Price Unit (PO)', related='purchase_line_id.price_unit')
    po_total_price = fields.Float(string='Total ', compute='_compute_po_total_price')
    analytic_imputation_id = fields.Many2one('analytic.imputation', string='Analytic Imputation ', compute='_compute_analytic_imputation_id')
    user_id = fields.Many2one('res.users', string='Responsible ', related='picking_id.user_id')
    picking_partner_id = fields.Many2one('res.partner', string='Supplier ', related='picking_id.partner_id')
    line_sequence = fields.Integer(string='Item', compute='_compute_line_sequence', default=0)
    return_lots = fields.Text(string='Return lots')

    def _compute_line_sequence(self):
        for rec in self:
            if rec.picking_id:
                no = 1
                rec.line_sequence = 0
                for move in rec.picking_id.move_ids_without_package:
                    move.line_sequence = no
                    no += 1
            else:
                rec.line_sequence = 0

    @api.depends('purchase_line_id.analytic_imputation_id', 'purchase_line_id.order_id.analytic_imputation_id')
    def _compute_analytic_imputation_id(self):
        for rec in self:
            if rec.purchase_line_id.analytic_imputation_id:
                rec.analytic_imputation_id = rec.purchase_line_id.analytic_imputation_id
            elif rec.purchase_line_id.order_id.analytic_imputation_id:
                rec.analytic_imputation_id = rec.purchase_line_id.order_id.analytic_imputation_id
            else:
                rec.analytic_imputation_id = False

    @api.depends('purchase_line_id.price_unit', 'quantity_done')
    def _compute_po_total_price(self):
        for rec in self:
            if rec.po_price_unit and rec.quantity_done:
                rec.po_total_price = rec.po_price_unit * rec.quantity_done
            else:
                rec.po_total_price = 0

    @api.depends('product_id', 'location_dest_id')
    def _compute_final_location_id(self):
        for rec in self:
            final_location_id = self.env['stock.putaway.rule'].search([
                ('product_id', '=', rec.product_id.id),
                ('location_in_id', '=', rec.location_dest_id.id),
            ], limit=1).location_out_id
            rec.final_location_id = final_location_id if final_location_id else rec.location_dest_id

    def _compute_qty_to_deliver(self):
        for rec in self:
            so_line_id = self.env['sale.order.line'].search([
                ('order_id', '=', rec.picking_id.sale_id.id),
                ('product_template_id', '=', rec.product_id.product_tmpl_id.id),
            ], limit=1)
            rec.qty_to_deliver = so_line_id.qty_to_deliver if so_line_id else -1

    def _get_all_dest_moves(self):
        dest_moves = self.mapped('move_dest_ids')
        return self if not dest_moves else self | dest_moves._get_all_dest_moves()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('purchase_order_id'):
            for vals in vals_list:
                vals['subcontracting_picking_id'] = self.env.context.get('purchase_order_id')
        return super(StockMove, self).create(vals_list)

    def _prepare_procurement_values(self):
        """ Prepare specific key for moves or other componenets that will be created from a stock rule
        comming from a stock move. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        self.ensure_one()
        group_id = self.group_id or False
        if self.rule_id:
            if self.rule_id.group_propagation_option == 'fixed' and self.rule_id.group_id:
                group_id = self.rule_id.group_id
            elif self.rule_id.group_propagation_option == 'none':
                group_id = False
        return {
            'date_planned': self.date_expected,
            'move_dest_ids': self,
            'group_id': group_id,
            'route_ids': self.route_ids,
            'warehouse_id': self.warehouse_id or self.picking_id.picking_type_id.warehouse_id or self.picking_type_id.warehouse_id,
            'priority': self.priority,
            'is_mto': True if self.procure_method == 'make_to_order' else False
        }
