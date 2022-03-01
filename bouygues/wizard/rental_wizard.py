# -*- coding: utf-8 -*-

from odoo import fields, models, api


class RentalWizard(models.TransientModel):
    _inherit = 'rental.wizard'

    rental_unit = fields.Selection(string='Unit', related='pricing_id.unit')
    rental_price = fields.Monetary(string='Unit Price', related='pricing_id.price')
    rental_duration = fields.Integer(string='Duration', related='duration')

