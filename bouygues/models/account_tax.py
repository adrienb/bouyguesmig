# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    eco_tax = fields.Boolean(string='Eco Taxe')
    storage_cost = fields.Boolean(string='Frais de Stockage')
