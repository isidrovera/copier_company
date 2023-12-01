from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, **kw):
        partner = request.env.user.partner_id

        # Obtener la última orden de venta en línea a través del campo last_website_so_id
        last_order = partner.last_website_so_id

        # Comprueba si la última orden de venta tiene subscription_state = 3_progress.
        if last_order and last_order.subscription_state == '3_progress':
            # Si la última orden está en progreso, busca los documentos relacionados
            docs = request.env['descarga.archivos'].search([])
            return request.render('copier_company.client_portal_descarga_archivos', {'docs': docs})
        
        # Si no hay una última orden de venta con subscription_state = 3_progress, muestra un mensaje.
        return request.render('copier_company.no_subscription_message')



    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


