# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderLineEditPrice(models.TransientModel):
    _name = 'sale.order.line.edit.price'
    _description = 'Edit Price Unit'

    price_unit = fields.Float(string="Price Unit", required=True)

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        sale_order_line_id = self.env['sale.order.line'].search([('id', '=', active_id)])
        sale_order_line_id.write({'price_unit': self.price_unit})

