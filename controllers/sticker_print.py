from odoo import http
from odoo.http import request


class StickerPrintController(http.Controller):

    @http.route('/stickers/print', type='http', auth='user', website=False)
    def print_stickers(self, ids=None, per_page='6', auto_print='1', **kwargs):
        if not ids:
            return request.not_found()

        ids_list = [
            int(x)
            for x in str(ids).split(',')
            if str(x).strip().isdigit()
        ]

        if not ids_list:
            return request.not_found()

        records = request.env['copier.company'].browse(ids_list).exists()

        if not records:
            return request.not_found()

        return request.render(
            'copier_company.sticker_a7_web_template',
            {
                'docs': records,
                'per_page': 6,
                'auto_print': auto_print == '1',
            }
        )