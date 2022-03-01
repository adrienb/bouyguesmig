# -*- coding: utf-8 -*-
import json
# import lasso

from odoo import api, fields, models


class Provider(models.Model):
    '''
    Configuration values of a SAML2 provider
    '''
    _name = 'bycn_saml.provider'
    _description = 'SAML2 provider'
    _order = 'sequence, name'

    # Name of the OAuth2 entity, authentic, xcg...
    name = fields.Char(
        string='Provider name',
        help='This description will be displayed on the login page',
        required=True,
        translate=True,
        index=True
    )
    idp_metadata = fields.Text(
        string='IDP Configuration',
        help='Configuration for this Identity Provider',
    )
    sp_metadata = fields.Text(
        string='SP Configuration',
        help='Configuration for the Service Provider (this Odoo instance)',
    )
    sp_pkey = fields.Text(
        string='SP private key',
        help='Private key for the Service Provider (this Odoo instance)',
    )
    matching_attribute = fields.Char(
        default='subject.nameId',
        help='This attribute will be used for lookup in SAML response',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    sequence = fields.Integer(
        index=True
    )
    button_css_class = fields.Char(
        string='Button CSS class',
        help='CSS class that serves you to style the login button.',
        default='btn btn-primary btn-block p-0'
    )
    link_css_class = fields.Char(
        string='Link CSS class',
        help='CSS class that serves you to style the link inside the login button.',
        default='btn btn-link text-white col-12'
    )
    body = fields.Char()

    # ----------------------------------------------------------------------------------------------------
    # 1- ORM Methods (create, write, unlink)
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 2- Constraints methods (_check_***)
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 3- Compute methods (namely _compute_***)
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 4- Onchange methods (namely onchange_***)
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 5- Actions methods (namely action_***)
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 6- Crons
    # ----------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    # 7- Technical methods (name must reflect the use)
    # ----------------------------------------------------------------------------------------------------

    def _get_lasso_for_provider(self):
        '''
        internal helper to get a configured lasso.Login object for the
        given provider id
        '''
        # TODO: we should cache those results somewhere because it is
        # really costly to always recreate a login variable from buffers
        # server = lasso.Server.newFromBuffers(
        #     self.sp_metadata,
        #     self.sp_pkey
        # )
        # server.addProviderFromBuffer(
        #     lasso.PROVIDER_ROLE_IDP,
        #     self.idp_metadata
        # )
        # return lasso.Login(server)
        return True

    def _get_auth_request(self, state):
        '''build an authentication request and give it back to our client
        '''
        self.ensure_one()

        login = self._get_lasso_for_provider()

        # This part MUST be performed on each call and cannot be cached
        login.initAuthnRequest()
        login.request.nameIdPolicy.format = None
        login.request.nameIdPolicy.allowCreate = True
        login.msgRelayState = json.dumps(state)
        login.buildAuthnRequestMsg()

        # msgUrl is a fully encoded url ready for redirect use
        # obtained after the buildAuthnRequestMsg() call
        return login.msgUrl
