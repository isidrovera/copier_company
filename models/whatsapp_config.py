# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppConfig(models.Model):
    _name = 'whatsapp.config'
    _description = 'Configuración de WhatsApp API (Baileys)'
    _order = 'sequence, id'

    # Información básica
    name = fields.Char('Nombre de Configuración', required=True, default='Configuración Principal')
    active = fields.Boolean('Activo', default=True, help="Solo una configuración puede estar activa")
    sequence = fields.Integer('Secuencia', default=10)
    
    # Configuración API
    api_url = fields.Char(
        'URL de la API', 
        required=True, 
        default='http://localhost:3000',
        help='URL base de Baileys API (ejemplo: http://localhost:3000)'
    )
    api_key = fields.Char(
        'API Key', 
        required=True,
        help='Clave de autenticación para Baileys API'
    )
    session_name = fields.Char(
        'Nombre de Sesión',
        default='default',
        help='Nombre de la sesión de WhatsApp'
    )
    
    # Estado de conexión
    is_connected = fields.Boolean(
        'Conectado',
        compute='_compute_connection_status',
        store=False,
        help='Estado de conexión con WhatsApp'
    )
    last_check = fields.Datetime('Última Verificación', readonly=True)
    connection_status = fields.Text('Estado Detallado', readonly=True)
    
    # Números de contacto técnico
    technical_phones = fields.Text(
        'Teléfonos Técnicos',
        help='Números de teléfono del equipo técnico (uno por línea o separados por coma)\nFormato: 51987654321'
    )
    supervisor_phone = fields.Char(
        'Teléfono Supervisor',
        help='Número del supervisor para tickets de alta prioridad\nFormato: 51987654321'
    )
    backup_phone = fields.Char(
        'Teléfono de Respaldo',
        default='51924894829',
        help='Número de respaldo si no hay otros configurados\nFormato: 51924894829'
    )
    
    # Configuración de notificaciones
    notify_client = fields.Boolean(
        'Notificar Cliente',
        default=True,
        help='Enviar notificación al cliente cuando reporte un servicio'
    )
    notify_technical = fields.Boolean(
        'Notificar Técnicos',
        default=True,
        help='Enviar notificación al equipo técnico'
    )
    notify_high_priority = fields.Boolean(
        'Notificar Supervisor en Prioridad Alta',
        default=True,
        help='Enviar notificación al supervisor cuando la prioridad sea Alta o Crítica'
    )
    send_photos = fields.Boolean(
        'Enviar Fotos',
        default=True,
        help='Enviar foto del problema al equipo técnico (si existe)'
    )
    
    # Plantillas de mensajes
    client_message_template = fields.Text(
        'Plantilla Mensaje Cliente',
        default="""🔧 *SOLICITUD DE SERVICIO REGISTRADA*

Hola *{contacto}*

Tu solicitud ha sido registrada exitosamente:

📋 *Número:* {numero_ticket}
🖨️ *Equipo:* {equipo}
📍 *Ubicación:* {ubicacion}
🏢 *Sede:* {sede}

⚠️ *Problema:* {tipo_problema}
⏰ *Prioridad:* {prioridad}

📝 *Descripción:*
_{descripcion}_

Nuestro equipo técnico te contactará pronto.
_Recibirás actualizaciones en este número._

---
_Copier Company S.A.C._
_Soluciones de Impresión_""",
        help='Plantilla del mensaje para el cliente. Variables disponibles: {contacto}, {numero_ticket}, {equipo}, {ubicacion}, {sede}, {tipo_problema}, {prioridad}, {descripcion}'
    )
    
    technical_message_template = fields.Text(
        'Plantilla Mensaje Técnico',
        default="""🚨 *NUEVA SOLICITUD DE SERVICIO*

📋 *Ticket:* {numero_ticket}
⏰ *Prioridad:* {prioridad}
🕐 *Creado:* {fecha_creacion}

👤 *Cliente:* {cliente}
📞 *Contacto:* {contacto}
📱 *Teléfono:* {telefono}
📧 *Email:* {email}

🖨️ *Equipo:*
- Modelo: {modelo}
- Serie: {serie}
- Marca: {marca}
- Ubicación: {ubicacion}
- Sede: {sede}

⚠️ *Tipo:* {tipo_problema}

📝 *Problema reportado:*
_{descripcion}_

🌐 *Origen:* {origen}

_Accede al sistema para más detalles_""",
        help='Plantilla del mensaje para técnicos. Variables disponibles: {numero_ticket}, {prioridad}, {fecha_creacion}, {cliente}, {contacto}, {telefono}, {email}, {modelo}, {serie}, {marca}, {ubicacion}, {sede}, {tipo_problema}, {descripcion}, {origen}'
    )
    
    # Estadísticas
    total_messages_sent = fields.Integer('Mensajes Enviados', readonly=True, default=0)
    total_messages_failed = fields.Integer('Mensajes Fallidos', readonly=True, default=0)
    last_message_date = fields.Datetime('Último Mensaje Enviado', readonly=True)
    
    # Logs
    log_messages = fields.Boolean('Registrar Mensajes en Log', default=True)
    
    _sql_constraints = [
        ('unique_active', 
         'CHECK(1=1)', 
         'Solo puede haber una configuración activa'),
    ]
    
    @api.constrains('active')
    def _check_single_active(self):
        """Asegurar que solo haya una configuración activa"""
        for record in self:
            if record.active:
                other_active = self.search([
                    ('active', '=', True),
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
    
    def _compute_connection_status(self):
        """Calcular estado de conexión"""
        for record in self:
            record.is_connected = False
            if record.api_url and record.api_key:
                try:
                    status = record.check_connection(silent=True)
                    record.is_connected = status.get('connected', False)
                except:
                    record.is_connected = False
    
    def check_connection(self, silent=False):
        """
        Verificar conexión con Baileys API
        
        Args:
            silent: Si es True, no muestra notificaciones
            
        Returns:
            dict: Estado de conexión
        """
        self.ensure_one()
        
        try:
            response = requests.get(
                f"{self.api_url}/api/status",
                headers={'x-api-key': self.api_key},
                timeout=5
            )
            
            self.last_check = fields.Datetime.now()
            
            if response.status_code == 200:
                data = response.json()
                is_connected = data.get('data', {}).get('isConnected', False)
                
                status_info = {
                    'connected': is_connected,
                    'message': '✅ Conectado a WhatsApp' if is_connected else '⚠️ API responde pero WhatsApp no conectado',
                    'data': data
                }
                
                self.connection_status = f"""Estado: {'Conectado ✅' if is_connected else 'Desconectado ⚠️'}
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Respuesta API: OK (200)"""
                
                if not silent:
                    if is_connected:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': '✅ Conexión exitosa con WhatsApp',
                                'type': 'success',
                                'sticky': False,
                            }
                        }
                    else:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': '⚠️ API responde pero WhatsApp no está conectado. Escanea el código QR.',
                                'type': 'warning',
                                'sticky': False,
                            }
                        }
                
                return status_info
            else:
                self.connection_status = f"""Estado: Error ❌
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Error HTTP: {response.status_code}"""
                
                if not silent:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': f'❌ Error de conexión: HTTP {response.status_code}',
                            'type': 'danger',
                            'sticky': False,
                        }
                    }
                
                return {'connected': False, 'message': f'Error HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            self.connection_status = f"""Estado: Timeout ❌
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Error: Tiempo de espera agotado"""
            
            if not silent:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': '❌ Timeout: La API no responde',
                        'type': 'danger',
                        'sticky': False,
                    }
                }
            
            return {'connected': False, 'message': 'Timeout'}
            
        except Exception as e:
            self.connection_status = f"""Estado: Error ❌
Última verificación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Error: {str(e)}"""
            
            if not silent:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'❌ Error: {str(e)}',
                        'type': 'danger',
                        'sticky': False,
                    }
                }
            
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
        """Enviar mensaje de prueba"""
        self.ensure_one()
        
        return {
            'name': _('Enviar Mensaje de Prueba'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.test.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id}
        }
    
    def get_technical_phones_list(self):
        """
        Obtener lista de teléfonos técnicos
        
        Returns:
            list: Lista de números limpiados
        """
        self.ensure_one()
        phones = []
        
        if self.technical_phones:
            # Soportar tanto comas como saltos de línea
            raw_phones = self.technical_phones.replace(',', '\n').split('\n')
            for phone in raw_phones:
                clean_phone = self._clean_phone_number(phone.strip())
                if clean_phone and clean_phone not in phones:
                    phones.append(clean_phone)
        
        return phones
    
    def _clean_phone_number(self, phone):
        """Limpiar número de teléfono"""
        import re
        
        if not phone:
            return ''
        
        # Remover todo excepto números
        clean = re.sub(r'[^0-9]', '', str(phone))
        
        # Normalizar para Perú
        if len(clean) == 9:
            clean = '51' + clean
        elif len(clean) == 11 and clean.startswith('051'):
            clean = clean[1:]
        
        # Validar longitud final
        if len(clean) != 11:
            return ''
        
        return clean
    
    @api.model
    def get_active_config(self):
        """Obtener configuración activa"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise ValidationError(_(
                'No hay configuración de WhatsApp activa. '
                'Por favor configura WhatsApp en: Configuración → Técnico → WhatsApp API'
            ))
        return config