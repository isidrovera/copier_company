from odoo import http
import requests
from odoo.http import request
import logging
from datetime import datetime
from werkzeug.wrappers import Response
import mimetypes

_logger = logging.getLogger(__name__)


class PCloudController(http.Controller):

    @http.route('/auth/callback', type='http', auth='public', csrf=False)
    def pcloud_callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')

        pcloud_config = request.env['pcloud.config'].search([], limit=1)
        if not pcloud_config:
            return "pCloud configuration not found."

        try:
            pcloud_config.get_access_token(code)
            return request.render('copier_company.pcloud_success', {})
        except Exception as e:
            return request.render('copier_company.pcloud_error', {'error': str(e)})
        

class PcloudController(http.Controller):
    @http.route('/soporte/descargas', type='http', auth='user', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        partner = request.env.user.partner_id
        if not partner.has_license:
            return request.render('copier_company.no_subscription_message')
    
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return request.render('copier_company.no_config_template')
    
        try:
            if search:
                contents = self._search_files_recursive(config, search, folder_id)
            else:
                contents = config.list_pcloud_contents(folder_id=int(folder_id))
            
            _logger.info('Contents: %s', contents)
            
            allowed_root_folders = [
                'Konica Minolta',
                'Ricoh',
                'Canon',
            ]
            
            current_folder_id = int(folder_id)
            filtered_contents = []
    
            if current_folder_id == 0:
                filtered_contents = [
                    item for item in contents 
                    if item.get('name', 'Unknown') in allowed_root_folders
                ]
            else:
                folder_path = config.get_folder_path(current_folder_id)
                
                if any(folder['name'] in allowed_root_folders for folder in folder_path):
                    filtered_contents = contents
                else:
                    _logger.info('Folder path not in allowed folders: %s', folder_path)
            
            processed_contents = [
                {
                    'name': item.get('name', 'Unknown'),
                    'isfolder': item.get('isfolder', False),
                    'id': item.get('folderid') if item.get('isfolder') else item.get('fileid'),
                    'modified': self._format_date(item.get('modified', 'Unknown')),
                    'size': self._format_size(item.get('size', 0)) if not item.get('isfolder') else '',
                    'icon': 'icons8-carpeta-48.png' if item.get('isfolder') else self._get_file_type(item.get('name', 'Unknown'))
                }
                for item in filtered_contents
            ]
    
            _logger.info('Processed Contents: %s', processed_contents)
            
        except Exception as e:
            _logger.error('Failed to list contents: %s', str(e))
            processed_contents = []
        
        return request.render('copier_company.pcloud_files_template', {
            'contents': processed_contents,
            'current_folder_id': int(folder_id),
            'search': search
        })

    def _search_files_recursive(self, config, search_term, folder_id=0):
        contents = config.list_pcloud_contents(folder_id=folder_id)
        matching_contents = []

        for item in contents:
            if search_term.lower() in item.get('name', '').lower():
                matching_contents.append(item)
            if item.get('isfolder'):
                matching_contents.extend(self._search_files_recursive(config, search_term, item.get('folderid')))
        
        return matching_contents

    def _get_file_type(self, file_name):
        ext = file_name.split('.')[-1].lower()
        icons = {
            'doc': 'icons8-ms-word-48.png',
            'docx': 'icons8-ms-word-48.png',
            'xls': 'icons8-microsoft-excel-2019-48.png',
            'xlsx': 'icons8-microsoft-excel-2019-48.png',
            'xlsm': 'icons8-microsoft-excel-2019-48.png',
            'ppt': 'icons8-powerpoint-48.png',
            'pptx': 'icons8-powerpoint-48.png',
            'pdf': 'icons8-pdf-48.png',
            'txt': 'icons8-text-48.png',
            'jpg': 'icons8-image-48.png',
            'jpeg': 'icons8-image-48.png',
            'png': 'icons8-image-48.png',
            'gif': 'icons8-image-48.png',
            'zip': 'icons8-zip-48.png',
            'rar': 'icons8-winrar-48.png',
            'tar': 'icons8-tar-100.png',
            'exe': 'icons8-ex-40.png',
            'pjl': 'icons8-idioma-48.png',
            'txt': 'icons8-edit-text-file-48.png',
            'djf': 'icons8-documento-48.png',
        }
        return icons.get(ext, 'icons8-file-48.png')

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _format_date(self, date_str):
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%d %b %Y, %H:%M')
            except ValueError:
                continue
        
        return date_str

    @http.route('/soporte/descarga', type='http', auth='user')
    def download_file(self, file_id, **kwargs):
        """
        Descarga un archivo mediante streaming directo desde pCloud.
        No almacena el archivo en memoria ni disco, sino que lo transmite directamente.
        Esto permite descargas concurrentes sin bloquear el servidor.
        """
        # Verificar licencia
        partner = request.env.user.partner_id
        if not partner.has_license:
            return request.redirect('/soporte/descargas')
        
        config = request.env['pcloud.config'].sudo().search([], limit=1)
        if not config or not file_id:
            return request.redirect('/soporte/descargas')
        
        try:
            file_id = int(file_id)
            
            # Obtener la URL de descarga de pCloud
            download_url = config.download_pcloud_file(file_id)
            
            if not download_url.startswith(('http://', 'https://')):
                download_url = 'https://' + download_url
            
            _logger.info('Starting streaming download from: %s', download_url)
            
            # Hacer una solicitud de streaming a pCloud
            # stream=True es crucial para no cargar todo en memoria
            pcloud_response = requests.get(
                download_url, 
                stream=True,
                timeout=(10, 300)  # 10 seg conexión, 300 seg lectura
            )
            pcloud_response.raise_for_status()
            
            # Obtener el nombre del archivo y tipo MIME
            file_name = download_url.split('/')[-1].split('?')[0]
            content_type = pcloud_response.headers.get('Content-Type', 'application/octet-stream')
            content_length = pcloud_response.headers.get('Content-Length', '')
            
            # Si no hay Content-Type, intentar detectarlo por extensión
            if content_type == 'application/octet-stream':
                guessed_type = mimetypes.guess_type(file_name)[0]
                if guessed_type:
                    content_type = guessed_type
            
            # Crear un generador para el streaming
            def generate():
                try:
                    # Leer en chunks de 64KB para balance entre memoria y rendimiento
                    for chunk in pcloud_response.iter_content(chunk_size=65536):
                        if chunk:
                            yield chunk
                except Exception as e:
                    _logger.error('Error during file streaming: %s', str(e))
                    raise
                finally:
                    pcloud_response.close()
            
            # Preparar headers para la descarga
            headers = [
                ('Content-Type', content_type),
                ('Content-Disposition', f'attachment; filename="{file_name}"'),
            ]
            
            # Agregar Content-Length si está disponible
            if content_length:
                headers.append(('Content-Length', content_length))
            
            # Crear respuesta con streaming
            response = Response(generate(), headers=headers, direct_passthrough=True)
            
            _logger.info('File streaming started for: %s (user: %s)', file_name, request.env.user.name)
            
            return response
            
        except requests.exceptions.Timeout:
            _logger.error('Timeout downloading file %s', file_id)
            return request.redirect('/soporte/descargas?error=timeout')
        except requests.exceptions.RequestException as e:
            _logger.error('Request error downloading file %s: %s', file_id, str(e))
            return request.redirect('/soporte/descargas?error=download_failed')
        except Exception as e:
            _logger.error('Unexpected error downloading file %s: %s', file_id, str(e))
            return request.redirect('/soporte/descargas?error=unexpected')