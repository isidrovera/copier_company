import logging
from datetime import timedelta, datetime
import pytz
import requests
import json
import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class RemoteAssistanceRequest(models.Model):
    _name = 'remote.assistance.request'
    _description = 'Solicitudes de Asistencia Remota'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'
    _rec_name = 'display_name'

    # Campo computed para el nombre del registro
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('equipment_id', 'contact_name', 'assistance_type')
    def _compute_display_name(self):
        """Calcula el nombre a mostrar del registro"""
        _logger.info("=== INICIANDO _compute_display_name para asistencia remota ===")
        for record in self:
            try:
                equipment_name = record.equipment_id.name.name if record.equipment_id and record.equipment_id.name else 'Sin equipo'
                contact_name = record.contact_name or 'Sin contacto'
                assistance_type = dict(record._fields['assistance_type'].selection).get(record.assistance_type, 'Sin tipo')
                
                record.display_name = f"{equipment_name} - {contact_name} ({assistance_type})"
                _logger.info("Display name calculado para registro ID %s: %s", record.id, record.display_name)
            except Exception as e:
                _logger.error("Error calculando display_name para registro ID %s: %s", record.id, str(e))
                record.display_name = f"Solicitud {record.id or 'Nueva'}"

    # Campos básicos
    equipment_id = fields.Many2one(
        'copier.company',
        string='Equipo',
        required=True,
        tracking=True,
        help='Equipo para el cual se solicita asistencia remota'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='equipment_id.cliente_id',
        store=True,
        readonly=True
    )
    
    request_date = fields.Datetime(
        string='Fecha de Solicitud',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    secuencia = fields.Char(
        string='Número de Solicitud',
        default='New',
        copy=False,
        required=True,
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Sobrescribe create para asignar secuencia automática"""
        _logger.info("=== INICIANDO create para RemoteAssistanceRequest ===")
        _logger.info("Valores recibidos: %s", vals)
        
        try:
            # Asignar secuencia si es nueva
            if vals.get('secuencia', 'New') == 'New':
                vals['secuencia'] = self.env['ir.sequence'].next_by_code('remote.assistance.request') or 'RAR/001'
                _logger.info("Secuencia asignada: %s", vals['secuencia'])
            
            # Crear el registro
            result = super(RemoteAssistanceRequest, self).create(vals)
            _logger.info("Solicitud de asistencia remota creada: ID=%s, Secuencia=%s", result.id, result.secuencia)
            
            # Crear nota en el chatter
            try:
                result.message_post(
                    body=f"""
                    🆕 <b>Nueva Solicitud de Asistencia Remota</b><br/>
                    • <b>Equipo:</b> {result.equipment_id.name.name if result.equipment_id.name else 'Sin nombre'}<br/>
                    • <b>Serie:</b> {result.equipment_id.serie_id or 'Sin serie'}<br/>
                    • <b>Cliente:</b> {result.partner_id.name if result.partner_id else 'Sin cliente'}<br/>
                    • <b>Contacto:</b> {result.contact_name}<br/>
                    • <b>Tipo:</b> {dict(result._fields['assistance_type'].selection).get(result.assistance_type, 'Sin tipo')}<br/>
                    • <b>Estado:</b> Pendiente
                    """,
                    message_type='notification'
                )
                _logger.info("Nota creada en chatter para solicitud ID %s", result.id)
            except Exception as e:
                _logger.error("Error creando nota en chatter: %s", str(e))
            
            return result
            
        except Exception as e:
            _logger.exception("Error en create de RemoteAssistanceRequest: %s", str(e))
            raise

    # Información del contacto
    contact_name = fields.Char(
        string='Nombre de Contacto',
        required=True,
        tracking=True,
        help='Nombre completo de la persona que solicita asistencia'
    )
    
    contact_email = fields.Char(
        string='Email de Contacto',
        required=True,
        tracking=True,
        help='Email para contactar durante la asistencia'
    )
    
    contact_phone = fields.Char(
        string='Teléfono de Contacto',
        tracking=True,
        help='Teléfono para contactar si es necesario'
    )

    # Datos de acceso remoto
    anydesk_id = fields.Char(
        string='ID de AnyDesk',
        tracking=True,
        help='ID de AnyDesk del equipo (ej: 123456789)'
    )
    
    username = fields.Char(
        string='Usuario del Equipo',
        tracking=True,
        help='Nombre de usuario para acceder al equipo'
    )
    
    user_password = fields.Char(
        string='Clave de Usuario',
        help='Contraseña del usuario (se almacena de forma segura)'
    )

    # Para escáneres por correo
    scanner_email = fields.Char(
        string='Email del Escáner',
        tracking=True,
        help='Dirección de email configurada en el escáner'
    )
    
    scanner_password = fields.Char(
        string='Clave del Email del Escáner',
        help='Contraseña del email del escáner'
    )

    # Detalles del problema
    problem_description = fields.Text(
        string='Descripción del Problema',
        required=True,
        tracking=True,
        help='Descripción detallada del problema que requiere asistencia'
    )
    
    assistance_type = fields.Selection([
        ('general', 'Asistencia General'),
        ('scanner_email', 'Configuración Escáner por Email'),
        ('network', 'Problemas de Red'),
        ('drivers', 'Instalación de Drivers'),
        ('printing', 'Problemas de Impresión'),
        ('scanning', 'Problemas de Escaneo'),
        ('maintenance', 'Mantenimiento Preventivo'),
        ('other', 'Otro')
    ], string='Tipo de Asistencia', required=True, tracking=True, default='general')

    # Estado y gestión
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('scheduled', 'Programado'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Fallido')
    ], string='Estado', default='pending', tracking=True)

    priority = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='medium', tracking=True)

    # Técnico asignado
    technician_id = fields.Many2one(
        'res.users',
        string='Técnico Asignado',
        tracking=True,
        help='Técnico responsable de brindar la asistencia'
    )

    # Programación
    scheduled_datetime = fields.Datetime(
        string='Fecha/Hora Programada',
        tracking=True,
        help='Fecha y hora programada para la asistencia'
    )
    
    estimated_duration = fields.Float(
        string='Duración Estimada (horas)',
        default=1.0,
        tracking=True,
        help='Tiempo estimado para completar la asistencia'
    )

    # Seguimiento de la sesión
    session_start_time = fields.Datetime(
        string='Inicio de Sesión',
        tracking=True
    )
    
    session_end_time = fields.Datetime(
        string='Fin de Sesión',
        tracking=True
    )
    
    actual_duration = fields.Float(
        string='Duración Real (horas)',
        compute='_compute_actual_duration',
        store=True,
        help='Duración real de la sesión de asistencia'
    )

    @api.depends('session_start_time', 'session_end_time')
    def _compute_actual_duration(self):
        """Calcula la duración real de la sesión"""
        _logger.info("=== INICIANDO _compute_actual_duration ===")
        for record in self:
            try:
                if record.session_start_time and record.session_end_time:
                    delta = record.session_end_time - record.session_start_time
                    record.actual_duration = delta.total_seconds() / 3600.0  # Convertir a horas
                    _logger.info("Duración calculada para solicitud %s: %.2f horas", record.secuencia, record.actual_duration)
                else:
                    record.actual_duration = 0.0
                    _logger.info("Duración no calculable para solicitud %s (faltan fechas)", record.secuencia)
            except Exception as e:
                _logger.error("Error calculando duración para solicitud %s: %s", record.secuencia, str(e))
                record.actual_duration = 0.0

    # Notas y seguimiento
    internal_notes = fields.Text(
        string='Notas del Técnico',
        help='Notas internas para el equipo técnico'
    )
    
    remote_session_notes = fields.Text(
        string='Notas de la Sesión Remota',
        tracking=True,
        help='Detalles de lo realizado durante la sesión remota'
    )
    
    solution_description = fields.Text(
        string='Descripción de la Solución',
        tracking=True,
        help='Descripción de la solución implementada'
    )

    # Campos de auditoría
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
    )
    
    estimated_cost = fields.Monetary(
        string='Costo Estimado',
        currency_field='currency_id',
        help='Costo estimado de la asistencia (si aplica)'
    )
    
    actual_cost = fields.Monetary(
        string='Costo Real',
        currency_field='currency_id',
        tracking=True,
        help='Costo real de la asistencia'
    )

    # Campos relacionados para facilitar búsquedas
    equipment_serie = fields.Char(
        string='Serie del Equipo',
        related='equipment_id.serie_id',
        store=True,
        readonly=True
    )
    
    equipment_location = fields.Char(
        string='Ubicación del Equipo',
        related='equipment_id.ubicacion',
        store=True,
        readonly=True
    )

    # Métodos para cambiar estado
    def action_schedule(self):
        """Marca la solicitud como programada"""
        _logger.info("=== INICIANDO action_schedule para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'scheduled'
            self.message_post(
                body=f"📅 Solicitud programada para {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M') if self.scheduled_datetime else 'fecha por definir'}",
                message_type='notification'
            )
            self.send_status_update_whatsapp(
                f"📅 *Su solicitud ha sido PROGRAMADA*\n\n"
                f"Fecha programada: {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M') if self.scheduled_datetime else 'Por confirmar'}\n"
                f"Nuestro técnico se pondrá en contacto con usted."
            )
            _logger.info("Solicitud %s marcada como programada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_schedule para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_start_session(self):
        """Inicia la sesión de asistencia remota"""
        _logger.info("=== INICIANDO action_start_session para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'in_progress'
            self.session_start_time = fields.Datetime.now()
            self.message_post(
                body=f"🚀 Sesión de asistencia remota iniciada a las {self.session_start_time.strftime('%d/%m/%Y %H:%M')}",
                message_type='notification'
            )
            self.send_status_update_whatsapp(
                f"🚀 *Sesión de asistencia INICIADA*\n\n"
                f"Hora de inicio: {self.session_start_time.strftime('%d/%m/%Y %H:%M')}\n"
                f"Nuestro técnico está trabajando en su equipo."
            )
            _logger.info("Sesión iniciada para solicitud %s", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_start_session para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_end_session(self):
        """Finaliza la sesión de asistencia remota"""
        _logger.info("=== INICIANDO action_end_session para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.session_end_time = fields.Datetime.now()
            duration_text = f"{self.actual_duration:.2f} horas" if self.actual_duration else "duración no calculable"
            self.message_post(
                body=f"✅ Sesión de asistencia remota finalizada a las {self.session_end_time.strftime('%d/%m/%Y %H:%M')} (Duración: {duration_text})",
                message_type='notification'
            )
            self.send_status_update_whatsapp(
                f"⏰ *Sesión de asistencia FINALIZADA*\n\n"
                f"Hora de finalización: {self.session_end_time.strftime('%d/%m/%Y %H:%M')}\n"
                f"Duración: {duration_text}\n"
                f"La asistencia técnica ha sido completada."
            )
            _logger.info("Sesión finalizada para solicitud %s, duración: %s", self.secuencia, duration_text)
        except Exception as e:
            _logger.exception("Error en action_end_session para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_complete(self):
        """Marca la solicitud como completada"""
        _logger.info("=== INICIANDO action_complete para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            if not self.session_end_time:
                self.session_end_time = fields.Datetime.now()
            self.state = 'completed'
            self.message_post(
                body="✅ Asistencia remota completada exitosamente",
                message_type='notification'
            )
            self.send_status_update_whatsapp(
                f"✅ *Su solicitud ha sido COMPLETADA*\n\n"
                f"La asistencia remota se realizó exitosamente.\n"
                f"Gracias por confiar en nuestros servicios."
            )
            _logger.info("Solicitud %s marcada como completada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_complete para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_cancel(self):
        """Cancela la solicitud de asistencia"""
        _logger.info("=== INICIANDO action_cancel para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'cancelled'
            self.message_post(
                body="❌ Solicitud de asistencia remota cancelada",
                message_type='notification'
            )
            self.send_status_update_whatsapp(
                f"❌ *Su solicitud ha sido CANCELADA*\n\n"
                f"La solicitud de asistencia remota fue cancelada.\n"
                f"Para más información, puede contactarnos directamente."
            )
            _logger.info("Solicitud %s cancelada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_cancel para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_reset_to_pending(self):
        """Regresa la solicitud a estado pendiente"""
        _logger.info("=== INICIANDO action_reset_to_pending para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'pending'
            self.session_start_time = False
            self.session_end_time = False
            self.message_post(
                body="🔄 Solicitud regresada a estado pendiente",
                message_type='notification'
            )
            _logger.info("Solicitud %s regresada a pendiente", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_reset_to_pending para solicitud %s: %s", self.secuencia, str(e))
            raise

    @api.model
    def create_from_public_form(self, vals):
        """Método específico para crear desde formulario público"""
        _logger.info("=== INICIANDO create_from_public_form ===")
        _logger.info("Valores del formulario público: %s", vals)
        
        try:
            # Validaciones específicas para formulario público
            required_fields = ['equipment_id', 'contact_name', 'contact_email', 'problem_description', 'assistance_type']
            missing_fields = [field for field in required_fields if not vals.get(field)]
            
            if missing_fields:
                error_msg = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # Buscar o crear partner basado en email
            partner = self.env['res.partner'].sudo().search([('email', '=', vals['contact_email'])], limit=1)
            if partner:
                _logger.info("Partner encontrado para email %s: ID=%s", vals['contact_email'], partner.id)
            else:
                try:
                    partner = self.env['res.partner'].sudo().create({
                        'name': vals['contact_name'],
                        'email': vals['contact_email'],
                        'phone': vals.get('contact_phone', ''),
                        'is_company': False
                    })
                    _logger.info("Nuevo partner creado: ID=%s", partner.id)
                except Exception as e:
                    _logger.error("Error creando partner: %s", str(e))
            
            # Crear la solicitud
            assistance_request = self.create(vals)
            _logger.info("Solicitud de asistencia remota creada desde formulario público: ID=%s", assistance_request.id)
            
            # Crear actividad para el equipo técnico
            try:
                self._create_technical_activity(assistance_request)
            except Exception as e:
                _logger.error("Error creando actividad técnica: %s", str(e))
            
            return assistance_request
            
        except Exception as e:
            _logger.exception("Error en create_from_public_form: %s", str(e))
            raise

    def _create_technical_activity(self, assistance_request):
        """Crea una actividad para el equipo técnico"""
        _logger.info("=== INICIANDO _create_technical_activity para solicitud %s ===", assistance_request.secuencia)
        
        try:
            # Buscar usuarios del grupo técnico o asignar al técnico si ya está definido
            if assistance_request.technician_id:
                assignee = assistance_request.technician_id
                _logger.info("Asignando actividad al técnico definido: %s", assignee.name)
            else:
                # Buscar grupo técnico (esto depende de cómo tengas configurados los grupos)
                tech_group = self.env.ref('base.group_user', False)  # Ajustar según tu configuración
                if tech_group and tech_group.users:
                    assignee = tech_group.users[0]  # Asignar al primer usuario del grupo
                    _logger.info("Asignando actividad al primer usuario del grupo técnico: %s", assignee.name)
                else:
                    assignee = self.env.user
                    _logger.info("Asignando actividad al usuario actual: %s", assignee.name)
            
            activity_vals = {
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Nueva Solicitud de Asistencia Remota - {assistance_request.secuencia}',
                'note': f'''
                    🖥️ <b>Nueva Solicitud de Asistencia Remota</b><br/><br/>
                    
                    <b>Equipo:</b> {assistance_request.equipment_id.name.name if assistance_request.equipment_id.name else 'Sin nombre'}<br/>
                    <b>Serie:</b> {assistance_request.equipment_id.serie_id or 'Sin serie'}<br/>
                    <b>Cliente:</b> {assistance_request.partner_id.name if assistance_request.partner_id else 'Sin cliente'}<br/>
                    <b>Ubicación:</b> {assistance_request.equipment_location or 'Sin ubicación'}<br/><br/>
                    
                    <b>Contacto:</b> {assistance_request.contact_name}<br/>
                    <b>Email:</b> {assistance_request.contact_email}<br/>
                    <b>Teléfono:</b> {assistance_request.contact_phone or 'No proporcionado'}<br/><br/>
                    
                    <b>Tipo de Asistencia:</b> {dict(assistance_request._fields['assistance_type'].selection).get(assistance_request.assistance_type, 'Sin tipo')}<br/>
                    <b>Prioridad:</b> {dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media')}<br/><br/>
                    
                    <b>Descripción del Problema:</b><br/>
                    {assistance_request.problem_description}<br/><br/>
                    
                    <b>Datos de Acceso:</b><br/>
                    {'• AnyDesk ID: ' + assistance_request.anydesk_id + '<br/>' if assistance_request.anydesk_id else ''}
                    {'• Usuario: ' + assistance_request.username + '<br/>' if assistance_request.username else ''}
                    {'• Email Escáner: ' + assistance_request.scanner_email + '<br/>' if assistance_request.scanner_email else ''}
                    
                    Por favor, revisar y programar la asistencia remota.
                ''',
                'user_id': assignee.id,
                'res_id': assistance_request.id,
                'res_model_id': self.env['ir.model']._get('remote.assistance.request').id,
                'date_deadline': fields.Date.today() + timedelta(days=1)  # Plazo de 1 día
            }
            
            activity = self.env['mail.activity'].create(activity_vals)
            _logger.info("Actividad técnica creada: ID=%s para usuario %s", activity.id, assignee.name)
            
        except Exception as e:
            _logger.exception("Error en _create_technical_activity: %s", str(e))
            raise

    # Constrains para validaciones
    @api.constrains('contact_email')
    def _check_contact_email(self):
        """Valida el formato del email de contacto"""
        for record in self:
            if record.contact_email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.contact_email):
                    _logger.error("Email inválido para solicitud %s: %s", record.secuencia, record.contact_email)
                    raise ValidationError(f"El email '{record.contact_email}' no tiene un formato válido.")

    @api.constrains('scheduled_datetime')
    def _check_scheduled_datetime(self):
        """Valida que la fecha programada no sea en el pasado"""
        for record in self:
            if record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                _logger.error("Fecha programada en el pasado para solicitud %s: %s", record.secuencia, record.scheduled_datetime)
                raise ValidationError("La fecha programada no puede ser en el pasado.")

    @api.constrains('session_start_time', 'session_end_time')
    def _check_session_times(self):
        """Valida que la hora de fin sea posterior a la de inicio"""
        for record in self:
            if record.session_start_time and record.session_end_time:
                if record.session_end_time <= record.session_start_time:
                    _logger.error("Horas de sesión inválidas para solicitud %s: inicio=%s, fin=%s", 
                                record.secuencia, record.session_start_time, record.session_end_time)
                    raise ValidationError("La hora de fin de sesión debe ser posterior a la hora de inicio.")

    contact_phone_clean = fields.Char(
        string='Teléfono Limpio',
        compute='_compute_contact_phone_clean',
        store=True,
        help='Número de teléfono formateado para WhatsApp'
    )

    @api.depends('contact_phone')
    def _compute_contact_phone_clean(self):
        """Formatea el número de teléfono para WhatsApp"""
        for record in self:
            if record.contact_phone:
                phone = record.contact_phone.replace('+', '').replace(' ', '').replace('-', '')
                # Remover cualquier carácter que no sea número
                phone = ''.join(filter(str.isdigit, phone))
                
                # Si el número no empieza con '51' y tiene 9 dígitos, agregar '51'
                if not phone.startswith('51') and len(phone) == 9:
                    phone = '51' + phone
                record.contact_phone_clean = phone
            else:
                record.contact_phone_clean = ''

    # MÉTODOS WHATSAPP a agregar
    def send_whatsapp_message(self, phone, message):
        """Envía mensaje de WhatsApp usando la API corporativa"""
        try:
            url = 'https://whatsappapi.copiercompanysac.com/api/message'
            data = {
                'phone': phone,
                'message': message
            }
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, json=data)
            
            _logger.info("WhatsApp API - Código de estado: %s", response.status_code)
            _logger.info("WhatsApp API - Respuesta: %s", response.text)
            
            try:
                response_json = response.json()
                _logger.info("WhatsApp API - Respuesta JSON: %s", response_json)
                return response_json
            except json.JSONDecodeError as e:
                error_msg = f"La respuesta no contiene un JSON válido: {str(e)}"
                _logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            _logger.exception("Error enviando mensaje WhatsApp: %s", str(e))
            return {"error": str(e)}

    def send_whatsapp_confirmation(self):
        """Envía confirmación por WhatsApp al cliente que solicitó asistencia remota"""
        self.ensure_one()
        
        if not self.contact_phone_clean:
            _logger.warning("No hay número de teléfono válido para enviar WhatsApp - Solicitud: %s", self.secuencia)
            return False
        
        try:
            # Determinar saludo según la hora
            lima_tz = pytz.timezone('America/Lima')
            current_time = datetime.now(lima_tz)
            current_hour = current_time.hour

            if 5 <= current_hour < 12:
                saludo = "👋 Buenos días"
            elif 12 <= current_hour < 18:
                saludo = "👋 Buenas tardes"
            else:
                saludo = "👋 Buenas noches"

            # Mapear tipos de asistencia para el mensaje
            assistance_names = {
                'general': 'Asistencia General',
                'scanner_email': 'Configuración Escáner por Email',
                'network': 'Problemas de Red',
                'drivers': 'Instalación de Drivers',
                'printing': 'Problemas de Impresión',
                'scanning': 'Problemas de Escaneo',
                'maintenance': 'Mantenimiento Preventivo',
                'other': 'Otro'
            }
            
            assistance_name = assistance_names.get(self.assistance_type, 'Asistencia Técnica')
            
            # Mapear prioridad
            priority_names = {
                'low': 'Baja',
                'medium': 'Media',
                'high': 'Alta',
                'urgent': 'Urgente'
            }
            
            priority_name = priority_names.get(self.priority, 'Media')
            equipment_name = self.equipment_id.name.name if self.equipment_id and self.equipment_id.name else 'Sin especificar'
            serie = self.equipment_id.serie_id or 'Sin serie'

            message = (
                f"*🏢 Copier Company*\n\n"
                f"{saludo}, {self.contact_name}.\n\n"
                f"Hemos recibido exitosamente su solicitud de asistencia remota:\n\n"
                f"📋 *Número de Solicitud:* {self.secuencia}\n"
                f"🖨️ *Equipo:* {equipment_name}\n"
                f"🔢 *Serie:* {serie}\n"
                f"🛠️ *Tipo de Asistencia:* {assistance_name}\n"
                f"🚨 *Prioridad:* {priority_name}\n\n"
                f"Nuestro equipo técnico revisará su solicitud y se pondrá en contacto con usted para programar la sesión de asistencia remota.\n\n"
                f"Recibirá actualizaciones del estado de su solicitud en: {self.contact_email}\n\n"
                f"Gracias por confiar en Copier Company.\n\n"
                f"Atentamente,\n"
                f"📞 Soporte Técnico Copier Company\n"
                f"☎️ Tel: +51975399303\n"
                f"📧 Email: info@copiercompanysac.com"
            )

            # Enviar mensaje
            response = self.send_whatsapp_message(self.contact_phone_clean, message)
            
            if response and not response.get('error'):
                # Crear nota en el chatter si el envío fue exitoso
                self.message_post(
                    body=f"✅ Confirmación WhatsApp enviada a {self.contact_phone_clean}",
                    message_type='notification'
                )
                _logger.info("WhatsApp de confirmación enviado exitosamente - Solicitud: %s, Teléfono: %s", 
                        self.secuencia, self.contact_phone_clean)
                return True
            else:
                error_msg = response.get('error', 'Error desconocido') if response else 'Sin respuesta'
                self.message_post(
                    body=f"❌ Error enviando WhatsApp a {self.contact_phone_clean}: {error_msg}",
                    message_type='notification'
                )
                _logger.error("Error enviando WhatsApp - Solicitud: %s, Error: %s", self.secuencia, error_msg)
                return False
                
        except Exception as e:
            _logger.exception("Error en send_whatsapp_confirmation - Solicitud: %s", self.secuencia)
            self.message_post(
                body=f"❌ Excepción enviando WhatsApp: {str(e)}",
                message_type='notification'
            )
            return False

    def send_status_update_whatsapp(self, status_message):
        """Envía actualización de estado por WhatsApp"""
        self.ensure_one()
        
        if not self.contact_phone_clean:
            return False
        
        try:
            lima_tz = pytz.timezone('America/Lima')
            current_time = datetime.now(lima_tz)
            current_hour = current_time.hour

            if 5 <= current_hour < 12:
                saludo = "👋 Buenos días"
            elif 12 <= current_hour < 18:
                saludo = "👋 Buenas tardes"
            else:
                saludo = "👋 Buenas noches"

            message = (
                f"*🏢 Copier Company*\n\n"
                f"{saludo}, {self.contact_name}.\n\n"
                f"Actualización de su solicitud de asistencia remota:\n\n"
                f"📋 *Solicitud:* {self.secuencia}\n"
                f"🖨️ *Equipo:* {self.equipment_id.name.name if self.equipment_id.name else 'Sin especificar'}\n\n"
                f"{status_message}\n\n"
                f"Gracias por su confianza.\n\n"
                f"Atentamente,\n"
                f"📞 Soporte Técnico Copier Company\n"
                f"☎️ Tel: +51975399303"
            )

            response = self.send_whatsapp_message(self.contact_phone_clean, message)
            
            if response and not response.get('error'):
                self.message_post(
                    body=f"✅ Actualización WhatsApp enviada: {status_message}",
                    message_type='notification'
                )
                return True
            else:
                self.message_post(
                    body=f"❌ Error enviando actualización WhatsApp",
                    message_type='notification'
                )
                return False
                
        except Exception as e:
            _logger.exception("Error enviando actualización WhatsApp: %s", str(e))
            return False

    # MODIFICAR EL MÉTODO CREATE EXISTENTE para agregar WhatsApp
    @api.model
    def create(self, vals):
        """Sobrescribe create para asignar secuencia automática y enviar confirmación WhatsApp"""
        _logger.info("=== INICIANDO create para RemoteAssistanceRequest ===")
        _logger.info("Valores recibidos: %s", vals)
        
        try:
            # Asignar secuencia si es nueva
            if vals.get('secuencia', 'New') == 'New':
                vals['secuencia'] = self.env['ir.sequence'].next_by_code('remote.assistance.request') or 'RAR/001'
                _logger.info("Secuencia asignada: %s", vals['secuencia'])
            
            # Crear el registro
            result = super(RemoteAssistanceRequest, self).create(vals)
            _logger.info("Solicitud de asistencia remota creada: ID=%s, Secuencia=%s", result.id, result.secuencia)
            
            # Crear nota en el chatter
            try:
                result.message_post(
                    body=f"""
                    🆕 <b>Nueva Solicitud de Asistencia Remota</b><br/>
                    • <b>Equipo:</b> {result.equipment_id.name.name if result.equipment_id.name else 'Sin nombre'}<br/>
                    • <b>Serie:</b> {result.equipment_id.serie_id or 'Sin serie'}<br/>
                    • <b>Cliente:</b> {result.partner_id.name if result.partner_id else 'Sin cliente'}<br/>
                    • <b>Contacto:</b> {result.contact_name}<br/>
                    • <b>Tipo:</b> {dict(result._fields['assistance_type'].selection).get(result.assistance_type, 'Sin tipo')}<br/>
                    • <b>Estado:</b> Pendiente
                    """,
                    message_type='notification'
                )
                _logger.info("Nota creada en chatter para solicitud ID %s", result.id)
            except Exception as e:
                _logger.error("Error creando nota en chatter: %s", str(e))
            
            # NUEVA LÍNEA: Enviar confirmación WhatsApp al cliente
            try:
                result.send_whatsapp_confirmation()
            except Exception as e:
                _logger.error("Error enviando confirmación WhatsApp: %s", str(e))
                # No interrumpir el proceso si falla el WhatsApp
            
            return result
            
        except Exception as e:
            _logger.exception("Error en create de RemoteAssistanceRequest: %s", str(e))
            raise