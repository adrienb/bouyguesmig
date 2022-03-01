import json
from odoo import api, _, fields
from odoo.exceptions import ValidationError, UserError
from odoo.addons.sale_product_matrix.models.sale_order import SaleOrder
from odoo.addons.purchase_product_matrix.models.purchase import PurchaseOrder
from odoo.addons.stock.wizard.stock_picking_return import ReturnPicking


def _create_returns(self):
    # TODO sle: the unreserve of the next moves could be less brutal
    for return_move in self.product_return_moves.mapped('move_id'):
        return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

    product_ids = []
    for r_move in self.product_return_moves:
        product_ids.append(r_move.product_id.id)

    lot_dic = {}
    for move in self.picking_id.move_line_ids_without_package:
        if move.product_id.id in product_ids and move.lot_id:
            if lot_dic.get(move.product_id.id):
                lot_dic[move.product_id.id] = lot_dic.get(move.product_id.id) + ', ' + move.lot_id.name
            else:
                lot_dic[move.product_id.id] = move.lot_id.name

    # create new picking for returned products
    picking_type_id = self.picking_type_id.id
    # picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
    new_picking = self.picking_id.copy({
        'move_lines': [],
        'picking_type_id': picking_type_id,
        'state': 'draft',
        'is_return': True,
        'origin': _("Return of %s") % self.picking_id.name,
        'location_id': self.picking_id.location_dest_id.id,
        'location_dest_id': self.picking_type_id.default_location_dest_id.id})
    new_picking.message_post_with_view('mail.message_origin_link',
                                       values={'self': new_picking, 'origin': self.picking_id},
                                       subtype_id=self.env.ref('mail.mt_note').id)
    returned_lines = 0
    for return_line in self.product_return_moves:
        if not return_line.move_id:
            raise UserError(_("You have manually created product lines, please delete them to proceed."))
        # TODO sle: float_is_zero?
        if return_line.quantity:
            returned_lines += 1
            vals = self._prepare_move_default_values(return_line, new_picking, lot_dic)
            r = return_line.move_id.copy(vals)
            vals = {}

            # +--------------------------------------------------------------------------------------------------------+
            # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
            # |              | returned_move_ids              ↑                                  | returned_move_ids
            # |              ↓                                | return_line.move_id              ↓
            # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
            # +--------------------------------------------------------------------------------------------------------+
            move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
            # link to original move
            move_orig_to_link |= return_line.move_id
            # link to siblings of original move, if any
            move_orig_to_link |= return_line.move_id \
                .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel')) \
                .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
            move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
            # link to children of originally returned moves, if any. Note that the use of
            # 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
            # instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
            # return directly to the destination moves of its parents. However, the return of
            # the return will be linked to the destination moves.
            move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids') \
                .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel')) \
                .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
            vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
            vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
            r.write(vals)
    if not returned_lines:
        raise UserError(_("Please specify at least one non-zero quantity."))

    new_picking.action_confirm()
    new_picking.action_assign()
    return new_picking.id, picking_type_id


ReturnPicking._create_returns = _create_returns


@api.onchange('grid')
def _apply_grid(self):
    """Apply the given list of changed matrix cells to the current SO."""
    if self.grid and self.grid_update:
        has_res = False
        grid = json.loads(self.grid)
        product_template = self.env['product.template'].browse(grid['product_template_id'])
        dirty_cells = grid['changes']
        Attrib = self.env['product.template.attribute.value']
        default_so_line_vals = {}
        new_lines = []
        for cell in dirty_cells:
            combination = Attrib.browse(cell['ptav_ids'])
            no_variant_attribute_values = combination - combination._without_no_variant_attributes()

            # create or find product variant from combination
            product = product_template._create_product_variant(combination)
            order_lines = self.order_line.filtered(
                lambda line: (line._origin or line).product_id == product and (
                            line._origin or line).product_no_variant_attribute_value_ids == no_variant_attribute_values)

            # if product variant already exist in order lines
            old_qty = sum(order_lines.mapped('product_uom_qty'))
            qty = cell['qty']
            diff = qty - old_qty
            # TODO keep qty check? cannot be 0 because we only get cell changes ...
            if diff and order_lines:
                if qty == 0:
                    if self.state in ['draft', 'sent']:
                        # Remove lines if qty was set to 0 in matrix
                        # only if SO state = draft/sent
                        self.order_line -= order_lines
                    else:
                        order_lines.update({'product_uom_qty': 0.0})
                else:
                    """
                    When there are multiple lines for same product and its quantity was changed in the matrix,
                    An error is raised.

                    A 'good' strategy would be to:
                        * Sets the quantity of the first found line to the cell value
                        * Remove the other lines.

                    But this would remove all business logic linked to the other lines...
                    Therefore, it only raises an Error for now.
                    """
                    if len(order_lines) > 1:
                        raise ValidationError(_(
                            "You cannot change the quantity of a product present in multiple sale lines."))
                    else:
                        if not default_so_line_vals:
                            OrderLine = self.env['sale.order.line']
                            default_so_line_vals = OrderLine.default_get(OrderLine._fields.keys())
                        last_sequence = self.order_line[-1:].sequence
                        if last_sequence:
                            default_so_line_vals['sequence'] = last_sequence + 1
                        new_lines.append((0, 0, dict(
                            default_so_line_vals,
                            product_id=product.id,
                            product_uom_qty=diff,
                            product_no_variant_attribute_value_ids=no_variant_attribute_values.ids,
                            is_from_matrix=True)
                                          ))
            elif diff and not order_lines:
                if not default_so_line_vals:
                    OrderLine = self.env['sale.order.line']
                    default_so_line_vals = OrderLine.default_get(OrderLine._fields.keys())
                last_sequence = self.order_line[-1:].sequence
                if last_sequence:
                    default_so_line_vals['sequence'] = last_sequence + 1
                new_lines.append((0, 0, dict(
                    default_so_line_vals,
                    product_id=product.id,
                    product_uom_qty=qty,
                    product_no_variant_attribute_value_ids=no_variant_attribute_values.ids,
                    is_from_matrix=True)
                                  ))
        if new_lines:
            message = ''
            result = {}
            warning = {}
            self.update(dict(order_line=new_lines))
            for line in self.order_line.filtered(
                    lambda line: line.product_template_id == product_template):
                if line.is_from_matrix:
                    line.state = 'draft'
                    line.analytic_imputation = self.analytic_imputation
                    line.is_from_matrix = False
                if line.product_id.product_sale_line_warn != 'no-message':
                    message += line.product_id.display_name + ' : ' + line.product_id.product_sale_line_warn_msg + '\n'
                    warning['title'] = _("Warning")
                    warning['message'] = message
                    result = {'warning': warning}
                    has_res = True
                    if line.product_id.product_sale_line_warn == 'block':
                        line.product_id = False

                line.product_id_change()
                line._onchange_discount()
        if has_res:
            return result


