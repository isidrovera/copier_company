from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, **kw):
        partner = request.env.user.partner_id
        
        stage = request.env['sale.order.stage'].sudo().search([('category', '=', 'progress')], limit=1)
        if stage:
            order = request.env['sale.order'].sudo().search([('partner_id', '=', partner.id), ('stage_id', '=', stage.id)], limit=1)
            if order:
                docs = request.env['descarga.archivos'].search([])
                return request.render('copier_company.client_portal_descarga_archivos', {'docs': docs})
        
        return request.render('copier_company.no_subscription_message')

