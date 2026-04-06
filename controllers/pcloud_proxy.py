"""
controllers/pcloud_proxy.py
===========================
Proxy de streaming para archivos de pCloud.

Resuelve el problema de IP binding de getfilelink:
  - El browser llama a /pcloud/stream/<file_id>/<filename>
  - Odoo hace la petición a pCloud desde el servidor (IP del VPS)
  - Odoo hace streaming de los bytes al browser
  - El browser recibe el archivo directamente sin redirecciones externas

Para previsualizacion de imagenes y archivos pequeños esto es ideal.
Para archivos grandes (>50MB) se usa publink directamente.
"""

from odoo import http
from odoo.http import request, Response
import requests
import logging

_logger = logging.getLogger(__name__)

# Límite para streaming directo vs publink (bytes)
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
        """
        Proxy de streaming para archivos de pCloud.
        Hace el request a pCloud desde el servidor (sin IP binding para el browser)
        y sirve el contenido al browser.

        URL: /pcloud/stream/{file_id}/{filename}

        Headers pasados al browser:
          - Content-Type     (del archivo original)
          - Content-Length   (para progress bar)
          - Content-Disposition: inline (para que el browser lo muestre, no descargue)
          - Cache-Control: max-age=3600 (cacheo en browser por 1h)
        """
        try:
            config = request.env['pcloud.config'].sudo().search(
                [('access_token', '!=', False)], limit=1
            )
            if not config:
                return Response("No pCloud config", status=503)

            # 1. Obtener URL de descarga real desde el servidor (IP del VPS = OK)
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

            if data.get('result') != 0:
                _logger.error('[pCloud proxy] getfilelink failed: %s', data)
                return Response(f"pCloud error: {data.get('error')}", status=502)

            hosts = data.get('hosts', [])
            path  = data.get('path', '')
            if not hosts or not path:
                return Response("pCloud no devolvió URL", status=502)

            download_url = hosts[0] + path
            if not download_url.startswith('http'):
                download_url = 'https://' + download_url

            # 2. Hacer streaming desde pCloud al browser
            # stream=True para no cargar todo en memoria
            file_resp = requests.get(download_url, stream=True, timeout=30)

            if file_resp.status_code != 200:
                _logger.error('[pCloud proxy] download failed: %s', file_resp.status_code)
                return Response("Error al obtener archivo", status=502)

            content_type = file_resp.headers.get('Content-Type', 'application/octet-stream')

            # Leer contenido completo en memoria
            # (funciona para documentos/imágenes; para archivos >200MB considerar publink)
            content = file_resp.content

            # Inline para tipos previewables, attachment para el resto
            inline_types = ('image/', 'video/', 'audio/', 'application/pdf', 'text/')
            disposition = 'inline' if any(content_type.startswith(t) for t in inline_types) \
                          else f'attachment; filename="{filename}"'

            _logger.info('[pCloud proxy] Serving file_id=%s name=%s type=%s size=%d',
                         file_id, filename, content_type, len(content))

            return Response(
                content,
                status=200,
                headers={
                    'Content-Type':        content_type,
                    'Content-Disposition': f'{disposition}; filename="{filename}"',
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
        """
        Retorna metadatos del archivo y la URL de proxy para usarla en el frontend.
        Llamado via JSON-RPC desde el explorador OWL.
        """
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
                'file_id': file_id,
                'name': name,
                'size': size,
                'proxy_url': f'/pcloud/stream/{file_id}/{name}',
                'use_proxy': size < STREAM_SIZE_LIMIT,
            }

        except Exception as e:
            _logger.exception('[pCloud proxy] Error getting info for file %s: %s', file_id, e)
            return {'error': str(e)}