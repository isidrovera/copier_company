# controllers/main.py
from odoo import http

class CopierServices(http.Controller):
    
    @http.route('/our-services', type='http', auth='public', website=True)
    def services_page(self, **kwargs):
        return http.request.render('copier_company.copier_services_modern')