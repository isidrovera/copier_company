# models/res_partner_extend.py
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Campo para identificar distribuidores
    is_distributor = fields.Boolean(
        string='Es Distribuidor',
        default=False,
        help='Marcar si este contacto es un distribuidor de máquinas'
    )
    
    # Campos para notificaciones WhatsApp
    whatsapp_phone = fields.Char(
        string='Teléfono WhatsApp',
        help='Número de teléfono para notificaciones por WhatsApp'
    )
    
    notify_new_stock = fields.Boolean(
        string='Notificar Nuevo Stock',
        default=True,
        help='Recibir notificaciones cuando lleguen nuevas máquinas'
    )
    
    notify_orders = fields.Boolean(
        string='Notificar Órdenes',
        default=True,
        help='Recibir notificaciones sobre el estado de las órdenes'
    )
    
    # Preferencias de máquinas
    preferred_brands = fields.Many2many(
        'marcas.maquinas',
        string='Marcas Preferidas',
        help='Marcas de máquinas de interés para notificaciones'
    )
    
    preferred_types = fields.Selection([
        ('monocroma', 'Monocroma'),
        ('color', 'Color'),
        ('both', 'Ambas')
    ], string='Tipos Preferidos', default='both',
       help='Tipos de máquinas de interés')
    
    # Campos relacionados con órdenes
    copier_order_count = fields.Integer(
        string='Órdenes de Máquinas',
        compute='_compute_copier_order_count'
    )
    
    copier_machine_count = fields.Integer(
        string='Máquinas Compradas',
        compute='_compute_copier_machine_count'
    )

    @api.depends('sale_order_ids')
    def _compute_copier_order_count(self):
        """Contar órdenes que contienen máquinas usadas"""
        for partner in self:
            # Contar órdenes que tienen productos "Venta de Máquina Usada"
            orders = partner.sale_order_ids.filtered(
                lambda o: any(line.product_id.name == 'Venta de Máquina Usada' 
                             for line in o.order_line)
            )
            partner.copier_order_count = len(orders)

    def _compute_copier_machine_count(self):
        """Contar máquinas compradas por este distribuidor"""
        for partner in self:
            machines = self.env['copier.stock'].search([
                ('reserved_by', '=', partner.id),
                ('state', '=', 'sold')
            ])
            partner.copier_machine_count = len(machines)

    def action_view_copier_orders(self):
        """Ver órdenes de máquinas de este distribuidor"""
        self.ensure_one()
        
        # Buscar órdenes que contengan máquinas usadas
        orders = self.sale_order_ids.filtered(
            lambda o: any(line.product_id.name == 'Venta de Máquina Usada' 
                         for line in o.order_line)
        )
        
        return {
            'name': f'Órdenes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders.ids)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_copier_machines(self):
        """Ver máquinas compradas por este distribuidor"""
        self.ensure_one()
        
        return {
            'name': f'Máquinas de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.stock',
            'view_mode': 'list,form',
            'domain': [('reserved_by', '=', self.id), ('state', '=', 'sold')],
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Campo relacionado para mostrar máquinas
    copier_machine_ids = fields.One2many(
        'copier.stock',
        'sale_order_id',
        string='Máquinas Relacionadas',
        readonly=True
    )
    
    copier_machine_count = fields.Integer(
        string='Cantidad de Máquinas',
        compute='_compute_copier_machine_count'
    )

    @api.depends('copier_machine_ids')
    def _compute_copier_machine_count(self):
        """Contar máquinas en esta orden"""
        for order in self:
            order.copier_machine_count = len(order.copier_machine_ids)

    def action_view_copier_machines(self):
        """Ver máquinas de esta orden"""
        self.ensure_one()
        
        return {
            'name': f'Máquinas - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.stock',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
        }