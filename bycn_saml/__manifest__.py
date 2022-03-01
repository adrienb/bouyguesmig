{
    'name': 'BYCN Saml2 Authentication',
    'version': '12.0.1',
    'summary': 'A library inspired by auth_saml OCA module for dealing with SAML & Single Sign-On',
    'author': 'BYCN IT, Bouygues-Construction Information Technologies',
    'category': 'Utils',
    'website': 'https://bouygues-construction.com',
    'depends': [
        'web_enterprise'
    ],
    'external_dependencies': {
        'python': ['lasso'],
    },
    # 'demo': [
    #     'demo/provider.xml',
    # ],
    'data': [
        'security/ir.model.access.csv',
        'data/provider.xml',
        'data/cron_sync_saml_data.xml',

        # 'views/saml_template.xml',
        # 'views/provider.xml',
        # 'views/res_users.xml',
        #
        # 'views/saml_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    # 'assets': {
    #     'web.assets_backend': [
    #         'bycn_saml/static/css/style.scss',
    #     ],
    # }
}
