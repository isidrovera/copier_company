# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppConfig(models.Model):
    _name = 'whatsapp.config'
    _description = 'Configuración de WhatsApp API (Baileys)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
   

    # ============================================
    # INFORMACIÓN BÁSICA
    # ============================================
    company_id = fields.Many2one(
        'res.company',
        'Compañía',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        tracking=True,
        help='Compañía a la que pertenece esta configuración'
    )
    allowed_company_ids = fields.Many2many(
        'res.company',
        string='Compañías Permitidas',
        compute='_compute_allowed_company_ids',
        store=True,
        help='Compañías que pueden acceder a esta configuración'
    )
    @api.depends('company_id')
    def _compute_allowed_company_ids(self):
        """Compute allowed companies"""
        for record in self:
            record.allowed_company_ids = record.company_id
    name = fields.Char(
        'Nombre de Configuración', 
        required=True, 
        default='Configuración Principal',
        tracking=True
    )
    active = fields.Boolean(
        'Activo', 
        default=True, 
        tracking=True,
        help="Solo una configuración puede estar activa"
    )
    sequence = fields.Integer('Secuencia', default=10)
    
    # ============================================
    # CONFIGURACIÓN API
    # ============================================
    api_url = fields.Char(
        'URL de la API', 
        required=True, 
        default='http://localhost:3000',
        tracking=True,
        help='URL base de Baileys API (ejemplo: http://localhost:3000 o http://baileys-api:3000)'
    )
    api_key = fields.Char(
        'API Key', 
        required=True,
        tracking=True,
        help='Clave de autenticación para Baileys API'
    )
    session_name = fields.Char(
        'Nombre de Sesión',
        default='default',
        help='Nombre de la sesión de WhatsApp en Baileys'
    )
    
    # ============================================
    # ESTADO DE CONEXIÓN
    # ============================================
    is_connected = fields.Boolean(
        'Conectado',
        readonly=True,
        tracking=True,
        help='Estado de conexión con WhatsApp'
    )
    last_check = fields.Datetime(
        'Última Verificación', 
        readonly=True
    )
    connection_status = fields.Text(
        'Estado Detallado', 
        readonly=True
    )
    
    # ============================================
    # ESTADÍSTICAS GLOBALES
    # ============================================
    total_messages_sent = fields.Integer(
        'Mensajes Enviados', 
        readonly=True, 
        default=0,
        help='Total de mensajes enviados exitosamente'
    )
    total_messages_failed = fields.Integer(
        'Mensajes Fallidos', 
        readonly=True, 
        default=0,
        help='Total de mensajes que fallaron'
    )
    last_message_date = fields.Datetime(
        'Último Mensaje Enviado', 
        readonly=True
    )
    
    # ============================================
    # OPCIONES GENERALES
    # ============================================
    log_messages = fields.Boolean(
        'Registrar en Logs', 
        default=True,
        help='Registrar mensajes enviados en el log del servidor'
    )
    auto_verify_numbers = fields.Boolean(
        'Verificar Números Automáticamente',
        default=True,
        help='Verificar que los números existen en WhatsApp antes de enviar'
    )
    
    # ============================================
    # CONSTRAINTS
    # ============================================
    
    _unique_active = models.Constraint(
        'CHECK(1=1)',
        'Solo puede haber una configuración activa'
    )

    
    # ============================================
    # VALIDACIONES
    # ============================================
    @api.constrains('active', 'company_id')  # ✅ AGREGAR company_id
    def _check_single_active(self):
        """Asegurar que solo haya una configuración activa por compañía"""
        for record in self:
            if record.active:
                other_active = self.search([
                    ('active', '=', True),
                    ('company_id', '=', record.company_id.id),  # ✅ AGREGAR ESTA LÍNEA
                    ('id', '!=', record.id)
                ])
                if other_active:
                    other_active.write({'active': False})
                    _logger.info("Desactivando otras configuraciones: %s", other_active.mapped('name'))
    @api.constrains('api_url')
    def _check_api_url(self):
        """Validar formato de URL"""
        for record in self:
            if record.api_url:
                if not record.api_url.startswith(('http://', 'https://')):
                    raise ValidationError(_('La URL debe comenzar con http:// o https://'))
    
    # ============================================
    # MÉTODOS PÚBLICOS - CONEXIÓN
    # ============================================
    def check_connection(self, silent=False):
        """
        Verificar conexión con Baileys API
        
        Args:
            silent (bool): Si es True, no muestra notificaciones UI
            
        Returns:
            dict: Estado de conexión con keys 'connected' y 'message'
        """
        self.ensure_one()
        
        try:
            response = requests.get(
                f"{self.api_url}/api/status",
                headers={'x-api-key': self.api_key},
                timeout=5
            )
            
            current_time = fields.Datetime.now()
            
            if response.status_code == 200:
                data = response.json()
                is_connected = data.get('data', {}).get('isConnected', False)
                
                # Actualizar estado
                self.write({
                    'is_connected': is_connected,
                    'last_check': current_time,
                    'connection_status': f"""Estado: {'Conectado ✅' if is_connected else 'Desconectado ⚠️'}
Última verificación: {current_time.strftime('%d/%m/%Y %H:%M:%S')}
Respuesta API: OK (200)"""
                })
                
                status_info = {
                    'connected': is_connected,
                    'message': '✅ Conectado a WhatsApp' if is_connected else '⚠️ API responde pero WhatsApp no conectado',
                    'data': data
                }
                
                if not silent:
                    return self._show_notification(
                        '✅ Conexión exitosa con WhatsApp' if is_connected else '⚠️ API responde pero WhatsApp no está conectado. Escanea el código QR.',
                        'success' if is_connected else 'warning'
                    )
                
                return status_info
                
            else:
                self.write({
                    'is_connected': False,
                    'last_check': current_time,
                    'connection_status': f"""Estado: Error ❌
Última verificación: {current_time.strftime('%d/%m/%Y %H:%M:%S')}
Error HTTP: {response.status_code}"""
                })
                
                if not silent:
                    return self._show_notification(
                        f'❌ Error de conexión: HTTP {response.status_code}',
                        'danger'
                    )
                
                return {'connected': False, 'message': f'Error HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            self.write({
                'is_connected': False,
                'last_check': fields.Datetime.now(),
                'connection_status': f"""Estado: Timeout ❌
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Error: Tiempo de espera agotado"""
            })
            
            if not silent:
                return self._show_notification('❌ Timeout: La API no responde', 'danger')
            
            return {'connected': False, 'message': 'Timeout'}
            
        except Exception as e:
            self.write({
                'is_connected': False,
                'last_check': fields.Datetime.now(),
                'connection_status': f"""Estado: Error ❌
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Error: {str(e)}"""
            })
            
            if not silent:
                return self._show_notification(f'❌ Error: {str(e)}', 'danger')
            
            return {'connected': False, 'message': str(e)}
    
    def action_open_qr_page(self):
        """Abrir página de código QR en el navegador"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'{self.api_url}/qr',
            'target': 'new',
        }
    
    def action_test_notification(self):
        """Abrir wizard para enviar mensaje de prueba"""
        self.ensure_one()
        
        return {
            'name': _('Enviar Mensaje de Prueba'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.test.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id}
        }
    
    def action_view_notifications(self):
        """Ver todas las notificaciones enviadas con esta configuración"""
        self.ensure_one()
        
        return {
            'name': _('Notificaciones WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.service.notification',
            'view_mode': 'list,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id}
        }
    
    # ============================================
    # MÉTODOS PÚBLICOS - API
    # ============================================
    def verify_number(self, phone):
        """
        Verificar que un número existe en WhatsApp
        
        Args:
            phone (str): Número de teléfono limpio (ej: 51987654321)
            
        Returns:
            bool: True si existe, False si no
        """
        self.ensure_one()
        
        if not self.auto_verify_numbers:
            return True
        
        try:
            import json
            
            response = requests.post(
                f"{self.api_url}/api/check-number",
                headers={
                    'x-api-key': self.api_key,
                    'Content-Type': 'application/json'
                },
                data=json.dumps({'number': phone}),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                exists = data.get('data', {}).get('exists', False)
                
                if self.log_messages:
                    _logger.info("📱 Verificación número %s: %s", phone, "Existe" if exists else "No existe")
                
                return exists
            
            return False
            
        except Exception as e:
            _logger.error("Error verificando número WhatsApp %s: %s", phone, str(e))
            return False
    
    def send_message(self, phone, message):
        """
        Enviar mensaje de texto a través de Baileys API
        
        Args:
            phone (str): Número limpio (51987654321)
            message (str): Texto del mensaje
            
        Returns:
            dict: Resultado con keys 'success', 'message_id', 'error'
        """
        self.ensure_one()
        
        try:
            import json
            
            payload = {
                'number': phone,
                'text': message
            }
            
            if self.log_messages:
                _logger.info("📤 Enviando mensaje WhatsApp a: %s", phone)
            
            response = requests.post(
                f"{self.api_url}/api/send/text",
                headers={
                    'x-api-key': self.api_key,
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # Actualizar estadísticas
                    self.write({
                        'total_messages_sent': self.total_messages_sent + 1,
                        'last_message_date': fields.Datetime.now()
                    })
                    
                    if self.log_messages:
                        _logger.info("✅ Mensaje enviado exitosamente a %s", phone)
                    
                    return {
                        'success': True,
                        'message_id': result.get('data', {}).get('messageId'),
                        'error': None
                    }
                else:
                    error_msg = result.get('message', 'Error desconocido')
                    
                    self.write({
                        'total_messages_failed': self.total_messages_failed + 1
                    })
                    
                    _logger.error("❌ Error enviando mensaje: %s", error_msg)
                    
                    return {
                        'success': False,
                        'message_id': None,
                        'error': error_msg
                    }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                
                self.write({
                    'total_messages_failed': self.total_messages_failed + 1
                })
                
                _logger.error("❌ Error HTTP enviando mensaje: %s", error_msg)
                
                return {
                    'success': False,
                    'message_id': None,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = str(e)
            
            self.write({
                'total_messages_failed': self.total_messages_failed + 1
            })
            
            _logger.exception("❌ Excepción enviando mensaje WhatsApp: %s", error_msg)
            
            return {
                'success': False,
                'message_id': None,
                'error': error_msg
            }
    
    def send_media(self, phone, file_data, media_type='document', caption='', filename=None):
        """
        Enviar archivo multimedia por WhatsApp (Baileys)

        Args:
            phone (str): Número limpio (ej: 51987654321)
            file_data (bytes | base64): Contenido del archivo
            media_type (str): 'image', 'document', 'video', 'audio'
            caption (str): Texto que acompaña el archivo
            filename (str): Nombre real del archivo (ej: Propuesta_CT-000113.pdf)

        Returns:
            dict: Resultado {'success': bool, 'message_id': str, 'error': str}
        """
        self.ensure_one()

        try:
            import tempfile
            import os
            import base64
            import mimetypes
            import requests

            # -------------------------------------------------
            # Decodificar base64 si es necesario
            # -------------------------------------------------
            if isinstance(file_data, str):
                file_data = base64.b64decode(file_data)

            # -------------------------------------------------
            # Determinar extensión y MIME
            # -------------------------------------------------
            suffix_map = {
                'image': '.jpg',
                'document': '.pdf',
                'video': '.mp4',
                'audio': '.mp3'
            }
            suffix = suffix_map.get(media_type, '.bin')

            if filename:
                mime_type, _ = mimetypes.guess_type(filename)
            else:
                mime_type = None

            mime_type = mime_type or {
                'image': 'image/jpeg',
                'document': 'application/pdf',
                'video': 'video/mp4',
                'audio': 'audio/mpeg'
            }.get(media_type, 'application/octet-stream')

            real_filename = filename or f'file{suffix}'

            # -------------------------------------------------
            # Crear archivo temporal
            # -------------------------------------------------
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name

            try:
                # -------------------------------------------------
                # Endpoint según tipo
                # -------------------------------------------------
                endpoint_map = {
                    'image': '/api/send/image',
                    'document': '/api/send/document',
                    'video': '/api/send/video',
                    'audio': '/api/send/audio'
                }
                endpoint = endpoint_map.get(media_type, '/api/send/document')

                _logger.info("📤 Enviando %s a %s (%s)", media_type, phone, real_filename)

                with open(tmp_path, 'rb') as f:
                    files = {
                        'file': (real_filename, f, mime_type)
                    }
                    data = {
                        'number': phone,
                        'caption': caption or ''
                    }

                    response = requests.post(
                        f"{self.api_url}{endpoint}",
                        headers={'x-api-key': self.api_key},
                        files=files,
                        data=data,
                        timeout=30
                    )

                _logger.info("📡 WhatsApp API Status: %s", response.status_code)

                if response.status_code == 200:
                    result = response.json()

                    if result.get('success'):
                        self.write({
                            'total_messages_sent': self.total_messages_sent + 1,
                            'last_message_date': fields.Datetime.now()
                        })

                        _logger.info("✅ Archivo enviado correctamente a %s", phone)

                        return {
                            'success': True,
                            'message_id': result.get('data', {}).get('messageId'),
                            'error': None
                        }

                    error_msg = result.get('message', 'Error desconocido')
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"

                self.write({'total_messages_failed': self.total_messages_failed + 1})
                _logger.error("❌ Error enviando archivo: %s", error_msg)

                return {
                    'success': False,
                    'message_id': None,
                    'error': error_msg
                }

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            self.write({'total_messages_failed': self.total_messages_failed + 1})
            _logger.exception("❌ Excepción enviando media")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
   
    @api.model
    def clean_phone_number(self, phone, country_code='51'):
        """
        Limpiar y normalizar número de teléfono
        
        Args:
            phone (str): Número en cualquier formato
            country_code (str): Código de país por defecto (51 = Perú)
            
        Returns:
            str: Número limpio o cadena vacía si es inválido
            
        Examples:
            >>> self.env['whatsapp.config'].clean_phone_number('987654321')
            '51987654321'
            >>> self.env['whatsapp.config'].clean_phone_number('+51 987 654 321')
            '51987654321'
            >>> self.env['whatsapp.config'].clean_phone_number('51987654321')
            '51987654321'
        """
        import re
        
        if not phone:
            return ''
        
        # Remover todo excepto números
        clean = re.sub(r'[^0-9]', '', str(phone))
        
        # Agregar código de país si falta
        if len(clean) == 9:  # Solo número local (987654321)
            clean = country_code + clean
        elif len(clean) == 11 and clean.startswith('0'):  # Con 0 inicial (0987654321)
            clean = country_code + clean[1:]
        elif len(clean) == 11 and clean.startswith(country_code):  # Ya correcto (51987654321)
            pass
        else:
            # Longitud incorrecta
            _logger.warning("Número con longitud incorrecta: %s (longitud: %d)", phone, len(clean))
            return ''
        
        # Validar longitud final (11 dígitos para Perú: 51 + 9 dígitos)
        expected_length = len(country_code) + 9
        if len(clean) != expected_length:
            _logger.warning("Número no cumple longitud esperada de %d dígitos: %s", expected_length, clean)
            return ''
        
        return clean
    
    def _show_notification(self, message, notification_type='info'):
        """Helper para mostrar notificaciones en UI"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }
    
    # ============================================
    # MÉTODOS DE MODELO
    # ============================================
    @api.model
    def get_active_config(self):
        """
        Obtener configuración activa para la compañía actual
        
        Returns:
            whatsapp.config: Configuración activa
            
        Raises:
            ValidationError: Si no hay configuración activa
        """
        config = self.search([
            ('active', '=', True),
            ('company_id', '=', self.env.company.id)  # ✅ AGREGAR ESTA LÍNEA
        ], limit=1)
        
        if not config:
            raise ValidationError(_(
                'No hay configuración de WhatsApp activa para la compañía %s.\n'
                'Por favor configura WhatsApp en:\n'
                'Ajustes → WhatsApp API Config'
            ) % self.env.company.name)  # ✅ AGREGAR nombre de compañía
        return config

