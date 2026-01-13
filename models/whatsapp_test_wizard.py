# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppTestMessageWizard(models.TransientModel):
    _name = 'whatsapp.test.message.wizard'
    _description = 'Enviar Mensaje de Prueba WhatsApp'
    
    config_id = fields.Many2one('whatsapp.config', 'Configuración', required=True)
    phone = fields.Char('Número de Teléfono', required=True, help='Formato: 51987654321')
    message = fields.Text(
        'Mensaje',
        required=True,
        default='🧪 *Mensaje de prueba*\n\nEste es un mensaje de prueba desde Odoo.\n\n_Copier Company S.A.C._'
    )
    
    def action_send_test(self):
        """Enviar mensaje de prueba"""
        self.ensure_one()
        
        try:
            import requests
            import json
            
            # Limpiar número
            clean_phone = self.config_id._clean_phone_number(self.phone)
            if not clean_phone:
                raise ValidationError(_('Formato de número inválido. Use formato: 51987654321'))
            
            # Verificar conexión
            status = self.config_id.check_connection(silent=True)
            if not status.get('connected'):
                raise ValidationError(_('WhatsApp no está conectado. Por favor escanea el código QR.'))
            
            # Verificar que el número existe en WhatsApp
            check_response = requests.post(
                f"{self.config_id.api_url}/api/check-number",
                headers={
                    'x-api-key': self.config_id.api_key,
                    'Content-Type': 'application/json'
                },
                data=json.dumps({'number': clean_phone}),
                timeout=10
            )
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                if not check_data.get('data', {}).get('exists'):
                    raise ValidationError(_(
                        'El número %s no existe en WhatsApp o no es válido.'
                    ) % clean_phone)
            
            # Enviar mensaje
            payload = {
                'number': clean_phone,
                'text': self.message
            }
            
            response = requests.post(
                f"{self.config_id.api_url}/api/send/text",
                headers={
                    'x-api-key': self.config_id.api_key,
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload),
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Actualizar estadísticas
                    self.config_id.write({
                        'total_messages_sent': self.config_id.total_messages_sent + 1,
                        'last_message_date': fields.Datetime.now()
                    })
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': f'✅ Mensaje de prueba enviado exitosamente a {clean_phone}',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise ValidationError(_('Error: %s') % result.get('message'))
            else:
                raise ValidationError(_('Error HTTP %s: %s') % (response.status_code, response.text))
                
        except ValidationError:
            raise
        except Exception as e:
            # Actualizar estadísticas de fallos
            self.config_id.write({
                'total_messages_failed': self.config_id.total_messages_failed + 1
            })
            raise ValidationError(_('Error enviando mensaje: %s') % str(e))