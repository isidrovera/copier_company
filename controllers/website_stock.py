# File: controllers/website_stock.py
from odoo import http
from odoo.http import request
import base64

class WebsiteStock(http.Controller):

    @http.route(['/stock-maquinas'], type='http', auth='user', website=True)
    def list_stock(self, **kwargs):
        machines = request.env['copier.stock'].sudo().search([
            ('state', '=', 'available')
        ])
        return request.render('copier_company.copier_list', {
            'machines': machines,
        })

    @http.route(['/stock-maquinas/<model("copier.stock"):machine>'], type='http', auth='user', website=True)
    def detail_stock(self, machine, **kwargs):
        return request.render('copier_company.copier_detail', {
            'machine': machine,
        })

    @http.route(['/stock-maquinas/<model("copier.stock"):machine>/reserve'], type='http', auth='user', methods=['POST'], website=True)
    def reserve_stock(self, machine, **post):
        file = post.get('payment_proof')
        if file:
            data = file.read()
            machine.sudo().write({
                'payment_proof': base64.b64encode(data),
            })
        machine.sudo().action_reserve()
        return request.redirect(f'/stock-maquinas/{machine.id}')