from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, **kw):
        partner = request.env.user.partner_id
        
        # Obtén el valor del campo "subscription_count" en el modelo "res.partner".
        subscription_count = partner.subscription_count
        
        # Comprueba si el valor del campo "subscription_count" es mayor que cero.
        if subscription_count > 0:
            # Si el cliente tiene una suscripción en progreso, busca los documentos y muestra la página.
            docs = request.env['descarga.archivos'].search([])
            return request.render('copier_company.client_portal_descarga_archivos', {'docs': docs})
        
        # Si el valor del campo "subscription_count" es cero o menos, muestra un mensaje.
        return request.render('copier_company.no_subscription_message')


    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


