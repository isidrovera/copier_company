# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
import base64
import werkzeug

class ManualController(http.Controller):
    
    @http.route('/manuales', type='http', auth='public', website=True)
    def list_manuals(self):
        categories = request.env['secure_pdf_viewer.category'].sudo().search([])
        manuals = request.env['secure_pdf_viewer.manual'].sudo().search([('active', '=', True)])
        
        values = {
            'categories': categories,
            'manuals': manuals,
            'category': None
        }
        return request.render('secure_pdf_viewer.manuals_list', values)
    
    @http.route('/manuales/categoria/<int:category_id>', type='http', auth='public', website=True)
    def list_manuals_by_category(self, category_id):
        categories = request.env['secure_pdf_viewer.category'].sudo().search([])
        category = request.env['secure_pdf_viewer.category'].sudo().browse(category_id)
        
        if not category.exists():
            return werkzeug.utils.redirect('/manuales')
            
        manuals = request.env['secure_pdf_viewer.manual'].sudo().search([
            ('category_id', '=', category_id),
            ('active', '=', True)
        ])
        
        values = {
            'categories': categories,
            'manuals': manuals,
            'category': category
        }
        return request.render('secure_pdf_viewer.manuals_list', values)
    
    @http.route('/manuales/ver/<int:manual_id>', type='http', auth='public', website=True)
    def view_manual(self, manual_id):
        manual = request.env['secure_pdf_viewer.manual'].sudo().browse(manual_id)
        
        if not manual.exists() or not manual.active:
            return werkzeug.utils.redirect('/manuales')
        
        # Incrementar contador de accesos
        manual.increment_access_count()
        
        values = {
            'manual': manual,
        }
        return request.render('secure_pdf_viewer.manual_viewer', values)
    
    @http.route('/manuales/pdf/<int:manual_id>', type='http', auth='public', website=True)
    def get_pdf_content(self, manual_id):
        """
        Esta ruta proporciona el contenido del PDF, pero con encabezados especiales
        que evitan que el navegador lo descargue directamente.
        """
        manual = request.env['secure_pdf_viewer.manual'].sudo().browse(manual_id)
        
        if not manual.exists() or not manual.active:
            return werkzeug.utils.redirect('/manuales')
        
        pdf_content = base64.b64decode(manual.pdf_file)
        
        # Establecer encabezados para prevenir la descarga y la impresión
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            # Evitar que el navegador sugiera guardar el archivo
            ('Content-Disposition', 'inline'),
            # Configurar la política de seguridad para evitar la descarga
            ('X-Content-Type-Options', 'nosniff'),
            # Establecer encabezados de cache para evitar almacenamiento
            ('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'),
            ('Pragma', 'no-cache'),
            ('Expires', '0'),
        ]
        
        # Devolver el contenido PDF con los encabezados de seguridad
        return request.make_response(pdf_content, headers=headers)