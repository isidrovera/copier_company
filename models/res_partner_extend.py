# models/res_partner_extend.py
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # CORREGIDO: Verificar si existe el modelo copier.stock
    # copier_machine_ids = fields.One2many(
    #     'copier.stock',
    #     'sale_order_id',
    #     string='Máquinas Relacionadas',
    #     readonly=True
    # )
    
    copier_machine_count = fields.Integer(
        string='Cantidad de Máquinas',
        compute='_compute_copier_machine_count'
    )

    def _compute_copier_machine_count(self):
        """Contar máquinas en esta orden"""
        for order in self:
            try:
                machines = self.env['copier.stock'].search([
                    ('sale_order_id', '=', order.id)
                ])
                order.copier_machine_count = len(machines)
            except:
                order.copier_machine_count = 0

    def action_view_copier_machines(self):
        """Ver máquinas de esta orden"""
        self.ensure_one()
        
        try:
            return {
                'name': f'Máquinas - {self.name}',
                'type': 'ir.actions.act_window',
                'res_model': 'copier.stock',
                'view_mode': 'list,form',
                'domain': [('sale_order_id', '=', self.id)],
            }
        except:
            return False