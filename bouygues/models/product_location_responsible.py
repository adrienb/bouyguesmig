# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductLocationResponsible(models.Model):
    _name = 'product.location.responsible'
    _description = 'Product responsible for the location'

    partner_id = fields.Many2one('res.partner')
    responsible_id = fields.Many2one('res.users', string='Responsible', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
