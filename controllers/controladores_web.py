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
            },
            'team_members': [
                {
                    'name': 'Carlos Mendoza',
                    'position': 'CEO & Fundador',
                    'experience': '15 años en tecnología',
                    'image': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80'
                },
                {
                    'name': 'Ana Rodriguez',
                    'position': 'Directora Técnica',
                    'experience': '12 años en soporte',
                    'image': 'https://images.unsplash.com/photo-1494790108755-2616b612b786?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80'
                },
                {
                    'name': 'Luis Vargas',
                    'position': 'Jefe de Ventas',
                    'experience': '10 años en ventas B2B',
                    'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80'
                }
            ],
            'certifications': [
                {
                    'name': 'Konica Minolta Partner',
                    'level': 'Authorized Dealer',
                    'year': '2010'
                },
                {
                    'name': 'Canon Business Partner',
                    'level': 'Certified Reseller',
                    'year': '2012'
                },
                {
                    'name': 'Ricoh Elite Partner',
                    'level': 'Gold Level',
                    'year': '2015'
                }
            ]
        }
        
        return http.request.render('copier_company.copier_about_us_modern', values)