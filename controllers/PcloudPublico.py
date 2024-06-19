from odoo import http
from odoo.http import request
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class PdfViewerController(http.Controller):

    @http.route('/pdf/viewer', type='http', auth='public')
    def pdf_viewer(self, file_id):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return "pCloud configuration not found."

        try:
            file_id = int(file_id)
            download_url = config.download_pcloud_file(file_id)
            if download_url:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                pdf_content = response.content
                headers = [
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'inline; filename="document.pdf"')
                ]
                return request.make_response(pdf_content, headers)
        except Exception as e:
            _logger.error('Failed to retrieve PDF: %s', str(e))
            return "Failed to retrieve PDF."

    @http.route('/pdf/files', type='http', auth='public', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return request.render('copier_company.no_config_template')

        try:
            contents = config.list_pcloud_contents(folder_id=int(folder_id))
            processed_contents = [
                {
                    'name': item.get('name', 'Unknown'),
                    'isfolder': item.get('isfolder', False),
                    'id': item.get('folderid') if item.get('isfolder') else item.get('fileid'),
                    'modified': self._format_date(item.get('modified', 'Unknown')),
                    'size': self._format_size(item.get('size', 0)) if not item.get('isfolder') else '',
                }
                for item in contents
            ]
        except Exception as e:
            _logger.error('Failed to list contents: %s', str(e))
            processed_contents = []

        return request.render('copier_company.pcloud_files_template', {
            'contents': processed_contents,
            'current_folder_id': int(folder_id),
            'search': search
        })

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
