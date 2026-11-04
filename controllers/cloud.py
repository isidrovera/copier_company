# -*- coding: utf-8 -*-
"""Portal pCloud para clientes de Copier Company / Odoo 19."""
import logging
import mimetypes
import re
from collections import deque
from datetime import datetime
from urllib.parse import quote

import requests
from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)
ALLOWED_ROOT_FOLDERS = ('Konica Minolta', 'Ricoh')  # Valores comprobados del controlador original.
PREVIEW_TYPES = {
    'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp',
    'txt': 'text/plain; charset=utf-8', 'log': 'text/plain; charset=utf-8',
    'csv': 'text/plain; charset=utf-8', 'mp4': 'video/mp4',
    'webm': 'video/webm', 'ogg': 'video/ogg',
}


class PCloudController(http.Controller):
    @http.route('/auth/callback', type='http', auth='public', csrf=False)
    def pcloud_callback(self, **kwargs):
        config = request.env['pcloud.config'].search([], limit=1)
        if not config:
            return 'pCloud configuration not found.'
        try:
            config.get_access_token(kwargs.get('code'))
            return request.render('copier_company.pcloud_success', {})
        except Exception as exc:
            _logger.exception('Fallo callback pCloud')
            return request.render('copier_company.pcloud_error', {'error': str(exc)})


