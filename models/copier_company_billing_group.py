# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CopierCompanyBillingGroup(models.Model):
    _inherit = 'copier.company'

    billing_group_id = fields.Many2one(
        'copier.billing.group',
        string='Grupo de Facturación',
        tracking=True,
        domain="[('cliente_id', '=', cliente_id), ('active', '=', True)]",
        help='Grupo o contrato donde esta máquina comparte volumen y facturación.'
    )

    @api.constrains('billing_group_id', 'cliente_id')
    def _check_billing_group_cliente(self):
        for rec in self:
            if rec.billing_group_id and rec.cliente_id:
                if rec.billing_group_id.cliente_id.id != rec.cliente_id.id:
                    raise ValidationError(
                        'El grupo de facturación debe pertenecer al mismo cliente de la máquina.'
                    )

    @api.onchange('cliente_id')
    def _onchange_cliente_id_billing_group(self):
        for rec in self:
            if rec.billing_group_id and rec.cliente_id:
                if rec.billing_group_id.cliente_id.id != rec.cliente_id.id:
                    rec.billing_group_id = False