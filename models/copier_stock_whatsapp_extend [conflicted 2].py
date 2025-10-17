# models/copier_stock_whatsapp_extend.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
        # store=False por defecto; suficiente para mostrar en vista
    )

    @api.depends('whatsapp_alert_ids')
    def _compute_whatsapp_alert_count(self):
        for machine in self:
            machine.whatsapp_alert_count = len(machine.whatsapp_alert_ids)

    def action_view_whatsapp_alerts(self):
        """Ver alertas WhatsApp de esta máquina"""
        self.ensure_one()
        return {
            'name': _('Alertas WhatsApp - %s') % (self.display_name,),
            'type': 'ir.actions.act_window',
            'res_model': 'copier.whatsapp.alert',
            'view_mode': 'tree,form',
            'domain': [('machine_id', '=', self.id)],
            'context': {'default_machine_id': self.id},
        }

    def action_send_manual_alert(self):
        """Enviar alerta manual para esta máquina"""
        self.ensure_one()

        # Si tu modelo realmente tiene 'state', perfecto; si no, elimina esta validación
        if getattr(self, 'state', False) and self.state != 'available':
            raise UserError(_("Solo se pueden enviar alertas para máquinas disponibles."))

        # Crear alertas para distribuidores interesados
        self.env['copier.whatsapp.alert'].create_new_stock_alerts(self.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Alertas Enviadas'),
                'message': _('Se han enviado alertas para la máquina %s') % self.display_name,
                'type': 'success',
                'sticky': False,
            }
        }
