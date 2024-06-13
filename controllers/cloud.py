from odoo import http
import requests
from odoo.http import request
import os
import mimetypes
from werkzeug.utils import redirect
import logging

_logger = logging.getLogger(__name__)

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
    def get_icon_class(self, filename):
        """Función para obtener la clase CSS del ícono basada en la extensión del archivo."""
        extension_to_icon = {
            '.pdf': 'fa-file-pdf-o',
            '.doc': 'fa-file-word-o',
            '.docx': 'fa-file-word-o',
            '.xls': 'fa-file-excel-o',
            '.xlsx': 'fa-file-excel-o',
            # Agrega más mapeos según sea necesario
        }
        extension = os.path.splitext(filename)[1].lower()
        return extension_to_icon.get(extension, 'fa-file-o')

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
            'get_icon_class': self.get_icon_class,
        })




    @http.route(['/cloud/storage/search'], type='http', auth='user', website=True)
    def search(self, query=''):
        """Método para buscar archivos por el query proporcionado."""
        base_path = '/mnt/cloud'
        search_results = self.search_files(base_path, query)
        return request.render('copier_company.cloud_storage_search_template', {
            'search_results': search_results,
            'query': query,
            'get_icon_class': self.get_icon_class,
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


class PCloudController(http.Controller):

    @http.route('/auth/callback', type='http', auth='public', csrf=False)
    def pcloud_callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')

        # Encuentra la configuración de pCloud en la base de datos
        pcloud_config = request.env['pcloud.config'].search([], limit=1)
        if not pcloud_config:
            return "pCloud configuration not found."

        # Intercambia el código de autorización por un token de acceso
        try:
            pcloud_config.get_access_token(code)
            return request.render('copier_company.pcloud_success', {})
        except Exception as e:
            return request.render('copier_company.pcloud_error', {'error': str(e)})
        
class PcloudController(http.Controller):

    @http.route('/pcloud/files', type='http', auth='public', website=True)
    def list_files(self, folder_id=0, **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return request.render('copier_company.no_config_template')
        
        try:
            contents = config.list_pcloud_contents(folder_id=int(folder_id))
            _logger.info('Contents: %s', contents)
            processed_contents = [
                {
                    'name': item.get('name', 'Unknown'),
                    'isfolder': item.get('isfolder', False),
                    'id': item.get('folderid') if item.get('isfolder') else item.get('fileid')
                }
                for item in contents
            ]
        except Exception as e:
            _logger.error('Failed to list contents: %s', str(e))
            processed_contents = []
        
        return request.render('copier_company.pcloud_files_template', {
            'contents': processed_contents,
            'current_folder_id': int(folder_id)
        })

    @http.route('/pcloud/download', type='http', auth='public')
    def download_file(self, file_id, **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config or not file_id:
            return request.redirect('/pcloud/files')
        
        try:
            file_id = int(file_id)
            download_url = config.download_pcloud_file(file_id)
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            file_name = download_url.split('/')[-1]
            headers = [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename={file_name}')
            ]
            return request.make_response(response.content, headers)
        except Exception as e:
            _logger.error('Failed to download file: %s', str(e))
            return request.redirect('/pcloud/files')