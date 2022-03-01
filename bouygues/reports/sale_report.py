# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    ref = fields.Char('Client Reference', readonly=True)
    client_order_ref = fields.Char('Client Order Reference', readonly=True)
    orders_id = fields.Many2one('sale.order', 'Order #s', readonly=True)
    # number_of_out_pickings = fields.Integer(string='OUT Pickings')

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['ref'] = ', partner.ref as ref'
        fields['client_order_ref'] = ', s.client_order_ref as client_order_ref'
        fields['orders_id'] = ', s.id as orders_id'
        # fields['number_of_out_pickings'] = ', s.number_of_out_pickings as number_of_out_pickings'

        groupby += ', partner.ref'
        groupby += ', s.client_order_ref'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
