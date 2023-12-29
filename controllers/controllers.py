from odoo import http
from odoo.http import request

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







    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


# En tu módulo personalizado, crea un archivo `controllers.py`





class HelpdeskFormController(http.Controller):
    @http.route('/helpdesk/get_series', auth="public", methods=['POST'], website=True)

    def get_series(self, **kw):
        # Obtener todas las series disponibles en el modelo 'copier.company'
        series = request.env['copier.company'].sudo().search_read([], ['name'])
        # Preparar la respuesta en formato JSON
        return [{'id': rec['id'], 'name': rec['name']} for rec in series]