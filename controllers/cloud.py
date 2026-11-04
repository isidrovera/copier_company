
# -*- coding: utf-8 -*-

"""
COPIER COMPANY - Portal de descargas pCloud
Odoo 19

Portal de clientes:
- Autenticación con usuario Odoo
- Validación mediante has_license
- Navegación por carpetas
- Búsqueda recursiva en tiempo real
- Descarga individual de archivos
- Vista previa de archivos compatibles
- Breadcrumbs
- Interfaz compatible con PcloudDescargas.js

No permite descargar carpetas completas.
"""

import logging
import mimetypes
import re

from datetime import datetime
from urllib.parse import quote

import requests

from odoo import http
from odoo.http import request

from werkzeug.wrappers import Response
from werkzeug.http import parse_options_header


_logger = logging.getLogger(__name__)


# Carpetas raíz permitidas en el controlador original.
ALLOWED_ROOT_FOLDERS = (
    "Konica Minolta",
    "Ricoh",
)

# Máximo de niveles para búsquedas recursivas.
MAX_SEARCH_DEPTH = 20

# Límite de carpetas examinadas por búsqueda.
MAX_SEARCH_FOLDERS = 300

# Extensiones admitidas para vista previa.
PREVIEW_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".txt": "text/plain",
    ".log": "text/plain",
    ".csv": "text/plain",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
}


class PCloudController(http.Controller):
    """
    Callback OAuth existente.
    """

    @http.route(
        "/auth/callback",
        type="http",
        auth="public",
        csrf=False,
    )
    def pcloud_callback(self, **kwargs):

        code = kwargs.get("code")

        if not code:
            return request.make_response(
                "No se recibió el código de autorización.",
                status=400,
            )

        config = request.env["pcloud.config"].search(
            [],
            limit=1,
        )

        if not config:
            return request.make_response(
                "pCloud configuration not found.",
                status=404,
            )

        try:
            config.get_access_token(code)

            return request.render(
                "copier_company.pcloud_success",
                {},
            )

        except Exception:
            _logger.exception(
                "Error en callback de pCloud."
            )

            return request.render(
                "copier_company.pcloud_error",
                {
                    "error": (
                        "No se pudo completar la autorización "
                        "de pCloud."
                    )
                },
            )


