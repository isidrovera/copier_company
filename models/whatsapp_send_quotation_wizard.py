# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WhatsAppQuotationPhoneLine(models.TransientModel):
    _name = 'whatsapp.quotation.phone.line'
    _description = 'Línea de Teléfono para Envío de Cotización WhatsApp'
    _order = 'sequence, id'

    # ==================================================
    # RELACIÓN CORRECTA CON EL WIZARD SIMPLE
    # ==================================================
    wizard_id = fields.Many2one(
        'whatsapp.send.quotation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    # ==================================================
    # CAMPOS
    # ==================================================
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

    # ==================================================
    # COMPUTE METHODS
    # ==================================================
    @api.depends('phone')
    def _compute_phone_clean(self):
        """
        Limpia y normaliza el número de teléfono
        """
        for line in self:
            if line.phone:
                try:
                    clean = self.env['whatsapp.config'].clean_phone_number(line.phone)
                    line.phone_clean = clean
                except Exception as e:
                    _logger.warning(
                        "Error limpiando teléfono %s: %s",
                        line.phone, str(e)
                    )
                    line.phone_clean = False
            else:
                line.phone_clean = False

    @api.depends('phone_clean')
    def _compute_is_valid(self):
        """
        Un número es válido si tiene 11 dígitos (Perú: 51 + 9 dígitos)
        """
        for line in self:
            line.is_valid = bool(
                line.phone_clean and len(line.phone_clean) == 11
            )

    # ==================================================
    # ONCHANGE METHODS
    # ==================================================
    @api.onchange('phone')
    def _onchange_phone(self):
        """
        Resetear verificación cuando cambia el número
        """
        for line in self:
            line.is_verified = False
            line.verification_result = False
