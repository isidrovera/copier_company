# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppTemplateRecipient(models.Model):
    _name = 'whatsapp.template.recipient'
    _description = 'Destinatarios Múltiples de Plantilla WhatsApp'
    _order = 'template_id, sequence, id'
    
    # ============================================
    # RELACIÓN
    # ============================================
    template_id = fields.Many2one(
        'whatsapp.template',
        'Plantilla',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(
        'Secuencia',
        default=10,
        help='Orden de prioridad (menor = mayor prioridad)'
    )
    
    # ============================================
    # CONFIGURACIÓN
    # ============================================
    name = fields.Char(
        'Nombre',
        required=True,
        help='Nombre descriptivo del destinatario (ej: Cliente Principal, Técnico Asignado)'
    )
    recipient_type = fields.Selection([
        ('field', 'Campo del Registro'),
        ('related', 'Campo Relacionado'),
        ('fixed', 'Número Fijo'),
        ('python', 'Código Python'),
    ], string='Tipo',
       required=True,
       default='field',
       help='Cómo obtener el número de teléfono')
    
    # Configuración según tipo
    recipient_field_id = fields.Many2one(
        'ir.model.fields',
        'Campo de Teléfono',
        domain="[('model_id', '=', model_id), ('ttype', '=', 'char')]",
        help='Campo que contiene el teléfono'
    )
    recipient_related_path = fields.Char(
        'Ruta del Campo Relacionado',
        help='Ruta al campo relacionado (ej: partner_id.mobile)'
    )
    recipient_fixed_number = fields.Char(
        'Número Fijo',
        help='Número de teléfono fijo (ej: 51987654321)'
    )
    recipient_python_code = fields.Text(
        'Código Python',
        help='Debe retornar una lista de números. Variable disponible: record'
    )
    
    # ============================================
    # OPCIONES
    # ============================================
    is_backup = fields.Boolean(
        'Es Respaldo',
        default=False,
        help='Solo usar este destinatario si los anteriores fallaron'
    )
    active = fields.Boolean(
        'Activo',
        default=True
    )
    
    # ============================================
    # CAMPOS RELACIONADOS (HELPERS)
    # ============================================
    model_id = fields.Many2one(
        'ir.model',
        related='template_id.model_id',
        store=False,
        readonly=True
    )

    
    # ============================================
    # VALIDACIONES
    # ============================================
    @api.constrains('recipient_type', 'recipient_field_id', 'recipient_related_path',
                    'recipient_fixed_number', 'recipient_python_code')
    def _check_recipient_config(self):
        """Validar configuración según tipo de destinatario"""
        for record in self:
            if record.recipient_type == 'field' and not record.recipient_field_id:
                raise ValidationError(_('Debe seleccionar un campo de teléfono'))
            
            if record.recipient_type == 'related' and not record.recipient_related_path:
                raise ValidationError(_('Debe ingresar la ruta del campo relacionado'))
            
            if record.recipient_type == 'fixed' and not record.recipient_fixed_number:
                raise ValidationError(_('Debe ingresar un número fijo'))
            
            if record.recipient_type == 'python' and not record.recipient_python_code:
                raise ValidationError(_('Debe ingresar código Python'))
    
    # ============================================
    # ONCHANGE
    # ============================================
    @api.onchange('recipient_type')
    def _onchange_recipient_type(self):
        """Limpiar campos al cambiar tipo"""
        if self.recipient_type != 'field':
            self.recipient_field_id = False
        if self.recipient_type != 'related':
            self.recipient_related_path = False
        if self.recipient_type != 'fixed':
            self.recipient_fixed_number = False
        if self.recipient_type != 'python':
            self.recipient_python_code = False
    
    # ============================================
    # MÉTODOS
    # ============================================
    def _get_phone_numbers(self, record):
        """
        Obtener números de teléfono para este destinatario
        
        Args:
            record: Registro del modelo objetivo
            
        Returns:
            list: Lista de números de teléfono limpios
        """
        self.ensure_one()
        
        if not self.active:
            return []
        
        phones = []
        config = self.template_id.config_id or self.env['whatsapp.config'].get_active_config()
        
        try:
            if self.recipient_type == 'field':
                if self.recipient_field_id:
                    phone = record[self.recipient_field_id.name]
                    if phone:
                        clean_phone = config.clean_phone_number(phone)
                        if clean_phone:
                            phones.append(clean_phone)
            
            elif self.recipient_type == 'related':
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
                        _logger.warning(f"Error accediendo a {self.recipient_related_path}: {e}")
            
            elif self.recipient_type == 'fixed':
                if self.recipient_fixed_number:
                    clean_phone = config.clean_phone_number(self.recipient_fixed_number)
                    if clean_phone:
                        phones.append(clean_phone)
            
            elif self.recipient_type == 'python':
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
                        _logger.error(f"Error ejecutando código Python: {e}")
            
        except Exception as e:
            _logger.exception(f"Error obteniendo números para destinatario {self.name}: {e}")
        
        return phones