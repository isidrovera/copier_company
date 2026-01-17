# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppSendMultiQuotationWizard(models.TransientModel):
    _name = 'whatsapp.send.multi.quotation.wizard'
    _description = 'Wizard para Enviar Cotizaciones Multi-Equipo por WhatsApp'

    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    quotation_ids = fields.Many2many(
        'copier.quotation',
        string='Cotizaciones Multi-Equipo',
        required=True,
        help='Cotizaciones multi-equipo a enviar por WhatsApp'
    )
    
    phone_line_ids = fields.One2many(
        'whatsapp.quotation.phone.line',
        'wizard_id',
        string='Números de Teléfono',
        help='Lista de números a los que se enviará la cotización'
    )
    
    message = fields.Text(
        string='Mensaje',
        required=True,
        help='Mensaje que acompañará la cotización. Usa variables como {secuencia}, {cliente}, etc.'
    )
    
    preview_html = fields.Html(
        string='Vista Previa',
        compute='_compute_preview_html',
        sanitize=False,
        help='Vista previa del mensaje con las variables reemplazadas'
    )
    
    attach_pdf = fields.Boolean(
        string='Adjuntar PDF',
        default=True,
        help='Adjuntar el PDF de la cotización al mensaje'
    )
    
    config_id = fields.Many2one(
        'whatsapp.config',
        string='Configuración WhatsApp',
        required=True,
        default=lambda self: self.env['whatsapp.config'].get_active_config(),
        help='Configuración de WhatsApp a utilizar'
    )
    
    # Campos informativos
    total_phones = fields.Integer(
        string='Total Números',
        compute='_compute_totals',
        store=False
    )
    
    valid_phones = fields.Integer(
        string='Números Válidos',
        compute='_compute_totals',
        store=False
    )
    
    message_length = fields.Integer(
        string='Caracteres',
        compute='_compute_message_length',
        store=False
    )
    
    # ============================================
    # COMPUTE METHODS
    # ============================================
    @api.depends('phone_line_ids', 'phone_line_ids.is_valid')
    def _compute_totals(self):
        """Calcular totales de números"""
        for wizard in self:
            wizard.total_phones = len(wizard.phone_line_ids)
            wizard.valid_phones = len(wizard.phone_line_ids.filtered('is_valid'))
    
    @api.depends('message')
    def _compute_message_length(self):
        """Calcular longitud del mensaje"""
        for wizard in self:
            wizard.message_length = len(wizard.message or '')
    
    @api.depends('message', 'quotation_ids')
    def _compute_preview_html(self):
        """Generar vista previa del mensaje con variables reemplazadas"""
        for wizard in self:
            if not wizard.message or not wizard.quotation_ids:
                wizard.preview_html = '<p style="color: #999;">No hay mensaje o cotizaciones seleccionadas</p>'
                continue
            
            # Tomar la primera cotización para el preview
            quotation = wizard.quotation_ids[0]
            
            try:
                # Reemplazar variables
                preview_text = wizard._process_message_variables(wizard.message, quotation)
                
                # Convertir a HTML (negrita para WhatsApp)
                preview_html = preview_text.replace('*', '<strong>').replace('*', '</strong>')
                preview_html = preview_html.replace('\n', '<br/>')
                
                wizard.preview_html = f'''
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-family: Arial, sans-serif;">
                        <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #25D366;">
                            {preview_html}
                        </div>
                        <div style="margin-top: 10px; color: #666; font-size: 11px;">
                            <i class="fa fa-info-circle"/> Vista previa basada en: {quotation.name}
                            {f' (y {len(wizard.quotation_ids) - 1} más)' if len(wizard.quotation_ids) > 1 else ''}
                        </div>
                    </div>
                '''
            except Exception as e:
                wizard.preview_html = f'<p style="color: red;">Error en vista previa: {str(e)}</p>'
    
    # ============================================
    # DEFAULT VALUES
    # ============================================
    @api.model
    def default_get(self, fields_list):
        """Cargar valores por defecto"""
        res = super().default_get(fields_list)
        
        # Mensaje por defecto
        if 'message' in fields_list:
            res['message'] = self._get_default_message()
        
        # Cargar números de teléfono si hay cotizaciones en contexto
        if 'phone_line_ids' in fields_list:
            quotation_ids = self.env.context.get('default_quotation_ids')
            if quotation_ids and isinstance(quotation_ids, list) and quotation_ids[0][2]:
                phone_lines = self._prepare_phone_lines(quotation_ids[0][2])
                res['phone_line_ids'] = phone_lines
        
        return res
    
    def _get_default_message(self):
        """Mensaje por defecto para cotizaciones multi-equipo"""
        return """¡Gracias por confiar en Copier Company!

Te enviamos la *Cotización {secuencia}* solicitada.

📋 *Resumen:*
- Cliente: {cliente}
- Equipos cotizados: {cantidad_equipos} equipo(s)
- Modalidad de pago: {modalidad_pago}
- Total mensual: {total_mensual}
- Total por modalidad: {total_por_modalidad}

Por favor, revisa el documento adjunto con el detalle completo de los equipos y condiciones.

*Validez de la oferta:* {validez_dias} días
*Fecha de vencimiento:* {fecha_vencimiento}

Si tienes alguna consulta o requieres información adicional, estaremos encantados de ayudarte.

*Saludos cordiales,*
Equipo Copier Company

📧 info@copiercompanysac.com
🌐 https://copiercompanysac.com"""
    
    def _prepare_phone_lines(self, quotation_ids):
        """Preparar líneas de teléfono desde cotizaciones multi-equipo"""
        phone_lines = []
        seen_phones = set()
        
        quotations = self.env['copier.quotation'].browse(quotation_ids)
        
        for quotation in quotations:
            # Obtener número usando el método del modelo
            phone_source = quotation.get_whatsapp_phone()
            
            if not phone_source:
                _logger.warning(f"No se encontró número de teléfono para {quotation.name}")
                continue
            
            # Dividir números por punto y coma
            phones = str(phone_source).split(';')
            
            for phone in phones:
                phone = phone.strip()
                if not phone or phone in seen_phones:
                    continue
                
                seen_phones.add(phone)
                
                phone_lines.append((0, 0, {
                    'phone': phone,
                    'partner_name': quotation.cliente_id.name if quotation.cliente_id else '',
                    'copier_reference': quotation.name,
                }))
        
        return phone_lines
    
    # ============================================
    # HELPER METHODS
    # ============================================
    def _process_message_variables(self, message, quotation):
        """
        Reemplazar variables en el mensaje con valores reales
        
        Args:
            message (str): Mensaje con variables
            quotation (copier.quotation): Registro de cotización multi-equipo
            
        Returns:
            str: Mensaje con variables reemplazadas
        """
        try:
            return message.format(
                secuencia=quotation.name or '',
                cliente=quotation.cliente_id.name or '',
                contacto=quotation.contacto or '',
                telefono=quotation.telefono or '',
                email=quotation.email or '',
                direccion=quotation.direccion or '',
                sede=quotation.sede or '',
                cantidad_equipos=len(quotation.linea_equipos_ids),
                modalidad_pago=quotation.modalidad_pago_id.name if quotation.modalidad_pago_id else '',
                total_mensual=f"{quotation.currency_id.symbol} {quotation.total_mensual:,.2f}",
                total_por_modalidad=f"{quotation.currency_id.symbol} {quotation.total_por_modalidad:,.2f}",
                subtotal=f"{quotation.currency_id.symbol} {quotation.subtotal_final:,.2f}",
                validez_dias=quotation.validez_dias or 30,
                fecha_vencimiento=quotation.fecha_vencimiento.strftime('%d/%m/%Y') if quotation.fecha_vencimiento else '',
                fecha_cotizacion=quotation.fecha_cotizacion.strftime('%d/%m/%Y') if quotation.fecha_cotizacion else '',
                empresa=self.env.company.name or 'Copier Company',
                total=f"{quotation.currency_id.symbol} {quotation.total_por_modalidad:,.2f}",
                ubicacion=quotation.direccion or '',
            )
        except KeyError as e:
            raise ValidationError(_(
                'Variable no reconocida en el mensaje: %s\n\n'
                'Variables disponibles:\n'
                '{secuencia}, {cliente}, {contacto}, {telefono}, {email}, '
                '{direccion}, {sede}, {cantidad_equipos}, {modalidad_pago}, '
                '{total_mensual}, {total_por_modalidad}, {subtotal}, '
                '{validez_dias}, {fecha_vencimiento}, {fecha_cotizacion}, '
                '{empresa}, {total}, {ubicacion}'
            ) % str(e))
    
    def _generate_pdf(self, quotation):
        """
        Generar PDF de cotización multi-equipo
        
        Args:
            quotation (copier.quotation): Registro de cotización
            
        Returns:
            tuple: (pdf_content, filename)
        """
        try:
            report_action = self.env.ref('copier_company.action_report_copier_quotation')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.id, quotation.ids
            )
            
            # Generar nombre del archivo
            filename = f"Cotizacion_Multiple_{quotation.name.replace('/', '_')}.pdf"
            
            return pdf_content, filename
        except Exception as e:
            _logger.error(f"Error generando PDF para {quotation.name}: {str(e)}")
            raise UserError(_(f'Error al generar PDF para {quotation.name}: {str(e)}'))
    
    # ============================================
    # ACCIONES
    # ============================================
    def action_verify_numbers(self):
        """Verificar que los números existan en WhatsApp"""
        self.ensure_one()
        
        if not self.phone_line_ids:
            raise UserError('No hay números de teléfono para verificar.')
        
        verified_count = 0
        invalid_count = 0
        
        for line in self.phone_line_ids:
            if line.phone_clean:
                exists = self.config_id.verify_number(line.phone_clean)
                line.is_verified = True
                line.verification_result = 'Existe ✓' if exists else 'No existe ✗'
                
                if exists:
                    verified_count += 1
                else:
                    invalid_count += 1
        
        message = f'✅ Verificación completada:\n'
        message += f'• {verified_count} números válidos\n'
        if invalid_count > 0:
            message += f'• {invalid_count} números no encontrados en WhatsApp'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Verificación de Números',
                'message': message,
                'type': 'success' if invalid_count == 0 else 'warning',
                'sticky': False,
            }
        }
    
    def action_send_quotations(self):
        """Enviar cotizaciones multi-equipo por WhatsApp"""
        self.ensure_one()
        
        # Validaciones
        if not self.phone_line_ids:
            raise UserError('Debe agregar al menos un número de teléfono.')
        
        if not self.quotation_ids:
            raise UserError('No hay cotizaciones seleccionadas.')
        
        valid_phones = self.phone_line_ids.filtered('is_valid')
        if not valid_phones:
            raise UserError('No hay números de teléfono válidos.')
        
        # Confirmar conexión
        connection_status = self.config_id.check_connection(silent=True)
        if not connection_status.get('connected'):
            raise UserError(_(
                'WhatsApp no está conectado.\n\n'
                'Por favor, verifica la conexión en:\n'
                'Ajustes → WhatsApp API Config\n\n'
                'Error: %s'
            ) % connection_status.get('message', 'Desconocido'))
        
        # Contadores
        total_sent = 0
        total_failed = 0
        results = []
        
        # Procesar cada cotización
        for quotation in self.quotation_ids:
            _logger.info(f"📤 Procesando cotización {quotation.name}")
            
            # Generar PDF si está marcado
            pdf_content = None
            pdf_filename = None
            
            if self.attach_pdf:
                try:
                    pdf_content, pdf_filename = self._generate_pdf(quotation)
                    _logger.info(f"✅ PDF generado para {quotation.name}: {pdf_filename} ({len(pdf_content)} bytes)")
                except Exception as e:
                    _logger.error(f"❌ Error generando PDF para {quotation.name}: {str(e)}")
                    results.append({
                        'quotation': quotation.name,
                        'status': 'error',
                        'message': f'Error generando PDF: {str(e)}'
                    })
                    total_failed += 1
                    continue
            
            # Procesar mensaje
            try:
                processed_message = self._process_message_variables(self.message, quotation)
            except Exception as e:
                _logger.error(f"❌ Error procesando variables para {quotation.name}: {str(e)}")
                results.append({
                    'quotation': quotation.name,
                    'status': 'error',
                    'message': f'Error en variables: {str(e)}'
                })
                total_failed += 1
                continue
            
            # Enviar a cada número válido
            for phone_line in valid_phones:
                try:
                    _logger.info(f"📱 Enviando a {phone_line.phone_clean}")
                    
                    # Enviar según si hay PDF o no
                    if pdf_content and self.attach_pdf and pdf_filename:
                        result = self.config_id.send_media(
                            phone=phone_line.phone_clean,
                            file_data=pdf_content,
                            media_type='document',
                            caption=processed_message,
                            filename=pdf_filename
                        )
                    else:
                        result = self.config_id.send_message(
                            phone=phone_line.phone_clean,
                            message=processed_message
                        )
                    
                    if result.get('success'):
                        total_sent += 1
                        _logger.info(f"✅ Enviado a {phone_line.phone}")
                        
                        # Registrar en chatter
                        quotation.message_post(
                            body=f"""✅ Cotización enviada por WhatsApp
                            
📱 Número: {phone_line.phone}
👤 Contacto: {phone_line.partner_name}
📄 Con PDF: {'Sí' if self.attach_pdf else 'No'}
🆔 Message ID: {result.get('message_id', 'N/A')}""",
                            message_type='notification'
                        )
                        
                        results.append({
                            'quotation': quotation.name,
                            'phone': phone_line.phone,
                            'status': 'success',
                            'message': 'Enviado exitosamente'
                        })
                    else:
                        total_failed += 1
                        error_msg = result.get('error', 'Error desconocido')
                        _logger.error(f"❌ Error enviando a {phone_line.phone}: {error_msg}")
                        
                        quotation.message_post(
                            body=f"""❌ Error enviando WhatsApp
                            
📱 Número: {phone_line.phone}
⚠️ Error: {error_msg}""",
                            message_type='notification'
                        )
                        
                        results.append({
                            'quotation': quotation.name,
                            'phone': phone_line.phone,
                            'status': 'error',
                            'message': error_msg
                        })
                
                except Exception as e:
                    total_failed += 1
                    _logger.exception(f"❌ Excepción enviando a {phone_line.phone}")
                    
                    results.append({
                        'quotation': quotation.name,
                        'phone': phone_line.phone,
                        'status': 'error',
                        'message': str(e)
                    })
        
        # Mensaje final
        if total_sent > 0 and total_failed == 0:
            notification_type = 'success'
            title = '✅ Envío Exitoso'
            message = f'Se enviaron {total_sent} mensaje(s) correctamente.'
        elif total_sent > 0 and total_failed > 0:
            notification_type = 'warning'
            title = '⚠️ Envío Parcial'
            message = f'Enviados: {total_sent} | Fallidos: {total_failed}'
        else:
            notification_type = 'danger'
            title = '❌ Error en Envío'
            message = f'No se pudo enviar ningún mensaje. Fallidos: {total_failed}'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': True,
            }
        }