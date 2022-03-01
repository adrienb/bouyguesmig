# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    create_date = fields.Datetime('Creation Date', readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", po.create_date as create_date"
