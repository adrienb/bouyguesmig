# -*- coding: utf-8 -*-

from odoo import fields, models


class ResZip(models.Model):
    _name = 'res.zip'
    _description = 'ZIP'

    name = fields.Char(string='ZIP')
    warehouse_id = fields.Many2one('stock.warehouse')
