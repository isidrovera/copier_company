import hashlib
import hmac
import logging
import os
import re
import requests
from datetime import datetime
from odoo import http
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class CopierQuotation(models.Model):
    _inherit = 'copier.quotation'

    def _generate_secure_token(self, action):
        """Genera un token seguro para las acciones web"""
        secret_key = self.env['ir.config_parameter'].sudo().get_param(
            'copier_company.quotation_secret', 'copier_company_default_key_2025'
        )
        
        # Mensaje único basado en ID, usuario y acción
        message = f"{self.id}:{self.create_uid.id}:{action}:{self.write_date}"
        
        # Generar token HMAC
        token = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()[:16]  # Usar primeros 16 caracteres
        
        return token

    def _get_action_urls(self):
        """Genera las URLs de acción con tokens seguros"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        tokens = {
            'approve': self._generate_secure_token('approve'),
            'reject': self._generate_secure_token('reject'),
            'review': self._generate_secure_token('review')
        }
        
        urls = {
            'approve': f"{base_url}/quotation/approve/{self.id}/{self.create_uid.id}?token={tokens['approve']}",
            'reject': f"{base_url}/quotation/reject/{self.id}/{self.create_uid.id}?token={tokens['reject']}",
            'review': f"{base_url}/quotation/review/{self.id}/{self.create_uid.id}?token={tokens['review']}",
            'status': f"{base_url}/quotation/status/{self.id}"
        }
        
        return urls

    def _update_email_template_context(self):
        """Actualiza el contexto del template de email con URLs de acción"""
        urls = self._get_action_urls()
        
        # Agregar URLs al contexto del template
        ctx = self.env.context.copy()
        ctx.update({
            'action_urls': urls,
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        })
        
        return ctx

    def action_enviar_cotizacion(self):
        """Envía la cotización por email con botones de acción y por WhatsApp"""
        self.ensure_one()
        
        try:
            # Validaciones previas
            if not self.cliente_id:
                raise UserError("No se puede enviar la cotización sin un cliente asignado.")
            
            if not self.cliente_id.email:
                raise UserError(f"El cliente {self.cliente_id.name} no tiene email configurado.")
            
            if not self.linea_equipos_ids:
                raise UserError("No se puede enviar una cotización sin equipos.")
            
            if self.estado != 'borrador':
                raise UserError("Solo se pueden enviar cotizaciones en estado 'Borrador'.")
            
            # Generar URLs de acción
            urls = self._get_action_urls()
            
            # Buscar el template de email
            template = self.env.ref('copier_company.email_template_cotizacion_multiple', raise_if_not_found=False)
            if not template:
                raise UserError("No se encontró el template de email para cotizaciones múltiples.")
            
            # Preparar contexto con URLs
            email_ctx = self._update_email_template_context()
            
            # Enviar email con contexto actualizado
            template.with_context(email_ctx).send_mail(self.id, force_send=True)
            
            # Cambiar estado
            self.write({
                'estado': 'enviado'
            })
            
            # Registrar en el chatter
            self.message_post(
                body=f"""
                📧 <strong>Cotización Enviada por Email</strong><br/>
                • Destinatario: {self.cliente_id.email}<br/>
                • Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
                • Enlaces de acción generados<br/>
                • Estado cambiado a: Enviado
                """,
                message_type='notification'
            )
            
            # Enviar notificación por WhatsApp
            self._send_whatsapp_notification()
            
            # Crear actividad de seguimiento
            self._create_followup_activity()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Cotización Enviada',
                    'message': f'La cotización {self.name} ha sido enviada exitosamente a {self.cliente_id.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error enviando cotización {self.name}: {str(e)}")
            
            # Registrar error en chatter
            self.message_post(
                body=f"❌ <strong>Error al enviar cotización:</strong><br/>{str(e)}",
                message_type='notification'
            )
            
            raise UserError(f"Error al enviar la cotización: {str(e)}")

    def _send_whatsapp_notification(self):
        """Envía notificación por WhatsApp con PDF adjunto (basado en send_whatsapp_report que funciona)"""
        try:
            if not self.cliente_id or not self.cliente_id.mobile:
                self.message_post(
                    body=f"⚠️ <strong>WhatsApp no enviado:</strong><br/>El cliente <strong>{self.cliente_id.name if self.cliente_id else 'Sin cliente'}</strong> no tiene número de teléfono móvil configurado.",
                    message_type='notification'
                )
                _logger.info(f"Cliente {self.cliente_id.name if self.cliente_id else 'Sin cliente'} no tiene WhatsApp configurado")
                return

            # Obtener números formateados
            formatted_phones = self._get_formatted_phones()
            if not formatted_phones:
                _logger.warning(f"No se pudieron formatear los números de WhatsApp para {self.cliente_id.name}")
                return

            # Generar el PDF de la cotización
            try:
                report_action = self.env.ref('copier_company.action_report_copier_quotation')
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    report_action.id, self.ids
                )
            except Exception as e:
                _logger.error(f"Error generando PDF: {str(e)}")
                # Fallback: enviar solo texto si no se puede generar PDF
                self._send_whatsapp_text_only()
                return

            # Guardar PDF temporalmente
            filename = f"Cotizacion_Multiple_{self.name.replace('/', '_')}.pdf"
            temp_pdf_path = os.path.join('/tmp', filename)

            try:
                with open(temp_pdf_path, 'wb') as temp_pdf:
                    temp_pdf.write(pdf_content)

                _logger.info(f"PDF generado: {temp_pdf_path}, tamaño: {os.path.getsize(temp_pdf_path)} bytes")

                # URL de la API (misma que funciona)
                WHATSAPP_API_URL = 'https://whatsappapi.copiercompanysac.com/api/message'
                success_count = 0

                for phone in formatted_phones:
                    try:
                        # Crear mensaje corporativo similar al que funciona
                        message = f"""🎯 *Nueva Cotización Múltiple Disponible*

    ¡Hola! Le hemos enviado la cotización *{self.name}* con múltiples equipos.

    📋 *Resumen:*
    • {len(self.linea_equipos_ids)} equipo(s) cotizado(s)
    • Modalidad: {self.modalidad_pago_id.name}
    • Total: S/. {self.total_por_modalidad:,.2f}

    📧 *También enviamos por email* para que pueda responder con un solo clic.

    *¿Alguna consulta? ¡Estamos aquí para ayudarle!*

    *Copier Company SAC*
    📧 info@copiercompanysac.com
    🌐 https://copiercompanysac.com"""

                        with open(temp_pdf_path, 'rb') as pdf_file:
                            files = {
                                'file': (filename, pdf_file, 'application/pdf')
                            }
                            
                            # Usar mismo formato que funciona
                            data = {
                                'phone': phone,
                                'type': 'media',  # Cambio clave: usar 'media' no 'text'
                                'message': message
                            }

                            _logger.info("Enviando a WhatsApp API - Datos: %s", {**data, 'file': f'PDF_{filename}'})

                            response = requests.post(
                                WHATSAPP_API_URL,
                                data=data,
                                files=files,
                                timeout=30
                            )

                            _logger.info("Respuesta API: Status=%s, Contenido=%s", 
                                    response.status_code, response.text)

                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('success'):
                                        success_count += 1
                                        _logger.info(f"WhatsApp enviado exitosamente a {phone}")
                                    else:
                                        _logger.error(f"Error en API WhatsApp para {phone}: {response_data}")
                                except Exception as json_error:
                                    _logger.error(f"Error parseando JSON: {json_error}, Response: {response.text}")
                            else:
                                _logger.error(f"Error HTTP {response.status_code} enviando WhatsApp a {phone}: {response.text}")

                    except Exception as e:
                        _logger.error(f"Error al enviar WhatsApp a {phone}: {str(e)}")
                        self.message_post(
                            body=f"❌ Error al enviar WhatsApp al número {phone}: {str(e)}",
                            message_type='notification'
                        )

            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
                    _logger.info(f"Archivo temporal eliminado: {temp_pdf_path}")

            if success_count > 0:
                self.message_post(
                    body=f"📱 Cotización múltiple enviada por WhatsApp a {success_count} número(s) con PDF adjunto",
                    message_type='notification'
                )
            else:
                self.message_post(
                    body="❌ No se pudo enviar WhatsApp. Revise los logs para más detalles.",
                    message_type='notification'
                )

        except Exception as e:
            _logger.error(f"Error general en envío WhatsApp: {str(e)}")
            self.message_post(
                body=f"❌ <strong>Error enviando WhatsApp:</strong> {str(e)}",
                message_type='notification'
            )

    def _get_formatted_phones(self):
        """Obtiene y formatea los números de teléfono del cliente"""
        if not self.cliente_id.mobile:
            return []
            
        # Dividir números por punto y coma
        phones = self.cliente_id.mobile.split(';')
        formatted_phones = []
        
        for phone in phones:
            formatted = self._format_phone_number(phone)
            if formatted:
                formatted_phones.append(formatted)
                
        return formatted_phones

    def _format_phone_number(self, phone):
        """Formatea un número de teléfono para WhatsApp"""
        if not phone:
            return False
            
        # Limpiar el número
        phone = phone.strip().replace(' ', '').replace('+', '')
        phone = re.sub(r'[^0-9]', '', phone)
        
        # Si el número no empieza con '51' y tiene 9 dígitos, agregar '51'
        if not phone.startswith('51') and len(phone) == 9:
            phone = f'51{phone}'
        
        # Validar que el número tenga formato correcto
        if len(phone) >= 11 and phone.startswith('51'):
            return phone
        
        return False
    def _send_whatsapp_text_only(self):
        """Fallback: enviar solo texto si falla el PDF"""
        try:
            formatted_phones = self._get_formatted_phones()
            WHATSAPP_API_URL = 'https://whatsappapi.copiercompanysac.com/api/message'
            
            message = f"""🎯 *Cotización Múltiple {self.name}*

    📧 Hemos enviado su cotización por email con todos los detalles.

    📋 *Resumen:*
    • {len(self.linea_equipos_ids)} equipo(s)
    • Total: S/. {self.total_por_modalidad:,.2f}

    *Por favor revise su correo electrónico*

    *Copier Company SAC*"""

            success_count = 0
            for phone in formatted_phones:
                try:
                    data = {
                        'phone': phone,
                        'type': 'text',
                        'message': message
                    }
                    
                    response = requests.post(WHATSAPP_API_URL, data=data, timeout=30)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data.get('success'):
                            success_count += 1
                            
                except Exception as e:
                    _logger.error(f"Error fallback WhatsApp a {phone}: {str(e)}")

            if success_count > 0:
                self.message_post(
                    body=f"📱 Notificación WhatsApp enviada a {success_count} número(s) (solo texto)",
                    message_type='notification'
                )
                
        except Exception as e:
            _logger.error(f"Error en fallback WhatsApp: {str(e)}")

    def action_send_pdf_whatsapp(self):
        """Botón para enviar solo PDF por WhatsApp (sin email)"""
        self.ensure_one()
        
        if self.estado == 'borrador':
            raise UserError("No se puede enviar una cotización que aún está en borrador.")
        
        try:
            # Usar la misma función que funciona
            self._send_whatsapp_notification()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '📱 WhatsApp Enviado',
                    'message': f'PDF de cotización {self.name} enviado por WhatsApp',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(f"Error enviando WhatsApp: {str(e)}")
    def _create_followup_activity(self):
        """Crea una actividad de seguimiento para el vendedor"""
        try:
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            
            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': f'Seguimiento Cotización {self.name}',
                'note': f"""
                📋 Cotización enviada al cliente {self.cliente_id.name}
                
                📅 Fecha de envío: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                💰 Monto: S/. {self.total_por_modalidad:,.2f}
                📧 Email: {self.cliente_id.email}
                📱 WhatsApp: {'Enviado' if self.cliente_id.mobile else 'No disponible'}
                
                ⏰ Realizar seguimiento en 2-3 días si no hay respuesta.
                """,
                'user_id': self.create_uid.id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('copier.quotation').id,
                'date_deadline': fields.Date.today() + relativedelta(days=3)
            })
            
        except Exception as e:
            _logger.error(f"Error creando actividad de seguimiento: {str(e)}")

    def action_reenviar_cotizacion(self):
        """Reenvía una cotización ya enviada"""
        self.ensure_one()
        
        if self.estado not in ['enviado', 'aprobado', 'rechazado']:
            raise UserError("Solo se pueden reenviar cotizaciones que ya fueron enviadas anteriormente.")
        
        # Forzar reenvío
        original_estado = self.estado
        self.estado = 'borrador'
        
        try:
            result = self.action_enviar_cotizacion()
            
            # Registrar reenvío
            self.message_post(
                body=f"🔄 <strong>Cotización Reenviada</strong><br/>Estado anterior: {original_estado}",
                message_type='notification'
            )
            
            return result
            
        except Exception as e:
            # Restaurar estado original si falla
            self.estado = original_estado
            raise

    def action_test_whatsapp(self):
        """Método de prueba para WhatsApp (solo para desarrollo)"""
        if not self.env.user.has_group('base.group_system'):
            raise UserError("Solo administradores pueden usar esta función de prueba")
        
        self._send_whatsapp_notification()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Test WhatsApp',
                'message': 'Mensaje de prueba enviado. Revisa los logs.',
                'type': 'info',
            }
        }

    def action_generar_urls_debug(self):
        """Genera URLs de debug para pruebas (solo administradores)"""
        if not self.env.user.has_group('base.group_system'):
            raise UserError("Solo administradores pueden generar URLs de debug")
        
        urls = self._get_action_urls()
        
        message = f"""
        URLs generadas para cotización {self.name}:
        
        ✅ Aprobar: {urls['approve']}
        ❌ Rechazar: {urls['reject']}
        👁️ Revisar: {urls['review']}
        📊 Estado: {urls['status']}
        """
        
        self.message_post(body=message, message_type='notification')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'URLs Generadas',
                'message': 'URLs de debug agregadas al chatter de la cotización',
                'type': 'success',
            }
        }

class CopierWebsite(http.Controller):
    
    @http.route('/about-us', type='http', auth='public', website=True)
    def about_us(self):
        return http.request.render('copier_company.copier_about_us_page')