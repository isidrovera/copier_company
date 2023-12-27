from odoo import http
from odoo.http import request

from odoo import http
from odoo.http import request

class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True)
    def descarga_archivos(self, page=1, search='', **kw):
        # Asegúrate de que 'page' sea un entero
        try:
            page = int(page)
        except ValueError:
            page = 1

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
                # Si hay un término de búsqueda, reiniciar la paginación a la primera página
                page = 1
                domain = ['|', '|',
                          ('name', 'ilike', '%' + search + '%'),
                          ('observacion', 'ilike', '%' + search + '%'),
                          ('modelo.name', 'ilike', '%' + search + '%')]
            
            # Obtener el número total de documentos
            total_docs = request.env['descarga.archivos'].sudo().search_count(domain)
            # Calcular el total de páginas
            total_pages = ((total_docs - 1) // items_per_page) + 1
            # Asegurarse de que el número de página esté dentro del rango
            page = max(min(page, total_pages), 1)
            # Calcular el desplazamiento
            offset = (page - 1) * items_per_page

            # Obtener los documentos para la página actual
            docs = request.env['descarga.archivos'].sudo().search(
                domain, offset=offset, limit=items_per_page
            )

            # Renderizar la vista con los documentos y la información de paginación
            return request.render('copier_company.Descargas', {
                'docs': docs,
                'page': page,
                'total_pages': total_pages,
                'search': search
            })
        else:
            # Mostrar mensaje si no hay suscripciones activas
            return request.render('copier_company.no_subscription_message')






    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


# En tu módulo personalizado, crea un archivo `controllers.py`




class MaquinasController(http.Controller):
    @http.route('/get_maquinas', auth='user', methods=['GET'], type='json')
    def get_maquinas(self, **kw):
        Maquinas = request.env['copier.company'].sudo()
        maquinas_records = Maquinas.search([])  # Aquí puedes añadir tu lógica de búsqueda o filtro
        maquinas_data = []
        for rec in maquinas_records:
            # Asegúrate de que 'name' es un campo Many2one que referencia a otro modelo que tiene un campo 'name'.
            maquina_name = rec.name.name if rec.name else ''
            serie_id = rec.serie_id or ''
            maquinas_data.append({
                'id': rec.id,
                'name': f"{maquina_name} Serie: {serie_id}"
            })
        return maquinas_data
