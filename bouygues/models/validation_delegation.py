# -*- coding: utf-8 -*-

from odoo import fields, models


class ValidationDelegation(models.Model):
    _name = 'validation.delegation'
    _description = 'Validation Delegation'

    user_id = fields.Many2one('res.users', string='User', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    employee_id = fields.Many2one('hr.employee.public', string='Employee')
