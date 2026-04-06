from odoo import http
from odoo.http import request, Response
import requests
import logging

_logger = logging.getLogger(__name__)

STREAM_SIZE_LIMIT = 50 * 1024 * 1024  # 50 MB


class PCloudProxyController(http.Controller):

    @http.route(
        '/pcloud/stream/<int:file_id>/<string:filename>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def stream_file(self, file_id, filename, **kwargs):
        try:
            config = request.env['pcloud.config'].sudo().search(
                [('access_token', '!=', False)], limit=1
            )
            if not config:
                return Response("No pCloud config", status=503)

            api_url = config._get_api_url()
            resp = requests.get(
                f"{api_url}/getfilelink",
                params={
                    'access_token': config.access_token,
                    'fileid': file_id,
                },
                timeout=15,
            )
            data = resp.json()

            # ★ DIAGNÓSTICO — ver respuesta completa de pCloud
            _logger.info('[pCloud proxy] getfilelink raw: %s', data)

            if data.get('result') != 0:
                _logger.error('[pCloud proxy] getfilelink failed: %s', data)
                return Response(f"pCloud error: {data.get('error')}", status=502)

            hosts = data.get('hosts', [])
            path  = data.get('path', '')

            _logger.info('[pCloud proxy] hosts=%s path=%s', hosts, path)

            if not hosts or not path:
                return Response("pCloud no devolvió URL", status=502)

            # ★ FIX — construcción robusta de URL
            host = hosts[0]
            if not host.startswith('http'):
                host = 'https://' + host
            host = host.rstrip('/')
            path = path if path.startswith('/') else '/' + path
            download_url = host + path

            _logger.info('[pCloud proxy] download_url=%s', download_url)

            # Streaming desde pCloud
            file_resp = requests.get(download_url, stream=True, timeout=30)

            _logger.info('[pCloud proxy] file_resp status=%s headers=%s',
                         file_resp.status_code, dict(file_resp.headers))

            if file_resp.status_code != 200:
                _logger.error('[pCloud proxy] download failed: %s', file_resp.status_code)
                return Response("Error al obtener archivo", status=502)

            content_type = file_resp.headers.get('Content-Type', 'application/octet-stream')
            content = file_resp.content

            _logger.info('[pCloud proxy] content length=%d', len(content))

            # ★ FIX — Content-Disposition correcto
            inline_types = ('image/', 'video/', 'audio/', 'application/pdf', 'text/')
            if any(content_type.startswith(t) for t in inline_types):
                disposition_header = f'inline; filename="{filename}"'
            else:
                disposition_header = f'attachment; filename="{filename}"'

            _logger.info('[pCloud proxy] Serving file_id=%s name=%s type=%s size=%d',
                         file_id, filename, content_type, len(content))

            return Response(
                content,
                status=200,
                headers={
                    'Content-Type':        content_type,
                    'Content-Disposition': disposition_header,
                    'Content-Length':      str(len(content)),
                    'Cache-Control':       'max-age=3600, private',
                },
            )

        except Exception as e:
            _logger.exception('[pCloud proxy] Error streaming file %s: %s', file_id, e)
            return Response("Error interno", status=500)

    @http.route(
        '/pcloud/info/<int:file_id>',
        type='jsonrpc',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def get_file_info(self, file_id, **kwargs):
        try:
            config = request.env['pcloud.config'].sudo().search(
                [('access_token', '!=', False)], limit=1
            )
            if not config:
                return {'error': 'No pCloud config'}

            api_url = config._get_api_url()
            resp = requests.get(
                f"{api_url}/stat",
                params={
                    'access_token': config.access_token,
                    'fileid': file_id,
                },
                timeout=15,
            )
            data = resp.json()

            if data.get('result') != 0:
                return {'error': data.get('error', 'Error desconocido')}

            meta = data.get('metadata', {})
            size = meta.get('size', 0)
            name = meta.get('name', f'file_{file_id}')

            return {
                'file_id':   file_id,
                'name':      name,
                'size':      size,
                'proxy_url': f'/pcloud/stream/{file_id}/{name}',
                'use_proxy': size < STREAM_SIZE_LIMIT,
            }

        except Exception as e:
            _logger.exception('[pCloud proxy] Error getting info for file %s: %s', file_id, e)
            return {'error': str(e)}