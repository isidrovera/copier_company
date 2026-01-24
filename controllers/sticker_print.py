from odoo import http
from odoo.http import request

class StickerPrintController(http.Controller):

    @http.route('/stickers/print', type='http', auth='user', website=False)
    def print_stickers(self, ids=None, **kwargs):
        if not ids:
            return "No se enviaron IDs"

        ids_list = [int(x) for x in ids.split(',') if x.isdigit()]
        records = request.env['copier.company'].browse(ids_list)

        return request.render(
            'copier_company.sticker_a7_web_template',
            {'docs': records}
        )
