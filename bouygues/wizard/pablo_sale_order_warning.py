# -*- coding: utf-8 -*-

from odoo import fields, models


class PabloSaleOrderWarning(models.TransientModel):
    _name = 'pablo.sale.order.warning'
    _description = 'Warning for products in pablo sale orders'

    def _get_warning_msg(self):
        return self.env.context.get('warning_msg')

    warning_msg = fields.Text(string="Warning message", readonly=True, default=_get_warning_msg)
