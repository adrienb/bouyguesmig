# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrderLineEditPrice(models.TransientModel):
    _name = 'purchase.order.line.edit.price'
    _description = 'Edit Price Unit'

    price_unit = fields.Float(string="Price Unit", required=True)

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        purchase_order_line_id = self.env['purchase.order.line'].search([('id', '=', active_id)])
        purchase_order_line_id.write({'price_unit': self.price_unit})

