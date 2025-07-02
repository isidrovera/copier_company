# Agregar este modelo al final de tu archivo models.py

import logging
from datetime import timedelta
from odoo import models, fields, api
import requests
import json
from datetime import datetime
import pytz
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class TonerRequest(models.Model):
    """Modelo para solicitudes de toner"""
    _name = 'toner.request'
    _description = 'Solicitudes de Toner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'
    _rec_name = 'display_name'

    # Campo computed para el nombre del registro
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('equipment_id', 'client_name', 'toner_type')
    def _compute_display_name(self):
        """Calcula el nombre a mostrar del registro"""
        for record in self:
            try:
                equipment_name = record.equipment_id.name.name if record.equipment_id and record.equipment_id.name else 'Sin equipo'
                client_name = record.client_name or 'Sin cliente'
                toner_type = dict(record._fields['toner_type'].selection).get(record.toner_type, 'Sin tipo')
                
                record.display_name = f"{equipment_name} - {client_name} ({toner_type})"
            except Exception:
                record.display_name = f"Solicitud Toner {record.id or 'Nueva'}"

    # Campos básicos
    equipment_id = fields.Many2one(
        'copier.company',
        string='Equipo',
        required=True,
        tracking=True,
        help='Equipo para el cual se solicita toner'
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
        """Sobrescribe create para asignar secuencia automática y enviar confirmación WhatsApp"""
        if vals.get('secuencia', 'New') == 'New':
            vals['secuencia'] = self.env['ir.sequence'].next_by_code('toner.request') or 'TR/001'
        
        result = super(TonerRequest, self).create(vals)
        
        # Crear nota en el chatter
        try:
            result.message_post(
                body=f"""
                🖨️ <b>Nueva Solicitud de Toner</b><br/>
                • <b>Equipo:</b> {result.equipment_id.name.name if result.equipment_id.name else 'Sin nombre'}<br/>
                • <b>Serie:</b> {result.equipment_id.serie_id or 'Sin serie'}<br/>
                • <b>Cliente:</b> {result.partner_id.name if result.partner_id else 'Sin cliente'}<br/>
                • <b>Solicitado por:</b> {result.client_name}<br/>
                • <b>Tipo:</b> {dict(result._fields['toner_type'].selection).get(result.toner_type, 'Sin tipo')}<br/>
                • <b>Estado:</b> Pendiente
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
        string='Nombre del Solicitante',
        required=True,
        tracking=True,
        help='Nombre completo de la persona que solicita el toner'
    )
    
    client_email = fields.Char(
        string='Email del Solicitante',
        required=True,
        tracking=True,
        help='Email de la persona que solicita'
    )
    
    client_phone = fields.Char(
        string='Teléfono del Solicitante',
        tracking=True,
        help='Teléfono de contacto'
    )

    # Detalles del toner
    toner_type = fields.Selection([
        ('black', 'Negro'),
        ('cyan', 'Cian'),
        ('magenta', 'Magenta'),
        ('yellow', 'Amarillo'),
        ('complete_set', 'Juego Completo'),
        ('maintenance_kit', 'Kit de Mantenimiento')
    ], string='Tipo de Toner', required=True, tracking=True)
    
    quantity = fields.Integer(
        string='Cantidad',
        default=1,
        required=True,
        tracking=True,
        help='Cantidad de toners solicitados'
    )
    
    urgency = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Urgencia', default='medium', tracking=True)
    
    current_toner_level = fields.Selection([
        ('empty', 'Vacío (0%)'),
        ('low', 'Bajo (1-10%)'),
        ('medium_low', 'Medio-Bajo (11-25%)'),
        ('medium', 'Medio (26-50%)'),
        ('high', 'Alto (51-75%)'),
        ('full', 'Lleno (76-100%)')
    ], string='Nivel Actual del Toner', help='Nivel aproximado del toner actual')
    
    reason = fields.Text(
        string='Motivo de la Solicitud',
        help='Descripción del motivo por el cual se solicita el toner'
    )
    
    # Estado y gestión
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('dispatched', 'Despachado'),
        ('delivered', 'Entregado'),
        ('installed', 'Instalado'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='pending', tracking=True)
    
    # Gestión interna
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        help='Usuario responsable de gestionar la solicitud'
    )
    
    approval_date = fields.Datetime(
        string='Fecha de Aprobación',
        tracking=True
    )
    
    dispatch_date = fields.Datetime(
        string='Fecha de Despacho',
        tracking=True
    )
    
    delivery_date = fields.Datetime(
        string='Fecha de Entrega',
        tracking=True
    )
    
    installation_date = fields.Datetime(
        string='Fecha de Instalación',
        tracking=True
    )
    
    # Información de entrega
    delivery_person = fields.Char(
        string='Persona que Recibe',
        help='Nombre de la persona que recibe el toner'
    )
    
    delivery_notes = fields.Text(
        string='Notas de Entrega',
        help='Observaciones sobre la entrega'
    )
    
    # Costos (opcional)
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
    )
    
    estimated_cost = fields.Monetary(
        string='Costo Estimado',
        currency_field='currency_id',
        help='Costo estimado del toner'
    )
    
    actual_cost = fields.Monetary(
        string='Costo Real',
        currency_field='currency_id',
        tracking=True,
        help='Costo real del toner'
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
    def action_approve(self):
        """Aprueba la solicitud"""
        self.ensure_one()
        self.state = 'approved'
        self.approval_date = fields.Datetime.now()
        if not self.responsible_id:
            self.responsible_id = self.env.user
        self.message_post(
            body=f"✅ Solicitud aprobada por {self.env.user.name}",
            message_type='notification'
        )
        
        # Enviar notificación WhatsApp
        self.send_status_update_whatsapp(
            f"✅ *Su solicitud ha sido APROBADA*\n\n"
            f"Nuestro equipo procederá con el despacho del toner solicitado."
        )

    def action_dispatch(self):
        """Marca como despachado"""
        self.ensure_one()
        self.state = 'dispatched'
        self.dispatch_date = fields.Datetime.now()
        self.message_post(
            body=f"📦 Toner despachado el {self.dispatch_date.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
        )
        
        # Enviar notificación WhatsApp
        self.send_status_update_whatsapp(
            f"📦 *Su toner ha sido DESPACHADO*\n\n"
            f"Fecha de despacho: {self.dispatch_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"Pronto nos pondremos en contacto para coordinar la entrega."
        )

    def action_deliver(self):
        """Marca como entregado"""
        self.ensure_one()
        self.state = 'delivered'
        self.delivery_date = fields.Datetime.now()
        self.message_post(
            body=f"🚚 Toner entregado el {self.delivery_date.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
        )
        
        # Enviar notificación WhatsApp
        self.send_status_update_whatsapp(
            f"🚚 *Su toner ha sido ENTREGADO*\n\n"
            f"Fecha de entrega: {self.delivery_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"Gracias por su confianza en nuestros servicios."
        )

    def action_install(self):
        """Marca como instalado"""
        self.ensure_one()
        self.state = 'installed'
        self.installation_date = fields.Datetime.now()
        self.message_post(
            body=f"🔧 Toner instalado el {self.installation_date.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
        )
        
        # Enviar notificación WhatsApp
        self.send_status_update_whatsapp(
            f"🔧 *Su toner ha sido INSTALADO*\n\n"
            f"Fecha de instalación: {self.installation_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"Su equipo está listo para continuar operando normalmente."
        )

    def action_reject(self):
        """Rechaza la solicitud"""
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(
            body=f"❌ Solicitud rechazada por {self.env.user.name}",
            message_type='notification'
        )
        
        # Enviar notificación WhatsApp
        self.send_status_update_whatsapp(
            f"❌ *Su solicitud ha sido RECHAZADA*\n\n"
            f"Para más información, puede contactarnos directamente."
        )

    def action_cancel(self):
        """Cancela la solicitud"""
        self.ensure_one()
        self.state = 'cancelled'
        self.message_post(
            body=f"🚫 Solicitud cancelada",
            message_type='notification'
        )

    def action_reset_to_pending(self):
        """Regresa a estado pendiente"""
        self.ensure_one()
        self.state = 'pending'
        self.message_post(
            body="🔄 Solicitud regresada a estado pendiente",
            message_type='notification'
        )

    @api.model
    def create_from_public_form(self, vals):
        """Método específico para crear desde formulario público"""
        _logger.info("=== INICIANDO create_from_public_form para toner ===")
        _logger.info("Valores del formulario: %s", vals)
        
        try:
            # Validaciones
            required_fields = ['equipment_id', 'client_name', 'client_email', 'toner_type']
            missing_fields = [field for field in required_fields if not vals.get(field)]
            
            if missing_fields:
                error_msg = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
                raise ValidationError(error_msg)
            
            # Crear la solicitud
            toner_request = self.create(vals)
            
            # Crear actividad para el equipo de logística
            try:
                self._create_logistics_activity(toner_request)
            except Exception as e:
                _logger.error("Error creando actividad logística: %s", str(e))
            
            return toner_request
            
        except Exception as e:
            _logger.exception("Error en create_from_public_form: %s", str(e))
            raise

    def _create_logistics_activity(self, toner_request):
        """Crea una actividad para el equipo de logística"""
        try:
            # Buscar usuarios del grupo de logística o ventas
            logistics_group = self.env.ref('sales_team.group_sale_salesman', False)
            if logistics_group and logistics_group.users:
                assignee = logistics_group.users[0]
            else:
                assignee = self.env.user
            
            urgency_icon = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}
            
            activity_vals = {
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Nueva Solicitud de Toner - {toner_request.secuencia}',
                'note': f'''
                    🖨️ <b>Nueva Solicitud de Toner</b><br/><br/>
                    
                    <b>Equipo:</b> {toner_request.equipment_id.name.name if toner_request.equipment_id.name else 'Sin nombre'}<br/>
                    <b>Serie:</b> {toner_request.equipment_id.serie_id or 'Sin serie'}<br/>
                    <b>Cliente:</b> {toner_request.partner_id.name if toner_request.partner_id else 'Sin cliente'}<br/>
                    <b>Ubicación:</b> {toner_request.equipment_location or 'Sin ubicación'}<br/><br/>
                    
                    <b>Solicitado por:</b> {toner_request.client_name}<br/>
                    <b>Email:</b> {toner_request.client_email}<br/>
                    <b>Teléfono:</b> {toner_request.client_phone or 'No proporcionado'}<br/><br/>
                    
                    <b>Detalles del Toner:</b><br/>
                    • Tipo: {dict(toner_request._fields['toner_type'].selection).get(toner_request.toner_type, 'Sin tipo')}<br/>
                    • Cantidad: {toner_request.quantity}<br/>
                    • Urgencia: {urgency_icon.get(toner_request.urgency, '⚪')} {dict(toner_request._fields['urgency'].selection).get(toner_request.urgency, 'Media')}<br/>
                    • Nivel actual: {dict(toner_request._fields['current_toner_level'].selection).get(toner_request.current_toner_level, 'No especificado') if toner_request.current_toner_level else 'No especificado'}<br/><br/>
                    
                    {'<b>Motivo:</b><br/>' + toner_request.reason + '<br/><br/>' if toner_request.reason else ''}
                    
                    Por favor, gestionar la entrega del toner solicitado.
                ''',
                'user_id': assignee.id,
                'res_id': toner_request.id,
                'res_model_id': self.env['ir.model']._get('toner.request').id,
                'date_deadline': fields.Date.today() + timedelta(days=1 if toner_request.urgency == 'urgent' else 3)
            }
            
            self.env['mail.activity'].create(activity_vals)
            
        except Exception as e:
            _logger.exception("Error en _create_logistics_activity: %s", str(e))
            raise

    # Validaciones
    @api.constrains('quantity')
    def _check_quantity(self):
        """Valida que la cantidad sea positiva"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("La cantidad debe ser mayor a cero.")

    @api.constrains('client_email')
    def _check_client_email(self):
        """Valida el formato del email"""
        for record in self:
            if record.client_email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.client_email):
                    raise ValidationError(f"El email '{record.client_email}' no tiene un formato válido.")
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
        """Envía confirmación por WhatsApp al cliente que solicitó el toner"""
        self.ensure_one()
        
        if not self.client_phone_clean:
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

            # Mapear tipos de toner para el mensaje
            toner_names = {
                'black': 'Toner Negro',
                'cyan': 'Toner Cian',
                'magenta': 'Toner Magenta',
                'yellow': 'Toner Amarillo',
                'complete_set': 'Juego Completo de Toners',
                'maintenance_kit': 'Kit de Mantenimiento'
            }
            
            toner_name = toner_names.get(self.toner_type, 'Toner')
            
            # Mapear urgencia
            urgency_names = {
                'low': 'Baja',
                'medium': 'Media',
                'high': 'Alta',
                'urgent': 'Urgente'
            }
            
            urgency_name = urgency_names.get(self.urgency, 'Media')
            equipment_name = self.equipment_id.name.name if self.equipment_id and self.equipment_id.name else 'Sin especificar'
            serie = self.equipment_id.serie_id or 'Sin serie'

            message = (
                f"*🏢 Copier Company*\n\n"
                f"{saludo}, {self.client_name}.\n\n"
                f"Hemos recibido exitosamente su solicitud de toner:\n\n"
                f"📋 *Número de Solicitud:* {self.secuencia}\n"
                f"🖨️ *Equipo:* {equipment_name}\n"
                f"🔢 *Serie:* {serie}\n"
                f"🖨️ *Tipo de Toner:* {toner_name}\n"
                f"📦 *Cantidad:* {self.quantity}\n"
                f"🚨 *Urgencia:* {urgency_name}\n\n"
                f"Su solicitud será procesada por nuestro equipo de logística y nos pondremos en contacto con usted para coordinar la entrega.\n\n"
                f"Recibirá actualizaciones del estado de su solicitud en: {self.client_email}\n\n"
                f"Gracias por confiar en Copier Company.\n\n"
                f"Atentamente,\n"
                f"📞 Logística Copier Company\n"
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
                _logger.info("WhatsApp de confirmación enviado exitosamente - Solicitud: %s, Teléfono: %s", 
                           self.secuencia, self.client_phone_clean)
                return True
            else:
                error_msg = response.get('error', 'Error desconocido') if response else 'Sin respuesta'
                self.message_post(
                    body=f"❌ Error enviando WhatsApp a {self.client_phone_clean}: {error_msg}",
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

    

    # Métodos para notificar cambios de estado por WhatsApp
    def send_status_update_whatsapp(self, status_message):
        """Envía actualización de estado por WhatsApp"""
        self.ensure_one()
        
        if not self.client_phone_clean:
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
                f"{saludo}, {self.client_name}.\n\n"
                f"Actualización de su solicitud de toner:\n\n"
                f"📋 *Solicitud:* {self.secuencia}\n"
                f"🖨️ *Equipo:* {self.equipment_id.name.name if self.equipment_id.name else 'Sin especificar'}\n\n"
                f"{status_message}\n\n"
                f"Gracias por su confianza.\n\n"
                f"Atentamente,\n"
                f"📞 Logística Copier Company\n"
                f"☎️ Tel: +51975399303"
            )

            response = self.send_whatsapp_message(self.client_phone_clean, message)
            
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