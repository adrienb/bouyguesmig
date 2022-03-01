# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    internal_ref = fields.Char(string='Internal Ref', related='product_id.default_code')
    supplier_ref = fields.Char(string='Supplier Ref', compute='_compute_supplier_ref')
    analytic_imputation_id = fields.Many2one('analytic.imputation', string='Analytic Imputation')
    manual_internal_ref = fields.Char(string='Internal Ref.')
    line_sequence = fields.Integer(string='Item')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    origin_document = fields.Char(string='Origin Document')
    sale_order_ids = fields.Many2many('sale.order', string='Linked sale.order', readonly=True)
    line_sequence = fields.Integer(string='Item', compute='_compute_line_sequence', default=0)
    so_origins = fields.Char(string='Origins', compute='_compute_so_origins')
    eco_product_created = fields.Boolean(default=False, copy=True)
    can_edit_price = fields.Boolean(related='product_template_id.can_edit_price')
    user_id = fields.Many2one('res.users', string='Purchase Responsible', related='order_id.user_id')
    date_approve = fields.Datetime(string='Confirmation Date', related='order_id.date_approve')

    def _compute_line_sequence(self):
        for rec in self:
            if rec.order_id:
                no = 1
                rec.line_sequence = 0
                for line in rec.order_id.order_line:
                    line.line_sequence = no
                    no += 1
            else:
                rec.line_sequence = 0

    @api.depends('sale_order_ids')
    def _compute_so_origins(self):
        for rec in self:
            origin_list = []
            for sale_order in rec.sale_order_ids:
                origin_list.append(sale_order.name)
            rec.so_origins = ', '.join(origin_list) if len(origin_list) > 0 else ''

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit * (1 - (self.discount or 0.0) / 100.0),
            'currency_id': self.order_id.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
            'discount': self.discount
        }

    @api.depends('product_template_id', 'product_template_id.seller_ids', 'partner_id')
    def _compute_supplier_ref(self):
        for rec in self:
            rec.supplier_ref = False
            if rec.product_template_id.seller_ids:
                for seller in rec.product_template_id.seller_ids:
                    if seller.name == rec.order_id.partner_id and rec.product_id == seller.product_id:
                        rec.supplier_ref = seller.product_code

    @api.model
    def create(self, values):
        if not values.get('analytic_imputation_id'):
            purchase_order_id = self.env['purchase.order'].browse(values.get('order_id'))
            if purchase_order_id:
                values['analytic_imputation_id'] = purchase_order_id.analytic_imputation_id.id
        return super(PurchaseOrderLine, self).create(values)

    @api.onchange('product_id')
    def onchange_product_id_warning(self):
        if not self.product_id or not self.env.user.has_group('purchase.group_warning_purchase'):
            return

        product_info = self.product_id

        if product_info.product_purchase_line_warn != 'no-message':
            title = _("Warning for %s") % product_info.name
            message = product_info.product_purchase_line_warn_msg
            if product_info.product_purchase_line_warn == 'block':
                self.product_id = False
            return {
                'warning': {
                    'title': title,
                    'message': message,
                }
            }
        return {}

    def add_received(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Add received quantity'),
            'res_model': 'purchase.order.service.received',
            'view_id': self.env.ref("bouygues.bouygues_purchase_order_service_received_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    def edit_price_unit(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Edit Price Unit'),
            'res_model': 'purchase.order.line.edit.price',
            'view_id': self.env.ref("bouygues.bouygues_purchase_order_line_edit_price_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action