SaleOrder._apply_grid = _apply_grid


@api.onchange('grid')
def _apply_grid_purchase(self):
    if self.grid and self.grid_update:
        has_res = False
        grid = json.loads(self.grid)
        product_template = self.env['product.template'].browse(grid['product_template_id'])
        dirty_cells = grid['changes']
        Attrib = self.env['product.template.attribute.value']
        default_po_line_vals = {}
        new_lines = []
        for cell in dirty_cells:
            combination = Attrib.browse(cell['ptav_ids'])
            no_variant_attribute_values = combination - combination._without_no_variant_attributes()

            # create or find product variant from combination
            product = product_template._create_product_variant(combination)
            # TODO replace the check on product_id by a first check on the ptavs and pnavs?
            # and only create/require variant after no line has been found ???
            order_lines = self.order_line.filtered(lambda line: (line._origin or line).product_id == product and (line._origin or line).product_no_variant_attribute_value_ids == no_variant_attribute_values)

            # if product variant already exist in order lines
            old_qty = sum(order_lines.mapped('product_qty'))
            qty = cell['qty']
            diff = qty - old_qty
            if diff and order_lines:
                if qty == 0:
                    if self.state in ['draft', 'sent']:
                        # Remove lines if qty was set to 0 in matrix
                        # only if SO state = draft/sent
                        self.order_line -= order_lines
                    else:
                        order_lines.update({'product_qty': 0.0})
                else:
                    """
                    When there are multiple lines for same product and its quantity was changed in the matrix,
                    An error is raised.

                    A 'good' strategy would be to:
                        * Sets the quantity of the first found line to the cell value
                        * Remove the other lines.

                    But this would remove all business logic linked to the other lines...
                    Therefore, it only raises an Error for now.
                    """
                    if len(order_lines) > 1:
                        raise ValidationError(_("You cannot change the quantity of a product present in multiple purchase lines."))
                    else:
                        order_lines[0].product_qty = qty
                        order_lines[0]._onchange_quantity()
                        # If we want to support multiple lines edition:
                        # removal of other lines.
                        # For now, an error is raised instead
                        # if len(order_lines) > 1:
                        #     # Remove 1+ lines
                        #     self.order_line -= order_lines[1:]
            elif diff:
                if not default_po_line_vals:
                    OrderLine = self.env['purchase.order.line']
                    default_po_line_vals = OrderLine.default_get(OrderLine._fields.keys())
                last_sequence = self.order_line[-1:].sequence
                if last_sequence:
                    default_po_line_vals['sequence'] = last_sequence
                new_lines.append((0, 0, dict(
                    default_po_line_vals,
                    product_id=product.id,
                    product_qty=qty,
                    product_no_variant_attribute_value_ids=no_variant_attribute_values.ids)
                ))
        if new_lines:
            message = ''
            result = {}
            warning = {}
            self.update(dict(order_line=new_lines))
            for line in self.order_line.filtered(lambda line: line.product_template_id == product_template):
                if line.product_id.product_sale_line_warn != 'no-message':
                    message += line.product_id.display_name + ' : ' + line.product_id.product_sale_line_warn_msg + '\n'
                    warning['title'] = _("Warning")
                    warning['message'] = message
                    result = {'warning': warning}
                    has_res = True
                    if line.product_id.product_sale_line_warn == 'block':
                        line.product_id = False
                line._product_id_change()
                line._onchange_quantity()
            if has_res:
                return result


PurchaseOrder._apply_grid = _apply_grid_purchase
