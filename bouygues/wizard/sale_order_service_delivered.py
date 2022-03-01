# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderServiceDelivered(models.TransientModel):
    _name = 'sale.order.service.delivered'
    _description = 'Add delivered quantity'

    qty_delivered = fields.Float(string="Delivered Quantity", required=True)

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        sale_order_line_id = self.env['sale.order.line'].search([('id', '=', active_id)])
        sale_order_line_id.write({'qty_delivered': self.qty_delivered})
        sale_order_line_id.order_id.write({'add_delivered_used': not sale_order_line_id.order_id.add_delivered_used})

