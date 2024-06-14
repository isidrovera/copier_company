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
                    'id': item.get('folderid') if item.get('isfolder') else item.get('fileid')
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
