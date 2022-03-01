# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import xml.etree.ElementTree as ET
import base64
# from lxml import etree

from odoo.exceptions import UserError


class PabloImport(models.Model):
    _name = 'pablo.import'
    _description = 'Pablo Imports'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', copy=False, readonly=True, default=lambda self: _('New'))
    filename = fields.Char(string='Filename')
    import_file = fields.Binary(string='Import File', copy=False)
    import_date = fields.Datetime(string='Import Date', copy=False)
    imported = fields.Boolean(copy=False, default=False)
    import_state = fields.Selection(readonly=True, selection=[('draft', "Draft"), ('imported', "Imported")], copy=False, default='draft')
    pablo_sale_order_ids = fields.One2many('pablo.sale.order', 'pablo_import_id')
    pablo_sale_order_count = fields.Integer(string='Pabloo Sale Orders', compute='_compute_pablo_sale_order_count')
    company_id = fields.Many2one('res.company', string='Company')
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the type.type without removing it.")

    def action_view_pablo_sale_orders(self):
        self.ensure_one()
        action = self.env.ref('bouygues.action_pablo_sale_order').read()[0]
        action['domain'] = [('pablo_import_id', '=', self.id)]
        return action

    @api.depends('pablo_sale_order_ids')
    def _compute_pablo_sale_order_count(self):
        for rec in self:
            rec.pablo_sale_order_count = len(rec.pablo_sale_order_ids)

    @api.model
    def create(self, vals):
        vals['name'] = 'Pablo import ' + self.env['ir.sequence'].next_by_code('pablo.import.sequence')
        return super(PabloImport, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.pablo_sale_order_ids:
                raise UserError(_('You can only delete pablo.import if no pablo.sale.order is present'))

    def import_sale_order(self):
        for rec in self:
            if not rec.import_file:
                continue
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': 'Pablo import %s' % rec.id,
                'code': 'pablo.import.%s' % rec.id,
                'padding': '3',
            })
            pablo_sale_order_values = []
            xml_file = base64.decodebytes(rec.import_file)

            root = ET.fromstring(xml_file)

            for record in root.findall('Record'):
                code_ste = record.find('CODE_STE').text
                sectimp = record.find('SECTIMP').text

                import_picking_contact = record.find('NMCTC1L').text if record.find('NMCTC1L').text else ''
                import_picking_contact_2 = record.find('NMCTC2L').text if record.find('NMCTC2L').text else ''
                import_pablo_order_creator = record.find('DEMANDEUR').text if record.find('DEMANDEUR').text else ''
                pablo_note = record.find('TITRE_CDE').text if record.find('TITRE_CDE').text else ''
                import_delivery_address = record.find('NOM_LIV').text if record.find('NOM_LIV').text else ''
                import_delivery_address_street = record.find('ADR_LIV').text if record.find('ADR_LIV').text else ''
                import_delivery_address_city_zip = record.find('VIL_LIV').text if record.find('VIL_LIV').text else ''
                customer_ref = record.find('ID_GED').text[:-4] if record.find('ID_GED').text else ''
                pablo_pdf = record.find('URL_GED').text if record.find('URL_GED').text else ''
                to_be_active = True
                status = 'draft'

                if record.find('NMCTC2L').text:
                    pablo_note += ' Picking contact 2 : ' + record.find('NMCTC2L').text

                existing_ref_so = self.env['sale.order'].search([('client_order_ref', '=', customer_ref)])
                existing_ref_pablo_so = self.env['pablo.sale.order'].search([('customer_ref', '=', customer_ref)])

                if len(existing_ref_pablo_so) > 0 or len(existing_ref_so) > 0:
                    to_be_active = False
                    status = 'doublon'

                customer_id = False
                if code_ste and sectimp:
                    customer_id = self.env['res.partner'].search([('ref', '=', code_ste + '.' + sectimp), ('parent_id', '=', False)], limit=1)
                picking_contact_id = self.env['res.partner'].search([('name', '=', record.find('NMCTC1L').text)], limit=1) if record.find('NMCTC1L').text else False
                pablo_order_creator_id = self.env['res.partner'].search([('name', '=', record.find('DEMANDEUR').text)], limit=1) if record.find('DEMANDEUR').text else False
                if not customer_id and code_ste and sectimp:
                    customer_id = self.env['res.partner'].search([('ref', '=', code_ste + sectimp), ('parent_id', '=', False)], limit=1)

                code_ste = code_ste if code_ste else ''
                sectimp = sectimp if sectimp else ''

                import_customer = code_ste + '.' + sectimp
                analytic_imputation = code_ste + '.' + sectimp

                pablo_sale_order_lines_values = []
                lignes_comm = record.find('Lignes_commande')

                pablo_sale_order_lines_ids = False
                if lignes_comm:
                    for line in record.find('Lignes_commande').findall('Ligne'):
                        product_id = self.env['product.product'].search([('default_code', '=', line.find('REF_FOUR').text)], limit=1) if line.find('REF_FOUR').text else False
                        line_code_ste = line.find('CODE_STE').text if line.find('CODE_STE').text else ''
                        line_sectimp = '.' + line.find('SECTIMP').text if line.find('SECTIMP').text else ''
                        line_codges = '.' + line.find('CODGES').text if line.find('CODGES').text else ''
                        line_analytic_imputation = line_code_ste + line_sectimp + line_codges

                        price_list_item = False
                        if product_id:
                            price_list_item = self.env['product.pricelist.item'].search([('pricelist_id', '=', 6), ('product_id', '=', product_id.id), ('date_start', '<=', fields.Date.today()), ('date_end', '>=', fields.Date.today())], limit=1)
                        price = 0.0
                        if price_list_item:
                            price = price_list_item.fixed_price
                        elif product_id:
                            price = product_id.lst_price
                        pablo_sale_order_lines_values.append({'product_id': product_id.id if product_id else False,
                                                              'price': price,
                                                              'pablo_ref': line.find('REF_FOUR').text,
                                                              'analytic_imputation': line_analytic_imputation,
                                                              'imported_price': line.find('PU').text,
                                                              'product_uom_qty': line.find('QTE_COMM').text})

                    pablo_sale_order_lines_ids = self.env['pablo.sale.order.line'].create(pablo_sale_order_lines_values)

                pablo_sale_order_values.append({'customer_id': customer_id.id if customer_id else False,
                                                'pablo_import_id': rec.id,
                                                'active': to_be_active,
                                                'pablo_sale_order_state': status,
                                                'picking_contact_id': picking_contact_id.id if picking_contact_id else False,
                                                'pablo_order_creator_id': pablo_order_creator_id.id if pablo_order_creator_id else False,
                                                'name': '%s - %s' % (rec.name, sequence_id[0]._next()),
                                                'import_customer': import_customer,
                                                'analytic_imputation': analytic_imputation,
                                                'customer_ref': customer_ref,
                                                'pablo_pdf': pablo_pdf,
                                                'pablo_note': pablo_note,
                                                'import_delivery_address': import_delivery_address,
                                                'import_delivery_address_street': import_delivery_address_street,
                                                'import_delivery_address_city_zip': import_delivery_address_city_zip,
                                                'import_picking_contact': import_picking_contact,
                                                'import_picking_contact_2': import_picking_contact_2,
                                                'import_pablo_order_creator_id': import_pablo_order_creator,
                                                'pablo_sale_order_line_ids': [(6, 0, pablo_sale_order_lines_ids.ids)] if pablo_sale_order_lines_ids else False})

            for sale_order_value in pablo_sale_order_values:
                pablo_sale_order = self.env['pablo.sale.order'].create(sale_order_value)

            rec.import_date = fields.Datetime.now()
            rec.import_state = 'imported'
            rec.imported = True
            sequence_id.unlink()

    def message_new(self, msg, custom_values=None):
        if custom_values is None:
            custom_values = {}
        attachments = msg.get('attachments')
        if attachments:
            custom_values['filename'] = attachments[0].fname
            custom_values['import_file'] = base64.encodebytes(attachments[0].content)
        result = super(PabloImport, self).message_new(msg, custom_values=custom_values)
        if attachments:
            if len(attachments) > 1:
                for attachment in attachments[1:]:
                    res = self.env['pablo.import'].create({
                        'filename': attachment.fname,
                        'import_file': base64.encodebytes(attachment.content),
                    })
                    res.import_sale_order()
            result.import_sale_order()
        return result
