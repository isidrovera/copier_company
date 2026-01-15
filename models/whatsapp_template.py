# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'Plantillas de WhatsApp'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    # ============================================
    # IDENTIFICACIÓN
    # ============================================
    name = fields.Char(
        'Nombre de Plantilla',
        required=True,
        tracking=True,
        help='Nombre descriptivo de la plantilla'
    )
    code = fields.Char(
        'Código Técnico',
        required=True,
        tracking=True,
        help='Código único para identificar la plantilla (ej: service_request_new)'
    )
    active = fields.Boolean(
        'Activo',
        default=True,
        tracking=True
    )
    sequence = fields.Integer(
        'Secuencia',
        default=10,
        help='Orden de aplicación cuando hay múltiples plantillas'
    )
    description = fields.Text(
        'Descripción',
        help='Descripción del propósito de esta plantilla'
    )
    
    # ============================================
    # MODELO OBJETIVO
    # ============================================
    model_id = fields.Many2one(
        'ir.model',
        'Modelo',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Modelo de Odoo al que aplica esta plantilla'
    )
    model_name = fields.Char(
        'Nombre Técnico del Modelo',
        related='model_id.model',
        store=True,
        readonly=True
    )
    
    # ============================================
    # MENSAJE
    # ============================================
    message_template = fields.Text(
        'Plantilla del Mensaje',
        required=True,
        tracking=True,
        help='Mensaje con variables entre llaves {campo}. Ejemplo: Hola {partner_id.name}'
    )
    available_fields_info = fields.Text(
        'Campos Disponibles',
        compute='_compute_available_fields_info',
        help='Lista de campos que puedes usar en la plantilla'
    )
    test_record_id = fields.Integer(
        'ID de Registro para Prueba',
        help='ID de un registro del modelo para generar vista previa'
    )
    preview_message = fields.Text(
        'Vista Previa',
        compute='_compute_preview_message',
        help='Vista previa del mensaje con datos reales'
    )
    
    # ============================================
    # DESTINATARIOS
    # ============================================
    recipient_type = fields.Selection([
        ('field', 'Campo del Registro'),
        ('related', 'Campo Relacionado'),
        ('fixed', 'Número Fijo'),
        ('python', 'Código Python'),
        ('multiple', 'Múltiples Destinatarios'),
    ], string='Tipo de Destinatario',
       required=True,
       default='field',
       tracking=True,
       help='Cómo obtener el número de teléfono del destinatario')
    
    recipient_field_id = fields.Many2one(
        'ir.model.fields',
        'Campo de Teléfono',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'char')]",
        help='Campo que contiene el teléfono (ej: mobile, phone, celular)'
    )
    recipient_related_path = fields.Char(
        'Ruta del Campo Relacionado',
        help='Ruta al campo relacionado (ej: partner_id.mobile, cliente_id.phone)'
    )
    recipient_fixed_number = fields.Char(
        'Número Fijo',
        help='Número de teléfono fijo (ej: 51987654321)'
    )
    recipient_python_code = fields.Text(
        'Código Python',
        help='Debe retornar una lista de números. Variable disponible: record'
    )
    recipient_ids = fields.One2many(
        'whatsapp.template.recipient',
        'template_id',
        'Destinatarios Múltiples',
        help='Configurar múltiples destinatarios con prioridad'
    )
    
    # ============================================
    # TRIGGERS
    # ============================================
    trigger_type = fields.Selection([
        ('manual', 'Manual (Solo desde botón)'),
        ('create', 'Al Crear Registro'),
        ('write', 'Al Modificar Registro'),
        ('state_change', 'Al Cambiar Estado'),
    ], string='Cuándo Enviar',
       required=True,
       default='manual',
       tracking=True,
       help='Evento que dispara el envío de la notificación')
    
    trigger_field_ids = fields.Many2many(
        'ir.model.fields',
        'whatsapp_template_trigger_field_rel',
        'template_id',
        'field_id',
        'Campos que Disparan',
        domain="[('model_id', '=', model_id)]",
        help='Solo enviar si se modifican estos campos (para trigger "Al Modificar")'
    )
    trigger_state_field_id = fields.Many2one(
        'ir.model.fields',
        'Campo de Estado',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'selection')]",
        help='Campo tipo Selection que representa el estado (para trigger "Cambio de Estado")'
    )
    trigger_state_from = fields.Char(
        'Estado Desde',
        help='Valor del estado origen (dejar vacío para cualquier estado)'
    )
    trigger_state_to = fields.Char(
        'Estado Hacia',
        help='Valor del estado destino que dispara la notificación'
    )
    
    # ============================================
    # CONDICIONES
    # ============================================
    condition_type = fields.Selection([
        ('none', 'Sin Condiciones'),
        ('domain', 'Filtro (Domain)'),
        ('python', 'Código Python'),
    ], string='Tipo de Condición',
       default='none',
       help='Condiciones adicionales para enviar')
    
    condition_domain = fields.Char(
        'Filtro Domain',
        help='Domain de Odoo. Ejemplo: [("prioridad", "in", ["2","3"])]'
    )
    condition_python_code = fields.Text(
        'Código Python (Condición)',
        help='Debe retornar True o False. Variable disponible: record'
    )
    
    # ============================================
    # ADJUNTOS
    # ============================================
    send_attachment = fields.Boolean(
        'Enviar Adjunto',
        default=False,
        help='Enviar un archivo adjunto desde un campo Binary del registro'
    )
    attachment_field_id = fields.Many2one(
        'ir.model.fields',
        'Campo del Archivo',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'binary')]",
        help='Campo tipo Binary que contiene el archivo a enviar'
    )
    attachment_type = fields.Selection([
        ('image', 'Imagen'),
        ('document', 'Documento'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ], string='Tipo de Archivo',
       default='image',
       help='Tipo de archivo multimedia')
    
    attachment_caption = fields.Char(
        'Pie de Foto/Documento',
        help='Texto que acompaña al archivo. Puede usar variables {campo}'
    )
    
    # ============================================
    # OPCIONES
    # ============================================
    config_id = fields.Many2one(
        'whatsapp.config',
        'Configuración WhatsApp',
        help='Si está vacío, usa la configuración activa por defecto'
    )
    verify_number_before_send = fields.Boolean(
        'Verificar Número en WhatsApp',
        default=True,
        help='Verificar que el número existe en WhatsApp antes de enviar'
    )
    auto_apply = fields.Boolean(
        'Aplicar Automáticamente',
        default=True,
        tracking=True,
        help='Aplicar esta plantilla automáticamente según el trigger configurado'
    )
    log_in_chatter = fields.Boolean(
        'Registrar en Chatter',
        default=True,
        help='Registrar mensaje enviado en el chatter del registro'
    )
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    notification_count = fields.Integer(
        'Notificaciones Enviadas',
        compute='_compute_notification_count',
        help='Total de notificaciones enviadas con esta plantilla'
    )
    last_notification_date = fields.Datetime(
        'Última Notificación',
        readonly=True
    )
    
    # ============================================
    # CONSTRAINTS
    # ============================================
    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'El código de la plantilla debe ser único'),
    ]
    
    # ============================================
    # COMPUTE
    # ============================================
    @api.depends('model_id')
    def _compute_available_fields_info(self):
        """Genera información sobre campos disponibles del modelo"""
        for record in self:
            if not record.model_id:
                record.available_fields_info = 'Selecciona un modelo para ver los campos disponibles'
                continue
            
            try:
                model = self.env[record.model_name]
                fields_info = []
                
                # Obtener campos del modelo
                for field_name, field in model._fields.items():
                    # Filtrar campos del sistema
                    if field_name in ['id', 'create_uid', 'write_uid', 'create_date', 
                                     'write_date', '__last_update', 'display_name']:
                        continue
                    
                    field_type = field.type
                    
                    # Campos simples
                    if field_type in ['char', 'text', 'integer', 'float', 'monetary', 
                                     'date', 'datetime', 'boolean', 'selection', 'html']:
                        fields_info.append(f"• {{{field_name}}} - {field.string} ({field_type})")
                    
                    # Campos relacionales Many2one
                    elif field_type == 'many2one':
                        fields_info.append(f"• {{{field_name}.name}} - {field.string}")
                        # Agregar campos comunes del related
                        if hasattr(field, 'comodel_name'):
                            related_model = self.env[field.comodel_name]
                            for rel_field in ['name', 'email', 'phone', 'mobile']:
                                if rel_field in related_model._fields:
                                    fields_info.append(f"  └ {{{field_name}.{rel_field}}}")
                
                record.available_fields_info = '\n'.join(fields_info) if fields_info else 'No hay campos disponibles'
                
            except Exception as e:
                record.available_fields_info = f'Error cargando campos: {str(e)}'
    
    @api.depends('message_template', 'test_record_id', 'model_id')
    def _compute_preview_message(self):
        """Genera vista previa del mensaje con datos reales"""
        for record in self:
            if not record.message_template or not record.test_record_id or not record.model_id:
                record.preview_message = 'Configure plantilla y seleccione registro de prueba'
                continue
            
            try:
                test_record = self.env[record.model_name].browse(record.test_record_id)
                if not test_record.exists():
                    record.preview_message = f'Registro ID {record.test_record_id} no encontrado'
                    continue
                
                preview = record._process_message_template(test_record)
                record.preview_message = preview
                
            except Exception as e:
                record.preview_message = f'Error generando preview: {str(e)}'
    
    @api.depends('model_id')
    def _compute_notification_count(self):
        """Cuenta notificaciones enviadas con esta plantilla"""
        for record in self:
            record.notification_count = self.env['whatsapp.notification'].search_count([
                ('template_id', '=', record.id)
            ])
    @api.model
    def _can_use_whatsapp(self, model_name):
        """
        Verifica si WhatsApp puede ser usado para el modelo dado.
        
        :param model_name: Nombre técnico del modelo (ej: 'res.partner', 'sale.order')
        :return: True si el modelo puede usar WhatsApp, False en caso contrario
        """
        # Verifica si el modelo existe
        if not model_name or model_name not in self.env:
            return False
        
        try:
            # Verifica si hay plantillas activas para este modelo
            template_count = self.search_count([
                ('model_name', '=', model_name),
                ('active', '=', True),
            ])
            
            if template_count == 0:
                return False
            
            # Verifica si el modelo tiene campos de teléfono
            model = self.env[model_name]
            model_fields = model._fields
            
            # Busca campos comunes de teléfono/móvil
            phone_fields = ['mobile', 'phone', 'whatsapp_number', 'celular', 'telefono']
            has_phone_field = any(field in model_fields for field in phone_fields)
            
            return has_phone_field
            
        except Exception as e:
            _logger.warning(f"Error verificando si el modelo {model_name} puede usar WhatsApp: {e}")
            return False
    # ============================================
    # ONCHANGE
    # ============================================
    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Limpiar campos dependientes al cambiar modelo"""
        if self.model_id:
            self.recipient_field_id = False
            self.recipient_related_path = False
            self.trigger_field_ids = [(5, 0, 0)]
            self.trigger_state_field_id = False
            self.attachment_field_id = False
            self.test_record_id = False
    
    @api.onchange('trigger_type')
    def _onchange_trigger_type(self):
        """Limpiar configuración de trigger al cambiar tipo"""
        if self.trigger_type not in ['write']:
            self.trigger_field_ids = [(5, 0, 0)]
        if self.trigger_type != 'state_change':
            self.trigger_state_field_id = False
            self.trigger_state_from = False
            self.trigger_state_to = False
    
    @api.onchange('recipient_type')
    def _onchange_recipient_type(self):
        """Limpiar configuración de destinatarios al cambiar tipo"""
        if self.recipient_type != 'field':
            self.recipient_field_id = False
        if self.recipient_type != 'related':
            self.recipient_related_path = False
        if self.recipient_type != 'fixed':
            self.recipient_fixed_number = False
        if self.recipient_type != 'python':
            self.recipient_python_code = False
    
    # ============================================
    # VALIDACIONES
    # ============================================
    @api.constrains('code')
    def _check_unique_code(self):
        """Validar que el código sea único"""
        for record in self:
            if record.code:
                duplicate = self.search([
                    ('code', '=', record.code),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        'Ya existe una plantilla con el código "%s"'
                    ) % record.code)
    
    @api.constrains('recipient_type', 'recipient_field_id', 'recipient_related_path', 
                    'recipient_fixed_number', 'recipient_python_code')
    def _check_recipient_config(self):
        """Validar configuración de destinatarios"""
        for record in self:
            if record.recipient_type == 'field' and not record.recipient_field_id:
                raise ValidationError(_('Debe seleccionar un campo de teléfono'))
            
            if record.recipient_type == 'related' and not record.recipient_related_path:
                raise ValidationError(_('Debe ingresar la ruta del campo relacionado'))
            
            if record.recipient_type == 'fixed' and not record.recipient_fixed_number:
                raise ValidationError(_('Debe ingresar un número fijo'))
            
            if record.recipient_type == 'python' and not record.recipient_python_code:
                raise ValidationError(_('Debe ingresar código Python'))
    
    @api.constrains('trigger_type', 'trigger_state_field_id', 'trigger_state_to')
    def _check_trigger_config(self):
        """Validar configuración de trigger"""
        for record in self:
            if record.trigger_type == 'state_change':
                if not record.trigger_state_field_id:
                    raise ValidationError(_('Debe seleccionar el campo de estado'))
                if not record.trigger_state_to:
                    raise ValidationError(_('Debe especificar el estado destino'))
    
    @api.constrains('send_attachment', 'attachment_field_id')
    def _check_attachment_config(self):
        """Validar configuración de adjuntos"""
        for record in self:
            if record.send_attachment and not record.attachment_field_id:
                raise ValidationError(_('Debe seleccionar el campo del archivo'))
    
    @api.constrains('condition_type', 'condition_domain', 'condition_python_code')
    def _check_condition_config(self):
        """Validar configuración de condiciones"""
        for record in self:
            if record.condition_type == 'domain' and not record.condition_domain:
                raise ValidationError(_('Debe ingresar un filtro domain'))
            
            if record.condition_type == 'python' and not record.condition_python_code:
                raise ValidationError(_('Debe ingresar código Python'))
            
            # Validar sintaxis del domain
            if record.condition_type == 'domain' and record.condition_domain:
                try:
                    eval(record.condition_domain)
                except Exception as e:
                    raise ValidationError(_(
                        'Error en el filtro domain: %s'
                    ) % str(e))
    
    # ============================================
    # ACCIONES
    # ============================================
    def action_view_notifications(self):
        """Ver notificaciones enviadas con esta plantilla"""
        self.ensure_one()
        
        return {
            'name': _('Notificaciones'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.notification',
            'view_mode': 'list,form',
            'domain': [('template_id', '=', self.id)],
            'context': {'default_template_id': self.id}
        }
    
    def action_test_template(self):
        """Abrir wizard para probar plantilla"""
        self.ensure_one()
        
        return {
            'name': _('Probar Plantilla'),
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.template.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id}
        }
    
    def action_duplicate_template(self):
        """Duplicar plantilla"""
        self.ensure_one()
        
        new_template = self.copy({
            'name': f'{self.name} (Copia)',
            'code': f'{self.code}_copy',
            'active': False
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ============================================
    # CORE - OBTENER DESTINATARIOS
    # ============================================
    def _get_recipients(self, record):
        """
        Obtener lista de destinatarios para un registro
        
        Args:
            record: Registro del modelo objetivo
            
        Returns:
            list: Lista de números de teléfono limpios
        """
        self.ensure_one()
        phones = []
        config = self.config_id or self.env['whatsapp.config'].get_active_config()
        
        try:
            if self.recipient_type == 'field':
                # Campo directo
                if self.recipient_field_id:
                    phone = record[self.recipient_field_id.name]
                    if phone:
                        clean_phone = config.clean_phone_number(phone)
                        if clean_phone:
                            phones.append(clean_phone)
            
            elif self.recipient_type == 'related':
                # Campo relacionado
                if self.recipient_related_path:
                    try:
                        phone = record
                        for part in self.recipient_related_path.split('.'):
                            phone = phone[part]
                        if phone:
                            clean_phone = config.clean_phone_number(phone)
                            if clean_phone:
                                phones.append(clean_phone)
                    except (KeyError, AttributeError) as e:
                        _logger.warning(f"Error accediendo a ruta {self.recipient_related_path}: {e}")
            
            elif self.recipient_type == 'fixed':
                # Número fijo
                if self.recipient_fixed_number:
                    clean_phone = config.clean_phone_number(self.recipient_fixed_number)
                    if clean_phone:
                        phones.append(clean_phone)
            
            elif self.recipient_type == 'python':
                # Código Python
                if self.recipient_python_code:
                    try:
                        local_dict = {'record': record, 'env': self.env}
                        exec(self.recipient_python_code, local_dict)
                        result = local_dict.get('result', [])
                        if isinstance(result, list):
                            for phone in result:
                                clean_phone = config.clean_phone_number(phone)
                                if clean_phone:
                                    phones.append(clean_phone)
                    except Exception as e:
                        _logger.error(f"Error ejecutando código Python de destinatarios: {e}")
            
            elif self.recipient_type == 'multiple':
                # Múltiples destinatarios (One2many)
                for recipient_line in self.recipient_ids.sorted('sequence'):
                    recipient_phones = recipient_line._get_phone_numbers(record)
                    phones.extend(recipient_phones)
                    # Si encontramos números y no es backup, detenemos
                    if recipient_phones and not recipient_line.is_backup:
                        break
            
            # Remover duplicados manteniendo orden
            phones = list(dict.fromkeys(phones))
            
            _logger.info(f"Destinatarios encontrados para plantilla {self.code}: {len(phones)}")
            return phones
            
        except Exception as e:
            _logger.exception(f"Error obteniendo destinatarios para plantilla {self.code}: {e}")
            return []
    
    # ============================================
    # CORE - PROCESAR MENSAJE
    # ============================================
    def _process_message_template(self, record):
        """
        Procesar plantilla de mensaje reemplazando variables
        
        Args:
            record: Registro del modelo objetivo
            
        Returns:
            str: Mensaje procesado
        """
        self.ensure_one()
        
        try:
            message = self.message_template
            
            # Buscar todas las variables {campo}
            variables = re.findall(r'\{([^}]+)\}', message)
            
            for var in variables:
                try:
                    # Soportar notación punto (ej: partner_id.name)
                    value = record
                    for part in var.split('.'):
                        value = value[part] if value else ''
                    
                    # Convertir valor a string
                    if value is False:
                        value = ''
                    elif isinstance(value, (list, tuple)):
                        value = ', '.join(str(v) for v in value)
                    else:
                        value = str(value)
                    
                    # Reemplazar variable
                    message = message.replace(f'{{{var}}}', value)
                    
                except (KeyError, AttributeError, TypeError) as e:
                    _logger.warning(f"Error procesando variable {{{var}}}: {e}")
                    message = message.replace(f'{{{var}}}', f'[{var}]')
            
            return message
            
        except Exception as e:
            _logger.exception(f"Error procesando plantilla de mensaje: {e}")
            return self.message_template
    
    # ============================================
    # CORE - VERIFICAR CONDICIONES
    # ============================================
    def _check_conditions(self, record):
        """
        Verificar si se cumplen las condiciones para enviar
        
        Args:
            record: Registro del modelo objetivo
            
        Returns:
            bool: True si se cumplen las condiciones
        """
        self.ensure_one()
        
        try:
            if self.condition_type == 'none':
                return True
            
            elif self.condition_type == 'domain':
                if self.condition_domain:
                    domain = eval(self.condition_domain)
                    # Agregar el ID del registro al domain
                    domain = [('id', '=', record.id)] + domain
                    count = self.env[self.model_name].search_count(domain)
                    return count > 0
                return True
            
            elif self.condition_type == 'python':
                if self.condition_python_code:
                    local_dict = {'record': record, 'env': self.env}
                    exec(self.condition_python_code, local_dict)
                    result = local_dict.get('result', False)
                    return bool(result)
                return True
            
            return True
            
        except Exception as e:
            _logger.error(f"Error verificando condiciones: {e}")
            return False
    
    # ============================================
    # CORE - ENVIAR NOTIFICACIÓN
    # ============================================
    def send_notification(self, record, force=False):
        """
        Enviar notificación WhatsApp
        
        Args:
            record: Registro del modelo objetivo
            force: Forzar envío ignorando condiciones
            
        Returns:
            list: Lista de whatsapp.notification creados
        """
        self.ensure_one()
        
        # Validar que el modelo coincida
        if record._name != self.model_name:
            raise UserError(_(
                'El registro no pertenece al modelo configurado en la plantilla'
            ))
        
        # Verificar condiciones
        if not force and not self._check_conditions(record):
            _logger.info(f"Condiciones no cumplidas para plantilla {self.code}")
            return []
        
        # Obtener configuración
        config = self.config_id or self.env['whatsapp.config'].get_active_config()
        
        # Verificar conexión
        connection_status = config.check_connection(silent=True)
        if not connection_status.get('connected'):
            _logger.error(f"WhatsApp no está conectado. No se puede enviar notificación.")
            return []
        
        # Obtener destinatarios
        recipients = self._get_recipients(record)
        if not recipients:
            _logger.warning(f"No se encontraron destinatarios para plantilla {self.code}")
            return []
        
        # Procesar mensaje
        message = self._process_message_template(record)
        
        # Crear notificaciones
        notifications = []
        
        for phone in recipients:
            # Verificar número si está configurado
            if self.verify_number_before_send:
                if not config.verify_number(phone):
                    _logger.warning(f"Número {phone} no existe en WhatsApp")
                    # Crear notificación fallida
                    notification = self.env['whatsapp.notification'].create({
                        'template_id': self.id,
                        'model_name': self.model_name,
                        'res_id': record.id,
                        'recipient_phone': phone,
                        'message_content': message,
                        'state': 'failed',
                        'error_message': 'Número no existe en WhatsApp',
                        'config_id': config.id,
                    })
                    notifications.append(notification)
                    continue
            
            # Crear notificación en estado borrador
            notification = self.env['whatsapp.notification'].create({
                'template_id': self.id,
                'model_name': self.model_name,
                'res_id': record.id,
                'recipient_phone': phone,
                'message_content': message,
                'state': 'draft',
                'config_id': config.id,
            })
            
            try:
                # Enviar mensaje
                result = config.send_message(phone, message)
                
                if result['success']:
                    # Actualizar notificación
                    notification.write({
                        'state': 'sent',
                        'sent_date': fields.Datetime.now(),
                        'api_message_id': result.get('message_id'),
                    })
                    
                    # Registrar en chatter si está configurado
                    if self.log_in_chatter:
                        record.message_post(
                            body=f"📱 Mensaje WhatsApp enviado a {phone}",
                            message_type='notification'
                        )
                    
                    _logger.info(f"✅ Notificación enviada a {phone}")
                    
                else:
                    # Marcar como fallida
                    notification.write({
                        'state': 'failed',
                        'error_message': result.get('error', 'Error desconocido'),
                    })
                    _logger.error(f"❌ Error enviando a {phone}: {result.get('error')}")
                
                # Enviar adjunto si está configurado
                if self.send_attachment and self.attachment_field_id and result['success']:
                    self._send_attachment(record, notification, config, phone)
                
            except Exception as e:
                # Marcar como fallida
                notification.write({
                    'state': 'failed',
                    'error_message': str(e),
                })
                _logger.exception(f"Excepción enviando notificación: {e}")
            
            notifications.append(notification)
        
        # Actualizar última notificación de la plantilla
        self.write({'last_notification_date': fields.Datetime.now()})
        
        return notifications
    
    def _send_attachment(self, record, notification, config, phone):
        """Enviar archivo adjunto"""
        try:
            file_data = record[self.attachment_field_id.name]
            if not file_data:
                return
            
            caption = self._process_message_template(record) if self.attachment_caption else ''
            
            result = config.send_media(
                phone=phone,
                file_data=file_data,
                media_type=self.attachment_type,
                caption=caption
            )
            
            if result['success']:
                notification.write({
                    'has_attachment': True,
                    'attachment_name': f"{self.attachment_field_id.name}.{self.attachment_type}"
                })
                _logger.info(f"✅ Adjunto enviado a {phone}")
            else:
                _logger.error(f"❌ Error enviando adjunto: {result.get('error')}")
                
        except Exception as e:
            _logger.exception(f"Error enviando adjunto: {e}")