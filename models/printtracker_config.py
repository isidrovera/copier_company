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

    # ARCHIVO: models/copier_counter.py
    # REEMPLAZAR completamente los métodos de PrintTracker en CopierCounter

    def action_update_from_printtracker(self):
        """Botón para actualizar contadores desde PrintTracker con logging completo"""
        self.ensure_one()
        
        _logger.info("=" * 60)
        _logger.info("INICIANDO ACTUALIZACIÓN DESDE PRINTTRACKER")
        _logger.info("=" * 60)
        _logger.info(f"Counter ID: {self.id}")
        _logger.info(f"Serie: {self.serie}")
        _logger.info(f"Estado: {self.state}")
        
        if self.state != 'draft':
            _logger.error(f"Estado inválido: {self.state} (debe ser 'draft')")
            raise UserError('Solo se pueden actualizar contadores en estado borrador.')
        
        if not self.maquina_id:
            _logger.error("No hay máquina asociada")
            raise UserError('No hay máquina asociada al contador.')
        
        _logger.info(f"Máquina ID: {self.maquina_id.id}")
        _logger.info(f"PrintTracker Device ID: {self.maquina_id.pt_device_id}")
        
        if not self.maquina_id.pt_device_id:
            _logger.error("Máquina no mapeada con PrintTracker")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'La máquina {self.serie} no está mapeada con PrintTracker.\nUse "Mapear con PrintTracker" en la máquina primero.',
                    'type': 'warning'
                }
            }
        
        try:
            # Paso 1: Obtener configuración
            _logger.info("PASO 1: Obteniendo configuración PrintTracker")
            config = self.env['copier.printtracker.config'].get_active_config()
            _logger.info(f"Config encontrada: {config.name}")
            _logger.info(f"URL API: {config.api_url}")
            _logger.info(f"Entidad ID: {config.entity_bbbb_id}")
            
            # Paso 2: Obtener medidores
            _logger.info("PASO 2: Obteniendo lecturas de PrintTracker")
            lectura_pt = self._obtener_ultima_lectura_printtracker_v2(config)
            
            if not lectura_pt:
                _logger.error("No se pudieron obtener lecturas de PrintTracker")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'No hay lecturas disponibles en PrintTracker para la serie: {self.serie}',
                        'type': 'warning'
                    }
                }
            
            # Paso 3: Validar contadores
            _logger.info("PASO 3: Validando nuevos contadores")
            validacion = self._validar_nuevos_contadores_pt(lectura_pt)
            if not validacion['valido']:
                _logger.error(f"Validación fallida: {validacion['mensaje']}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Validación fallida: {validacion["mensaje"]}',
                        'type': 'danger'
                    }
                }
            
            # Paso 4: Actualizar contadores
            _logger.info("PASO 4: Actualizando contadores")
            self._actualizar_contadores_desde_printtracker(lectura_pt)
            
            # Paso 5: Marcar sincronización
            _logger.info("PASO 5: Marcando sincronización")
            self.maquina_id.write({'pt_last_sync': fields.Datetime.now()})
            
            _logger.info("ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            _logger.info("=" * 60)
            
            return self._mostrar_exito_actualizacion_pt(lectura_pt)
            
        except Exception as e:
            _logger.error("=" * 60)
            _logger.error(f"ERROR CRÍTICO EN ACTUALIZACIÓN: {e}")
            _logger.error("=" * 60)
            import traceback
            _logger.error(f"Traceback completo: {traceback.format_exc()}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def _obtener_ultima_lectura_printtracker_v2(self, config):
        """
        SOLUCIÓN FINAL: La API requiere AMBOS parámetros page Y limit > 0
        CORRECCIÓN: Buscar por deviceId._id en lugar de deviceKey
        """
        _logger.info("--- Iniciando obtención de medidores ---")
        _logger.info(f"Device ID buscado: {self.maquina_id.pt_device_id}")
        
        try:
            # Construir URL y headers
            url = f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/currentMeter'
            headers = config.get_api_headers()
            
            _logger.info(f"URL petición: {url}")
            _logger.info(f"Headers: {headers}")
            
            # PARÁMETROS OBLIGATORIOS FINALES: page Y limit
            params = {
                'includeChildren': True,
                'page': 1,      # OBLIGATORIO
                'limit': 100    # OBLIGATORIO 
            }
            
            _logger.info(f"Parámetros finales: {params}")
            _logger.info("Haciendo petición HTTP con page=1 y limit=100...")
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=config.timeout_seconds
            )
            
            _logger.info(f"Status Code: {response.status_code}")
            _logger.info(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            if response.status_code == 200:
                all_meters = response.json()
                _logger.info(f"✅ ÉXITO: {len(all_meters)} medidores recibidos")
                
                # Buscar nuestro dispositivo
                target_device_id = self.maquina_id.pt_device_id
                _logger.info(f"Buscando dispositivo: {target_device_id}")
                
                for i, meter_data in enumerate(all_meters):
                    # CORRECCIÓN: La estructura correcta es deviceId._id, NO deviceKey
                    device_info = meter_data.get('deviceId', {})
                    device_id_actual = device_info.get('_id') if isinstance(device_info, dict) else None
                    
                    # Log de debug para el primer registro
                    if i == 0:
                        _logger.info(f"Estructura ejemplo página 1:")
                        _logger.info(f"  deviceId type: {type(device_info)}")
                        if isinstance(device_info, dict):
                            _logger.info(f"  deviceId keys: {list(device_info.keys())}")
                        _logger.info(f"  deviceId._id: {device_id_actual}")
                    
                    if device_id_actual == target_device_id:
                        _logger.info(f"🎯 MEDIDOR ENCONTRADO en posición {i+1}")
                        _logger.info(f"Device ID: {device_id_actual}")
                        _logger.info(f"Timestamp: {meter_data.get('timestamp', 'N/A')}")
                        
                        # Analizar estructura del medidor
                        page_counts = meter_data.get('pageCounts', {})
                        _logger.info(f"Estructura pageCounts: {list(page_counts.keys())}")
                        
                        default_counts = None
                        if 'default' in page_counts:
                            default_counts = page_counts['default']
                            _logger.info(f"✅ Usando estructura 'default'")
                            _logger.info(f"Campos disponibles: {list(default_counts.keys())}")
                        elif 'life' in page_counts:
                            default_counts = page_counts['life']
                            _logger.info(f"✅ Usando estructura 'life'")
                            _logger.info(f"Campos disponibles: {list(default_counts.keys())}")
                        else:
                            _logger.error("❌ No se encontró estructura 'default' ni 'life'")
                            _logger.info(f"Estructuras disponibles: {list(page_counts.keys())}")
                            return None
                        
                        # Extraer y logar valores específicos
                        if default_counts:
                            total_black = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
                            total_color = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
                            total_pages = self._safe_int(default_counts.get('total', {}).get('value', 0))
                            
                            _logger.info(f"📊 VALORES EXTRAÍDOS:")
                            _logger.info(f"  Total páginas: {total_pages:,}")
                            _logger.info(f"  Total B/N: {total_black:,}")
                            _logger.info(f"  Total Color: {total_color:,}")
                            
                            # Verificar que los valores sean válidos
                            if total_black == 0 and total_color == 0 and total_pages == 0:
                                _logger.warning("⚠️ Todos los contadores son 0 - verificar estructura")
                            else:
                                _logger.info("✅ Valores válidos encontrados")
                        
                        return meter_data
                
                # Si no se encontró en página 1, intentar página 2
                _logger.warning(f"❌ Dispositivo NO encontrado en página 1")
                _logger.info("🔄 Intentando página 2...")
                
                response_page2 = requests.get(
                    url,
                    headers=headers,
                    params={'includeChildren': True, 'page': 2, 'limit': 100},
                    timeout=config.timeout_seconds
                )
                
                if response_page2.status_code == 200:
                    all_meters_page2 = response_page2.json()
                    _logger.info(f"📄 Página 2: {len(all_meters_page2)} medidores")
                    
                    for i, meter_data in enumerate(all_meters_page2):
                        # CORRECCIÓN: Usar deviceId._id
                        device_info = meter_data.get('deviceId', {})
                        device_id_actual = device_info.get('_id') if isinstance(device_info, dict) else None
                        if device_id_actual == target_device_id:
                            _logger.info(f"🎯 MEDIDOR ENCONTRADO en página 2, posición {i+1}")
                            return meter_data
                
                # Log de debug: mostrar dispositivos disponibles
                _logger.warning(f"❌ Dispositivo {target_device_id} NO encontrado en ninguna página")
                _logger.info("📋 Device IDs disponibles (primeros 10):")
                
                available_devices = []
                for i, meter in enumerate(all_meters[:10]):
                    device_info = meter.get('deviceId', {})
                    device_id_actual = device_info.get('_id', 'N/A') if isinstance(device_info, dict) else 'N/A'
                    timestamp = meter.get('timestamp', 'N/A')
                    available_devices.append(device_id_actual)
                    _logger.info(f"  {i+1}. {device_id_actual} | {timestamp}")
                
                return None
                
            else:
                _logger.error(f"❌ Error HTTP {response.status_code}")
                _logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            _logger.error(f"💥 Excepción en obtención de medidores: {e}")
            import traceback
            _logger.error(f"Traceback completo: {traceback.format_exc()}")
            return None

    def debug_printtracker_api_raw(self):
        """Debug directo de la API con diferentes combinaciones de parámetros"""
        try:
            config = self.env['copier.printtracker.config'].get_active_config()
            url = f'{config.api_url.rstrip("/")}/entity/{config.entity_bbbb_id}/currentMeter'
            headers = config.get_api_headers()
            
            # Probar diferentes combinaciones
            test_cases = [
                {'page': 1},
                {'page': 1, 'includeChildren': True},
                {'page': 1, 'includeChildren': True, 'limit': 10},
                {'page': 1, 'limit': 10},
            ]
            
            results = []
            
            for i, params in enumerate(test_cases):
                try:
                    _logger.info(f"Probando caso {i+1}: {params}")
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        results.append(f"✅ Caso {i+1}: {len(data)} medidores")
                        _logger.info(f"Éxito caso {i+1}: {len(data)} medidores")
                        
                        # Si encontramos nuestro dispositivo, reportarlo
                        target_id = self.maquina_id.pt_device_id if self.maquina_id else None
                        if target_id:
                            found = any(m.get('deviceKey') == target_id for m in data)
                            if found:
                                results.append(f"   🎯 Dispositivo {target_id[:8]}... ENCONTRADO")
                                _logger.info(f"Dispositivo encontrado en caso {i+1}")
                    else:
                        results.append(f"❌ Caso {i+1}: HTTP {response.status_code}")
                        _logger.error(f"Error caso {i+1}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    results.append(f"💥 Caso {i+1}: {str(e)}")
                    _logger.error(f"Excepción caso {i+1}: {e}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Debug API PrintTracker',
                    'message': '\n'.join(results),
                    'type': 'info',
                    'sticky': True
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error en debug: {str(e)}',
                    'type': 'danger'
                }
            }


    def _validar_nuevos_contadores_pt(self, lectura_pt):
        """Validación con logging detallado"""
        _logger.info("--- Iniciando validación de contadores ---")
        
        try:
            # Extraer contadores de PrintTracker
            page_counts = lectura_pt.get('pageCounts', {})
            default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
            
            if not default_counts:
                _logger.error("No se encontró estructura de contadores válida")
                return {
                    'valido': False,
                    'mensaje': 'No se encontró estructura de contadores válida en PrintTracker'
                }
            
            # Extraer valores
            contador_bn_nuevo = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
            contador_color_nuevo = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
            
            _logger.info(f"Contadores actuales en Odoo:")
            _logger.info(f"  B/N anterior: {self.contador_anterior_bn}")
            _logger.info(f"  Color anterior: {self.contador_anterior_color}")
            _logger.info(f"Contadores nuevos de PrintTracker:")
            _logger.info(f"  B/N nuevo: {contador_bn_nuevo}")
            _logger.info(f"  Color nuevo: {contador_color_nuevo}")
            
            # Validaciones
            if contador_bn_nuevo < self.contador_anterior_bn:
                error_msg = f'El contador B/N de PrintTracker ({contador_bn_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_bn:,})'
                _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            if contador_color_nuevo < self.contador_anterior_color:
                error_msg = f'El contador Color de PrintTracker ({contador_color_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_color:,})'
                _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            # Calcular incrementos
            incremento_bn = contador_bn_nuevo - self.contador_anterior_bn
            incremento_color = contador_color_nuevo - self.contador_anterior_color
            
            _logger.info(f"Incrementos calculados:")
            _logger.info(f"  B/N: +{incremento_bn:,}")
            _logger.info(f"  Color: +{incremento_color:,}")
            
            # Validar incrementos razonables
            if incremento_bn > 100000:
                error_msg = f'Incremento B/N muy alto: {incremento_bn:,} páginas. Verificar datos.'
                _logger.warning(f"ADVERTENCIA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            if incremento_color > 50000:
                error_msg = f'Incremento Color muy alto: {incremento_color:,} páginas. Verificar datos.'
                _logger.warning(f"ADVERTENCIA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            _logger.info("VALIDACIÓN EXITOSA: Todos los controles pasaron")
            return {'valido': True}
            
        except Exception as e:
            error_msg = f'Error validando contadores: {str(e)}'
            _logger.error(f"EXCEPCIÓN EN VALIDACIÓN: {error_msg}")
            return {'valido': False, 'mensaje': error_msg}

    def _actualizar_contadores_desde_printtracker(self, lectura_pt):
        """Actualización con logging detallado"""
        _logger.info("--- Iniciando actualización de contadores ---")
        
        try:
            # Extraer contadores
            page_counts = lectura_pt.get('pageCounts', {})
            default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
            
            contador_bn_nuevo = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
            contador_color_nuevo = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
            
            # Obtener fecha de lectura
            timestamp = lectura_pt.get('timestamp')
            fecha_lectura = self._parse_printtracker_datetime(timestamp) if timestamp else fields.Datetime.now()
            
            _logger.info(f"Valores a actualizar:")
            _logger.info(f"  contador_actual_bn: {self.contador_actual_bn} → {contador_bn_nuevo}")
            _logger.info(f"  contador_actual_color: {self.contador_actual_color} → {contador_color_nuevo}")
            _logger.info(f"  pt_last_reading_date: {fecha_lectura}")
            
            valores_actualizar = {
                'contador_actual_bn': contador_bn_nuevo,
                'contador_actual_color': contador_color_nuevo,
                'pt_updated': True,
                'pt_last_reading_date': fecha_lectura
            }
            
            # Actualizar registro
            self.write(valores_actualizar)
            _logger.info("Registro actualizado en base de datos")
            
            # Mensaje en el chatter
            incremento_bn = contador_bn_nuevo - self.contador_anterior_bn
            incremento_color = contador_color_nuevo - self.contador_anterior_color
            
            mensaje_chatter = f"""Contadores actualizados desde PrintTracker

    Lecturas actualizadas:
    • B/N: {self.contador_anterior_bn:,} → {contador_bn_nuevo:,} 
    (+{incremento_bn:,} páginas)
    • Color: {self.contador_anterior_color:,} → {contador_color_nuevo:,} 
    (+{incremento_color:,} páginas)

    Fecha lectura PT: {fecha_lectura}
    ID Device: {self.maquina_id.pt_device_id}"""
            
            self.message_post(
                body=mensaje_chatter,
                message_type='notification'
            )
            _logger.info("Mensaje agregado al chatter")
            
            _logger.info("ACTUALIZACIÓN COMPLETADA")
            
        except Exception as e:
            _logger.error(f"Error en actualización: {e}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _mostrar_exito_actualizacion_pt(self, lectura_pt):
        """Mensaje de éxito con logging"""
        incremento_bn = self.contador_actual_bn - self.contador_anterior_bn
        incremento_color = self.contador_actual_color - self.contador_anterior_color
        
        mensaje = f"""Actualización exitosa desde PrintTracker

    Nuevos contadores:
    • B/N: {self.contador_actual_bn:,} (+{incremento_bn:,})
    • Color: {self.contador_actual_color:,} (+{incremento_color:,})

    Fecha lectura: {self.pt_last_reading_date}
    Total a facturar: S/ {self.total:.2f}"""
        
        _logger.info("MOSTRANDO MENSAJE DE ÉXITO AL USUARIO")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Contadores Actualizados desde PrintTracker',
                'message': mensaje,
                'type': 'success',
                'sticky': True
            }
        }
    # TAMBIÉN AGREGAR este botón de debug al modelo CopierCounter para testing
    def action_debug_printtracker_meters(self):
        """Acción para el botón de debug de medidores"""
        return self.debug_printtracker_meters()
    def _validar_nuevos_contadores_pt(self, lectura_pt):
        """Validación mejorada que permite primeras lecturas con logging detallado"""
        _logger.info("--- Iniciando validación de contadores ---")
        
        try:
            # Extraer contadores de PrintTracker
            page_counts = lectura_pt.get('pageCounts', {})
            default_counts = page_counts.get('default', {}) or page_counts.get('life', {})
            
            if not default_counts:
                _logger.error("No se encontró estructura de contadores válida")
                return {
                    'valido': False,
                    'mensaje': 'No se encontró estructura de contadores válida en PrintTracker'
                }
            
            # Extraer valores
            contador_bn_nuevo = self._safe_int(default_counts.get('totalBlack', {}).get('value', 0))
            contador_color_nuevo = self._safe_int(default_counts.get('totalColor', {}).get('value', 0))
            
            _logger.info(f"Contadores actuales en Odoo:")
            _logger.info(f"  B/N anterior: {self.contador_anterior_bn}")
            _logger.info(f"  Color anterior: {self.contador_anterior_color}")
            _logger.info(f"Contadores nuevos de PrintTracker:")
            _logger.info(f"  B/N nuevo: {contador_bn_nuevo}")
            _logger.info(f"  Color nuevo: {contador_color_nuevo}")
            
            # DETECTAR SI ES PRIMERA LECTURA
            es_primera_lectura = (self.contador_anterior_bn == 0 and self.contador_anterior_color == 0)
            
            if es_primera_lectura:
                _logger.info("🆕 DETECTADA PRIMERA LECTURA - Saltando validaciones de incremento")
                
                # Para primera lectura, solo validar que los valores sean razonables
                if contador_bn_nuevo < 0:
                    error_msg = f'Contador B/N inválido: {contador_bn_nuevo} (no puede ser negativo)'
                    _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                    return {'valido': False, 'mensaje': error_msg}
                
                if contador_color_nuevo < 0:
                    error_msg = f'Contador Color inválido: {contador_color_nuevo} (no puede ser negativo)'
                    _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                    return {'valido': False, 'mensaje': error_msg}
                
                # Validación de valores extremos para primera lectura
                if contador_bn_nuevo > 10000000:  # 10 millones como límite absoluto
                    error_msg = f'Contador B/N extremadamente alto: {contador_bn_nuevo:,}. Verificar si es correcto.'
                    _logger.warning(f"ADVERTENCIA: {error_msg}")
                    return {'valido': False, 'mensaje': error_msg}
                
                if contador_color_nuevo > 5000000:  # 5 millones como límite absoluto
                    error_msg = f'Contador Color extremadamente alto: {contador_color_nuevo:,}. Verificar si es correcto.'
                    _logger.warning(f"ADVERTENCIA: {error_msg}")
                    return {'valido': False, 'mensaje': error_msg}
                
                _logger.info("✅ PRIMERA LECTURA VALIDADA: Valores dentro de rangos aceptables")
                return {'valido': True}
            
            # VALIDACIONES PARA LECTURAS SUBSECUENTES
            _logger.info("📊 Validando lectura subsecuente...")
            
            # Validar que no sean menores a los anteriores
            if contador_bn_nuevo < self.contador_anterior_bn:
                error_msg = f'El contador B/N de PrintTracker ({contador_bn_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_bn:,})'
                _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            if contador_color_nuevo < self.contador_anterior_color:
                error_msg = f'El contador Color de PrintTracker ({contador_color_nuevo:,}) es menor al anterior registrado ({self.contador_anterior_color:,})'
                _logger.error(f"VALIDACIÓN FALLIDA: {error_msg}")
                return {'valido': False, 'mensaje': error_msg}
            
            # Calcular incrementos
            incremento_bn = contador_bn_nuevo - self.contador_anterior_bn
            incremento_color = contador_color_nuevo - self.contador_anterior_color
            
            _logger.info(f"Incrementos calculados:")
            _logger.info(f"  B/N: +{incremento_bn:,}")
            _logger.info(f"  Color: +{incremento_color:,}")
            
            # Validar incrementos razonables para lecturas mensuales
            limite_bn_mensual = 100000      # 100k páginas B/N por mes
            limite_color_mensual = 50000    # 50k páginas Color por mes
            
            if incremento_bn > limite_bn_mensual:
                error_msg = f'Incremento B/N muy alto: {incremento_bn:,} páginas. ¿Confirma que es correcto?'
                _logger.warning(f"ADVERTENCIA: {error_msg}")
                # CAMBIO: En lugar de rechazar, convertir en advertencia permisiva
                _logger.info("ℹ️ Permitiendo incremento alto por ser posible en equipos de alto volumen")
            
            if incremento_color > limite_color_mensual:
                error_msg = f'Incremento Color muy alto: {incremento_color:,} páginas. ¿Confirma que es correcto?'
                _logger.warning(f"ADVERTENCIA: {error_msg}")
                # CAMBIO: En lugar de rechazar, convertir en advertencia permisiva
                _logger.info("ℹ️ Permitiendo incremento alto por ser posible en equipos de alto volumen")
            
            _logger.info("✅ VALIDACIÓN EXITOSA: Todos los controles pasaron")
            return {'valido': True}
            
        except Exception as e:
            error_msg = f'Error validando contadores: {str(e)}'
            _logger.error(f"EXCEPCIÓN EN VALIDACIÓN: {error_msg}")
            return {'valido': False, 'mensaje': error_msg}

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