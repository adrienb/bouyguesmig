# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    internal_quant = fields.Boolean(compute='_compute_internal_quant', store=True)

    @api.depends('location_id', 'location_id.usage')
    def _compute_internal_quant(self):
        for rec in self:
            rec.internal_quant = rec.location_id and rec.location_id.usage == 'internal'

    #TODO : Verifier la modification, anciennenment la méthode était sur stock.inventory, la seule modification concerne les droits d'accès
    def _apply_inventory(self):
        move_vals = []
        if not self.user_has_groups('bouygues.bouygues_logistic_extended_sales_group,bouygues.bouygues_manager_sales_group,stock.group_stock_manager'):
            raise UserError(_('Only a stock manager and a logistic can validate an inventory adjustment.'))
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     out=True))
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
        moves._action_done()
        self.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.write({'inventory_quantity': 0, 'user_id': False})
        self.write({'inventory_diff_quantity': 0})
