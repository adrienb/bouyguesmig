# -*- coding: utf-8 -*-

from odoo import http, models, fields, api


class StockWarning(models.Model):
    _name = 'stock.warning'
    _description = 'Stock Warning'

    name = fields.Char(string='Name')
    filename = fields.Char(string="Filename")
    file = fields.Binary(string='File')
