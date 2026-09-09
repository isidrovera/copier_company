# -*- coding: utf-8 -*-
# ====================================================================================
# models/printtracker_config.py
# Integración PrintTracker Pro - Copier Company
# Corregido según documentación oficial Print Tracker API 1.0.0
# ====================================================================================

from datetime import datetime, timezone
import logging
import time

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class PrintTrackerConfig(models.Model):
    _name = 'copier.printtracker.config'
    _description = 'Configuración API PrintTracker Pro - Copier Company'
    _rec_name = 'name'

    name = fields.Char(
        'Nombre de Configuración',
        required=True,
        default='PrintTracker Pro Config',
    )
    api_url = fields.Char(
        'URL Base API',
        required=True,
        default='https://papi.printtrackerpro.com/v1',
        help='URL base de la API de PrintTracker Pro',
    )
    api_key = fields.Char(
        'API Key',
        required=True,
        help='Token de autenticación para la API',
    )
    entity_bbbb_id = fields.Char(
        'ID Entidad Principal',
        required=True,
        help='ID de la entidad principal en PrintTracker',
    )

    connection_status = fields.Selection(
        [
            ('not_tested', 'No Probado'),
            ('connected', 'Conectado'),
            ('error', 'Error de Conexión'),
        ],
        string='Estado Conexión',
        default='not_tested',
        readonly=True,
    )
    last_error = fields.Text('Último Error', readonly=True)
    timeout_seconds = fields.Integer('Timeout (segundos)', default=30)
    max_retries = fields.Integer('Reintentos Máximos', default=3)
    retry_delay = fields.Integer('Delay entre Reintentos (seg)', default=5)

    def get_api_headers(self):
        self.ensure_one()
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _retry_api_call(self, func, *args, **kwargs):
        """Ejecuta una llamada HTTP con reintentos para errores de transporte."""
        self.ensure_one()
        max_retries = max(int(self.max_retries or 1), 1)
        retry_delay = max(int(self.retry_delay or 0), 0)

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException:
                if attempt >= max_retries - 1:
                    raise
                _logger.warning(
                    'PrintTracker: intento %s/%s falló. Reintentando en %ss...',
                    attempt + 1,
                    max_retries,
                    retry_delay,
                )
                if retry_delay:
                    time.sleep(retry_delay)

    def _get(self, path, params=None):
        """GET centralizado para la API de PrintTracker."""
        self.ensure_one()
        url = f'{self.api_url.rstrip("/")}/{path.lstrip("/")}'

        def _call():
            return requests.get(
                url,
                headers=self.get_api_headers(),
                params=params or {},
                timeout=self.timeout_seconds or 30,
            )

        response = self._retry_api_call(_call)
        return response

    def test_connection(self):
        self.ensure_one()
        try:
            _logger.info(
                'PrintTracker: probando conexión | url=%s | entity=%s',
                self.api_url,
                self.entity_bbbb_id,
            )

            response = self._get(f'entity/{self.entity_bbbb_id}')

            if response.status_code == 200:
                data = response.json() or {}
                entity_name = data.get('name', 'Sin nombre')
                self.write({
                    'connection_status': 'connected',
                    'last_error': False,
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'PrintTracker Pro',
                        'message': f'Conexión exitosa\nEntidad: {entity_name}',
                        'type': 'success',
                        'sticky': False,
                    },
                }

            error_msg = f'HTTP {response.status_code}: {response.text}'
            self.write({
                'connection_status': 'error',
                'last_error': error_msg,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PrintTracker Pro',
                    'message': f'Error de conexión: {error_msg}',
                    'type': 'danger',
                    'sticky': True,
                },
            }

        except Exception as exc:
            error_msg = str(exc)
            self.write({
                'connection_status': 'error',
                'last_error': error_msg,
            })
            _logger.exception('PrintTracker: error probando conexión')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PrintTracker Pro',
                    'message': f'Error: {error_msg}',
                    'type': 'danger',
                    'sticky': True,
                },
            }

    @api.model
    def get_active_config(self):
        config = self.search([], limit=1)
        if not config:
            raise UserError('No hay configuración de PrintTracker configurada.')
        if not config.api_key:
            raise UserError('La configuración de PrintTracker no tiene API Key.')
        if not config.entity_bbbb_id:
            raise UserError('La configuración de PrintTracker no tiene ID de entidad.')
        return config


# ====================================================================================
# Extensión de copier.company
# ====================================================================================

