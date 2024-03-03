from odoo import http
from odoo.http import request
import os
import mimetypes

class CloudStorageController(http.Controller):
    @http.route(['/cloud/storage', '/cloud/storage/<path:extra>'], auth='user', website=True)
    def list_files(self, extra=''):
        base_path = '/mnt/cloud'
        path = os.path.join(base_path, extra)
        if not os.path.exists(path) or not os.path.isdir(path):
            return request.not_found()
        
        files_dirs = [{'name': f, 'is_dir': os.path.isdir(os.path.join(path, f))} for f in os.listdir(path)]
        
        return request.render('copier_company.cloud_storage_template', {
            'files_dirs': files_dirs,
            'current_path': extra,
        })
    
    # Aquí puedes agregar métodos adicionales para subir y descargar archivos

