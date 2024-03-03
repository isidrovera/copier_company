from odoo import http
from odoo.http import request
import os
import mimetypes
from werkzeug.utils import redirect

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
    
    @http.route('/cloud/storage/download/<path:filename>', auth='user')
    def download_file(self, filename):
        base_path = '/mnt/cloud'
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return request.make_response(file_content, [
                ('Content-Type', mimetypes.guess_type(file_path)[0] or 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file_path))
            ])
        return request.not_found()


