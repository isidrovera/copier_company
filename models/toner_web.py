# Agregar este modelo al final de tu archivo models.py

import logging
from datetime import timedelta
from odoo import models, fields, api
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
        """Sobrescribe create para asignar secuencia automática"""
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

    def action_dispatch(self):
        """Marca como despachado"""
        self.ensure_one()
        self.state = 'dispatched'
        self.dispatch_date = fields.Datetime.now()
        self.message_post(
            body=f"📦 Toner despachado el {self.dispatch_date.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
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

    def action_install(self):
        """Marca como instalado"""
        self.ensure_one()
        self.state = 'installed'
        self.installation_date = fields.Datetime.now()
        self.message_post(
            body=f"🔧 Toner instalado el {self.installation_date.strftime('%d/%m/%Y %H:%M')}",
            message_type='notification'
        )

    def action_reject(self):
        """Rechaza la solicitud"""
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(
            body=f"❌ Solicitud rechazada por {self.env.user.name}",
            message_type='notification'
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