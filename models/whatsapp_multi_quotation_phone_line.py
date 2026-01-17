# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

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
        """Limpiar y normalizar el número de teléfono"""
        for line in self:
            if line.phone:
                # Usar el método de whatsapp.config para limpiar
                clean = self.env['whatsapp.config'].clean_phone_number(line.phone)
                line.phone_clean = clean
            else:
                line.phone_clean = ''
    
    @api.depends('phone_clean')
    def _compute_is_valid(self):
        """Validar si el número es correcto"""
        for line in self:
            # Un número es válido si tiene formato correcto (11 dígitos para Perú)
            line.is_valid = bool(line.phone_clean and len(line.phone_clean) == 11)
    
    # ============================================
    # ONCHANGE METHODS
    # ============================================
    @api.onchange('phone')
    def _onchange_phone(self):
        """Resetear verificación al cambiar el número"""
        for line in self:
            line.is_verified = False
            line.verification_result = ''