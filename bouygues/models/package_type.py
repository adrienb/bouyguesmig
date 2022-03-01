# -*- coding: utf-8 -*-

from odoo import fields, models


class PackageType(models.Model):
    _name = 'package.type'
    _description = 'Type of Package'

    picking_id = fields.Many2one('stock.picking')
    package_type_id = fields.Many2one('package.type.type', string='Package Type')
    number = fields.Integer(string='Number')
    weight = fields.Float(string='Weight (kg)')
    location = fields.Char(string='Location')
