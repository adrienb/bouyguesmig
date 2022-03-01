# -*- coding: utf-8 -*-
import re
import logging
import passlib
import lasso

from odoo import api, fields, models, _, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError, AccessDenied


_logger = logging.getLogger(__name__)
BYCN_SAML_PROVIDER = 'bycn_saml.provider'
RES_USERS = 'res.users'


class ResUser(models.Model):
    '''
    Add SAML login capabilities to Odoo users.
    '''

    _inherit = RES_USERS

    saml_provider_id = fields.Many2one(
        comodel_name=BYCN_SAML_PROVIDER,
        help='Provider to use for given user',
        string='SAML Provider',
    )
    saml_uid = fields.Char(
        string='SAML User ID',
        help='SAML Provider user_id',
        copy=False
    )

    _sql_constraints = [
        (
            'uniq_users_saml_provider_saml_uid',
            'unique(saml_provider_id, saml_uid)',
            'SAML UID must be unique per provider'
        )
    ]

    # ----------------------------------------------------------------------------------------------------
    # 1- ORM Methods (create, write, unlink)
    # ----------------------------------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result._autoremove_password_if_saml()
        return result

    def write(self, vals):
        result = super().write(vals)
        self._autoremove_password_if_saml()
        return result

    # ----------------------------------------------------------------------------------------------------
    # 2- Constraints methods (_check_***)
    # ----------------------------------------------------------------------------------------------------
    @api.constrains('password', 'saml_uid')
    def _check_no_password_with_saml(self):
        '''
        Ensure no Odoo user posesses both an SAML user ID and an Odoo
        password. Except admin which is not constrained by this rule.
        '''
        if self._allow_saml_and_password():
            return
        # Super admin is the only user we allow to have a local password
        # in the database
        for record in self:
            if (
                not record.password or
                not record.saml_uid or
                record.id is SUPERUSER_ID
            ):
                continue
            raise ValidationError(
                _(
                    'This database disallows users to '
                    'have both passwords and SAML IDs. '
                    'Errors for login %s'
                ) % (
                    record.login
                )
            )

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
    def cron_sync_saml_data(self, ids=[], exclude=False, limit=False):
        SAML_PROVIDER = self.env[BYCN_SAML_PROVIDER].sudo()
        USER = self.sudo()

        # 1- Getting default SAML provider
        default_provider = SAML_PROVIDER.search([], limit=1)
        if not default_provider:
            raise ValidationError(
                'Please, set some default provider before going further'
            )

        # 2- Getting user missing saml_uid or saml_provider_id
        domain = [
            '|',
            ('saml_uid', '=', False),
            ('saml_provider_id', '=', False)
        ]
        if ids:
            operator = 'in' if not exclude else 'not in'
            domain = [('id', operator, ids)] + domain
        users = USER.search(domain, limit=limit)

        _logger.info(f'Starting execution of user synch for {users}')
        user_dict = self._get_user_email_dict(
            user_ids=users
        )
        treated_users = []
        for valid_email in user_dict:
            user = user_dict[valid_email]
            user_logins = ', '.join(user.mapped('login'))
            try:
                # 3. Check if any login or partner email is valid and are not duplicates.
                if not valid_email:
                    raise ValidationError(
                        f'These users do not have valid emails addresses: {user_logins}'
                    )
                elif len(user) > 1:
                    raise ValidationError(
                        f'The email address {valid_email} is used on multiple users: {user_logins}'
                    )

                # 4. Preparing to update saml_uid
                values = {
                    'saml_uid': valid_email
                }

                # 5. Update SAML provider if none is attached to the user.
                if not user.saml_provider_id:
                    values.update({
                        'saml_provider_id': default_provider.id
                    })

                # 6. Writting value to database.
                user.write(values)
                self.env.cr.commit()
                treated_users.append(user.login)
            except Exception as e:
                _logger.error(
                    f'Error when linking saml_uid of users {user} with logins {user_logins}.'
                )
                _logger.exception(e)
                self.env.cr.rollback()
        _logger.info(f'Completing CRON with treated users {treated_users}')

    # ----------------------------------------------------------------------------------------------------
    # 7- Technical methods (name must reflect the use)
    # ----------------------------------------------------------------------------------------------------
    def is_valid_email(self, email):
        """
        Summary
        ----------
        Check email validity
        Parameters
        ----------
        email : str
            Email value to check
        Returns
        -------
        bool : False if email address isn't valid
        """
        if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email) is not None:
            return True
        return False

    def _get_user_email_dict(self, user_ids):
        """
            Get recordset of users as a dict of email, recordset
            Users in dict with key False are user not having valid email
            Users in dict with more than one values are duplicate users
        """
        user_dict = {}
        for user_id in user_ids:
            try:
                user_email = user_id.partner_id.email if user_id.partner_id.email else 'no_email'
                emails = [user_id.login, user_email]
                valid_email = [e for e in emails if self.is_valid_email(e)]
                valid_email = valid_email[0] if valid_email else False
                user_dict.setdefault(valid_email, self.env[RES_USERS])
                user_dict[valid_email] += user_id
            except Exception as e:
                _logger.error(
                    f'Error occurred when dealing with user {user_id.login}: {e}'
                )
                _logger.exception(e)
        return user_dict

    def _get_after_login_url(self, redirect):
        return redirect or '/web'

    def auth_saml(self, provider, saml_response, redirect):
        validation = self._auth_saml_validate(
            provider_id=provider,
            token=saml_response
        )

        # required check
        if not validation.get('user_id'):
            raise AccessDenied()

        # retrieve and sign in user
        user = self._auth_saml_signin(
            provider=provider,
            validation=validation,
            saml_response=saml_response
        )

        if not user:
            raise AccessDenied()

        # return user credentials
        return self.env.cr.dbname, user.login, saml_response, user._get_after_login_url(
            redirect=redirect
        )

    def _autoremove_password_if_saml(self):
        '''
        Helper to remove password if it is forbidden for SAML users.
        '''
        if self._allow_saml_and_password():
            return
        to_remove_password = self.filtered(
            lambda rec: (
                rec.id != SUPERUSER_ID and
                rec.saml_uid and
                not (rec.password or rec.password_crypt)
            )
        )
        to_remove_password.write({
            'password': False,
            'password_crypt': False,
        })

    def _allow_saml_and_password(self):
        '''
        Know if both SAML and local password auth methods can coexist.
        '''
        return tools.str2bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'bycn_saml.allow_saml.uid_and_internal_password', 'True'
            )
        )

    def _get_name_ascii(self, attribute):
        try:
            return attribute.name
        except Exception:
            _logger.warning(
                'sso_after_response: error decoding attribute name %s',
                attribute.dump()
            )
        return False

    def _get_name_format_ascii(self, attribute):
        try:
            if not attribute.nameFormat:
                return False
            return attribute.nameFormat
        except Exception:
            message = 'sso_after_response: name or format of an \
                attribute failed to decode as ascii: %s'
            _logger.warning(
                message, attribute.dump(), exc_info=True
            )
        return False

    def _get_nickname(self, attribute):
        try:
            if not attribute.friendlyName:
                return False
            return attribute.friendlyName
        except Exception:
            message = 'sso_after_response: name or format of an \
                attribute failed to decode as ascii: %s'
            _logger.warning(
                message, attribute.dump(), exc_info=True
            )
        return False

    def _get_attribute_value(self, name, lformat, nickname, attribute):
        attrs = {}
        try:
            key = key = tuple(
                i for i in [name, lformat, nickname] if i
            )
            attrs[key] = list()
            for value in attribute.attributeValue:
                content = [a.exportToXml() for a in value.any]
                content = ''.join(content)
                attrs[key].append(content)
        except Exception:
            message = 'sso_after_response: value of an \
                attribute failed to decode as ascii: %s due to %s'
            _logger.warning(
                message, attribute.dump(), exc_info=True
            )
        return attrs

    def _auth_saml_signin(self, provider, validation, saml_response):
        ''' retrieve and sign into openerp the user corresponding to provider
        and validated access token

            :param provider: saml provider id (int)
            :param validation: result of validation of access token (dict)
            :param saml_response: saml parameters response from the IDP
            :return: user login (str)
            :raise: openerp.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        '''
        TOKEN_ENV = self.env['bycn_saml.token']
        saml_uid = validation['user_id']
        user = self.search([
            ('saml_uid', '=', saml_uid),
            ('saml_provider_id', '=', provider),
        ])
        if len(user) != 1:
            raise AccessDenied(
                'User %s not found' % (
                    saml_uid
                )
            )
        # now find if a token for this user/provider already exists
        token_ids = TOKEN_ENV.search([
            ('saml_provider_id', '=', provider),
            ('user_id', '=', user.id)
        ])
        if token_ids:
            token_ids.write({
                'saml_access_token': saml_response
            })
        else:
            TOKEN_ENV.create({
                'saml_access_token': saml_response,
                'saml_provider_id': provider,
                'user_id': user.id
            })
        return user

    def _auth_saml_validate(self, provider_id, token):
        '''
        return the validation data corresponding to the access token
        '''

        provider = self.env[BYCN_SAML_PROVIDER].browse(
            provider_id
        )

        # we are not yet logged in, so the userid cannot have access to the
        # fields we need yet
        login = provider.sudo()._get_lasso_for_provider()
        matching_attribute = provider.matching_attribute

        try:
            login.processAuthnResponseMsg(token)
        except (lasso.DsError, lasso.ProfileCannotVerifySignatureError) as e:
            _logger.exception(e)
            raise AccessDenied(_('Lasso Profile cannot verify signature'))
        except lasso.ProfileStatusNotSuccessError as e:
            _logger.exception(e)
            raise AccessDenied(_('Profile Status failure'))

        try:
            login.acceptSso()
        except lasso.Error as e:
            _logger.exception(e)
            raise AccessDenied(
                'Invalid assertion : %s' % lasso.strError(e[0])
            )

        attrs = {}
        for att_statement in login.assertion.attributeStatement:
            for attribute in att_statement.attribute:
                name = self._get_name_ascii(
                    attribute=attribute
                )
                lformat = self._get_name_format_ascii(
                    attribute=attribute
                )
                nickname = self._get_nickname(
                    attribute=attribute
                )
                attribute_attrs = self._get_attribute_value(
                    name=name,
                    lformat=lformat,
                    nickname=nickname,
                    attribute=attribute
                )
                attrs.update(attribute_attrs)

        matching_value = None
        for key in attrs:
            if (
                isinstance(key, tuple) and
                key[0] == matching_attribute
            ):
                matching_value = attrs[key][0]
                break

        default_matching_attribute = 'subject.nameId'
        if (
            not matching_value and
            matching_attribute == default_matching_attribute
        ):
            matching_value = login.assertion.subject.nameId.content
        elif (
            not matching_value and
            matching_attribute != default_matching_attribute
        ):
            raise AccessDenied(
                'Matching attribute %s not found in user attrs: %s' % (
                    matching_attribute, attrs
                )
            )
        return {'user_id': matching_value}

    def _check_credentials(self, token, env):
        '''Override to handle SAML auths.

        The token can be a password if the user has used the normal form...
        but we are more interested in the case when they are tokens
        and the interesting code is inside the 'except' clause.
        '''
        try:
            # Attempt a regular login (via other auth addons) first.
            super(ResUser, self)._check_credentials(token, env)
        except (AccessDenied, passlib.exc.PasswordSizeError):
            # since normal auth did not succeed we now try to find if the user
            # has an active token attached to his uid
            res = self.env['bycn_saml.token'].sudo().search([
                ('user_id', '=', self.env.user.id),
                ('saml_access_token', '=', token)
            ])
            if not res:
                raise AccessDenied()
