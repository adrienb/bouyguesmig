# -*- coding: utf-8 -*-

from odoo import http, models, fields, api
from datetime import datetime


class WmsExportResPartnerChm(models.Model):
    _inherit = 'edi.integration'

    type = fields.Selection(
        selection_add=[('wms_export_res_partner_chm', 'WMS Export - res.partner - CHM'),
                       ('wms_export_res_partner_tlr', 'WMS Export - res.partner - TLR'),
                       ('wms_export_stock_picking_reception_chm', 'WMS Export - stock.picking Reception - CHM'),
                       ('wms_export_stock_picking_reception_tlr', 'WMS Export - stock.picking Reception - TLR'),
                       ('wms_export_stock_picking_preparation_chm', 'WMS Export - stock.picking Preparation - CHM'),
                       ('wms_export_stock_picking_preparation_tlr', 'WMS Export - stock.picking Preparation - TLR'),
                       ('wms_export_stock_picking_intersite_chm', 'WMS Export - stock.picking Intersite - CHM'),
                       ('wms_export_stock_picking_intersite_tlr', 'WMS Export - stock.picking Intersite - TLR'),
                       ('wms_export_product_product_tlr', 'WMS Export - product.product - TLR'),
                       ('wms_export_product_product_chm', 'WMS Export - product.product - CHM'),
                       ('wms_export_mrp_production_chm', 'WMS Export - mrp.production - CHM'),
                       ('wms_export_mrp_production_tlr', 'WMS Export - mrp.production - TLR'),
                       ('wms_export_product_image_tlr', 'WMS Export - Product Image - TLR'),
                       ('wms_export_product_image_chm', 'WMS Export - Product Image - CHM'),
                       ],
        ondelete={
                'wms_export_res_partner_chm': 'cascade',
                'wms_export_res_partner_tlr': 'cascade',
                'wms_export_stock_picking_reception_chm': 'cascade',
                'wms_export_stock_picking_reception_tlr': 'cascade',
                'wms_export_stock_picking_preparation_chm': 'cascade',
                'wms_export_stock_picking_preparation_tlr': 'cascade',
                'wms_export_stock_picking_intersite_chm': 'cascade',
                'wms_export_stock_picking_intersite_tlr': 'cascade',
                'wms_export_product_product_tlr': 'cascade',
                'wms_export_product_product_chm': 'cascade',
                'wms_export_mrp_production_chm': 'cascade',
                'wms_export_mrp_production_tlr': 'cascade',
                'wms_export_product_image_tlr': 'cascade',
                'wms_export_product_image_chm': 'cascade',
                })

    def get_all_data(self):
        if self.type == 'wms_export_product_product_tlr' or self.type == 'wms_export_product_product_chm':
            return self.env['product.product'].search_read(['&', ('wms_exported', '=', False), '|', ('company_id', '=', 2), ('company_id', '=', False)],
                                                           ['id',
                                                                'default_code',
                                                                'art_eanu',
                                                                'art_eanc',
                                                                'art_eanp',
                                                                'variant_display_name',
                                                                'standard_price',
                                                                'weight',
                                                                'art_lonu',
                                                                'art_laru',
                                                                'art_hauu',
                                                                'art_clas',
                                                                'tracking',
                                                                'description_picking',
                                                                'description_pickingout',
                                                                'art_qtec',
                                                                'art_qtep',
                                                                'art_stat',
                                                                'art_code',
                                                                'class_code',
                                                                'packing_code',
                                                                'ICPE_code',
                                                                'native_country_code',
                                                                'customs_code'])

        if self.type == 'wms_export_product_image_tlr':
            return self.env['product.product'].search_read([('type', '=', 'product'), '|', ('company_id', '=', 2), ('company_id', '=', False)], ['id', 'default_code', 'qty_available_tourville'])

        if self.type == 'wms_export_product_image_chm':
            return self.env['product.product'].search_read([('type', '=', 'product'), '|', ('company_id', '=', 2), ('company_id', '=', False)], ['id', 'default_code', 'qty_available_chilly'])

        else:
            return False

    def get_all_xml_ids(self):
        xml_ids_dic = {}
        xml_ids = self.env['ir.model.data'].search_read([('model', '=', 'product.product')], ['complete_name', 'res_id'])
        for xml_id in xml_ids:
            xml_ids_dic[str(xml_id.get('res_id'))] = str(xml_id.get('complete_name'))
        return xml_ids_dic

    def generate_xml_id_product(self, str_id, name, xml_ids_dic):
        if str_id:
            if xml_ids_dic.get(str_id):
                return xml_ids_dic.get(str_id)
            else:
                new_xml_id = self.env['ir.model.data'].create({
                        'module': '__export__',
                        'name': name + str_id,
                        'model': 'product.product',
                        'res_id': int(str_id),
                        'noupdate': False,
                    })
                return str(new_xml_id.complete_name)
        else:
            return 'false'

    def generate_xml_id(self, record, name):
        if record:
            xml_id = self.env['ir.model.data'].search_read([('model', '=', record._name), ('res_id', '=', record.id)], ['complete_name'], limit=1)
            if xml_id:
                return str(xml_id[0].get('complete_name'))
            else:
                new_xml_id = self.env['ir.model.data'].create({
                        'module': '__export__',
                        'name': name + str(record.id),
                        'model': record._name,
                        'res_id': record.id,
                        'noupdate': False,
                    })
                return str(new_xml_id.complete_name)
        else:
            return 'false'

    def _get_synchronization_name_out(self, records):
        return '%s - %s' % (
            self.name,
            fields.Datetime.now()
        )

    def _create_synchronization_out(self, records, flow_type):
        filenames = {
            'wms_export_res_partner_chm': 'CHM_TIE_',
            'wms_export_res_partner_tlr': 'TLR_TIE_',
            'wms_export_stock_picking_reception_chm': 'CHM_ATT_',
            'wms_export_stock_picking_reception_tlr': 'TLR_ATT_',
            'wms_export_stock_picking_preparation_chm': 'CHM_CMD_',
            'wms_export_stock_picking_preparation_tlr': 'TLR_CMD_',
            'wms_export_stock_picking_intersite_chm': 'CHM_CMD_',
            'wms_export_stock_picking_intersite_tlr': 'TLR_CMD_',
            'wms_export_product_product_tlr': 'TLR_ART_',
            'wms_export_product_product_chm': 'CHM_ART_',
            'wms_export_mrp_production_chm': 'CHM_OFS_',
            'wms_export_mrp_production_tlr': 'TLR_OFS_',
            'wms_export_product_image_tlr': 'TLR_ISTK_',
            'wms_export_product_image_chm': 'CHM_ISTK_',
        }

        if filenames.get(self.type):
            filename = filenames.get(self.type) + datetime.now().strftime("%Y%m%d%H%M%S")
        else:
            filename = self._get_synchronization_name_out(records)

        return self.env['edi.synchronization'].create({
            'integration_id': self.id,
            'name': self._get_synchronization_name_out(records),
            'filename': ('%s.%s' % (filename, self.synchronization_content_type))[:100],
            'synchronization_date': fields.Datetime.now(),
        })

    def _get_data(self):
        header = ''
        fields = []

        if self.type == 'wms_export_res_partner_chm' or self.type == 'wms_export_res_partner_tlr':
            header = 'id;code_supplier;name;street;zip;city;country_code/code;phone;fax;email;vat;ref;street2;'
            fields = [
                'self.generate_xml_id(rec, "res_partner_")',
                'rec.code_supplier',
                'rec.name',
                'rec.street',
                'rec.zip',
                'rec.city',
                'rec.country_id.code',
                'rec.phone',
                'rec.fax',
                'rec.email',
                'rec.vat',
                'rec.ref',
                'rec.street2',
            ]
        elif self.type == 'wms_export_stock_picking_reception_chm' or self.type == 'wms_export_stock_picking_reception_tlr':
            header = 'name;move_lines/id;partner_id/id;scheduled_date;move_lines/product_id/id;move_lines/product_id/default_code;move_lines/product_qty;origin;id;purchase_id/origin;move_lines/return_lots;move_lines/supplier_ref;'
            fields = [
                'rec.display_name',
                'self.generate_xml_id(move_line, "stock_move_line_")',
                'self.generate_xml_id(rec.partner_id, "res_partner_")',
                'rec.scheduled_date.date() if rec.scheduled_date else ""',
                'self.generate_xml_id(move_line.product_id, "product_product_")',
                'move_line.product_id.default_code',
                'move_line.move_id.product_uom_qty',
                'rec.origin',
                'self.generate_xml_id(rec, "stock_picking_")',
                'move_line.move_id.purchase_line_id.so_origins',
                'move_line.return_lots',
                'move_line.move_id.purchase_line_id.supplier_ref',
            ]
        elif self.type == 'wms_export_stock_picking_preparation_chm' or self.type == 'wms_export_stock_picking_preparation_tlr' or self.type == 'wms_export_stock_picking_intersite_tlr' or self.type == 'wms_export_stock_picking_intersite_chm':
            header = 'name;partner_id/id;date_expected;so_note;note;partner_id;partner_id/street;partner_id/zip;partner_id/city;partner_id/country_id/code;picking_contact_id;contact_mobile;contact_email;move_lines/id;move_lines/product_id/id;move_lines/product_id/default_code;move_lines/product_uom_qty;sale_id/analytic_imputation;product_type;origin;user_id;date;partner_id/ref;id;client_order_ref;partner_id/street2;'
            fields = [
                'rec.display_name',
                'self.generate_xml_id(rec.partner_id, "res_partner_")',
                'rec.scheduled_date.date() if rec.scheduled_date else ""',
                'rec.dropship_note',
                'rec.note',
                'rec.partner_id.display_name',
                'rec.partner_id.street',
                'rec.partner_id.zip',
                'rec.partner_id.city',
                'rec.partner_id.country_id.code',
                'rec.picking_contact_id.name',
                'rec.contact_mobile',
                'rec.contact_mail',
                'self.generate_xml_id(move_line, "stock_move_line_")',
                'self.generate_xml_id(move_line.product_id, "product_product_")',
                'move_line.product_id.default_code',
                'move_line.product_uom_qty',
                'rec.sale_id.analytic_imputation',
                'rec.sale_id.type.name',
                'rec.origin',
                'rec.user_id.name',
                'rec.sale_id.date_order.date() if rec.sale_id.date_order else ""',
                'rec.partner_id.ref',
                'self.generate_xml_id(rec, "stock_picking_")',
                'rec.sale_id.client_order_ref',
                'rec.partner_id.street2',
            ]
        elif self.type == 'wms_export_product_product_tlr' or self.type == 'wms_export_product_product_chm':
            header = 'default_code;id;art_eanu;art_eanc;art_eanp;name;standard_price;weight;art_longu;art_laru;art_hauu;art_clas;tracking;description_picking;description_pickingout;art_qtec;art_qtep;art_stat;art_code;class_code;packing_code;ICPE_code;native_country_id/code;customs_code;'
            fields = [
                'default_code',
                'xml_id',
                'art_eanu',
                'art_eanc',
                'art_eanp',
                'variant_display_name',
                'standard_price',
                'weight',
                'art_lonu',
                'art_laru',
                'art_hauu',
                'art_clas',
                'tracking',
                'description_picking',
                'description_pickingout',
                'art_qtec',
                'art_qtep',
                'art_stat',
                'art_code',
                'class_code',
                'packing_code',
                'ICPE_code',
                'native_country_code',
                'customs_code'
            ]
        elif self.type == 'wms_export_mrp_production_chm' or self.type == 'wms_export_mrp_production_tlr':
            header = 'id;name;product_id/id;product_id/default_code;origin;product_qty;ove_raw_ids/id;Move_raw_ids/product_id/id;Move_raw_ids/product_id/default_code;Move_raw_ids/reserved_availability;'
            fields = [
                'self.generate_xml_id(rec, "mrp_production_")',
                'rec.name',
                'self.generate_xml_id(rec.product_id, "product_product_")',
                'rec.product_id.default_code',
                'rec.origin',
                'rec.product_qty',
                'self.generate_xml_id(move, "stock_move_")',
                'self.generate_xml_id(move.product_id, "product_product_")',
                'move.product_id.default_code',
                'move.reserved_availability'
            ]
        elif self.type == 'wms_export_product_image_chm':
            header = '"default_code";qty_available_chilly;'
            fields = [
                'default_code',
                'qty_available_chilly'
            ]
        elif self.type == 'wms_export_product_image_tlr':
            header = '"default_code";qty_available_tourville;'
            fields = [
                'default_code',
                'qty_available_tourville'
            ]

        return header, fields

    def _create_data(self, header, fields, records, mode, xml_ids_dic, all_products):
        row_data = ''

        if mode == 'production':
            for rec in records:
                for move in rec.move_raw_ids:
                    for field in fields:
                        value = str(eval(field))
                        if value.lower() == 'false':
                            row_data += ';'
                        else:
                            row_data += value + ';'
                    row_data += '\n'

        if mode == 'reception' or mode == 'preparation':
            for rec in records:
                for move_line in rec.move_line_ids_without_package:
                    for field in fields:
                        value = str(eval(field))
                        if field == 'rec.partner_id.name' and value.lower() == 'false':
                            value = str(rec.partner_id.parent_id.name)
                        if (field == 'rec.dropship_note' or field == 'rec.note' or field == 'move_line.return_lots') and value.lower() != 'false':
                            value = '"' + value + '"'
                        if value.lower() == 'false':
                            row_data += ';'
                        else:
                            row_data += value + ';'
                    row_data += '\n'

        if mode == 'partner':
            for rec in records:
                for field in fields:
                    value = str(eval(field))
                    if value.lower() == 'false':
                        row_data += ';'
                    else:
                        row_data += value + ';'
                row_data += '\n'

        if mode == 'product':
            for rec in all_products:
                for field in fields:
                    if field == 'xml_id':
                        value = self.generate_xml_id_product(str(rec.get('id')), 'product_product_', xml_ids_dic)
                    else:
                        value = str(rec.get(field))
                    if value.lower() == 'false':
                        row_data += ';'
                    else:
                        row_data += value + ';'
                row_data += '\n'

        if mode == 'image':
            for rec in all_products:
                for field in fields:
                    if field == 'default_code':
                        value = '"' + str(rec.get(field)) + '"'
                    else:
                        value = str(rec.get(field))
                    if value.lower() == 'false':
                        row_data += ';'
                    else:
                        row_data += value + ';'
                row_data += '\n'

        return header + '\n' + row_data


    def _get_content(self, records):

        if self.type == 'wms_export_res_partner_chm':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'partner', {}, False)
            return data

        elif self.type == 'wms_export_res_partner_tlr':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'partner', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_reception_chm':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'reception', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_reception_tlr':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'reception', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_preparation_chm':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'preparation', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_preparation_tlr':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'preparation', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_intersite_chm':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'preparation', {}, False)
            return data

        elif self.type == 'wms_export_stock_picking_intersite_tlr':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'preparation', {}, False)
            return data

        elif self.type == 'wms_export_product_product_tlr':
            xml_ids_dic = self.get_all_xml_ids()
            all_products = self.get_all_data()
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'product', xml_ids_dic, all_products)
            return data

        elif self.type == 'wms_export_product_product_chm':
            xml_ids_dic = self.get_all_xml_ids()
            all_products = self.get_all_data()
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'product', xml_ids_dic, all_products)
            return data

        elif self.type == 'wms_export_mrp_production_chm':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'production', {}, False)
            return data

        elif self.type == 'wms_export_mrp_production_tlr':
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'production', {}, False)
            return data

        elif self.type == 'wms_export_product_image_chm' or self.type == 'wms_export_product_image_tlr':
            all_products = self.get_all_data()
            header, fields = self._get_data()
            data = self._create_data(header, fields, records, 'image', {}, all_products)
            return data

        else:
            return super()._get_record_to_send()

    def _postprocess(self, send_result, filename, content, records):
        for rec in records:
            if rec._name == 'product.product' and 'ISTK' not in filename:
                rec.wms_exported = True
            if rec._name == 'stock.picking':
                rec.wms_exported = True
                rec.export_filename = filename
        return


