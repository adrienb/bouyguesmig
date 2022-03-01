# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class PurchaseReportDashboard(models.Model):
    _name = "purchase.report.dashboard"
    _description = "Purchase Report Dashboard"
    _auto = False
    _order = 'date_order desc, price_total desc'

    date_order = fields.Datetime('Order Date', readonly=True, help="Date on which this document has been created")
    state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'Order Status', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    date_approve = fields.Datetime('Confirmation Date', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    user_id = fields.Many2one('res.users', 'Purchase Representative', readonly=True)
    delay = fields.Float('Days to Confirm', digits=(16, 2), readonly=True)
    price_total = fields.Float('Total', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    po_name = fields.Char('Purchase Order Reference', readonly=True)
    country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Commercial Entity', readonly=True)
    order_id = fields.Many2one('purchase.order', 'Order', readonly=True)
    orders_done_id = fields.Many2one('purchase.order', '# of Orders', readonly=True)
    orders_all_id = fields.Many2one('purchase.order', '# Orders', readonly=True)
    untaxed_total = fields.Float('Untaxed Total', readonly=True)
    po_state = fields.Selection([
        ('draft', "RFQ"),
        ('sent', "RFQ Sent"),
        ('to approve', "To Approve"),
        ('to_be_approved', "To Be Approved"),
        ('refused', "Refused"),
        ('purchase', "In Progress"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
        ('total_sale', "Sale"),
        ('partial_sale', "Partial Sale"),
        ('partial_ship', "Partially Shipped"),
    ], 'Purchase Order State', readonly=True)
    number_of_late_dropships = fields.Integer('# of Late Dropships', readonly=True)
    number_of_backorders = fields.Integer('# of Backorders', readonly=True)
    real_delivery_date = fields.Date(readonly=True)
    average_delivery_time = fields.Float(readonly=True, group_operator="avg")
    days_between_delivery_today = fields.Integer('Days between Delivery and today', readonly=True)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
                SELECT
                    min(po.id) as id,
                    count(*) as nbr,
                    po.id as order_id,
                    po.id as orders_done_id,
                    po.id as orders_all_id,
                    po.name as po_name,
                    po.date_order as date_order,
                    po.state,
                    po.po_state as po_state,
                    po.date_approve,
                    po.dest_address_id,
                    po.partner_id as partner_id,
                    po.user_id as user_id,
                    po.company_id as company_id,
                    po.fiscal_position_id as fiscal_position_id,
                    po.currency_id,
                    po.real_delivery_date,
                    po.number_of_backorders as number_of_backorders,
                    po.number_of_late_dropships number_of_late_dropships,
                    po.days_between_delivery_today days_between_delivery_today,
                    extract(epoch from age(po.real_delivery_date,po.date_approve))/(24*60*60)::decimal(16,2) as average_delivery_time,
                    extract(epoch from age(po.date_approve,po.date_order))/(24*60*60)::decimal(16,2) as delay,
                    sum(l.price_total / COALESCE(po.currency_rate, 1.0))::decimal(16,2) as price_total,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(l.price_subtotal / COALESCE(po.currency_rate, 1.0))::decimal(16,2) as untaxed_total
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
            purchase_order po
                join res_partner partner on po.partner_id = partner.id
                join purchase_order_line l on (po.id=l.order_id)
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom line_uom on (line_uom.id=l.product_uom)
                    left join uom_uom product_uom on (product_uom.id=t.uom_id)
                    left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                left join currency_rate cr on (cr.currency_id = po.currency_id and
                    cr.company_id = po.company_id and
                    cr.date_start <= coalesce(po.date_order, now()) and
                    (cr.date_end is null or cr.date_end > coalesce(po.date_order, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                po.id,
                po.company_id,
                po.user_id,
                po.partner_id,
                po.currency_id,
                po.date_approve,
                po.dest_address_id,
                po.fiscal_position_id,
                po.date_order,
                po.state,
                po.po_state,
                po.real_delivery_date,
                po.days_between_delivery_today,
                partner.country_id,
                partner.commercial_partner_id
        """
        return group_by_str
