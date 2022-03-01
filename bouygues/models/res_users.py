# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    view_company_switch_button = fields.Boolean('Can view Company switch button', default=False)
    show_taxes = fields.Boolean(compute='_compute_show_taxes')

    @api.depends('groups_id')
    def _compute_show_taxes(self):
        for user in self:
            user.show_taxes = bool(self.env['account.tax'].check_access_rights('read', raise_exception=False))
