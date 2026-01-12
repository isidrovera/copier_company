from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class CopierServiceRequest(models.Model):
    _name = 'copier.service.request'
    _description = 'Solicitudes de Servicio Técnico'
    _inherit = ['mail.thread', 'mail.activity.mixin']
   

    # ==========================================
    # CAMPOS BÁSICOS
    # ==========================================
    
    name = fields.Char(
        string='Número de Solicitud',
        default='New',
        copy=False,
        required=True,
        readonly=True,
        tracking=True
    )
    
    maquina_id = fields.Many2one(
        'copier.company',
        string='Máquina',
        required=True,
        tracking=True,
        ondelete='restrict'
    )
    
    # Campos relacionados auto-completados desde la máquina
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='maquina_id.cliente_id',
        store=True,
        readonly=True
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
        related='maquina_id.ubicacion',
        store=True,
        readonly=True
    )
    
    sede = fields.Char(
        string='Sede',
        related='maquina_id.sede',
        store=True,
        readonly=True
    )
    
    ip_maquina = fields.Char(
        string='IP',
        related='maquina_id.ip_id',
        store=True,
        readonly=True
    )
    
    contacto = fields.Char(
        string='Persona de Contacto',
        related='maquina_id.contacto',
        store=True
    )
    
    telefono_contacto = fields.Char(
        string='Teléfono',
        related='maquina_id.celular',
        store=True
    )
    
    # ==========================================
    # INFORMACIÓN DE LA SOLICITUD
    # ==========================================
    
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
        ('whatsapp', 'WhatsApp'),
        ('telefono', 'Teléfono'),
        ('email', 'Email'),
        ('interno', 'Interno'),
    ],
        string='Origen',
        required=True,
        default='telefono',
        tracking=True
    )
    
    prioridad = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Normal'),
        ('2', 'Alta'),
        ('3', 'Crítica'),
    ],
        string='Prioridad',
        default='1',
        required=True,
        tracking=True
    )
    
    estado = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('confirmado', 'Confirmado'),
        ('en_ruta', 'En Ruta'),
        ('en_sitio', 'En Sitio'),
        ('pausado', 'Pausado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ],
        string='Estado',
        default='nuevo',
        required=True,
        tracking=True
    )
    
    # ==========================================
    # ASIGNACIÓN Y PROGRAMACIÓN
    # ==========================================
    
    tecnico_id = fields.Many2one(
        'res.users',
        string='Técnico Asignado',
        tracking=True
        
    )
    
    tecnico_respaldo_id = fields.Many2one(
        'res.users',
        string='Técnico de Respaldo',
        tracking=True
       
    )
    
    fecha_programada = fields.Datetime(
        string='Fecha/Hora Programada',
        tracking=True
    )
    
    duracion_estimada = fields.Float(
        string='Duración Estimada (horas)',
        default=3.0
    )
    
    # ==========================================
    # EJECUCIÓN DEL SERVICIO
    # ==========================================
    
    fecha_inicio = fields.Datetime(
        string='Inicio del Servicio',
        readonly=True,
        tracking=True
    )
    
    fecha_fin = fields.Datetime(
        string='Fin del Servicio',
        readonly=True,
        tracking=True
    )
    
    duracion_real = fields.Float(
        string='Duración Real (horas)',
        compute='_compute_duracion_real',
        store=True
    )
    
    diagnostico = fields.Text(
        string='Diagnóstico Técnico',
        tracking=True
    )
    
    trabajo_realizado = fields.Text(
        string='Trabajo Realizado',
        tracking=True
    )
    
    solucion_aplicada = fields.Selection([
        ('reparado', 'Reparado en Sitio'),
        ('seguimiento', 'Requiere Seguimiento'),
        ('taller', 'Equipo Llevado a Taller'),
        ('respaldo', 'Equipo de Respaldo Dejado'),
        ('externo', 'Problema Externo (Cliente)'),
        ('no_resuelto', 'No Resuelto'),
    ],
        string='Solución Aplicada',
        tracking=True
    )
    
    insumos_utilizados = fields.Text(
        string='Insumos/Repuestos Utilizados',
        help='Tóner, kits de mantenimiento, piezas, etc.'
    )
    
    # ==========================================
    # CONTADORES AL MOMENTO DEL SERVICIO
    # ==========================================
    
    contador_bn = fields.Integer(
        string='Contador B/N',
        help='Contador blanco y negro al momento del servicio'
    )
    
    contador_color = fields.Integer(
        string='Contador Color',
        help='Contador a color al momento del servicio'
    )
    
    contador_total = fields.Integer(
        string='Contador Total',
        compute='_compute_contador_total',
        store=True
    )
    
    # ==========================================
    # EVIDENCIAS Y CONFORMIDAD
    # ==========================================
    
    foto_antes = fields.Binary(
        string='Foto Antes',
        attachment=True
    )
    
    foto_despues = fields.Binary(
        string='Foto Después',
        attachment=True
    )
    
    fotos_adicionales = fields.Many2many(
        'ir.attachment',
        'service_request_attachment_rel',
        'service_id',
        'attachment_id',
        string='Fotos Adicionales'
    )
    
    observaciones_tecnico = fields.Text(
        string='Observaciones del Técnico'
    )
    
    firma_cliente = fields.Binary(
        string='Firma del Cliente',
        attachment=True
    )
    
    nombre_firma = fields.Char(
        string='Nombre quien firma',
        tracking=True
    )
    
    conformidad_cliente = fields.Boolean(
        string='Cliente Conforme',
        default=False,
        tracking=True
    )
    
    # ==========================================
    # EVALUACIÓN
    # ==========================================
    
    calificacion = fields.Selection([
        ('1', '⭐ Muy Insatisfecho'),
        ('2', '⭐⭐ Insatisfecho'),
        ('3', '⭐⭐⭐ Neutral'),
        ('4', '⭐⭐⭐⭐ Satisfecho'),
        ('5', '⭐⭐⭐⭐⭐ Muy Satisfecho'),
    ],
        string='Calificación del Cliente',
        tracking=True
    )
    
    comentario_cliente = fields.Text(
        string='Comentarios del Cliente'
    )
    
    # ==========================================
    # SLA Y MÉTRICAS
    # ==========================================
    
    tiempo_respuesta = fields.Float(
        string='Tiempo de Respuesta (horas)',
        compute='_compute_tiempos_sla',
        store=True,
        help='Tiempo desde creación hasta asignación'
    )
    
    tiempo_resolucion = fields.Float(
        string='Tiempo de Resolución (horas)',
        compute='_compute_tiempos_sla',
        store=True,
        help='Tiempo desde creación hasta completado'
    )
    
    sla_cumplido = fields.Boolean(
        string='SLA Cumplido',
        compute='_compute_sla_cumplido',
        store=True
    )
    
    sla_limite = fields.Datetime(
        string='Límite SLA',
        compute='_compute_sla_limite',
        store=True
    )
    
    # ==========================================
    # CAMPOS TÉCNICOS
    # ==========================================
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )
    
    active = fields.Boolean(
        default=True
    )
    
    color = fields.Integer(
        string='Color',
        compute='_compute_color'
    )

    # ==========================================
    # MÉTODOS COMPUTE
    # ==========================================
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_duracion_real(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                delta = record.fecha_fin - record.fecha_inicio
                record.duracion_real = delta.total_seconds() / 3600  # convertir a horas
            else:
                record.duracion_real = 0.0
    
    @api.depends('contador_bn', 'contador_color')
    def _compute_contador_total(self):
        for record in self:
            record.contador_total = (record.contador_bn or 0) + (record.contador_color or 0)
    
    @api.depends('create_date', 'fecha_programada', 'fecha_fin', 'estado')
    def _compute_tiempos_sla(self):
        for record in self:
            # Tiempo de respuesta: creación → asignación/programación
            if record.create_date and record.fecha_programada:
                delta = record.fecha_programada - record.create_date
                record.tiempo_respuesta = delta.total_seconds() / 3600
            else:
                record.tiempo_respuesta = 0.0
            
            # Tiempo de resolución: creación → completado
            if record.create_date and record.fecha_fin and record.estado == 'completado':
                delta = record.fecha_fin - record.create_date
                record.tiempo_resolucion = delta.total_seconds() / 3600
            else:
                record.tiempo_resolucion = 0.0
    
    @api.depends('prioridad', 'create_date')
    def _compute_sla_limite(self):
        """Calcula el límite de SLA según la prioridad"""
        sla_horas = {
            '3': 2,   # Crítica: 2 horas
            '2': 4,   # Alta: 4 horas
            '1': 24,  # Normal: 24 horas
            '0': 48,  # Baja: 48 horas
        }
        
        for record in self:
            if record.create_date:
                horas = sla_horas.get(record.prioridad, 24)
                record.sla_limite = record.create_date + timedelta(hours=horas)
            else:
                record.sla_limite = False
    
    @api.depends('tiempo_resolucion', 'sla_limite', 'estado')
    def _compute_sla_cumplido(self):
        for record in self:
            if record.estado == 'completado' and record.sla_limite and record.fecha_fin:
                record.sla_cumplido = record.fecha_fin <= record.sla_limite
            else:
                record.sla_cumplido = False
    
    def _compute_color(self):
        """Color del registro según estado y SLA"""
        for record in self:
            if record.estado == 'completado':
                record.color = 10  # Verde
            elif record.estado == 'cancelado':
                record.color = 1   # Gris
            elif record.prioridad == '3':
                record.color = 9   # Rojo (crítica)
            elif record.sla_limite and fields.Datetime.now() > record.sla_limite:
                record.color = 2   # Naranja (SLA vencido)
            else:
                record.color = 0   # Blanco

    # ==========================================
    # MÉTODOS ONCHANGE
    # ==========================================
    
    @api.onchange('maquina_id')
    def _onchange_maquina_id(self):
        """Al seleccionar máquina, sugerir técnico por zona"""
        if self.maquina_id:
            # Aquí puedes agregar lógica para asignar técnico por zona
            # Por ahora dejamos que se asigne manualmente
            pass
    
    # ==========================================
    # MÉTODOS CRUD
    # ==========================================
    
    @api.model
    def create(self, vals):
        """Override create para enviar email de confirmación"""
        # Manejar vals_list (puede ser dict o lista)
        if isinstance(vals, list):
            records = super(CopierServiceRequest, self).create(vals)
            # Enviar confirmación para cada registro
            for record in records:
                try:
                    record._send_email_confirmacion()
                except Exception as e:
                    _logger.error("Error enviando confirmación para %s: %s", record.name, str(e))
            return records
        else:
            # Crear el registro
            record = super(CopierServiceRequest, self).create(vals)
            
            # Enviar email de confirmación
            try:
                record._send_email_confirmacion()
            except Exception as e:
                _logger.error("Error enviando email de confirmación: %s", str(e))
            
            return record
        
    def write(self, vals):
        # Capturar cambios de estado
        old_estado = self.estado
        
        res = super(CopierServiceRequest, self).write(vals)
        
        # Notificaciones según cambio de estado
        if 'estado' in vals and vals['estado'] != old_estado:
            self._notificar_cambio_estado(old_estado, vals['estado'])
        
        return res
    
    # ==========================================
    # MÉTODOS DE ACCIÓN
    # ==========================================
    
    def action_asignar_tecnico(self):
        """Asignar técnico a la solicitud"""
        self.ensure_one()
        
        if not self.tecnico_id:
            raise ValidationError(_("Debe asignar un técnico antes de continuar."))
        
        self.write({'estado': 'asignado'})
        
        # Crear actividad para el técnico
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.tecnico_id.id,
            summary=f'Servicio técnico programado: {self.name}',
            note=f'Problema: {self.tipo_problema_id.name}\nCliente: {self.cliente_id.name}\nUbicación: {self.ubicacion}'
        )
        
        # Notificar al técnico
        self.message_post(
            body=f'''
                👨‍🔧 Técnico Asignado: {self.tecnico_id.name}
                
                • Cliente: {self.cliente_id.name}
                • Equipo: {self.modelo_maquina.name}
                • Ubicación: {self.ubicacion}
                • Problema: {self.tipo_problema_id.name}
            ''',
            partner_ids=[self.tecnico_id.partner_id.id] if self.tecnico_id.partner_id else []
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
        """Técnico inicia ruta hacia el cliente"""
        self.ensure_one()
        
        self.write({
            'estado': 'en_ruta'
        })
        
        self.message_post(
            body=f'🚗 El técnico {self.tecnico_id.name} está en camino.',
            message_type='notification'
        )
        
        return True
    
    def action_iniciar_servicio(self):
        """Check-in: técnico llega al sitio"""
        self.ensure_one()
        
        self.write({
            'estado': 'en_sitio',
            'fecha_inicio': fields.Datetime.now()
        })
        
        self.message_post(
            body=f'🔧 Servicio iniciado a las {fields.Datetime.now().strftime("%H:%M")}',
            message_type='notification'
        )
        
        return True
    
    def action_pausar_servicio(self):
        """Pausar servicio (espera de repuesto, autorización, etc)"""
        self.ensure_one()
        
        return {
            'name': 'Pausar Servicio',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.service.pause.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_service_id': self.id}
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
        self.ensure_one()
        
        return {
            'name': 'Cancelar Servicio',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.service.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_service_id': self.id}
        }
    
    def action_enviar_encuesta(self):
        """Enviar encuesta de satisfacción al cliente"""
        self.ensure_one()
        
        # Aquí integrarías con WhatsApp o Email
        # Por ahora solo mensaje
        
        self.message_post(
            body='📧 Encuesta de satisfacción enviada al cliente',
            message_type='notification'
        )
        
        return True
    
    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================
    
    def _registrar_contador(self):
        """Registra el contador en copier.counter"""
        self.ensure_one()
        
        try:
            self.env['copier.counter'].create({
                'maquina_id': self.maquina_id.id,
                'contador_bn': self.contador_bn or 0,
                'contador_color': self.contador_color or 0,
                'fecha_lectura': self.fecha_fin or fields.Datetime.now(),
                'notas': f'Contador registrado en servicio {self.name}'
            })
            _logger.info(f"Contador registrado para servicio {self.name}")
        except Exception as e:
            _logger.error(f"Error registrando contador: {str(e)}")
    
    def _notificar_nueva_solicitud(self):
        """Notifica la creación de una nueva solicitud"""
        self.ensure_one()
        
        self.message_post(
            body=f'''
                📋 Nueva Solicitud de Servicio Creada
                
                • Cliente: {self.cliente_id.name}
                • Máquina: {self.modelo_maquina.name}
                • Ubicación: {self.ubicacion}
                • Problema: {self.problema_reportado}
                • Prioridad: {dict(self._fields['prioridad'].selection)[self.prioridad]}
            ''',
            message_type='notification'
        )
    
    def _notificar_cambio_estado(self, old_estado, new_estado):
        """Notifica cambios de estado"""
        for record in self:
            estados_dict = dict(record._fields['estado'].selection)
            
            record.message_post(
                body=f'Estado cambiado: {estados_dict.get(old_estado)} → {estados_dict.get(new_estado)}',
                message_type='notification'
            )
    
    # ==========================================
    # CRON JOB - VERIFICAR SLA
    # ==========================================
    
    @api.model
    def _cron_check_sla(self):
        """Cron que verifica servicios próximos a vencer SLA"""
        _logger.info("Verificando SLA de servicios técnicos...")
        
        ahora = fields.Datetime.now()
        
        # Buscar servicios activos próximos a vencer (1 hora antes)
        servicios = self.search([
            ('estado', 'not in', ['completado', 'cancelado']),
            ('sla_limite', '!=', False)
        ])
        
        for servicio in servicios:
            tiempo_restante = (servicio.sla_limite - ahora).total_seconds() / 3600
            
            # Alertar si falta 1 hora o menos
            if 0 < tiempo_restante <= 1:
                servicio.message_post(
                    body=f'⚠️ ALERTA: SLA vence en {int(tiempo_restante * 60)} minutos',
                    message_type='notification'
                )
                
                # Crear actividad urgente
                if servicio.tecnico_id:
                    servicio.activity_schedule(
                        'mail.mail_activity_data_warning',
                        user_id=servicio.tecnico_id.id,
                        summary='⚠️ SLA Próximo a Vencer',
                        note=f'El servicio {servicio.name} está próximo a vencer su SLA.'
                    )
            
            # Alertar si ya venció
            elif tiempo_restante <= 0 and servicio.estado not in ['completado', 'cancelado']:
                servicio.message_post(
                    body='🚨 SLA VENCIDO - Servicio fuera de tiempo',
                    message_type='notification'
                )


# ==========================================
# MODELO: TIPOS DE PROBLEMAS
# ==========================================

class CopierServiceProblemType(models.Model):
    _name = 'copier.service.problem.type'
    _description = 'Tipos de Problemas de Servicio'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Tipo de Problema',
        required=True,
        translate=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    descripcion = fields.Text(
        string='Descripción'
    )
    
    icono = fields.Char(
        string='Icono',
        help='Emoji o código de icono',
        default='🔧'
    )
    
    active = fields.Boolean(
        default=True
    )
    
    # Estadísticas
    cantidad_servicios = fields.Integer(
        string='Servicios',
        compute='_compute_cantidad_servicios'
    )
    
    def _compute_cantidad_servicios(self):
        for record in self:
            record.cantidad_servicios = self.env['copier.service.request'].search_count([
                ('tipo_problema_id', '=', record.id)
            ])


# ==========================================
# WIZARD: PAUSAR SERVICIO
# ==========================================

class CopierServicePauseWizard(models.TransientModel):
    _name = 'copier.service.pause.wizard'
    _description = 'Wizard para Pausar Servicio'
    
    service_id = fields.Many2one(
        'copier.service.request',
        string='Servicio',
        required=True
    )
    
    motivo = fields.Text(
        string='Motivo de la Pausa',
        required=True
    )
    
    def action_pausar(self):
        self.ensure_one()
        
        self.service_id.write({
            'estado': 'pausado'
        })
        
        self.service_id.message_post(
            body=f'⏸️ Servicio pausado: {self.motivo}',
            message_type='notification'
        )
        
        return {'type': 'ir.actions.act_window_close'}


# ==========================================
# WIZARD: CANCELAR SERVICIO
# ==========================================

class CopierServiceCancelWizard(models.TransientModel):
    _name = 'copier.service.cancel.wizard'
    _description = 'Wizard para Cancelar Servicio'
    
    service_id = fields.Many2one(
        'copier.service.request',
        string='Servicio',
        required=True
    )
    
    motivo = fields.Text(
        string='Motivo de Cancelación',
        required=True
    )
    
    def action_cancelar(self):
        self.ensure_one()
        
        self.service_id.write({
            'estado': 'cancelado'
        })
        
        self.service_id.message_post(
            body=f'❌ Servicio cancelado: {self.motivo}',
            message_type='notification'
        )
        
        return {'type': 'ir.actions.act_window_close'}