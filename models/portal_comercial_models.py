# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Extensión de pedidos de venta para identificar qué ejecutiva
    portal es propietaria del documento.
    """
    _inherit = 'sale.order'

    portal_executive_id = fields.Many2one(
        'res.partner',
        string='Ejecutiva Portal',
        copy=False,
        index=True,
        tracking=True,
        help='Ejecutiva portal propietaria de la cotización o pedido.',
    )

    def _prepare_invoice(self):
        """
        Copia automáticamente la ejecutiva desde el pedido hacia
        la factura creada por el flujo estándar de Ventas.
        """
        self.ensure_one()

        vals = super()._prepare_invoice()
        vals['portal_executive_id'] = self.portal_executive_id.id or False
        return vals


class AccountMove(models.Model):
    """
    Extensión de facturas para conservar la ejecutiva propietaria.
    """
    _inherit = 'account.move'

    portal_executive_id = fields.Many2one(
        'res.partner',
        string='Ejecutiva Portal',
        copy=False,
        index=True,
        tracking=True,
        help='Ejecutiva portal propietaria de la factura.',
    )