# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ModelosMaquinas(models.Model):
    _name = 'modelos.maquinas'
    _description = 'Modelos de Máquinas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ⚠️ MISMA regla que tu _sql_constraints = unique(name)
    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if rec.name:
                dup = self.search_count([
                    ('name', '=', rec.name),
                    ('id', '!=', rec.id)
                ])
                if dup:
                    raise ValidationError(
                        _('El modelo de la máquina debe ser único!')
                    )

    name = fields.Char(string='Modelo', required=True, index=True)
    marca_id = fields.Many2one('marcas.maquinas', string='Marca')
    especificaciones = fields.Html(string="Especificaciones")
    active = fields.Boolean(string="Activo", default=True)
    imagen = fields.Binary(string='Imagen', attachment=True, store=True)

    tipo_maquina = fields.Selection([
        ('fotocopiadora', 'Fotocopiadora'),
        ('impresora', 'Impresora'),
        ('multifuncional', 'Multifuncional'),
        ('otro', 'Otro')
    ], string='Tipo de Máquina', required=True, default='fotocopiadora', tracking=True)

    producto_name = fields.Char(
        string='Nombre del Producto',
        compute='_compute_producto_name',
        store=True,
        help='Nombre que tendrá el producto en inventario'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto Creado',
        readonly=True,
        help='Producto de inventario asociado a este modelo'
    )

    has_product = fields.Boolean(
        string='Tiene Producto',
        compute='_compute_has_product',
        help='Indica si ya se creó el producto para este modelo'
    )

    @api.depends('tipo_maquina', 'marca_id', 'name')
    def _compute_producto_name(self):
        for record in self:
            if record.tipo_maquina and record.marca_id and record.name:
                tipo_title = dict(
                    record._fields['tipo_maquina'].selection
                ).get(record.tipo_maquina, '')
                record.producto_name = f"{tipo_title} {record.marca_id.name} {record.name}"
            else:
                record.producto_name = ""

    @api.depends('product_id')
    def _compute_has_product(self):
        for record in self:
            record.has_product = bool(record.product_id)

    def action_create_product(self):
        self.ensure_one()

        try:
            if not self.tipo_maquina:
                raise UserError("Debe seleccionar el tipo de máquina antes de crear el producto.")

            if not self.marca_id:
                raise UserError("Debe seleccionar la marca antes de crear el producto.")

            if not self.name:
                raise UserError("Debe ingresar el nombre del modelo antes de crear el producto.")

            if self.product_id:
                raise UserError(f"Ya existe un producto asociado: {self.product_id.name}")

            existing_product = self.env['product.product'].search([
                ('name', '=', self.producto_name)
            ], limit=1)

            if existing_product:
                raise UserError(
                    f"Ya existe un producto con el nombre '{self.producto_name}'. "
                    f"Por favor, revise si hay duplicados."
                )

            category = self._get_or_create_category()

            income_account, expense_account = self._get_default_accounts()

            product_vals = {
                'name': self.producto_name,
                'type': 'consu',
                'categ_id': category.id,
                'is_storable': True,
                'sale_ok': True,
                'purchase_ok': True,
                'invoice_policy': 'order',
                'default_code': self._generate_internal_reference(),
                'description': (
                    f"Modelo: {self.name}\n"
                    f"Marca: {self.marca_id.name}\n"
                    f"Tipo: {dict(self._fields['tipo_maquina'].selection).get(self.tipo_maquina)}"
                ),
                'company_id': self.env.company.id,
                'active': True,
                'tracking': 'serial',
            }

            if income_account:
                product_vals['property_account_income_id'] = income_account.id
            if expense_account:
                product_vals['property_account_expense_id'] = expense_account.id

            new_product = self.env['product.product'].create(product_vals)

            self.write({'product_id': new_product.id})

            _logger.info(
                "Producto creado exitosamente: %s (ID: %s) para modelo %s",
                new_product.name, new_product.id, self.name
            )

            self.message_post(
                body=(
                    f"✅ Producto de inventario creado exitosamente: <b>{new_product.name}</b><br/>"
                    f"Referencia interna: {new_product.default_code}<br/>"
                    f"Categoría: {category.name}<br/>"
                    f"Seguimiento: Por número de serie"
                ),
                message_type='notification'
            )

            return {
                'type': 'ir.actions.act_window',
                'name': 'Producto Creado',
                'res_model': 'product.product',
                'res_id': new_product.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {'form_view_initial_mode': 'readonly'}
            }

        except Exception as e:
            _logger.exception("Error al crear producto para modelo %s", self.name)
            raise UserError(f"Error al crear el producto: {str(e)}")

    def _get_or_create_category(self):
        category_name = dict(
            self._fields['tipo_maquina'].selection
        ).get(self.tipo_maquina, 'Fotocopiadora')

        category = self.env['product.category'].search([
            ('name', '=', category_name)
        ], limit=1)

        if not category:
            category = self.env['product.category'].create({
                'name': category_name,
                'removal_strategy_id': False,
                'parent_id': False,
            })
            _logger.info(f"Categoría creada: {category_name}")

        return category

    def _get_default_accounts(self):
        try:
            income_account = expense_account = False

            try:
                income_account = self.env['account.account'].search([
                    ('code', '=like', '7%'),
                    ('deprecated', '=', False)
                ], limit=1)

                expense_account = self.env['account.account'].search([
                    ('code', '=like', '6%'),
                    ('deprecated', '=', False)
                ], limit=1)

            except Exception as e:
                _logger.warning(f"Error buscando cuentas específicas: {str(e)}")

            return income_account, expense_account

        except Exception as e:
            _logger.warning(f"Error obteniendo cuentas por defecto: {str(e)}")
            return False, False

    def _generate_internal_reference(self):
        try:
            marca_code = self.marca_id.name[:3].upper() if self.marca_id else "XXX"
            tipo_code = self.tipo_maquina[:4].upper() if self.tipo_maquina else "XXXX"
            modelo_clean = ''.join(c for c in self.name if c.isalnum())[:10]
            return f"{tipo_code}-{marca_code}-{modelo_clean}"
        except Exception:
            return f"PROD-{self.id}"

    def action_view_product(self):
        self.ensure_one()

        if not self.product_id:
            raise UserError("No hay un producto asociado a este modelo.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Producto Asociado',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def unlink(self):
        for record in self:
            if record.product_id:
                raise UserError(
                    f"Este modelo tiene un producto asociado: {record.product_id.name}\n\n"
                    f"Para eliminar el modelo, primero debe:\n"
                    f"1. Eliminar manualmente el producto desde Inventario > Productos, o\n"
                    f"2. Desvincular el producto editando este modelo"
                )

        return super().unlink()


class MarcasMaquinas(models.Model):
    _name = 'marcas.maquinas'
    _description = 'Marcas de Máquinas'

    name = fields.Char(string='Marca')

    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if rec.name:
                dup = self.search_count([
                    ('name', '=', rec.name),
                    ('id', '!=', rec.id)
                ])
                if dup:
                    raise ValidationError("Ya existe una marca con este nombre.")


class AccesoriosMaquinas(models.Model):
    _name = 'accesorios.maquinas'
    _description = 'Accesorios de Máquinas'

    name = fields.Char(string='Accesorio', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if rec.name:
                dup = self.search_count([
                    ('name', '=', rec.name),
                    ('id', '!=', rec.id)
                ])
                if dup:
                    raise ValidationError("Ya existe un accesorio con este nombre.")


class CopierEstados(models.Model):
    _name = 'copier.estados'
    _description = 'Copier States'

    name = fields.Char(string="Name", required=True)


class CopierDuracionAlquiler(models.Model):
    _name = 'copier.duracion'
    _description = 'Aqui se crean el tiempo de duracion de alquiler'

    name = fields.Char(string='Duración')
