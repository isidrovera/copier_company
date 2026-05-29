# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CopierBillingGroup(models.Model):
    _name = 'copier.billing.group'
    _description = 'Grupo de Facturación de Máquinas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'cliente_id, name'

    name = fields.Char(
        string='Nombre del Grupo',
        required=True,
        tracking=True,
        help='Ejemplo: Cliente ABC - Oficina Principal'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True
    )

    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        store=True,
        tracking=True,
        readonly=True,
        index=True,
        copy=False,
        help="Cliente congelado al momento de crear el servicio. No cambia si la máquina cambia de cliente."
    )

    machine_ids = fields.One2many(
        'copier.company',
        'billing_group_id',
        string='Máquinas del Grupo'
    )

    machine_count = fields.Integer(
        string='Cantidad de Máquinas',
        compute='_compute_machine_count'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1),
        required=True
    )

    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Términos de pago'
    )

    dia_facturacion = fields.Integer(
        string='Día de Facturación',
        default=30,
        tracking=True
    )

    # ==========================
    # CONFIGURACIÓN DE VOLUMEN
    # ==========================

    volumen_mensual_bn = fields.Integer(
        string='Volumen B/N Compartido',
        tracking=True,
        help='Bolsa B/N compartida entre todas las máquinas del grupo.'
    )

    volumen_mensual_color = fields.Integer(
        string='Volumen Color Compartido',
        tracking=True,
        help='Opcional. Si color se cobra por consumo real, puede quedar en 0.'
    )

    cobrar_color_real = fields.Boolean(
        string='Color por consumo real',
        default=True,
        tracking=True,
        help='Si está activo, el color se cobra según consumo real, sin mínimo compartido.'
    )

    # ==========================
    # PRECIOS Y PRODUCTOS
    # ==========================

    producto_facturable_bn_id = fields.Many2one(
        'product.product',
        string='Producto B/N',
        tracking=True
    )

    producto_facturable_color_id = fields.Many2one(
        'product.product',
        string='Producto Color',
        tracking=True
    )

    costo_copia_bn = fields.Float(
        string='Costo por Copia B/N',
        digits=(16, 6),
        default=0.04,
        tracking=True
    )

    costo_copia_color = fields.Float(
        string='Costo por Copia Color',
        digits=(16, 6),
        default=0.20,
        tracking=True
    )

    precio_bn_incluye_igv = fields.Boolean(
        string='Precio B/N incluye IGV',
        default=False,
        tracking=True
    )

    precio_color_incluye_igv = fields.Boolean(
        string='Precio Color incluye IGV',
        default=False,
        tracking=True
    )

    igv = fields.Float(
        string='IGV (%)',
        default=18.0,
        tracking=True
    )

    descuento = fields.Float(
        string='Descuento (%)',
        default=0.0,
        tracking=True
    )

    # ==========================
    # DETRACCIÓN
    # ==========================

    aplicar_detraccion_auto = fields.Boolean(
        string='Aplicar detracción automática',
        default=True,
        tracking=True
    )

    monto_minimo_detraccion = fields.Monetary(
        string='Monto mínimo detracción',
        currency_field='currency_id',
        default=700.00,
        tracking=True
    )

    operation_type_detraccion = fields.Selection(
        selection=[
            ('1001', '1001 - Operación Sujeta a Detracción'),
        ],
        string='Tipo de operación para detracción',
        default='1001',
        tracking=True
    )

    note = fields.Text(
        string='Notas'
    )

    @api.depends('machine_ids')
    def _compute_machine_count(self):
        for rec in self:
            rec.machine_count = len(rec.machine_ids)

    @api.constrains('machine_ids', 'cliente_id')
    def _check_machines_cliente(self):
        for rec in self:
            maquinas_otro_cliente = rec.machine_ids.filtered(
                lambda m: m.cliente_id and m.cliente_id.id != rec.cliente_id.id
            )
            if maquinas_otro_cliente:
                raise ValidationError(
                    'Todas las máquinas del grupo deben pertenecer al mismo cliente del grupo.\n\n'
                    'Máquinas con cliente diferente:\n%s' %
                    '\n'.join(maquinas_otro_cliente.mapped('serie_id'))
                )

    def _precio_sin_igv(self, precio, incluye_igv):
        self.ensure_one()
        precio = precio or 0.0
        if incluye_igv:
            return precio / (1 + ((self.igv or 18.0) / 100.0))
        return precio

    def _get_lecturas_confirmadas(self):
        self.ensure_one()

        if not self.machine_ids:
            raise UserError('Este grupo no tiene máquinas vinculadas.')

        lecturas = self.env['copier.counter'].search([
            ('maquina_id', 'in', self.machine_ids.ids),
            ('state', '=', 'confirmed'),
        ], order='fecha_facturacion asc, id asc')

        if not lecturas:
            raise UserError('No hay lecturas confirmadas para las máquinas de este grupo.')

        return lecturas

    def action_view_machines(self):
        self.ensure_one()
        return {
            'name': 'Máquinas del Grupo',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.company',
            'view_mode': 'list,form',
            'domain': [('billing_group_id', '=', self.id)],
            'context': {
                'default_billing_group_id': self.id,
                'default_cliente_id': self.cliente_id.id,
            },
        }

    def action_view_confirmed_readings(self):
        self.ensure_one()
        return {
            'name': 'Lecturas Confirmadas del Grupo',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.counter',
            'view_mode': 'list,form',
            'domain': [
                ('maquina_id', 'in', self.machine_ids.ids),
                ('state', '=', 'confirmed'),
            ],
            'target': 'current',
        }

    def action_create_group_invoice(self):
        self.ensure_one()

        if not self.cliente_id:
            raise UserError('El grupo no tiene cliente configurado.')

        lecturas = self._get_lecturas_confirmadas()

        total_bn = sum(lecturas.mapped('total_copias_bn'))
        total_color = sum(lecturas.mapped('total_copias_color'))

        volumen_bn_incluido = self.volumen_mensual_bn or 0
        exceso_bn = max(0, total_bn - volumen_bn_incluido)

        if self.cobrar_color_real:
            color_facturable = total_color
        else:
            volumen_color_incluido = self.volumen_mensual_color or 0
            color_facturable = max(total_color, volumen_color_incluido)

        precio_bn_sin_igv = self._precio_sin_igv(
            self.costo_copia_bn,
            self.precio_bn_incluye_igv
        )
        precio_color_sin_igv = self._precio_sin_igv(
            self.costo_copia_color,
            self.precio_color_incluye_igv
        )

        invoice_lines = []

        detalle_maquinas = []
        for lectura in lecturas:
            detalle_maquinas.append(
                '- %s | Serie: %s | B/N: %s | Color: %s' % (
                    lectura.maquina_id.name.name if lectura.maquina_id.name else 'Máquina',
                    lectura.serie or lectura.maquina_id.serie_id or '',
                    lectura.total_copias_bn or 0,
                    lectura.total_copias_color or 0,
                )
            )

        detalle = '\n'.join(detalle_maquinas)

        if volumen_bn_incluido > 0:
            if not self.producto_facturable_bn_id:
                raise UserError('Debe configurar el producto B/N en el grupo.')

            subtotal_bn_base = volumen_bn_incluido * precio_bn_sin_igv

            invoice_lines.append((0, 0, {
                'product_id': self.producto_facturable_bn_id.id,
                'name': (
                    'Bolsa mensual B/N compartida - %s\n'
                    'Volumen incluido: %s copias B/N\n'
                    'Consumo total B/N: %s\n\n'
                    'Detalle por máquina:\n%s'
                ) % (
                    self.name,
                    volumen_bn_incluido,
                    total_bn,
                    detalle,
                ),
                'quantity': 1,
                'price_unit': subtotal_bn_base,
            }))

        if exceso_bn > 0:
            if not self.producto_facturable_bn_id:
                raise UserError('Debe configurar el producto B/N en el grupo.')

            invoice_lines.append((0, 0, {
                'product_id': self.producto_facturable_bn_id.id,
                'name': (
                    'Exceso B/N - %s\n'
                    'Consumo total B/N: %s\n'
                    'Volumen incluido: %s\n'
                    'Exceso B/N: %s'
                ) % (
                    self.name,
                    total_bn,
                    volumen_bn_incluido,
                    exceso_bn,
                ),
                'quantity': exceso_bn,
                'price_unit': precio_bn_sin_igv,
            }))

        if color_facturable > 0:
            if not self.producto_facturable_color_id:
                raise UserError('Debe configurar el producto Color en el grupo.')

            invoice_lines.append((0, 0, {
                'product_id': self.producto_facturable_color_id.id,
                'name': (
                    'Copias Color - %s\n'
                    'Consumo total color: %s\n\n'
                    'Detalle por máquina:\n%s'
                ) % (
                    self.name,
                    total_color,
                    detalle,
                ),
                'quantity': color_facturable,
                'price_unit': precio_color_sin_igv,
            }))

        if not invoice_lines:
            raise UserError('No hay líneas para facturar en este grupo.')

        fecha_factura = fields.Date.today()

        fechas_emision = lecturas.filtered(lambda l: l.fecha_emision_factura).mapped('fecha_emision_factura')
        if fechas_emision:
            fecha_factura = max(fechas_emision)

        invoice_vals = {
            'partner_id': self.cliente_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fecha_factura,
            'invoice_payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'invoice_origin': 'Grupo: %s | Lecturas: %s' % (
                self.name,
                ', '.join(lecturas.mapped('name'))
            ),
            'invoice_line_ids': invoice_lines,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Aplicar detracción por factura final, no por grupo.
        self.env['copier.invoice.helper']._apply_detraccion_if_needed(
            invoice=invoice,
            aplicar=self.aplicar_detraccion_auto,
            monto_minimo=self.monto_minimo_detraccion,
            operation_type=self.operation_type_detraccion,
        )

        lecturas.write({'state': 'invoiced'})

        invoice.message_post(
            body=(
                'Factura creada desde grupo de facturación: <b>%s</b><br/>'
                'Máquinas: %s<br/>'
                'Total B/N: %s<br/>'
                'Volumen B/N incluido: %s<br/>'
                'Exceso B/N: %s<br/>'
                'Total Color: %s'
            ) % (
                self.name,
                len(self.machine_ids),
                total_bn,
                volumen_bn_incluido,
                exceso_bn,
                total_color,
            )
        )

        for lectura in lecturas:
            lectura.message_post(
                body='Lectura facturada dentro del grupo <b>%s</b> en la factura <b>%s</b>.' % (
                    self.name,
                    invoice.name or invoice.ref or invoice.id,
                )
            )

        return {
            'name': 'Factura del Grupo',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }