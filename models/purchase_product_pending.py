# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields


class PurchaseProductPending(models.Model):
    _name = 'purchase.product.pending'
    _description = 'Factura pendiente por producto desconocido'
    _order = 'create_date desc'

    token = fields.Char(
        string='Token',
        required=True,
        readonly=True,
        default=lambda self: str(uuid.uuid4()),
        copy=False,
    )
    description_proveedor = fields.Char(
        string='Descripción en factura',
        required=True,
    )
    supplier_name = fields.Char(
        string='Proveedor',
    )
    supplier_ruc = fields.Char(
        string='RUC proveedor',
    )
    invoice_id = fields.Char(
        string='N° Factura',
    )
    invoice_payload = fields.Text(
        string='Payload JSON',
        required=True,
        help='JSON completo de la factura recibida',
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pendiente'),
            ('resolved', 'Resuelto'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='pending',
        required=True,
    )
    resolved_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto resuelto',
    )
    resolved_po_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Orden de compra creada',
    )
    resolution_type = fields.Selection(
        selection=[
            ('new', 'Producto nuevo creado'),
            ('existing', 'Producto existente seleccionado'),
        ],
        string='Tipo de resolución',
    )