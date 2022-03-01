# -*- coding: utf-8 -*-

from odoo import fields, models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def write(self, vals):
        res = super(MailThread, self).write(vals)
        values_list = []
        odoobot = self.env.ref('base.partner_root')
        for rec in self:
            values_list.append({'author_id': odoobot.id,
                                'email_from': self.env.company.email,
                                'body': 'The record has been modified',
                                'message_type': 'notification',
                                'model': rec._name,
                                'partner_ids': [],
                                'record_name': False,
                                'res_id': rec.id,
                                'subject': False,
                                'subtype_id': 2,
                                'tracking_value_ids': [[0,
                                                        0,
                                                        {'field': rec.write_uid.id,
                                                         'field_desc': 'Modified by',
                                                         'field_type': 'selection',
                                                         'new_value_char': self.env.user.name,
                                                         'old_value_char': False,
                                                         'tracking_sequence': 100}],
                                                       ]})
        if len(values_list) > 0:
            self.env['mail.message'].create(values_list)
        return res
