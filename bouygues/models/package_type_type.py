# -*- coding: utf-8 -*-

from odoo import fields, models


class PackageTypeType(models.Model):
    _name = 'package.type.type'
    _description = 'Type of Package'

    name = fields.Char(string='Name')
