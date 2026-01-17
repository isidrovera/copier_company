# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WhatsAppMultiQuotationPhoneLine(models.TransientModel):
    _name = 'whatsapp.multi.quotation.phone.line'
    _description = 'Línea WhatsApp – Cotización Multi'

    wizard_id = fields.Many2one(
        'whatsapp.send.multi.quotation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    phone = fields.Char(
        string='Número de Teléfono',
        required=True
    )

    phone_clean = fields.Char(
        string='Número Limpio',
        compute='_compute_phone_clean',
        store=True
    )

    partner_name = fields.Char(string='Contacto')
    copier_reference = fields.Char(string='Cotización')

    is_valid = fields.Boolean(
        string='Válido',
        compute='_compute_is_valid',
        store=True
    )

    @api.depends('phone')
    def _compute_phone_clean(self):
        for line in self:
            if line.phone:
                line.phone_clean = (
                    self.env['whatsapp.config']
                    .clean_phone_number(line.phone)
                )
            else:
                line.phone_clean = False

    @api.depends('phone_clean')
    def _compute_is_valid(self):
        for line in self:
            line.is_valid = bool(line.phone_clean and len(line.phone_clean) >= 11)
