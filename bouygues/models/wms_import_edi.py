# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, tools
from datetime import datetime
import csv
from io import StringIO, BytesIO
import base64
from datetime import datetime


class WmsImportEdi(models.Model):
    _inherit = 'edi.integration'

    type = fields.Selection(
        selection_add=[('wms_import_stock_picking_preparation', 'WMS Import - stock.picking Preparation'),
                       ('wms_import_stock_picking_reception', 'WMS Import - stock.picking Reception'),
                       ('wms_import_mrp_production_validation', 'WMS Import - mrp.production Validation'),
                       ('wms_import_product_product_stock', 'WMS Import - product.product Stock'),
                       ('wms_import_product_product_data', 'WMS Import - product.product Data'),
                       ('wms_import_inventory_adjustment', 'WMS Import - Inventory Adjustment'),
                       ('wms_import_move_line_preparation', 'WMS Import - Move Line Preparation'),
                       ],
        ondelete={
                'wms_import_stock_picking_preparation': 'cascade',
                'wms_import_stock_picking_reception': 'cascade',
                'wms_import_mrp_production_validation': 'cascade',
                'wms_import_product_product_stock': 'cascade',
                'wms_import_product_product_data': 'cascade',
                'wms_import_inventory_adjustment': 'cascade',
                'wms_import_move_line_preparation': 'cascade',
                })

    def get_all_xml_ids_import(self):
        xml_ids_dic = {}
        xml_ids = self.env['ir.model.data'].search_read([('model', '=', 'product.product')], ['complete_name', 'res_id'])
        for xml_id in xml_ids:
            xml_ids_dic[str(xml_id.get('complete_name'))] = str(xml_id.get('res_id'))
        return xml_ids_dic

    def _process_content(self, filename, content):
        if self.type == 'wms_import_stock_picking_preparation':
            self._process_data(filename, content)
        elif self.type == 'wms_import_stock_picking_reception':
            self._process_data(filename, content)
        elif self.type == 'wms_import_mrp_production_validation':
            self._process_data(filename, content)
        elif self.type == 'wms_import_product_product_stock':
            self._process_data(filename, content)
        elif self.type == 'wms_import_product_product_data':
            self._process_data(filename, content)
        elif self.type == 'wms_import_inventory_adjustment':
            self._process_data(filename, content)
        elif self.type == 'wms_import_move_line_preparation':
            self._process_data(filename, content)
        else:
            return super()._get_record_to_send()

        return "done"

    def _process_data(self, filename, content):
        pickings_to_validate = self.env['stock.picking']
        file_read = StringIO(content)
        reader = csv.DictReader(file_read, delimiter=';')

        current_picking = ''
        current_mrp_production_id = ''
        current_move_line = ''

        if self.type == 'wms_import_stock_picking_reception':

            locations = {}

            if 'CHM' in filename:
                locations = {
                    'STD': 'self.env["stock.location"].search([("name", "=", "Stock"), ("location_id", "=", 53)])',
                    'CASSE': 'self.env["stock.location"].search([("name", "=", "DICHM-CASSE")])',
                    'DEP': 'self.env["stock.location"].search([("name", "=", "DICHM-DEP")])',
                    'HOM': 'self.env["stock.location"].search([("name", "=", "DICHM-HOM")])',
                    'MQT': 'self.env["stock.location"].search([("name", "=", "DICHM-MQT")])',
                    'NC': 'self.env["stock.location"].search([("name", "=", "DICHM-NC")])',
                    'NS': 'self.env["stock.location"].search([("name", "=", "DICHM-NS")])',
                    'RET': 'self.env["stock.location"].search([("name", "=", "DICHM-RET")])',
                    'SAV': 'self.env["stock.location"].search([("name", "=", "DICHM-SAV")])',
                }
            if 'TLR' in filename:
                locations = {
                    'STD': 'self.env["stock.location"].search([("name", "=", "Stock"), ("location_id", "=", 21)])',
                    'CASSE': 'self.env["stock.location"].search([("name", "=", "DITLR-CASSE")])',
                    'DEP': 'self.env["stock.location"].search([("name", "=", "DITLR-DEP")])',
                    'HOM': 'self.env["stock.location"].search([("name", "=", "DITLR-HOM")])',
                    'MQT': 'self.env["stock.location"].search([("name", "=", "DITLR-MQT")])',
                    'NC': 'self.env["stock.location"].search([("name", "=", "DITLR-NC")])',
                    'NS': 'self.env["stock.location"].search([("name", "=", "DITLR-NS")])',
                    'RET': 'self.env["stock.location"].search([("name", "=", "DITLR-RET")])',
                    'SAV': 'self.env["stock.location"].search([("name", "=", "DITLR-SAV")])',
                }

            for row in reader:
                if not current_picking == row['REA_ALPHA15']:
                    picking = self.env['stock.picking'].browse(
                        self.env['ir.model.data'].search([('name', '=', row['REA_ALPHA15'].split('.')[1])]).res_id)
                    current_picking = row['REA_ALPHA15']
                    if picking:
                        picking.import_filename = filename
                        pickings_to_validate |= picking
                        picking.top_litige = True if int(row['REL_TOP1']) == 1 else False
                        picking.quality_code = row['QUA_CODE']
                        picking.booking_ref = row['REE_NOFO']
                        picking.speedwms_ref = int(row['REE_NORE']) if row['REE_NORE'] else 0
                        if row['REE_DARE']:
                            date_string = row['REE_DARE'] + '000000'
                            picking.date_done = datetime.strptime(date_string, '%Y%m%d%H%M%S')
                if not current_move_line == row['REA_ALPHA11']:
                    move_line = self.env['stock.move.line'].browse(
                        self.env['ir.model.data'].search([('name', '=', row['REA_ALPHA11'].split('.')[1])]).res_id)
                    current_move_line = row['REA_ALPHA11']
                if move_line:
                    if picking.is_resupply:
                        move_line.lot_id = False
                    if row['QUA_CODE'] == 'STD' or row['QUA_CODE'] == 'HOM' or row['QUA_CODE'] == 'RET':
                        move_line.qty_done = float(row['MVT_QTE']) if row['MVT_QTE'] else 0.0
                    else:
                        new_move_line = move_line.copy()
                        new_move_line.qty_done = float(row['MVT_QTE']) if row['MVT_QTE'] else 0.0
                        new_move_line.picking_id = picking
                        new_move_line.location_dest_id = eval(locations.get(row['QUA_CODE']))

            for pick in pickings_to_validate:
                pick.with_context(custom_date_done=True).action_done()

        if self.type == 'wms_import_stock_picking_preparation':
            for row in reader:
                if not current_picking == row['OPL_ALPHA13']:
                    picking = self.env['stock.picking'].browse(
                        self.env['ir.model.data'].search([('name', '=', row['OPL_ALPHA13'].split('.')[1])]).res_id)
                    current_picking = row['OPL_ALPHA13']
                    if picking:
                        picking.import_filename = filename.split('/')[-1]
                        pickings_to_validate |= picking
                        picking.transporter_id = self.env['res.partner'].browse(self.env['ir.model.data'].search([('name', '=', row['TIE_ALPHA12'].split('.')[1])]).res_id) if row['TIE_ALPHA12'] else False
                        picking.weight = float(row['SEX_POISR']) if row['SEX_POISR'] else 0.0
                if not current_move_line == row['OPL_ALPHA12']:
                    move_line = self.env['stock.move.line'].browse(
                        self.env['ir.model.data'].search([('name', '=', row['OPL_ALPHA12'].split('.')[1])]).res_id)
                    current_move_line = row['OPL_ALPHA12']
                    if move_line:
                        move_line.qty_done = float(row['MIL_QTTP']) if row['MIL_QTTP'] else 0.0
                        if row['NSE_NUMS']:
                            move_line.lot_id = self.env['stock.production.lot'].create({
                                'name': row['NSE_NUMS'],
                                'product_id': move_line.product_id.id,
                                'company_id': 2,
                            })

            for rec in pickings_to_validate:
                if len(rec.move_line_ids_without_package.filtered(lambda l: l.qty_done > 0)) == 0:
                    rec.wms_exported = False
                    if '-' in rec.name:
                        name_number = rec.name.split('-')[1]
                        new_name_number = str(int(name_number) + 1)
                        rec.name = rec.name.replace('-' + name_number, '-' + new_name_number)
                    else:
                        rec.name += '-1'
                    continue
                pickings = self.env['stock.picking']
                for move in rec.move_ids_without_package:
                    for dest_move in move.move_dest_ids:
                        pickings |= dest_move.picking_id
                list(set(pickings))
                rec.action_done()
                for pick in pickings:
                    for move in pick.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                    pick.action_done()
                    template = self.env.ref('bouygues.bouygues_mail_template_stock_picking_delivery_report',
                                            raise_if_not_found=False)
                    email_list = []
                    if pick.picking_contact_id.email:
                        email_list.append(str(pick.picking_contact_id.email))
                    if pick.sale_id.pablo_order_creator_id.email:
                        email_list.append(str(pick.sale_id.pablo_order_creator_id.email))
                    emails = ','.join(email_list)

                    if template and emails and pick.state == 'done':
                        email_values = {'email_to': emails, 'email_from': 'noreplydistrimo@bouygues-construction.com'}
                        template.send_mail(pick.id, email_values=email_values, force_send=True)

        if self.type == 'wms_import_move_line_preparation':
            for row in reader:
                move_line = self.env['stock.move.line'].browse(self.env['ir.model.data'].search([('name', '=', row['OPL_ALPHA12'].split('.')[1])]).res_id)
                if move_line:
                    move_line.qty_done = float(row['MIL_QTTP'])

        if self.type == 'wms_import_mrp_production_validation':

            # Returns a dic with 'xml_id': product_id
            xml_ids_dic = self.get_all_xml_ids_import()

            # Store all production and mrp production to validate them at the end
            production_to_validate = self.env['mrp.product.produce']
            mrp_production_to_validate = self.env['mrp.production']

            for row in reader:

                # Check if the mrp_production is the same so we don't search for it again
                if not current_mrp_production_id == row['OPE_ALPHA18']:
                    mrp_production_id = self.env['mrp.production'].browse(self.env['ir.model.data'].search([('name', '=', row['OPE_ALPHA18'].split('.')[1])]).res_id)
                    mrp_production_to_validate |= mrp_production_id
                    current_mrp_production_id = row['OPE_ALPHA18']
                    if mrp_production_id and mrp_production_id.state == 'confirmed':
                        production = self.env['mrp.product.produce'].with_context(default_production_id=mrp_production_id.id).create({'production_id': mrp_production_id.id})
                        production_to_validate |= production
                        production._generate_produce_lines()

                # Get the current product
                product_id = self.env['product.product'].browse(int(xml_ids_dic.get(row['OPL_ALPHA11'])))

                # Check if we have serial numbers for this product
                if row['NSE_NUMS']:
                    serial_number_list = row['NSE_NUMS'].split(',')

                    # For each serial number, we need to assign it to a line with a qty of 1
                    for serial_number in serial_number_list:

                        # Get the line for the corresponding product
                        raw_workorder_line_id = production.raw_workorder_line_ids.filtered(lambda l: l.product_id == product_id and not l.lot_id)

                        # Create a serial number for this line and put the qty at 1
                        raw_workorder_line_id[0].lot_id = self.env['stock.production.lot'].create({
                            'name': serial_number,
                            'product_id': product_id.id,
                            'company_id': 2,
                        })

                        raw_workorder_line_id[0].qty_done = 1

                # If there is no serial number, we just put the qty done for the corresponding line
                else:
                    raw_workorder_line_id = production.raw_workorder_line_ids.filtered(lambda l: l.product_id == product_id)
                    raw_workorder_line_id[0].qty_done = float(row['OPL_QTAP'])

            list(set(production_to_validate))
            for prod in production_to_validate:
                prod.do_produce()

            list(set(mrp_production_to_validate))
            for mrp_prod in mrp_production_to_validate:
                mrp_prod.button_mark_done()

        if self.type == 'wms_import_product_product_stock':
            xml_ids_dic = self.get_all_xml_ids_import()
            products_dic = {}
            error_list = []

            product_id_list = []
            for row in reader:
                product_id_list.append(int(xml_ids_dic.get(row['ART_ALPHA11'])))

            if 'CHM' in filename:
                all_products = self.env['product.product'].search_read([('id', 'in', product_id_list)], ['id', 'qty_available_chilly', 'qty_available_chilly_casse', 'qty_available_chilly_dep', 'qty_available_chilly_hom', 'qty_available_chilly_mqt', 'qty_available_chilly_nc', 'qty_available_chilly_ns', 'qty_available_chilly_ret', 'qty_available_chilly_sav'])
                for product in all_products:
                    products_dic[str(product.get('id'))] = {
                        'STD': str(product.get('qty_available_chilly')),
                        'CASSE': str(product.get('qty_available_chilly_casse')),
                        'DEP': str(product.get('qty_available_chilly_dep')),
                        'HOM': str(product.get('qty_available_chilly')),
                        'MQT': str(product.get('qty_available_chilly_mqt')),
                        'NC': str(product.get('qty_available_chilly_nc')),
                        'NS': str(product.get('qty_available_chilly_ns')),
                        'RET': str(product.get('qty_available_chilly_ret')),
                        'SAV': str(product.get('qty_available_chilly_sav')),
                    }

            if 'TLR' in filename:
                all_products = self.env['product.product'].search_read([('id', 'in', product_id_list)], ['id', 'qty_available_tourville', 'qty_available_tourville_casse', 'qty_available_tourville_dep', 'qty_available_tourville_hom', 'qty_available_tourville_mqt', 'qty_available_tourville_nc', 'qty_available_tourville_ns', 'qty_available_tourville_ret', 'qty_available_tourville_sav'])
                for product in all_products:
                    products_dic[str(product.get('id'))] = {
                        'STD': str(product.get('qty_available_tourville')),
                        'CASSE': str(product.get('qty_available_tourville_casse')),
                        'DEP': str(product.get('qty_available_tourville_dep')),
                        'HOM': str(product.get('qty_available_tourville')),
                        'MQT': str(product.get('qty_available_tourville_mqt')),
                        'NC': str(product.get('qty_available_tourville_nc')),
                        'NS': str(product.get('qty_available_tourville_ns')),
                        'RET': str(product.get('qty_available_tourville_ret')),
                        'SAV': str(product.get('qty_available_tourville_sav')),
                    }

            file_read = StringIO(content)
            reader = csv.DictReader(file_read, delimiter=';')
            for row in reader:
                id_product = xml_ids_dic.get(row['ART_ALPHA11'])
                qty_available = products_dic.get(id_product).get(row['QUA_CODE'])
                if float(qty_available) != float(row['PST_QTED']):
                    error_list.append({
                        'id': str(row['ART_ALPHA11']),
                        'qty_odoo': str(qty_available),
                        'qty_wms': str(row['PST_QTED']),
                        'qua_code': str(row['QUA_CODE'])
                        })

            if len(error_list) > 0:
                for error in error_list:
                    row_data = error.get('id') + ';' + error.get('qty_odoo') + ';' + error.get('qty_wms') + ';' + error.get('qua_code') + ';'
                    row_data += '\n'

                data = 'id;qty_odoo;qty_wms;qua_code' + '\n' + row_data

                byte_data = data.encode()

                warning_name = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                self.env['stock.warning'].create({
                    'name': warning_name,
                    'filename': 'error_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.csv',
                    'file': base64.encodestring(byte_data)
                })

                values = self.env.ref('bouygues.bouygues_mail_template_product_stock_import_warning').generate_email(self.id, fields=None)
                values['email_from'] = self.env.company.email
                values['email_to'] = 'damien.micheaux@bksystemes.fr'
                values['body_html'] = '<p>New warning regarding product stock from import. Please check the warning named: ' + warning_name
                values['body'] = tools.html_sanitize(values['body_html'])
                mail = self.env['mail.mail'].create(values)
                mail.send()

        if self.type == 'wms_import_product_product_data':
            xml_ids_dic = self.get_all_xml_ids_import()

            for row in reader:
                product_id = self.env['product.product'].browse(int(xml_ids_dic.get(row['ART_ALPHA11'])))
                product_id.art_eanu = row['ART_EANU']
                product_id.art_eanc = row['ART_EANC']
                product_id.art_eanp = row['ART_EANP']
                product_id.weight = float(row['ART_POIU'])
                product_id.art_lonu = float(row['ART_LONU'])
                product_id.art_laru = float(row['ART_LARU'])
                product_id.art_hauu = float(row['ART_HAUU'])
                product_id.art_qtec = int(row['ART_QTEC'])
                product_id.Art_qtep = int(row['ART_QTEP'])
                product_id.art_code = row['ART_ALPHA1']
                product_id.class_code = row['ART_ALPHA2']
                product_id.packing_code = row['ART_ALPHA3']
                product_id.ICPE_code = row['ART_ALPHA4']
                product_id.customs_code = row['ART_ALPHA6']

                native_country_id = self.env['res.country'].search([('code', '=', row['ART_ALPHA5'])])
                product_id.native_country_id = native_country_id if native_country_id else False

        if self.type == 'wms_import_inventory_adjustment':
            xml_ids_dic = self.get_all_xml_ids_import()

            line_dic = []
            product_id_list = []

            if 'CHM' in filename:
                location_id = self.env["stock.location"].search([("name", "=", "Stock"), ("location_id", "=", 53)])
            if 'TLR' in filename:
                location_id = self.env["stock.location"].search([("name", "=", "Stock"), ("location_id", "=", 21)])

            for row in reader:
                product_id_list.append(int(xml_ids_dic.get(row['ART_ALPHA11'])))
                line_dic.append({
                    'product_id': int(xml_ids_dic.get(row['ART_ALPHA11'])),
                    'from': row['Old_qua_code'],
                    'to': row['New_qua_code'],
                    'qty': int(row['MVT_QTE']),
                })

            stock_inventory_id = self.env['stock.inventory'].create({
                'name': filename[-26:-4],
                'location_ids': [(4, location_id.id,)],
                'company_id': self.env['res.company'].search([('id', '=', 2)]).id,
                'product_ids': [(6, 0, product_id_list)],
            })

            stock_inventory_id._action_start()

            for line in line_dic:
                line_id = stock_inventory_id.line_ids.filtered(lambda l: l.product_id.id == line.get('product_id'))
                if not line_id:
                    line_id = self.env['stock.inventory.line'].create([{
                        'product_id': line.get('product_id'),
                        'location_id': location_id.id,
                        'inventory_id': stock_inventory_id.id
                    }])
                if line_id:
                    if line.get('to') == 'STD':
                        if not (line.get('from') == 'HOM' or line.get('from') == 'RET'):
                            line_id[0].product_qty = line_id[0].product_qty + line.get('qty')
                    elif line.get('to') == 'HOM':
                        line_id[0].product_qty = line_id[0].product_qty + line.get('qty')
                    else:
                        line_id[0].product_qty -= line.get('qty')

            stock_inventory_id._action_done()






