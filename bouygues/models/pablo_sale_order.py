# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


PABLO_STATE = [
    ('draft', "Draft"),
    ('done', "Done"),
    ('cancel', "Cancelled"),
    ('doublon', "Doublon"),
]


class PabloSaleOrder(models.Model):
    _name = 'pablo.sale.order'
    _description = 'Pablo Sale Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    customer_id = fields.Many2one('res.partner', string='Customer')
    import_customer = fields.Char(string='Import Customer')
    delivery_address_id = fields.Many2one('res.partner', string='Delivery Address')
    delivery_name = fields.Char(string='Delivery Name', related='delivery_address_id.name')
    delivery_street = fields.Char(string='Street', related='delivery_address_id.street')
    delivery_zip = fields.Char(string='ZIP', related='delivery_address_id.zip')
    delivery_city = fields.Char(string='City', related='delivery_address_id.city')
    import_delivery_address = fields.Char(string='Import Delivery Address')
    import_delivery_address_street = fields.Char(string='Import Street')
    import_delivery_address_city_zip = fields.Char(string='Import ZIP/City')
    picking_contact_id = fields.Many2one('res.partner', string='Picking Contact')
    import_pablo_order_creator_id = fields.Char(string='Import Pablo Order Creator')
    pablo_order_creator_id = fields.Many2one('res.partner', string='Pablo Order Creator')
    import_picking_contact = fields.Char(string='Import Picking Contact')
    import_picking_contact_2 = fields.Char(string='Import Picking Contact 2')
    analytic_imputation = fields.Char(string='Analytic Imputation')
    pablo_sale_order_line_ids = fields.One2many('pablo.sale.order.line', 'pablo_sale_order_id')
    pablo_import_id = fields.Many2one('pablo.import', string='Pablo Import')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order Created')
    pablo_sale_order_state = fields.Selection(readonly=True, selection=PABLO_STATE, copy=False)
    pablo_pdf = fields.Char(string='Pablo PDF')
    customer_ref = fields.Char(string='Customer Reference')
    company_id = fields.Many2one('res.company', string='Company', related='pablo_import_id.company_id')
    pablo_note = fields.Text(string='Pablo Note')
    picking_contact_mobile = fields.Char(string='Contact Mobile', related='picking_contact_id.mobile')
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the type.type without removing it.")

    def action_cancel(self):
        self.write({'pablo_sale_order_state': 'cancel'})

    def import_sale_order(self):
        if self.customer_id and self.delivery_address_id:
            # Check if there is a blocking message on products
            warning = False
            blocking = False
            message = ''
            for product_line in self.pablo_sale_order_line_ids:
                if product_line.product_id.product_sale_line_warn == 'block':
                    blocking = True
                    message += product_line.product_id.display_name + ' (BLOQUANT) : ' + product_line.product_id.product_sale_line_warn_msg + '\n'
                if product_line.product_id.product_sale_line_warn == 'warning':
                    warning = True
                    message += product_line.product_id.display_name + ' (NON BLOQUANT) : ' + product_line.product_id.product_sale_line_warn_msg + '\n'
            if blocking:
                raise UserError(_(message))

            warehouse = False
            if self.delivery_address_id.country_id.code == 'FR':
                zip_id = self.env['res.zip'].search([('name', '=', self.delivery_address_id.zip)], limit=1)
                warehouse = zip_id.warehouse_id
            if not warehouse:
                warehouse = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id') or self.env['stock.warehouse'].search(
                    [('company_id', '=', self.company_id.id)], limit=1) or self.env['stock.warehouse'].search(
                    [('company_id', '=', self.env.company.id)], limit=1)

            pablo_note = self.pablo_note if self.pablo_note else ''
            so_note = self.customer_id.so_note if self.customer_id.so_note else ''

            so_id = self.env['sale.order'].create({
                'partner_id': self.customer_id.id,
                'partner_shipping_id': self.delivery_address_id.id,
                'picking_contact_id': self.picking_contact_id.id,
                'pablo_order_creator_id': self.pablo_order_creator_id.id,
                'client_order_ref': self.customer_ref,
                'analytic_imputation': self.analytic_imputation,
                'pablo_import_user_id': self.env.user.id,
                'so_note': so_note + ' ' + pablo_note,
                'warehouse_id': warehouse.id if warehouse else False,
            })
            line_values = []
            for line in self.pablo_sale_order_line_ids:
                line_values.append({
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.imported_price,
                    'order_id': so_id.id,
                    'analytic_imputation': line.analytic_imputation,
                })

            if self.pablo_sale_order_line_ids:
                self.env['sale.order.line'].create(line_values)
            self.write({
                'pablo_sale_order_state': 'done',
                'sale_order_id': so_id.id,
            })

            if warning:
                action = ({
                    'type': 'ir.actions.act_window',
                    'name': _('Pablo Sale Order Warning'),
                    'res_model': 'pablo.sale.order.warning',
                    'view_id': self.env.ref("bouygues.pablo_sale_order_warning_action_view_form").id,
                    'target': 'new',
                    'view_mode': 'form',
                    'context': {
                        'warning_msg': message,
                    },
                })
                return action
        else:
            raise UserError(_('You need a customer and a delivery address'))




