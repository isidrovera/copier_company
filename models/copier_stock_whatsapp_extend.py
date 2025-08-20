# models/copier_stock_whatsapp_extend.py
from odoo import api, fields, models

class CopierStock(models.Model):
    _inherit = 'copier.stock'
    
    # Relación con alertas WhatsApp
    whatsapp_alert_ids = fields.One2many(
        'copier.whatsapp.alert',
        'machine_id',
        string='Alertas WhatsApp'
    )
    
    whatsapp_alert_count = fields.Integer(
        string='Total Alertas',
        compute='_compute_whatsapp_alert_count'
    )

    @api.depends('whatsapp_alert_ids')
    def _compute_whatsapp_alert_count(self):
        for machine in self:
            machine.whatsapp_alert_count = len(machine.whatsapp_alert_ids)

    def action_view_whatsapp_alerts(self):
        """Ver alertas WhatsApp de esta máquina"""
        self.ensure_one()
        
        return {
            'name': f'Alertas WhatsApp - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.whatsapp.alert',
            'view_mode': 'list,form',
            'domain': [('machine_id', '=', self.id)],
            'context': {'default_machine_id': self.id}
        }

    def action_send_manual_alert(self):
        """Enviar alerta manual para esta máquina"""
        self.ensure_one()
        
        if self.state != 'available':
            raise exceptions.UserError("Solo se pueden enviar alertas para máquinas disponibles.")
        
        # Crear alertas para distribuidores interesados
        self.env['copier.whatsapp.alert'].create_new_stock_alerts(self.id)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Alertas Enviadas',
                'message': f'Se han enviado alertas para la máquina {self.name}',
                'type': 'success',
                'sticky': False,
            }
        }