class CopierCompany(models.Model):
    _inherit = 'copier.company'

    pt_device_id = fields.Char(
        'ID PrintTracker Device',
        help='ID del dispositivo en PrintTracker. Este ID corresponde al deviceKey de los medidores.',
        index=True,
        tracking=True,
    )
    pt_entity_id = fields.Char(
        'ID Entidad PrintTracker',
        help='Entidad real a la que pertenece el dispositivo en PrintTracker.',
        index=True,
        tracking=True,
    )
    pt_last_sync = fields.Datetime(
        'Última Sincronización PT',
        readonly=True,
        tracking=True,
    )
    pt_mapped = fields.Boolean(
        'Mapeado con PrintTracker',
        compute='_compute_pt_mapped',
    )

    @api.depends('pt_device_id')
    def _compute_pt_mapped(self):
        for record in self:
            record.pt_mapped = bool(record.pt_device_id)

    def _normalize_pt_serial(self, value):
        """Normaliza solo espacios externos. No altera caracteres internos de la serie."""
        return (value or '').strip()

    def _find_printtracker_device(self, config):
        """Compatibilidad: usa la búsqueda corregida y selección más reciente."""
        return self._search_device_with_pagination(config)

    def action_map_printtracker(self):
        """Busca de nuevo la serie y actualiza el vínculo con PrintTracker."""
        self.ensure_one()

        if not self.serie_id:
            raise UserError('La máquina debe tener una serie para mapear con PrintTracker.')

        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            device_found = self._search_device_with_pagination(config)

            if not device_found:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': (
                            f'No se encontró dispositivo con serie "{self.serie_id}" '
                            'en PrintTracker.'
                        ),
                        'type': 'warning',
                    }
                }

            device_id = device_found.get('id')
            entity_key = device_found.get('entityKey')

            if not device_id:
                raise UserError(
                    f'PrintTracker encontró la serie {self.serie_id}, '
                    'pero no devolvió un ID de dispositivo.'
                )

            if not entity_key:
                _logger.warning(
                    "PrintTracker: dispositivo sin entityKey | serie=%s | device=%s",
                    self.serie_id,
                    device_found,
                )

            self.write({
                'pt_device_id': device_id,
                'pt_entity_id': entity_key or config.entity_bbbb_id,
                'pt_last_sync': fields.Datetime.now(),
            })

            last_meter_timestamp = device_found.get(
                '_odoo_latest_meter_timestamp'
            ) or 'Sin lectura disponible'

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': (
                        'Máquina mapeada exitosamente con PrintTracker\n'
                        f'Serie: {self.serie_id}\n'
                        f'Device ID: {device_id}\n'
                        f'Entity ID: {entity_key or config.entity_bbbb_id}\n'
                        f'Última lectura: {last_meter_timestamp}'
                    ),
                    'type': 'success',
                    'sticky': True,
                }
            }

        except Exception as e:
            _logger.exception("Error mapeando con PrintTracker")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }

    def _pt_timestamp_for_sort(self, value):
        """Convierte un timestamp de PrintTracker en un valor comparable."""
        self.ensure_one()

        if not value:
            return datetime.min.replace(tzinfo=timezone.utc)

        try:
            timestamp = str(value).strip()
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1] + '+00:00'

            parsed = datetime.fromisoformat(timestamp)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError):
            _logger.warning(
                'PrintTracker: timestamp de dispositivo no reconocido: %r',
                value,
            )
            return datetime.min.replace(tzinfo=timezone.utc)

    def _get_printtracker_device_latest_meter(self, config, device):
        """Obtiene la última lectura de un candidato sin modificar Odoo."""
        self.ensure_one()

        device_id = device.get('id')
        entity_id = device.get('entityKey') or config.entity_bbbb_id
        if not device_id or not entity_id:
            return None

        date_param = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        try:
            response = config._get(
                f'entity/{entity_id}/device/{device_id}/meter/mostRecentPriorTo',
                params={'date': date_param},
            )
        except requests.exceptions.RequestException:
            _logger.exception(
                'PrintTracker: error consultando última lectura del candidato %s',
                device_id,
            )
            return None

        if response.status_code != 200:
            _logger.warning(
                'PrintTracker: candidato sin lectura accesible | deviceId=%s | HTTP=%s',
                device_id,
                response.status_code,
            )
            return None

        data = response.json()
        if isinstance(data, list):
            return data[0] if data else None
        return data if isinstance(data, dict) else None

    def _select_best_printtracker_device(self, config, devices):
        """Elige la coincidencia cuya lectura tenga el timestamp más reciente."""
        self.ensure_one()

        unique_devices = []
        seen = set()
        for device in devices:
            device_id = device.get('id')
            if not device_id or device_id in seen:
                continue
            seen.add(device_id)
            unique_devices.append(device)

        if not unique_devices:
            return None

        ranked = []
        for position, device in enumerate(unique_devices):
            reading = self._get_printtracker_device_latest_meter(config, device)
            timestamp = (reading or {}).get('timestamp')
            ranked.append((
                self._pt_timestamp_for_sort(timestamp),
                -position,
                device,
                timestamp,
            ))

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        _, _, selected, timestamp = ranked[0]
        selected = dict(selected)
        selected['_odoo_latest_meter_timestamp'] = timestamp

        _logger.info(
            'PrintTracker: mejor coincidencia seleccionada | serie=%s | '
            'candidatos=%s | deviceId=%s | entityKey=%s | timestamp=%s',
            self.serie_id,
            len(unique_devices),
            selected.get('id'),
            selected.get('entityKey'),
            timestamp,
        )
        return selected

    def _search_device_with_pagination(self, config):
        """
        Busca todos los dispositivos que coincidan con la serie.

        Primero busca solo dispositivos habilitados. Si no existe ninguno,
        repite incluyendo deshabilitados. Cuando hay duplicados, elige el que
        tenga la lectura con timestamp más reciente.
        """
        self.ensure_one()
        serie_buscar = self._normalize_pt_serial(self.serie_id)

        if not serie_buscar:
            return None

        path = f'entity/{config.entity_bbbb_id}/device'
        serial_upper = serie_buscar.upper()

        def _matches(device):
            candidate = self._normalize_pt_serial(device.get('serialNumber'))
            return candidate.upper() == serial_upper

        for exclude_disabled in (True, False):
            candidates = []

            response = config._get(
                path,
                params={
                    'includeChildren': True,
                    'excludeDisabled': exclude_disabled,
                    'serialNumber': serie_buscar,
                    'limit': 100,
                    'page': 1,
                },
            )

            if response.status_code != 200:
                raise UserError(
                    f'Error HTTP {response.status_code} buscando la serie '
                    f'{serie_buscar} en PrintTracker: {response.text}'
                )

            direct_devices = response.json() or []
            if isinstance(direct_devices, list):
                candidates.extend(
                    device for device in direct_devices if _matches(device)
                )

            # Si el filtro remoto no encontró la serie, recorrer toda la flota.
            if not candidates:
                page = 1
                while True:
                    response = config._get(
                        path,
                        params={
                            'includeChildren': True,
                            'excludeDisabled': exclude_disabled,
                            'limit': 100,
                            'page': page,
                        },
                    )

                    if response.status_code != 200:
                        raise UserError(
                            f'Error HTTP {response.status_code} consultando '
                            f'dispositivos PrintTracker: {response.text}'
                        )

                    page_devices = response.json() or []
                    if not isinstance(page_devices, list) or not page_devices:
                        break

                    candidates.extend(
                        device for device in page_devices if _matches(device)
                    )

                    if len(page_devices) < 100:
                        break

                    page += 1
                    if page > 200:
                        _logger.warning(
                            'PrintTracker: límite de seguridad de paginación '
                            'alcanzado buscando %s',
                            serie_buscar,
                        )
                        break

            if candidates:
                _logger.info(
                    'PrintTracker: coincidencias de serie=%s | activos=%s | cantidad=%s',
                    serie_buscar,
                    exclude_disabled,
                    len(candidates),
                )
                return self._select_best_printtracker_device(config, candidates)

        return None

    def debug_list_printtracker_devices(self):
        """Muestra una muestra de dispositivos y deja detalle en logs."""
        self.ensure_one()
        config = self.env['copier.printtracker.config'].get_active_config()

        response = config._get(
            f'entity/{config.entity_bbbb_id}/device',
            params={
                'includeChildren': True,
                'excludeDisabled': False,
                'limit': 20,
                'page': 1,
            },
        )

        if response.status_code != 200:
            raise UserError(f'HTTP {response.status_code}: {response.text}')

        devices = response.json() or []
        lines = [f'Dispositivos recibidos: {len(devices)}', '']

        for i, device in enumerate(devices[:10], start=1):
            lines.append(
                f'{i}. Serie: {device.get("serialNumber") or "N/A"} | '
                f'ID: {device.get("id") or "N/A"} | '
                f'Entidad: {device.get("entityKey") or "N/A"}'
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug PrintTracker',
                'message': '\n'.join(lines),
                'type': 'info',
                'sticky': True,
            },
        }


