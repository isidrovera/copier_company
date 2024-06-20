from odoo import http
from odoo.http import request
import logging
import datetime
_logger = logging.getLogger(__name__)

class PdfViewerController(http.Controller):

    @http.route('/pdf/viewer', type='http', auth='public', website=True)
    def pdf_viewer(self, file_id):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            _logger.error("pCloud configuration not found.")
            return "pCloud configuration not found."

        try:
            file_id = int(file_id)
            download_info = config.get_pcloud_file_info(file_id)
            if not download_info:
                _logger.error("Failed to get download information for file_id %s", file_id)
                return "Failed to get download information."

            download_url = download_info['hosts'][0] + download_info['path']
            if not download_url.startswith('http://') and not download_url.startswith('https://'):
                download_url = 'https://' + download_url

            _logger.info("Download URL: %s", download_url)
            return request.render('copier_company.pdf_view_template', {
                'pdf_url': download_url
            })
        except Exception as e:
            _logger.error('Failed to retrieve PDF: %s', str(e))
            return "Failed to retrieve PDF."

    @http.route('/pdf/files', type='http', auth='public', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            _logger.error("pCloud configuration not found.")
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

        return request.render('copier_company.pcloud_pdf_template', {
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
