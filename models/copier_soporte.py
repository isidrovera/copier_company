# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import base64

import logging

_logger = logging.getLogger(__name__)


class CopierServiceProblemType(models.Model):
    """Catálogo de tipos de problemas técnicos"""
    _name = 'copier.service.problem.type'
    _description = 'Tipos de Problemas de Servicio Técnico'
   
    
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción'
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    icono = fields.Char(
        string='Icono Emoji',
        default='🔧',
        help='Emoji que representa el tipo de problema'
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )


class CopierServiceRequest(models.Model):
    """Solicitud de Servicio Técnico"""
    _name = 'copier.service.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Solicitud de Servicio Técnico'

    
    # ========================================
    # CAMPOS BÁSICOS
    # ========================================
    
    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Nuevo')
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    
    # ========================================
    # INFORMACIÓN DEL EQUIPO
    # ========================================
    
    maquina_id = fields.Many2one(
        'copier.company',
        string='Equipo',
        required=True,
        tracking=True,
        ondelete='restrict'
    )
    
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        store=True,
        tracking=True,
        readonly=True,
        index=True,
        copy=False,
        help="Cliente congelado al momento de crear el servicio. No cambia si la máquina cambia de cliente."
    )
        
    serie_maquina = fields.Char(
        string='Serie',
        related='maquina_id.serie_id',
        store=True,
        readonly=True
    )
    
    modelo_maquina = fields.Many2one(
        'modelos.maquinas',  
        string='Modelo',
        related='maquina_id.name',
        store=True,
        readonly=True
    )
        
    ubicacion = fields.Char(
        string='Ubicación',
        store=True,
        readonly=True,
        copy=False,
        help="Ubicación congelada al momento de crear el servicio."
    )
        
    sede = fields.Char(
        string='Sede',
        store=True,
        readonly=True,
        copy=False,
        help="Sede congelada al momento de crear el servicio."
    )
    
    ip_maquina = fields.Char(
        string='IP',
        store=True,
        readonly=True,
        copy=False,
        help="IP congelada al momento de crear el servicio."
    )
        
    # ========================================
    # INFORMACIÓN DE LA SOLICITUD
    # ========================================
    
    problema_reportado = fields.Text(
        string='Problema Reportado',
        required=True,
        tracking=True
    )
    
    tipo_problema_id = fields.Many2one(
        'copier.service.problem.type',
        string='Tipo de Problema',
        required=True,
        tracking=True
    )
    
    origen_solicitud = fields.Selection([
        ('portal', 'Portal Web'),
        ('whatsapp', 'WhatsApp/QR'),
        ('telefono', 'Teléfono'),
        ('email', 'Email'),
        ('interno', 'Interno')
    ], string='Origen', default='portal', required=True, tracking=True)
    
    prioridad = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Normal'),
        ('2', 'Alta'),
        ('3', 'Crítica')
    ], string='Prioridad', default='1', required=True, tracking=True)
    
    estado = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('confirmado', 'Confirmado'),
        ('en_ruta', 'En Ruta'),
        ('en_sitio', 'En Sitio'),
        ('pausado', 'Pausado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='nuevo', required=True, tracking=True)
    
    # ========================================
    # DATOS DE CONTACTO (del reportante)
    # ========================================
    
    contacto = fields.Char(
        string='Contacto',
        help='Nombre de la persona que reporta'
    )
    
    correo = fields.Char(
        string='Email',
        help='Email del reportante'
    )
 
    telefono_contacto = fields.Char(
        string='Teléfono',
        help='Teléfono del reportante'
    )
    
    # ========================================
    # ASIGNACIÓN DE TÉCNICO
    # ========================================
    
    tecnico_id = fields.Many2one(
    'res.partner',
    string='Técnico Asignado',
    tracking=True,
    domain=[('is_company', '=', False)]  # ✅ Filtrar solo personas, no empresas
)

    tecnico_respaldo_id = fields.Many2one(
        'res.partner',  # ✅ Cambiar de res.users a res.partner
        string='Técnico Respaldo',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
        
    fecha_programada = fields.Datetime(
        string='Fecha Programada',
        tracking=True
    )
    
    duracion_estimada = fields.Float(
        string='Duración Estimada (horas)',
        default=2.0
    )
    vehicle_brand = fields.Char(
        string='Marca del Vehículo',
        help='Marca del vehículo (ej: Mitsubishi, Toyota)'
    )

    vehicle_model = fields.Char(
        string='Modelo del Vehículo',
        help='Modelo del vehículo (ej: L200, Hilux)'
    )

    vehicle_plate = fields.Char(
        string='Placa',
        tracking=True,
        help='Placa del vehículo (ej: BTH677)'
    )

    vehicle_info = fields.Char(
        string='Información del Vehículo',
        compute='_compute_vehicle_info',
        store=True,
        help='Información completa del vehículo (marca, modelo y placa)'
    )
    @api.depends('vehicle_brand', 'vehicle_model', 'vehicle_plate')
    def _compute_vehicle_info(self):
        """Concatena la información del vehículo en un solo campo"""
        for record in self:
            parts = []
            
            # Agregar marca si existe
            if record.vehicle_brand:
                parts.append(record.vehicle_brand)
            
            # Agregar modelo si existe
            if record.vehicle_model:
                parts.append(record.vehicle_model)
            
            # Agregar placa si existe
            if record.vehicle_plate:
                parts.append(f"Placa: {record.vehicle_plate}")
            
            # Unir con guiones
            if parts:
                record.vehicle_info = " - ".join(parts)
            else:
                record.vehicle_info = False
    # ========================================
    # EJECUCIÓN DEL SERVICIO
    # ========================================
    
    fecha_inicio = fields.Datetime(
        string='Fecha Inicio',
        tracking=True,
        readonly=True
    )
    
    fecha_fin = fields.Datetime(
        string='Fecha Fin',
        tracking=True,
        readonly=True
    )
    
    duracion_real = fields.Float(
        string='Duración Real (horas)',
        compute='_compute_duracion_real',
        store=True
    )
    
    diagnostico = fields.Text(
        string='Diagnóstico del Técnico'
    )
    
    trabajo_realizado = fields.Text(
        string='Trabajo Realizado',
        tracking=True
    )
    
    solucion_aplicada = fields.Selection([
        ('reparacion', 'Reparación'),
        ('ajuste', 'Ajuste'),
        ('limpieza', 'Limpieza'),
        ('actualizacion', 'Actualización'),
        ('reemplazo', 'Reemplazo de Componente'),
        ('configuracion', 'Configuración'),
        ('capacitacion', 'Capacitación'),
        ('otro', 'Otro')
    ], string='Tipo de Solución', tracking=True)
    
    insumos_utilizados = fields.Text(
        string='Insumos Utilizados',
        help='Descripción de insumos/repuestos utilizados'
    )
    
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=False
    )

    # Y agrega este método compute:

    @api.depends('prioridad', 'estado', 'sla_cumplido')
    def _compute_color(self):
        """Calcula el color para la vista kanban/list según prioridad y estado"""
        for record in self:
            # Prioridad crítica = rojo
            if record.prioridad == '3':
                record.color = 1  # Rojo
            # Prioridad alta = naranja
            elif record.prioridad == '2':
                record.color = 3  # Naranja
            # Completado = verde
            elif record.estado == 'completado':
                if record.sla_cumplido:
                    record.color = 10  # Verde
                else:
                    record.color = 9  # Rosa (completado pero SLA no cumplido)
            # Cancelado = gris
            elif record.estado == 'cancelado':
                record.color = 4  # Azul claro/gris
            # Pausado = amarillo
            elif record.estado == 'pausado':
                record.color = 5  # Amarillo
            # Normal = sin color
            else:
                record.color = 0  # Sin color
    
    # ========================================
    # CONTADORES
    # ========================================
    
    contador_bn = fields.Integer(
        string='Contador B/N',
        help='Contador blanco y negro al momento del servicio'
    )
    
    contador_color = fields.Integer(
        string='Contador Color',
        help='Contador color al momento del servicio'
    )
    
    contador_total = fields.Integer(
        string='Contador Total',
        compute='_compute_contador_total',
        store=True
    )
    
    # ========================================
    # EVIDENCIAS
    # ========================================
    
    foto_antes = fields.Binary(
        string='Foto Antes',
        attachment=True
    )
    
    foto_despues = fields.Binary(
        string='Foto Después',
        attachment=True
    )
    
    fotos_adicionales = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Fotos Adicionales',
        domain=[('res_model', '=', 'copier.service.request')],
        help='Fotos adicionales del servicio'
    )
    
    observaciones_tecnico = fields.Text(
        string='Observaciones del Técnico'
    )
    
    firma_cliente = fields.Binary(
        string='Firma del Cliente',
        attachment=True
    )
    
    nombre_firma = fields.Char(
        string='Nombre Quien Firma'
    )
    
    conformidad_cliente = fields.Boolean(
        string='Cliente Conforme',
        default=False
    )
    
    # ========================================
    # EVALUACIÓN
    # ========================================
    
    calificacion = fields.Selection([
        ('1', '⭐ Muy Malo'),
        ('2', '⭐⭐ Malo'),
        ('3', '⭐⭐⭐ Regular'),
        ('4', '⭐⭐⭐⭐ Bueno'),
        ('5', '⭐⭐⭐⭐⭐ Excelente')
    ], string='Calificación', tracking=True)
    
    comentario_cliente = fields.Text(
        string='Comentario del Cliente'
    )
    
    # ========================================
    # SLA (Service Level Agreement)
    # ========================================
    
    tiempo_respuesta = fields.Float(
        string='Tiempo de Respuesta (horas)',
        compute='_compute_sla',
        store=True,
        help='Tiempo desde creación hasta asignación de técnico'
    )
    
    tiempo_resolucion = fields.Float(
        string='Tiempo de Resolución (horas)',
        compute='_compute_sla',
        store=True,
        help='Tiempo desde creación hasta completado'
    )
    
    sla_cumplido = fields.Boolean(
        string='SLA Cumplido',
        compute='_compute_sla',
        store=True
    )
    
    sla_limite_1 = fields.Float(
        string='Límite SLA (horas)',
        compute='_compute_sla_limite',
        store=True
    )
    
    # ========================================
    # PAUSAS/CANCELACIONES
    # ========================================
    
    motivo_pausa = fields.Text(
        string='Motivo de Pausa'
    )
    
    fecha_pausa = fields.Datetime(
        string='Fecha de Pausa',
        readonly=True
    )
    
    motivo_cancelacion = fields.Text(
        string='Motivo de Cancelación'
    )
    
    fecha_cancelacion = fields.Datetime(
        string='Fecha de Cancelación',
        readonly=True
    )
    
    # ========================================
    # CONTROL DE NOTIFICACIONES
    # ========================================
    
    recordatorio_enviado = fields.Boolean(
        string='Recordatorio Enviado',
        default=False,
        help='Indica si ya se envió el recordatorio de evaluación',
        tracking=True
    )
    # ========================================
    # TOKENS DE ACCESO PÚBLICO
    # ========================================

    tracking_token = fields.Char(
        string='Token de Seguimiento',
        readonly=True,
        copy=False,
        index=True,
        help='Token único para seguimiento público sin login'
    )

    evaluation_token = fields.Char(
        string='Token de Evaluación',
        readonly=True,
        copy=False,
        index=True,
        help='Token único para evaluación pública sin login'
    )

    evaluation_token_used = fields.Boolean(
        string='Token de Evaluación Usado',
        default=False,
        readonly=True,
        help='Indica si el token de evaluación ya fue utilizado'
    )

    tracking_url = fields.Char(
        string='URL de Seguimiento',
        compute='_compute_public_urls',
        store=False,
        help='URL pública para seguimiento del servicio'
    )

    evaluation_url = fields.Char(
        string='URL de Evaluación',
        compute='_compute_public_urls',
        store=False,
        help='URL pública para evaluar el servicio'
    )

    fecha_evaluacion = fields.Datetime(
        string='Fecha de Evaluación',
        readonly=True,
        help='Fecha en que el cliente evaluó el servicio'
    )
    @api.depends('tracking_token', 'evaluation_token')
    def _compute_public_urls(self):
        """Calcular URLs públicas de seguimiento y evaluación"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        for record in self:
            if record.tracking_token:
                record.tracking_url = f"{base_url}/service/track/{record.tracking_token}"
            else:
                record.tracking_url = ''
            
            if record.evaluation_token:
                record.evaluation_url = f"{base_url}/service/evaluate/{record.evaluation_token}"
            else:
                record.evaluation_url = ''
    # ========================================
    # COMPUTED FIELDS
    # ========================================
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_duracion_real(self):
        """Calcula la duración real del servicio"""
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                delta = record.fecha_fin - record.fecha_inicio
                record.duracion_real = delta.total_seconds() / 3600.0
            else:
                record.duracion_real = 0.0
    
    @api.depends('contador_bn', 'contador_color')
    def _compute_contador_total(self):
        """Calcula el contador total"""
        for record in self:
            record.contador_total = (record.contador_bn or 0) + (record.contador_color or 0)
    
    @api.depends('prioridad')
    def _compute_sla_limite(self):
        """Calcula el límite SLA según la prioridad"""
        sla_map = {
            '3': 2.0,   # Crítica: 2 horas
            '2': 4.0,   # Alta: 4 horas
            '1': 24.0,  # Normal: 24 horas
            '0': 48.0   # Baja: 48 horas
        }
        for record in self:
            record.sla_limite_1 = sla_map.get(record.prioridad, 24.0)
    
    @api.depends('create_date', 'fecha_inicio', 'fecha_fin', 'sla_limite_1', 'estado')
    def _compute_sla(self):
        """Calcula los tiempos de SLA"""
        for record in self:
            # Tiempo de respuesta (hasta asignación)
            if record.fecha_inicio and record.create_date:
                delta = record.fecha_inicio - record.create_date
                record.tiempo_respuesta = delta.total_seconds() / 3600.0
            else:
                record.tiempo_respuesta = 0.0
            
            # Tiempo de resolución (hasta completado)
            if record.fecha_fin and record.create_date:
                delta = record.fecha_fin - record.create_date
                record.tiempo_resolucion = delta.total_seconds() / 3600.0
            else:
                record.tiempo_resolucion = 0.0
            
            # Verificar si se cumplió el SLA
            if record.estado == 'completado' and record.tiempo_resolucion:
                record.sla_cumplido = record.tiempo_resolucion <= record.sla_limite_1
            else:
                record.sla_cumplido = False
    
    # ========================================
    # MÉTODOS DE CREACIÓN
    # ========================================
    
    @api.model
    def create(self, vals):
        """
        Override create para asignar secuencia, congelar datos históricos,
        generar tokens y enviar notificaciones.

        Importante:
        - cliente_id se guarda como snapshot del cliente actual de la máquina.
        - ubicación, sede e IP también se congelan.
        - Si luego la máquina retorna y se asigna a otro cliente,
        este servicio no cambia de cliente ni ubicación histórica.
        """

        def _autocompletar_snapshot_desde_maquina(vals_dict):
            """
            Rellena datos desde la máquina SOLO si vienen vacíos en vals.

            Esto evita que el servicio dependa del cliente actual de la máquina
            después de creado.
            """
            maquina_id = vals_dict.get('maquina_id')
            if not maquina_id:
                return vals_dict

            maquina = self.env['copier.company'].browse(maquina_id).exists()
            if not maquina:
                return vals_dict

            cliente = maquina.cliente_id

            # ==============================
            # SNAPSHOT DEL CLIENTE
            # ==============================
            if cliente and not vals_dict.get('cliente_id'):
                vals_dict['cliente_id'] = cliente.id

            # ==============================
            # SNAPSHOT DE CONTACTO
            # ==============================
            if not vals_dict.get('correo'):
                vals_dict['correo'] = maquina.correo or cliente.email or False

            if not vals_dict.get('telefono_contacto'):
                vals_dict['telefono_contacto'] = (
                    maquina.celular
                    or cliente.mobile
                    or cliente.phone
                    or False
                )

            if not vals_dict.get('contacto'):
                vals_dict['contacto'] = (
                    maquina.contacto
                    or cliente.complete_name
                    or cliente.name
                    or False
                )

            # ==============================
            # SNAPSHOT DE UBICACIÓN
            # ==============================
            if not vals_dict.get('ubicacion'):
                vals_dict['ubicacion'] = maquina.ubicacion or False

            if not vals_dict.get('sede'):
                vals_dict['sede'] = maquina.sede or False

            if not vals_dict.get('ip_maquina'):
                vals_dict['ip_maquina'] = maquina.ip_id or False

            return vals_dict

        # =========================================================
        # SOPORTE PARA create() CON LISTA DE VALORES
        # =========================================================
        if isinstance(vals, list):
            records = self.env['copier.service.request']

            for val in vals:
                val = _autocompletar_snapshot_desde_maquina(val)

                if val.get('name', _('Nuevo')) == _('Nuevo'):
                    val['name'] = self.env['ir.sequence'].next_by_code(
                        'copier.service.request'
                    ) or _('Nuevo')

                record = super(CopierServiceRequest, self).create(val)
                records |= record

                record._generate_tokens()

                try:
                    record._send_email_confirmacion()
                except Exception as e:
                    _logger.error(
                        "Error enviando confirmación para %s: %s",
                        record.name,
                        str(e)
                    )

                record._notificar_nueva_solicitud()

            return records

        # =========================================================
        # SOPORTE PARA create() NORMAL
        # =========================================================
        vals = _autocompletar_snapshot_desde_maquina(vals)

        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'copier.service.request'
            ) or _('Nuevo')

        record = super(CopierServiceRequest, self).create(vals)

        record._generate_tokens()

        try:
            record._send_email_confirmacion()
        except Exception as e:
            _logger.error(
                "Error enviando email de confirmación: %s",
                str(e)
            )

        record._notificar_nueva_solicitud()

        return record

    @api.onchange('maquina_id')
    def _onchange_maquina_id(self):
        """
        Al seleccionar una máquina en el formulario:
        - Copia el cliente actual.
        - Copia contacto, correo, teléfono.
        - Copia ubicación, sede e IP.

        Estos datos quedan guardados en el servicio como historial.
        """
        for rec in self:
            if not rec.maquina_id:
                rec.cliente_id = False
                rec.contacto = False
                rec.correo = False
                rec.telefono_contacto = False
                rec.ubicacion = False
                rec.sede = False
                rec.ip_maquina = False
                continue

            maquina = rec.maquina_id
            cliente = maquina.cliente_id

            rec.cliente_id = cliente.id or False

            rec.contacto = (
                maquina.contacto
                or cliente.complete_name
                or cliente.name
                or False
            )

            rec.correo = (
                maquina.correo
                or cliente.email
                or False
            )

            rec.telefono_contacto = (
                maquina.celular
                or cliente.mobile
                or cliente.phone
                or False
            )

            rec.ubicacion = maquina.ubicacion or False
            rec.sede = maquina.sede or False
            rec.ip_maquina = maquina.ip_id or False
    def write(self, vals):
        """Override write para notificar cambios de estado"""
        res = super(CopierServiceRequest, self).write(vals)
        
        # Notificar cambios de estado importantes
        if 'estado' in vals:
            for record in self:
                record._notificar_cambio_estado(vals['estado'])
        
        return res
    
    # ========================================
    # ACCIONES DE WORKFLOW
    # ========================================
    
    def action_asignar_tecnico(self):
        """Asignar técnico a la solicitud"""
        self.ensure_one()
        
        if not self.tecnico_id:
            raise ValidationError(_("Debe asignar un técnico antes de continuar."))
        
        self.write({'estado': 'asignado'})
        
        # ✅ OPCIÓN 1: Crear actividad para el usuario que ejecuta la acción
        # (el administrador o supervisor que asigna)
        try:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.env.user.id,  # ✅ Usuario actual, no el técnico
                summary=f'Servicio técnico asignado a {self.tecnico_id.name}: {self.name}',
                note=f'''
                    Técnico: {self.tecnico_id.name}
                    Problema: {self.tipo_problema_id.name}
                    Cliente: {self.cliente_id.name}
                    Ubicación: {self.ubicacion}
                '''
            )
        except Exception as e:
            _logger.warning(f"No se pudo crear actividad: {str(e)}")
        
        # ✅ OPCIÓN 2: Si el técnico tiene usuario vinculado, crear actividad para él
        # (solo si tiene cuenta de usuario)
        if self.tecnico_id.user_ids:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=self.tecnico_id.user_ids[0].id,
                    summary=f'Servicio técnico programado: {self.name}',
                    note=f'Problema: {self.tipo_problema_id.name}\nCliente: {self.cliente_id.name}\nUbicación: {self.ubicacion}'
                )
            except Exception as e:
                _logger.warning(f"No se pudo crear actividad para técnico: {str(e)}")
        
        # ✅ Notificar al técnico en el chatter (siempre funciona con res.partner)
        self.message_post(
            body=f'''
                👨‍🔧 Técnico Asignado: {self.tecnico_id.name}
                
                • Cliente: {self.cliente_id.name}
                • Equipo: {self.modelo_maquina.name}
                • Ubicación: {self.ubicacion}
                • Problema: {self.tipo_problema_id.name}
            ''',
            partner_ids=[self.tecnico_id.id]  # ✅ Notificar al partner directamente
        )
        
        return True

    
    def action_confirmar_visita(self):
        """Confirmar fecha de visita del técnico"""
        self.ensure_one()
        
        if not self.fecha_programada:
            raise ValidationError(_("Debe programar una fecha para la visita."))
        
        self.write({'estado': 'confirmado'})
        
        # Enviar email al cliente con técnico asignado
        try:
            self._send_email_tecnico_asignado()
        except Exception as e:
            _logger.error("Error enviando email técnico asignado: %s", str(e))
        
        return True
    
    def action_iniciar_ruta(self):
        """Técnico indica que está en camino"""
        self.ensure_one()
        
        if not self.tecnico_id:
            raise ValidationError(_("No hay técnico asignado a esta solicitud."))
        
        self.write({'estado': 'en_ruta'})
        
        self.message_post(
            body=f'''
                🚗 Técnico en Ruta
                
                • Técnico: {self.tecnico_id.name}
                • Hora: {fields.Datetime.now().strftime('%H:%M')}
            '''
        )
        
        return True
        
    def action_iniciar_servicio(self):
        """Técnico hace check-in en el sitio"""
        self.ensure_one()
        
        if not self.tecnico_id:
            raise ValidationError(_("No hay técnico asignado a esta solicitud."))
        
        self.write({
            'estado': 'en_sitio',
            'fecha_inicio': fields.Datetime.now()
        })
        
        self.message_post(
            body=f'''
                ✅ Servicio Iniciado
                
                • Técnico: {self.tecnico_id.name}
                • Hora inicio: {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}
            '''
        )
        
        return True
    
    def action_pausar_servicio(self):
        """Pausar servicio temporalmente"""
        return {
            'name': _('Pausar Servicio'),
            'type': 'ir.actions.act_window',
            'res_model': 'copier.service.pause.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    def action_completar_servicio(self):
        """Completar servicio técnico"""
        self.ensure_one()
        
        if not self.trabajo_realizado:
            raise ValidationError(_("Debe describir el trabajo realizado antes de completar."))
        
        self.write({
            'estado': 'completado',
            'fecha_fin': fields.Datetime.now()
        })
        
        # Registrar contador si hay valores
        if self.contador_bn or self.contador_color:
            try:
                self._registrar_contador()
            except Exception as e:
                _logger.error("Error registrando contador: %s", str(e))
        
        # Enviar email de servicio completado
        try:
            self._send_email_completado()
        except Exception as e:
            _logger.error("Error enviando email de completado: %s", str(e))
        
        return True
    
    def action_cancelar_servicio(self):
        """Cancelar servicio"""
        return {
            'name': _('Cancelar Servicio'),
            'type': 'ir.actions.act_window',
            'res_model': 'copier.service.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    
    def _registrar_contador(self):
        """
        Crea un registro de contador al completar el servicio.

        Importante:
        - Usa cliente_id del servicio, no el cliente actual de la máquina.
        - Así no se contamina el historial si la máquina fue reasignada.
        """
        self.ensure_one()

        if not self.contador_bn and not self.contador_color:
            return

        counter_vals = {
            'maquina_id': self.maquina_id.id,
            'cliente_id': self.cliente_id.id or self.maquina_id.cliente_id.id or False,
            'fecha': self.fecha_fin or fields.Datetime.now(),
            'contador_actual_bn': self.contador_bn,
            'contador_actual_color': self.contador_color,
            'observaciones': f'Registrado desde servicio técnico {self.name}',
            'state': 'draft',
        }

        try:
            counter = self.env['copier.counter'].create(counter_vals)
            _logger.info(
                "Contador creado desde servicio %s: ID=%s Cliente=%s",
                self.name,
                counter.id,
                self.cliente_id.display_name if self.cliente_id else 'Sin cliente'
            )

            self.message_post(
                body=f'''
                    📊 Contador Registrado

                    • Cliente: {self.cliente_id.name if self.cliente_id else 'N/A'}
                    • B/N: {self.contador_bn:,}
                    • Color: {self.contador_color:,}
                    • Total: {self.contador_total:,}
                '''
            )
        except Exception as e:
            _logger.exception("Error creando contador: %s", str(e))
            raise
    
    def _notificar_nueva_solicitud(self):
        """Notifica la creación de una nueva solicitud en el chatter"""
        self.ensure_one()
        
        self.message_post(
            body=f'''
                📋 Nueva Solicitud de Servicio Creada
                
                • Cliente: {self.cliente_id.name}
                • Máquina: {self.modelo_maquina.name}
                • Ubicación: {self.ubicacion}
                • Problema: {self.tipo_problema_id.name}
                • Prioridad: {dict(self._fields['prioridad'].selection)[self.prioridad]}
            ''',
            message_type='notification'
        )
    
    def _notificar_cambio_estado(self, nuevo_estado):
        """Notifica cambios de estado importantes"""
        self.ensure_one()
        
        estados_importantes = ['asignado', 'en_ruta', 'en_sitio', 'completado', 'cancelado']
        
        if nuevo_estado in estados_importantes:
            estado_nombre = dict(self._fields['estado'].selection)[nuevo_estado]
            
            self.message_post(
                body=f'''
                    🔄 Cambio de Estado: {estado_nombre}
                    
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                    • Usuario: {self.env.user.name}
                ''',
                message_type='notification'
            )
    def registrar_evaluacion_publica(self, calificacion, comentario=''):
        """
        Registrar evaluación desde formulario público
        
        Args:
            calificacion (str): '1' a '5'
            comentario (str): Comentario opcional del cliente
        """
        self.ensure_one()
        
        # Validar que esté completado
        if self.estado != 'completado':
            raise ValidationError(_('Solo se pueden evaluar servicios completados.'))
        
        # Validar que no esté ya evaluado
        if self.calificacion:
            raise ValidationError(_('Este servicio ya fue evaluado.'))
        
        # Validar que el token no haya sido usado
        if self.evaluation_token_used:
            raise ValidationError(_('El enlace de evaluación ya fue utilizado.'))
        
        # Guardar evaluación
        self.write({
            'calificacion': calificacion,
            'comentario_cliente': comentario,
            'fecha_evaluacion': fields.Datetime.now(),
            'evaluation_token_used': True,
        })
        
        _logger.info("✅ Evaluación registrada para solicitud %s: %s estrellas", 
                    self.name, calificacion)
        
        # Registrar en chatter
        estrellas = '⭐' * int(calificacion)
        self.message_post(
            body=f'''
                ⭐ Evaluación del Cliente
                
                • Calificación: {estrellas}
                • Comentario: {comentario or 'Sin comentarios'}
                • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
            ''',
            message_type='notification'
        )
    def get_tracking_data(self):
        """
        Obtener datos para la página de seguimiento público
        
        Returns:
            dict: Datos del servicio para mostrar públicamente
        """
        self.ensure_one()
        
        # Estados con iconos
        estado_icons = {
            'nuevo': '🆕',
            'asignado': '👨‍🔧',
            'confirmado': '✅',
            'en_ruta': '🚗',
            'en_sitio': '🔧',
            'pausado': '⏸️',
            'completado': '✅',
            'cancelado': '❌',
        }
        
        # Prioridades
        prioridad_names = {
            '0': 'Baja',
            '1': 'Normal',
            '2': 'Alta',
            '3': 'Crítica'
        }
        
        # Timeline de eventos
        timeline = []
        
        # Evento: Creación
        timeline.append({
            'fecha': self.create_date,
            'titulo': 'Solicitud Creada',
            'descripcion': f'Tu solicitud fue registrada con éxito',
            'icon': '📋',
            'completed': True
        })
        
        # Evento: Técnico asignado
        if self.tecnico_id:
            timeline.append({
                'fecha': self.write_date,
                'titulo': 'Técnico Asignado',
                'descripcion': f'Técnico: {self.tecnico_id.name}',
                'icon': '👨‍🔧',
                'completed': True
            })
        
        # Evento: Servicio iniciado
        if self.fecha_inicio:
            timeline.append({
                'fecha': self.fecha_inicio,
                'titulo': 'Servicio Iniciado',
                'descripcion': 'El técnico comenzó a trabajar en tu equipo',
                'icon': '🔧',
                'completed': True
            })
        
        # Evento: Servicio completado
        if self.fecha_fin:
            timeline.append({
                'fecha': self.fecha_fin,
                'titulo': 'Servicio Completado',
                'descripcion': 'El servicio fue finalizado exitosamente',
                'icon': '✅',
                'completed': True
            })
        
        return {
            'numero': self.name,
            'estado': dict(self._fields['estado'].selection).get(self.estado),
            'estado_icon': estado_icons.get(self.estado, '📋'),
            'estado_key': self.estado,
            'prioridad': prioridad_names.get(self.prioridad, 'Normal'),
            'fecha_creacion': self.create_date,
            'cliente': self.cliente_id.name if self.cliente_id else 'N/A',
            'equipo': self.modelo_maquina.name if self.modelo_maquina else 'N/A',
            'serie': self.serie_maquina or 'N/A',
            'ubicacion': self.ubicacion or 'N/A',
            'problema': self.tipo_problema_id.name if self.tipo_problema_id else 'N/A',
            'tecnico': self.tecnico_id.name if self.tecnico_id else 'Por asignar',
            'tecnico_telefono': self.tecnico_id.phone if self.tecnico_id and self.tecnico_id.phone else None,
            'vehicle_info': self.vehicle_info,  # ✅ Campo computado
            'fecha_programada': self.fecha_programada,
            'trabajo_realizado': self.trabajo_realizado if self.estado == 'completado' else None,
            'timeline': sorted(timeline, key=lambda x: x['fecha']),
            'puede_evaluar': self.estado == 'completado' and not self.calificacion,
            'ya_evaluado': bool(self.calificacion),
            'calificacion': self.calificacion if self.calificacion else None,
        }
    def _generate_tokens(self):
        """Generar tokens únicos de seguimiento y evaluación"""
        import uuid
        
        self.ensure_one()
        
        if not self.tracking_token:
            self.tracking_token = str(uuid.uuid4()).replace('-', '')
            _logger.info("Token de seguimiento generado para solicitud %s: %s", 
                        self.name, self.tracking_token[:8] + "...")
        
        if not self.evaluation_token:
            self.evaluation_token = str(uuid.uuid4()).replace('-', '')
            _logger.info("Token de evaluación generado para solicitud %s: %s", 
                        self.name, self.evaluation_token[:8] + "...")
    # ========================================
    # CRON JOB: VERIFICAR SLA
    # ========================================
    
    @api.model
    def _cron_check_sla(self):
        """Verifica SLAs próximos a vencer y envía alertas"""
        _logger.info("=== INICIANDO CRON: Verificación de SLA ===")
        
        # Buscar solicitudes pendientes
        solicitudes = self.search([
            ('estado', 'not in', ['completado', 'cancelado']),
            ('create_date', '!=', False)
        ])
        
        alertas_enviadas = 0
        
        for solicitud in solicitudes:
            try:
                # Calcular tiempo transcurrido
                tiempo_transcurrido = (fields.Datetime.now() - solicitud.create_date).total_seconds() / 3600.0
                tiempo_restante = solicitud.sla_limite_1 - tiempo_transcurrido
                
                # Alertar si queda menos de 1 hora
                if 0 < tiempo_restante <= 1.0:
                    solicitud.message_post(
                        body=f'''
                            ⚠️ ALERTA SLA
                            
                            • Tiempo restante: {tiempo_restante:.1f} horas
                            • Límite SLA: {solicitud.sla_limite_1} horas
                            • Prioridad: {dict(solicitud._fields['prioridad'].selection)[solicitud.prioridad]}
                            
                            ¡ACCIÓN REQUERIDA!
                        ''',
                        message_type='notification'
                    )
                    alertas_enviadas += 1
                    
            except Exception as e:
                _logger.error("Error verificando SLA para solicitud %s: %s", solicitud.name, str(e))
                continue
        
        _logger.info("=== CRON FINALIZADO: %s alertas enviadas ===", alertas_enviadas)
    
    # ========================================
    # MÉTODOS DE NOTIFICACIÓN POR EMAIL
    # ========================================
    
    def _send_email_confirmacion(self):
        """
        Envía email de confirmación al crear la solicitud.
        Se llama desde: create()
        """
        self.ensure_one()
        _logger.info("=== Enviando email de confirmación para solicitud %s ===", self.name)
        
        try:
            # Validar que haya un correo
            if not self.correo:
                _logger.warning("No se puede enviar confirmación: solicitud %s no tiene email", self.name)
                return False
            
            # Buscar la plantilla
            template = self.env.ref('copier_company.email_template_service_confirmacion', raise_if_not_found=False)
            if not template:
                _logger.error("Plantilla email_template_service_confirmacion no encontrada")
                return False
            
            _logger.info("Plantilla encontrada: %s (ID: %s)", template.name, template.id)
            
            # Enviar el email
            template.send_mail(
                self.id,
                force_send=True,  # Enviar inmediatamente
                email_values={
                    'email_to': self.correo,
                    'email_from': 'info@copiercompanysac.com',
                }
            )
            
            _logger.info("✅ Email de confirmación enviado a: %s", self.correo)
            
            # Registrar en el chatter
            self.message_post(
                body=f'''
                    📧 Email de Confirmación Enviado
                    
                    • Destinatario: {self.correo}
                    • Plantilla: Confirmación de Solicitud
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            
            return True
            
        except Exception as e:
            _logger.exception("Error al enviar email de confirmación: %s", str(e))
            self.message_post(
                body=f'''
                    ❌ Error al enviar email de confirmación
                    
                    • Error: {str(e)}
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            return False
    
    def _send_email_tecnico_asignado(self):
        """
        Envía email cuando se asigna un técnico.
        Se llama desde: action_confirmar_visita()
        """
        self.ensure_one()
        _logger.info("=== Enviando email técnico asignado para solicitud %s ===", self.name)
        
        try:
            # Validaciones
            if not self.correo:
                _logger.warning("No se puede enviar email: solicitud %s no tiene email", self.name)
                return False
            
            if not self.tecnico_id:
                _logger.warning("No se puede enviar email: solicitud %s no tiene técnico asignado", self.name)
                return False
            
            if not self.fecha_programada:
                _logger.warning("No se puede enviar email: solicitud %s no tiene fecha programada", self.name)
                return False
            
            # Buscar la plantilla
            template = self.env.ref('copier_company.email_template_service_tecnico_asignado', raise_if_not_found=False)
            if not template:
                _logger.error("Plantilla email_template_service_tecnico_asignado no encontrada")
                return False
            
            _logger.info("Plantilla encontrada: %s (ID: %s)", template.name, template.id)
            
            # Enviar el email
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.correo,
                    'email_from': 'info@copiercompanysac.com',
                }
            )
            
            _logger.info("✅ Email técnico asignado enviado a: %s", self.correo)
            
            # Registrar en el chatter
            self.message_post(
                body=f'''
                    📧 Email de Técnico Asignado Enviado
                    
                    • Destinatario: {self.correo}
                    • Técnico: {self.tecnico_id.name}
                    • Fecha programada: {self.fecha_programada.strftime('%d/%m/%Y %H:%M')}
                    • Fecha envío: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            
            return True
            
        except Exception as e:
            _logger.exception("Error al enviar email técnico asignado: %s", str(e))
            self.message_post(
                body=f'''
                    ❌ Error al enviar email de técnico asignado
                    
                    • Error: {str(e)}
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            return False
    def action_print_service_report(self):
        """Imprimir reporte PDF del servicio técnico"""
        self.ensure_one()
        return self.env.ref(
            'copier_company.action_report_service_request'
        ).report_action(self)
    def _send_email_completado(self):
        """
        Envía email cuando se completa el servicio.
        Incluye solicitud de evaluación y reporte PDF.
        Se llama desde: action_completar_servicio()
        """
        self.ensure_one()
        _logger.info("=== Enviando email servicio completado para solicitud %s ===", self.name)
        
        try:
            # Validaciones
            if not self.correo:
                _logger.warning("No se puede enviar email: solicitud %s no tiene email", self.name)
                return False
            
            if self.estado != 'completado':
                _logger.warning("No se puede enviar email: solicitud %s no está completada (estado: %s)", 
                            self.name, self.estado)
                return False
            
            # Buscar la plantilla
            template = self.env.ref('copier_company.email_template_service_completado', raise_if_not_found=False)
            if not template:
                _logger.error("Plantilla email_template_service_completado no encontrada")
                return False
            
            _logger.info("Plantilla encontrada: %s (ID: %s)", template.name, template.id)
            
            # ✅ GENERAR PDF CON MANEJO DE ERRORES
            attachment_id = None
            try:
                # Buscar el reporte
                report = self.env.ref('copier_company.action_report_service_request', raise_if_not_found=False)
                
                if report:
                    _logger.info("Generando PDF del reporte ID: %s", report.id)
                    
                    # Generar PDF
                    pdf_content, _ = report.render_qweb_pdf([self.id])
                    
                    # Crear adjunto
                    attachment = self.env['ir.attachment'].create({
                        'name': f'Reporte_Servicio_{self.name}.pdf',
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/pdf',
                    })
                    attachment_id = attachment.id
                    _logger.info("PDF generado y adjunto creado: ID %s", attachment_id)
                else:
                    _logger.warning("Reporte 'action_report_service_request' no encontrado, se enviará email sin PDF")
                    
            except Exception as e:
                _logger.error("Error generando PDF del reporte: %s", str(e))
                _logger.info("Continuando envío de email sin adjunto PDF")
                # Continuamos sin el PDF
            
            # ✅ ENVIAR EMAIL (con o sin PDF)
            email_values = {
                'email_to': self.correo,
                'email_from': 'info@copiercompanysac.com',
            }
            
            # Agregar adjunto solo si se generó correctamente
            if attachment_id:
                email_values['attachment_ids'] = [(4, attachment_id)]
            
            template.send_mail(
                self.id,
                force_send=True,
                email_values=email_values
            )
            
            _logger.info("✅ Email servicio completado enviado a: %s", self.correo)
            
            # Registrar en el chatter
            mensaje_pdf = " (con reporte PDF adjunto)" if attachment_id else " (sin reporte PDF)"
            self.message_post(
                body=f'''
                    📧 Email de Servicio Completado Enviado{mensaje_pdf}
                    
                    • Destinatario: {self.correo}
                    • Técnico: {self.tecnico_id.name if self.tecnico_id else 'N/A'}
                    • Fecha finalización: {self.fecha_fin.strftime('%d/%m/%Y %H:%M') if self.fecha_fin else 'N/A'}
                    • Fecha envío: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                    • Incluye: Solicitud de evaluación
                ''',
                message_type='notification'
            )
            
            return True
            
        except Exception as e:
            _logger.exception("Error al enviar email servicio completado: %s", str(e))
            self.message_post(
                body=f'''
                    ❌ Error al enviar email de servicio completado
                    
                    • Error: {str(e)}
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            return False
    
    def _send_email_recordatorio_evaluacion(self):
        """
        Envía UN SOLO recordatorio de evaluación.
        Se llama desde: _cron_enviar_recordatorio_evaluacion()
        Solo se envía si:
        - Han pasado 48 horas desde la finalización
        - No ha calificado
        - No se ha enviado recordatorio antes
        """
        self.ensure_one()
        _logger.info("=== Enviando recordatorio de evaluación para solicitud %s ===", self.name)
        
        try:
            # Validaciones
            if not self.correo:
                _logger.warning("No se puede enviar recordatorio: solicitud %s no tiene email", self.name)
                return False
            
            if self.estado != 'completado':
                _logger.warning("No se puede enviar recordatorio: solicitud %s no está completada", self.name)
                return False
            
            if self.calificacion:
                _logger.info("No se envía recordatorio: solicitud %s ya fue calificada", self.name)
                return False
            
            if self.recordatorio_enviado:
                _logger.info("No se envía recordatorio: solicitud %s ya recibió recordatorio", self.name)
                return False
            
            # Buscar la plantilla
            template = self.env.ref('copier_company.email_template_service_recordatorio_evaluacion', raise_if_not_found=False)
            if not template:
                _logger.error("Plantilla email_template_service_recordatorio_evaluacion no encontrada")
                return False
            
            _logger.info("Plantilla encontrada: %s (ID: %s)", template.name, template.id)
            
            # Enviar el email
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.correo,
                    'email_from': 'info@copiercompanysac.com',
                }
            )
            
            # MARCAR QUE YA SE ENVIÓ (IMPORTANTE)
            self.write({'recordatorio_enviado': True})
            
            _logger.info("✅ Recordatorio de evaluación enviado a: %s", self.correo)
            
            # Registrar en el chatter
            self.message_post(
                body=f'''
                    📧 Recordatorio de Evaluación Enviado
                    
                    • Destinatario: {self.correo}
                    • Días desde finalización: {(fields.Datetime.now() - self.fecha_fin).days if self.fecha_fin else 'N/A'}
                    • Fecha envío: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                    • Nota: Este es el único recordatorio que se enviará
                ''',
                message_type='notification'
            )
            
            return True
            
        except Exception as e:
            _logger.exception("Error al enviar recordatorio de evaluación: %s", str(e))
            self.message_post(
                body=f'''
                    ❌ Error al enviar recordatorio de evaluación
                    
                    • Error: {str(e)}
                    • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
                ''',
                message_type='notification'
            )
            return False
    
    # ========================================
    # CRON JOB: RECORDATORIO DE EVALUACIÓN
    # ========================================
    
    @api.model
    def _cron_enviar_recordatorio_evaluacion(self):
        """
        Cron job que se ejecuta diariamente.
        Busca servicios completados hace 48 horas sin calificación
        y envía recordatorio por EMAIL y WHATSAPP.
        """
        _logger.info("=== INICIANDO CRON: Envío de recordatorios de evaluación ===")
        
        try:
            now = fields.Datetime.now()
            fecha_48h_antes = now - timedelta(hours=48)
            fecha_46h_antes = now - timedelta(hours=46)
            fecha_50h_antes = now - timedelta(hours=50)
            
            _logger.info("Buscando servicios completados entre %s y %s", 
                        fecha_50h_antes.strftime('%d/%m/%Y %H:%M'),
                        fecha_46h_antes.strftime('%d/%m/%Y %H:%M'))
            
            domain = [
                ('estado', '=', 'completado'),
                ('fecha_fin', '!=', False),
                ('fecha_fin', '>=', fecha_50h_antes),
                ('fecha_fin', '<=', fecha_46h_antes),
                ('calificacion', '=', False),
                ('recordatorio_enviado', '=', False),
                ('correo', '!=', False),
            ]
            
            solicitudes = self.search(domain)
            
            _logger.info("Solicitudes encontradas: %s", len(solicitudes))
            
            if not solicitudes:
                _logger.info("No hay solicitudes pendientes de recordatorio")
                return
            
            enviados_email = 0
            enviados_whatsapp = 0
            errores = 0
            
            for solicitud in solicitudes:
                try:
                    _logger.info("Procesando solicitud %s (ID: %s)", solicitud.name, solicitud.id)
                    
                    # Enviar EMAIL
                    if solicitud._send_email_recordatorio_evaluacion():
                        enviados_email += 1
                    else:
                        errores += 1
                    
                    # ✅ ENVIAR WHATSAPP
                    try:
                        if solicitud._notify_evaluation_reminder():
                            enviados_whatsapp += 1
                    except Exception as e:
                        _logger.error("Error enviando recordatorio WhatsApp: %s", str(e))
                        
                except Exception as e:
                    _logger.exception("Error procesando solicitud %s: %s", solicitud.name, str(e))
                    errores += 1
                    continue
            
            _logger.info("=== CRON FINALIZADO ===")
            _logger.info("Total procesadas: %s", len(solicitudes))
            _logger.info("Emails enviados: %s", enviados_email)
            _logger.info("WhatsApp enviados: %s", enviados_whatsapp)
            _logger.info("Errores: %s", errores)
            
        except Exception as e:
            _logger.exception("Error general en CRON de recordatorios: %s", str(e))

# ========================================
# WIZARDS
# ========================================

class CopierServicePauseWizard(models.TransientModel):
    """Wizard para pausar un servicio"""
    _name = 'copier.service.pause.wizard'
    _description = 'Pausar Servicio Técnico'
    
    request_id = fields.Many2one(
        'copier.service.request',
        string='Solicitud',
        required=True
    )
    
    motivo_pausa = fields.Text(
        string='Motivo de la Pausa',
        required=True
    )
    
    def action_pausar(self):
        """Confirma la pausa del servicio"""
        self.ensure_one()
        
        self.request_id.write({
            'estado': 'pausado',
            'motivo_pausa': self.motivo_pausa,
            'fecha_pausa': fields.Datetime.now()
        })
        
        self.request_id.message_post(
            body=f'''
                ⏸️ Servicio Pausado
                
                • Motivo: {self.motivo_pausa}
                • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
            ''',
            message_type='notification'
        )
        
        return {'type': 'ir.actions.act_window_close'}


class CopierServiceCancelWizard(models.TransientModel):
    """Wizard para cancelar un servicio"""
    _name = 'copier.service.cancel.wizard'
    _description = 'Cancelar Servicio Técnico'
    
    request_id = fields.Many2one(
        'copier.service.request',
        string='Solicitud',
        required=True
    )
    
    motivo_cancelacion = fields.Text(
        string='Motivo de la Cancelación',
        required=True
    )
    
    def action_cancelar(self):
        """Confirma la cancelación del servicio"""
        self.ensure_one()
        
        self.request_id.write({
            'estado': 'cancelado',
            'motivo_cancelacion': self.motivo_cancelacion,
            'fecha_cancelacion': fields.Datetime.now()
        })
        
        self.request_id.message_post(
            body=f'''
                ❌ Servicio Cancelado
                
                • Motivo: {self.motivo_cancelacion}
                • Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
            ''',
            message_type='notification'
        )
        
        return {'type': 'ir.actions.act_window_close'}