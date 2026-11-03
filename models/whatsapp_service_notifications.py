# -*- coding: utf-8 -*-
import logging
import pytz
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Zona horaria de Perú
PERU_TZ = pytz.timezone('America/Lima')


def to_peru_time(dt_utc, fmt='%d/%m/%Y %H:%M'):
    """
    Convierte un datetime UTC a hora peruana formateada.
    
    Args:
        dt_utc: datetime en UTC (puede ser naive o aware)
        fmt: formato de salida
    Returns:
        str: fecha/hora formateada en hora peruana
    """
    if not dt_utc:
        return 'No disponible'
    if dt_utc.tzinfo is None:
        dt_utc = pytz.utc.localize(dt_utc)
    dt_peru = dt_utc.astimezone(PERU_TZ)
    return dt_peru.strftime(fmt)


class WhatsAppServiceNotification(models.Model):
    """Gestión de Notificaciones WhatsApp para Servicios Técnicos"""
    _name = 'whatsapp.service.notification'
    _description = 'Notificaciones WhatsApp de Servicios Técnicos'
    
    _rec_name = 'service_request_id'
    
    # ============================================
    # CAMPOS BÁSICOS
    # ============================================
    service_request_id = fields.Many2one(
        'copier.service.request',
        string='Solicitud de Servicio',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    notification_type = fields.Selection([
        ('new_request_support', 'Nueva Solicitud (Soporte)'),
        ('new_request_client', 'Confirmación (Cliente)'),
        ('technician_assigned', 'Técnico Asignado'),
        ('technician_on_route', 'Técnico en Camino'),
        ('service_started', 'Servicio Iniciado'),
        ('service_completed', 'Servicio Completado'),
        ('service_paused', 'Servicio Pausado'),
        ('service_cancelled', 'Servicio Cancelado'),
        ('evaluation_reminder', 'Recordatorio Evaluación'),
        ('sla_alert', 'Alerta SLA'),
    ], string='Tipo de Notificación', required=True, index=True)
    
    recipient_type = fields.Selection([
        ('support', 'Soporte'),
        ('client', 'Cliente'),
        ('technician', 'Técnico'),
    ], string='Tipo de Destinatario', required=True)
    
    phone_number = fields.Char(
        string='Número de Teléfono',
        required=True,
        help='Número limpio formato: 51987654321'
    )
    
    message_text = fields.Text(
        string='Mensaje Enviado',
        required=True
    )
    
    # ============================================
    # ESTADO Y RESULTADO
    # ============================================
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    ], string='Estado', default='pending', required=True, index=True)
    
    sent_date = fields.Datetime(
        string='Fecha de Envío',
        readonly=True
    )
    
    error_message = fields.Text(
        string='Mensaje de Error',
        readonly=True
    )
    
    whatsapp_message_id = fields.Char(
        string='ID Mensaje WhatsApp',
        readonly=True,
        help='ID del mensaje retornado por la API'
    )
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuración WhatsApp',
        readonly=True
    )
    
    # ============================================
    # CAMPOS RELACIONADOS
    # ============================================
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='service_request_id.company_id',
        store=True,
        readonly=True
    )
    
    # ============================================
    # MÉTODO PRINCIPAL DE ENVÍO
    # ============================================
    def send_notification(self):
        """Enviar notificación WhatsApp"""
        self.ensure_one()
        
        try:
            # Obtener configuración activa
            config = self.env['whatsapp.config'].get_active_config()
            
            if not config.is_connected:
                _logger.warning("WhatsApp no conectado, verificando conexión...")
                connection = config.check_connection(silent=True)
                if not connection.get('connected'):
                    raise ValidationError(_('WhatsApp no está conectado. Por favor escanea el código QR.'))
            
            # Limpiar número
            clean_phone = self.env['whatsapp.config'].clean_phone_number(self.phone_number)
            if not clean_phone:
                raise ValidationError(_('Número de teléfono inválido: %s') % self.phone_number)
            
            # Verificar número (opcional según configuración)
            if config.auto_verify_numbers:
                exists = config.verify_number(clean_phone)
                if not exists:
                    _logger.warning("Número %s no existe en WhatsApp", clean_phone)
                    self.write({
                        'state': 'failed',
                        'error_message': f'Número {self.phone_number} no existe en WhatsApp'
                    })
                    return False
            
            # Enviar mensaje
            result = config.send_message(clean_phone, self.message_text)
            
            if result['success']:
                self.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'whatsapp_message_id': result.get('message_id'),
                    'config_id': config.id,
                    'error_message': False
                })
                
                _logger.info("✅ Notificación WhatsApp enviada: %s a %s", 
                            self.notification_type, self.phone_number)
                
                # Registrar en chatter de la solicitud
                now_peru = to_peru_time(fields.Datetime.now())
                self.service_request_id.message_post(
                    body=f"""
                        📱 Notificación WhatsApp Enviada
                        
                        • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                        • Destinatario: {self.phone_number}
                        • Fecha: {now_peru}
                        • Estado: Enviado ✅
                    """,
                    message_type='notification'
                )
                
                return True
            else:
                self.write({
                    'state': 'failed',
                    'error_message': result.get('error', 'Error desconocido')
                })
                
                _logger.error("❌ Error enviando notificación WhatsApp: %s", result.get('error'))
                
                now_peru = to_peru_time(fields.Datetime.now())
                self.service_request_id.message_post(
                    body=f"""
                        ❌ Error Enviando Notificación WhatsApp
                        
                        • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                        • Destinatario: {self.phone_number}
                        • Error: {result.get('error')}
                        • Fecha: {now_peru}
                    """,
                    message_type='notification'
                )
                
                return False
                
        except Exception as e:
            error_msg = str(e)
            
            self.write({
                'state': 'failed',
                'error_message': error_msg
            })
            
            _logger.exception("❌ Excepción enviando notificación WhatsApp: %s", error_msg)
            
            now_peru = to_peru_time(fields.Datetime.now())
            self.service_request_id.message_post(
                body=f"""
                    ❌ Excepción Enviando Notificación WhatsApp
                    
                    • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                    • Error: {error_msg}
                    • Fecha: {now_peru}
                """,
                message_type='notification'
            )
            
            return False
    
    # ============================================
    # ACCIÓN MANUAL
    # ============================================
    def action_retry_send(self):
        """Reintentar envío de notificación fallida"""
        for record in self:
            if record.state == 'failed':
                record.send_notification()


