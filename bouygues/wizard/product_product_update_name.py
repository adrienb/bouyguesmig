from odoo import http, models, fields, api, _
from odoo.exceptions import UserError


class ProductProductUpdateName(models.TransientModel):
    _name = 'product.product.update.name'
    _description = 'Update Name'

    name = fields.Char(string="Name")

    def action_apply(self):
        active_id = self.env.context.get('active_id')
        product_product_id = self.env['product.product'].search([('id', '=', active_id)])
        product_product_id.with_context(lang='en_US').write({'name': self.name})
        product_product_id.with_context(lang='fr_FR').write({'name': self.name})

