# -*- coding: utf-8 -*-

from odoo import fields, models


class PrAnalysisExtraction(models.TransientModel):
    _name = 'pr.analysis.extraction'
    _description = 'PR Analysis'

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")

    def action_apply(self):
        self.env['product.product'].extract_pr_analysis(self.start_date, self.end_date)