class WhatsAppServiceTemplate(models.Model):
    """Plantillas de Mensajes WhatsApp para Servicios"""
    _name = 'whatsapp.service.template'
    _description = 'Plantillas de Mensajes WhatsApp'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Nombre',
        required=True
    )
    preview_text = fields.Text(
        string='Vista Preliminar',
        compute='_compute_preview_text',
        store=False,
        help='Vista preliminar del mensaje con valores de ejemplo'
    )
    
    @api.depends('template_text')
    def _compute_preview_text(self):
        """Generar vista preliminar con datos de ejemplo"""
        for record in self:
            if not record.template_text:
                record.preview_text = ''
                continue
            
            # Variables de ejemplo (incluye TODAS las variables disponibles)
            sample_variables = {
                'number': 'ST-2024-001',
                'client': 'Empresa Demo S.A.C.',
                'equipment': 'Ricoh MP C3004',
                'serie': 'E1234567890',
                'location': 'Av. Javier Prado 123, Piso 5, Oficina 501',
                'sede': 'Sede Principal - San Isidro',
                'problem': 'Atasco de papel',
                'priority': 'Alta',
                'technician': 'Juan Pérez',
                'technician_phone': '+51 987 654 321',
                'technician_dni': '12345678',
                'vehicle': 'Mitsubishi L200 - Placa: BTH677',
                'date': '15/01/2026 14:30',
                'contact': 'María García',
                'phone': '+51 987 654 321',
                'work_done': 'Se realizó limpieza de rodillos, ajuste de sensores y pruebas de impresión.',
                'reason': 'Falta de repuestos en stock',
                'time': '15/01/2026 16:45',
                'time_remaining': '1.5 horas',
                'tracking_url': 'https://copiercompanysac.com/service/track/abc123',
                'evaluation_url': 'https://copiercompanysac.com/service/evaluate/xyz789',
            }
            
            try:
                record.preview_text = record.template_text.format(**sample_variables)
            except KeyError as e:
                record.preview_text = f'⚠️ Error en plantilla: Variable no reconocida {str(e)}\n\nPlantilla original:\n{record.template_text}'
    
    def action_send_test_message(self):
        """Abrir wizard para enviar mensaje de prueba"""
        self.ensure_one()
        
        return {
            'name': _('Enviar Mensaje de Prueba'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.template.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_template_text': self.preview_text,
            }
        }
    
    def action_show_variables_help(self):
        """Mostrar ayuda con todas las variables disponibles"""
        self.ensure_one()
        
        return {
            'name': _('Variables Disponibles'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.template.variables.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
    
    notification_type = fields.Selection([
        ('new_request_support', 'Nueva Solicitud (Soporte)'),
        ('new_request_client', 'Confirmación (Cliente)'),
        ('technician_assigned', 'Técnico Asignado'),
        ('technician_on_route', 'Técnico en Camino'),
        ('service_started', 'Servicio Iniciado'),
        ('service_completed', 'Servicio Completado'),
        ('service_paused', 'Servicio Pausado'),
        ('service_cancelled', 'Servicio Cancelado'),
        ('evaluation_reminder', 'Recordatorio Evaluación'),
        ('sla_alert', 'Alerta SLA'),
    ], string='Tipo de Notificación', required=True, index=True)
    
    template_text = fields.Text(
        string='Plantilla del Mensaje',
        required=True,
        help="""Variables disponibles:
        {number} - Número de solicitud
        {client} - Nombre del cliente
        {equipment} - Modelo del equipo
        {serie} - Serie del equipo
        {location} - Ubicación
        {sede} - Sede del equipo
        {problem} - Tipo de problema
        {priority} - Prioridad
        {technician} - Nombre del técnico
        {technician_phone} - Teléfono del técnico
        {technician_dni} - DNI del técnico
        {vehicle} - Información del vehículo (marca, modelo, placa)
        {date} - Fecha programada (hora Perú)
        {contact} - Nombre del contacto
        {phone} - Teléfono de contacto
        {work_done} - Trabajo realizado
        {reason} - Motivo de pausa/cancelación
        {time} - Fecha/hora actual (hora Perú)
        {time_remaining} - Tiempo restante SLA
        {tracking_url} - URL de seguimiento
        {evaluation_url} - URL de evaluación
        """
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )
    
    
    _unique_type_company = models.Constraint(
        'UNIQUE(notification_type, company_id)',
        'Solo puede haber una plantilla por tipo de notificación por compañía.'
    )

    @api.model
    def get_template(self, notification_type):
        """Obtener plantilla activa para un tipo de notificación"""
        template = self.search([
            ('notification_type', '=', notification_type),
            ('active', '=', True),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if template:
            return template.template_text
        
        # Templates por defecto si no existe
        return self._get_default_template(notification_type)
    
    @api.model
    def _get_default_template(self, notification_type):
        """Templates por defecto con variables de vehículo, DNI y hora peruana"""
        templates = {
            'new_request_support': """🚨 *NUEVA SOLICITUD DE SERVICIO*

📋 Número: {number}
👤 Cliente: {client}
🖨️ Equipo: {equipment} (Serie: {serie})
📍 Ubicación: {location}
🏢 Sede: {sede}
🔧 Problema: {problem}
⚠️ Prioridad: {priority}

📞 Contacto: {contact}
📱 Teléfono: {phone}

⏰ Hora (Perú): {time}""",

            'new_request_client': """✅ *SOLICITUD RECIBIDA*

Hola {contact}, hemos recibido tu solicitud de servicio técnico.

📋 *Número:* {number}
🖨️ *Equipo:* {equipment}
📍 *Ubicación:* {location}
🔧 *Problema:* {problem}

Nuestro equipo técnico revisará tu solicitud y te contactará pronto.

📧 Recibirás actualizaciones por email y WhatsApp.

_Gracias por confiar en nosotros_ 🙏""",

            'technician_assigned': """👨‍🔧 *TÉCNICO ASIGNADO*

Hola {contact},

Tu solicitud *{number}* ha sido asignada:

👤 *Técnico:* {technician}
🪪 *DNI:* {technician_dni}
📱 *Teléfono:* {technician_phone}
🚗 *Vehículo:* {vehicle}
📅 *Fecha programada:* {date}
🖨️ *Equipo:* {equipment}
📍 *Ubicación:* {location}

El técnico se pondrá en contacto contigo para confirmar la visita.

_¡Gracias por tu paciencia!_ 🙏""",

            'technician_on_route': """🚗 *TÉCNICO EN CAMINO*

Hola {contact},

El técnico *{technician}* está en camino a tu ubicación.

📋 Solicitud: {number}
🪪 DNI: {technician_dni}
🚗 Vehículo: {vehicle}
📍 Destino: {location}
⏰ Hora de salida: {time}

_Por favor mantente atento_ 📱""",

            'service_started': """✅ *SERVICIO INICIADO*

El técnico *{technician}* ha iniciado el servicio en tu equipo.

📋 Solicitud: {number}
🖨️ Equipo: {equipment}
⏰ Inicio: {time}

_Trabajando en resolver el problema..._ 🔧""",

            'service_completed': """🎉 *SERVICIO COMPLETADO*

Hola {contact},

Tu solicitud *{number}* ha sido completada exitosamente.

✅ *Trabajo realizado:*
{work_done}

📄 *Ver detalles del servicio:*
{tracking_url}

⭐ *Califica nuestro servicio aquí:*
{evaluation_url}

⏰ Finalizado: {time}
👨‍🔧 Técnico: {technician}

📝 *¿Cómo calificas el servicio?*
Tu opinión es muy importante para nosotros.

_¡Gracias por tu confianza!_ 🙏""",

            'service_paused': """⏸️ *SERVICIO PAUSADO*

Hola {contact},

Tu solicitud *{number}* ha sido pausada temporalmente.

📝 Motivo: {reason}

Te contactaremos pronto para continuar.

_Disculpa las molestias_ 🙏""",

            'service_cancelled': """❌ *SERVICIO CANCELADO*

Hola {contact},

Tu solicitud *{number}* ha sido cancelada.

📝 Motivo: {reason}
⏰ Fecha: {time}

Si necesitas más información, no dudes en contactarnos.

_Quedamos a tu disposición_ 📞""",

            'evaluation_reminder': """⭐ *RECORDATORIO DE EVALUACIÓN*

Hola {contact},

Hace unos días completamos el servicio de tu equipo (Solicitud *{number}*).

📝 Evalúa aquí (toma menos de 1 minuto):
{evaluation_url}

Tu evaluación nos ayuda a mejorar nuestro servicio.

_¡Gracias por tu tiempo!_ 🙏""",

            'sla_alert': """⚠️ *ALERTA SLA - SOLICITUD {number}*

🚨 Solicitud próxima a vencer

👤 Cliente: {client}
🖨️ Equipo: {equipment}
📍 Ubicación: {location}
⏰ Tiempo restante: {time_remaining}

_ACCIÓN REQUERIDA_ ⚡"""
        }
        
        return templates.get(notification_type, '')


class CopierServiceRequest(models.Model):
    """Extensión del modelo de Solicitud de Servicio para WhatsApp"""
    _inherit = 'copier.service.request'
    
    # ============================================
    # CONFIGURACIÓN DE NOTIFICACIONES
    # ============================================
    enable_whatsapp_notifications = fields.Boolean(
        string='Habilitar Notificaciones WhatsApp',
        default=True,
        help='Enviar notificaciones por WhatsApp además de email'
    )
    
    whatsapp_notification_ids = fields.One2many(
        'whatsapp.service.notification',
        'service_request_id',
        string='Notificaciones WhatsApp'
    )
    
    whatsapp_notifications_count = fields.Integer(
        string='Total Notificaciones WhatsApp',
        compute='_compute_whatsapp_notifications_count'
    )
    
    @api.depends('whatsapp_notification_ids')
    def _compute_whatsapp_notifications_count(self):
        for record in self:
            record.whatsapp_notifications_count = len(record.whatsapp_notification_ids)
    
    # ============================================
    # MÉTODO CENTRAL DE NOTIFICACIÓN WHATSAPP
    # ============================================
    def _send_whatsapp_notification(self, notification_type, recipient_type, phone, work_done=None, reason=None):
        """
        Método central para enviar notificaciones WhatsApp.
        Todas las fechas se convierten a hora peruana (America/Lima).
        
        Args:
            notification_type (str): Tipo de notificación
            recipient_type (str): Tipo de destinatario (support, client, technician)
            phone (str): Número de teléfono del destinatario
            work_done (str): Trabajo realizado (para service_completed)
            reason (str): Motivo (para pausas/cancelaciones)
        
        Returns:
            bool: True si se envió correctamente
        """
        self.ensure_one()
        
        if not self.enable_whatsapp_notifications:
            _logger.info("Notificaciones WhatsApp deshabilitadas para %s", self.name)
            return False
        
        try:
            # Obtener plantilla
            template_text = self.env['whatsapp.service.template'].get_template(notification_type)
            if not template_text:
                _logger.warning("No hay plantilla para tipo: %s", notification_type)
                return False
            
            # Limpiar número
            clean_phone = self.env['whatsapp.config'].clean_phone_number(phone)
            if not clean_phone:
                _logger.warning("Número inválido para notificación: %s", phone)
                return False
            
            # ============================================
            # PREPARAR VARIABLES CON HORA PERUANA
            # ============================================
            
            # URLs públicas
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            tracking_url = f"{base_url}/service/track/{self.tracking_token}" if self.tracking_token else 'N/A'
            evaluation_url = f"{base_url}/service/evaluate/{self.evaluation_token}" if self.evaluation_token else 'N/A'
            
            # Prioridad legible
            prioridad_map = {'0': 'Baja', '1': 'Normal', '2': 'Alta', '3': 'Crítica'}
            
            # Datos del técnico
            tecnico = self.tecnico_id
            technician_name = tecnico.name if tecnico else 'Por asignar'
            technician_phone = tecnico.phone or 'No disponible' if tecnico else 'No disponible'
            technician_dni = tecnico.vat or 'No registrado' if tecnico else 'No registrado'
            
            # Datos del vehículo
            vehicle_info = self.vehicle_info or 'No asignado'
            
            # Hora actual en Perú
            now_utc = fields.Datetime.now()
            
            variables = {
                # Solicitud
                'number': self.name or 'N/A',
                'priority': prioridad_map.get(self.prioridad, 'Normal'),
                
                # Cliente
                'client': self.cliente_id.name if self.cliente_id else 'N/A',
                'contact': self.contacto or 'N/A',
                'phone': self.telefono_contacto or 'N/A',
                
                # Equipo
                'equipment': self.modelo_maquina.name if self.modelo_maquina else 'N/A',
                'serie': self.serie_maquina or 'N/A',
                'location': self.ubicacion or 'N/A',
                'sede': self.sede or 'N/A',
                'problem': self.tipo_problema_id.name if self.tipo_problema_id else 'N/A',
                
                # Técnico
                'technician': technician_name,
                'technician_phone': technician_phone,
                'technician_dni': technician_dni,
                
                # Vehículo
                'vehicle': vehicle_info,
                
                # Fechas (HORA PERUANA)
                'date': to_peru_time(self.fecha_programada),
                'time': to_peru_time(now_utc),
                
                # Trabajo / Motivos
                'work_done': work_done or self.trabajo_realizado or 'N/A',
                'reason': reason or 'No especificado',
                
                # SLA
                'time_remaining': 'N/A',
                
                # URLs
                'tracking_url': tracking_url,
                'evaluation_url': evaluation_url,
            }
            
            # Calcular tiempo restante para SLA
            if self.create_date and self.sla_limite_1:
                tiempo_transcurrido = (now_utc - self.create_date).total_seconds() / 3600.0
                tiempo_restante = self.sla_limite_1 - tiempo_transcurrido
                if tiempo_restante > 0:
                    variables['time_remaining'] = f"{tiempo_restante:.1f} horas"
                else:
                    variables['time_remaining'] = '⚠️ VENCIDO'
            
            # Renderizar plantilla
            try:
                message = template_text.format(**variables)
            except KeyError as e:
                _logger.error("Variable no encontrada en plantilla %s: %s", notification_type, str(e))
                # Intentar enviar con la variable faltante como N/A
                try:
                    variables[str(e).strip("'")] = 'N/A'
                    message = template_text.format(**variables)
                except Exception:
                    return False
            
            # Crear registro de notificación
            notification = self.env['whatsapp.service.notification'].create({
                'service_request_id': self.id,
                'notification_type': notification_type,
                'recipient_type': recipient_type,
                'phone_number': clean_phone,
                'message_text': message,
                'state': 'pending',
            })
            
            # Enviar
            return notification.send_notification()
            
        except Exception as e:
            _logger.exception("Error en _send_whatsapp_notification: %s", str(e))
            return False
    
    # ============================================
    # MÉTODOS DE NOTIFICACIÓN POR TIPO
    # ============================================
    
    def _notify_support_new_request(self):
        """Notificar a soporte sobre nueva solicitud"""
        self.ensure_one()
        
        support_phone = self.env['ir.config_parameter'].sudo().get_param(
            'whatsapp.support_phone', '51975399303'
        )
        
        return self._send_whatsapp_notification(
            notification_type='new_request_support',
            recipient_type='support',
            phone=support_phone
        )
    
    def _notify_client_request_received(self):
        """Notificar al cliente que su solicitud fue recibida"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            _logger.warning("Solicitud %s no tiene teléfono de contacto", self.name)
            return False
        
        return self._send_whatsapp_notification(
            notification_type='new_request_client',
            recipient_type='client',
            phone=self.telefono_contacto
        )
    
    def _notify_technician_assigned(self):
        """Notificar al cliente que se asignó técnico"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='technician_assigned',
            recipient_type='client',
            phone=self.telefono_contacto
        )
    
    def _notify_technician_on_route(self):
        """Notificar al cliente que el técnico está en camino"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='technician_on_route',
            recipient_type='client',
            phone=self.telefono_contacto
        )
    
    def _notify_service_started(self):
        """Notificar al cliente que el servicio inició"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='service_started',
            recipient_type='client',
            phone=self.telefono_contacto
        )
    
    def _notify_service_completed(self):
        """Notificar al cliente que el servicio se completó"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='service_completed',
            recipient_type='client',
            phone=self.telefono_contacto,
            work_done=self.trabajo_realizado or 'Ver detalles en el reporte'
        )
    
    def _notify_service_paused(self):
        """Notificar al cliente que el servicio se pausó"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='service_paused',
            recipient_type='client',
            phone=self.telefono_contacto,
            reason=self.motivo_pausa or 'No especificado'
        )
    
    def _notify_service_cancelled(self):
        """Notificar al cliente que el servicio se canceló"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='service_cancelled',
            recipient_type='client',
            phone=self.telefono_contacto,
            reason=self.motivo_cancelacion or 'No especificado'
        )
    
    def _notify_evaluation_reminder(self):
        """Enviar recordatorio de evaluación"""
        self.ensure_one()
        
        if not self.telefono_contacto:
            return False
        
        return self._send_whatsapp_notification(
            notification_type='evaluation_reminder',
            recipient_type='client',
            phone=self.telefono_contacto
        )
    
    # ============================================
    # OVERRIDE DE MÉTODOS EXISTENTES
    # ============================================
    @api.model
    def create(self, vals):
        """Override para enviar notificaciones al crear"""
        record = super(CopierServiceRequest, self).create(vals)
        
        # Notificar a soporte
        try:
            record._notify_support_new_request()
        except Exception as e:
            _logger.error("Error notificando soporte por WhatsApp: %s", str(e))
        
        # Notificar al cliente
        try:
            record._notify_client_request_received()
        except Exception as e:
            _logger.error("Error notificando cliente por WhatsApp: %s", str(e))
        
        return record
    
    def action_confirmar_visita(self):
        """Override para notificar técnico asignado"""
        res = super(CopierServiceRequest, self).action_confirmar_visita()
        
        try:
            self._notify_technician_assigned()
        except Exception as e:
            _logger.error("Error notificando técnico asignado por WhatsApp: %s", str(e))
        
        return res
    
    def action_iniciar_ruta(self):
        """Override para notificar técnico en camino"""
        res = super(CopierServiceRequest, self).action_iniciar_ruta()
        
        try:
            self._notify_technician_on_route()
        except Exception as e:
            _logger.error("Error notificando técnico en ruta por WhatsApp: %s", str(e))
        
        return res
    
    def action_iniciar_servicio(self):
        """Override para notificar servicio iniciado"""
        res = super(CopierServiceRequest, self).action_iniciar_servicio()
        
        try:
            self._notify_service_started()
        except Exception as e:
            _logger.error("Error notificando servicio iniciado por WhatsApp: %s", str(e))
        
        return res
    
    def action_completar_servicio(self):
        """Override para notificar servicio completado"""
        res = super(CopierServiceRequest, self).action_completar_servicio()
        
        try:
            self._notify_service_completed()
        except Exception as e:
            _logger.error("Error notificando servicio completado por WhatsApp: %s", str(e))
        
        return res
    
    # ============================================
    # ACCIÓN MANUAL PARA VER NOTIFICACIONES
    # ============================================
    def action_view_whatsapp_notifications(self):
        """Abrir vista de notificaciones WhatsApp"""
        self.ensure_one()
        
        return {
            'name': _('Notificaciones WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.service.notification',
            'view_mode': 'list,form',
            'domain': [('service_request_id', '=', self.id)],
            'context': {'default_service_request_id': self.id}
        }


class CopierServicePauseWizard(models.TransientModel):
    """Override del wizard de pausa para notificar"""
    _inherit = 'copier.service.pause.wizard'
    
    def action_pausar(self):
        """Override para notificar pausa"""
        res = super(CopierServicePauseWizard, self).action_pausar()
        
        try:
            self.request_id._notify_service_paused()
        except Exception as e:
            _logger.error("Error notificando pausa por WhatsApp: %s", str(e))
        
        return res


class CopierServiceCancelWizard(models.TransientModel):
    """Override del wizard de cancelación para notificar"""
    _inherit = 'copier.service.cancel.wizard'
    
    def action_cancelar(self):
        """Override para notificar cancelación"""
        res = super(CopierServiceCancelWizard, self).action_cancelar()
        
        try:
            self.request_id._notify_service_cancelled()
        except Exception as e:
            _logger.error("Error notificando cancelación por WhatsApp: %s", str(e))
        
        return res


class WhatsAppTemplateTestWizard(models.TransientModel):
    _name = 'whatsapp.template.test.wizard'
    _description = 'Wizard para Enviar Mensaje de Prueba de Plantilla'
    
    template_id = fields.Many2one(
        'whatsapp.service.template',
        string='Plantilla',
        required=True,
        readonly=True
    )
    
    phone = fields.Char(
        string='Número de Teléfono',
        required=True,
        default='+51 ',
        help='Ingresa el número con código de país (ejemplo: +51 987654321)'
    )
    
    template_text = fields.Text(
        string='Mensaje de Prueba',
        required=True,
        help='Este es el mensaje que se enviará con los datos de ejemplo'
    )
    
    def action_send_test(self):
        """Enviar mensaje de prueba"""
        self.ensure_one()
        
        clean_phone = self.env['whatsapp.config'].clean_phone_number(self.phone)
        
        if not clean_phone:
            raise ValidationError(_(
                'Número de teléfono inválido.\n'
                'Formato correcto: +51987654321 o 51987654321'
            ))
        
        try:
            config = self.env['whatsapp.config'].get_active_config()
            
            if not config.is_connected:
                connection = config.check_connection(silent=True)
                if not connection.get('connected'):
                    raise ValidationError(_('WhatsApp no está conectado. Por favor escanea el código QR.'))
            
            if config.auto_verify_numbers:
                exists = config.verify_number(clean_phone)
                if not exists:
                    raise ValidationError(_(
                        'El número %s no existe en WhatsApp.\n'
                        'Verifica que el número sea correcto y tenga WhatsApp activo.'
                    ) % self.phone)
            
            result = config.send_message(clean_phone, self.template_text)
            
            if result['success']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'✅ Mensaje de prueba enviado exitosamente a {self.phone}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise ValidationError(_(
                    '❌ Error al enviar mensaje de prueba:\n%s'
                ) % result['error'])
                
        except ValidationError:
            raise
        except Exception as e:
            _logger.exception("Error enviando mensaje de prueba: %s", str(e))
            raise ValidationError(_(
                '❌ Error inesperado al enviar mensaje:\n%s'
            ) % str(e))


# ============================================
# WIZARD: AYUDA DE VARIABLES
# ============================================
class WhatsAppTemplateVariablesWizard(models.TransientModel):
    _name = 'whatsapp.template.variables.wizard'
    _description = 'Ayuda de Variables para Plantillas WhatsApp'
    
    variables_info = fields.Html(
        string='Variables Disponibles',
        default=lambda self: self._get_variables_html(),
        readonly=True
    )
    
    def _get_variables_html(self):
        """Generar HTML con información de todas las variables"""
        return """
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h3 style="color: #25D366; margin-bottom: 20px;">
                📱 Variables Disponibles para Plantillas WhatsApp
            </h3>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="color: #333; margin-top: 0;">💡 ¿Cómo usar las variables?</h4>
                <p style="color: #666;">
                    Escribe las variables entre llaves <code>{}</code> en tu plantilla. 
                    Se reemplazarán automáticamente con los datos reales al enviar el mensaje.
                </p>
                <p style="color: #666; margin-bottom: 0;">
                    <strong>Ejemplo:</strong> <code>Hola {contact}, tu solicitud {number} fue recibida.</code>
                </p>
            </div>

            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #25D366;">
                <h4 style="color: #1b5e20; margin-top: 0;">🕐 Zona Horaria</h4>
                <p style="color: #2e7d32; margin-bottom: 0;">
                    Todas las fechas y horas se muestran en <strong>hora peruana (UTC-5)</strong> automáticamente.
                </p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #25D366; color: white;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Variable</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Descripción</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Ejemplo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">📋 Solicitud</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{number}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Número de la solicitud</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">ST-2024-001</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{priority}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Prioridad</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Alta</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{problem}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Tipo de problema reportado</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Atasco de papel</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">👤 Cliente</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{client}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Nombre del cliente (empresa)</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Empresa Demo S.A.C.</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{contact}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Persona de contacto</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">María García</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{phone}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Teléfono de contacto</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">+51 987 654 321</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">🖨️ Equipo</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{equipment}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Modelo del equipo</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Ricoh MP C3004</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{serie}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Serie del equipo</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">E1234567890</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{location}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Ubicación del equipo</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Av. Javier Prado 123</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{sede}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Sede del equipo</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Sede Principal</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">👨‍🔧 Técnico</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{technician}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Nombre del técnico</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Juan Pérez</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{technician_phone}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Teléfono del técnico</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">+51 987 654 321</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{technician_dni}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">DNI del técnico (campo VAT)</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">12345678</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">🚗 Vehículo</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{vehicle}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Info completa (marca, modelo, placa)</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Mitsubishi L200 - Placa: BTH677</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">📅 Fechas (Hora Perú)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{date}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Fecha programada del servicio</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">15/01/2026 14:30</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{time}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Fecha/hora actual del envío</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">15/01/2026 16:45</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{time_remaining}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Tiempo restante SLA</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">1.5 horas</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">📝 Contenido</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{work_done}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Trabajo realizado</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Se realizó limpieza de rodillos...</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{reason}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Motivo de pausa/cancelación</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Falta de repuestos</td>
                    </tr>

                    <tr style="background-color: #e8f5e9;">
                        <td colspan="3" style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">🔗 URLs</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{tracking_url}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">URL de seguimiento público</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">https://...track/abc123</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{evaluation_url}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">URL de evaluación pública</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">https://...evaluate/xyz789</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">⚠️ Importante</h4>
                <ul style="color: #856404; margin-bottom: 0;">
                    <li>Las variables son <strong>case-sensitive</strong> (distinguen mayúsculas/minúsculas)</li>
                    <li>Usa exactamente el nombre mostrado en la tabla</li>
                    <li>Si una variable no está disponible, se mostrará "N/A" o "No disponible"</li>
                    <li>Todas las fechas se muestran en <strong>hora peruana (UTC-5)</strong></li>
                    <li>El DNI del técnico se obtiene del campo <strong>VAT</strong> de res.partner</li>
                    <li>El vehículo muestra marca, modelo y placa combinados</li>
                </ul>
            </div>
            
            <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #17a2b8;">
                <h4 style="color: #0c5460; margin-top: 0;">💡 Formato WhatsApp</h4>
                <ul style="color: #0c5460; margin-bottom: 0;">
                    <li>Usa <code>*texto*</code> para <strong>negritas</strong></li>
                    <li>Usa <code>_texto_</code> para <em>cursivas</em></li>
                    <li>Usa <code>~texto~</code> para <del>tachado</del></li>
                    <li>Usa <code>```texto```</code> para código/monoespaciado</li>
                </ul>
            </div>
        </div>
        """