class PcloudController(http.Controller):

    # ======================================================
    # VALIDACIONES GENERALES
    # ======================================================

    def _has_license(self):
        """
        Usa exactamente el campo existente.
        """

        partner = request.env.user.partner_id

        return bool(partner.has_license)

    def _get_config(self):
        """
        Configuración pCloud existente.
        """

        return request.env["pcloud.config"].search(
            [],
            limit=1,
        )

    def _parse_id(self, value):
        """
        Evita errores cuando folder_id llega vacío.
        """

        try:
            result = int(value or 0)

            if result < 0:
                return None

            return result

        except (ValueError, TypeError):
            return None

    def _get_allowed_roots(self, config):
        """
        Devuelve las carpetas raíz autorizadas.
        """

        contents = config.list_pcloud_contents(
            folder_id=0
        )

        roots = []

        for item in contents:

            if not item.get("isfolder"):
                continue

            if item.get("name") not in ALLOWED_ROOT_FOLDERS:
                continue

            roots.append(item)

        return roots

    def _get_folder_path(self, config, folder_id):
        """
        Utiliza get_folder_path() existente en
        el modelo pcloud.config.
        """

        if folder_id == 0:
            return []

        return config.get_folder_path(folder_id)

    def _folder_allowed(self, config, folder_id):
        """
        Comprueba que la carpeta pertenezca a una
        raíz permitida.

        No basta con comprobar únicamente el nombre
        de una subcarpeta.
        """

        if folder_id == 0:
            return True

        path = self._get_folder_path(
            config,
            folder_id,
        )

        if not path:
            return False

        roots = self._get_allowed_roots(config)

        root_ids = {
            int(item["folderid"])
            for item in roots
            if item.get("folderid") is not None
        }

        first_folder = path[0]

        return (
            self._parse_id(first_folder.get("id"))
            in root_ids
        )

    def _get_file_metadata(self, config, file_id):
        """
        Consulta metadatos reales mediante la API
        stat de pCloud.
        """

        url = (
            config._get_api_url()
            + "/stat"
        )

        response = requests.get(
            url,
            params={
                "access_token": config.access_token,
                "fileid": file_id,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("result") != 0:
            return None

        metadata = data.get("metadata") or {}

        if metadata.get("isfolder"):
            return None

        return metadata

    def _file_allowed(self, config, file_id):
        """
        Valida el archivo antes de descargar o
        mostrar una vista previa.
        """

        metadata = self._get_file_metadata(
            config,
            file_id,
        )

        if not metadata:
            return None

        parent_id = self._parse_id(
            metadata.get("parentfolderid")
        )

        if parent_id is None:
            return None

        if not self._folder_allowed(
            config,
            parent_id,
        ):
            return None

        return metadata

    # ======================================================
    # FORMATO DE ARCHIVOS
    # ======================================================

    def _format_size(self, size):

        try:
            size = float(size or 0)
        except (ValueError, TypeError):
            size = 0

        for unit in (
            "B",
            "KB",
            "MB",
            "GB",
            "TB",
        ):

            if size < 1024.0:
                return f"{size:.2f} {unit}"

            size /= 1024.0

        return f"{size:.2f} PB"

    def _format_date(self, date_str):

        if not date_str:
            return ""

        date_formats = (
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        )

        for fmt in date_formats:

            try:
                parsed = datetime.strptime(
                    str(date_str),
                    fmt,
                )

                return parsed.strftime(
                    "%d %b %Y, %H:%M"
                )

            except (ValueError, TypeError):
                continue

        return str(date_str)

    def _get_file_type(self, file_name):

        ext = str(file_name).rsplit(
            ".",
            1,
        )[-1].lower()

        icons = {
            "doc": "icons8-ms-word-48.png",
            "docx": "icons8-ms-word-48.png",
            "xls": "icons8-microsoft-excel-2019-48.png",
            "xlsx": "icons8-microsoft-excel-2019-48.png",
            "xlsm": "icons8-microsoft-excel-2019-48.png",
            "ppt": "icons8-powerpoint-48.png",
            "pptx": "icons8-powerpoint-48.png",
            "pdf": "icons8-pdf-48.png",
            "txt": "icons8-edit-text-file-48.png",
            "log": "icons8-edit-text-file-48.png",
            "csv": "icons8-file-48.png",
            "jpg": "icons8-image-48.png",
            "jpeg": "icons8-image-48.png",
            "png": "icons8-image-48.png",
            "gif": "icons8-image-48.png",
            "webp": "icons8-image-48.png",
            "zip": "icons8-zip-48.png",
            "rar": "icons8-winrar-48.png",
            "tar": "icons8-tar-100.png",
            "exe": "icons8-ex-40.png",
            "pjl": "icons8-idioma-48.png",
            "djf": "icons8-documento-48.png",
        }

        return icons.get(
            ext,
            "icons8-file-48.png",
        )

    def _process_item(self, item):
        """
        Formato utilizado por QWeb y JavaScript.
        """

        is_folder = bool(
            item.get("isfolder", False)
        )

        item_id = (
            item.get("folderid")
            if is_folder
            else item.get("fileid")
        )

        name = item.get(
            "name",
            "Unknown",
        )

        return {
            "name": name,
            "isfolder": is_folder,
            "id": item_id,
            "modified": self._format_date(
                item.get("modified")
            ),
            "size": (
                ""
                if is_folder
                else self._format_size(
                    item.get("size", 0)
                )
            ),
            "icon": (
                "icons8-carpeta-48.png"
                if is_folder
                else self._get_file_type(name)
            ),
        }

    # ======================================================
    # BÚSQUEDA RECURSIVA
    # ======================================================

    def _search_files_recursive(
        self,
        config,
        search_term,
        folder_id=0,
    ):
        """
        Busca dentro de las carpetas autorizadas.

        No accede recursivamente a carpetas raíz
        no autorizadas.
        """

        search_term = str(
            search_term or ""
        ).strip().casefold()

        if not search_term:
            return []

        results = []

        visited = set()

        queue = []

        if folder_id == 0:

            roots = self._get_allowed_roots(
                config
            )

            for root in roots:

                root_id = self._parse_id(
                    root.get("folderid")
                )

                if root_id is None:
                    continue

                if search_term in str(
                    root.get("name", "")
                ).casefold():

                    results.append(root)

                queue.append(
                    (root_id, 1)
                )

        else:

            if not self._folder_allowed(
                config,
                folder_id,
            ):
                return []

            queue.append(
                (folder_id, 0)
            )

        while queue:

            current_id, depth = queue.pop(0)

            if current_id in visited:
                continue

            if len(visited) >= MAX_SEARCH_FOLDERS:
                _logger.warning(
                    "Búsqueda pCloud alcanzó el límite "
                    "de %s carpetas.",
                    MAX_SEARCH_FOLDERS,
                )
                break

            visited.add(current_id)

            contents = config.list_pcloud_contents(
                folder_id=current_id
            )

            for item in contents:

                name = str(
                    item.get("name", "")
                )

                if search_term in name.casefold():
                    results.append(item)

                if (
                    item.get("isfolder")
                    and depth < MAX_SEARCH_DEPTH
                ):

                    child_id = self._parse_id(
                        item.get("folderid")
                    )

                    if (
                        child_id is not None
                        and child_id not in visited
                    ):
                        queue.append(
                            (child_id, depth + 1)
                        )

        return results

    # ======================================================
    # PORTAL DE DESCARGAS
    # ======================================================

    @http.route(
        "/soporte/descargas",
        type="http",
        auth="user",
        website=True,
    )
    def list_files(
        self,
        folder_id=0,
        search="",
        **kwargs,
    ):

        if not self._has_license():

            return request.render(
                "copier_company.no_subscription_message"
            )

        folder_id = self._parse_id(
            folder_id
        )

        if folder_id is None:
            folder_id = 0

        search = str(
            search or ""
        ).strip()

        config = self._get_config()

        if not config:

            return request.render(
                "copier_company.no_config_template"
            )

        contents = []

        folder_path = []

        try:

            if not self._folder_allowed(
                config,
                folder_id,
            ):
                return request.not_found()

            if search:

                contents = self._search_files_recursive(
                    config,
                    search,
                    folder_id,
                )

            elif folder_id == 0:

                contents = self._get_allowed_roots(
                    config
                )

            else:

                contents = config.list_pcloud_contents(
                    folder_id=folder_id
                )

            folder_path = self._get_folder_path(
                config,
                folder_id,
            )

        except Exception:

            _logger.exception(
                "Error al listar descargas pCloud."
            )

            contents = []

        processed_contents = [
            self._process_item(item)
            for item in contents
        ]

        processed_contents.sort(
            key=lambda item: (
                not item["isfolder"],
                item["name"].casefold(),
            )
        )

        return request.render(
            "copier_company.pcloud_files_template",
            {
                "contents": processed_contents,
                "current_folder_id": folder_id,
                "folder_path": folder_path,
                "search": search,

                # No existen todavía estadísticas
                # de descargas en el código recibido.
                "popular_files": [],
            },
        )

    # ======================================================
    # BÚSQUEDA EN TIEMPO REAL
    # ======================================================

    @http.route(
        "/soporte/descargas/buscar",
        type="http",
        auth="user",
        methods=["GET"],
        website=True,
    )
    def search_files(
        self,
        folder_id=0,
        search="",
        **kwargs,
    ):

        if not self._has_license():

            return request.make_json_response(
                {
                    "items": [],
                    "error": "Sin licencia activa",
                },
                status=403,
            )

        folder_id = self._parse_id(
            folder_id
        )

        if folder_id is None:

            return request.make_json_response(
                {
                    "items": [],
                    "error": "Carpeta inválida",
                },
                status=400,
            )

        search = str(
            search or ""
        ).strip()

        config = self._get_config()

        if not config:

            return request.make_json_response(
                {
                    "items": [],
                    "error": "Sin configuración pCloud",
                },
                status=503,
            )

        try:

            if not self._folder_allowed(
                config,
                folder_id,
            ):

                return request.make_json_response(
                    {
                        "items": [],
                        "error": "Acceso no permitido",
                    },
                    status=403,
                )

            if search:

                contents = self._search_files_recursive(
                    config,
                    search,
                    folder_id,
                )

            elif folder_id == 0:

                contents = self._get_allowed_roots(
                    config
                )

            else:

                contents = config.list_pcloud_contents(
                    folder_id=folder_id
                )

            items = [
                self._process_item(item)
                for item in contents
            ]

            items.sort(
                key=lambda item: (
                    not item["isfolder"],
                    item["name"].casefold(),
                )
            )

            return request.make_json_response(
                {
                    "items": items,
                    "count": len(items),
                }
            )

        except Exception:

            _logger.exception(
                "Error en búsqueda pCloud."
            )

            return request.make_json_response(
                {
                    "items": [],
                    "error": "Error al buscar archivos",
                },
                status=502,
            )

    # ======================================================
    # UTILIDADES DE TRANSMISIÓN
    # ======================================================

    def _get_safe_filename(self, filename):
        """
        Limpia caracteres de control para cabeceras.
        """

        filename = str(
            filename or "archivo"
        )

        filename = filename.replace(
            "\r",
            ""
        ).replace(
            "\n",
            ""
        )

        filename = filename.replace(
            "/",
            "_"
        ).replace(
            "\\",
            "_"
        )

        return filename

    def _content_disposition(
        self,
        filename,
        inline=False,
    ):

        filename = self._get_safe_filename(
            filename
        )

        disposition = (
            "inline"
            if inline
            else "attachment"
        )

        ascii_name = re.sub(
            r'[^\x20-\x7e]',
            "_",
            filename,
        ).replace(
            '"',
            "_"
        )

        return (
            f'{disposition}; filename="{ascii_name}"; '
            f"filename*=UTF-8''{quote(filename, safe='')}"
        )

    def _stream_file(
        self,
        config,
        file_id,
        metadata,
        inline=False,
        head_only=False,
    ):
        """
        Transmite archivos desde pCloud.

        No guarda el archivo en ir.attachment.
        """

        filename = self._get_safe_filename(
            metadata.get("name", "archivo")
        )

        extension = (
            "."
            + filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        if inline:

            content_type = PREVIEW_MIME_TYPES.get(
                extension
            )

            if not content_type:

                return request.make_response(
                    "Vista previa no disponible.",
                    status=415,
                )

        else:

            content_type = (
                mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

        headers = [
            ("Content-Type", content_type),
            (
                "Content-Disposition",
                self._content_disposition(
                    filename,
                    inline=inline,
                ),
            ),
            ("X-Content-Type-Options", "nosniff"),
            ("Cache-Control", "private, no-store"),
        ]

        if inline:
            headers.extend([
                (
                    "Content-Security-Policy",
                    "default-src 'none'; "
                    "style-src 'none'; "
                    "sandbox",
                ),
            ])

        if head_only:

            return Response(
                b"",
                headers=headers,
                status=200,
            )

        download_url = config.download_pcloud_file(
            file_id
        )

        if not download_url.startswith(
            ("https://", "http://")
        ):
            download_url = (
                "https://" + download_url
            )

        upstream = requests.get(
            download_url,
            stream=True,
            timeout=(10, 300),
        )

        try:
            upstream.raise_for_status()

        except Exception:
            upstream.close()
            raise

        if upstream.headers.get("Content-Length"):
            headers.append(
                (
                    "Content-Length",
                    upstream.headers["Content-Length"],
                )
            )

        def generate():

            try:

                for chunk in upstream.iter_content(
                    chunk_size=65536
                ):

                    if chunk:
                        yield chunk

            finally:
                upstream.close()

        return Response(
            generate(),
            headers=headers,
            direct_passthrough=True,
        )

    # ======================================================
    # DESCARGA INDIVIDUAL
    # ======================================================

    @http.route(
        "/soporte/descarga",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def download_file(
        self,
        file_id=None,
        **kwargs,
    ):

        if not self._has_license():

            return request.redirect(
                "/soporte/descargas"
            )

        file_id = self._parse_id(
            file_id
        )

        if file_id is None:

            return request.make_response(
                "Archivo inválido.",
                status=400,
            )

        config = self._get_config()

        if not config:
            return request.not_found()

        try:

            metadata = self._file_allowed(
                config,
                file_id,
            )

            if not metadata:

                return request.not_found()

            response = self._stream_file(
                config,
                file_id,
                metadata,
                inline=False,
            )

            _logger.info(
                "Descarga iniciada: file_id=%s usuario=%s",
                file_id,
                request.env.user.id,
            )

            return response

        except requests.exceptions.Timeout:

            _logger.warning(
                "Timeout descargando file_id=%s",
                file_id,
            )

            return request.redirect(
                "/soporte/descargas?error=timeout"
            )

        except requests.exceptions.RequestException:

            _logger.exception(
                "Error de conexión descargando file_id=%s",
                file_id,
            )

            return request.redirect(
                "/soporte/descargas?error=download_failed"
            )

        except Exception:

            _logger.exception(
                "Error descargando file_id=%s",
                file_id,
            )

            return request.redirect(
                "/soporte/descargas?error=unexpected"
            )

    # ======================================================
    # VISTA PREVIA
    # ======================================================

    @http.route(
        "/soporte/vista-previa",
        type="http",
        auth="user",
        methods=["GET", "HEAD"],
    )
    def preview_file(
        self,
        file_id=None,
        **kwargs,
    ):

        if not self._has_license():

            return request.make_response(
                "Acceso no permitido.",
                status=403,
            )

        file_id = self._parse_id(
            file_id
        )

        if file_id is None:

            return request.make_response(
                "Archivo inválido.",
                status=400,
            )

        config = self._get_config()

        if not config:
            return request.not_found()

        try:

            metadata = self._file_allowed(
                config,
                file_id,
            )

            if not metadata:
                return request.not_found()

            filename = metadata.get(
                "name",
                "",
            ).lower()

            extension = (
                "." + filename.rsplit(".", 1)[-1]
                if "." in filename
                else ""
            )

            if extension not in PREVIEW_MIME_TYPES:

                return request.make_response(
                    "Formato sin vista previa.",
                    status=415,
                )

            head_only = (
                request.httprequest.method == "HEAD"
            )

            return self._stream_file(
                config,
                file_id,
                metadata,
                inline=True,
                head_only=head_only,
            )

        except requests.exceptions.RequestException:

            _logger.exception(
                "Error de conexión en vista previa."
            )

            return request.make_response(
                "No se pudo obtener el archivo.",
                status=502,
            )

        except Exception:

            _logger.exception(
                "Error en vista previa file_id=%s",
                file_id,
            )

            return request.make_response(
                "Vista previa no disponible.",
                status=500,
            )
