# -*- coding: utf-8 -*-
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppMultiQuotationPhoneLine(models.TransientModel):
    _name = 'whatsapp.multi.quotation.phone.line'
    _description = 'Línea de Teléfono para Envío de Cotización Multi-Equipo WhatsApp'
    _order = 'sequence, id'

    # ============================================
    # CAMPOS
    # ============================================
    wizard_id = fields.Many2one(
        'whatsapp.send.multi.quotation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    phone = fields.Char(
        string='Número de Teléfono',
        required=True,
        help='Número en cualquier formato (se limpiará automáticamente)'
    )
    
    phone_clean = fields.Char(
        string='Número Limpio',
        compute='_compute_phone_clean',
        store=True,
        help='Número formateado para WhatsApp (ej: 51987654321)'
    )
    
    partner_name = fields.Char(
        string='Contacto',
        help='Nombre del contacto asociado'
    )
    
    copier_reference = fields.Char(
        string='Cotización',
        help='Referencia a la cotización'
    )
    
    is_valid = fields.Boolean(
        string='Válido',
        compute='_compute_is_valid',
        store=True,
        help='Indica si el número tiene formato válido'
    )
    
    validation_message = fields.Char(
        string='Estado',
        compute='_compute_is_valid',
        store=True,
        help='Mensaje de validación del número'
    )
    
    is_verified = fields.Boolean(
        string='Verificado',
        default=False,
        help='Indica si se verificó con la API de WhatsApp'
    )
    
    verification_result = fields.Char(
        string='Resultado',
        help='Resultado de la verificación'
    )
    
    # ============================================
    # COMPUTE METHODS
    # ============================================
    @api.depends('phone')
    def _compute_phone_clean(self):
        """Limpiar y normalizar el número de teléfono usando el método de whatsapp.config"""
        for line in self:
            if line.phone:
                # Usar el método centralizado de limpieza
                clean = self.env['whatsapp.config'].clean_phone_number(line.phone)
                line.phone_clean = clean
            else:
                line.phone_clean = ''
    
    @api.depends('phone_clean')
    def _compute_is_valid(self):
        """Validar si el número es correcto"""
        for line in self:
            if not line.phone_clean:
                line.is_valid = False
                line.validation_message = '❌ Inválido'
                continue
            
            # Validar longitud (11 dígitos para Perú: 51 + 9)
            phone_len = len(line.phone_clean)
            
            if phone_len == 11 and line.phone_clean.startswith('51'):
                line.is_valid = True
                line.validation_message = '✅ Válido'
            elif phone_len < 11:
                line.is_valid = False
                line.validation_message = f'❌ Muy corto ({phone_len})'
            elif phone_len > 11:
                line.is_valid = False
                line.validation_message = f'❌ Muy largo ({phone_len})'
            else:
                line.is_valid = False
                line.validation_message = '❌ Formato incorrecto'
    
    # ============================================
    # ONCHANGE METHODS
    # ============================================
    @api.onchange('phone')
    def _onchange_phone(self):
        """Resetear verificación al cambiar el número"""
        for line in self:
            line.is_verified = False
            line.verification_result = ''
    
    # ============================================
    # MÉTODOS DE ACCIÓN
    # ============================================
    def action_verify_number(self):
        """Verificar un número individual en WhatsApp"""
        self.ensure_one()
        
        if not self.is_valid:
            raise UserError(_('El número no tiene formato válido para verificar.'))
        
        if not self.wizard_id.config_id:
            raise UserError(_('No hay configuración de WhatsApp disponible.'))
        
        # Verificar con la API
        try:
            exists = self.wizard_id.config_id.verify_number(self.phone_clean)
            
            self.write({
                'is_verified': True,
                'verification_result': '✅ Existe en WhatsApp' if exists else '❌ No existe en WhatsApp'
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Verificación Completada',
                    'message': f'Número {self.phone}: {self.verification_result}',
                    'type': 'success' if exists else 'warning',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error(f"Error verificando número {self.phone_clean}: {str(e)}")
            raise UserError(_(f'Error al verificar número: {str(e)}'))