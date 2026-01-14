# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsAppNotification(models.Model):
    _name = 'whatsapp.notification'
    _description = 'Log de Notificaciones WhatsApp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'
    
    # ============================================
    # IDENTIFICACIÓN
    # ============================================
    name = fields.Char(
        'Número',
        default='Nuevo',
        copy=False,
        readonly=True,
        tracking=True
    )
    
    # ============================================
    # PLANTILLA Y REGISTRO
    # ============================================
    template_id = fields.Many2one(
        'whatsapp.template',
        'Plantilla',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    template_code = fields.Char(
        related='template_id.code',
        string='Código Plantilla',
        store=True,
        readonly=True
    )
    model_name = fields.Char(
        'Modelo',
        required=True,
        index=True,
        help='Nombre técnico del modelo (ej: copier.service.request)'
    )
    res_id = fields.Integer(
        'ID del Registro',
        required=True,
        index=True,
        help='ID del registro que generó la notificación'
    )
    record_reference = fields.Char(
        'Referencia',
        compute='_compute_record_reference',
        store=True,
        help='Referencia al registro (Modelo + ID)'
    )
    
    # ============================================
    # DESTINATARIO
    # ============================================
    recipient_phone = fields.Char(
        'Teléfono Destinatario',
        required=True,
        index=True,
        help='Número de teléfono en formato limpio (ej: 51987654321)'
    )
    recipient_name = fields.Char(
        'Nombre Destinatario',
        help='Nombre de la persona/entidad destinataria'
    )
    recipient_type = fields.Selection([
        ('client', 'Cliente'),
        ('technical', 'Técnico'),
        ('supervisor', 'Supervisor'),
        ('other', 'Otro'),
    ], string='Tipo de Destinatario',
       default='other')
    
    # ============================================
    # MENSAJE
    # ============================================
    message_content = fields.Text(
        'Contenido del Mensaje',
        required=True,
        help='Mensaje procesado que se envió'
    )
    has_attachment = fields.Boolean(
        'Tiene Adjunto',
        default=False
    )
    attachment_name = fields.Char(
        'Nombre del Adjunto'
    )
    
    # ============================================
    # ESTADO
    # ============================================
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ], string='Estado',
       default='draft',
       required=True,
       tracking=True,
       index=True)
    
    sent_date = fields.Datetime(
        'Fecha de Envío',
        readonly=True,
        tracking=True
    )
    error_message = fields.Text(
        'Mensaje de Error',
        readonly=True,
        help='Descripción del error si el envío falló'
    )
    retry_count = fields.Integer(
        'Intentos',
        default=0,
        help='Número de intentos de reenvío'
    )
    
    # ============================================
    # RESPUESTA API
    # ============================================
    api_message_id = fields.Char(
        'ID del Mensaje API',
        readonly=True,
        help='ID del mensaje retornado por WhatsApp API'
    )
    api_response = fields.Text(
        'Respuesta API',
        readonly=True,
        help='Respuesta completa de la API (JSON)'
    )
    delivery_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
    ], string='Estado de Entrega',
       readonly=True,
       help='Estado de entrega en WhatsApp (si está disponible)')
    
    # ============================================
    # CONFIGURACIÓN
    # ============================================
    config_id = fields.Many2one(
        'whatsapp.config',
        'Configuración Usada',
        required=True,
        ondelete='restrict'
    )
    
    # ============================================
    # SECUENCIA
    # ============================================
    @api.model_create_multi
    def create(self, vals_list):
        """Asignar secuencia al crear"""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('whatsapp.notification') or 'Nuevo'
        return super().create(vals_list)
    
    # ============================================
    # COMPUTE
    # ============================================
    @api.depends('model_name', 'res_id')
    def _compute_record_reference(self):
        """Generar referencia al registro"""
        for record in self:
            if record.model_name and record.res_id:
                try:
                    target_record = self.env[record.model_name].browse(record.res_id)
                    if target_record.exists():
                        display_name = target_record.display_name or f'ID {record.res_id}'
                        record.record_reference = f"{record.model_name} - {display_name}"
                    else:
                        record.record_reference = f"{record.model_name} - [Eliminado]"
                except Exception:
                    record.record_reference = f"{record.model_name} - ID {record.res_id}"
            else:
                record.record_reference = 'Sin referencia'
    
    # ============================================
    # ACCIONES
    # ============================================
    def action_open_record(self):
        """Abrir el registro que generó la notificación"""
        self.ensure_one()
        
        try:
            target_record = self.env[self.model_name].browse(self.res_id)
            if not target_record.exists():
                raise UserError(_('El registro ya no existe'))
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.model_name,
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            raise UserError(_('Error abriendo registro: %s') % str(e))
    
    def action_retry_send(self):
        """Reintentar envío de notificación fallida"""
        self.ensure_one()
        
        if self.state not in ['failed', 'cancelled']:
            raise UserError(_('Solo se pueden reintentar notificaciones fallidas o canceladas'))
        
        try:
            # Obtener registro original
            target_record = self.env[self.model_name].browse(self.res_id)
            if not target_record.exists():
                raise UserError(_('El registro original ya no existe'))
            
            # Obtener configuración
            config = self.config_id or self.env['whatsapp.config'].get_active_config()
            
            # Verificar conexión
            connection_status = config.check_connection(silent=True)
            if not connection_status.get('connected'):
                raise UserError(_('WhatsApp no está conectado'))
            
            # Marcar como enviando
            self.write({
                'state': 'sending',
                'retry_count': self.retry_count + 1,
                'error_message': False,
            })
            
            # Enviar mensaje
            result = config.send_message(self.recipient_phone, self.message_content)
            
            if result['success']:
                self.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'api_message_id': result.get('message_id'),
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': '✅ Mensaje reenviado exitosamente',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                self.write({
                    'state': 'failed',
                    'error_message': result.get('error', 'Error desconocido'),
                })
                
                raise UserError(_('Error reenviando mensaje: %s') % result.get('error'))
                
        except UserError:
            raise
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': str(e),
            })
            raise UserError(_('Error reenviando notificación: %s') % str(e))
    
    def action_cancel(self):
        """Cancelar notificación"""
        for record in self:
            if record.state in ['draft', 'sending']:
                record.state = 'cancelled'
    
    def action_set_to_draft(self):
        """Volver a borrador"""
        for record in self:
            if record.state in ['failed', 'cancelled']:
                record.write({
                    'state': 'draft',
                    'error_message': False,
                })