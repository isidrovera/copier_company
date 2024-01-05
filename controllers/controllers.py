from odoo import http
from odoo.http import request
import json


class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, page=1, search='', **kw):
        # Convertir 'page' a un entero
        try:
            page = int(page)
        except ValueError:
            page = 1  # En caso de error, reiniciar a la primera página

        partner = request.env.user.partner_id
        items_per_page = 20

        # Verificar suscripciones activas
        subscriptions_in_progress = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')
        ])

        if subscriptions_in_progress:
            domain = []
            if search:
                domain = ['|', '|',
                          ('name', 'ilike', '%' + search + '%'),
                          ('observacion', 'ilike', '%' + search + '%'),
                          ('modelo.name', 'ilike', '%' + search + '%')]
            
            # Si hay término de búsqueda, reiniciar la paginación a la primera página
            if search:
                page = 1
            
            total_docs = request.env['descarga.archivos'].sudo().search_count(domain)
            total_pages = ((total_docs - 1) // items_per_page) + 1
            page = max(min(page, total_pages), 1)
            offset = (page - 1) * items_per_page

            docs = request.env['descarga.archivos'].sudo().search(
                domain, offset=offset, limit=items_per_page
            )

            return request.render('copier_company.Descargas', {
                'docs': docs,
                'page': page,
                'total_pages': total_pages,
                'search': search
            })
        else:
            # Mostrar mensaje de suscripción expirada
            return request.render('copier_company.no_subscription_message')

    @http.route('/descarga/cloud', type='http', auth='user', website=True)
    def vista_nube(self, **kw):
        # Aquí simplemente renderizas una nueva plantilla que contendrá el iframe o la integración que prefieras
        return request.render('copier_company.Cloud', {})





class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler', auth='public', website=True)
    def portal_alquiler_form(self, **kwargs):
        marcas = request.env['marcas.maquinas'].sudo().search([])
        # Elimina la siguiente línea, ya que no estás utilizando 'alquiler_id'
        # alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {
            'marcas': marcas
        })

    @http.route('/portal/alquiler/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_alquiler_submit(self, **post):
        alquiler_vals = {
            'marca_id': int(post.get('marca_id')),
            'tipo': post.get('tipo'),
            'cantidad': post.get('cantidad'),
            'empresa': post.get('empresa'),
            'contacto': post.get('contacto'),
            'celular': post.get('celular'),
            'correo': post.get('correo'),
            'detalles': post.get('detalles'),
            'formato': post.get('formato'),
        }
        nuevo_alquiler = request.env['cotizacion.alquiler'].sudo().create(alquiler_vals)
        # Aquí, puedes redirigir al usuario a una página de confirmación o de vuelta al formulario con un mensaje de éxito
        return request.redirect('/ruta_de_confirmacion')
    @http.route('/ruta_de_confirmacion', auth='public', website=True)
    def confirmacion(self, **kwargs):
        return request.render('copier_company.confirmacion_template', {})





class HelpdeskTicketController(http.Controller):

    @http.route('/helpdesk/ticket/form', type='http', auth="public", website=True)
    def ticket_form(self, **kw):
        productos = request.env['copier.company'].sudo().search([])
        response = super(HelpdeskTicketController, self).ticket_form()
        response.qcontext.update({
            'productos': productos
        })
        return response
class CustomHelpdeskController(http.Controller):
    _inherit = 'helpdesk.ticket'

    @http.route()
    class HelpdeskControllerExtended(http.Controller):
        @http.route('/helpdesk/customer-care-1', type='http', auth="public", website=True)
        def helpdesk_form_extended(self, **kw):
            response = super(HelpdeskControllerExtended, self).helpdesk_form(**kw)
            products = request.env['copier.company'].sudo().search([])
            response.qcontext['products'] = products
            return response