# controllers/main.py
from odoo import http

class CopierServices(http.Controller):
    
    @http.route('/our-services', type='http', auth='public', website=True)
    def services_page(self, **kwargs):
        return http.request.render('copier_company.copier_services_modern')



class CopierAboutUs(http.Controller):
    
    @http.route('/about-us', type='http', auth='public', website=True)
    def about_us_page(self, **kwargs):
        # Datos para pasar al template
        values = {
            'company_stats': {
                'years_experience': 15,
                'clients_served': 500,
                'equipment_installed': 1200,
                'satisfaction_rate': 98
            }
        }
        
        return http.request.render('copier_company.copier_about_us_modern', values)