# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PabloSaleOrderLine(models.Model):
    _name = 'pablo.sale.order.line'
    _description = 'Pablo Sale Order Line'

    imported_price = fields.Float(string='Imported Price')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float(string='Price')
    pablo_sale_order_id = fields.Many2one('pablo.sale.order')
    product_template_id = fields.Many2one('product.template', string='Product Template')
    product_uom_qty = fields.Float(string='Quantity')
    analytic_imputation = fields.Char(string='Analytic Imputation')
    pablo_ref = fields.Char(string='Pablo Ref')
    end_of_life = fields.Boolean(compute='_compute_end_life')
    not_sellable = fields.Boolean(compute='_compute_end_life')

    @api.depends('product_id')
    def _compute_end_life(self):
        for rec in self:
            rec.end_of_life = False
            rec.not_sellable = False
            if rec.product_id.end_life:
                rec.end_of_life = True
                if rec.product_id.free_qty == 0:
                    rec.not_sellable = True