# ====================================================================================
# Extensión de copier.counter
# ====================================================================================

class CopierCounter(models.Model):
    _inherit = 'copier.counter'

    pt_updated = fields.Boolean(
        'Actualizado desde PrintTracker',
        default=False,
        help='Indica si los contadores fueron actualizados desde PrintTracker.',
    )
    pt_last_reading_date = fields.Datetime(
        'Fecha Lectura PrintTracker',
        help='Fecha de la última lectura obtenida de PrintTracker.',
    )

    def action_update_from_printtracker(self):
        """Actualiza contadores desde PrintTracker y remapea si es necesario."""
        self.ensure_one()

        _logger.info("=" * 70)
        _logger.info("INICIANDO ACTUALIZACIÓN DESDE PRINTTRACKER")
        _logger.info(
            "Counter=%s | ID=%s | serie=%s | estado=%s",
            self.name,
            self.id,
            self.serie,
            self.state,
        )

        if self.state != 'draft':
            raise UserError(
                'Solo se pueden actualizar contadores en estado borrador.'
            )

        if not self.maquina_id:
            raise UserError('No hay máquina asociada al contador.')

        config = self.env['copier.printtracker.config'].get_active_config()

        try:
            # Si falta mapeo completo, remapear antes de consultar.
            if (
                not self.maquina_id.pt_device_id
                or not self.maquina_id.pt_entity_id
            ):
                _logger.info(
                    "PrintTracker: mapeo incompleto. Remapeando serie=%s...",
                    self.serie,
                )
                device = self.maquina_id._search_device_with_pagination(config)

                if not device:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': (
                                f'No se encontró la serie {self.serie} '
                                'en PrintTracker.'
                            ),
                            'type': 'warning',
                        }
                    }

                self.maquina_id.write({
                    'pt_device_id': device.get('id'),
                    'pt_entity_id': (
                        device.get('entityKey') or config.entity_bbbb_id
                    ),
                    'pt_last_sync': fields.Datetime.now(),
                })

            lectura_pt = self._obtener_ultima_lectura_printtracker_v2(config)

            # Si falla, volver a localizar dispositivo por serie y actualizar
            # tanto deviceId como entityKey antes de reintentar.
            if not lectura_pt:
                _logger.warning(
                    "PrintTracker: no se encontró lectura con mapeo actual. "
                    "Remapeando serie=%s...",
                    self.serie,
                )

                device = self.maquina_id._search_device_with_pagination(config)

                if device:
                    self.maquina_id.write({
                        'pt_device_id': device.get('id'),
                        'pt_entity_id': (
                            device.get('entityKey') or config.entity_bbbb_id
                        ),
                        'pt_last_sync': fields.Datetime.now(),
                    })

                    lectura_pt = (
                        self._obtener_ultima_lectura_printtracker_v2(config)
                    )

            if not lectura_pt:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': (
                            f'No se pudo obtener la lectura de PrintTracker '
                            f'para la serie {self.serie}. Revise el log.'
                        ),
                        'type': 'warning',
                    }
                }

            validacion = self._validar_nuevos_contadores_pt(lectura_pt)

            # Una lectura puede existir pero pertenecer a un vínculo antiguo.
            # Si los contadores retroceden, buscar de nuevo la serie y probar
            # otro dispositivo antes de devolver el error al usuario.
            if not validacion.get('valido'):
                old_device_id = self.maquina_id.pt_device_id
                old_entity_id = self.maquina_id.pt_entity_id
                device = self.maquina_id._search_device_with_pagination(config)

                new_device_id = (device or {}).get('id')
                new_entity_id = (
                    (device or {}).get('entityKey') or config.entity_bbbb_id
                )

                if (
                    new_device_id
                    and (
                        new_device_id != old_device_id
                        or new_entity_id != old_entity_id
                    )
                ):
                    _logger.warning(
                        'PrintTracker: lectura inválida con vínculo anterior; '
                        'remapeando serie=%s | deviceId=%s -> %s | entityId=%s -> %s',
                        self.serie,
                        old_device_id,
                        new_device_id,
                        old_entity_id,
                        new_entity_id,
                    )
                    self.maquina_id.write({
                        'pt_device_id': new_device_id,
                        'pt_entity_id': new_entity_id,
                        'pt_last_sync': fields.Datetime.now(),
                    })
                    lectura_remapeada = (
                        self._obtener_ultima_lectura_printtracker_v2(config)
                    )
                    if lectura_remapeada:
                        lectura_pt = lectura_remapeada
                        validacion = self._validar_nuevos_contadores_pt(
                            lectura_pt
                        )

            if not validacion.get('valido'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': validacion.get(
                            'mensaje',
                            'Lectura PrintTracker no válida.',
                        ),
                        'type': 'danger',
                    }
                }

            self._actualizar_contadores_desde_printtracker(lectura_pt)

            self.maquina_id.write({
                'pt_last_sync': fields.Datetime.now(),
            })

            _logger.info("ACTUALIZACIÓN PRINTTRACKER COMPLETADA")
            _logger.info("=" * 70)

            return self._mostrar_exito_actualizacion_pt(lectura_pt)

        except Exception as e:
            _logger.exception(
                "Error crítico actualizando desde PrintTracker | serie=%s",
                self.serie,
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }

    def _obtener_ultima_lectura_printtracker_v2(self, config):
        """
        Obtiene la lectura más reciente del dispositivo usando:
        /entity/{entityId}/device/{deviceId}/meter/mostRecentPriorTo

        Regla de selección del bloque de contadores:
        - CANON: pageCounts.equiv
        - Otras marcas: pageCounts.life

        Para equipos monocromos:
        - totalBlack -> B/N
        - Color -> 0

        Para equipos color:
        - totalBlack -> B/N
        - totalColor -> Color
        """
        self.ensure_one()

        maquina = self.maquina_id
        device_id = maquina.pt_device_id
        entity_id = maquina.pt_entity_id or config.entity_bbbb_id

        if not device_id:
            _logger.warning(
                "PrintTracker: máquina sin pt_device_id | serie=%s",
                self.serie,
            )
            return None

        if not maquina.pt_entity_id:
            _logger.warning(
                "PrintTracker: máquina sin pt_entity_id | serie=%s | "
                "usando entidad principal temporalmente=%s",
                self.serie,
                config.entity_bbbb_id,
            )

        from datetime import datetime, timezone

        # Siempre consultar la lectura más reciente disponible al momento
        # de pulsar "Actualizar desde PrintTracker".
        fecha_ref = datetime.now(timezone.utc)
        date_param = fecha_ref.isoformat().replace('+00:00', 'Z')

        url = (
            f'{config.api_url.rstrip("/")}/entity/{entity_id}/device/'
            f'{device_id}/meter/mostRecentPriorTo'
        )

        params = {'date': date_param}

        _logger.info(
            "PrintTracker mostRecentPriorTo | serie=%s | entityId=%s | "
            "deviceId=%s | date=%s",
            self.serie,
            entity_id,
            device_id,
            date_param,
        )

        def _meter_call():
            return requests.get(
                url,
                headers=config.get_api_headers(),
                params=params,
                timeout=config.timeout_seconds,
            )

        response = config._retry_api_call(_meter_call)

        if response.status_code != 200:
            _logger.error(
                "PrintTracker mostRecentPriorTo HTTP %s | serie=%s | "
                "entityId=%s | deviceId=%s | respuesta=%s",
                response.status_code,
                self.serie,
                entity_id,
                device_id,
                response.text[:1000],
            )
            return None

        data = response.json()

        if isinstance(data, list):
            if not data:
                _logger.warning(
                    "PrintTracker: mostRecentPriorTo sin lecturas | serie=%s",
                    self.serie,
                )
                return None
            lectura = data[0]
        elif isinstance(data, dict):
            lectura = data
        else:
            _logger.error(
                "PrintTracker: formato inesperado | tipo=%s",
                type(data).__name__,
            )
            return None

        page_counts = lectura.get('pageCounts') or {}
        life_counts = page_counts.get('life') or {}
        equiv_counts = page_counts.get('equiv') or {}

        def _value(block, key):
            raw = block.get(key) or {}
            if isinstance(raw, dict):
                raw = raw.get('value', 0)
            return self._safe_int(raw)

        life_total = _value(life_counts, 'total')
        life_black = _value(life_counts, 'totalBlack')
        life_color = _value(life_counts, 'totalColor')

        equiv_total = _value(equiv_counts, 'total')
        equiv_black = _value(equiv_counts, 'totalBlack')
        equiv_color = _value(equiv_counts, 'totalColor')

        _logger.info(
            "PrintTracker LIFE | serie=%s | total=%s | B/N=%s | Color=%s",
            self.serie,
            life_total,
            life_black,
            life_color,
        )

        _logger.info(
            "PrintTracker EQUIV | serie=%s | total=%s | B/N=%s | Color=%s",
            self.serie,
            equiv_total,
            equiv_black,
            equiv_color,
        )

        # Detectar la marca desde copier.company.marca_id.
        marca_nombre = ''
        if maquina.marca_id:
            marca_nombre = (
                maquina.marca_id.display_name
                or getattr(maquina.marca_id, 'name', '')
                or ''
            )

        marca_normalizada = str(marca_nombre).strip().lower()

        # PrintTracker muestra EQUIV para Canon.
        # Para las demás marcas se mantiene LIFE.
        usar_equiv = 'canon' in marca_normalizada

        if usar_equiv:
            selected_source = 'equiv'
            selected_total = equiv_total
            selected_black = equiv_black
            selected_color = equiv_color

            # Seguridad: si EQUIV no trae datos útiles, usar LIFE.
            if not equiv_counts or (
                selected_total == 0
                and selected_black == 0
                and selected_color == 0
                and (
                    life_total > 0
                    or life_black > 0
                    or life_color > 0
                )
            ):
                _logger.warning(
                    "PrintTracker: CANON sin valores EQUIV útiles; "
                    "usando LIFE como respaldo | serie=%s",
                    self.serie,
                )
                selected_source = 'life'
                selected_total = life_total
                selected_black = life_black
                selected_color = life_color
        else:
            selected_source = 'life'
            selected_total = life_total
            selected_black = life_black
            selected_color = life_color

            # Seguridad: si LIFE no existe o viene totalmente vacío y EQUIV sí
            # tiene datos, usar EQUIV para no guardar cero por error.
            if not life_counts or (
                selected_total == 0
                and selected_black == 0
                and selected_color == 0
                and (
                    equiv_total > 0
                    or equiv_black > 0
                    or equiv_color > 0
                )
            ):
                _logger.warning(
                    "PrintTracker: LIFE sin valores útiles; "
                    "usando EQUIV como respaldo | serie=%s | marca=%s",
                    self.serie,
                    marca_nombre,
                )
                selected_source = 'equiv'
                selected_total = equiv_total
                selected_black = equiv_black
                selected_color = equiv_color

        if maquina.tipo != 'color':
            selected_color = 0

        lectura['_odoo_counter_source'] = selected_source
        lectura['_odoo_selected_black'] = selected_black
        lectura['_odoo_selected_color'] = selected_color
        lectura['_odoo_selected_total'] = selected_total

        # Mantener las claves anteriores por compatibilidad con los métodos
        # existentes del archivo, aunque ahora pueden provenir de LIFE o EQUIV.
        lectura['_odoo_life_black'] = selected_black
        lectura['_odoo_life_color'] = selected_color
        lectura['_odoo_life_total'] = selected_total

        _logger.info(
            "PrintTracker CONTADOR SELECCIONADO | serie=%s | marca=%s | "
            "fuente=%s | total=%s | B/N=%s | Color=%s",
            self.serie,
            marca_nombre or 'Sin marca',
            selected_source.upper(),
            selected_total,
            selected_black,
            selected_color,
        )

        _logger.info(
            "PrintTracker lectura seleccionada | serie=%s | entityId=%s | "
            "deviceKey=%s | timestamp=%s | B/N=%s | Color=%s",
            self.serie,
            entity_id,
            lectura.get('deviceKey'),
            lectura.get('timestamp'),
            selected_black,
            selected_color,
        )

        return lectura

    def _get_pt_counts_container(self, lectura_pt):
        """
        Devuelve el bloque de contadores más adecuado.
        La documentación muestra normalmente `life`; algunas lecturas pueden incluir `default`.
        """
        page_counts = (lectura_pt or {}).get('pageCounts') or {}
        return page_counts.get('life') or page_counts.get('default') or {}

    def _validar_nuevos_contadores_pt(self, lectura_pt):
        """Valida los contadores seleccionados de PrintTracker."""
        self.ensure_one()

        contador_bn_nuevo = self._safe_int(
            lectura_pt.get(
                '_odoo_selected_black',
                lectura_pt.get('_odoo_life_black', 0),
            )
        )
        contador_color_nuevo = self._safe_int(
            lectura_pt.get(
                '_odoo_selected_color',
                lectura_pt.get('_odoo_life_color', 0),
            )
        )

        fuente = lectura_pt.get('_odoo_counter_source', 'life').upper()

        if self.maquina_id.tipo != 'color':
            contador_color_nuevo = 0

        anterior_bn = self.contador_anterior_bn or 0
        anterior_color = self.contador_anterior_color or 0

        _logger.info(
            "Validando PrintTracker %s | serie=%s | anterior_bn=%s | "
            "nuevo_bn=%s | anterior_color=%s | nuevo_color=%s",
            fuente,
            self.serie,
            anterior_bn,
            contador_bn_nuevo,
            anterior_color,
            contador_color_nuevo,
        )

        if contador_bn_nuevo < 0 or contador_color_nuevo < 0:
            return {
                'valido': False,
                'mensaje': 'PrintTracker devolvió contadores negativos.',
            }

        if contador_bn_nuevo < anterior_bn:
            return {
                'valido': False,
                'mensaje': (
                    f'El contador B/N {fuente} de PrintTracker '
                    f'({contador_bn_nuevo:,}) es menor al contador anterior '
                    f'registrado ({anterior_bn:,}).'
                ),
            }

        if self.maquina_id.tipo == 'color' and contador_color_nuevo < anterior_color:
            return {
                'valido': False,
                'mensaje': (
                    f'El contador Color {fuente} de PrintTracker '
                    f'({contador_color_nuevo:,}) es menor al contador anterior '
                    f'registrado ({anterior_color:,}).'
                ),
            }

        incremento_bn = contador_bn_nuevo - anterior_bn
        incremento_color = contador_color_nuevo - anterior_color

        if incremento_bn > 100000:
            _logger.warning(
                "PrintTracker: incremento B/N alto permitido | serie=%s | incremento=%s",
                self.serie,
                incremento_bn,
            )

        if self.maquina_id.tipo == 'color' and incremento_color > 50000:
            _logger.warning(
                "PrintTracker: incremento Color alto permitido | serie=%s | incremento=%s",
                self.serie,
                incremento_color,
            )

        return {'valido': True}

    def _actualizar_contadores_desde_printtracker(self, lectura_pt):
        """
        Actualiza los contadores usando la fuente seleccionada:
        CANON -> EQUIV
        otras marcas -> LIFE
        """
        self.ensure_one()

        contador_bn_nuevo = self._safe_int(
            lectura_pt.get(
                '_odoo_selected_black',
                lectura_pt.get('_odoo_life_black', 0),
            )
        )
        contador_color_nuevo = self._safe_int(
            lectura_pt.get(
                '_odoo_selected_color',
                lectura_pt.get('_odoo_life_color', 0),
            )
        )

        fuente = lectura_pt.get('_odoo_counter_source', 'life').upper()

        if self.maquina_id.tipo != 'color':
            contador_color_nuevo = 0

        timestamp = lectura_pt.get('timestamp')
        fecha_lectura = (
            self._parse_printtracker_datetime(timestamp)
            if timestamp
            else fields.Datetime.now()
        )

        anterior_bn = self.contador_anterior_bn or 0
        anterior_color = self.contador_anterior_color or 0

        self.write({
            'contador_actual_bn': contador_bn_nuevo,
            'contador_actual_color': contador_color_nuevo,
            'pt_updated': True,
            'pt_last_reading_date': fecha_lectura,
        })

        _logger.info(
            "PrintTracker actualizado desde %s | serie=%s | B/N=%s -> %s | "
            "Color=%s -> %s",
            fuente,
            self.serie,
            anterior_bn,
            contador_bn_nuevo,
            anterior_color,
            contador_color_nuevo,
        )

        self.message_post(
            body=(
                f"Contadores actualizados desde PrintTracker ({fuente})<br/>"
                f"B/N: {anterior_bn:,} → {contador_bn_nuevo:,}<br/>"
                f"Color: {anterior_color:,} → {contador_color_nuevo:,}<br/>"
                f"Fecha lectura PT: {fecha_lectura}<br/>"
                f"ID Device: {self.maquina_id.pt_device_id}"
            ),
            message_type='notification',
        )

    def _safe_int(self, value, default=0):
        try:
            if value in (None, '', 'N/A'):
                return default

            if isinstance(value, bool):
                return int(value)

            if isinstance(value, (int, float)):
                return int(value)

            value_str = str(value).strip().replace(',', '')

            try:
                return int(float(value_str))
            except (ValueError, TypeError):
                digits = ''.join(ch for ch in value_str if ch.isdigit())
                return int(digits) if digits else default

        except Exception:
            _logger.warning('PrintTracker: no se pudo convertir %r a entero.', value)
            return default

    def _parse_printtracker_datetime(self, datetime_str):
        """Convierte timestamp ISO/RFC3339 de PrintTracker a datetime UTC sin tz para Odoo."""
        if not datetime_str:
            return fields.Datetime.now()

        try:
            value = str(datetime_str).strip()

            # Python acepta +00:00; reemplazamos Z por UTC explícito.
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'

            parsed = datetime.fromisoformat(value)

            if parsed.tzinfo:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

            return parsed

        except Exception:
            _logger.warning(
                'PrintTracker: timestamp no reconocido %r. Se usará fecha actual.',
                datetime_str,
            )
            return fields.Datetime.now()

    def _mostrar_exito_actualizacion_pt(self, lectura_pt):
        self.ensure_one()

        incremento_bn = (self.contador_actual_bn or 0) - (self.contador_anterior_bn or 0)
        incremento_color = (
            (self.contador_actual_color or 0) - (self.contador_anterior_color or 0)
        )

        lines = [
            'Actualización exitosa desde PrintTracker',
            '',
            f'B/N: {self.contador_actual_bn:,} (+{incremento_bn:,})',
        ]

        if self.maquina_id.tipo == 'color':
            lines.append(
                f'Color: {self.contador_actual_color:,} (+{incremento_color:,})'
            )

        lines.extend([
            '',
            f'Fecha lectura: {self.pt_last_reading_date}',
            f'Total a facturar: S/ {self.total:.2f}',
        ])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Contadores Actualizados desde PrintTracker',
                'message': '\n'.join(lines),
                'type': 'success',
                'sticky': True,
            },
        }

    def debug_printtracker_api_raw(self):
        """Debug útil: comprueba el mapeo y busca el deviceKey en currentMeter."""
        self.ensure_one()

        if not self.maquina_id:
            raise UserError('No hay máquina asociada.')

        config = self.env['copier.printtracker.config'].get_active_config()

        device_id = self.maquina_id.pt_device_id or 'SIN MAPEO'
        lectura = None
        if self.maquina_id.pt_device_id:
            lectura = self._obtener_ultima_lectura_printtracker_v2(config)

        lines = [
            f'Serie: {self.serie}',
            f'Device ID: {device_id}',
            f'Entidad del dispositivo: {self.maquina_id.pt_entity_id or "N/A"}',
            f'Lectura encontrada: {"SÍ" if lectura else "NO"}',
        ]

        if lectura:
            counts = self._get_pt_counts_container(lectura)
            lines.extend([
                f'Timestamp: {lectura.get("timestamp") or "N/A"}',
                f'B/N: {self._safe_int((counts.get("totalBlack") or {}).get("value", 0))}',
                f'Color: {self._safe_int((counts.get("totalColor") or {}).get("value", 0))}',
            ])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug API PrintTracker',
                'message': '\n'.join(lines),
                'type': 'info',
                'sticky': True,
            },
        }

    def action_debug_printtracker_meters(self):
        """Compatibilidad con el botón debug existente."""
        self.ensure_one()
        return self.debug_printtracker_api_raw()

    def action_update_multiple_from_printtracker(self):
        """Actualiza múltiples contadores en borrador."""
        contadores_draft = self.filtered(lambda c: c.state == 'draft')

        if not contadores_draft:
            raise UserError('Solo se pueden actualizar contadores en estado borrador.')

        actualizados = 0
        errores = []

        for contador in contadores_draft:
            try:
                resultado = contador.action_update_from_printtracker()
                params = (resultado or {}).get('params') or {}

                if params.get('type') == 'success':
                    actualizados += 1
                else:
                    errores.append(
                        f'{contador.serie}: {params.get("message") or "No actualizado"}'
                    )
            except Exception as exc:
                _logger.exception(
                    'PrintTracker: error actualizando contador %s',
                    contador.name,
                )
                errores.append(f'{contador.serie}: {exc}')

        mensaje = f'Proceso completado: {actualizados} contadores actualizados'
        if errores:
            mensaje += f' | {len(errores)} con observaciones/error'
            mensaje += '\n' + '\n'.join(errores[:10])
            if len(errores) > 10:
                mensaje += f'\n... y {len(errores) - 10} más.'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Actualización Masiva desde PrintTracker',
                'message': mensaje,
                'type': 'success' if not errores else 'warning',
                'sticky': True,
            },
        }
