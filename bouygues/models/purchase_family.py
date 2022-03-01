# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseFamily(models.Model):
    _name = 'purchase.family'
    _description = 'Purchase Family'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    parent_id = fields.Many2one('purchase.family', string='Parent')
