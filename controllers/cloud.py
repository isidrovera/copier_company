from odoo import http
import requests
from odoo.http import request
import os
import mimetypes
from werkzeug.utils import redirect
from datetime import datetime
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


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
    @http.route('/soporte/descargas', type='http', auth='user', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        # Verificar suscripciones activas como en DescargaArchivosController
        partner = request.env.user.partner_id
        subscriptions_in_progress = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')
        ])

        if not subscriptions_in_progress:
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
            
            exclusions = [
                '.cache', '.config', '.git', '.github', '.local',
                'Crypto Folder', 'System Volume Information', '.DS_Store', '.editorconfig', '.gitattributes',
                '.gitignore', '.last_revision', '.mailmap', '.npmignore', '.npmrc', '.parentlock', '.travis.yml',
                '.dockerignore','.pydio_id','.megaignore',''
            ]
            
            filtered_contents = [item for item in contents if item.get('name', 'Unknown') not in exclusions]
            
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
        # Intenta una lista de formatos de fecha hasta que uno funcione
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # Fri, 02 Feb 2024 14:26:10 +0000
            '%Y-%m-%d %H:%M:%S',         # 2024-02-02 14:26:10
            '%Y-%m-%dT%H:%M:%S',         # 2024-02-02T14:26:10
            # Añade más formatos según lo que esperes recibir
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%d %b %Y, %H:%M')
            except ValueError:
                continue
        
        return date_str

    @http.route('/soporte/descarga', type='http', auth='public')
    def download_file(self, file_id, **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config or not file_id:
            return request.redirect('/soporte/descargas')
        
        try:
            file_id = int(file_id)
            download_url = config.download_pcloud_file(file_id)
            
            if not download_url.startswith(('http://', 'https://')):
                download_url = 'https://' + download_url
            
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
            return request.redirect('/soporte/descargas')