class PcloudController(http.Controller):
    def _licensed(self):
        return bool(request.env.user.partner_id.has_license)

    def _config(self):
        return request.env['pcloud.config'].search([], limit=1)

    def _id(self, value):
        try:
            number = int(value or 0)
            return number if number >= 0 else None
        except (ValueError, TypeError):
            return None

    def _roots(self, config):
        return [item for item in config.list_pcloud_contents(0)
                if item.get('isfolder') and item.get('name') in ALLOWED_ROOT_FOLDERS]

    def _allowed_folder(self, config, folder_id, roots=None):
        if folder_id == 0:
            return True
        roots = self._roots(config) if roots is None else roots
        allowed_ids = {self._id(item.get('folderid')) for item in roots}
        path = config.get_folder_path(folder_id)
        # Fail closed if path is missing or truncated.
        return bool(path and self._id(path[0].get('id')) in allowed_ids
                      and self._id(path[-1].get('id')) == folder_id
                      and self._id(path[-1].get('parentfolderid')) is not None)

    def _stat(self, config, file_id):
        response = requests.get(config._get_api_url() + '/stat', params={
            'access_token': config.access_token, 'fileid': file_id}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('result') != 0:
            return None
        meta = data.get('metadata') or {}
        return meta if not meta.get('isfolder') else None

    def _authorized_file(self, config, file_id):
        meta = self._stat(config, file_id)
        if not meta:
            return None
        folder_id = self._id(meta.get('parentfolderid'))
        if folder_id is None or not self._allowed_folder(config, folder_id):
            return None
        return meta

    def _size(self, size):
        try: size = float(size or 0)
        except (TypeError, ValueError): size = 0
        for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} PB'

    def _date(self, value):
        if not value:
            return ''
        for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try: return datetime.strptime(str(value), fmt).strftime('%d %b %Y, %H:%M')
            except (TypeError, ValueError): pass
        return str(value)

    def _item(self, item, path=''):
        is_folder = bool(item.get('isfolder'))
        return {'id': item.get('folderid') if is_folder else item.get('fileid'),
                'name': item.get('name', ''), 'isfolder': is_folder,
                'modified': self._date(item.get('modified')),
                'size': '' if is_folder else self._size(item.get('size', 0)),
                'path': path}

    def _global_search(self, config, query, roots):
        """Search recursively over all authorized roots, no artificial depth cap.

        An API or network failure is propagated rather than presented as a complete search.
        """
        query = query.casefold()
        results, queue, visited = [], deque(), set()
        for root in roots:
            folder_id = self._id(root.get('folderid'))
            if folder_id is None:
                continue
            if query in root.get('name', '').casefold():
                results.append(self._item(root, 'Inicio'))
            queue.append((folder_id, root.get('name', '')))
        while queue:
            folder_id, path = queue.popleft()
            if folder_id in visited:
                continue
            visited.add(folder_id)
            for entry in config.list_pcloud_contents(folder_id):
                name = entry.get('name', '')
                if query in name.casefold():
                    results.append(self._item(entry, path))
                if entry.get('isfolder'):
                    child_id = self._id(entry.get('folderid'))
                    if child_id is not None and child_id not in visited:
                        queue.append((child_id, path + ' / ' + name))
        return results

    @http.route('/soporte/descargas', type='http', auth='user', website=True)
    def list_files(self, folder_id=0, search='', **kwargs):
        if not self._licensed():
            return request.render('copier_company.no_subscription_message')
        config = self._config()
        if not config:
            return request.render('copier_company.no_config_template')
        folder_id = self._id(folder_id)
        if folder_id is None:
            return request.not_found()
        try:
            roots = self._roots(config)
            if not self._allowed_folder(config, folder_id, roots):
                return request.not_found()
            path = config.get_folder_path(folder_id) if folder_id else []
            if search and str(search).strip():
                contents = self._global_search(config, str(search).strip(), roots)
            elif folder_id:
                contents = [self._item(i) for i in config.list_pcloud_contents(folder_id)]
            else:
                contents = [self._item(i) for i in roots]
            contents.sort(key=lambda v: (not v['isfolder'], v['name'].casefold()))
            return request.render('copier_company.pcloud_files_template', {
                'contents': contents, 'current_folder_id': folder_id,
                'folder_path': path, 'root_folders': [self._item(i) for i in roots],
            })
        except Exception:
            _logger.exception('Error listando archivos del portal')
            return request.make_response('No se pudo cargar la carpeta. Inténtalo nuevamente.', status=502)

    @http.route('/soporte/descargas/buscar', type='http', auth='user', methods=['GET'], website=True)
    def search_files(self, search='', **kwargs):
        if not self._licensed():
            return request.make_json_response({'error': 'Sin licencia'}, status=403)
        config = self._config()
        if not config:
            return request.make_json_response({'error': 'pCloud no configurado'}, status=503)
        query = str(search or '').strip()
        if not query:
            return request.make_json_response({'items': []})
        try:
            results = self._global_search(config, query, self._roots(config))
            results.sort(key=lambda v: (not v['isfolder'], v['name'].casefold()))
            return request.make_json_response({'items': results, 'count': len(results)})
        except Exception:
            _logger.exception('Error en búsqueda global pCloud')
            return request.make_json_response({'error': 'Búsqueda no completada'}, status=502)

    def _stream(self, config, file_id, meta, inline=False, head=False):
        name = str(meta.get('name') or 'archivo').replace('\r', '').replace('\n', '').replace('/', '_').replace('\\', '_')
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        if inline and ext not in PREVIEW_TYPES:
            return request.make_response('Vista previa no disponible.', status=415)
        content_type = PREVIEW_TYPES[ext] if inline else (mimetypes.guess_type(name)[0] or 'application/octet-stream')
        ascii_name = re.sub(r'[^\x20-\x7e]', '_', name).replace('"', '_')
        disposition = 'inline' if inline else 'attachment'
        headers = [('Content-Type', content_type),
                   ('Content-Disposition', f'{disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(name, safe="")}'),
                   ('X-Content-Type-Options', 'nosniff'), ('Cache-Control', 'private, no-store')]
        if inline:
            headers.append(('Content-Security-Policy', "default-src 'none'; sandbox"))
        if head:
            return Response(b'', headers=headers)
        url = config.download_pcloud_file(file_id)
        if not url.startswith(('https://', 'http://')):
            url = 'https://' + url
        upstream = requests.get(url, stream=True, timeout=(10, 300))
        try: upstream.raise_for_status()
        except Exception:
            upstream.close()
            raise
        if upstream.headers.get('Content-Length'):
            headers.append(('Content-Length', upstream.headers['Content-Length']))
        def chunks():
            try:
                for part in upstream.iter_content(chunk_size=65536):
                    if part:
                        yield part
            finally:
                upstream.close()
        return Response(chunks(), headers=headers, direct_passthrough=True)

    @http.route('/soporte/descarga', type='http', auth='user', methods=['GET'])
    def download_file(self, file_id=None, **kwargs):
        if not self._licensed():
            return request.redirect('/soporte/descargas')
        file_id = self._id(file_id)
        if file_id is None:
            return request.not_found()
        config = self._config()
        if not config:
            return request.not_found()
        try:
            meta = self._authorized_file(config, file_id)
            if not meta:
                return request.not_found()
            return self._stream(config, file_id, meta)
        except Exception:
            _logger.exception('Error descargando archivo %s', file_id)
            return request.make_response('Error al descargar el archivo.', status=502)

    @http.route('/soporte/vista-previa', type='http', auth='user', methods=['GET', 'HEAD'])
    def preview_file(self, file_id=None, **kwargs):
        if not self._licensed():
            return request.make_response('Sin licencia', status=403)
        file_id = self._id(file_id)
        if file_id is None:
            return request.not_found()
        config = self._config()
        if not config:
            return request.not_found()
        try:
            meta = self._authorized_file(config, file_id)
            if not meta:
                return request.not_found()
            return self._stream(config, file_id, meta, inline=True,
                                head=request.httprequest.method == 'HEAD')
        except Exception:
            _logger.exception('Error vista previa %s', file_id)
            return request.make_response('Vista previa no disponible', status=502)
