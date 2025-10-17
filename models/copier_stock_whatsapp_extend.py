# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CopierStock(models.Model):
    _inherit = 'copier.stock'

    # Relación con alertas de WhatsApp
    whatsapp_alert_ids = fields.One2many(
        'copier.whatsapp.alert',
        'machine_id',
        string='Alertas WhatsApp'
    )

    whatsapp_alert_count = fields.Integer(
        string='Total Alertas',
        compute='_compute_whatsapp_alert_count',
        store=False
    )

    @api.depends('whatsapp_alert_ids')
    def _compute_whatsapp_alert_count(self):
        for machine in self:
            machine.whatsapp_alert_count = len(machine.whatsapp_alert_ids)

    # ---------------------------
    # ACCIONES
    # ---------------------------
    def action_view_whatsapp_alerts(self):
        """Abrir las alertas WhatsApp asociadas a esta máquina."""
        self.ensure_one()

        # Si no existe el modelo, evitamos traceback
        if 'copier.whatsapp.alert' not in self.env:
            raise UserError(_('El modelo de alertas WhatsApp no está instalado.'))

        return {
            'name': _('Alertas WhatsApp - %s') % (self.display_name or self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'copier.whatsapp.alert',
            'view_mode': 'tree,form',
            'domain': [('machine_id', '=', self.id)],
            'context': {'default_machine_id': self.id},
            'target': 'current',
        }

    def action_send_manual_alert(self):
        """Enviar una alerta manual (broadcast) para esta máquina a los suscriptores interesados."""
        self.ensure_one()

        # Validaciones de negocio
        if self.state != 'available':
            raise UserError(_('Solo se pueden enviar alertas para máquinas en estado "Disponible".'))

        if 'copier.whatsapp.alert' not in self.env:
            raise UserError(_('El modelo de alertas WhatsApp no está instalado.'))

        Alert = self.env['copier.whatsapp.alert']

        # Verificamos si el modelo implementa el helper; si no, caemos a create básico
        create_helper = getattr(Alert, 'create_new_stock_alerts', None)

        try:
            if callable(create_helper):
                # Helper centralizado (recomendado)
                created = create_helper(self.id)
                created_count = len(created) if created else 0
            else:
                # Fallback: creamos un registro básico de alerta (adaptar a tu esquema)
                vals = {
                    'machine_id': self.id,
                    'message': _('Nueva disponibilidad: %s (Serie: %s)') % (self.modelo_id.display_name, self.serie or '-'),
                    # Agrega aquí cualquier otro campo requerido de copier.whatsapp.alert,
                    # por ejemplo: 'subscriber_id', 'status', etc.
                }
                Alert.create(vals)
                created_count = 1

            # Notificación amigable en la UI
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Alertas enviadas'),
                    'message': _('%s alerta(s) generada(s) para la máquina %s') % (created_count, (self.display_name or self.name)),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except UserError:
            # Re-lanzamos UserError tal cual para que Odoo muestre el mensaje
            raise
        except Exception as e:
            _logger.exception('Error al enviar alerta manual de WhatsApp: %s', e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Ocurrió un error al enviar la alerta: %s') % (str(e)),
                    'type': 'danger',
                    'sticky': True,
                }
            }
