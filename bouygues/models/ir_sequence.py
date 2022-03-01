# -*- coding: utf-8 -*-

from odoo import fields, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    location_sequence = fields.Boolean(string='Location Sequence')
    purchase_sequence = fields.Boolean(string='Purchase Sequence')
