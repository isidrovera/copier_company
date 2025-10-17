# Agregar este modelo al final de tu archivo models.py

import logging
from datetime import timedelta
from odoo import models, fields, api
import requests
import json
from datetime import datetime
import pytz
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class ClientCounterSubmission(models.Model):
    """Modelo para contadores enviados por clientes"""
    _name = 'client.counter.submission'
    _description = 'Contadores Enviados por Clientes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
 
    _rec_name = 'display_name'

    # Campo computed para el nombre del registro
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('equipment_id', 'submission_date', 'client_name')
    def _compute_display_name(self):
        """Calcula el nombre a mostrar del registro"""
        for record in self:
            try:
                equipment_name = record.equipment_id.name.name if record.equipment_id and record.equipment_id.name else 'Sin equipo'
                date_str = record.submission_date.strftime('%d/%m/%Y') if record.submission_date else 'Sin fecha'
                client_name = record.client_name or 'Sin cliente'
                
                record.display_name = f"{equipment_name} - {client_name} ({date_str})"
            except Exception:
                record.display_name = f"Contador {record.id or 'Nuevo'}"

    # Campos básicos
    equipment_id = fields.Many2one(
        'copier.company',
        string='Equipo',
        required=True,
        tracking=True,
        help='Equipo para el cual se reportan los contadores'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='equipment_id.cliente_id',
        store=True,
        readonly=True
    )
    
    submission_date = fields.Datetime(
        string='Fecha de Reporte',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    secuencia = fields.Char(
        string='Número de Reporte',
        default='New',
        copy=False,
        required=True,
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Sobrescribe create para asignar secuencia automática y enviar confirmación WhatsApp"""
        if vals.get('secuencia', 'New') == 'New':
            vals['secuencia'] = self.env['ir.sequence'].next_by_code('client.counter.submission') or 'CCR/001'
        
        result = super(ClientCounterSubmission, self).create(vals)
        
        # Crear nota en el chatter
        try:
            result.message_post(
                body=f"""
                📊 <b>Nuevos Contadores Reportados</b><br/>
                • <b>Equipo:</b> {result.equipment_id.name.name if result.equipment_id.name else 'Sin nombre'}<br/>
                • <b>Serie:</b> {result.equipment_id.serie_id or 'Sin serie'}<br/>
                • <b>Cliente:</b> {result.partner_id.name if result.partner_id else 'Sin cliente'}<br/>
                • <b>Reportado por:</b> {result.client_name}<br/>
                • <b>Contador B/N:</b> {result.counter_bn:,}<br/>
                • <b>Contador Color:</b> {result.counter_color:,}<br/>
                • <b>Estado:</b> Pendiente de Revisión
                """,
                message_type='notification'
            )
        except Exception as e:
            _logger.error("Error creando nota en chatter: %s", str(e))
        
        # Enviar confirmación WhatsApp al cliente
        try:
            result.send_whatsapp_confirmation()
        except Exception as e:
            _logger.error("Error enviando confirmación WhatsApp: %s", str(e))
            # No interrumpir el proceso si falla el WhatsApp
        
        return result
    # Información del contacto
    client_name = fields.Char(
        string='Nombre del Reportante',
        required=True,
        tracking=True,
        help='Nombre completo de la persona que reporta los contadores'
    )
    
    client_email = fields.Char(
        string='Email del Reportante',
        required=True,
        tracking=True,
        help='Email de la persona que reporta'
    )
    
    client_phone = fields.Char(
        string='Teléfono del Reportante',
        tracking=True,
        help='Teléfono de contacto'
    )

    # Contadores reportados
    counter_bn = fields.Integer(
        string='Contador Blanco y Negro',
        required=True,
        tracking=True,
        help='Lectura actual del contador de copias en blanco y negro'
    )
    
    counter_color = fields.Integer(
        string='Contador Color',
        default=0,
        tracking=True,
        help='Lectura actual del contador de copias a color'
    )
    
    # Campos calculados basados en lecturas anteriores
    previous_counter_bn = fields.Integer(
        string='Contador B/N Anterior',
        compute='_compute_previous_counters',
        store=True,
        help='Último contador B/N registrado'
    )
    
    previous_counter_color = fields.Integer(
        string='Contador Color Anterior',
        compute='_compute_previous_counters',
        store=True,
        help='Último contador Color registrado'
    )
    
    copies_bn_period = fields.Integer(
        string='Copias B/N del Período',
        compute='_compute_period_copies',
        store=True,
        help='Copias B/N realizadas en este período'
    )
    
    copies_color_period = fields.Integer(
        string='Copias Color del Período',
        compute='_compute_period_copies',
        store=True,
        help='Copias Color realizadas en este período'
    )

    @api.depends('equipment_id')
    def _compute_previous_counters(self):
        """Calcula los contadores anteriores basado en la última lectura"""
        for record in self:
            if record.equipment_id:
                # Buscar la última lectura confirmada del equipo
                last_counter = self.env['copier.counter'].search([
                    ('maquina_id', '=', record.equipment_id.id),
                    ('state', 'in', ['confirmed', 'invoiced'])
                ], order='fecha desc', limit=1)
                
                if last_counter:
                    record.previous_counter_bn = last_counter.contador_actual_bn or 0
                    record.previous_counter_color = last_counter.contador_actual_color or 0
                else:
                    record.previous_counter_bn = 0
                    record.previous_counter_color = 0
            else:
                record.previous_counter_bn = 0
                record.previous_counter_color = 0

    @api.depends('counter_bn', 'counter_color', 'previous_counter_bn', 'previous_counter_color')
    def _compute_period_copies(self):
        """Calcula las copias del período"""
        for record in self:
            record.copies_bn_period = max(0, record.counter_bn - record.previous_counter_bn)
            record.copies_color_period = max(0, record.counter_color - record.previous_counter_color)

    # Información adicional
    notes = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales sobre los contadores'
    )
    
    counter_photo = fields.Binary(
        string='Foto del Contador',
        help='Foto de la pantalla del contador como evidencia'
    )
    
    counter_photo_filename = fields.Char(
        string='Nombre del Archivo',
        help='Nombre del archivo de la foto'
    )
    
    # Estado y gestión
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado'),
        ('processed', 'Procesado'),
        ('rejected', 'Rechazado')
    ], string='Estado', default='pending', tracking=True)
    
    # Técnico que revisa
    reviewer_id = fields.Many2one(
        'res.users',
        string='Revisado por',
        tracking=True,
        help='Usuario que revisó los contadores'
    )
    
    review_date = fields.Datetime(
        string='Fecha de Revisión',
        tracking=True
    )
    
    review_notes = fields.Text(
        string='Notas de Revisión',
        help='Notas del técnico que revisó'
    )

    # Relación con contador oficial (si se crea)
    official_counter_id = fields.Many2one(
        'copier.counter',
        string='Contador Oficial Generado',
        readonly=True,
        help='Contador oficial generado a partir de este reporte'
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

    # Campos para cálculos estimados de facturación
    estimated_amount_bn = fields.Monetary(
        string='Monto Estimado B/N',
        compute='_compute_estimated_amounts',
        currency_field='currency_id',
        help='Monto estimado para copias B/N'
    )
    
    estimated_amount_color = fields.Monetary(
        string='Monto Estimado Color',
        compute='_compute_estimated_amounts',
        currency_field='currency_id',
        help='Monto estimado para copias Color'
    )
    
    estimated_total_amount = fields.Monetary(
        string='Monto Total Estimado',
        compute='_compute_estimated_amounts',
        currency_field='currency_id',
        help='Monto total estimado'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='equipment_id.currency_id',
        store=True,
        readonly=True
    )
    total_copies_period = fields.Integer(
        string='Total Copias del Período',
        compute='_compute_total_copies_period',
        store=True,
        help='Total de copias del período (B/N + Color)'
    )

    @api.depends('copies_bn_period', 'copies_color_period')
    def _compute_total_copies_period(self):
        """Calcula el total de copias del período"""
        for record in self:
            record.total_copies_period = record.copies_bn_period + record.copies_color_period
    @api.depends('copies_bn_period', 'copies_color_period', 'equipment_id.costo_copia_bn', 'equipment_id.costo_copia_color')
    def _compute_estimated_amounts(self):
        """Calcula los montos estimados basado en los costos del equipo"""
        for record in self:
            if record.equipment_id:
                record.estimated_amount_bn = record.copies_bn_period * record.equipment_id.costo_copia_bn
                record.estimated_amount_color = record.copies_color_period * record.equipment_id.costo_copia_color
                record.estimated_total_amount = record.estimated_amount_bn + record.estimated_amount_color
            else:
                record.estimated_amount_bn = 0
                record.estimated_amount_color = 0
                record.estimated_total_amount = 0

    # Métodos para cambiar estado
    def action_review(self):
        """Marca como revisado"""
        self.ensure_one()
        self.state = 'reviewed'
        self.reviewer_id = self.env.user
        self.review_date = fields.Datetime.now()
        self.message_post(
            body=f"👀 Contadores revisados por {self.env.user.name}",
            message_type='notification'
        )

    def action_approve(self):
        """Aprueba los contadores"""
        self.ensure_one()
        self.state = 'approved'
        if not self.reviewer_id:
            self.reviewer_id = self.env.user
            self.review_date = fields.Datetime.now()
        self.message_post(
            body=f"✅ Contadores aprobados por {self.env.user.name}",
            message_type='notification'
        )

    def action_process_to_official(self):
        """Procesa y crea contador oficial"""
        self.ensure_one()
        
        if self.official_counter_id:
            raise UserError("Ya existe un contador oficial generado para este reporte.")
        
        if self.state != 'approved':
            raise UserError("Solo se pueden procesar reportes aprobados.")
        
        # Crear contador oficial
        counter_vals = {
            'maquina_id': self.equipment_id.id,
            'fecha': self.submission_date.date(),
            'contador_actual_bn': self.counter_bn,
            'contador_actual_color': self.counter_color,
            'total_copias_bn': self.copies_bn_period,
            'total_copias_color': self.copies_color_period,
            'state': 'draft',
            'notas': f"Generado automáticamente desde reporte cliente {self.secuencia}\n\nObservaciones del cliente:\n{self.notes or 'Sin observaciones'}"
        }
        
        # Si el modelo copier.counter tiene más campos, agregarlos aquí
        try:
            official_counter = self.env['copier.counter'].create(counter_vals)
            self.official_counter_id = official_counter.id
            self.state = 'processed'
            
            self.message_post(
                body=f"🔄 Contador oficial creado: {official_counter.name or official_counter.id}",
                message_type='notification'
            )
            
            return {
                'name': 'Contador Oficial',
                'view_mode': 'form',
                'res_model': 'copier.counter',
                'res_id': official_counter.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        except Exception as e:
            _logger.exception("Error creando contador oficial: %s", str(e))
            raise UserError(f"Error al crear el contador oficial: {str(e)}")

    def action_reject(self):
        """Rechaza los contadores"""
        self.ensure_one()
        self.state = 'rejected'
        if not self.reviewer_id:
            self.reviewer_id = self.env.user
            self.review_date = fields.Datetime.now()
        self.message_post(
            body=f"❌ Contadores rechazados por {self.env.user.name}",
            message_type='notification'
        )

    def action_reset_to_pending(self):
        """Regresa a estado pendiente"""
        self.ensure_one()
        self.state = 'pending'
        self.reviewer_id = False
        self.review_date = False
        self.review_notes = False
        self.message_post(
            body="🔄 Reporte regresado a estado pendiente",
            message_type='notification'
        )

    @api.model
    def create_from_public_form(self, vals):
        """Método específico para crear desde formulario público"""
        _logger.info("=== INICIANDO create_from_public_form para contadores ===")
        _logger.info("Valores del formulario: %s", vals)
        
        try:
            # Validaciones
            required_fields = ['equipment_id', 'client_name', 'client_email', 'counter_bn']
            missing_fields = [field for field in required_fields if not vals.get(field)]
            
            if missing_fields:
                error_msg = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
                raise ValidationError(error_msg)
            
            # Crear el reporte
            counter_submission = self.create(vals)
            
            # Crear actividad para el equipo administrativo
            try:
                self._create_admin_activity(counter_submission)
            except Exception as e:
                _logger.error("Error creando actividad administrativa: %s", str(e))
            
            return counter_submission
            
        except Exception as e:
            _logger.exception("Error en create_from_public_form: %s", str(e))
            raise

    def _create_admin_activity(self, counter_submission):
        """Crea una actividad para el equipo administrativo"""
        try:
            # Buscar usuarios del grupo administrativo o contable
            admin_group = self.env.ref('account.group_account_user', False)
            if admin_group and admin_group.users:
                assignee = admin_group.users[0]
            else:
                assignee = self.env.user
            
            activity_vals = {
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Revisar Contadores - {counter_submission.secuencia}',
                'note': f'''
                    📊 <b>Nuevos Contadores Reportados por Cliente</b><br/><br/>
                    
                    <b>Equipo:</b> {counter_submission.equipment_id.name.name if counter_submission.equipment_id.name else 'Sin nombre'}<br/>
                    <b>Serie:</b> {counter_submission.equipment_id.serie_id or 'Sin serie'}<br/>
                    <b>Cliente:</b> {counter_submission.partner_id.name if counter_submission.partner_id else 'Sin cliente'}<br/>
                    <b>Ubicación:</b> {counter_submission.equipment_location or 'Sin ubicación'}<br/><br/>
                    
                    <b>Reportado por:</b> {counter_submission.client_name}<br/>
                    <b>Email:</b> {counter_submission.client_email}<br/>
                    <b>Teléfono:</b> {counter_submission.client_phone or 'No proporcionado'}<br/><br/>
                    
                    <b>Contadores Reportados:</b><br/>
                    • Blanco y Negro: {counter_submission.counter_bn:,}<br/>
                    • Color: {counter_submission.counter_color:,}<br/><br/>
                    
                    <b>Copias del Período:</b><br/>
                    • B/N: {counter_submission.copies_bn_period:,}<br/>
                    • Color: {counter_submission.copies_color_period:,}<br/><br/>
                    
                    <b>Monto Estimado:</b> S/ {counter_submission.estimated_total_amount:,.2f}<br/><br/>
                    
                    {'<b>Observaciones:</b><br/>' + counter_submission.notes + '<br/><br/>' if counter_submission.notes else ''}
                    
                    Por favor, revisar y aprobar los contadores para generar la facturación.
                ''',
                'user_id': assignee.id,
                'res_id': counter_submission.id,
                'res_model_id': self.env['ir.model']._get('client.counter.submission').id,
                'date_deadline': fields.Date.today() + timedelta(days=2)
            }
            
            self.env['mail.activity'].create(activity_vals)
            
        except Exception as e:
            _logger.exception("Error en _create_admin_activity: %s", str(e))
            raise

    # Validaciones
    @api.constrains('counter_bn', 'counter_color')
    def _check_counters(self):
        """Valida que los contadores sean válidos"""
        for record in self:
            if record.counter_bn < 0:
                raise ValidationError("El contador de blanco y negro no puede ser negativo.")
            
            if record.counter_color < 0:
                raise ValidationError("El contador de color no puede ser negativo.")
            
            # Validar que los contadores no sean menores a los anteriores
            if record.counter_bn < record.previous_counter_bn:
                raise ValidationError(
                    f"El contador B/N ({record.counter_bn:,}) no puede ser menor "
                    f"al contador anterior ({record.previous_counter_bn:,})."
                )
            
            if record.counter_color < record.previous_counter_color:
                raise ValidationError(
                    f"El contador Color ({record.counter_color:,}) no puede ser menor "
                    f"al contador anterior ({record.previous_counter_color:,})."
                )

    @api.constrains('client_email')
    def _check_client_email(self):
        """Valida el formato del email"""
        for record in self:
            if record.client_email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.client_email):
                    raise ValidationError(f"El email '{record.client_email}' no tiene un formato válido.")

    # Método para vista de dashboard/resumen
    def get_summary_data(self):
        """Obtiene datos de resumen para dashboard"""
        self.ensure_one()
        return {
            'equipment_name': self.equipment_id.name.name if self.equipment_id.name else 'Sin nombre',
            'client_name': self.client_name,
            'submission_date': self.submission_date.strftime('%d/%m/%Y %H:%M'),
            'copies_total': self.copies_bn_period + self.copies_color_period,
            'estimated_amount': self.estimated_total_amount,
            'state_display': dict(self._fields['state'].selection).get(self.state, 'Desconocido'),
        }

    client_phone_clean = fields.Char(
        string='Teléfono Limpio',
        compute='_compute_client_phone_clean',
        store=True,
        help='Número de teléfono formateado para WhatsApp'
    )

    @api.depends('client_phone')
    def _compute_client_phone_clean(self):
        """Formatea el número de teléfono para WhatsApp"""
        for record in self:
            if record.client_phone:
                phone = record.client_phone.replace('+', '').replace(' ', '').replace('-', '')
                # Remover cualquier carácter que no sea número
                phone = ''.join(filter(str.isdigit, phone))
                
                # Si el número no empieza con '51' y tiene 9 dígitos, agregar '51'
                if not phone.startswith('51') and len(phone) == 9:
                    phone = '51' + phone
                record.client_phone_clean = phone
            else:
                record.client_phone_clean = ''

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
        """Envía confirmación por WhatsApp al cliente que reportó los contadores"""
        self.ensure_one()
        
        if not self.client_phone_clean:
            _logger.warning("No hay número de teléfono válido para enviar WhatsApp - Reporte: %s", self.secuencia)
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

            # Construir mensaje de confirmación
            equipment_name = self.equipment_id.name.name if self.equipment_id and self.equipment_id.name else 'Sin especificar'
            serie = self.equipment_id.serie_id or 'Sin serie'
            total_copias = self.copies_bn_period + self.copies_color_period

            message = (
                f"*🏢 Copier Company*\n\n"
                f"{saludo}, {self.client_name}.\n\n"
                f"Hemos recibido exitosamente su reporte de contadores:\n\n"
                f"📋 *Número de Reporte:* {self.secuencia}\n"
                f"🖨️ *Equipo:* {equipment_name}\n"
                f"🔢 *Serie:* {serie}\n"
                f"📊 *Contador B/N:* {self.counter_bn:,}\n"
                f"📊 *Contador Color:* {self.counter_color:,}\n"
                f"📈 *Total Copias del Período:* {total_copias:,}\n\n"
                f"Su reporte será revisado por nuestro equipo administrativo y procesado para la facturación correspondiente.\n\n"
                f"Recibirá confirmación de la validación en: {self.client_email}\n\n"
                f"Gracias por confiar en Copier Company.\n\n"
                f"Atentamente,\n"
                f"📞 Administración Copier Company\n"
                f"☎️ Tel: +51975399303\n"
                f"📧 Email: info@copiercompanysac.com"
            )

            # Enviar mensaje
            response = self.send_whatsapp_message(self.client_phone_clean, message)
            
            if response and not response.get('error'):
                # Crear nota en el chatter si el envío fue exitoso
                self.message_post(
                    body=f"✅ Confirmación WhatsApp enviada a {self.client_phone_clean}",
                    message_type='notification'
                )
                _logger.info("WhatsApp de confirmación enviado exitosamente - Reporte: %s, Teléfono: %s", 
                           self.secuencia, self.client_phone_clean)
                return True
            else:
                error_msg = response.get('error', 'Error desconocido') if response else 'Sin respuesta'
                self.message_post(
                    body=f"❌ Error enviando WhatsApp a {self.client_phone_clean}: {error_msg}",
                    message_type='notification'
                )
                _logger.error("Error enviando WhatsApp - Reporte: %s, Error: %s", self.secuencia, error_msg)
                return False
                
        except Exception as e:
            _logger.exception("Error en send_whatsapp_confirmation - Reporte: %s", self.secuencia)
            self.message_post(
                body=f"❌ Excepción enviando WhatsApp: {str(e)}",
                message_type='notification'
            )
            return False

    