from odoo import http
from odoo.http import request
import logging
import requests

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

    @http.route('/pdf/download', type='http', auth='public')
    def pdf_download(self, file_id):
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

            response = request.make_response(
                requests.get(download_url).content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'inline; filename="file.pdf"')
                ]
            )
            return response
        except Exception as e:
            _logger.error('Failed to retrieve PDF: %s', str(e))
            return "Failed to retrieve PDF."
