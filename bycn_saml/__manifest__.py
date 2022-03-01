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

    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
