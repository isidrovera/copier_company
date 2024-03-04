from odoo import http
from odoo.http import request
import os
import mimetypes
from werkzeug.utils import redirect

class CloudStorageController(http.Controller):
    @staticmethod
    def search_files(base_path, search_query):
        """Método estático para buscar archivos que coincidan con el query de búsqueda en todos los subdirectorios."""
        matches = []
        for root, dirnames, filenames in os.walk(base_path):
            for filename in filenames:
                if search_query.lower() in filename.lower():
                    # Asegurar que la ruta relativa sea segura y solo dentro del directorio permitido
                    rel_path = os.path.relpath(os.path.join(root, filename), base_path)
                    matches.append(rel_path)
        return matches

    @http.route(['/cloud/storage', '/cloud/storage/<path:extra>'], auth='user', website=True)
    def list_files(self, extra=''):
        base_path = '/mnt/cloud'
        path = os.path.normpath(os.path.join(base_path, extra))
        
        # Prevenir la salida del directorio base
        if not path.startswith(base_path):
            return request.not_found()

        if not os.path.exists(path) or not os.path.isdir(path):
            return request.not_found()
        
        files_dirs = [{
            'name': f,
            'is_dir': os.path.isdir(os.path.join(path, f)),
            'path': os.path.join(extra, f)  # Asegúrate de que esta línea esté presente
        } for f in sorted(os.listdir(path))]  # Asegúrate de que 'sorted' esté presente para mantener el orden en la lista
        
        return request.render('copier_company.cloud_storage_template', {
            'files_dirs': files_dirs,
            'current_path': extra,
        })




    @http.route(['/cloud/storage/search'], type='http', auth='user', website=True)
    def search(self, query=''):
        """Método para buscar archivos por el query proporcionado."""
        base_path = '/mnt/cloud'
        search_results = self.search_files(base_path, query)
        return request.render('copier_company.cloud_storage_search_template', {
            'search_results': search_results,
            'query': query,
        })

    @http.route('/cloud/storage/download/<path:filename>', auth='user')
    def download_file(self, filename):
        """Método para descargar el archivo especificado."""
        base_path = '/mnt/cloud'
        file_path = os.path.normpath(os.path.join(base_path, filename))
        
        # Prevenir la descarga fuera del directorio base
        if not file_path.startswith(base_path):
            return request.not_found()

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return request.make_response(file_content, [
                ('Content-Type', mimetypes.guess_type(file_path)[0] or 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file_path))
            ])
        return request.not_found()


