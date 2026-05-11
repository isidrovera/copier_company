# -*- coding: utf-8 -*-

from odoo import models, fields


class CopierCounterBillingGroup(models.Model):
    _inherit = 'copier.counter'

    billing_group_id = fields.Many2one(
        'copier.billing.group',
        string='Grupo de Facturación',
        related='maquina_id.billing_group_id',
        store=True,
        readonly=True
    )

    def action_create_invoice(self):
        result = super().action_create_invoice()

        invoice = False

        if isinstance(result, dict) and result.get('res_model') == 'account.move' and result.get('res_id'):
            invoice = self.env['account.move'].browse(result['res_id'])

        if invoice:
            self.env['copier.invoice.helper']._apply_detraccion_if_needed(
                invoice=invoice,
                aplicar=True,
                monto_minimo=700.00,
                operation_type='1001',
            )

        return result