# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
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
        'res.users',
        string='Técnico Asignado',
        tracking=True,
        domain=[('share', '=', False)]
    )
    
    tecnico_respaldo_id = fields.Many2one(
        'res.users',
        string='Técnico Respaldo',
        tracking=True,
        domain=[('share', '=', False)]
    )
    
    fecha_programada = fields.Datetime(
        string='Fecha Programada',
        tracking=True
    )
    
    duracion_estimada = fields.Float(
        string='Duración Estimada (horas)',
        default=2.0
    )
    
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
    
    fotos_adicionales = fields.Many2many(
        'ir.attachment',
        'service_request_attachment_rel',
        'request_id',
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
    
    sla_limite = fields.Float(
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
            record.sla_limite = sla_map.get(record.prioridad, 24.0)
    
    @api.depends('create_date', 'fecha_inicio', 'fecha_fin', 'sla_limite')
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
                record.sla_cumplido = record.tiempo_resolucion <= record.sla_limite
            else:
                record.sla_cumplido = False
    
    # ========================================
    # MÉTODOS DE CREACIÓN
    # ========================================
    
    @api.model
    def create(self, vals):
        """Override create para asignar secuencia y enviar notificaciones"""
        # Manejar vals_list (puede ser dict o lista)
        if isinstance(vals, list):
            records = self.env['copier.service.request']
            for val in vals:
                # Asignar secuencia si es nuevo
                if val.get('name', _('Nuevo')) == _('Nuevo'):
                    val['name'] = self.env['ir.sequence'].next_by_code('copier.service.request') or _('Nuevo')
                
                # Crear registro
                record = super(CopierServiceRequest, self).create(val)
                records |= record
                
                # Enviar confirmación
                try:
                    record._send_email_confirmacion()
                except Exception as e:
                    _logger.error("Error enviando confirmación para %s: %s", record.name, str(e))
                
                # Notificar creación en chatter
                record._notificar_nueva_solicitud()
            
            return records
        else:
            # Asignar secuencia
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('copier.service.request') or _('Nuevo')
            
            # Crear el registro
            record = super(CopierServiceRequest, self).create(vals)
            
            # Enviar email de confirmación
            try:
                record._send_email_confirmacion()
            except Exception as e:
                _logger.error("Error enviando email de confirmación: %s", str(e))
            
            # Notificar en chatter
            record._notificar_nueva_solicitud()
            
            return record
    
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
        """Técnico indica que está en camino"""
        self.ensure_one()
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
        """Crea un registro de contador al completar el servicio"""
        self.ensure_one()
        
        if not self.contador_bn and not self.contador_color:
            return
        
        # Crear contador
        counter_vals = {
            'maquina_id': self.maquina_id.id,
            'fecha': self.fecha_fin or fields.Datetime.now(),
            'contador_actual_bn': self.contador_bn,
            'contador_actual_color': self.contador_color,
            'observaciones': f'Registrado desde servicio técnico {self.name}',
            'state': 'draft',
        }
        
        try:
            counter = self.env['copier.counter'].create(counter_vals)
            _logger.info("Contador creado desde servicio %s: ID=%s", self.name, counter.id)
            
            self.message_post(
                body=f'''
                    📊 Contador Registrado
                    
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
                tiempo_restante = solicitud.sla_limite - tiempo_transcurrido
                
                # Alertar si queda menos de 1 hora
                if 0 < tiempo_restante <= 1.0:
                    solicitud.message_post(
                        body=f'''
                            ⚠️ ALERTA SLA
                            
                            • Tiempo restante: {tiempo_restante:.1f} horas
                            • Límite SLA: {solicitud.sla_limite} horas
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
    
    def _send_email_completado(self):
        """
        Envía email cuando se completa el servicio.
        Incluye solicitud de evaluación.
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
            
            # Enviar el email
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.correo,
                    'email_from': 'info@copiercompanysac.com',
                }
            )
            
            _logger.info("✅ Email servicio completado enviado a: %s", self.correo)
            
            # Registrar en el chatter
            self.message_post(
                body=f'''
                    📧 Email de Servicio Completado Enviado
                    
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
        y que NO hayan recibido recordatorio aún.
        Envía UN SOLO recordatorio por solicitud.
        """
        _logger.info("=== INICIANDO CRON: Envío de recordatorios de evaluación ===")
        
        try:
            # Calcular fecha de hace 48 horas (con margen de ±6 horas)
            now = fields.Datetime.now()
            fecha_48h_antes = now - timedelta(hours=48)
            fecha_46h_antes = now - timedelta(hours=46)  # Margen superior
            fecha_50h_antes = now - timedelta(hours=50)  # Margen inferior
            
            _logger.info("Buscando servicios completados entre %s y %s", 
                        fecha_50h_antes.strftime('%d/%m/%Y %H:%M'),
                        fecha_46h_antes.strftime('%d/%m/%Y %H:%M'))
            
            # Buscar solicitudes que cumplan TODAS las condiciones
            domain = [
                ('estado', '=', 'completado'),
                ('fecha_fin', '!=', False),
                ('fecha_fin', '>=', fecha_50h_antes),  # Completado hace 48-50 horas
                ('fecha_fin', '<=', fecha_46h_antes),  # Completado hace 46-48 horas
                ('calificacion', '=', False),  # No ha calificado
                ('recordatorio_enviado', '=', False),  # No se ha enviado recordatorio
                ('correo', '!=', False),  # Tiene email
            ]
            
            solicitudes = self.search(domain)
            
            _logger.info("Solicitudes encontradas: %s", len(solicitudes))
            
            if not solicitudes:
                _logger.info("No hay solicitudes pendientes de recordatorio")
                return
            
            # Enviar recordatorio a cada solicitud
            enviados = 0
            errores = 0
            
            for solicitud in solicitudes:
                try:
                    _logger.info("Procesando solicitud %s (ID: %s)", solicitud.name, solicitud.id)
                    
                    if solicitud._send_email_recordatorio_evaluacion():
                        enviados += 1
                    else:
                        errores += 1
                        
                except Exception as e:
                    _logger.exception("Error procesando solicitud %s: %s", solicitud.name, str(e))
                    errores += 1
                    continue
            
            _logger.info("=== CRON FINALIZADO ===")
            _logger.info("Total procesadas: %s", len(solicitudes))
            _logger.info("Enviados exitosamente: %s", enviados)
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