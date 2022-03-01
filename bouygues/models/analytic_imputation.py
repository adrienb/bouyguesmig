# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AnalyticImputation(models.Model):
    _name = 'analytic.imputation'
    _description = 'Analytic Imputation'
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    company_id = fields.Many2one('res.company', string='Company')
    parent_id = fields.Many2one('analytic.imputation', string='Parent', domain="[('id', '!=', id)]")
    child_ids = fields.One2many('analytic.imputation', 'parent_id')
    all_child_ids = fields.Many2many('analytic.imputation', 'analytic_imputation_childs_rel', 'anim', 'childanim', compute='_compute_all_child_ids', store=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)
    used_in_po = fields.Boolean(string='Used in PO')
    validation_template_ids = fields.Many2many('validation.template')
    updated = fields.Boolean(default=False)

    @api.depends('parent_id', 'child_ids', 'child_ids.child_ids')
    def _compute_all_child_ids(self):
        for rec in self:
            parent = rec
            while parent:
                children = parent.child_ids
                current_children = children
                while current_children:
                    current_children = current_children.child_ids
                    children |= current_children
                parent.all_child_ids = children
                parent = parent.parent_id

    @api.depends('name', 'code')
    def _compute_complete_name(self):
        for rec in self:
            if rec.code:
                rec.complete_name = '[%s] %s' % (rec.code, rec.name)
            else:
                rec.complete_name = rec.name