# ============================================
# WIZARD: ENVIAR MENSAJE DE PRUEBA
# ============================================
class WhatsAppTestMessageWizard(models.TransientModel):
    _name = 'whatsapp.test.message.wizard'
    _description = 'Wizard para Enviar Mensaje de Prueba WhatsApp'
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuración',
        required=True,
        readonly=True
    )
    phone = fields.Char(
        string='Número de Teléfono',
        required=True,
        help='Formato: 51987654321 (código de país + número)'
    )
    message = fields.Text(
        string='Mensaje',
        required=True,
        default='Este es un mensaje de prueba desde Odoo 🚀'
    )
    
    def action_send_test(self):  # ✅ CORREGIDO: cambié de action_send_test_message a action_send_test
        """Enviar mensaje de prueba"""
        self.ensure_one()
        
        # Limpiar número
        clean_phone = WhatsAppConfig.clean_phone_number(self.phone)
        
        if not clean_phone:
            raise ValidationError(_(
                'Número de teléfono inválido.\n'
                'Formato correcto: 51987654321 (código país + número)'
            ))
        
        # Verificar que el número existe (opcional)
        if self.config_id.auto_verify_numbers:
            exists = self.config_id.verify_number(clean_phone)
            if not exists:
                raise ValidationError(_(
                    'El número %s no existe en WhatsApp o no está registrado.'
                ) % self.phone)
        
        # Enviar mensaje
        result = self.config_id.send_message(clean_phone, self.message)
        
        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'✅ Mensaje enviado exitosamente a {self.phone}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise ValidationError(_(
                '❌ Error al enviar mensaje:\n%s'
            ) % result['error'])