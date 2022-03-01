# -*- coding: utf-8 -*-

from odoo import http, api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools import float_compare
import base64

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_user_warehouse_id(self):
        if self.env.context.get('default_is_rental_order'):
            distriplus_warehouse = self.env['stock.warehouse'].search([('name', 'ilike', 'distriplus')], limit=1)
            if distriplus_warehouse:
                return distriplus_warehouse
        elif self.partner_shipping_id and self.partner_shipping_id.country_id.code == 'FR':
            zip_id = self.env['res.zip'].search([('name', '=', self.partner_shipping_id.zip)], limit=1)
            return zip_id.warehouse_id
        else:
            return self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')

    @api.model
    def _default_pricelist_id(self):
        pricelist = False
        if self.env.context.get('default_is_rental_order'):
            pricelist = self.env.ref("__export__.product_pricelist_6_f5d88853").id
        return pricelist

    so_state = fields.Selection(readonly=False, compute='_compute_so_state', selection=[
        ('draft', "Quotation"),
        ('sent', "Quotation Sent"),
        ('progress', "In Progress"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
        ('total_sale', "Sale"),
        ('partial_sale', "Partial Sale"),
        ('partial_ship', "Partially Shipped"),
    ], store=True)
    picking_contact_id = fields.Many2one('res.partner', string='Picking Contact')
    pablo_order_creator_id = fields.Many2one('res.partner', string='Pablo Order Creator')
    contact_phone = fields.Char(string='Contact phone', related='picking_contact_id.phone')
    contact_mobile = fields.Char(string='Contact mobile', related='picking_contact_id.mobile')
    shipping_name = fields.Char(string='Name', related='partner_shipping_id.name')
    shipping_street = fields.Char(string='Street', related='partner_shipping_id.street')
    shipping_zip = fields.Char(string='ZIP', related='partner_shipping_id.zip')
    shipping_city = fields.Char(string='City', related='partner_shipping_id.city')
    partner_parent_child_ids = fields.Many2many('res.partner', compute='_compute_partner_child_parent_ids')
    partner_ref = fields.Char(related='partner_id.ref')
    so_note = fields.Text(string='Note')
    pablo_note = fields.Text(string='Supplier Instructions')
    purchase_order_ids = fields.Many2many('purchase.order', compute='_compute_purchase_order_ids')
    purchase_orders_count = fields.Integer(compute='_compute_purchase_orders_count', string='Purchase Order Count')
    warehouse_id = fields.Many2one(default=_default_user_warehouse_id, readonly=False)
    type = fields.Many2one('type.type', string='Type', copy=False)
    my_sales_team = fields.Boolean(compute='_dummy_compute', search='_search_my_sales_team')
    pablo_import_user_id = fields.Many2one('res.users', string='Imported from Pablo by', readonly=True)
    analytic_imputation = fields.Char(string='Analytic Imputation')
    assigned_user_id = fields.Many2one('res.users', string='Assigned to', tracking=True)
    user_id = fields.Many2one(copy=False, domain=lambda self: [('groups_id', 'in', [
        self.env.ref('sales_team.group_sale_salesman').id,
        self.env.ref('bouygues.bouygues_trade_sales_group').id,
    ])])
    is_distrimo_company = fields.Boolean(compute='_compute_is_distrimo_company')
    sale_date = fields.Date(string='Sale Date')
    commitment_date = fields.Datetime(states={}, string='Delivery Date', copy=False, compute='_compute_commitment_date', store=True, readonly=False)
    is_pablo_delivered = fields.Boolean(compute='_compute_is_pablo_delivered')
    add_delivered_used = fields.Boolean()
    pricelist_id = fields.Many2one(default=_default_pricelist_id)
    has_kit = fields.Boolean(sudo_compute='_compute_has_kit')

    @api.depends('order_line')
    def _compute_has_kit(self):
        for rec in self:
            rec.has_kit = False
            bom_ids = self.env['mrp.bom'].search([('type', '=', 'phantom'), ('product_tmpl_id', 'in', rec.order_line.product_template_id.ids)])
            if bom_ids:
                rec.has_kit = True
                rec.picking_policy = 'one'
            else:
                rec.picking_policy = 'direct'

    def _compute_is_pablo_delivered(self):
        for rec in self:
            rec.is_pablo_delivered = True
            for line in rec.order_line:
                if 'HS' in line.name:
                    a = 1+1
                if line.name[:2] != 'HS' and line.product_uom_qty > line.qty_delivered:
                    rec.is_pablo_delivered = False

    @api.depends('partner_id', 'partner_id.delivery_date_day')
    def _compute_commitment_date(self):
        for rec in self:
            delivery_date = datetime.today()
            rec.commitment_date = False
            if rec.partner_id.delivery_date_day:
                while delivery_date.weekday() != int(rec.partner_id.delivery_date_day):
                    delivery_date += timedelta(1)
                rec.commitment_date = datetime.combine(delivery_date, datetime.min.time())

    def _compute_is_distrimo_company(self):
        for rec in self:
            rec.is_distrimo_company = True if 'Distrimo' in self.env.company.name else False

    def action_assign_to_me(self):
        self.write({'assigned_user_id': self.env.user.id})

    def _dummy_compute(self):
        pass

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id and not self.env.context.get('default_is_rental_order'):
            warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
            self.warehouse_id = warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)

    def _search_my_sales_team(self, operator, value):
        team_id = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        sale_order_ids = self.env['sale.order'].search([('team_id', '=', team_id.id)])
        return [('id', 'in', sale_order_ids.ids)]

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        if self.is_rental_order:
            distriplus_warehouse = self.env['stock.warehouse'].search([('name', 'ilike', 'distriplus')], limit=1)
            if distriplus_warehouse:
                self.warehouse_id = distriplus_warehouse
            else:
                warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
                self.warehouse_id = warehouse_id or self.env['stock.warehouse'].search(
                    [('company_id', '=', self.company_id.id)], limit=1)
        elif self.partner_shipping_id and self.partner_shipping_id.zip and self.partner_shipping_id.country_id.code == 'FR':
            zip_id = self.env['res.zip'].search([('name', '=', self.partner_shipping_id.zip)], limit=1)
            if zip_id:
                self.warehouse_id = zip_id.warehouse_id
            else:
                warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
                self.warehouse_id = warehouse_id or self.env['stock.warehouse'].search(
                    [('company_id', '=', self.company_id.id)], limit=1)
        else:
            warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
            self.warehouse_id = warehouse_id or self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)], limit=1)

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.purchase_order_ids.ids)]
        return action

    @api.depends('purchase_order_ids')
    def _compute_purchase_orders_count(self):
        for rec in self:
            rec.purchase_orders_count = len(rec.purchase_order_ids)

    def _compute_purchase_order_ids(self):
        for rec in self:
            rec.purchase_order_ids = self.env['purchase.order'].search([('sale_order_ids', 'in', rec.id)])

    @api.depends('partner_id')
    def _compute_partner_child_parent_ids(self):
        for rec in self:
            rec.partner_parent_child_ids = rec.partner_id._get_partner_parent_ids() | rec.partner_id._get_partner_child_ids()

    @api.constrains('client_order_ref')
    def _check_client_order_ref(self):
        for rec in self:
            if rec.client_order_ref:
                self.env.cr.execute("SELECT COUNT(*) FROM sale_order WHERE lower(client_order_ref) = %s AND id != %s", (rec.client_order_ref.lower(), rec.id))
                count = self.env.cr.fetchone()[0]
                if count > 0:
                    raise ValidationError('Customer Reference must be unique')

    @api.depends('state', 'picking_ids', 'order_line', 'picking_ids.state', 'add_delivered_used')
    def _compute_so_state(self):
        for rec in self:
            if rec.state == 'draft' or rec.state == 'sent' or rec.state == 'cancel':
                rec.so_state = rec.state
            else:
                done_pickings = rec.picking_ids.filtered(lambda p: p.state == 'done')
                done_cancelled_pickings = rec.picking_ids.filtered(lambda p: p.state in ['cancel', 'done'])
                delivered_lines = rec.order_line.filtered(lambda l: float_compare(l.product_uom_qty, l.qty_delivered, precision_digits=3) == 0)
                partial_sale = len(rec.order_line.filtered(lambda l: l.qty_delivered > 0)) > 0
                # Toutes les quantitées livrées = commandées + tout en done
                if len(done_pickings) == len(rec.picking_ids) and len(delivered_lines) == len(rec.order_line) and len(rec.order_line) > 0:
                    rec.so_state = 'total_sale'
                    if not rec.sale_date:
                        rec.sale_date = datetime.now().date()
                # Tout en done ou cancel mais pas toutes les quantitées livrées = commandées
                elif len(done_cancelled_pickings) == len(rec.picking_ids) and len(delivered_lines) != len(rec.order_line) and len(rec.order_line) > 0 and partial_sale:
                    rec.so_state = 'partial_sale'
                    if not rec.sale_date:
                        rec.sale_date = datetime.now().date()
                # Au moins 1 picking done mais pas tous
                elif len(done_pickings) > 0 and len(done_pickings) != len(rec.picking_ids):
                    rec.so_state = 'partial_ship'
                elif rec.state == 'done':
                    rec.so_state = 'done'
                else:
                    rec.so_state = 'progress'

    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if self.partner_id and self.partner_id.so_note:
            self.so_note = self.so_note + self.partner_id.so_note if self.so_note else self.partner_id.so_note

        if not self.partner_id:
            return
        warning = {}
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn and partner.sale_warn == 'warning':
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }

        if warning:
            return {'warning': warning}

    def check_blocking_warning(self):
        partner = self.partner_id
        if partner.sale_warn != 'block' and partner.parent_id:
            partner = partner.parent_id
        if partner.sale_warn and partner.sale_warn == 'block':
            message = ("Warning for %s : %s") % (partner.name, partner.sale_warn_msg)
            return message
        return False

    def action_confirm(self):
        warning = self.check_blocking_warning()
        if warning:
            raise UserError(_(warning))
        if not self.picking_contact_id:
            raise UserError(_('Picking contact is required'))
        if not self.client_order_ref:
            raise UserError(_('Customer reference is required'))
        block_product_id = self.env['ir.config_parameter'].sudo().get_param('bouygues.default_product_id_block')
        for rec in self:
            for line in rec.order_line:
                if line.product_id.id == int(block_product_id):
                    raise UserError(_('A line is a blocked product'))
                if line.price_unit == 0 and line.display_type != 'line_section' and line.display_type != 'line_note':
                    raise UserError(_('A line has a unit price of 0'))

        template = self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
        email_list = []
        if self.picking_contact_id.email:
            email_list.append(str(self.picking_contact_id.email))
        if self.pablo_order_creator_id.email:
            email_list.append(str(self.pablo_order_creator_id.email))
        emails = ','.join(email_list)
        if template and emails:
            email_values = {'email_to': emails, 'email_from': 'noreplydistrimo@bouygues-construction.com'}
            template.send_mail(self.id, email_values=email_values, force_send=True)

        return super(SaleOrder, self.with_context(origin_sale_order_id=self.id, dropship_note=self.so_note)).action_confirm()

    @api.model
    def create(self, vals):
        if vals.get('is_rental_order'):
            vals['pricelist_id'] = self.env.ref("__export__.product_pricelist_6_f5d88853").id
            wrhs = self.env['stock.warehouse'].search([('name', 'ilike', 'distriplus')], limit=1)
            if wrhs:
                vals['warehouse_id'] = wrhs.id
        elif vals.get('partner_shipping_id'):
            partner_shipping_id = self.env['res.partner'].browse(vals.get('partner_shipping_id'))
            if partner_shipping_id.country_id.code == 'FR':
                zip_id = self.env['res.zip'].search([('name', '=', partner_shipping_id.zip)], limit=1)
                if zip_id:
                    vals['warehouse_id'] = zip_id.warehouse_id.id
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
                        })
        res = super(SaleOrder, self).create(vals)
        if len(eco_product_ids) > 0:
            for product in eco_product_ids:
                product['order_id'] = res.id
                self.env['sale.order.line'].create(product)
        return res

    def write(self, vals):
        eco_product_ids = []
        if vals.get('is_rental_order'):
            vals['pricelist_id'] = self.env.ref("__export__.product_pricelist_6_f5d88853").id
            wrhs = self.env['stock.warehouse'].search([('name', 'ilike', 'distriplus')], limit=1)
            if wrhs:
                vals['warehouse_id'] = wrhs.id
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
                            })
        res = super(SaleOrder, self).write(vals)
        if len(eco_product_ids) > 0:
            for product in eco_product_ids:
                product['order_id'] = self.id
                self.env['sale.order.line'].create(product)
        return res

    def select_products(self):
        action = ({
            'type': 'ir.actions.act_window',
            'name': _('Select multiple products'),
            'res_model': 'sale.order.multiple.product',
            'view_id': self.env.ref("bouygues.bouygues_sale_order_multiple_product_view_form").id,
            'target': 'new',
            'view_mode': 'form',
        })
        return action

    def extract_sales_count(self, minimum_amount, maximum_amount):
        filename = 'sales_count - ' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Commande;Client;Warehouse;Montant HTVA;'

        fields = [
            'sale.name',
            'sale.partner_id.name',
            'sale.warehouse_id.name',
            'sale.amount_untaxed',
        ]

        all_sales = self.env['sale.order'].search([('amount_untaxed', '>=', minimum_amount), ('amount_untaxed', '<=', maximum_amount), ('company_id', '=', self.env.company.id)])
        row_data = ''

        for sale in all_sales:
            for field in fields:
                value = str(eval(field))
                row_data += ';' if value.lower() == 'false' else value + ';'
            row_data += '\n'

        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Sales Count - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def extract_client_sales(self):

        partner_dic = {}
        partner_names = self.env['res.partner'].search_read([('company_id', '=', self.env.company.id)], ['id', 'name'])
        for partner in partner_names:
            partner_dic[str(partner.get('id'))] = str(partner.get('name'))

        domain = [
            ('company_id', '=', self.env.company.id),
            ('partner_id', '!=', False),
        ]

        groups = self.env['sale.order'].read_group(domain, ['amount_total', 'id'], ['partner_id'])

        filename = 'client_sales - ' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Client;Montant TVAC;Nb commande;Montant TVAC/Nb commande;'

        row_data = ''

        for group in groups:
            partner_name = partner_dic.get(str(group.get('partner_id')[0]))
            amount_total = group.get('amount_total')
            partner_id_count = group.get('partner_id_count')
            if partner_name:
                row_data += partner_name + ';' + format(amount_total, '.2f') + ';' + str(partner_id_count) + ';' + format(float(amount_total) / float(partner_id_count), '.2f') + ';' + '\n'

        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Client Sales - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def extract_pablo_delivery(self):
        filename = 'pablo_delivery_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv'

        header = 'Valid SO;Delivered SO; Valid SO / Delivered SO (%);'

        valid_so = 0
        delivered_so = 0
        pablo_so_ids = self.env['pablo.sale.order'].search([('pablo_sale_order_state', '=', 'done'), ('sale_order_id', '!=', False)])
        for pablo_so_id in pablo_so_ids:
            if len(pablo_so_id.sale_order_id.order_line.filtered(lambda l: l.name[:2] != 'HS')) > 0:
                valid_so += 1
                if len(pablo_so_id.sale_order_id.order_line.filtered(lambda l: float_compare(l.product_uom_qty, l.qty_delivered, precision_digits=3) != 0 and l.name[:2] != 'HS')) == 0:
                    delivered_so += 1

        value = (float(delivered_so)/float(valid_so))*100

        row_data = str(valid_so) + ';' + str(delivered_so) + ';' + format(value, '.2f') + ';' + '\n'

        data = header + '\n' + row_data

        byte_data = data.encode()

        self.env['export.wms'].create({
            'name': 'Extraction : Pablo Delivery - ' + datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss"),
            'filename': filename,
            'export_file': base64.encodestring(byte_data)
        })

    def action_print_sale_order_report_distrimo(self):
        return self.env.ref('bouygues.action_sale_order_report_distrimo_bouygues').report_action(self)