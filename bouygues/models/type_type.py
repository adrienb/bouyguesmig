# -*- coding: utf-8 -*-

from odoo import fields, models


class TypeType(models.Model):
    _name = 'type.type'
    _description = 'Type'

    name = fields.Char(string='Name')
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the type.type without removing it.")
