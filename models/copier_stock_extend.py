# models/copier_stock_extend.py
from odoo import api, fields, models, _, exceptions
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CopierStock(models.Model):
    _inherit = 'copier.stock'
    
    # Campo cliente para pre-asignar
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente Asignado',
        domain=[('customer_rank', '>', 0)],
        tracking=True,
        help='Cliente pre-asignado para esta máquina'
    )
    
    # Relación con sale.order nativo de Odoo
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        tracking=True,
        readonly=True
    )
    
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de Orden',
        tracking=True,
        readonly=True
    )
    
    # Agregar estado 'in_order'
    state = fields.Selection(selection_add=[
        ('in_order', 'En Orden'),
    ], ondelete={'in_order': 'cascade'})
    
    # Campo para agrupar máquinas en una sola orden
    group_order_key = fields.Char(
        string='Clave de Agrupación',
        help='Campo técnico para agrupar máquinas en una orden'
    )

    @api.onchange('reserved_by')
    def _onchange_reserved_by(self):
        """Auto-asignar cliente cuando se reserva"""
        if self.reserved_by:
            self.customer_id = self.reserved_by

    def action_create_sale_order(self):
        """Crear orden de venta para esta máquina"""
        self.ensure_one()
        
        if self.state != 'available':
            raise exceptions.UserError("Solo se pueden crear órdenes para máquinas disponibles.")
        
        return {
            'name': 'Crear Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.sale.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_machine_ids': [(6, 0, [self.id])],
                'default_single_machine': True,
                'default_partner_id': self.customer_id.id if self.customer_id else False
            },
        }

    def action_create_multiple_sale_order(self):
        """Crear orden de venta para múltiples máquinas seleccionadas"""
        available_machines = self.filtered(lambda m: m.state == 'available')
        
        if not available_machines:
            raise exceptions.UserError("No hay máquinas disponibles seleccionadas.")
        
        # Buscar cliente común si todas tienen el mismo
        common_customer = False
        customers = available_machines.mapped('customer_id')
        if len(set(customers.ids)) == 1 and customers:
            common_customer = customers[0].id
        
        return {
            'name': 'Crear Orden de Venta Múltiple',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.sale.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_machine_ids': [(6, 0, available_machines.ids)],
                'default_single_machine': False,
                'default_partner_id': common_customer
            },
        }

    def action_add_to_existing_order(self):
        """Agregar máquina a una orden existente"""
        self.ensure_one()
        
        if self.state != 'available':
            raise exceptions.UserError("Solo se pueden agregar máquinas disponibles.")
        
        return {
            'name': 'Agregar a Orden Existente',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.add.to.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_machine_id': self.id},
        }

    def _create_sale_order_line(self, sale_order):
        """Crear línea de orden de venta para esta máquina"""
        self.ensure_one()
        
        # Usar el producto específico del modelo si existe, sino genérico
        product = self._get_machine_product()
        
        # Crear descripción detallada con información de la máquina
        description = self._get_sale_line_description(product)
        
        # Crear línea de orden
        line_vals = {
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': description,
            'product_uom_qty': 1,
            'price_unit': self.sale_price,
            'product_uom': product.uom_id.id,
        }
        
        order_line = self.env['sale.order.line'].create(line_vals)
        
        # Vincular máquina con orden y línea
        self.write({
            'sale_order_id': sale_order.id,
            'sale_order_line_id': order_line.id,
            'state': 'in_order',
            'customer_id': sale_order.partner_id.id  # Actualizar cliente asignado
        })
        
        return order_line

    def _get_machine_product(self):
        """Obtener producto específico del modelo o genérico"""
        # Primero intentar usar el producto específico del modelo
        if self.modelo_id and hasattr(self.modelo_id, 'product_id') and self.modelo_id.product_id:
            return self.modelo_id.product_id
        
        # Si no, usar producto genérico
        return self._get_or_create_sale_product()

    def _get_sale_line_description(self, product):
        """Generar descripción detallada para la línea de venta"""
        # Descripción base del producto
        description = product.name
        
        # Agregar detalles específicos de la máquina
        details = []
        
        if self.marca_id and self.modelo_id:
            details.append(f"{self.marca_id.name} {self.modelo_id.name}")
        
        if self.serie:
            details.append(f"Serie: {self.serie}")
        
        if self.tipo:
            tipo_name = dict(self._fields['tipo'].selection).get(self.tipo, self.tipo)
            details.append(f"Tipo: {tipo_name}")
        
        if self.contometro:
            details.append(f"Contómetro: {self.contometro:,}")
        
        # Combinar descripción
        if details:
            description += f"\n{' - '.join(details)}"
        
        return description

    def _get_or_create_sale_product(self):
        """Obtener o crear producto genérico para ventas"""
        # Buscar producto existente
        product = self.env['product.product'].search([
            ('name', '=', 'Venta de Máquina Usada'),
            ('type', '=', 'consu')
        ], limit=1)
        
        if not product:
            # Crear producto genérico
            category = self.env['product.category'].search([
                ('name', '=', 'Máquinas Usadas')
            ], limit=1)
            
            if not category:
                category = self.env['product.category'].create({
                    'name': 'Máquinas Usadas'
                })
            
            product = self.env['product.product'].create({
                'name': 'Venta de Máquina Usada',
                'type': 'consu',
                'categ_id': category.id,
                'sale_ok': True,
                'purchase_ok': False,
                'list_price': 0,  # El precio se define por máquina
                'description': 'Producto genérico para venta de máquinas usadas',
            })
            
            _logger.info(f"Producto genérico creado: {product.name}")
        
        return product

    def action_view_sale_order(self):
        """Ver la orden de venta asociada"""
        self.ensure_one()
        
        if not self.sale_order_id:
            raise exceptions.UserError("Esta máquina no tiene una orden de venta asociada.")
        
        return {
            'name': 'Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CopierSaleOrderWizard(models.TransientModel):
    _name = 'copier.sale.order.wizard'
    _description = 'Asistente para Crear Orden de Venta'

    # Campos del asistente
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Distribuidor',
        required=True,
        domain=[('customer_rank', '>', 0)]
    )
    
    machine_ids = fields.Many2many(
        'copier.stock',
        string='Máquinas Seleccionadas',
        required=True
    )
    
    single_machine = fields.Boolean(
        string='Orden de Una Máquina',
        default=False
    )
    
    total_amount = fields.Float(
        string='Total',
        compute='_compute_total_amount'
    )
    
    notes = fields.Text(string='Notas')
    
    # Información de reserva
    reservation_days = fields.Integer(
        string='Días de Reserva',
        default=5,
        help='Días que se mantendrá la reserva'
    )

    @api.depends('machine_ids.sale_price')
    def _compute_total_amount(self):
        """Calcular total de máquinas seleccionadas"""
        for wizard in self:
            wizard.total_amount = sum(wizard.machine_ids.mapped('sale_price'))

    def action_create_order(self):
        """Crear la orden de venta"""
        self.ensure_one()
        
        # Validar que todas las máquinas estén disponibles
        unavailable = self.machine_ids.filtered(lambda m: m.state != 'available')
        if unavailable:
            raise exceptions.UserError(
                f"Las siguientes máquinas ya no están disponibles: {', '.join(unavailable.mapped('name'))}"
            )
        
        # Crear orden de venta
        order_vals = {
            'partner_id': self.partner_id.id,
            'date_order': fields.Datetime.now(),
            'note': self.notes or f'Orden para {len(self.machine_ids)} máquina(s) usada(s)',
            'state': 'draft',
        }
        
        sale_order = self.env['sale.order'].create(order_vals)
        
        # Crear líneas para cada máquina
        for machine in self.machine_ids:
            machine._create_sale_order_line(sale_order)
        
        # Mensaje en la orden
        sale_order.message_post(
            body=f"Orden creada automáticamente con {len(self.machine_ids)} máquina(s):<br/>" +
                 "<br/>".join([f"• {m.marca_id.name} {m.modelo_id.name} (Serie: {m.serie}) - ${m.sale_price}" 
                              for m in self.machine_ids]),
            message_type='notification'
        )
        
        # Log de creación
        _logger.info(f"Orden de venta {sale_order.name} creada con {len(self.machine_ids)} máquinas")
        
        # Retornar acción para abrir la orden creada
        return {
            'name': 'Orden de Venta Creada',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'}
        }


class CopierAddToOrderWizard(models.TransientModel):
    _name = 'copier.add.to.order.wizard'
    _description = 'Asistente para Agregar a Orden Existente'

    machine_id = fields.Many2one(
        'copier.stock',
        string='Máquina',
        required=True
    )
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=True,
        domain=[('state', 'in', ['draft', 'sent'])]
    )

    def action_add_to_order(self):
        """Agregar máquina a orden existente"""
        self.ensure_one()
        
        if self.machine_id.state != 'available':
            raise exceptions.UserError("La máquina ya no está disponible.")
        
        if self.sale_order_id.state not in ['draft', 'sent']:
            raise exceptions.UserError("Solo se puede agregar a órdenes en borrador o enviadas.")
        
        # Crear línea de orden
        self.machine_id._create_sale_order_line(self.sale_order_id)
        
        # Mensaje en la orden
        self.sale_order_id.message_post(
            body=f"Máquina agregada: {self.machine_id.marca_id.name} {self.machine_id.modelo_id.name} "
                 f"(Serie: {self.machine_id.serie}) - ${self.machine_id.sale_price}",
            message_type='notification'
        )
        
        return {
            'name': 'Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }