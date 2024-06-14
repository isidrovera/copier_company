from odoo import http
import requests
from odoo.http import request
import os
import mimetypes
from werkzeug.utils import redirect
import logging

_logger = logging.getLogger(__name__)

class PcloudController(http.Controller):

    @http.route('/pcloud/files', type='http', auth='public', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return request.render('copier_company.no_config_template')
        
        try:
            if search:
                contents = self._search_files_recursive(config, search)
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
                    'size': self._format_size(item.get('size', 0)),
                    'modified': self._format_date(item.get('modified', '')),
                    'icon': self._get_icon(item.get('name', ''), item.get('isfolder', False))
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

    def _format_size(self, size):
        if size == 0:
            return '0.00 B'
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return f"{s} {size_name[i]}"

    def _format_date(self, date_str):
        try:
            date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date_str

    def _get_icon(self, name, isfolder):
        if isfolder:
            return 'icons8-carpet-48.png'
        ext = name.split('.')[-1].lower()
        icon_map = {
            'zip': 'icons8-zip-48.png',
            'rar': 'icons8-winrar-48.png',
            'pdf': 'icons8-pdf-48.png',
            'doc': 'icons8-ms-word-48.png',
            'docx': 'icons8-ms-word-48.png',
            'xls': 'icons8-microsoft-excel-2019-48.png',
            'xlsx': 'icons8-microsoft-excel-2019-48.png',
        }
        return icon_map.get(ext, 'icons8-file-48.png')

    @http.route('/pcloud/download', type='http', auth='public')
    def download_file(self, file_id, **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config or not file_id:
            return request.redirect('/pcloud/files')
        
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
            return request.redirect('/pcloud/files')
