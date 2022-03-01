# -*- coding: utf-8 -*-

from odoo import fields, models


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def _default_users_ids(self):
        # for each partner, determine corresponding portal.wizard.user records
        partner_ids = self.env.context.get('active_ids', [])
        contact_ids = set()
        user_changes = []
        for partner in self.env['res.partner'].sudo().browse(partner_ids):
            contact_partners = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
            for contact in contact_partners:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    in_portal = True
                    if contact.user_ids:
                        in_portal = self.env.ref('base.group_portal') in contact.user_ids[0].groups_id
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'in_portal': in_portal,
                    }))
        return user_changes

    user_ids = fields.One2many('portal.wizard.user', 'wizard_id', string='Users',default=_default_users_ids)
