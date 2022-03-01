# -*- coding: utf-8 -*-

from odoo import fields, models


class ValidationTemplate(models.Model):
    _name = 'validation.template'
    _description = 'Validation Template'

    def _get_validation_1_user_ids(self):
        group_2_user_ids = self.env.ref('bouygues.bouygues_validation_2_group').users
        group_1_user_ids = self.env.ref('bouygues.bouygues_validation_1_group').users - group_2_user_ids
        return [
            ('id', 'in', group_1_user_ids.ids),
            ('company_ids', 'in', self.env.company.ids),
            ('id', 'in', self.env.ref('hr.group_hr_user').users.ids),
        ]

    def _get_validation_2_user_ids(self):
        group_3_user_ids = self.env.ref('bouygues.bouygues_validation_3_group').users
        group_2_user_ids = self.env.ref('bouygues.bouygues_validation_2_group').users - group_3_user_ids
        return [
            ('id', 'in', group_2_user_ids.ids),
            ('company_ids', 'in', self.env.company.ids),
            ('id', 'in', self.env.ref('hr.group_hr_user').users.ids),
        ]

    def _get_validation_3_user_ids(self):
        group_4_user_ids = self.env.ref('bouygues.bouygues_validation_4_group').users
        group_3_user_ids = self.env.ref('bouygues.bouygues_validation_3_group').users - group_4_user_ids
        return [
            ('id', 'in', group_3_user_ids.ids),
            ('company_ids', 'in', self.env.company.ids),
            ('id', 'in', self.env.ref('hr.group_hr_user').users.ids),
        ]

    def _get_validation_4_user_ids(self):
        group_5_user_ids = self.env.ref('bouygues.bouygues_validation_5_group').users
        group_4_user_ids = self.env.ref('bouygues.bouygues_validation_4_group').users - group_5_user_ids
        return [
            ('id', 'in', group_4_user_ids.ids),
            ('company_ids', 'in', self.env.company.ids),
            ('id', 'in', self.env.ref('hr.group_hr_user').users.ids),
        ]

    def _get_validation_5_user_ids(self):
        group_5_user_ids = self.env.ref('bouygues.bouygues_validation_5_group').users
        return [
            ('id', 'in', group_5_user_ids.ids),
            ('company_ids', 'in', self.env.company.ids),
            ('id', 'in', self.env.ref('hr.group_hr_user').users.ids),
        ]

    name = fields.Char(string='Name')
    validation_limit_1_user_id = fields.Many2one('res.users', string='Validation limit 1 user', domain=_get_validation_1_user_ids, copy=False)
    validation_limit_2_user_id = fields.Many2one('res.users', string='Validation limit 2 user', domain=_get_validation_2_user_ids, copy=False)
    validation_limit_3_user_id = fields.Many2one('res.users', string='Validation limit 3 user', domain=_get_validation_3_user_ids, copy=False)
    validation_limit_4_user_id = fields.Many2one('res.users', string='Validation limit 4 user', domain=_get_validation_4_user_ids, copy=False)
    validation_limit_5_user_id = fields.Many2one('res.users', string='Validation limit 5 user', domain=_get_validation_5_user_ids, copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
