# -*- coding: utf-8 -*-

from datetime import datetime
from functools import partial
from werkzeug import url_encode

from odoo import api, fields, models, tools, upgrade, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
import csv
import base64
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_type_ids = fields.One2many('package.type', 'picking_id', string='Type of Package')
    transporter_id = fields.Many2one('res.partner', string='Transporter', copy=False)
    preparator_id = fields.Many2one('res.partner', string='Preparator', copy=False)
    picking_contact_id = fields.Many2one('res.partner', string='Picking Contact', related='sale_id.picking_contact_id')
    contact_phone = fields.Char(string='Contact phone', related='picking_contact_id.phone')
    contact_mobile = fields.Char(string='Contact mobile', related='picking_contact_id.mobile')
    purchase_picking_contact_id = fields.Many2one('res.partner', string='Purchase Picking Contact', related='purchase_id.purchase_picking_contact_id')
    purchase_contact_phone = fields.Char(string='Purchase Contact phone', related='purchase_picking_contact_id.phone')
    purchase_contact_mobile = fields.Char(string='Purchase Contact mobile', related='purchase_picking_contact_id.mobile')
    contact_mail = fields.Char(string='Contact email', related='picking_contact_id.email')
    purchase_contact_mail = fields.Char(string='Purchase Contact email', related='purchase_picking_contact_id.email')
    sale_order_line_ids = fields.One2many(related='sale_id.order_line')
    currency_id = fields.Many2one("res.currency", related='sale_id.currency_id')
    amount_by_group = fields.Binary(compute='_amount_by_group')
    amount_untaxed = fields.Monetary(compute='_amount_all', currency_field='currency_id')
    amount_tax = fields.Monetary(compute='_amount_all', currency_field='currency_id')
    amount_total = fields.Monetary(compute='_amount_all', currency_field='currency_id')
    package_type_type_ids = fields.Many2many('package.type.type', compute='_compute_package_type_type_ids')
    real_delivery_date = fields.Date(string='Real delivery date', readonly=True, related='purchase_id.real_delivery_date')
    is_pick = fields.Boolean(string='Pick', related='picking_type_id.is_pick')
    is_out = fields.Boolean(string='Out', related='picking_type_id.is_out')
    is_receipt = fields.Boolean(string='Receipt', compute='_compute_is_receipt')
    is_resupply = fields.Boolean(string='Resupply', related='picking_type_id.is_resupply')
    dropship_note = fields.Text(string='Dropship Note')
    lock_user_id = fields.Many2one('res.users')
    is_manual_locked = fields.Boolean()
    is_printed = fields.Boolean(string='Is Printed', copy=False)
    subcontracting_po_count = fields.Integer(compute='_compute_subcontracting_po_count', string='Purchase Order Count')
    resupply_done = fields.Boolean(default=False, copy=False)
    total_weight = fields.Float(compute='_compute_total_weight')
    write_date = fields.Datetime(string='Write Date')
    updated_today = fields.Boolean(compute='_compute_updated_today', search='_search_updated_today')
    origin_po = fields.Char(string='Origin PO', compute='_compute_origin_po')
    ditrl_text = fields.Text(string='DITLR')
    dichm_text = fields.Text(string='DICHM')
    paqtl_text = fields.Text(string='PAQTL')
    locd_text = fields.Text(string='LOCD')
    warehouse_text_printed = fields.Boolean(string='Print on PDF')
    ditrl_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    dichm_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    paqtl_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    locd_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    top_litige = fields.Boolean(string='Top Litige')
    quality_code = fields.Char(string='Quality Code')
    booking_ref = fields.Char(string='Booking Reference')
    speedwms_ref = fields.Integer(string='Reference SpeedWMS')
    support_number = fields.Char(string='Support n°')
    weight = fields.Float(string='Weight')
    tracking_number = fields.Char(string='Tracking Number')
    picking_type_name = fields.Char(related='picking_type_id.name', string='Picking Type Name')
    picking_type_warehouse_id = fields.Many2one('stock.warehouse', related='picking_type_id.warehouse_id')
    tracking_number = fields.Char(string='Tracking Number')
    wms_exported = fields.Boolean(default=False, copy=False)
    return_lots = fields.Text(string='Return lots')
    is_return = fields.Boolean(copy=False)
    sale_client_order_ref = fields.Char(related='sale_id.client_order_ref')
    export_filename = fields.Char(string='Export Filename')
    import_filename = fields.Char(string='Import Filename')
    sale_client_order_ref = fields.Char(related='sale_id.client_order_ref')
    has_group_wms_admin = fields.Boolean(compute="_compute_has_group_wms_admin", default=False)
    partner_shipping_id = fields.Many2one('res.partner', string='Subcontracting Delivery Address')
    shipping_name = fields.Char(string='Name', related='partner_shipping_id.name')
    shipping_street = fields.Char(string='Street', related='partner_shipping_id.street')
    shipping_zip = fields.Char(string='ZIP', related='partner_shipping_id.zip')
    shipping_city = fields.Char(string='City', related='partner_shipping_id.city')
    intersite_ids = fields.Many2many('stock.picking.intersite', 'picking_rel', 'picking', 'intersite')
    is_dropship = fields.Boolean(string='Is Dropship', compute='_compute_is_dropship')
    kit_move_line_ids = fields.Many2many('stock.move.line', compute='_compute_kit_move_line_ids')

    @api.depends('move_line_ids_without_package')
    def _compute_kit_move_line_ids(self):
        for rec in self:
            kit_move_line_ids = self.env['stock.move.line']
            sale_line_id = []
            for move_line in rec.move_line_ids_without_package:
                if move_line.move_id.bom_line_id and move_line.move_id.bom_line_id.bom_id.type == 'phantom' and move_line.move_id.sale_line_id and move_line.move_id.sale_line_id.id not in sale_line_id:
                    kit_move_line_ids += move_line
                    sale_line_id.append(move_line.move_id.sale_line_id.id)
            rec.kit_move_line_ids = kit_move_line_ids if len(kit_move_line_ids) > 0 else False

    @api.depends('picking_type_id')
    def _compute_is_dropship(self):
        for r in self:
            r.is_dropship = True if 'dropship' in r.picking_type_id.name.lower() else False

    def _compute_has_group_wms_admin(self):
        for rec in self:
            rec.has_group_wms_admin = self.env.user.has_group('bouygues.bouygues_wms_admin')

    @api.depends('picking_type_id', 'picking_type_id.warehouse_id')
    def _compute_warehouse_boolean(self):
        for rec in self:
            rec.ditrl_warehouse = rec.picking_type_id.warehouse_id.code == 'DITLR'
            rec.dichm_warehouse = rec.picking_type_id.warehouse_id.code == 'DICHM'
            rec.paqtl_warehouse = rec.picking_type_id.warehouse_id.code == 'PAQTL'
            rec.locd_warehouse = rec.picking_type_id.warehouse_id.code == 'LOCD+'

    @api.depends('move_ids_without_package', 'move_ids_without_package.subcontracting_picking_id')
    def _compute_origin_po(self):
        for rec in self:
            origins = []
            for move in rec.move_ids_without_package:
                if move.subcontracting_picking_id:
                    origins.append(move.subcontracting_picking_id.name)
            rec.origin_po = ', '.join(origins)

    @api.depends('write_date')
    def _compute_updated_today(self):
        for rec in self:
            rec.updated_today = (
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) <= rec.write_date <= datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
            )

    def _search_updated_today(self, operator, value):
        today_pickings = self.env['stock.picking'].search([
            ('write_date', '>=', datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)),
            ('write_date', '<=', datetime.now().replace(hour=23, minute=59, second=59)),
        ])
        return [('id', 'in', today_pickings.ids)]

    @api.depends('move_line_ids_without_package', 'move_line_ids_without_package.product_id', 'move_line_ids_without_package.qty_done')
    def _compute_total_weight(self):
        total_weight = 0
        for move in self.move_line_ids_without_package:
            total_weight += move.qty_done*move.product_id.weight
        self.total_weight = total_weight

    @api.depends('picking_type_id')
    def _compute_is_receipt(self):
        for r in self:
            if r.picking_type_id.code == 'incoming':
                r.is_receipt = True
            else:
                r.is_receipt = False

    @api.depends('move_ids_without_package', 'move_ids_without_package.subcontracting_picking_id')
    def _compute_subcontracting_po_count(self):
        for rec in self:
            rec.subcontracting_po_count = len(rec.move_ids_without_package.subcontracting_picking_id)

    def action_view_sub_contracting_purchase_orders(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.move_ids_without_package.subcontracting_picking_id.ids)]
        return action

    def _compute_package_type_type_ids(self):
        for rec in self:
            rec.package_type_type_ids = self.env['package.type.type'].search([])

    def _amount_by_group(self):
        for rec in self:
            if rec.sale_id:
                currency = rec.sale_id.currency_id or rec.sale_id.company_id.currency_id
                fmt = partial(formatLang, self.with_context(lang=rec.sale_id.partner_id.lang).env,
                              currency_obj=currency)
                res = {}
                for line in rec.move_line_ids_without_package.filtered(lambda lline: not lline.move_id.bom_line_id and not lline.move_id.bom_line_id.bom_id.type == 'phantom'):
                    price_reduce = line.move_id.sale_line_id.price_reduce
                    taxes = line.move_id.sale_line_id.tax_id.compute_all(price_reduce,
                                                                         quantity=line.qty_done,
                                                                         product=line.product_id,
                                                                         partner=rec.sale_id.partner_shipping_id)[
                        'taxes']
                    for tax in line.move_id.sale_line_id.tax_id:
                        group = tax.tax_group_id
                        res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                        for t in taxes:
                            if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                                res[group]['amount'] += t['amount']
                                res[group]['base'] += t['base']

                for line in rec.kit_move_line_ids:
                    price_reduce = line.move_id.sale_line_id.price_reduce
                    taxes = line.move_id.sale_line_id.tax_id.compute_all(price_reduce,
                                                                         quantity=line.move_id.sale_line_id.product_uom_qty,
                                                                         product=line.product_id,
                                                                         partner=rec.sale_id.partner_shipping_id)[
                        'taxes']
                    for tax in line.move_id.sale_line_id.tax_id:
                        group = tax.tax_group_id
                        res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                        for t in taxes:
                            if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                                res[group]['amount'] += t['amount']
                                res[group]['base'] += t['base']
                res = sorted(res.items(), key=lambda l: l[0].sequence)
                rec.amount_by_group = [(
                    l[0].name, l[1]['amount'], l[1]['base'],
                    fmt(l[1]['amount']), fmt(l[1]['base']),
                    len(res),
                ) for l in res]
            else:
                rec.amount_by_group = False

    def action_cancel(self):
        if self.user_has_groups('bouygues.bouygues_supplier_sales_group,!bouygues.bouygues_supplier_extended_sales_group,!bouygues.bouygues_manager_sales_group,!stock.group_stock_user'):
            for rec in self:
                if rec.picking_type_id.sequence_code not in ['IN']:
                    raise UserError(_('Supplier should only be able to delete IN Stock Picking'))
        super(StockPicking, self).action_cancel()

    @api.depends('move_line_ids_without_package')
    def _amount_all(self):
        for rec in self:
            amount_untaxed = amount_tax = 0.0
            for line in rec.move_line_ids_without_package.filtered(lambda line: not line.move_id.bom_line_id and not line.move_id.bom_line_id.bom_id.type == 'phantom'):
                if line.move_id.sale_line_id:
                    amount_untaxed += line.move_id.sale_line_id.price_reduce * line.qty_done
                    amount_tax += line.price_tax
            for line in rec.kit_move_line_ids:
                amount_untaxed += line.move_id.sale_line_id.price_reduce * line.move_id.sale_line_id.product_uom_qty
                amount_tax += line.move_id.sale_line_id.price_tax
            rec.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def action_done(self):
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(
            lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            if pick.owner_id:
                pick.move_lines.write({'restrict_partner_id': pick.owner_id.id})
                pick.move_line_ids.write({'owner_id': pick.owner_id.id})

            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                        'name': _('New Move:') + ops.product_id.display_name,
                        'product_id': ops.product_id.id,
                        'product_uom_qty': ops.qty_done,
                        'product_uom': ops.product_uom_id.id,
                        'description_picking': ops.description_picking,
                        'location_id': pick.location_id.id,
                        'location_dest_id': pick.location_dest_id.id,
                        'picking_id': pick.id,
                        'picking_type_id': pick.picking_type_id.id,
                        'restrict_partner_id': pick.owner_id.id,
                        'company_id': pick.company_id.id,
                    })
                    ops.move_id = new_move.id
                    new_move = new_move._action_confirm()
                    todo_moves |= new_move
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))

        if not self.env.context.get('custom_date_done'):
            self.write({'date_done': fields.Datetime.now()})
        self._send_confirmation_email()

        new_package_type_ids_values = []
        for package_type in self.package_type_ids:
            values = {
                'package_type_id': package_type.package_type_id.id,
                'weight': package_type.weight,
                'number': package_type.number,
                'location': package_type.location,
            }
            new_package_type_ids_values.append(values)
        all_pickings = self.env['stock.picking']
        for move in self.move_ids_without_package:
            all_moves = move._get_all_dest_moves()
            all_pickings |= all_moves.mapped('picking_id')
        for picking in all_pickings:
            if picking != self:
                picking.write({
                    'package_type_ids': [(0, 0, package) for package in new_package_type_ids_values],
                    'preparator_id': self.preparator_id.id,
                    'transporter_id': self.transporter_id.id,
                })

        return True

    def button_validate(self):
        for rec in self:
            if rec.picking_type_id.is_out and not rec.transporter_id:
                raise UserError(_('You must have a transporter'))
            if rec.picking_type_id.code == 'incoming':
                for move in rec.move_ids_without_package:
                    if move.is_subcontract:
                        subcontracting_move_ids = self.env['stock.move'].search([
                            ('subcontracting_picking_id', '=', move.subcontracting_picking_id.id),
                            ('is_subcontract', '=', False),
                        ])
                        subcontracting_picking_ids = self.env['stock.picking'].search([
                            '&',
                                '&',
                                    ('state', 'not in', ['done', 'cancel']),
                                    ('id', 'in', subcontracting_move_ids.mapped('picking_id').ids),
                                '|',
                                    ('is_out', '=', True),
                                    ('is_pick', '=', True),
                        ])
                        if len(subcontracting_picking_ids) > 0:
                            raise UserError(_('You must first validate your PICK/OUT pickings'))
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if rec.picking_type_id.code == 'incoming' and rec.picking_type_id.warehouse_id == self.env.ref(
                    'boa.warehouse_paquetage'):
                template_id = self.env.ref('bouygues.bouygues_mail_template_reception_validation')
                values = template_id.generate_email(rec.id, fields=None)
                values['email_to'] = rec.picking_type_id.warning_user_id.login
                values['email_from'] = rec.company_id.email
                mail = self.env['mail.mail'].create(values)
                mail.send()
        return res

    def write(self, vals):
        for rec in self:
            if self.env.context.get('intersite_id'):
                vals['intersite_ids'] = [(4, self.env.context.get('intersite_id'))]
            if rec.is_manual_locked and self.env.user != rec.lock_user_id and not self.env.user.has_group(
                    'stock.group_stock_manager'):
                raise UserError(_('The picking is locked'))
            elif rec.is_manual_locked:
                vals['lock_user_id'] = False
                vals['is_manual_locked'] = False
            if rec.picking_type_id.is_resupply and not rec.resupply_done:
                vals['resupply_done'] = True
                if not rec.backorder_id:
                    vals['origin'] = 'Intersite ' + str(datetime.now().date())
                else:
                    vals['origin'] = rec.backorder_id.origin
                vals['partner_id'] = rec.picking_type_id.resupply_contact_id.id
            if rec.resupply_done and ('origin' in vals or 'partner_id' in vals):
                if rec.origin:
                    vals['origin'] = rec.origin
                if rec.partner_id:
                    vals['partner_id'] = rec.partner_id.id
        return super(StockPicking, self).write(vals)

    def action_lock_picking(self):
        for rec in self:
            if rec.is_manual_locked:
                raise UserError(_('The pick is already locked'))
            rec.lock_user_id = self.env.user
            rec.is_manual_locked = True

    def action_delock_picking(self):
        for rec in self:
            if rec.lock_user_id == self.env.user or self.env.user.has_group('stock.group_stock_manager'):
                rec.lock_user_id = False
                rec.is_manual_locked = False
            else:
                raise UserError(_('Only the admin or the user who locked the picking can unlock it'))

    def action_done_picking(self):
        for rec in self:
            pickings = self.env['stock.picking']
            for move in rec.move_ids_without_package:
                for dest_move in move.move_dest_ids:
                    pickings |= dest_move.picking_id
            list(set(pickings))
            rec.action_done()
            for pick in pickings:
                for move in pick.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                pick.action_done()
                template = self.env.ref('bouygues.bouygues_mail_template_stock_picking_delivery_report', raise_if_not_found=False)

                if template:
                    if pick.picking_contact_id.email:
                        email_values = {'email_to': str(pick.picking_contact_id.email), 'email_from': 'noreplydistrimo@bouygues-construction.com'}
                        template.send_mail(pick.id, email_values=email_values, force_send=True)
                    if pick.sale_id.pablo_order_creator_id.email:
                        email_values = {'email_to': str(pick.sale_id.pablo_order_creator_id.email), 'email_from': 'noreplydistrimo@bouygues-construction.com'}
                        template.send_mail(pick.id, email_values=email_values, force_send=True)

    @api.model
    def create(self, vals):
        if self.env.context.get('intersite_id'):
            vals['intersite_ids'] = [(4, self.env.context.get('intersite_id'))]
        if self.env.context.get('dropship_note'):
            vals['dropship_note'] = self.env.context.get('dropship_note')
        if vals.get('picking_type_id'):
            picking_type_id = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
            if self.env.context.get('subcontracting_partner_shipping_id') and (picking_type_id.is_pick or picking_type_id.is_out):
                vals['partner_shipping_id'] = self.env.context.get('subcontracting_partner_shipping_id')
            if picking_type_id.is_resupply:
                if not vals.get('backorder_id'):
                    vals['origin'] = 'Intersite ' + str(datetime.now().date())
                else:
                    backorder_picking = self.env['stock.picking'].browse(vals.get('backorder_id'))
                    vals['printed'] = backorder_picking.printed
                    vals['origin'] = backorder_picking.origin
                vals['partner_id'] = picking_type_id.resupply_contact_id.id
            if self.env.context.get('purchase_order_id'):
                purchase_order_id = self.env['purchase.order'].browse(self.env.context.get('purchase_order_id'))
                if picking_type_id.code == 'incoming':
                    vals['user_id'] = purchase_order_id.user_id.id
                if self.env.context.get('dropship_note_po'):
                    if picking_type_id.is_pick or picking_type_id.is_out:
                        vals['dropship_note'] = self.env.context.get('dropship_note_po')
        return super(StockPicking, self).create(vals)

    @api.depends('state', 'is_locked', 'is_out')
    def _compute_show_validate(self):
        for picking in self:
            if picking.state in ('waiting', 'confirmed') and picking.is_out:
                picking.show_validate = False
            elif not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned') or not picking.is_locked:
                picking.show_validate = False
            else:
                picking.show_validate = True

    def _mark_pickings_printed(self):
        pickings = self.env['stock.picking'].search(
            [('state', 'not in', ['done', 'cancel']), ('is_resupply', '=', True)])
        for picking in pickings:
            picking.printed = True

    def action_print_subcontracting_report(self):
        for rec in self:
            rec.is_printed = True
        return self.env.ref('bouygues.action_subcontracting_delivery_report_bouygues').report_action(self)

    def action_print_delivery_report(self):
        for rec in self:
            rec.is_printed = True
        return self.env.ref('bouygues.action_delivery_report_bouygues').report_action(self)

    def action_print_reception_report(self):
        for rec in self:
            rec.is_printed = True
        return self.env.ref('bouygues.action_reception_report_bouygues').report_action(self)

    def action_print_preparation_report(self):
        for rec in self:
            rec.is_printed = True
        return self.env.ref('bouygues.action_preparation_report_bouygues').report_action(self)

    def _prepare_subcontract_mo_vals(self, subcontract_move, bom):
        subcontract_move.ensure_one()
        picking_found = False
        pickings = self.env['stock.picking'].search([
            ('partner_id', '=', self.partner_id.id),
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_dest_id.id),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned']),
        ])
        for picking in pickings:
            if len(picking.move_ids_without_package) > 0:
                if picking.move_ids_without_package[0].subcontracting_picking_id.id == self.env.context.get('purchase_order_id'):
                    picking_found = True
        if picking_found:
            group = picking.group_id
        else:
            group = self.env['procurement.group'].create({
                'name': self.name,
                'partner_id': self.partner_id.id,
            })
        product = subcontract_move.product_id
        warehouse = self._get_warehouse(subcontract_move)
        vals = {
            'company_id': subcontract_move.company_id.id,
            'procurement_group_id': group.id,
            'product_id': product.id,
            'product_uom_id': subcontract_move.product_uom.id,
            'bom_id': bom.id,
            'location_src_id': subcontract_move.picking_id.partner_id.with_context(force_company=subcontract_move.company_id.id).property_stock_subcontractor.id,
            'location_dest_id': subcontract_move.picking_id.partner_id.with_context(force_company=subcontract_move.company_id.id).property_stock_subcontractor.id,
            'product_qty': subcontract_move.product_uom_qty,
            'picking_type_id': warehouse.subcontracting_type_id.id,
        }
        return vals

    def validate_pickings_in(self):
        picking_ids = self.filtered(lambda x: x.picking_type_id.code == 'incoming')
        pick_to_do = self.env['stock.picking']
        for picking in picking_ids:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        if pick_to_do:
            pick_to_do.action_done()
        return False

    def _send_mail_reception_to_process(self):
        pickings_dic = self.env['stock.picking'].read_group([('company_id', '!=', 1), ('state', '=', 'assigned'), ('picking_type_code', '=', 'incoming'), ('scheduled_date', '<', datetime.now())], ['id'], ['user_id'])
        action = self.env.ref('bouygues.bouygues_action_stock_picking_in_mail')
        action['domain'] = [('state', '=', 'assigned'), ('picking_type_code', '=', 'incoming'), ('scheduled_date', '<', datetime.now())]
        action_url = '%s/web#%s' % (
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    url_encode({
                        'action': action.id,
                        'active_model': 'stock.picking',
                        'menu_id': self.env.ref('stock.menu_stock_root').id})
                    )
        button = "<p><a style='background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;' href=%s>View receptions</a></p>" % (action_url)
        for user in pickings_dic:
            no_pickings = str(user['user_id_count'])
            values = self.env.ref('bouygues.bouygues_mail_template_reception_to_process').generate_email(self.id, fields=None)
            if user['user_id'] and user['user_id'][0] and self.env['res.users'].browse(user['user_id'][0]).login and self.env.company.email:
                values['email_from'] = self.env.company.email
                values['email_to'] = self.env['res.users'].browse(user['user_id'][0]).login
                values['body_html'] = '<p>Bonjour, <br/><br/>Vous avez ' + no_pickings + ' commande(s) non réceptionnée(s) et avec une date de livraison dépassée.<br/>Merci de faire le nécessaire. <br/>Lien vers le menu Réceptions (sauf Distrimo) : <br/></p>' + button + '<br/>Ce mail est envoyé automatiquement, merci de ne pas y répondre.'
                values['body'] = tools.html_sanitize(values['body_html'])
                mail = self.env['mail.mail'].create(values)
                mail.send()



