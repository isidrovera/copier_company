from odoo import http
from odoo.http import request

class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', website=True, auth='user')
    def descarga_archivos(self, page=0, **kw):
        partner = request.env.user.partner_id
        limit = 10  # Número de registros por página
        page = int(page) if page else 1
        offset = (page - 1) * limit

        subscriptions_in_progress = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')
        ])

        if subscriptions_in_progress:
            doc_count = request.env['descarga.archivos'].sudo().search_count([])
            docs = request.env['descarga.archivos'].sudo().search([], limit=limit, offset=offset)
            pager = request.website.pager(
                url="/descarga/archivos",
                total=doc_count,
                page=page,
                step=limit
            )
            return request.render('copier_company.Descargas', {'docs': docs, 'pager': pager})
        else:
            return request.render('copier_company.no_subscription_message')


    
#class PortalAlquilerController(http.Controller):
    
   # @http.route('/portal/alquiler/<int:alquiler_id>', auth='public', website=True)
   # def portal_alquiler_form(self, alquiler_id, **kwargs):
      #  alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
      #  return request.render('copier_company.portal_alquiler_form', {'alquiler': alquiler})