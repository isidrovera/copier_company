from odoo import http
from odoo.http import request
from odoo import http
from odoo.http import request

class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True, auth='user')
    def descarga_archivos(self, page=0, limit=20, **kw):
        # Convertir los parámetros de la URL a enteros
        page = int(page) if page else 1
        limit = int(limit) if limit else 20
        offset = (page - 1) * limit

        partner = request.env.user.partner_id
        stage = request.env['sale.order'].sudo().search(
            [('subscription_state', '=', 'progress')], 
            limit=1
        )

        if stage:
            order = request.env['sale.order'].sudo().search(
                [('partner_id', '=', partner.id), ('stage_id', '=', stage.id)], 
                limit=1
            )

            if order:
                doc_count = request.env['descarga.archivos'].sudo().search_count([])
                pager = request.website.pager(
                    url="/descarga/archivos",
                    total=doc_count,
                    page=page,
                    step=limit
                )
                docs = request.env['descarga.archivos'].sudo().search([], limit=limit, offset=offset)
                return request.render(
                    'copier_company.client_portal_descarga_archivos', 
                    {
                        'docs': docs,
                        'pager': pager,
                    }
                )
        
        return request.render('copier_company.no_subscription_message')

    
class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
    def portal_alquiler_form(self, alquiler_id, **kwargs):
        alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})


