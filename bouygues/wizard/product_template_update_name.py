from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplateUpdateName(models.TransientModel):
    _name = 'product.template.update.name'
    _description = 'Update Name'

    name = fields.Char(string="Name")

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        product_template_id = self.env['product.template'].search([('id', '=', active_id)])
        product_template_id.with_context(lang='en_US').write({'name': self.name})
        product_template_id.with_context(lang='fr_FR').write({'name': self.name})

