from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, **kw):
        partner = request.env.user.partner_id

        # Buscar suscripciones del partner que estén en el estado '3_progress'
        subscriptions_in_progress = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')  # Usando el valor del estado proporcionado
        ])

        # Comprobar si hay suscripciones en el estado '3_progress'
        if subscriptions_in_progress:
            # Si existe al menos una suscripción en progreso, buscar los documentos relacionados
            docs = request.env['descarga.archivos'].search([])
            return request.render('copier_company.Descargas', {'docs': docs})
        else:
            # Si no hay suscripciones en el estado '3_progress', mostrar un mensaje
            return request.render('copier_company.no_subscription_message')

    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


