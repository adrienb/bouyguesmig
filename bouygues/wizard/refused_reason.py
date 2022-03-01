# -*- coding: utf-8 -*-

from odoo import fields, models


class RefusedReason(models.TransientModel):
    _name = 'refused.reason'
    _description = 'Refused reason'

    refused_reason = fields.Char(string="Refused reason", required=True)

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        purchase_order_id = self.env['purchase.order'].search([('id', '=', active_id)])
        purchase_order_id.write({'refused_reason': self.refused_reason})
