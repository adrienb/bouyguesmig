# -*- coding: utf-8 -*-

# from . import controllers
from . import models
# from . import reports
# from . import wizard

from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    base_group_id = env['ir.model.data'].search([
        ('name', '=', 'group_user'),
        ('module', '=', 'base')
    ])

    bouygues_base_group_id = env['res.groups'].create({
        'name': 'Base Group',
        'implied_ids': [(6, 0, [base_group_id.res_id])],
    })
    env['ir.model.data'].create({
        'module': 'bouygues',
        'name': 'bouygues_base_group',
        'model': 'res.groups',
        'res_id': bouygues_base_group_id.id,
        'noupdate': False,
    })

    trade_sale_group_id = env['res.groups'].create({
        'name': 'Trade / Sales',
        'implied_ids': [(6, 0, [bouygues_base_group_id.id])],
    })
    env['ir.model.data'].create({
        'module': 'bouygues',
        'name': 'bouygues_trade_sales_group',
        'model': 'res.groups',
        'res_id': trade_sale_group_id.id,
        'noupdate': False,
    })

