from odoo import models, api, fields
from lxml import etree


class BaseModelExtend(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(BaseModelExtend, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            if not self.env.user.has_group('bouygues.bouygues_can_import'):
                for node in doc.xpath("//tree"):
                    node.set('import', 'false')
            result['arch'] = etree.tostring(doc)
        if view_type == 'kanban':
            doc = etree.XML(result['arch'])
            if not self.env.user.has_group('bouygues.bouygues_can_import'):
                for node in doc.xpath("//kanban"):
                    node.set('import', 'false')
            result['arch'] = etree.tostring(doc)
        return result
