# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class WhatsAppSendWizard(models.TransientModel):
    _name = 'whatsapp.send.wizard'
    _description = 'Wizard para Enviar WhatsApp'
    
    # ============================================
    # CAMPOS
    # ============================================
    model_name = fields.Char(
        'Modelo',
        required=True,
        help='Nombre técnico del modelo'
    )
    res_id = fields.Integer(
        'ID del Registro',
        required=True,
        help='ID del registro'
    )
    template_id = fields.Many2one(
        'whatsapp.template',
        'Plantilla',
        required=True,
        domain="[('model_name', '=', model_name), ('active', '=', True)]",
        help='Plantilla a usar para el mensaje'
    )
    
    # Preview
    preview_message = fields.Text(
        'Vista Previa del Mensaje',
        compute='_compute_preview_message',
        help='Vista previa del mensaje que se enviará'
    )
    preview_recipients = fields.Text(
        'Destinatarios',
        compute='_compute_preview_recipients',
        help='Números a los que se enviará el mensaje'
    )
    
    force_send = fields.Boolean(
        'Forzar Envío',
        default=False,
        help='Enviar aunque no se cumplan las condiciones'
    )
    
    # ============================================
    # COMPUTE
    # ============================================
    @api.depends('template_id', 'model_name', 'res_id')
    def _compute_preview_message(self):
        """Generar vista previa del mensaje"""
        for wizard in self:
            if not wizard.template_id or not wizard.model_name or not wizard.res_id:
                wizard.preview_message = 'Seleccione una plantilla para ver la vista previa'
                continue
            
            try:
                record = self.env[wizard.model_name].browse(wizard.res_id)
                if not record.exists():
                    wizard.preview_message = 'Registro no encontrado'
                    continue
                
                message = wizard.template_id._process_message_template(record)
                wizard.preview_message = message
                
            except Exception as e:
                wizard.preview_message = f'Error generando vista previa: {str(e)}'
    
    @api.depends('template_id', 'model_name', 'res_id')
    def _compute_preview_recipients(self):
        """Obtener destinatarios"""
        for wizard in self:
            if not wizard.template_id or not wizard.model_name or not wizard.res_id:
                wizard.preview_recipients = 'Seleccione una plantilla para ver los destinatarios'
                continue
            
            try:
                record = self.env[wizard.model_name].browse(wizard.res_id)
                if not record.exists():
                    wizard.preview_recipients = 'Registro no encontrado'
                    continue
                
                recipients = wizard.template_id._get_recipients(record)
                
                if recipients:
                    wizard.preview_recipients = '\n'.join([f"📱 {phone}" for phone in recipients])
                else:
                    wizard.preview_recipients = '⚠️ No se encontraron destinatarios'
                
            except Exception as e:
                wizard.preview_recipients = f'Error obteniendo destinatarios: {str(e)}'
    
    # ============================================
    # ACCIONES
    # ============================================
    def action_send(self):
        """Enviar notificación WhatsApp"""
        self.ensure_one()
        
        try:
            # Obtener registro
            record = self.env[self.model_name].browse(self.res_id)
            if not record.exists():
                raise UserError(_('El registro ya no existe'))
            
            # Enviar notificación
            notifications = self.template_id.send_notification(record, force=self.force_send)
            
            if not notifications:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': '⚠️ No se pudo enviar ninguna notificación. Revise la configuración.',
                        'type': 'warning',
                        'sticky': True,
                    }
                }
            
            # Contar enviadas y fallidas
            sent_count = len([n for n in notifications if n.state == 'sent'])
            failed_count = len([n for n in notifications if n.state == 'failed'])
            
            if sent_count > 0:
                message = f'✅ {sent_count} mensaje(s) enviado(s) correctamente'
                if failed_count > 0:
                    message += f'\n⚠️ {failed_count} mensaje(s) fallaron'
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': message,
                        'type': 'success' if failed_count == 0 else 'warning',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'❌ Todos los mensajes fallaron ({failed_count})',
                        'type': 'danger',
                        'sticky': True,
                    }
                }
                
        except Exception as e:
            raise UserError(_('Error enviando notificación: %s') % str(e))
    
    def action_send_and_close(self):
        """Enviar y cerrar wizard"""
        self.action_send()
        return {'type': 'ir.actions.act_window_close'}