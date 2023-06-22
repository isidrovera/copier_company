from odoo import http
from odoo.http import request
class DescargasArchivos(http.Controller):
    
    @http.route('/descargas/archivos', auth='public', website=True)
    def index(self, **kw):
        archivos = request.env['descarga.archivos'].sudo().search([])
        descargas_count = request.env['descarga.archivos'].sudo().search_count([])
        return http.request.render('copier_company.archivos_template', {'archivos': archivos, 'descargas_count': descargas_count})
