# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime
import pytz
import requests
import json
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class RemoteAssistanceRequest(models.Model):
    _name = 'remote.assistance.request'
    _description = 'Solicitudes de Asistencia Remota'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # --------- Identidad / Display ----------
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('equipment_id', 'contact_name', 'assistance_type')
    def _compute_display_name(self):
        """Calcula el nombre a mostrar del registro"""
        for record in self:
            try:
                equipment_name = (record.equipment_id.name.name
                                  if record.equipment_id and record.equipment_id.name else 'Sin equipo')
                contact_name = record.contact_name or 'Sin contacto'
                assistance_type = dict(record._fields['assistance_type'].selection).get(record.assistance_type, 'Sin tipo')
                record.display_name = f"{equipment_name} - {contact_name} ({assistance_type})"
            except Exception:
                record.display_name = f"Solicitud {record.id or 'Nueva'}"

    # --------- Campos básicos ----------
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

    # --------- Contacto ----------
    contact_name = fields.Char(string='Nombre de Contacto', required=True, tracking=True)
    contact_email = fields.Char(string='Email de Contacto', required=True, tracking=True)
    contact_phone = fields.Char(string='Teléfono de Contacto', tracking=True)

    # --------- Acceso remoto ----------
    anydesk_id = fields.Char(string='ID de AnyDesk', tracking=True)
    username = fields.Char(string='Usuario del Equipo', tracking=True)
    user_password = fields.Char(string='Clave de Usuario', help='Contraseña del usuario (almacenada en texto).')
    scanner_email = fields.Char(string='Email del Escáner', tracking=True)
    scanner_password = fields.Char(string='Clave del Email del Escáner')

    # --------- Problema y tipo ----------
    problem_description = fields.Text(string='Descripción del Problema', required=True, tracking=True)
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

    # --------- Estado / Gestión ----------
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

    technician_id = fields.Many2one('res.users', string='Técnico Asignado', tracking=True)

    # --------- Programación ----------
    scheduled_datetime = fields.Datetime(string='Fecha/Hora Programada', tracking=True)
    estimated_duration = fields.Float(string='Duración Estimada (horas)', default=1.0, tracking=True)

    # --------- Seguimiento de sesión ----------
    session_start_time = fields.Datetime(string='Inicio de Sesión', tracking=True)
    session_end_time = fields.Datetime(string='Fin de Sesión', tracking=True)
    actual_duration = fields.Float(
        string='Duración Real (horas)',
        compute='_compute_actual_duration',
        store=True
    )

    @api.depends('session_start_time', 'session_end_time')
    def _compute_actual_duration(self):
        for record in self:
            try:
                if record.session_start_time and record.session_end_time:
                    delta = record.session_end_time - record.session_start_time
                    record.actual_duration = delta.total_seconds() / 3600.0
                else:
                    record.actual_duration = 0.0
            except Exception:
                record.actual_duration = 0.0

    # --------- Notas / Costos ----------
    internal_notes = fields.Text(string='Notas del Técnico')
    remote_session_notes = fields.Text(string='Notas de la Sesión Remota', tracking=True)
    solution_description = fields.Text(string='Descripción de la Solución', tracking=True)

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
    )
    estimated_cost = fields.Monetary(string='Costo Estimado', currency_field='currency_id')
    actual_cost = fields.Monetary(string='Costo Real', currency_field='currency_id', tracking=True)

    # --------- Atajos de búsqueda ----------
    equipment_serie = fields.Char(string='Serie del Equipo', related='equipment_id.serie_id', store=True, readonly=True)
    equipment_location = fields.Char(string='Ubicación del Equipo', related='equipment_id.ubicacion', store=True, readonly=True)

    # --------- Normalización de teléfono ----------
    contact_phone_clean = fields.Char(
        string='Teléfono Limpio',
        compute='_compute_contact_phone_clean',
        store=True,
        help='Número de teléfono formateado para WhatsApp'
    )

    @api.depends('contact_phone')
    def _compute_contact_phone_clean(self):
        for record in self:
            if record.contact_phone:
                phone = record.contact_phone.replace('+', '').replace(' ', '').replace('-', '')
                phone = ''.join(filter(str.isdigit, phone))
                if not phone.startswith('51') and len(phone) == 9:
                    phone = '51' + phone
                record.contact_phone_clean = phone
            else:
                record.contact_phone_clean = ''

    # ========= CREATE (ÚNICO) =========
    @api.model
    def create(self, vals):
        """Asigna secuencia, crea nota en chatter y envía confirmación por WhatsApp."""
        _logger.info("=== CREATE RemoteAssistanceRequest === vals=%s", vals)
        # Secuencia
        if vals.get('secuencia', 'New') == 'New':
            vals['secuencia'] = self.env['ir.sequence'].next_by_code('remote.assistance.request') or 'RAR/001'
        # Crear
        rec = super().create(vals)

        # Nota en chatter
        try:
            eq_name = rec.equipment_id.name.name if rec.equipment_id and rec.equipment_id.name else 'Sin nombre'
            serie = rec.equipment_id.serie_id or 'Sin serie'
            cliente = rec.partner_id.name if rec.partner_id else 'Sin cliente'
            tipo = dict(rec._fields['assistance_type'].selection).get(rec.assistance_type, 'Sin tipo')
            rec.message_post(
                body=(
                    "🆕 <b>Nueva Solicitud de Asistencia Remota</b><br/>"
                    f"• <b>Equipo:</b> {eq_name}<br/>"
                    f"• <b>Serie:</b> {serie}<br/>"
                    f"• <b>Cliente:</b> {cliente}<br/>"
                    f"• <b>Contacto:</b> {rec.contact_name or 'Sin contacto'}<br/>"
                    f"• <b>Tipo:</b> {tipo}<br/>"
                    "• <b>Estado:</b> Pendiente"
                ),
                message_type='notification'
            )
        except Exception as e:
            _logger.error("Error creando nota en chatter: %s", e)

        # WhatsApp (no bloqueante)
        try:
            rec.send_whatsapp_confirmation()
        except Exception as e:
            _logger.error("Error enviando confirmación WhatsApp: %s", e)

        return rec

    # ========= Acciones de estado =========
    def action_schedule(self):
        self.ensure_one()
        self.state = 'scheduled'
        self.message_post(
            body=f"📅 Solicitud programada para {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M') if self.scheduled_datetime else 'fecha por definir'}",
            message_type='notification'
        )
        self.send_status_update_whatsapp(
            "📅 *Su solicitud ha sido PROGRAMADA*\n\n"
            f"Fecha programada: {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M') if self.scheduled_datetime else 'Por confirmar'}\n"
            "Nuestro técnico se pondrá en contacto con usted."
        )

    def action_start_session(self):
        self.ensure_one()
        self.state = 'in_progress'
        self.session_start_time = fields.Datetime.now()
        self.message_post(
            body=f"🚀 Sesión de asistencia remota iniciada a las {self.session_start_time.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
        )
        self.send_status_update_whatsapp(
            "🚀 *Sesión de asistencia INICIADA*\n\n"
            f"Hora de inicio: {self.session_start_time.strftime('%d/%m/%Y %H:%M')}\n"
            "Nuestro técnico está trabajando en su equipo."
        )

    def action_end_session(self):
        self.ensure_one()
        self.session_end_time = fields.Datetime.now()
        duration_text = f"{self.actual_duration:.2f} horas" if self.actual_duration else "duración no calculable"
        self.message_post(
            body=f"✅ Sesión de asistencia remota finalizada a las {self.session_end_time.strftime('%d/%m/%Y %H:%M')} (Duración: {duration_text})",
            message_type='notification'
        )
        self.send_status_update_whatsapp(
            "⏰ *Sesión de asistencia FINALIZADA*\n\n"
            f"Hora de finalización: {self.session_end_time.strftime('%d/%m/%Y %H:%M')}\n"
            f"Duración: {duration_text}\n"
            "La asistencia técnica ha sido completada."
        )

    def action_complete(self):
        self.ensure_one()
        if not self.session_end_time:
            self.session_end_time = fields.Datetime.now()
        self.state = 'completed'
        self.message_post(body="✅ Asistencia remota completada exitosamente", message_type='notification')
        self.send_status_update_whatsapp(
            "✅ *Su solicitud ha sido COMPLETADA*\n\n"
            "La asistencia remota se realizó exitosamente.\n"
            "Gracias por confiar en nuestros servicios."
        )

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'
        self.message_post(body="❌ Solicitud de asistencia remota cancelada", message_type='notification')
        self.send_status_update_whatsapp(
            "❌ *Su solicitud ha sido CANCELADA*\n\n"
            "La solicitud de asistencia remota fue cancelada.\n"
            "Para más información, puede contactarnos directamente."
        )

    def action_reset_to_pending(self):
        self.ensure_one()
        self.state = 'pending'
        self.session_start_time = False
        self.session_end_time = False
        self.message_post(body="🔄 Solicitud regresada a estado pendiente", message_type='notification')

    # ========= Creación desde portal =========
    @api.model
    def create_from_public_form(self, vals):
        """Crear desde formulario público + actividad para técnicos."""
        required = ['equipment_id', 'contact_name', 'contact_email', 'problem_description', 'assistance_type']
        missing = [f for f in required if not vals.get(f)]
        if missing:
            raise ValidationError(f"Campos requeridos faltantes: {', '.join(missing)}")

        # Partner por email (best-effort)
        partner = self.env['res.partner'].sudo().search([('email', '=', vals['contact_email'])], limit=1)
        if not partner:
            try:
                partner = self.env['res.partner'].sudo().create({
                    'name': vals['contact_name'],
                    'email': vals['contact_email'],
                    'phone': vals.get('contact_phone', ''),
                    'is_company': False
                })
            except Exception as e:
                _logger.error("Error creando partner: %s", e)

        rec = self.create(vals)
        try:
            self._create_technical_activity(rec)
        except Exception as e:
            _logger.error("Error creando actividad técnica: %s", e)
        return rec

    def _create_technical_activity(self, assistance_request):
        """Crea actividad para el equipo técnico (To-do)."""
        # Asignación: técnico definido > primer usuario grupo interno > usuario actual
        if assistance_request.technician_id:
            assignee = assistance_request.technician_id
        else:
            tech_group = self.env.ref('base.group_user', False)
            assignee = tech_group.users[:1] and tech_group.users[0] or self.env.user

        activity_vals = {
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f'Nueva Solicitud de Asistencia Remota - {assistance_request.secuencia}',
            'note': f'''
                🖥️ <b>Nueva Solicitud de Asistencia Remota</b><br/><br/>
                <b>Equipo:</b> {(assistance_request.equipment_id.name.name if assistance_request.equipment_id and assistance_request.equipment_id.name else 'Sin nombre')}<br/>
                <b>Serie:</b> {assistance_request.equipment_id.serie_id or 'Sin serie'}<br/>
                <b>Cliente:</b> {assistance_request.partner_id.name if assistance_request.partner_id else 'Sin cliente'}<br/>
                <b>Ubicación:</b> {assistance_request.equipment_location or 'Sin ubicación'}<br/><br/>
                <b>Contacto:</b> {assistance_request.contact_name}<br/>
                <b>Email:</b> {assistance_request.contact_email}<br/>
                <b>Teléfono:</b> {assistance_request.contact_phone or 'No proporcionado'}<br/><br/>
                <b>Tipo de Asistencia:</b> {dict(assistance_request._fields['assistance_type'].selection).get(assistance_request.assistance_type, 'Sin tipo')}<br/>
                <b>Prioridad:</b> {dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media')}<br/><br/>
                <b>Descripción del Problema:</b><br/>{(assistance_request.problem_description or '').replace(chr(10), '<br/>')}<br/><br/>
                <b>Datos de Acceso:</b><br/>
                {('• AnyDesk ID: ' + assistance_request.anydesk_id + '<br/>') if assistance_request.anydesk_id else ''}
                {('• Usuario: ' + assistance_request.username + '<br/>') if assistance_request.username else ''}
                {('• Email Escáner: ' + assistance_request.scanner_email + '<br/>') if assistance_request.scanner_email else ''}
                Por favor, revisar y programar la asistencia remota.
            ''',
            'user_id': assignee.id,
            'res_id': assistance_request.id,
            'res_model_id': self.env['ir.model']._get('remote.assistance.request').id,
            'date_deadline': fields.Date.today() + timedelta(days=1)
        }
        self.env['mail.activity'].create(activity_vals)

    # ========= Validaciones =========
    @api.constrains('contact_email')
    def _check_contact_email(self):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.contact_email and not re.match(email_pattern, record.contact_email):
                raise ValidationError(f"El email '{record.contact_email}' no tiene un formato válido.")

    @api.constrains('scheduled_datetime')
    def _check_scheduled_datetime(self):
        for record in self:
            if record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                raise ValidationError(_("La fecha programada no puede ser en el pasado."))

    @api.constrains('session_start_time', 'session_end_time')
    def _check_session_times(self):
        for record in self:
            if record.session_start_time and record.session_end_time and record.session_end_time <= record.session_start_time:
                raise ValidationError(_("La hora de fin de sesión debe ser posterior a la hora de inicio."))

    # ========= WhatsApp =========
    def send_whatsapp_message(self, phone, message):
        """Envía mensaje de WhatsApp usando la API corporativa (no bloqueante)."""
        try:
            url = 'https://whatsappapi.copiercompanysac.com/api/message'
            data = {'phone': phone, 'message': message}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, json=data)
            try:
                return response.json()
            except json.JSONDecodeError as e:
                _logger.error("Respuesta WhatsApp no es JSON válido: %s", e)
                return {"error": "Respuesta no-JSON de la API"}
        except Exception as e:
            _logger.exception("Error enviando WhatsApp: %s", e)
            return {"error": str(e)}

    def send_whatsapp_confirmation(self):
        self.ensure_one()
        if not self.contact_phone_clean:
            _logger.warning("Sin teléfono válido para WhatsApp en %s", self.secuencia)
            return False

        lima_tz = pytz.timezone('America/Lima')
        current_hour = datetime.now(lima_tz).hour
        saludo = "👋 Buenos días" if 5 <= current_hour < 12 else ("👋 Buenas tardes" if current_hour < 18 else "👋 Buenas noches")

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
        priority_names = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta', 'urgent': 'Urgente'}

        equipment_name = (self.equipment_id.name.name if self.equipment_id and self.equipment_id.name else 'Sin especificar')
        serie = self.equipment_id.serie_id or 'Sin serie'
        assistance_name = assistance_names.get(self.assistance_type, 'Asistencia Técnica')
        priority_name = priority_names.get(self.priority, 'Media')

        message = (
            f"*🏢 Copier Company*\n\n"
            f"{saludo}, {self.contact_name}.\n\n"
            "Hemos recibido exitosamente su solicitud de asistencia remota:\n\n"
            f"📋 *Número de Solicitud:* {self.secuencia}\n"
            f"🖨️ *Equipo:* {equipment_name}\n"
            f"🔢 *Serie:* {serie}\n"
            f"🛠️ *Tipo de Asistencia:* {assistance_name}\n"
            f"🚨 *Prioridad:* {priority_name}\n\n"
            "Nuestro equipo técnico revisará su solicitud y se pondrá en contacto con usted para programar la sesión de asistencia remota.\n\n"
            f"Recibirá actualizaciones del estado de su solicitud en: {self.contact_email}\n\n"
            "Gracias por confiar en Copier Company.\n\n"
            "Atentamente,\n"
            "📞 Soporte Técnico Copier Company\n"
            "☎️ Tel: +51975399303\n"
            "📧 Email: info@copiercompanysac.com"
        )

        resp = self.send_whatsapp_message(self.contact_phone_clean, message)
        if resp and not resp.get('error'):
            self.message_post(body=f"✅ Confirmación WhatsApp enviada a {self.contact_phone_clean}", message_type='notification')
            return True
        self.message_post(body=f"❌ Error enviando WhatsApp a {self.contact_phone_clean}: {resp.get('error', 'desconocido') if resp else 'sin respuesta'}", message_type='notification')
        return False

    def send_status_update_whatsapp(self, status_message):
        self.ensure_one()
        if not self.contact_phone_clean:
            return False

        lima_tz = pytz.timezone('America/Lima')
        current_hour = datetime.now(lima_tz).hour
        saludo = "👋 Buenos días" if 5 <= current_hour < 12 else ("👋 Buenas tardes" if current_hour < 18 else "👋 Buenas noches")

        eq_name = (self.equipment_id.name.name if self.equipment_id and self.equipment_id.name else 'Sin especificar')

        message = (
            f"*🏢 Copier Company*\n\n"
            f"{saludo}, {self.contact_name}.\n\n"
            "Actualización de su solicitud de asistencia remota:\n\n"
            f"📋 *Solicitud:* {self.secuencia}\n"
            f"🖨️ *Equipo:* {eq_name}\n\n"
            f"{status_message}\n\n"
            "Gracias por su confianza.\n\n"
            "Atentamente,\n"
            "📞 Soporte Técnico Copier Company\n"
            "☎️ Tel: +51975399303"
        )

        resp = self.send_whatsapp_message(self.contact_phone_clean, message)
        if resp and not resp.get('error'):
            self.message_post(body=f"✅ Actualización WhatsApp enviada: {status_message}", message_type='notification')
            return True
        self.message_post(body="❌ Error enviando actualización WhatsApp", message_type='notification')
        return False
