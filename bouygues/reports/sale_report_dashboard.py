# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReportDashboard(models.Model):
    _name = "sale.report.dashboard"
    _description = "Sales Analysis Report Dashboard"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char('Order Reference', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    nbr = fields.Integer('# of Orders', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
    industry_id = fields.Many2one('res.partner.industry', 'Customer Industry', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Customer Entity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    so_state = fields.Selection(string='SO State', readonly=True, selection=[
        ('draft', "Quotation"),
        ('sent', "Quotation Sent"),
        ('progress', "In Progress"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
        ('total_sale', "Sale"),
        ('partial_sale', "Partial Sale"),
        ('partial_ship', "Partially Shipped"),
    ])
    campaign_id = fields.Many2one('utm.campaign', 'Campaign')
    medium_id = fields.Many2one('utm.medium', 'Medium')
    source_id = fields.Many2one('utm.source', 'Source')
    create_date = fields.Datetime('Creation Date', readonly=True)

    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)

    ref = fields.Char('Client Reference', readonly=True)
    client_order_ref = fields.Char('Client Order Reference', readonly=True)
    orders_id = fields.Many2one('sale.order', 'Order #s', readonly=True)
    # number_of_out_pickings = fields.Integer(string='Delivery #')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)
    product_uom_qty = fields.Float('Qty Ordered', readonly=True)
    qty_delivered = fields.Float('Qty Delivered', readonly=True)
    qty_to_invoice = fields.Float('Qty To Invoice', readonly=True)
    qty_invoiced = fields.Float('Qty Invoiced', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    untaxed_amount_to_invoice = fields.Float('Untaxed Amount To Invoice', readonly=True)
    untaxed_amount_invoiced = fields.Float('Untaxed Amount Invoiced', readonly=True)
    type = fields.Many2one('type.type', string='Type', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(s.id) as id,
            count(*) as nbr,
            s.name as name,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
            sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
            sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
            sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_total,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_to_invoice,
            sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_invoiced,
            s.date_order as date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            s.campaign_id as campaign_id,
            s.medium_id as medium_id,
            s.so_state as so_state,
            s.type as type,
            s.create_date as create_date,
            s.source_id as source_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            s.pricelist_id as pricelist_id,
            s.analytic_account_id as analytic_account_id,
            s.team_id as team_id,
            partner.country_id as country_id,
            partner.industry_id as industry_id,
            partner.commercial_partner_id as commercial_partner_id,
            s.id as order_id,
            partner.ref as ref,
            s.client_order_ref as client_order_ref,
            s.id as orders_id,
            s.warehouse_id as warehouse_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
                sale_order s
                      join res_partner partner on s.partner_id = partner.id
                      join sale_order_line l on (s.id=l.order_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                        left join uom_uom u on (u.id=l.product_uom)
                        left join uom_uom u2 on (u2.id=t.uom_id)
                        left join product_pricelist pp on (s.pricelist_id = pp.id)
                %s
        """ % from_clause

        groupby_ = """
            s.id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.so_state,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.type,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            partner.ref,
            s.client_order_ref,
            s.warehouse_id,
            s.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

class SaleOrderReportProforma(models.AbstractModel):
    _name = 'report.sale.report_saleproforma'
    _description = 'Proforma Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True
        }
