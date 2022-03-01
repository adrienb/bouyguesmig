# -*- coding: utf-8 -*-

from odoo import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            result['view_company_switch_button'] = self.env.user.view_company_switch_button
        return result
