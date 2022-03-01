# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    validation_delegation_ids = fields.One2many('validation.delegation', 'employee_id', string='Delegates')
