# ====================================================================================
# ARCHIVO 1: models/printtracker_config.py
# Configuración de conexión con PrintTracker
# ====================================================================================

from odoo import models, fields, api
import requests
import logging
import time

_logger = logging.getLogger(__name__)

class PrintTrackerConfig(models.Model):
    _name = 'copier.printtracker.config'
    _description = 'Configuración API PrintTracker Pro - Copier Company'
    _rec_name = 'name'

    name = fields.Char('Nombre de Configuración', required=True, default='PrintTracker Pro Config')
    api_url = fields.Char('URL Base API', required=True, 
                         default='https://papi.printtrackerpro.com/v1',
                         help='URL base de la API de PrintTracker Pro')
    api_key = fields.Char('API Key', required=True,
                         help='Token de autenticación para la API')
    entity_bbbb_id = fields.Char('ID Entidad Principal', required=True,
                                help='ID de la entidad BBBB en PrintTracker')
    
    # Estado de conexión
    connection_status = fields.Selection([
        ('not_tested', 'No Probado'),
        ('connected', 'Conectado'),
        ('error', 'Error de Conexión')
    ], string='Estado Conexión', default='not_tested', readonly=True)
    
    last_error = fields.Text('Último Error', readonly=True)
    timeout_seconds = fields.Integer('Timeout (segundos)', default=30)
    max_retries = fields.Integer('Reintentos Máximos', default=3)
    retry_delay = fields.Integer('Delay entre Reintentos (seg)', default=5)

    def get_api_headers(self):
        """Retorna headers para requests a la API"""
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

    def _retry_api_call(self, func, *args, **kwargs):
        """Wrapper para reintentar llamadas API fallidas"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                _logger.warning(f"Intento {attempt + 1} falló, reintentando en {self.retry_delay}s...")
                time.sleep(self.retry_delay)

    def test_connection(self):
        """Prueba la conexión con PrintTracker API"""
        try:
            _logger.info(f"Probando conexión a {self.api_url} con entidad {self.entity_bbbb_id}")
            
            def _test_call():
                return requests.get(
                    f'{self.api_url.rstrip("/")}/entity/{self.entity_bbbb_id}',
                    headers=self.get_api_headers(),
                    timeout=self.timeout_seconds
                )
            
            response = self._retry_api_call(_test_call)
            
            if response.status_code == 200:
                data = response.json()
                entity_name = data.get('name', 'Sin nombre')
                
                self.write({
                    'connection_status': 'connected',
                    'last_error': False
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Conexión exitosa con PrintTracker Pro\nEntidad: {entity_name}',
                        'type': 'success'
                    }
                }
            else:
                error_msg = f'Error HTTP {response.status_code}: {response.text}'
                self.write({
                    'connection_status': 'error',
                    'last_error': error_msg
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Error de conexión: {error_msg}',
                        'type': 'danger'
                    }
                }
                
        except Exception as e:
            error_msg = str(e)
            self.write({
                'connection_status': 'error',
                'last_error': error_msg
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {error_msg}',
                    'type': 'danger'
                }
            }

    @api.model
    def get_active_config(self):
        """Obtiene la configuración activa"""
        config = self.search([], limit=1)
        if not config:
            raise ValueError("No hay configuración de PrintTracker configurada")
        return config

# ====================================================================================
# ARCHIVO 2: models/copier_company.py (AGREGAR ESTOS CAMPOS Y MÉTODOS)
# Extensión del modelo existente
# ====================================================================================

class CopierCompany(models.Model):
    _inherit = 'copier.company'
    
    # NUEVOS CAMPOS PARA PRINTTRACKER
    pt_device_id = fields.Char(
        'ID PrintTracker Device', 
        help='ID del dispositivo en PrintTracker Pro',
        index=True
    )
    pt_last_sync = fields.Datetime(
        'Última Sincronización PT',
        readonly=True,
        help='Última vez que se sincronizó con PrintTracker'
    )
    pt_mapped = fields.Boolean(
        'Mapeado con PrintTracker',
        compute='_compute_pt_mapped',
        help='Indica si está mapeado con PrintTracker'
    )

    @api.depends('pt_device_id')
    def _compute_pt_mapped(self):
        for record in self:
            record.pt_mapped = bool(record.pt_device_id)

    def action_map_printtracker(self):
        """Acción para mapear con PrintTracker por serie usando paginación del ejemplo"""
        self.ensure_one()
        
        if not self.serie_id:
            raise UserError('La máquina debe tener una serie para mapear con PrintTracker.')
        
        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            
            # Buscar dispositivo con paginación siguiendo el patrón del ejemplo
            device_found = self._search_device_with_pagination(config)
            
            if device_found:
                self.write({
                    'pt_device_id': device_found.get('id'),
                    'pt_last_sync': fields.Datetime.now()
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Máquina mapeada exitosamente con PrintTracker\nSerie: {self.serie_id}\nDispositivo ID: {device_found.get("id")}\nUbicación: {device_found.get("customLocation", "N/A")}',
                        'type': 'success'
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'No se encontró dispositivo con serie "{self.serie_id}" en PrintTracker.\n\nVerifica que la serie coincida exactamente.',
                        'type': 'warning'
                    }
                }
                
        except Exception as e:
            _logger.error(f"Error mapeando con PrintTracker: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def _search_device_with_pagination(self, config):
        """
        Búsqueda con paginación siguiendo exactamente el patrón del código de ejemplo
        Basado en sync_all_devices del archivo printtracker_config.py
        """
        serie_buscar = self.serie_id.strip()
        _logger.info(f"Iniciando búsqueda paginada para serie: {serie_buscar}")
        
        all_devices = []
        page = 1
        total_pages_processed = 0
        
        # PAGINACIÓN COMPLETA siguiendo el patrón del ejemplo
        while True:
            _logger.info(f"=== PROCESANDO PÁGINA {page} ===")
            
            params = {
                'includeChildren': True,
                'excludeDisabled': False,  # Incluir dispositivos deshabilitados por si acaso
                'limit': 100,             # Mismo límite que el ejemplo
                'page': page              # Parámetro clave que faltaba
            }
            
            def _devices_call():
                return requests.get(
                    f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/device',
                    headers=config.get_api_headers(),
                    params=params,
                    timeout=config.timeout_seconds
                )
            
            response = config._retry_api_call(_devices_call)
            
            _logger.info(f"Respuesta API página {page}: Status {response.status_code}")
            
            if response.status_code == 200:
                devices_page = response.json()
                
                _logger.info(f"Página {page}: {len(devices_page)} dispositivos recibidos")
                
                if not devices_page:
                    _logger.info(f"Página {page} vacía - Fin de datos")
                    break
                
                # BUSCAR EN ESTA PÁGINA INMEDIATAMENTE
                for device in devices_page:
                    device_serial = device.get('serialNumber', '').strip()
                    
                    if device_serial == serie_buscar:
                        _logger.info(f"DISPOSITIVO ENCONTRADO: {device_serial} -> ID: {device.get('id')}")
                        _logger.info(f"Ubicación: {device.get('customLocation', 'N/A')}")
                        _logger.info(f"Entidad: {device.get('entityKey', 'N/A')}")
                        return device
                
                all_devices.extend(devices_page)
                total_pages_processed += 1
                
                # Si la página está incompleta, es la última (patrón del ejemplo)
                if len(devices_page) < 100:
                    _logger.info(f"Página {page} incompleta - Última página")
                    break
                
                page += 1
                
                # Límite de seguridad (del ejemplo)
                if page > 50:
                    _logger.warning(f"Límite de seguridad alcanzado: {page-1} páginas")
                    break
                    
            else:
                error_msg = f'Error HTTP {response.status_code} en página {page}: {response.text}'
                _logger.error(f"Error de API: {error_msg}")
                
                if page == 1:
                    raise Exception(error_msg)
                else:
                    _logger.warning(f"Error en página {page}, continuando con datos obtenidos")
                    break
        
        # Log final de debug
        _logger.info(f"=== RESUMEN BÚSQUEDA ===")
        _logger.info(f"Páginas procesadas: {total_pages_processed}")
        _logger.info(f"Total dispositivos revisados: {len(all_devices)}")
        _logger.info(f"Serie buscada: '{serie_buscar}'")
        
        # Log de algunas series encontradas para debug
        series_encontradas = [d.get('serialNumber', 'N/A') for d in all_devices[:10]]
        _logger.info(f"Primeras 10 series encontradas: {series_encontradas}")
        
        return None
    def debug_list_printtracker_devices(self):
        """Método de debug para listar los primeros dispositivos"""
        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            
            response = requests.get(
                f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/device',
                headers=config.get_api_headers(),
                params={
                    'includeChildren': True,
                    'limit': 20,
                    'page': 1
                },
                timeout=config.timeout_seconds
            )
            
            if response.status_code == 200:
                devices = response.json()
                
                message_lines = [
                    f"DEBUG DISPOSITIVOS PRINTTRACKER",
                    f"Total en primera página: {len(devices)}",
                    "",
                    "Primeros 10 dispositivos:"
                ]
                
                for i, device in enumerate(devices[:10]):
                    message_lines.append(
                        f"{i+1}. Serie: '{device.get('serialNumber')}' | ID: {device.get('id')} | Ubicación: {device.get('customLocation', 'N/A')}"
                    )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Debug PrintTracker',
                        'message': '\n'.join(message_lines),
                        'type': 'info',
                        'sticky': True
                    }
                }
            else:
                raise Exception(f'Error HTTP {response.status_code}: {response.text}')
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error en debug: {str(e)}',
                    'type': 'danger'
                }
            }

# ====================================================================================
# ARCHIVO 3: models/copier_counter.py (AGREGAR ESTOS MÉTODOS)
# Extensión del modelo CopierCounter existente
# ====================================================================================

class CopierCounter(models.Model):
    _inherit = 'copier.counter'
    
    # Campo para rastrear si fue actualizado desde PrintTracker
    pt_updated = fields.Boolean(
        'Actualizado desde PrintTracker',
        default=False,
        help='Indica si los contadores fueron actualizados desde PrintTracker'
    )
    pt_last_reading_date = fields.Datetime(
        'Fecha Lectura PrintTracker',
        help='Fecha de la última lectura obtenida de PrintTracker'
    )

    def action_update_from_printtracker(self):
        """Botón para actualizar contadores desde PrintTracker"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError('Solo se pueden actualizar contadores en estado borrador.')
        
        if not self.maquina_id:
            raise UserError('No hay máquina asociada al contador.')
        
        if not self.maquina_id.pt_device_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'La máquina {self.serie} no está mapeada con PrintTracker.\nUse "Mapear con PrintTracker" en la máquina primero.',
                    'type': 'warning'
                }
            }
        
        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            
            # Obtener medidores actuales de PrintTracker
            lectura_pt = self._obtener_ultima_lectura_printtracker(config)
            
            if not lectura_pt:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'No hay lecturas disponibles en PrintTracker para la serie: {self.serie}',
                        'type': 'warning'
                    }
                }
            
            # Validar nuevos contadores
            validacion = self._validar_nuevos_contadores_pt(lectura_pt)
            if not validacion['valido']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Validación fallida: {validacion["mensaje"]}',
                        'type': 'danger'
                    }
                }
            
            # Actualizar contadores
            self._actualizar_contadores_desde_printtracker(lectura_pt)
            
            # Marcar sincronización
            self.maquina_id.write({'pt_last_sync': fields.Datetime.now()})
            
            return self._mostrar_exito_actualizacion_pt(lectura_pt)
            
        except Exception as e:
            _logger.error(f"Error actualizando desde PrintTracker: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    # REEMPLAZAR el método _obtener_ultima_lectura_printtracker en CopierCounter

    def _obtener_ultima_lectura_printtracker(self, config):
        """
        Obtiene la lectura más reciente de PrintTracker usando el endpoint correcto
        SIN parámetros de paginación que causan error 400
        """
        try:
            _logger.info(f"Obteniendo medidores para device_id: {self.maquina_id.pt_device_id}")
            
            # Usar endpoint sin parámetros problemáticos
            response = requests.get(
                f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/currentMeter',
                headers=config.get_api_headers(),
                params={
                    'includeChildren': True
                    # Removidos: excludeDisabled, limit, page que causan error 400
                },
                timeout=config.timeout_seconds
            )
            
            if response.status_code == 200:
                all_meters = response.json()
                _logger.info(f"Total medidores recibidos: {len(all_meters)}")
                
                # Buscar el medidor del dispositivo específico
                for meter_data in all_meters:
                    device_key = meter_data.get('deviceKey')
                    if device_key == self.maquina_id.pt_device_id:
                        _logger.info(f"Medidor encontrado para dispositivo: {device_key}")
                        _logger.info(f"Timestamp medidor: {meter_data.get('timestamp', 'N/A')}")
                        return meter_data
                
                _logger.warning(f"No se encontró medidor para device_id: {self.maquina_id.pt_device_id}")
                _logger.info(f"Device IDs disponibles: {[m.get('deviceKey') for m in all_meters[:5]]}")
                return None
            else:
                _logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            _logger.error(f"Error obteniendo lecturas de PrintTracker: {e}")
            return None

    def debug_printtracker_meters(self):
        """Método de debug para listar medidores disponibles - SIN parámetros problemáticos"""
        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            
            response = requests.get(
                f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/currentMeter',
                headers=config.get_api_headers(),
                params={
                    'includeChildren': True
                    # Sin limit ni page para evitar error 400
                },
                timeout=config.timeout_seconds
            )
            
            if response.status_code == 200:
                meters = response.json()
                
                message_lines = [
                    f"DEBUG MEDIDORES PRINTTRACKER",
                    f"Total medidores: {len(meters)}",
                    "",
                    "Primeros 10 medidores:"
                ]
                
                for i, meter in enumerate(meters[:10]):
                    device_key = meter.get('deviceKey', 'N/A')
                    timestamp = meter.get('timestamp', 'N/A')
                    page_counts = meter.get('pageCounts', {})
                    default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
                    
                    total_pages = 0
                    black_pages = 0
                    color_pages = 0
                    
                    if default_counts:
                        total_pages = default_counts.get('total', {}).get('value', 0)
                        black_pages = default_counts.get('totalBlack', {}).get('value', 0)
                        color_pages = default_counts.get('totalColor', {}).get('value', 0)
                    
                    message_lines.append(
                        f"{i+1}. Device: {device_key[:8]}... | Total: {total_pages} | B/N: {black_pages} | Color: {color_pages}"
                    )
                
                # Verificar si existe medidor para nuestra máquina
                our_device_id = self.maquina_id.pt_device_id if self.maquina_id else "N/A"
                found_our_meter = None
                
                for meter in meters:
                    if meter.get('deviceKey') == our_device_id:
                        found_our_meter = meter
                        break
                
                message_lines.extend([
                    "",
                    f"Buscando device_id: {our_device_id[:8]}..." if our_device_id != "N/A" else "Sin device_id configurado",
                    f"Encontrado: {'SÍ' if found_our_meter else 'NO'}"
                ])
                
                if found_our_meter:
                    page_counts = found_our_meter.get('pageCounts', {})
                    default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
                    
                    if default_counts:
                        total = default_counts.get('total', {}).get('value', 0)
                        black = default_counts.get('totalBlack', {}).get('value', 0)
                        color = default_counts.get('totalColor', {}).get('value', 0)
                        
                        message_lines.extend([
                            f"Contadores actuales:",
                            f"  Total: {total}",
                            f"  B/N: {black}",
                            f"  Color: {color}"
                        ])
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Debug Medidores PrintTracker',
                        'message': '\n'.join(message_lines),
                        'type': 'info',
                        'sticky': True
                    }
                }
            else:
                raise Exception(f'Error HTTP {response.status_code}: {response.text}')
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error en debug medidores: {str(e)}',
                    'type': 'danger'
                }
            }

    # TAMBIÉN AGREGAR este botón de debug al modelo CopierCounter para testing
    def action_debug_printtracker_meters(self):
        """Acción para el botón de debug de medidores"""
        return self.debug_printtracker_meters()
    def _validar_nuevos_contadores_pt(self, lectura_pt):
        """Valida que los nuevos contadores de PrintTracker sean coherentes"""
        try:
            # Extraer contadores de la estructura de PrintTracker
            page_counts = lectura_pt.get('pageCounts', {})
            default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
            
            if not default_counts:
                return {
                    'valido': False,
                    'mensaje': 'No se encontró estructura de contadores válida en PrintTracker'
                }
            
            # Extraer valores de contadores
            contador_bn_nuevo = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
            contador_color_nuevo = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
            
            _logger.info(f"Contadores PT - B/N: {contador_bn_nuevo}, Color: {contador_color_nuevo}")
            _logger.info(f"Contadores actuales - B/N anterior: {self.contador_anterior_bn}, Color anterior: {self.contador_anterior_color}")
            
            # Validar que no sean menores a los anteriores
            if contador_bn_nuevo < self.contador_anterior_bn:
                return {
                    'valido': False,
                    'mensaje': f'El contador B/N de PrintTracker ({contador_bn_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_bn:,})'
                }
            
            if contador_color_nuevo < self.contador_anterior_color:
                return {
                    'valido': False,
                    'mensaje': f'El contador Color de PrintTracker ({contador_color_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_color:,})'
                }
            
            # Validar incrementos razonables
            incremento_bn = contador_bn_nuevo - self.contador_anterior_bn
            incremento_color = contador_color_nuevo - self.contador_anterior_color
            
            if incremento_bn > 100000:
                return {
                    'valido': False,
                    'mensaje': f'Incremento B/N muy alto: {incremento_bn:,} páginas. Verificar datos.'
                }
            
            if incremento_color > 50000:
                return {
                    'valido': False,
                    'mensaje': f'Incremento Color muy alto: {incremento_color:,} páginas. Verificar datos.'
                }
            
            return {'valido': True}
            
        except Exception as e:
            return {
                'valido': False,
                'mensaje': f'Error validando contadores: {str(e)}'
            }

    def _safe_int(self, value, default=0):
        """Convierte un valor a entero de forma segura"""
        try:
            if value is None or value == '' or value == 'N/A':
                return default
            if isinstance(value, str):
                value = ''.join(filter(str.isdigit, value))
                if not value:
                    return default
            return int(value)
        except (ValueError, TypeError):
            _logger.warning(f"No se pudo convertir '{value}' a entero, usando {default}")
            return default

    def _actualizar_contadores_desde_printtracker(self, lectura_pt):
        """Actualiza los contadores con los datos de PrintTracker"""
        try:
            # Extraer contadores
            page_counts = lectura_pt.get('pageCounts', {})
            default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
            
            contador_bn_nuevo = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
            contador_color_nuevo = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
            
            # Obtener fecha de lectura
            timestamp = lectura_pt.get('timestamp')
            fecha_lectura = self._parse_printtracker_datetime(timestamp) if timestamp else fields.Datetime.now()
            
            valores_actualizar = {
                'contador_actual_bn': contador_bn_nuevo,
                'contador_actual_color': contador_color_nuevo,
                'pt_updated': True,
                'pt_last_reading_date': fecha_lectura
            }
            
            self.write(valores_actualizar)
            
            # Log de la actualización
            _logger.info(
                f"Contadores actualizados desde PrintTracker para {self.serie}: "
                f"B/N: {self.contador_anterior_bn} → {contador_bn_nuevo}, "
                f"Color: {self.contador_anterior_color} → {contador_color_nuevo}"
            )
            
            # Mensaje en el chatter
            self.message_post(
                body=f"""Contadores actualizados desde PrintTracker
                
Lecturas actualizadas:
• B/N: {self.contador_anterior_bn:,} → {contador_bn_nuevo:,} 
  (+{contador_bn_nuevo - self.contador_anterior_bn:,} páginas)
• Color: {self.contador_anterior_color:,} → {contador_color_nuevo:,} 
  (+{contador_color_nuevo - self.contador_anterior_color:,} páginas)

Fecha lectura PT: {fecha_lectura}
ID Device: {self.maquina_id.pt_device_id}""",
                message_type='notification'
            )
            
        except Exception as e:
            _logger.error(f"Error actualizando contadores: {e}")
            raise

    def _parse_printtracker_datetime(self, datetime_str):
        """Convierte fecha de PrintTracker a formato Odoo"""
        try:
            if not datetime_str:
                return fields.Datetime.now()
            
            from datetime import datetime
            import re
            
            # Limpiar formato ISO 8601
            clean_datetime = re.sub(r'\.\d+Z?$', '', datetime_str)
            clean_datetime = clean_datetime.replace('T', ' ').replace('Z', '')
            
            try:
                parsed_dt = datetime.strptime(clean_datetime, '%Y-%m-%d %H:%M:%S')
                return parsed_dt
            except ValueError:
                _logger.error(f"Formato de fecha inválido: {datetime_str}")
                return fields.Datetime.now()
                
        except Exception as e:
            _logger.error(f"Error parseando fecha: {e}")
            return fields.Datetime.now()

    def _mostrar_exito_actualizacion_pt(self, lectura_pt):
        """Muestra mensaje de éxito con detalles"""
        incremento_bn = self.contador_actual_bn - self.contador_anterior_bn
        incremento_color = self.contador_actual_color - self.contador_anterior_color
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Contadores Actualizados desde PrintTracker',
                'message': f"""Actualización exitosa:

Nuevos contadores:
• B/N: {self.contador_actual_bn:,} (+{incremento_bn:,})
• Color: {self.contador_actual_color:,} (+{incremento_color:,})

Fecha lectura: {self.pt_last_reading_date}
Total a facturar: S/ {self.total:.2f}""",
                'type': 'success',
                'sticky': True
            }
        }

    def action_update_multiple_from_printtracker(self):
        """Actualiza múltiples contadores desde PrintTracker"""
        contadores_draft = self.filtered(lambda c: c.state == 'draft')
        
        if not contadores_draft:
            raise UserError('Solo se pueden actualizar contadores en estado borrador.')
        
        actualizados = 0
        errores = []
        
        for contador in contadores_draft:
            try:
                resultado = contador.action_update_from_printtracker()
                if resultado['params']['type'] == 'success':
                    actualizados += 1
                else:
                    errores.append(f"{contador.serie}: {resultado['params']['message']}")
            except Exception as e:
                errores.append(f"{contador.serie}: {str(e)}")
        
        mensaje = f"Proceso completado: {actualizados} contadores actualizados"
        if errores:
            mensaje += f", {len(errores)} errores"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Actualización Masiva desde PrintTracker',
                'message': mensaje,
                'type': 'success' if not errores else 'warning',
                'sticky': True
            }
        }