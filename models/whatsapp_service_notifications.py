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
            
            # ✅ LIMPIAR NÚMERO (forma recomendada)
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
            
            # Variables de ejemplo
            sample_variables = {
                'number': 'ST-2024-001',
                'client': 'Empresa Demo S.A.C.',
                'equipment': 'Ricoh MP C3004',
                'serie': 'E1234567890',
                'location': 'Av. Javier Prado 123, Piso 5, Oficina 501',
                'problem': 'Atasco de papel',
                'priority': 'Alta',
                'technician': 'Juan Pérez',
                'date': '15/01/2026 14:30',
                'contact': 'María García',
                'phone': '+51 987 654 321',
                'work_done': 'Se realizó limpieza de rodillos, ajuste de sensores y pruebas de impresión. Equipo funcionando correctamente.',
                'reason': 'Falta de repuestos en stock',
                'time': '15/01/2026 16:45',
                'time_remaining': '1.5 horas',
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
    # MÉTODOS DE NOTIFICACIÓN WHATSAPP
    # ============================================
    
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
        
        # ✅ LIMPIAR NÚMERO (forma recomendada)
        clean_phone = self.env['whatsapp.config'].clean_phone_number(self.phone)
        
        if not clean_phone:
            raise ValidationError(_(
                'Número de teléfono inválido.\n'
                'Formato correcto: +51987654321 o 51987654321'
            ))
        
        try:
            # Obtener configuración activa
            config = self.env['whatsapp.config'].get_active_config()
            
            # Verificar conexión
            if not config.is_connected:
                connection = config.check_connection(silent=True)
                if not connection.get('connected'):
                    raise ValidationError(_('WhatsApp no está conectado. Por favor escanea el código QR.'))
            
            # Verificar número (opcional)
            if config.auto_verify_numbers:
                exists = config.verify_number(clean_phone)
                if not exists:
                    raise ValidationError(_(
                        'El número %s no existe en WhatsApp.\n'
                        'Verifica que el número sea correcto y tenga WhatsApp activo.'
                    ) % self.phone)
            
            # Enviar mensaje
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
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #25D366; color: white;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Variable</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Descripción</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Ejemplo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{number}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Número de la solicitud</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">ST-2024-001</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{client}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Nombre del cliente</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Empresa Demo S.A.C.</td>
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
                        <td style="padding: 10px; border: 1px solid #ddd;">Av. Javier Prado 123, Piso 5</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{problem}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Tipo de problema reportado</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Atasco de papel</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{priority}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Prioridad de la solicitud</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Alta / Normal / Baja / Crítica</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{technician}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Nombre del técnico asignado</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Juan Pérez</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{date}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Fecha programada del servicio</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">15/01/2026 14:30</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{contact}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Nombre de la persona de contacto</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">María García</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{phone}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Teléfono de contacto</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">+51 987 654 321</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{work_done}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Descripción del trabajo realizado</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Se realizó limpieza de rodillos...</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{reason}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Motivo de pausa o cancelación</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Falta de repuestos en stock</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{time}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Fecha y hora actual del envío</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">15/01/2026 16:45</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><code>{time_remaining}</code></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">Tiempo restante para alertas SLA</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">1.5 horas</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">⚠️ Importante</h4>
                <ul style="color: #856404; margin-bottom: 0;">
                    <li>Las variables son <strong>case-sensitive</strong> (distinguen mayúsculas/minúsculas)</li>
                    <li>Usa exactamente el nombre mostrado en la tabla</li>
                    <li>No todas las variables están disponibles en todos los tipos de notificación</li>
                    <li>Si una variable no está disponible, se mostrará "N/A"</li>
                </ul>
            </div>
            
            <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #17a2b8;">
                <h4 style="color: #0c5460; margin-top: 0;">💡 Consejos</h4>
                <ul style="color: #0c5460; margin-bottom: 0;">
                    <li>Usa emojis para hacer tus mensajes más atractivos 🎉</li>
                    <li>Usa <code>*texto*</code> para <strong>negritas</strong></li>
                    <li>Usa <code>_texto_</code> para <em>cursivas</em></li>
                    <li>Usa <code>~texto~</code> para <del>tachado</del></li>
                    <li>Usa <code>```texto```</code> para código/monoespaciado</li>
                </ul>
            </div>
        </div>
        """