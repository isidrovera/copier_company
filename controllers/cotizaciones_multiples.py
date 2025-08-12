import hashlib
import hmac
import logging
from datetime import datetime, timedelta

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)

class QuotationWebController(http.Controller):
    """Controlador web para manejar acciones de cotización desde email"""

    def _generate_token(self, quotation_id, user_id, action):
        """Genera un token seguro para la acción"""
        secret_key = request.env['ir.config_parameter'].sudo().get_param(
            'copier_company.quotation_secret', 'default_secret_key'
        )
        message = f"{quotation_id}:{user_id}:{action}"
        return hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()[:16]  # Usar solo primeros 16 caracteres

    def _validate_token(self, quotation_id, user_id, action, token):
        """Valida el token de seguridad"""
        expected_token = self._generate_token(quotation_id, user_id, action)
        return hmac.compare_digest(expected_token, token)

    def _validate_quotation_access(self, quotation_id, user_id):
        """Valida acceso a la cotización y retorna el registro"""
        try:
            quotation = request.env['copier.quotation'].sudo().browse(quotation_id)
            
            if not quotation.exists():
                raise ValidationError("Cotización no encontrada")
            
            # Verificar que la cotización esté en estado válido
            if quotation.estado not in ['borrador', 'enviado']:
                raise ValidationError("Esta cotización ya fue procesada anteriormente")
            
            # Verificar que no haya vencido
            if quotation.fecha_vencimiento and quotation.fecha_vencimiento < datetime.now().date():
                raise ValidationError("Esta cotización ha vencido")
                
            # Verificar que el usuario tenga acceso
            if quotation.create_uid.id != user_id:
                raise ValidationError("No tiene permisos para acceder a esta cotización")
                
            return quotation
            
        except Exception as e:
            _logger.error(f"Error validando acceso a cotización {quotation_id}: {str(e)}")
            raise ValidationError(f"Error de acceso: {str(e)}")

    def _log_quotation_action(self, quotation, action, details=None):
        """Registra la acción en el chatter de la cotización"""
        try:
            message = f"🌐 Acción web: {action}"
            if details:
                message += f"\n{details}"
            
            quotation.message_post(
                body=message,
                message_type='notification',
                author_id=request.env.user.id
            )
        except Exception as e:
            _logger.error(f"Error registrando acción: {str(e)}")

    def _send_internal_notification(self, quotation, action, details=None):
        """Envía notificación interna al equipo comercial"""
        try:
            # Crear actividad para el vendedor
            activity_type = request.env.ref('mail.mail_activity_data_todo')
            
            summary_map = {
                'approved': f'✅ Cotización {quotation.name} APROBADA',
                'rejected': f'❌ Cotización {quotation.name} RECHAZADA',
                'review': f'👁️ Cotización {quotation.name} requiere REVISIÓN'
            }
            
            note = f"""
            El cliente {quotation.cliente_id.name} ha respondido a la cotización {quotation.name}:
            
            Acción: {action.upper()}
            Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            {details or ''}
            
            Por favor, realizar el seguimiento correspondiente.
            """
            
            request.env['mail.activity'].sudo().create({
                'activity_type_id': activity_type.id,
                'summary': summary_map.get(action, f'Acción en cotización {quotation.name}'),
                'note': note,
                'user_id': quotation.create_uid.id,
                'res_id': quotation.id,
                'res_model_id': request.env['ir.model']._get('copier.quotation').id,
                'date_deadline': datetime.now().date() + timedelta(days=1)
            })
            
        except Exception as e:
            _logger.error(f"Error enviando notificación interna: {str(e)}")

    def _send_whatsapp_confirmation(self, quotation, action):
        """Envía confirmación por WhatsApp al cliente"""
        try:
            if not quotation.cliente_id.mobile:
                return
                
            messages = {
                'approved': f"✅ ¡Excelente! Hemos recibido la aprobación de su cotización {quotation.name}. Nuestro equipo se contactará pronto para coordinar la entrega.",
                'rejected': f"📝 Hemos recibido su respuesta sobre la cotización {quotation.name}. Nuestro equipo comercial se contactará para atender sus observaciones.",
                'review': f"👁️ Hemos recibido su solicitud de revisión para la cotización {quotation.name}. Nuestro equipo se contactará pronto para coordinar los ajustes."
            }
            
            message = messages.get(action, "Gracias por su respuesta a nuestra cotización.")
            
            # Usar la función existente de WhatsApp si está disponible
            whatsapp_url = request.env['ir.config_parameter'].sudo().get_param(
                'copier_company.whatsapp_api_url', 
                'https://whatsappapi.copiercompanysac.com/api/message'
            )
            
            # Aquí iría la integración con WhatsApp
            # Por ahora solo logueamos
            _logger.info(f"WhatsApp a enviar: {message}")
            
        except Exception as e:
            _logger.error(f"Error enviando WhatsApp: {str(e)}")

    @http.route('/quotation/approve/<int:quotation_id>/<int:user_id>', type='http', auth="public", website=True)
    def approve_quotation(self, quotation_id, user_id, token=None, **kwargs):
        """Aprueba una cotización"""
        try:
            # Generar token si no se proporciona (para compatibilidad)
            if not token:
                token = self._generate_token(quotation_id, user_id, 'approve')
            
            # Validar acceso
            quotation = self._validate_quotation_access(quotation_id, user_id)
            
            # Aprobar cotización
            quotation.sudo().write({
                'estado': 'aprobado'
            })
            
            # Registrar acción
            self._log_quotation_action(quotation, 'Aprobación vía web')
            
            # Notificaciones
            self._send_internal_notification(quotation, 'approved')
            self._send_whatsapp_confirmation(quotation, 'approved')
            
            # Renderizar página de éxito
            return request.render('copier_company.quotation_approved_template', {
                'quotation': quotation,
                'success': True,
                'message': 'Su cotización ha sido aprobada exitosamente'
            })
            
        except Exception as e:
            _logger.error(f"Error aprobando cotización: {str(e)}")
            return request.render('copier_company.quotation_error_template', {
                'error': str(e),
                'quotation_id': quotation_id
            })

    @http.route('/quotation/reject/<int:quotation_id>/<int:user_id>', type='http', auth="public", website=True, methods=['GET', 'POST'])
    def reject_quotation(self, quotation_id, user_id, token=None, **kwargs):
        """Rechaza una cotización"""
        try:
            # Generar token si no se proporciona
            if not token:
                token = self._generate_token(quotation_id, user_id, 'reject')
            
            # Validar acceso
            quotation = self._validate_quotation_access(quotation_id, user_id)
            
            if request.httprequest.method == 'GET':
                # Mostrar formulario de rechazo
                return request.render('copier_company.quotation_reject_form_template', {
                    'quotation': quotation,
                    'quotation_id': quotation_id,
                    'user_id': user_id,
                    'token': token
                })
            
            elif request.httprequest.method == 'POST':
                # Procesar rechazo
                motivo = kwargs.get('motivo', '').strip()
                
                if not motivo:
                    raise ValidationError("El motivo del rechazo es obligatorio")
                
                if len(motivo) < 10:
                    raise ValidationError("Por favor, proporcione un motivo más detallado (mínimo 10 caracteres)")
                
                # Actualizar cotización
                quotation.sudo().write({
                    'estado': 'rechazado'
                })
                
                # Registrar acción con motivo
                details = f"Motivo del rechazo:\n{motivo}"
                self._log_quotation_action(quotation, 'Rechazo vía web', details)
                
                # Notificaciones
                self._send_internal_notification(quotation, 'rejected', f"Motivo: {motivo}")
                self._send_whatsapp_confirmation(quotation, 'rejected')
                
                # Renderizar página de confirmación
                return request.render('copier_company.quotation_rejected_template', {
                    'quotation': quotation,
                    'success': True,
                    'message': 'Su respuesta ha sido registrada. Nos contactaremos pronto.'
                })
                
        except Exception as e:
            _logger.error(f"Error rechazando cotización: {str(e)}")
            return request.render('copier_company.quotation_error_template', {
                'error': str(e),
                'quotation_id': quotation_id
            })

    @http.route('/quotation/review/<int:quotation_id>/<int:user_id>', type='http', auth="public", website=True, methods=['GET', 'POST'])
    def review_quotation(self, quotation_id, user_id, token=None, **kwargs):
        """Solicita revisión de una cotización"""
        try:
            # Generar token si no se proporciona
            if not token:
                token = self._generate_token(quotation_id, user_id, 'review')
            
            # Validar acceso
            quotation = self._validate_quotation_access(quotation_id, user_id)
            
            if request.httprequest.method == 'GET':
                # Mostrar formulario de revisión
                return request.render('copier_company.quotation_review_form_template', {
                    'quotation': quotation,
                    'quotation_id': quotation_id,
                    'user_id': user_id,
                    'token': token
                })
            
            elif request.httprequest.method == 'POST':
                # Procesar solicitud de revisión
                comentarios = kwargs.get('comentarios', '').strip()
                cambios_solicitados = kwargs.get('cambios_solicitados', '').strip()
                telefono_contacto = kwargs.get('telefono_contacto', '').strip()
                
                if not comentarios and not cambios_solicitados:
                    raise ValidationError("Por favor, indique qué aspectos desea revisar o modificar")
                
                # Mantener estado como 'enviado' para permitir nuevas modificaciones
                details = f"""
                Comentarios: {comentarios}
                Cambios solicitados: {cambios_solicitados}
                Teléfono de contacto: {telefono_contacto}
                """
                
                # Registrar acción
                self._log_quotation_action(quotation, 'Solicitud de revisión vía web', details)
                
                # Notificaciones
                self._send_internal_notification(quotation, 'review', details)
                self._send_whatsapp_confirmation(quotation, 'review')
                
                # Renderizar página de confirmación
                return request.render('copier_company.quotation_review_received_template', {
                    'quotation': quotation,
                    'success': True,
                    'message': 'Su solicitud de revisión ha sido recibida. Nos contactaremos pronto.'
                })
                
        except Exception as e:
            _logger.error(f"Error procesando revisión: {str(e)}")
            return request.render('copier_company.quotation_error_template', {
                'error': str(e),
                'quotation_id': quotation_id
            })

    @http.route('/quotation/status/<int:quotation_id>', type='http', auth="public", website=True)
    def quotation_status(self, quotation_id, **kwargs):
        """Muestra el estado actual de una cotización"""
        try:
            quotation = request.env['copier.quotation'].sudo().browse(quotation_id)
            
            if not quotation.exists():
                raise ValidationError("Cotización no encontrada")
            
            return request.render('copier_company.quotation_status_template', {
                'quotation': quotation
            })
            
        except Exception as e:
            return request.render('copier_company.quotation_error_template', {
                'error': str(e),
                'quotation_id': quotation_id
            })

    @http.route('/quotation/generate_tokens', type='http', auth="user", website=False)
    def generate_tokens_for_testing(self, **kwargs):
        """Método de desarrollo para generar tokens de prueba"""
        if not request.env.user.has_group('base.group_system'):
            return "No autorizado"
        
        quotation_id = int(kwargs.get('quotation_id', 1))
        user_id = int(kwargs.get('user_id', 1))
        
        tokens = {
            'approve': self._generate_token(quotation_id, user_id, 'approve'),
            'reject': self._generate_token(quotation_id, user_id, 'reject'),
            'review': self._generate_token(quotation_id, user_id, 'review')
        }
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        urls = {
            'approve': f"{base_url}/quotation/approve/{quotation_id}/{user_id}?token={tokens['approve']}",
            'reject': f"{base_url}/quotation/reject/{quotation_id}/{user_id}?token={tokens['reject']}",
            'review': f"{base_url}/quotation/review/{quotation_id}/{user_id}?token={tokens['review']}"
        }
        
        return f"""
        <h3>URLs de prueba para cotización {quotation_id}:</h3>
        <p><a href="{urls['approve']}">Aprobar</a></p>
        <p><a href="{urls['reject']}">Rechazar</a></p>
        <p><a href="{urls['review']}">Revisar</a></p>
        """