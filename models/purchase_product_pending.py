# -*- coding: utf-8 -*-
import uuid
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PurchaseProductPending(models.Model):
    _name = 'purchase.product.pending'
    _description = 'Factura pendiente por producto desconocido'
    _order = 'create_date desc'

    # ----- Token único de cada línea pendiente -----
    token = fields.Char(
        string='Token',
        required=True,
        readonly=True,
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        index=True,
    )

    # ----- Token compartido entre TODOS los pendientes de la misma factura -----
    # Esto permite que un solo link/email resuelva todas las líneas desconocidas
    # de una factura en una sola pantalla.
    group_token = fields.Char(
        string='Token de grupo (factura)',
        required=True,
        readonly=True,
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        index=True,
        help='Token compartido por todas las líneas desconocidas de la misma factura.',
    )

    # ----- Datos de la línea -----
    description_proveedor = fields.Char(
        string='Descripción en factura',
        required=True,
    )
    line_index = fields.Integer(
        string='Índice de línea',
        required=True,
        default=0,
        help='Posición de esta línea dentro del array lines[] del payload original.',
    )
    line_quantity = fields.Float(
        string='Cantidad',
        digits=(16, 4),
        default=0.0,
    )
    line_unit_price = fields.Float(
        string='Precio unitario',
        digits=(16, 4),
        default=0.0,
    )

    # ----- Datos de la factura (cabecera) -----
    supplier_name = fields.Char(string='Proveedor')
    supplier_ruc = fields.Char(string='RUC proveedor')
    invoice_id = fields.Char(string='N° Factura', index=True)
    currency_name = fields.Char(string='Moneda', default='USD')
    invoice_payload = fields.Text(
        string='Payload JSON',
        required=True,
        help='JSON completo de la factura recibida (idéntico en todos los pendientes del mismo group_token).',
    )

    # ----- Estado -----
    state = fields.Selection(
        selection=[
            ('pending', 'Pendiente'),
            ('resolved', 'Resuelto'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='pending',
        required=True,
        index=True,
    )

    # ----- Resolución -----
    resolved_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto resuelto',
    )
    resolved_po_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Orden de compra creada',
        help='Se asigna a TODOS los pendientes del mismo group_token cuando se resuelve la última línea y se crea la PO.',
    )
    resolution_type = fields.Selection(
        selection=[
            ('new', 'Producto nuevo creado'),
            ('existing', 'Producto existente seleccionado'),
        ],
        string='Tipo de resolución',
    )

    # ----- Computed: total pendiente del grupo (para mostrar en UI) -----
    group_pending_count = fields.Integer(
        string='Pendientes en el grupo',
        compute='_compute_group_pending_count',
    )
    group_total_count = fields.Integer(
        string='Total en el grupo',
        compute='_compute_group_pending_count',
    )

    @api.depends('group_token', 'state')
    def _compute_group_pending_count(self):
        for rec in self:
            if not rec.group_token:
                rec.group_pending_count = 0
                rec.group_total_count = 0
                continue
            siblings = self.search([('group_token', '=', rec.group_token)])
            rec.group_total_count = len(siblings)
            rec.group_pending_count = len(siblings.filtered(lambda r: r.state == 'pending'))