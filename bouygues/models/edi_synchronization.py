# -*- coding: utf-8 -*-

from odoo import http, models, fields, api
from datetime import datetime
import traceback


class EdiSynchronization(models.Model):
    _inherit = 'edi.synchronization'

    def _report_error(self, activity, exception=None, message=None):
        values = self.env.ref('bouygues.bouygues_mail_template_synchronization_problem').generate_email(self.id, fields=None)
        values['email_from'] = self.env.company.email
        values['email_to'] = 'L.PILON@bouygues-construction.com,C.FERRIES@bouygues-construction.com'
        mail = self.env['mail.mail'].create(values)
        mail.send()
        description = "Unkown Error"
        if exception:
            tb = traceback.format_exc()
            description = "%s\n\n%s" % (str(exception), str(tb))
        if message:
            description = message

        self.write({
            'state': 'fail',
            'error_ids' : [(0, 0, {
                'activity': activity,
                'description': description,
            })]
        })
        self.flush(fnames=['state', 'error_ids', 'content_type'], records=self)


