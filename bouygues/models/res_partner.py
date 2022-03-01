# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime
#
# CONSTRUCTION_SITE_TYPE = 'construction_site'
#
# MODEL_NAME = 'res.partner'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    industry_name = fields.Char(string='Industry Name', related='industry_id.name')
    is_customer = fields.Boolean(string='Customer', default=False)
    is_supplier = fields.Boolean(string='Is Supplier', default=False)
    is_user = fields.Boolean(string='User', default=False)
    so_note = fields.Text(string='SO Note')
    product_location_responsible_ids = fields.One2many('product.location.responsible', 'partner_id', string='Responsibles')
    dropship_responsible_id = fields.Many2one('res.users', string='Dropship Responsible')
    abbreviation = fields.Char(string='Abbreviation')
    linked_partner_id = fields.Many2one('res.partner', string='Linked partner', compute='_compute_linked_partner_id')
    current_abbreviation_path = fields.Char(string='Current Abbreviation Path', compute='_compute_current_abbreviation_path')
    portal_access_to_give = fields.Boolean(copy=False, string='Portal access to give')
    portal_access_given = fields.Boolean(copy=False, string='Portal access given')
    partner_category_id = fields.Many2one('partner.category', copy=False, string='Partner Category')
    mandatory_country = fields.Boolean(compute='_compute_mandatory_country')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', required=False)
    code_supplier = fields.Char(string='Code Supplier')
    fax = fields.Char(string='Fax')
    id_v12 = fields.Char(string='ID V12')
    delivery_date_day = fields.Selection([('0', 'Lundi'), ('1', 'Mardi'), ('2', 'Mercredi'), ('3', 'Jeudi'), ('4', 'Vendredi'), ('5', 'Samedi'), ('6', 'Dimanche')], string='Delivery Day')
    property_product_pricelist = fields.Many2one(compute_sudo=True)
    connected_so_ids = fields.One2many('sale.order', inverse_name='picking_contact_id')

    @api.depends('type')
    def _compute_mandatory_country(self):
        for rec in self:
            rec.mandatory_country = True if rec.type in ['invoice', 'delivery', 'other', 'private'] else False

    def _get_partner_parent_ids(self):
        parent_ids = self.parent_id
        return self if not parent_ids else self | parent_ids._get_partner_parent_ids()

    def _get_partner_child_ids(self):
        child_ids = self.child_ids
        return self if not child_ids else self | child_ids._get_partner_child_ids()

    @api.depends('parent_id')
    def _compute_linked_partner_id(self):
        for rec in self:
            rec.linked_partner_id = rec.parent_id

    @api.depends('abbreviation', 'parent_id')
    def _compute_current_abbreviation_path(self):
        for rec in self:
            if rec.parent_id:
                rec.current_abbreviation_path = rec.parent_id.current_abbreviation_path + ' | ' + (rec.abbreviation if rec.abbreviation else '????')
            else:
                rec.current_abbreviation_path = rec.abbreviation if rec.abbreviation else '????'

    def name_get(self):
        if self._context.get('partner_show_abbreviation'):
            res = []
            for partner in self:
                name = partner.current_abbreviation_path
                res.append((partner.id, name))
            return res
        return super(ResPartner, self).name_get()

    @api.constrains('name')
    def _check_supplier_name(self):
        for rec in self:
            forbidden_characters = [';', '#', '"', '_', '\\', '/']
            for character in forbidden_characters:
                if rec.name and character in rec.name:
                    raise ValidationError('You cannot use special character in the name')
            if rec.name and rec.is_supplier:
                self.env.cr.execute("SELECT COUNT(*) FROM res_partner WHERE lower(name) = %s AND is_supplier", (rec.name.lower(),))
                count = self.env.cr.fetchone()[0]
                if count > 1:
                    raise ValidationError('Supplier name must be unique')
