# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class WhatsAppTemplateTestWizard(models.TransientModel):
    _name = 'whatsapp.template.test.wizard'
    _description = 'Wizard para Probar Plantilla WhatsApp'
    
    # ============================================
    # CAMPOS
    # ============================================
    template_id = fields.Many2one(
        'whatsapp.template',
        'Plantilla',
        required=True,
        ondelete='cascade'
    )
    model_id = fields.Many2one(
        'ir.model',
        related='template_id.model_id',
        string='Modelo',
        store=False,  # ← Sin store para evitar problemas de carga
        readonly=True
    )
    test_record_id = fields.Integer(
        'ID del Registro de Prueba',
        required=True,
        help='ID de un registro real del modelo para generar la prueba'
    )
    test_phone = fields.Char(
        'Teléfono de Prueba',
        help='Número de teléfono para enviar prueba (opcional, si está vacío usa los destinatarios configurados)'
    )
    
    # Preview
    preview_message = fields.Text(
        'Vista Previa del Mensaje',
        compute='_compute_preview',
        help='Mensaje que se enviará'
    )
    preview_recipients = fields.Text(
        'Destinatarios',
        compute='_compute_preview',
        help='Destinatarios que recibirán el mensaje'
    )
    
    # ============================================
    # COMPUTE
    # ============================================
    @api.depends('template_id', 'test_record_id', 'test_phone')
    def _compute_preview(self):
        """Generar vista previa"""
        for wizard in self:
            if not wizard.template_id or not wizard.test_record_id:
                wizard.preview_message = 'Configure los datos para ver la vista previa'
                wizard.preview_recipients = ''
                continue
            
            try:
                # Obtener modelo desde template_id directamente
                model_name = wizard.template_id.model_name
                if not model_name:
                    wizard.preview_message = 'Plantilla sin modelo configurado'
                    wizard.preview_recipients = ''
                    continue
                
                # Obtener registro
                record = self.env[model_name].browse(wizard.test_record_id)
                if not record.exists():
                    wizard.preview_message = f'Registro ID {wizard.test_record_id} no encontrado'
                    wizard.preview_recipients = ''
                    continue
                
                # Mensaje
                message = wizard.template_id._process_message_template(record)
                wizard.preview_message = message
                
                # Destinatarios
                if wizard.test_phone:
                    config = wizard.template_id.config_id or self.env['whatsapp.config'].get_active_config()
                    clean_phone = config.clean_phone_number(wizard.test_phone)
                    wizard.preview_recipients = f"📱 {clean_phone} (Manual)"
                else:
                    recipients = wizard.template_id._get_recipients(record)
                    if recipients:
                        wizard.preview_recipients = '\n'.join([f"📱 {phone}" for phone in recipients])
                    else:
                        wizard.preview_recipients = '⚠️ No se encontraron destinatarios'
                
            except Exception as e:
                _logger.exception("Error generando preview")
                wizard.preview_message = f'Error: {str(e)}'
                wizard.preview_recipients = ''
    
    # ============================================
    # ACCIONES
    # ============================================
    def action_send_test(self):
        """Enviar mensaje de prueba"""
        self.ensure_one()
        
        try:
            # Obtener modelo desde template_id
            model_name = self.template_id.model_name
            if not model_name:
                raise UserError(_('La plantilla no tiene modelo configurado'))
            
            # Obtener registro
            record = self.env[model_name].browse(self.test_record_id)
            if not record.exists():
                raise UserError(_('Registro ID %s no encontrado') % self.test_record_id)
            
            # Si hay teléfono manual, crear notificación directa
            if self.test_phone:
                config = self.template_id.config_id or self.env['whatsapp.config'].get_active_config()
                clean_phone = config.clean_phone_number(self.test_phone)
                
                if not clean_phone:
                    raise ValidationError(_('Formato de teléfono inválido'))
                
                # Verificar conexión
                connection_status = config.check_connection(silent=True)
                if not connection_status.get('connected'):
                    raise UserError(_('WhatsApp no está conectado'))
                
                # Procesar mensaje
                message = self.template_id._process_message_template(record)
                
                # Enviar
                result = config.send_message(clean_phone, message)
                
                if result['success']:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': f'✅ Mensaje de prueba enviado a {clean_phone}',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(_('Error: %s') % result.get('error'))
            
            else:
                # Usar destinatarios configurados
                notifications = self.template_id.send_notification(record, force=True)
                
                if not notifications:
                    raise UserError(_('No se encontraron destinatarios'))
                
                sent_count = len([n for n in notifications if n.state == 'sent'])
                
                if sent_count > 0:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': f'✅ {sent_count} mensaje(s) de prueba enviado(s)',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(_('Todos los envíos fallaron'))
                    
        except UserError:
            raise
        except Exception as e:
            _logger.exception("Error enviando prueba")
            raise UserError(_('Error enviando prueba: %s') % str(e))