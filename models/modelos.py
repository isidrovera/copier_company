from odoo import api, fields, models, _
import requests
import logging
import base64
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class ModelosMaquinas(models.Model):
    _name = 'modelos.maquinas'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El modelo de la máquina debe ser único!')
    ]
    name = fields.Char(string='Modelo', required=True, index=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca')
    especificaciones = fields.Html(string="Especificaciones")
    active = fields.Boolean(string="Activo", default=True)    
    imagen = fields.Binary(string='Imagen', attachment=True, 
    store=True
    )
    
    
    # Campo nuevo para tipo de máquina
    tipo_maquina = fields.Selection([
        ('fotocopiadora', 'Fotocopiadora'),
        ('impresora', 'Impresora'),
        ('multifuncional', 'Multifuncional'),
        ('otro', 'Otro')
    ], string='Tipo de Máquina', required=True, default='fotocopiadora', tracking=True)
    
    # Campo concatenado para nombre del producto
    producto_name = fields.Char(
        string='Nombre del Producto',
        compute='_compute_producto_name',
        store=True,
        help='Nombre que tendrá el producto en inventario'
    )
    
    # Relación con el producto creado
    product_id = fields.Many2one(
        'product.product',
        string='Producto Creado',
        readonly=True,
        help='Producto de inventario asociado a este modelo'
    )
    
    # Campo para saber si ya tiene producto
    has_product = fields.Boolean(
        string='Tiene Producto',
        compute='_compute_has_product',
        help='Indica si ya se creó el producto para este modelo'
    )

    @api.depends('tipo_maquina', 'marca_id', 'name')
    def _compute_producto_name(self):
        """Genera el nombre concatenado del producto"""
        for record in self:
            if record.tipo_maquina and record.marca_id and record.name:
                tipo_title = dict(record._fields['tipo_maquina'].selection).get(record.tipo_maquina, '')
                record.producto_name = f"{tipo_title} {record.marca_id.name} {record.name}"
            else:
                record.producto_name = ""

    @api.depends('product_id')
    def _compute_has_product(self):
        """Verifica si ya tiene producto creado"""
        for record in self:
            record.has_product = bool(record.product_id)

    def action_create_product(self):
        """
        Crea el producto de inventario para este modelo de máquina
        Se ejecuta mediante botón en la vista
        """
        self.ensure_one()
        
        try:
            # Validaciones previas
            if not self.tipo_maquina:
                raise UserError("Debe seleccionar el tipo de máquina antes de crear el producto.")
            
            if not self.marca_id:
                raise UserError("Debe seleccionar la marca antes de crear el producto.")
            
            if not self.name:
                raise UserError("Debe ingresar el nombre del modelo antes de crear el producto.")
            
            if self.product_id:
                raise UserError(f"Ya existe un producto asociado: {self.product_id.name}")
            
            # Verificar si ya existe un producto con el mismo nombre
            existing_product = self.env['product.product'].search([
                ('name', '=', self.producto_name)
            ], limit=1)
            
            if existing_product:
                raise UserError(f"Ya existe un producto con el nombre '{self.producto_name}'. "
                              f"Por favor, revise si hay duplicados.")
            
            # Buscar o crear la categoría "Fotocopiadora"
            category = self._get_or_create_category()
            
            # Obtener cuentas contables por defecto
            income_account, expense_account = self._get_default_accounts()
            
            # Crear el producto
            product_vals = {
                'name': self.producto_name,
                'type': 'consu',  # Consumible (como se ve en la imagen)
                'categ_id': category.id,
                'is_storable': True,  # Rastear inventario
                'sale_ok': True,  # Puede ser vendido
                'purchase_ok': True,  # Se puede comprar
                'invoice_policy': 'order',  # Política de facturación
                'default_code': self._generate_internal_reference(),  # Referencia
                'description': f"Modelo: {self.name}\nMarca: {self.marca_id.name}\nTipo: {dict(self._fields['tipo_maquina'].selection).get(self.tipo_maquina)}",
                'company_id': self.env.company.id,
                'active': True,
            }
            
            # Agregar seguimiento por número de serie único
            product_vals['tracking'] = 'serial'  # Por número de serie único
            
            # Agregar cuentas contables solo si existen
            income_account, expense_account = self._get_default_accounts()
            if income_account:
                product_vals['property_account_income_id'] = income_account.id
            if expense_account:
                product_vals['property_account_expense_id'] = expense_account.id
            
            # Crear el producto
            new_product = self.env['product.product'].create(product_vals)
            
            # Vincular el producto al modelo
            self.write({'product_id': new_product.id})
            
            # Log de la operación
            _logger.info(f"Producto creado exitosamente: {new_product.name} (ID: {new_product.id}) "
                        f"para modelo {self.name}")
            
            # Mensaje en el chatter
            self.message_post(
                body=f"✅ Producto de inventario creado exitosamente: <b>{new_product.name}</b><br/>"
                     f"Referencia interna: {new_product.default_code}<br/>"
                     f"Categoría: {category.name}<br/>"
                     f"Seguimiento: Por número de serie",
                message_type='notification'
            )
            
            # Retornar acción para mostrar el producto creado
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
            _logger.error(f"Error al crear producto para modelo {self.name}: {str(e)}")
            raise UserError(f"Error al crear el producto: {str(e)}")

    def _get_or_create_category(self):
        """Busca o crea la categoría apropiada según el tipo de máquina"""
        category_name = dict(self._fields['tipo_maquina'].selection).get(self.tipo_maquina, 'Fotocopiadora')
        
        # Buscar categoría existente
        category = self.env['product.category'].search([
            ('name', '=', category_name)
        ], limit=1)
        
        # Si no existe, crearla
        if not category:
            category = self.env['product.category'].create({
                'name': category_name,
                'removal_strategy_id': False,
                'parent_id': False,
            })
            _logger.info(f"Categoría creada: {category_name}")
        
        return category

    def _get_default_accounts(self):
        """Obtiene las cuentas contables por defecto para productos"""
        try:
            income_account = expense_account = False
            
            # Intentar obtener cuentas por defecto sin filtrar por company_id
            try:
                # Buscar cuenta de ingresos
                income_account = self.env['account.account'].search([
                    ('code', '=like', '7%'),
                    ('deprecated', '=', False)
                ], limit=1)
                
                # Buscar cuenta de gastos  
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
        """Genera una referencia interna para el producto"""
        try:
            # Crear referencia basada en marca y modelo
            marca_code = self.marca_id.name[:3].upper() if self.marca_id else "XXX"
            tipo_code = self.tipo_maquina[:4].upper() if self.tipo_maquina else "XXXX"
            
            # Tomar solo caracteres alfanuméricos del modelo
            modelo_clean = ''.join(c for c in self.name if c.isalnum())[:10]
            
            return f"{tipo_code}-{marca_code}-{modelo_clean}"
            
        except Exception:
            # Fallback si hay error
            return f"PROD-{self.id}"

    def action_view_product(self):
        """Acción para ver el producto asociado"""
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
        """Override para manejar eliminación del producto asociado"""
        for record in self:
            if record.product_id:
                # Preguntar al usuario qué hacer con el producto
                raise UserError(
                    f"Este modelo tiene un producto asociado: {record.product_id.name}\n\n"
                    f"Para eliminar el modelo, primero debe:\n"
                    f"1. Eliminar manualmente el producto desde Inventario > Productos, o\n"
                    f"2. Desvincular el producto editando este modelo"
                )
        
        return super().unlink()
class MarcasMaquinas(models.Model):
    _name = 'marcas.maquinas'
    name = fields.Char(string='Marca')
    
class AccesoriosMaquinas(models.Model):
    _name = 'accesorios.maquinas'
    name = fields.Char(string='Accesorio')
class CopierEstados(models.Model):
    _name = 'copier.estados'
    _description = 'Copier States'

    name = fields.Char(string="Name", required=True)

class CopierDuracionAlquiler(models.Model):
    
    _name='copier.duracion'
    _description = 'Aqui se crean el tiempo de duracion de alquiler'
    name = fields.Char(string='Duración')
    
