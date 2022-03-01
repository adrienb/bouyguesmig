# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    description_pickingin = fields.Text(related='product_id.description_pickingin')
    currency_id = fields.Many2one("res.currency", related='move_id.sale_line_id.order_id.currency_id')
    price_tax = fields.Monetary(compute='_compute_amount', string='Total Tax', readonly=True, store=True, currency_field='currency_id')
    source_purchase_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True, compute='_compute_source_purchase_id')
    source_sale_id = fields.Many2one('sale.order', string='sale Order', readonly=True, compute='_compute_source_sale_id')
    return_lots = fields.Text(string='Return lots', related='move_id.return_lots')

    @api.depends('origin')
    def _compute_source_purchase_id(self):
        for rec in self:
            source_purchase_id = self.env['purchase.order'].search([('name', '=', rec.origin)])
            if source_purchase_id:
                rec.source_purchase_id = source_purchase_id
            else:
                rec.source_purchase_id = False

    @api.depends('origin')
    def _compute_source_sale_id(self):
        for rec in self:
            source_sale_id = self.env['sale.order'].search([('name', '=', rec.origin)])
            if source_sale_id:
                rec.source_sale_id = source_sale_id
            else:
                rec.source_sale_id = False

    @api.depends('qty_done', 'move_id.sale_line_id.discount', 'move_id.sale_line_id.price_unit', 'move_id.sale_line_id.tax_id')
    def _compute_amount(self):
        for line in self:
            if line.move_id.sale_line_id:
                price = line.move_id.sale_line_id.price_unit * (1 - (line.move_id.sale_line_id.discount or 0.0) / 100.0)
                taxes = line.move_id.sale_line_id.tax_id.compute_all(price, line.move_id.sale_line_id.order_id.currency_id, line.qty_done, product=line.move_id.sale_line_id.product_id, partner=line.move_id.sale_line_id.order_id.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                })
            else:
                line.update({
                    'price_tax': 0
                })
