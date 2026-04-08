# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductNameAlias(models.Model):
    _name = 'product.name.alias'
    _description = 'Alias de nombre de producto'
    _order = 'name asc'

    name = fields.Char(
        string='Nombre alternativo',
        required=True,
        help='Nombre exacto (en minúsculas) que puede llegar en una factura de proveedor',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Ya existe un alias con ese nombre exacto.'),
    ]