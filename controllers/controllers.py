from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, **kw):
        partner = request.env.user.partner_id
        
        # Filtra las órdenes de venta relacionadas con el cliente actual que tengan subscription_state = 3_progress.
        orders_with_subscription = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')
        ])
        
        # Comprueba si hay alguna orden de venta con subscription_state = 3_progress.
        if orders_with_subscription:
            # Si existe al menos una orden de venta, busca los documentos y muestra la página.
            docs = request.env['descarga.archivos'].search([])
            return request.render('copier_company.client_portal_descarga_archivos', {'docs': docs})
        
        # Si no hay órdenes de venta con subscription_state = 3_progress, muestra un mensaje.
        return request.render('copier_company.no_subscription_message')


    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


