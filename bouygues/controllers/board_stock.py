# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree as ElementTree

from odoo.http import Controller, route, request


class BoardStock(Controller):

    @route('/board_stock/add_to_dashboard_stock', type='json', auth='user')
    def add_to_dashboard_stock(self, action_id, context_to_save, domain, view_mode, name=''):
        # Retrieve the 'My Dashboard' action from its xmlid
        action = request.env.ref('bouygues.open_board_stock_my_dash_action')

        if action and action['res_model'] == 'board.stock' and action['views'][0][1] == 'form' and action_id:
            # Maybe should check the content instead of model board.board ?
            view_id = action['views'][0][0]
            board = request.env['board.stock'].fields_view_get(view_id, 'form')
            if board and 'arch' in board:
                xml = ElementTree.fromstring(board['arch'])
                column = xml.find('./board/column')
                if column is not None:
                    new_action = ElementTree.Element('action', {
                        'name': str(action_id),
                        'string': name,
                        'view_mode': view_mode,
                        'context': str(context_to_save),
                        'domain': str(domain)
                    })
                    column.insert(0, new_action)
                    arch = ElementTree.tostring(xml, encoding='unicode')
                    request.env['ir.ui.view.custom'].create({
                        'user_id': request.session.uid,
                        'ref_id': view_id,
                        'arch': arch,
                        'board_stock': True
                    })
                    return True

        return False
