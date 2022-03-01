# -*- coding: utf-8 -*-

from odoo import api, models


class SetValuesBouygues(models.AbstractModel):
    _name = 'set.values.bouygues'
    _description = 'Set values for Bouygues'

    @api.model
    def _set_xml_ids_update_false(self):
        records = self.env['ir.model.data'].search([
            '|',
                '|',
                    '&',
                        '&',
                            ('module', '=', 'stock'),
                            ('model', '=', 'ir.ui.menu'),
                            ('name', 'in', [
                                'menu_warehouse_report',
                                'menu_stock_config_settings',
                                'menu_warehouse_config',
                                'menu_reordering_rules_config',
                            ]),
                    '&',
                        ('module', '=', 'portal'),
                        ('name', 'in', [
                            'mail_template_data_portal_welcome',
                        ]),
                '&',
                    ('module', '=', 'purchase'),
                    ('name', 'in', [
                        'email_template_edi_purchase',
                        'email_template_edi_purchase_done',
                    ]),
        ])
        for record in records:
            record.noupdate = False
