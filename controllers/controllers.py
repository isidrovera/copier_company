from odoo import http
from odoo.http import request
class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', auth='public', website=True)
    def descarga_archivos(self, **kw):
        docs = request.env['descarga.archivos'].search([])
        partner = request.env.user.partner_id
        if partner.subscription_count == 1:
            return request.render('copier_company.client_portal_descarga_archivos', {'docs': docs})
        else:
            message = "Lo siento, no tiene acceso a esta página porque no tiene una suscripción activa. ¡Pero no se preocupe! Puede comprar una suscripción en nuestra página de servicios."
            return request.redirect('/our-services', message=message)

