# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrderServiceReceived(models.TransientModel):
    _name = 'purchase.order.service.received'
    _description = 'Add received quantity'

    qty_received = fields.Float(string="Received Quantity", required=True)

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        purchase_order_line_id = self.env['purchase.order.line'].search([('id', '=', active_id)])
        purchase_order_line_id.write({'qty_received': self.qty_received})
        purchase_order_line_id.order_id.write({'add_received_used': not purchase_order_line_id.order_id.add_received_used})

