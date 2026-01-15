# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
                self.service_request_id.message_post(
                    body=f"""
                        📱 Notificación WhatsApp Enviada
                        
                        • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                        • Destinatario: {self.phone_number}
                        • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
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
                
                # Registrar error en chatter
                self.service_request_id.message_post(
                    body=f"""
                        ❌ Error Enviando Notificación WhatsApp
                        
                        • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                        • Destinatario: {self.phone_number}
                        • Error: {result.get('error')}
                        • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
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
            
            # Registrar excepción en chatter
            self.service_request_id.message_post(
                body=f"""
                    ❌ Excepción Enviando Notificación WhatsApp
                    
                    • Tipo: {dict(self._fields['notification_type'].selection).get(self.notification_type)}
                    • Error: {error_msg}
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
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
        {problem} - Tipo de problema
        {priority} - Prioridad
        {technician} - Nombre del técnico
        {date} - Fecha programada
        {contact} - Nombre del contacto
        {phone} - Teléfono de contacto
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
    
    _sql_constraints = [
        ('unique_type_company', 
         'UNIQUE(notification_type, company_id)', 
         'Solo puede haber una plantilla activa por tipo de notificación por compañía.')
    ]
    
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
        """Templates por defecto"""
        templates = {
            'new_request_support': """🚨 *NUEVA SOLICITUD DE SERVICIO*

📋 Número: {number}
👤 Cliente: {client}
🖨️ Equipo: {equipment} (Serie: {serie})
📍 Ubicación: {location}
🔧 Problema: {problem}
⚠️ Prioridad: {priority}

📞 Contacto: {contact}
📱 Teléfono: {phone}

⏰ Hora: {time}""",

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
📅 *Fecha programada:* {date}
🖨️ *Equipo:* {equipment}
📍 *Ubicación:* {location}

El técnico se pondrá en contacto contigo para confirmar la visita.

_¡Gracias por tu paciencia!_ 🙏""",

            'technician_on_route': """🚗 *TÉCNICO EN CAMINO*

Hola {contact},

El técnico *{technician}* está en camino a tu ubicación.

📋 Solicitud: {number}
📍 Destino: {location}
⏰ Llegada estimada: Próximamente

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

📝 *¿Nos ayudas con tu opinión?*
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
    # MÉTODOS DE NOTIFICACIÓN WHATSAPP
    # ============================================
    def _send_whatsapp_notification(self, notification_type, recipient_type, phone, **kwargs):
        """
        Método genérico para crear y enviar notificación WhatsApp
        
        Args:
            notification_type (str): Tipo de notificación
            recipient_type (str): 'support', 'client', 'technician'
            phone (str): Número de teléfono
            **kwargs: Variables adicionales para la plantilla
        """
        self.ensure_one()
        
        if not self.enable_whatsapp_notifications:
            _logger.info("Notificaciones WhatsApp deshabilitadas para solicitud %s", self.name)
            return False
        
        try:
            # Obtener plantilla
            template_text = self.env['whatsapp.service.template'].get_template(notification_type)
            
            if not template_text:
                _logger.warning("No se encontró plantilla para tipo: %s", notification_type)
                return False
            
            # Preparar variables base
            variables = {
                'number': self.name,
                'client': self.cliente_id.name if self.cliente_id else 'N/A',
                'equipment': self.modelo_maquina.name if self.modelo_maquina else 'N/A',
                'serie': self.serie_maquina or 'N/A',
                'location': self.ubicacion or 'N/A',
                'problem': self.tipo_problema_id.name if self.tipo_problema_id else 'N/A',
                'priority': dict(self._fields['prioridad'].selection).get(self.prioridad, 'Normal'),
                'technician': self.tecnico_id.name if self.tecnico_id else 'N/A',
                'date': self.fecha_programada.strftime('%d/%m/%Y %H:%M') if self.fecha_programada else 'Por confirmar',
                'contact': self.contacto or 'N/A',
                'phone': self.telefono_contacto or 'N/A',
                'time': fields.Datetime.now().strftime('%d/%m/%Y %H:%M'),
            }
            
            # Agregar variables adicionales
            variables.update(kwargs)
            
            # Formatear mensaje
            try:
                message_text = template_text.format(**variables)
            except KeyError as e:
                _logger.error("Variable faltante en plantilla: %s", str(e))
                return False
            
            # Crear registro de notificación
            notification = self.env['whatsapp.service.notification'].create({
                'service_request_id': self.id,
                'notification_type': notification_type,
                'recipient_type': recipient_type,
                'phone_number': phone,
                'message_text': message_text,
                'state': 'pending',
            })
            
            # Enviar notificación
            return notification.send_notification()
            
        except Exception as e:
            _logger.exception("Error creando notificación WhatsApp: %s", str(e))
            return False
    
    def _notify_support_new_request(self):
        """Notificar a soporte sobre nueva solicitud"""
        self.ensure_one()
        
        # Número de soporte (hardcoded o desde configuración)
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