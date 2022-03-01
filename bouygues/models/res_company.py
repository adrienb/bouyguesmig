# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_validation = fields.Boolean(string='5 steps validation')
    use_notification = fields.Boolean(string='Use notifications')
    approved_mail_template_id = fields.Many2one('mail.template', string='Approved mail template')
    refused_mail_template_id = fields.Many2one('mail.template', string='Refused mail template')
    total_approval_mail_template_id = fields.Many2one('mail.template', string='Total Approval mail template')
    unrefused_mail_template_id = fields.Many2one('mail.template', string='Unrefused mail template')
    validation_limit_1 = fields.Monetary(string='Validation limit 1', currency_field='currency_id')
    validation_limit_2 = fields.Monetary(string='Validation limit 2', currency_field='currency_id')
    validation_limit_3 = fields.Monetary(string='Validation limit 3', currency_field='currency_id')
    validation_limit_4 = fields.Monetary(string='Validation limit 4', currency_field='currency_id')
    validation_limit_5 = fields.Monetary(string='Validation limit 5', currency_field='currency_id')
    company_footer = fields.Text(string='Report footer', default=lambda self: self.env.company.name)

    @api.onchange('use_validation')
    def _onchange_use_validation(self):
        self.approved_mail_template_id = self.env.ref('bouygues.bouygues_mail_template_purchase_approval')
        self.refused_mail_template_id = self.env.ref('bouygues.bouygues_mail_template_purchase_refuse')
        self.total_approval_mail_template_id = self.env.ref('bouygues.bouygues_mail_template_purchase_total_approval')
        self.unrefused_mail_template_id = self.env.ref('bouygues.bouygues_mail_template_purchase_unrefused')
