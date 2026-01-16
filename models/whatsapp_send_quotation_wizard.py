# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppSendQuotationWizard(models.TransientModel):
    _name = 'whatsapp.send.quotation.wizard'
    _description = 'Wizard para Enviar Cotizaciones por WhatsApp'

    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    copier_company_ids = fields.Many2many(
        'copier.company',
        string='Cotizaciones',
        required=True,
        help='Cotizaciones a enviar por WhatsApp'
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
    
    @api.depends('message', 'copier_company_ids')
    def _compute_preview_html(self):
        """Generar vista previa del mensaje con variables reemplazadas"""
        for wizard in self:
            if not wizard.message or not wizard.copier_company_ids:
                wizard.preview_html = '<p style="color: #999;">No hay mensaje o cotizaciones seleccionadas</p>'
                continue
            
            # Tomar la primera cotización para el preview
            copier = wizard.copier_company_ids[0]
            
            try:
                # Reemplazar variables
                preview_text = wizard._process_message_variables(wizard.message, copier)
                
                # Convertir a HTML (negrita para WhatsApp)
                preview_html = preview_text.replace('*', '<strong>').replace('*', '</strong>')
                preview_html = preview_html.replace('\n', '<br/>')
                
                wizard.preview_html = f'''
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-family: Arial, sans-serif;">
                        <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #25D366;">
                            {preview_html}
                        </div>
                        <div style="margin-top: 10px; color: #666; font-size: 11px;">
                            <i class="fa fa-info-circle"/> Vista previa basada en: {copier.secuencia}
                            {f' (y {len(wizard.copier_company_ids) - 1} más)' if len(wizard.copier_company_ids) > 1 else ''}
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
            copier_ids = self.env.context.get('default_copier_company_ids')
            if copier_ids and isinstance(copier_ids, list) and copier_ids[0][2]:
                phone_lines = self._prepare_phone_lines(copier_ids[0][2])
                res['phone_line_ids'] = phone_lines
        
        return res
    
    def _get_default_message(self):
        """Mensaje por defecto para cotizaciones"""
        return """¡Gracias por confiar en Copier Company!

Te enviamos la *Propuesta Comercial {secuencia}* solicitada.

📋 *Detalles:*
- Cliente: {cliente}
- Máquina: {maquina} - {marca}
- Total: {total}

Por favor, revisa el documento adjunto. Si tienes alguna consulta o requieres información adicional, estaremos encantados de ayudarte.

*Saludos cordiales,*
Equipo Copier Company

📧 info@copiercompanysac.com
🌐 https://copiercompanysac.com"""
    
    def _prepare_phone_lines(self, copier_ids):
        """Preparar líneas de teléfono desde las cotizaciones"""
        phone_lines = []
        seen_phones = set()
        
        copiers = self.env['copier.company'].browse(copier_ids)
        
        for copier in copiers:
            if not copier.cliente_id:
                continue
            
            # Intentar obtener números de diferentes campos posibles
            phone_numbers = []
            
            # 1. Primero intentar el campo 'celular' de copier.company
            if hasattr(copier, 'celular') and copier.celular:
                phone_numbers.append(copier.celular)
            
            # 2. Luego intentar campos del partner
            partner = copier.cliente_id
            
            # Intentar mobile (si existe)
            if hasattr(partner, 'mobile') and partner.mobile:
                phone_numbers.append(partner.mobile)
            
            # Intentar phone
            if hasattr(partner, 'phone') and partner.phone:
                phone_numbers.append(partner.phone)
            
            # Si no hay números, continuar con el siguiente
            if not phone_numbers:
                _logger.warning(f"No se encontraron números para la cotización {copier.secuencia}")
                continue
            
            # Procesar cada número encontrado
            for phone_field in phone_numbers:
                # Dividir números por punto y coma
                phones = str(phone_field).split(';')
                
                for phone in phones:
                    phone = phone.strip()
                    if not phone or phone in seen_phones:
                        continue
                    
                    seen_phones.add(phone)
                    
                    phone_lines.append((0, 0, {
                        'phone': phone,
                        'partner_name': copier.cliente_id.name,
                        'copier_reference': copier.secuencia,
                    }))
        
        return phone_lines
    
    # ============================================
    # HELPER METHODS
    # ============================================
    def _process_message_variables(self, message, copier):
        """
        Reemplazar variables en el mensaje con valores reales
        
        Args:
            message (str): Mensaje con variables
            copier (copier.company): Registro de cotización
            
        Returns:
            str: Mensaje con variables reemplazadas
        """
        try:
            return message.format(
                secuencia=copier.secuencia or '',
                cliente=copier.cliente_id.name or '',
                contacto=copier.contacto or '',
                maquina=copier.name.name if copier.name else '',
                marca=copier.marca_id.name if copier.marca_id else '',
                serie=copier.serie_id or '',
                total=f"{copier.currency_id.symbol} {copier.total_facturar_mensual:,.2f}",
                subtotal=f"{copier.currency_id.symbol} {copier.subtotal_sin_igv:,.2f}",
                fecha=copier.fecha_formateada or '',
                empresa=self.env.company.name or 'Copier Company',
                ubicacion=copier.ubicacion or '',
                volumen_bn=f"{copier.volumen_mensual_bn:,}" if copier.volumen_mensual_bn else '0',
                volumen_color=f"{copier.volumen_mensual_color:,}" if copier.volumen_mensual_color else '0',
                costo_bn=copier.get_label_costo_bn() if hasattr(copier, 'get_label_costo_bn') else '',
                costo_color=copier.get_label_costo_color() if hasattr(copier, 'get_label_costo_color') else '',
            )
        except KeyError as e:
            raise ValidationError(_(
                'Variable no reconocida en el mensaje: %s\n\n'
                'Variables disponibles:\n'
                '{secuencia}, {cliente}, {contacto}, {maquina}, {marca}, '
                '{serie}, {total}, {subtotal}, {fecha}, {empresa}, '
                '{ubicacion}, {volumen_bn}, {volumen_color}, {costo_bn}, {costo_color}'
            ) % str(e))
    
    def _generate_pdf(self, copier):
        """
        Generar PDF de cotización
        
        Args:
            copier (copier.company): Registro de cotización
            
        Returns:
            tuple: (pdf_content, filename)
        """
        try:
            report_action = self.env.ref('copier_company.action_report_report_cotizacion_alquiler')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.id, copier.ids
            )
            
            # Generar el mismo nombre que en send_whatsapp_report original
            filename = f"Propuesta_Comercial_{copier.secuencia}.pdf"
            
            return pdf_content, filename
        except Exception as e:
            _logger.error(f"Error generando PDF para {copier.secuencia}: {str(e)}")
            raise UserError(_(f'Error al generar PDF para {copier.secuencia}: {str(e)}'))
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
        """Enviar cotizaciones por WhatsApp"""
        self.ensure_one()
        
        # Validaciones
        if not self.phone_line_ids:
            raise UserError('Debe agregar al menos un número de teléfono.')
        
        if not self.copier_company_ids:
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
        for copier in self.copier_company_ids:
            _logger.info(f"📤 Procesando cotización {copier.secuencia}")
            
            # Generar PDF si está marcado
            pdf_content = None
            pdf_filename = None  # ⭐ INICIALIZAR SIEMPRE
            
            if self.attach_pdf:
                try:
                    pdf_content, pdf_filename = self._generate_pdf(copier)
                    _logger.info(f"✅ PDF generado para {copier.secuencia}: {pdf_filename} ({len(pdf_content)} bytes)")
                except Exception as e:
                    _logger.error(f"❌ Error generando PDF para {copier.secuencia}: {str(e)}")
                    results.append({
                        'copier': copier.secuencia,
                        'status': 'error',
                        'message': f'Error generando PDF: {str(e)}'
                    })
                    total_failed += 1
                    continue
            
            # Procesar mensaje
            try:
                processed_message = self._process_message_variables(self.message, copier)
            except Exception as e:
                _logger.error(f"❌ Error procesando variables para {copier.secuencia}: {str(e)}")
                results.append({
                    'copier': copier.secuencia,
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
                    if pdf_content and self.attach_pdf and pdf_filename:  # ⭐ VERIFICAR que pdf_filename existe
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
                        copier.message_post(
                            body=f"""✅ Cotización enviada por WhatsApp
                            
📱 Número: {phone_line.phone}
👤 Contacto: {phone_line.partner_name}
📄 Con PDF: {'Sí' if self.attach_pdf else 'No'}
🆔 Message ID: {result.get('message_id', 'N/A')}""",
                            message_type='notification'
                        )
                        
                        results.append({
                            'copier': copier.secuencia,
                            'phone': phone_line.phone,
                            'status': 'success',
                            'message': 'Enviado exitosamente'
                        })
                    else:
                        total_failed += 1
                        error_msg = result.get('error', 'Error desconocido')
                        _logger.error(f"❌ Error enviando a {phone_line.phone}: {error_msg}")
                        
                        copier.message_post(
                            body=f"""❌ Error enviando WhatsApp
                            
📱 Número: {phone_line.phone}
⚠️ Error: {error_msg}""",
                            message_type='notification'
                        )
                        
                        results.append({
                            'copier': copier.secuencia,
                            'phone': phone_line.phone,
                            'status': 'error',
                            'message': error_msg
                        })
                
                except Exception as e:
                    total_failed += 1
                    _logger.exception(f"❌ Excepción enviando a {phone_line.phone}")
                    
                    results.append({
                        'copier': copier.secuencia,
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
    
    def action_add_phone(self):
        """Agregar número de teléfono manualmente (placeholder para botón)"""
        # Este método puede expandirse para abrir un mini-wizard si se desea
        return True
    
    def action_show_variables_help(self):
        """Mostrar ayuda de variables disponibles"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Variables Disponibles',
                'message': '''
Usa estas variables en tu mensaje:

- {secuencia} - Número de cotización
- {cliente} - Nombre del cliente
- {contacto} - Persona de contacto
- {maquina} - Modelo de máquina
- {marca} - Marca
- {serie} - Número de serie
- {total} - Total a facturar
- {subtotal} - Subtotal sin IGV
- {fecha} - Fecha de cotización
- {empresa} - Nombre de la empresa
- {ubicacion} - Ubicación
- {volumen_bn} - Volumen mensual B/N
- {volumen_color} - Volumen mensual color
- {costo_bn} - Costo por copia B/N
- {costo_color} - Costo por copia color
                ''',
                'type': 'info',
                'sticky': True,
            }
        }