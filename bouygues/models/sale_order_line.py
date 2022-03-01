# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from collections import defaultdict
from datetime import timedelta, datetime
import base64

from odoo.tools.misc import get_lang


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _default_analytic_imputation(self):
        for line in self:
            if line.order_id:
                line.analytic_imputation = line.order_id.analytic_imputation

    warehouse_id = fields.Many2one(compute='_compute_warehouse_id', readonly=False, store=True)
    can_edit_price = fields.Boolean(related='product_template_id.can_edit_price')
    is_from_matrix = fields.Boolean(default=False)
    analytic_imputation = fields.Char('Analytic Imputation', default=_default_analytic_imputation)
    can_edit_quantity = fields.Boolean(string='Can edit quantity ?', compute='_compute_can_edit_quantity', default=True)
    product_default_code = fields.Char(string='Internal Ref.', related='product_id.default_code')
    is_dropship = fields.Boolean(compute='_compute_is_dropship')
    is_mto = fields.Boolean(compute='_compute_is_mto')
    is_kit = fields.Boolean(compute='_compute_is_kit')
    is_service = fields.Boolean(compute='_compute_is_service')
    eco_product_created = fields.Boolean(default=False, copy=True)
    line_sequence = fields.Integer(string='Item', compute='_compute_line_sequence', default=0)
    rental_unit = fields.Selection([('week', 'week'), ('day', 'day'), ('month', 'month')], string='Unit')
    rental_price = fields.Monetary(string='Unit Price')
    duration = fields.Integer(string='Duration')

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

    @api.depends('product_id', 'product_id.route_ids', 'route_id')
    def _compute_is_dropship(self):
        for rec in self:
            rec.is_dropship = False
            if rec.product_id:
                for route in rec.product_id.route_ids:
                    if 'dropship' in route.name.lower():
                        rec.is_dropship = True

    @api.depends('product_id', 'product_id.bom_ids')
    def _compute_is_kit(self):
        for rec in self:
            rec.is_kit = False
            if rec.product_id:
                for bom in rec.product_id.bom_ids:
                    if bom.type == 'phantom':
                        rec.is_kit = True

    @api.depends('product_id', 'product_id.type')
    def _compute_is_service(self):
        for rec in self:
            rec.is_service = True if rec.product_id and rec.product_id.type == 'service' else False

    @api.depends('product_id', 'product_id.route_ids')
    def _compute_is_mto(self):
        for rec in self:
            rec.is_mto = False
            if rec.product_id:
                for route in rec.product_id.route_ids:
                    if 'mto' in route.name.lower():
                        rec.is_mto = True

    def _compute_warehouse_id(self):
        for rec in self:
            if rec.order_id and rec.order_id.warehouse_id:
                rec.warehouse_id = rec.order_id.warehouse_id
                rec._onchange_warehouse_id()
            else:
                rec.warehouse_id = False

    @api.depends('move_ids', 'move_ids.state')
    def _compute_can_edit_quantity(self):
        for rec in self:
            rec.can_edit_quantity = True
            if rec.move_ids:
                for move in rec.move_ids:
                    if move.state in ('partially_available', 'assigned', 'done'):
                        rec.can_edit_quantity = False
                        continue

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
         1. The quotation has a commitment_date, we take it as delivery date
         2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self:
            if not line.display_qty_widget:
                continue
            if line.order_id.commitment_date:
                date = line.order_id.commitment_date
            else:
                date = line._expected_date()
            grouped_lines[(line.warehouse_id.id, date)] |= line

        treated = self.browse()
        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[
                    line.product_id.id]
                if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today,
                                                                                        line.product_uom)
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today,
                                                                                   line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(
                        line.virtual_available_at_date, line.product_uom)
                qty_processed_per_product[line.product_id.id] += line.product_uom_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False
        remaining.warehouse_id = False

    @api.depends('product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.warehouse_id', 'order_id.commitment_date')
    def _compute_qty_at_date(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
         1. The quotation has a commitment_date, we take it as delivery date
         2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self:
            if not line.display_qty_widget:
                continue
            if not line.warehouse_id:
                line.warehouse_id = line.order_id.warehouse_id
            else:
                line.warehouse_id = line.warehouse_id
            if line.order_id.commitment_date:
                date = line.order_id.commitment_date
            else:
                date = line._expected_date()
            grouped_lines[(line.warehouse_id.id, date)] |= line
        treated = self.browse()
        for (warehouse, scheduled_date), lines in grouped_lines.items():
            model = self.env['product.product']
            self.env.add_to_compute(model._fields['qty_available'], lines.mapped('product_id'))
            self.env.add_to_compute(model._fields['free_qty'], lines.mapped('product_id'))
            self.env.add_to_compute(model._fields['virtual_available'], lines.mapped('product_id'))
            model.with_context(to_date=scheduled_date, warehouse=warehouse).recompute()
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                line.qty_available_today, line.free_qty_today, line.virtual_available_at_date = qties_per_product[line.product_id.id]
                # if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                #     line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
                #     line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
                #     line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False
        remaining.warehouse_id = False

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_planned = self.order_id.date_order \
                       + timedelta(days=self.customer_lead or 0.0) - timedelta(
            days=self.order_id.company_id.security_lead)
        values.update({
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'warehouse_id': self.warehouse_id or self.order_id.warehouse_id or False,
            'partner_id': self.order_id.partner_shipping_id.id,
            'company_id': self.order_id.company_id,
        })
        for line in self.filtered("order_id.commitment_date"):
            date_planned = fields.Datetime.from_string(line.order_id.commitment_date) - timedelta(
                days=line.order_id.company_id.security_lead)
            values.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return values

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sale_order_id = self.env['sale.order'].browse(vals.get('order_id'))
            if not vals.get('analytic_imputation') and sale_order_id:
                vals['analytic_imputation'] = sale_order_id.analytic_imputation
        return super(SaleOrderLine, self).create(vals_list)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
        )

        vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        if product.end_life:
            end_message = self.product_id.end_life_message if self.product_id.end_life_message else 'No message has been set'
            if (product.free_qty > 0 and not product.finish_stock) or product.free_qty == 0:
                if self.product_id.substitution_product_product_id:
                    self.product_id = self.product_id.substitution_product_product_id
                    self.name = self.product_id.display_name
                else:
                    self.product_id = False
            return {
                'warning': {
                    'title': _("Warning for %s") % product.name,
                    'message': end_message,
                }
            }

        if product.product_sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.product_sale_line_warn_msg
            if product.product_sale_line_warn == 'block':
                self.product_id = False
            return {
                'warning': {
                    'title': title,
                    'message': message,
                },
            }
        return {}

    def add_delivered(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Add delivered quantity'),
            'res_model': 'sale.order.service.delivered',
            'view_id': self.env.ref("bouygues.bouygues_sale_order_service_delivered_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    def edit_price_unit(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Edit Price Unit'),
            'res_model': 'sale.order.line.edit.price',
            'view_id': self.env.ref("bouygues.bouygues_sale_order_line_edit_price_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'product_uom', 'product_uom_qty',
            'tax_id', 'analytic_tag_ids'
        ]

    def extract_facture(self):
        filename = 'facture_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'ID V12 Client;Nom Client;Code article V12;Qté à facturer;Date;Date;Prix de vente unitaire;Remise;Réf Client;Numéro de série;Ligne commande / Article;Ligne commande / Imputation;Monter HT à facturer'

        fields = [
            'line.order_partner_id.id_v12',
            'line.order_partner_id.name',
            'line.product_id.code_v12',
            'line.qty_to_invoice',
            'line.scheduled_date',
            'line.scheduled_date',
            'line.price_unit',
            'line.discount',
            'line.order_id.client_order_ref',
            'lot',
            'line.name',
            'line.analytic_imputation',
            'line.price_subtotal',
        ]

        all_lines = self.env['sale.order.line'].search([('company_id', '=', self.env.company.id), ('qty_to_invoice', '>', 0)])

        row_data = ''

        for line in all_lines:
            for field in fields:
                if field == 'lot':
                    lot_name = []
                    for move in line.move_ids:
                        for move_line in move.move_line_ids:
                            if move_line.lot_id:
                                lot_name.append(move_line.lot_id.name)
                    value = ','.join(lot_name) if len(lot_name) > 0 else 'false'
                else:
                    value = str(eval(field))
                if value.lower() == 'false':
                    row_data += ';'
                else:
                    row_data += value + ';'
            row_data += '\n'

        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Facture - ' + datetime.now().strftime("%Y %m %d %H %M %S"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })



