# models/copier_stock_extend.py
from odoo import api, fields, models, _, exceptions
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CopierStock(models.Model):
    _inherit = 'copier.stock'
    
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
                'default_single_machine': True
            },
        }

    def action_create_multiple_sale_order(self):
        """Crear orden de venta para múltiples máquinas seleccionadas"""
        available_machines = self.filtered(lambda m: m.state == 'available')
        
        if not available_machines:
            raise exceptions.UserError("No hay máquinas disponibles seleccionadas.")
        
        return {
            'name': 'Crear Orden de Venta Múltiple',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.sale.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_machine_ids': [(6, 0, available_machines.ids)],
                'default_single_machine': False
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
        
        # Buscar o crear producto genérico para máquinas usadas
        product = self._get_or_create_sale_product()
        
        # Crear línea de orden
        line_vals = {
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': f'{product.name} - {self.marca_id.name} {self.modelo_id.name} (Serie: {self.serie})',
            'product_uom_qty': 1,
            'price_unit': self.sale_price,
            'product_uom': product.uom_id.id,
        }
        
        order_line = self.env['sale.order.line'].create(line_vals)
        
        # Vincular máquina con orden y línea
        self.write({
            'sale_order_id': sale_order.id,
            'sale_order_line_id': order_line.id,
            'state': 'in_order'
        })
        
        return order_line

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