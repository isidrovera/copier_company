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


# En tu módulo personalizado, crea un archivo `controllers.py`




class MaquinasController(http.Controller):
    @http.route('/get_maquinas', auth='user', methods=['GET'], type='json')
    def get_maquinas(self, **kw):
        Maquinas = request.env['copier.company'].sudo()
        maquinas_records = Maquinas.search([])  # Aquí puedes añadir tu lógica de búsqueda o filtro
        maquinas_data = []
        for rec in maquinas_records:
            maquinas_data.append({
                'id': rec.id,
                'name': f"{rec.name.name} Serie: {rec.serie_id}"
            })
        return maquinas_data
