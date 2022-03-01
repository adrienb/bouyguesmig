# -*- coding: utf-8 -*-

from functools import partial
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang
from odoo.tools import float_compare
from werkzeug.urls import url_encode
from datetime import datetime


VALIDATION_USER_COUNT = 5


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_validation_1_user_ids(self):
        group_2_user_ids = self.env.ref('bouygues.bouygues_validation_2_group').users
        group_1_user_ids = self.env.ref('bouygues.bouygues_validation_1_group').users - group_2_user_ids
        return [('id', 'in', group_1_user_ids.ids), ('company_ids', 'in', self.env.company.ids), ('id', 'in', self.env.ref('hr.group_hr_user').users.ids)]

    def _get_validation_2_user_ids(self):
        group_3_user_ids = self.env.ref('bouygues.bouygues_validation_3_group').users
        group_2_user_ids = self.env.ref('bouygues.bouygues_validation_2_group').users - group_3_user_ids
        return [('id', 'in', group_2_user_ids.ids), ('company_ids', 'in', self.env.company.ids), ('id', 'in', self.env.ref('hr.group_hr_user').users.ids)]

    def _get_validation_3_user_ids(self):
        group_4_user_ids = self.env.ref('bouygues.bouygues_validation_4_group').users
        group_3_user_ids = self.env.ref('bouygues.bouygues_validation_3_group').users - group_4_user_ids
        return [('id', 'in', group_3_user_ids.ids), ('company_ids', 'in', self.env.company.ids), ('id', 'in', self.env.ref('hr.group_hr_user').users.ids)]

    def _get_validation_4_user_ids(self):
        group_5_user_ids = self.env.ref('bouygues.bouygues_validation_5_group').users
        group_4_user_ids = self.env.ref('bouygues.bouygues_validation_4_group').users - group_5_user_ids
        return [('id', 'in', group_4_user_ids.ids), ('company_ids', 'in', self.env.company.ids), ('id', 'in', self.env.ref('hr.group_hr_user').users.ids)]

    def _get_validation_5_user_ids(self):
        group_5_user_ids = self.env.ref('bouygues.bouygues_validation_5_group').users
        return [('id', 'in', group_5_user_ids.ids), ('company_ids', 'in', self.env.company.ids), ('id', 'in', self.env.ref('hr.group_hr_user').users.ids)]

    responsible_id = fields.Many2one('res.users', string='Responsible', readonly=True, compute='_compute_responsible_id', store=True)
    picking_contact_id = fields.Many2one('res.partner', string='Picking Contact', readonly=True, compute='_compute_picking_contact_id')
    purchase_picking_contact_id = fields.Many2one('res.partner', string='Purchase Picking Contact')
    contact_phone = fields.Char(string='Contact phone', related='picking_contact_id.phone')
    contact_mobile = fields.Char(string='Contact mobile', related='picking_contact_id.mobile')
    purchase_contact_phone = fields.Char(string='Purchase Contact phone', related='purchase_picking_contact_id.phone')
    purchase_contact_mobile = fields.Char(string='Purchase Contact mobile', related='purchase_picking_contact_id.mobile')
    po_state = fields.Selection(readonly=False, compute='_compute_po_state', selection=[
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
    ], store=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Order Count')
    subcontract_picking_count = fields.Integer(compute='_compute_subcontract_picking_count', string='Subcontracted Picking Count')
    is_subcontract = fields.Boolean(compute='_compute_is_subcontract')
    real_delivery_date = fields.Date(string='Real delivery date', copy=False)
    date_planned = fields.Datetime(copy=False)
    sale_order_ids = fields.Many2many('sale.order')
    dropship_note = fields.Text(string='Dropship Note')
    analytic_imputation_id = fields.Many2one('analytic.imputation', string='Analytic Imputation', domain="[('used_in_po', '=', True), ('company_id', '=', company_id)]")
    analytic_imputation_all_child_ids = fields.Many2many('analytic.imputation', related='analytic_imputation_id.all_child_ids')
    validation_limit_1_user_id = fields.Many2one('res.users', string='Validation limit 1 user', domain=_get_validation_1_user_ids)
    validation_limit_2_user_id = fields.Many2one('res.users', string='Validation limit 2 user', domain=_get_validation_2_user_ids)
    validation_limit_3_user_id = fields.Many2one('res.users', string='Validation limit 3 user', domain=_get_validation_3_user_ids)
    validation_limit_4_user_id = fields.Many2one('res.users', string='Validation limit 4 user', domain=_get_validation_4_user_ids)
    validation_limit_5_user_id = fields.Many2one('res.users', string='Validation limit 5 user', domain=_get_validation_5_user_ids)
    validation_1 = fields.Boolean(default=False, copy=False, readonly=True)
    validation_2 = fields.Boolean(default=False, copy=False, readonly=True)
    validation_3 = fields.Boolean(default=False, copy=False, readonly=True)
    validation_4 = fields.Boolean(default=False, copy=False, readonly=True)
    validation_5 = fields.Boolean(default=False, copy=False, readonly=True)
    validation_1_needed = fields.Boolean(default=False, copy=False, compute='_compute_validation_needed')
    validation_2_needed = fields.Boolean(default=False, copy=False, compute='_compute_validation_needed')
    validation_3_needed = fields.Boolean(default=False, copy=False, compute='_compute_validation_needed')
    validation_4_needed = fields.Boolean(default=False, copy=False, compute='_compute_validation_needed')
    validation_5_needed = fields.Boolean(default=False, copy=False, compute='_compute_validation_needed')
    validation_1_date = fields.Datetime(string='Validation date 1', readonly=True, copy=False)
    validation_2_date = fields.Datetime(string='Validation date 2', readonly=True, copy=False)
    validation_3_date = fields.Datetime(string='Validation date 3', readonly=True, copy=False)
    validation_4_date = fields.Datetime(string='Validation date 4', readonly=True, copy=False)
    validation_5_date = fields.Datetime(string='Validation date 5', readonly=True, copy=False)
    to_be_approved = fields.Boolean(default=False, copy=False)
    refused = fields.Boolean(default=False, copy=False)
    approved = fields.Boolean(default=False, copy=False)
    use_validation = fields.Boolean(related='company_id.use_validation')
    refused_reason = fields.Char(string='Refusal reason')
    refused_id = fields.Many2one('res.users', string='Refused by')
    approve_refuse_buttons_visible = fields.Boolean(compute='_compute_approve_refuse_buttons_visible', copy=False, readonly=True)
    type = fields.Many2one('type.type', string='Type')
    ditrl_text = fields.Text(string='DITLR')
    dichm_text = fields.Text(string='DICHM')
    paqtl_text = fields.Text(string='PAQTL')
    locd_text = fields.Text(string='LOCD')
    warehouse_text_printed = fields.Boolean(string='Print on PDF')
    ditrl_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    dichm_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    paqtl_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    locd_warehouse = fields.Boolean(compute='_compute_warehouse_boolean')
    user_id = fields.Many2one(copy=False)
    is_distrimo_company = fields.Boolean(compute='_compute_is_distrimo_company')
    is_materiel_company = fields.Boolean(compute='_compute_is_materiel_company')
    amount_by_group = fields.Binary(compute='_amount_by_group')
    is_dropship = fields.Boolean(compute='_compute_is_dropship')
    add_received_used = fields.Boolean()
    partner_shipping_id = fields.Many2one('res.partner', string='Subcontracting Delivery Address')
    shipping_name = fields.Char(string='Name', related='partner_shipping_id.name')
    shipping_street = fields.Char(string='Street', related='partner_shipping_id.street')
    shipping_zip = fields.Char(string='ZIP', related='partner_shipping_id.zip')
    shipping_city = fields.Char(string='City', related='partner_shipping_id.city')
    number_of_backorders = fields.Integer(compute='_compute_number_of_backorders', store=True)
    number_of_late_dropships = fields.Integer(compute='_compute_number_of_late_dropships', store=True)
    days_between_delivery_today = fields.Integer(compute='_compute_days_between_delivery_today', store=True)

    @api.depends('picking_ids')
    def _compute_number_of_backorders(self):
        for rec in self:
            rec.number_of_backorders = len(rec.picking_ids.filtered(lambda p: p.backorder_id))

    @api.depends('picking_ids', 'picking_ids.state', 'real_delivery_date', 'is_dropship')
    def _compute_number_of_late_dropships(self):
        now = fields.Datetime.now().date()
        for rec in self:
            rec.number_of_late_dropships = len(rec.picking_ids.filtered(lambda p: rec.is_dropship and p.real_delivery_date and p.real_delivery_date < now and p.state != 'done'))

    @api.depends('real_delivery_date')
    def _compute_days_between_delivery_today(self):
        now = fields.Datetime.now().date()
        for rec in self:
            if rec.real_delivery_date:
                date_days = rec.real_delivery_date - now
                rec.days_between_delivery_today = date_days.days

    def _recompute_late_dropships_days_delivery_today(self):
        po = self.env['purchase.order']
        self.env.add_to_compute(po._fields['number_of_late_dropships'], po.search([]))
        self.env.add_to_compute(po._fields['days_between_delivery_today'], po.search([]))

    @api.depends('subcontract_picking_count')
    def _compute_is_subcontract(self):
        for rec in self:
            rec.is_subcontract = True if rec.subcontract_picking_count > 0 else False

    @api.depends('picking_type_id')
    def _compute_is_dropship(self):
        for rec in self:
            rec.is_dropship = True if 'dropship' in rec.picking_type_id.name.lower() else False

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.taxes_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id)['taxes']
                for tax in line.taxes_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]

    def _compute_is_distrimo_company(self):
        for rec in self:
            rec.is_distrimo_company = True if 'Distrimo' in self.env.company.name else False

    def _compute_is_materiel_company(self):
        for rec in self:
            rec.is_materiel_company = True if 'Distrimo' not in self.env.company.name and 'MATERIEL' in self.env.company.name else False

    @api.depends('picking_type_id', 'picking_type_id.warehouse_id')
    def _compute_warehouse_boolean(self):
        for rec in self:
            rec.ditrl_warehouse = True if rec.picking_type_id.warehouse_id.code == 'DITLR' else False
            rec.dichm_warehouse = True if rec.picking_type_id.warehouse_id.code == 'DICHM' else False
            rec.paqtl_warehouse = True if rec.picking_type_id.warehouse_id.code == 'PAQTL' else False
            rec.locd_warehouse = True if rec.picking_type_id.warehouse_id.code == 'LOCD+' else False

    @api.depends('validation_1', 'validation_2', 'validation_3', 'validation_4', 'validation_5', 'validation_limit_1_user_id', 'validation_limit_2_user_id', 'validation_limit_3_user_id', 'validation_limit_4_user_id', 'validation_limit_5_user_id')
    def _compute_approve_refuse_buttons_visible(self):
        for rec in self:
            visible_user_ids = []
            for i in range(1, VALIDATION_USER_COUNT + 1):
                if not getattr(rec, 'validation_%s' % i):
                    [visible_user_ids.append(user.id) for user in rec._get_user_or_delegate(getattr(rec, 'validation_limit_%i_user_id' % i))]
            if self.env.user.id in visible_user_ids:
                rec.approve_refuse_buttons_visible = True
            else:
                rec.approve_refuse_buttons_visible = False

    @api.onchange('analytic_imputation_id')
    def _onchange_analytic_imputation_id(self):
        for rec in self:
            for validation_template in rec.analytic_imputation_id.validation_template_ids:
                if validation_template.warehouse_id == rec.picking_type_id.warehouse_id:
                    for i in range(1, VALIDATION_USER_COUNT + 1):
                        if getattr(validation_template, 'validation_limit_%s_user_id' % i) and getattr(rec, 'validation_%s_needed' % i):
                            setattr(rec, 'validation_limit_%s_user_id' % i, getattr(validation_template, 'validation_limit_%s_user_id' % i))
                        else:
                            setattr(rec, 'validation_limit_%s_user_id' % i, False)
            for line in rec.order_line:
                if not line.analytic_imputation_id and rec.analytic_imputation_id:
                    line.analytic_imputation_id = rec.analytic_imputation_id

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id_bouygues(self):
        for rec in self:
            for validation_template in rec.analytic_imputation_id.validation_template_ids:
                if validation_template.warehouse_id == rec.picking_type_id.warehouse_id:
                    for i in range(1, VALIDATION_USER_COUNT + 1):
                        if getattr(validation_template, 'validation_limit_%s_user_id' % i) and getattr(
                                rec, 'validation_%s_needed' % i):
                            setattr(rec, 'validation_limit_%s_user_id' % i,
                                    getattr(validation_template, 'validation_limit_%s_user_id' % i))
                        else:
                            setattr(rec, 'validation_limit_%s_user_id' % i, False)

    @api.onchange('amount_untaxed')
    def _onchange_amount_untaxed(self):
        for rec in self:
            for validation_template in rec.analytic_imputation_id.validation_template_ids:
                if validation_template.warehouse_id == rec.picking_type_id.warehouse_id:
                    for i in range(1, VALIDATION_USER_COUNT + 1):
                        if getattr(validation_template, 'validation_limit_%s_user_id' % i) and getattr(rec, 'validation_%s_needed' % i) and not getattr(rec, 'validation_limit_%s_user_id' % i):
                            setattr(rec, 'validation_limit_%s_user_id' % i, getattr(validation_template, 'validation_limit_%s_user_id' % i))
                        elif getattr(validation_template, 'validation_limit_%s_user_id' % i) and getattr(rec, 'validation_%s_needed' % i) and getattr(rec, 'validation_limit_%s_user_id' % i):
                            setattr(rec, 'validation_limit_%s_user_id' % i, getattr(rec, 'validation_limit_%s_user_id' % i))
                        else:
                            setattr(rec, 'validation_limit_%s_user_id' % i, False)

    @api.depends('amount_untaxed', 'to_be_approved')
    def _compute_validation_needed(self):
        if not self.approved and not self.to_be_approved:
            if not self.env.user.has_group('bouygues.bouygues_validation_1_group'):
                self.validation_1_needed = True
            else:
                self.validation_1_needed = False

            for i in range(2, VALIDATION_USER_COUNT + 1):
                if self.amount_untaxed > getattr(self.company_id, 'validation_limit_%s' % (i - 1)) and not self.env.user.has_group('bouygues.bouygues_validation_%s_group' % i):
                    setattr(self, 'validation_%s_needed' % i, True)
                else:
                    setattr(self, 'validation_%s_needed' % i, False)
        else:
            for i in range(1, VALIDATION_USER_COUNT + 1):
                if getattr(self, 'validation_limit_%s_user_id' % i):
                    setattr(self, 'validation_%s_needed' % i, True)
                else:
                    setattr(self, 'validation_%s_needed' % i, False)

    def action_view_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', 'in', self.sale_order_ids.ids)]
        return action

    def action_view_subcontract_pickings(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        subcontracting_move_ids = self.env['stock.move'].search([('subcontracting_picking_id', '=', self.id), ('is_subcontract', '=', False)])
        subcontracting_picking_ids = self.env['stock.picking'].search(
            [
                '&',
                    ('id', 'in', subcontracting_move_ids.mapped('picking_id').ids), '|', ('is_out', '=', True),
                    ('is_pick', '=', True),
            ]
        )
        action['domain'] = [('id', 'in', subcontracting_picking_ids.ids)]
        return action

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    @api.depends('order_line')
    def _compute_subcontract_picking_count(self):
        for rec in self:
            subcontracting_move_ids = self.env['stock.move'].search([('subcontracting_picking_id', '=', rec.id), ('is_subcontract', '=', False)])
            subcontracting_picking_ids = self.env['stock.picking'].search(
                [
                    '&',
                        ('id', 'in', subcontracting_move_ids.mapped('picking_id').ids), '|', ('is_out', '=', True),
                        ('is_pick', '=', True),
                ]
            )
            rec.subcontract_picking_count = len(subcontracting_picking_ids)

    @api.depends('order_line')
    def _compute_picking_contact_id(self):
        for rec in self:
            if rec.order_line:
                for line in rec.order_line:
                    if line.sale_order_id and line.sale_order_id.picking_contact_id:
                        rec.picking_contact_id = line.sale_order_id.picking_contact_id
                        break
                    else:
                        rec.picking_contact_id = False
            else:
                rec.picking_contact_id = False

    @api.depends('picking_type_id', 'picking_type_id.warehouse_id', 'partner_id', 'partner_id.product_location_responsible_ids', 'partner_id.dropship_responsible_id')
    def _compute_responsible_id(self):
        for rec in self:
            rec.responsible_id = False
            if rec.partner_id and rec.is_dropship:
                rec.responsible_id = rec.partner_id.dropship_responsible_id
            if rec.picking_type_id.warehouse_id and rec.partner_id:
                user_id = self.env['product.location.responsible'].search([('partner_id', '=', rec.partner_id.id), ('warehouse_id', '=', rec.picking_type_id.warehouse_id.id)], limit=1).responsible_id
                rec.responsible_id = user_id if user_id else False

    @api.depends('state', 'picking_ids', 'order_line', 'picking_ids.state', 'refused', 'to_be_approved', 'add_received_used')
    def _compute_po_state(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.po_state = rec.state
            elif rec.refused:
                rec.po_state = 'refused'
            elif rec.to_be_approved:
                rec.po_state = 'to_be_approved'
            elif rec.state == 'draft' or rec.state == 'sent' or rec.state == 'to approve':
                rec.po_state = rec.state
            else:
                done_pickings = rec.picking_ids.filtered(lambda p: p.state == 'done')
                cancel_pickings = rec.picking_ids.filtered(lambda p: p.state == 'cancel')
                received_lines = rec.order_line.filtered(lambda l: float_compare(l.product_qty, l.qty_received, precision_digits=3) == 0)
                partial_sale = len(rec.order_line.filtered(lambda l: l.qty_received > 0)) > 0
                # Toutes les quantitées livrées = commandées + tout en done (Pas ça pour partial sale)
                if len(done_pickings) == len(rec.picking_ids) and len(received_lines) == len(rec.order_line) and len(rec.order_line) > 0:
                    rec.po_state = 'total_sale'
                # Tout en done ou cancel mais pas toutes les quantitées livrées = commandées
                elif (len(done_pickings) + len(cancel_pickings)) == len(rec.picking_ids) and len(received_lines) != len(rec.order_line) and len(rec.order_line) > 0 and partial_sale:
                    rec.po_state = 'partial_sale'
                # Au moins 1 picking done mais pas tous
                elif len(done_pickings) > 0 and len(done_pickings) != len(rec.picking_ids):
                    rec.po_state = 'partial_ship'
                elif rec.state == 'done':
                    rec.po_state = rec.state
                else:
                    rec.po_state = 'purchase'

    def approve_refuse_notification(self, approved, to_approve, unrefused):
        manager_ids = []

        # TODO : Problème de notif avec délégué

        # We only want to send notifications to the delegate if there is one
        for i in range(1, VALIDATION_USER_COUNT + 1):
            users = self._get_user_or_delegate(getattr(self, 'validation_limit_%s_user_id' % i))
            if len(users) > 0:
                manager_ids.append(users[len(users) - 1].id)

        # Add PO creator and remove duplicate and current user from the list
        manager_ids.append(self.create_uid.id)
        manager_ids = list(set(manager_ids))
        if self.env.user.id in manager_ids: manager_ids.remove(self.env.user.id)

        if approved and not self.approved:
            manager_ids = [self.create_uid.id]

        activity_data = {
            'res_id': self.id,
            'res_model_id': self.env['ir.model']._get(self._name).id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
        }

        template_id = self.env['mail.template']

        templates = {
           self.env.ref('bouygues.bouygues_mail_template_purchase_approval'): approved,
           self.env.ref('bouygues.bouygues_mail_template_purchase_total_approval'): approved and self.approved,
           self.env.ref('bouygues.bouygues_mail_template_purchase_refuse'): not approved and not to_approve and not unrefused,
           self.env.ref('bouygues.bouygues_mail_template_purchase_unrefused'): unrefused,
        }

        action = self.env.ref('purchase.purchase_rfq')
        action_url = '%s/web#%s' % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            url_encode({
                'action': action.id,
                'active_model': 'purchase.order',
                'view_type': 'form',
                'id': self.id,
                'menu_id': self.env.ref('purchase.menu_purchase_root').id})
        )
        button = "<p><a style='background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;' href=%s>View PO</a></p>" % (
            action_url)

        for key, value in templates.items():
            if value:
                template_id = key

        if template_id:
            values = template_id.generate_email(self.id, fields=None)
            values['email_from'] = self.company_id.email
            if approved:
                values['body_html'] = '<p>The purchase order <b>' + self.name + '</b> has been approved by ' + str(self.env.user.name) + '.<br/></p>' + button
            if approved and self.approved:
                values['body_html'] = '<p>The purchase order <b>' + self.name + '</b> has been approved by all managers.<br/></p>' + button
            if not approved and not to_approve and not unrefused:
                values['body_html'] = '<p>The purchase order <b>' + self.name + '</b> has been refused by ' + str(self.env.user.name) + '.<br/></p>' + button
            if unrefused:
                values['body_html'] = '<p>The purchase order <b>' + self.name + '</b> has been unrefused by ' + str(self.env.user.name) + ' and is ready to be approved.<br/></p>' + button
            values['body'] = tools.html_sanitize(values['body_html'])

        for user in manager_ids:
            if template_id:
                values['email_to'] = self.env['res.users'].browse(user).login
                mail = self.env['mail.mail'].create(values)
                mail.send()
            if to_approve and not unrefused:
                activity_data['user_id'] = self.env['res.users'].browse(user).id
                self.env['mail.activity'].create(activity_data)

    def check_if_approved(self):
        approval = []

        if not self.validation_1:
            approval.append(True)

        for i in range(2, VALIDATION_USER_COUNT + 1):
            if self.amount_untaxed > getattr(self.company_id, 'validation_limit_%s' % (i - 1)) and not getattr(self, 'validation_%s' % i):
                approval.append(True)

        if not any(approval):
            self.approved = True
            self.to_be_approved = False

    def _get_user_or_delegate(self, validation_user):
        users = []
        if validation_user:
            users.append(validation_user)
            if validation_user.employee_id:
                for delegation in validation_user.employee_id.validation_delegation_ids:
                    if delegation.start_date < fields.datetime.now().date() < delegation.end_date:
                        users.append(delegation.user_id)
                        return users
            return users
        return users

    def action_approve_po(self):
        approval_error_message = True

        for i in range(1, VALIDATION_USER_COUNT + 1):
            if not getattr(self, 'validation_%s' % i) and self.env.user in self._get_user_or_delegate(getattr(self, 'validation_limit_%s_user_id' % i)):
                setattr(self, 'validation_%s' % i, True)
                setattr(self, 'validation_%s_date' % i, fields.Datetime.now())
                approval_error_message = False

        if approval_error_message:
            raise UserError(_('You cannot approve or you have already approved'))

        self.check_if_approved()
        self.approve_refuse_notification(True, False, False)

    def _set_approval_levels(self):
        for i in reversed(range(2, VALIDATION_USER_COUNT + 1)):
            if self.amount_untaxed > getattr(self.company_id, 'validation_limit_%s' % (i - 1)) and self.env.user.has_group('bouygues.bouygues_validation_%s_group' % i):
                self.write({'validation_%s' % y: True for y in range(2, i + 1)})
                self.write({'validation_%s_date' % y: fields.Datetime.now() for y in range(2, i + 1)})

        if self.env.user.has_group('bouygues.bouygues_validation_1_group'):
            self.validation_1 = True
            self.validation_1_date = fields.Datetime.now()

    def check_required(self):
        if not self.validation_1 and not self.validation_limit_1_user_id:
            raise UserError(_('Please select all required validators'))

        for i in range(2, VALIDATION_USER_COUNT + 1):
            if self.amount_untaxed > getattr(self.company_id, 'validation_limit_%s' % (i - 1)) and not getattr(self, 'validation_%s' % i) and not getattr(self, 'validation_limit_%s_user_id' % i):
                raise UserError(_('Please select all required validators'))

    def button_confirm(self):
        for rec in self:
            if rec.use_validation:
                rec._set_approval_levels()
                rec.check_if_approved()
                if not rec.to_be_approved and not rec.approved:
                    rec.check_required()
                    rec.to_be_approved = True
                    rec.approve_refuse_notification(False, True, False)
                elif rec.approved:
                    return super(PurchaseOrder, self.with_context(purchase_order_id=self.id, subcontracting_partner_shipping_id=self.partner_shipping_id.id, dropship_note_po=self.dropship_note)).button_confirm()
            else:
                return super(PurchaseOrder, self.with_context(purchase_order_id=self.id, subcontracting_partner_shipping_id=self.partner_shipping_id.id, dropship_note_po=self.dropship_note)).button_confirm()

    @api.model
    def create(self, vals):
        if self.env.context.get('origin_sale_order_id'):
            sale_order = self.env['sale.order'].browse(self.env.context.get('origin_sale_order_id'))
            vals['sale_order_ids'] = [(4, sale_order.id, None)]
        if self.env.context.get('dropship_note'):
            vals['dropship_note'] = self.env.context.get('dropship_note')
        eco_product_ids = []
        if vals.get('order_line'):
            for order_line in vals.get('order_line'):
                if not order_line[2].get('eco_product_created'):
                    product_id = self.env['product.product'].browse(int(order_line[2].get('product_id')))
                    if product_id and product_id.eco_product_id:
                        order_line[2]['eco_product_created'] = True
                        eco_product_ids.append({
                            'name': product_id.eco_product_id.display_name,
                            'product_id': product_id.eco_product_id.id,
                            'product_qty': 1,
                            'price_unit': product_id.eco_product_id.lst_price,
                            'product_uom': product_id.eco_product_id.uom_id.id,
                            'date_planned': datetime.now(),
                        })

        res = super(PurchaseOrder, self).create(vals)
        if len(eco_product_ids) > 0:
            for product in eco_product_ids:
                product['order_id'] = res.id
                self.env['purchase.order.line'].create(product)
        location_product = False
        for line in res.order_line:
            if line.product_template_id.purchase_family_id and 'lmc' in line.product_template_id.purchase_family_id.name.lower():
                location_product = True
        sequence_id = self.env['ir.sequence'].search([
            ('purchase_sequence', '=', True),
            ('location_sequence', '=', location_product),
            ('company_id', '=', res.company_id.id),
        ])
        if sequence_id:
            res.name = sequence_id.next_by_id()
        return res

    def write(self, vals):
        eco_product_ids = []
        if vals.get('order_line'):
            for order_line in vals.get('order_line'):
                if order_line[0] == 0:
                    if not order_line[2].get('eco_product_created'):
                        product_id = self.env['product.product'].browse(int(order_line[2].get('product_id')))
                        if product_id and product_id.eco_product_id:
                            order_line[2]['eco_product_created'] = True
                            eco_product_ids.append({
                                'name': product_id.eco_product_id.display_name,
                                'product_id': product_id.eco_product_id.id,
                                'product_qty': 1,
                                'price_unit': product_id.eco_product_id.lst_price,
                                'product_uom': product_id.eco_product_id.uom_id.id,
                                'date_planned': datetime.now(),
                            })
        if self.env.context.get('origin_sale_order_id'):
            sale_order = self.env['sale.order'].browse(self.env.context.get('origin_sale_order_id'))
            vals['sale_order_ids'] = [(4, sale_order.id, None)]
        res = super(PurchaseOrder, self).write(vals)
        if len(eco_product_ids) > 0:
            for product in eco_product_ids:
                product['order_id'] = self.id
                self.env['purchase.order.line'].create(product)
        return res

    def action_refuse_po(self):
        authorized_user_ids = []

        for i in range(1, VALIDATION_USER_COUNT + 1):
            [authorized_user_ids.append(user.id) for user in self._get_user_or_delegate(getattr(self, 'validation_limit_%i_user_id' % i))]

        if self.env.user not in self.env['res.users'].browse(authorized_user_ids):
            raise UserError(_('You cannot refuse'))
        else:
            self.refused = True
            self.to_be_approved = False
            self.approve_refuse_notification(False, False, False)
            self.refused_id = self.env.user.id
            action = ({
                'type': 'ir.actions.act_window',
                'name': _('Refused Reason'),
                'res_model': 'refused.reason',
                'view_id': self.env.ref("bouygues.bouygues_refused_reason_view_form").id,
                'target': 'new',
                'view_mode': 'form',
            })
            return action

    def action_unrefuse_po(self):
        if self.env.user.has_group('bouygues.bouygues_purchase_superadmin_group') or self.env.user == self.refused_id:
            self.refused = False
            self.to_be_approved = True
            self.approve_refuse_notification(False, False, True)
            self.validation_1 = False
            self.validation_2 = False
            self.validation_3 = False
            self.validation_4 = False
            self.validation_5 = False
            self.validation_1_date = False
            self.validation_2_date = False
            self.validation_3_date = False
            self.validation_4_date = False
            self.validation_5_date = False
            self.to_be_approved = False
            self.refused_reason = False
            self.refused_id = False
        else:
            raise UserError(_('Only admins and the person who refused can unrefuse'))

    def action_print_purchase_order_report(self):
        return self.env.ref('bouygues.action_purchase_order_report_bouygues').report_action(self)
