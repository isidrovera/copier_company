from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
import qrcode
import base64
import io
from dateutil import tz
from datetime import datetime
from PIL import Image
from PIL import ImageDraw, ImageFont
import textwrap
import os
import re
import requests

import logging
_logger = logging.getLogger(__name__)

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Registro y gestión de máquinas multifuncionales en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('modelos.maquinas', string='Máquina', tracking=True)
    secuencia = fields.Char('Cotización N°', default='New', copy=False, required=True, readonly=True)
    
    @api.model
    def create(self, vals):
        vals['secuencia'] = self.env['ir.sequence'].next_by_code('copier.company') or '/'
        return super(CopierCompany, self).create(vals)
    
    imagen_id = fields.Binary(related='name.imagen',string="Imagen de la Máquina", attachment=True)


    fecha_formateada = fields.Char('Fecha', compute='_compute_fecha_formateada', store=True)

    @api.depends('create_date')
    def _compute_fecha_formateada(self):
        meses = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        lima_tz = tz.gettz('America/Lima')
        
        for record in self:
            if record.create_date:
                fecha_lima = record.create_date.astimezone(lima_tz)
                record.fecha_formateada = f"Lima {fecha_lima.day} de {meses[fecha_lima.month]} {fecha_lima.year}"

    def enviar_correo_propuesta(self):
        template = self.env.ref('copier_company.email_template_propuesta_alquiler')
        if template:
            template.send_mail(self.id, force_send=True)
            estado_enviado = self.env.ref('copier_company.estado_enviado')
            self.write({'estado_maquina_id': estado_enviado.id})
    
    especificaciones_id = fields.Html(related='name.especificaciones', string='Especificaciones')
    serie_id = fields.Char(string='Serie', tracking=True)
    marca_id = fields.Many2one('marcas.maquinas', string='Marca', related='name.marca_id')
    es_color = fields.Boolean(string='Es impresora color', default=False, tracking=True)
    tipo = fields.Selection([
        ('monocroma', 'Blanco y negro'),
        ('color', 'Color')
    ], string='Tipo de impresora', default='monocroma', tracking=True)
    
    # Campos del cliente
    cliente_id = fields.Many2one('res.partner', string='Cliente', tracking=True)
    tipo_identificacion = fields.Many2one(related='cliente_id.l10n_latam_identification_type_id', string="Tipo de identificación", readonly=False)
    identificacion = fields.Char(related='cliente_id.vat', string="Número de identificación", readonly=False)
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Teléfono')
    correo = fields.Char(string='Correo')
    
    # Campos de ubicación
    ubicacion = fields.Char(string='Ubicación', tracking=True)
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    
    # Configuración técnica
    formato = fields.Selection([
        ('a4', 'A4'),
        ('a3', 'A3')
    ], string='Formato', default='a4', tracking=True)
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado_maquina_id = fields.Many2one('copier.estados', string="Estado de la Máquina",
                                       default=lambda self: self.env.ref('copier_company.estado_disponible').id,
                                       tracking=True)
    tipo_calculo = fields.Selection([
        ('auto', 'Cálculo Automático'),
        ('manual_sin_igv_bn', 'Monto Mensual B/N sin IGV'),
        ('manual_con_igv_bn', 'Monto Mensual B/N con IGV'),
        ('manual_sin_igv_color', 'Monto Mensual Color sin IGV'),
        ('manual_con_igv_color', 'Monto Mensual Color con IGV'),
        ('manual_sin_igv_total', 'Monto Mensual Total sin IGV'),
        ('manual_con_igv_total', 'Monto Mensual Total con IGV'),
    ], string='Tipo de Cálculo', default='auto', tracking=True)
    monto_mensual_bn = fields.Monetary(
        string="Monto Mensual B/N",
        currency_field='currency_id'
    )
    
    monto_mensual_color = fields.Monetary(
        string="Monto Mensual Color",
        currency_field='currency_id'
    )
    monto_mensual_total = fields.Monetary(
        string="Monto Mensual Total",
        currency_field='currency_id'
    )

    subtotal_sin_igv = fields.Monetary(
        string="Subtotal (Sin IGV)",
        compute='_compute_renta_mensual',
        currency_field='currency_id',
        store=True
    )

    monto_igv = fields.Monetary(
        string="Monto IGV",
        compute='_compute_renta_mensual',
        currency_field='currency_id',
        store=True
    )

    monto_mensual_ingresado = fields.Monetary(
        string="Monto Mensual Ingresado",
        currency_field='currency_id'
    )
    @api.onchange('tipo_calculo', 'monto_mensual_bn', 'monto_mensual_color', 'monto_mensual_total',
                 'volumen_mensual_bn', 'volumen_mensual_color', 'igv')
    def _onchange_montos_mensuales(self):
        """Actualiza los costos unitarios cuando se cambian los montos mensuales deseados"""
        # Evitar cálculos innecesarios
        if self.tipo_calculo == 'auto':
            return
            
        # Validar que haya volúmenes válidos
        if self.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn'] and self.volumen_mensual_bn <= 0:
            return
            
        if self.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color'] and self.volumen_mensual_color <= 0:
            return
            
        if self.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
            if (self.volumen_mensual_bn + self.volumen_mensual_color) <= 0:
                return
        
        # Cálculo para monto mensual B/N
        if self.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn']:
            monto_sin_igv = self.monto_mensual_bn
            if self.tipo_calculo == 'manual_con_igv_bn':
                monto_sin_igv = self.monto_mensual_bn / (1 + (self.igv / 100))
                
            if self.volumen_mensual_bn > 0:
                self.costo_copia_bn = monto_sin_igv / self.volumen_mensual_bn
        
        # Cálculo para monto mensual Color
        elif self.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color']:
            monto_sin_igv = self.monto_mensual_color
            if self.tipo_calculo == 'manual_con_igv_color':
                monto_sin_igv = self.monto_mensual_color / (1 + (self.igv / 100))
                
            if self.volumen_mensual_color > 0:
                self.costo_copia_color = monto_sin_igv / self.volumen_mensual_color
        
        # Cálculo para monto mensual Total (distribución proporcional)
        elif self.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
            monto_sin_igv = self.monto_mensual_total
            if self.tipo_calculo == 'manual_con_igv_total':
                monto_sin_igv = self.monto_mensual_total / (1 + (self.igv / 100))
            
            # Si solo hay volumen B/N
            if self.volumen_mensual_bn > 0 and self.volumen_mensual_color == 0:
                self.costo_copia_bn = monto_sin_igv / self.volumen_mensual_bn
                self.costo_copia_color = 0
            
            # Si solo hay volumen Color
            elif self.volumen_mensual_color > 0 and self.volumen_mensual_bn == 0:
                self.costo_copia_color = monto_sin_igv / self.volumen_mensual_color
                self.costo_copia_bn = 0
            
            # Si hay ambos tipos, distribuir proporcionalmente pero manteniendo relación
            elif self.volumen_mensual_bn > 0 and self.volumen_mensual_color > 0:
                # Por defecto, el color suele ser más caro (4-5 veces)
                ratio_precio = 4
                
                # Fórmula: volumen_bn * x + volumen_color * (ratio*x) = monto_sin_igv
                # Donde x es el precio unitario B/N
                denominator = self.volumen_mensual_bn + (ratio_precio * self.volumen_mensual_color)
                
                if denominator > 0:
                    precio_bn = monto_sin_igv / denominator
                    precio_color = precio_bn * ratio_precio
                    
                    self.costo_copia_bn = precio_bn
                    self.costo_copia_color = precio_color

    def format_phone_number(self, phone):
        if not phone:
            return False
        # Eliminar espacios en blanco y el carácter '+'
        phone = phone.strip().replace(' ', '').replace('+', '')
        # Eliminar cualquier otro carácter que no sea número
        phone = re.sub(r'[^0-9]', '', phone)
        
        # Si el número no empieza con '51' y tiene 9 dígitos, agregar '51'
        if not phone.startswith('51') and len(phone) == 9:
            phone = f'51{phone}'
        
        return phone

    def get_formatted_phones(self):
        """Obtiene y formatea los números de teléfono del cliente"""
        if not self.cliente_id.mobile:
            return False
            
        # Dividir números por punto y coma y formatear cada uno
        phones = self.cliente_id.mobile.split(';')
        formatted_phones = []
        
        for phone in phones:
            formatted = self.format_phone_number(phone)
            if formatted:
                formatted_phones.append(formatted)
                
        return formatted_phones

    def send_whatsapp_report(self):
        try:
            if not self.cliente_id or not self.cliente_id.mobile:
                raise UserError('Se requiere un cliente con número de teléfono.')

            formatted_phones = self.get_formatted_phones()
            if not formatted_phones:
                raise UserError('No se encontraron números de teléfono válidos.')

            # Generar el PDF
            report_action = self.env.ref('copier_company.action_report_report_cotizacion_alquiler')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.id, self.ids
            )

            # Guardar PDF temporalmente
            filename = f"Propuesta_Comercial_{self.secuencia}.pdf"
            temp_pdf_path = os.path.join('/tmp', filename)

            try:
                with open(temp_pdf_path, 'wb') as temp_pdf:
                    temp_pdf.write(pdf_content)

                _logger.info(f"PDF generado: {temp_pdf_path}, tamaño: {os.path.getsize(temp_pdf_path)} bytes")

                WHATSAPP_API_URL = 'https://whatsappapi.copiercompanysac.com/api/message'
                success_count = 0

                for phone in formatted_phones:
                    try:
                        # Crear el mensaje corporativo
                        message = f"""¡Gracias por confiar en Copier Company!

        Te enviamos la *Propuesta Comercial {self.secuencia}* solicitada. 

        Por favor, revisa el documento adjunto. Si tienes alguna consulta o requieres información adicional, estaremos encantados de ayudarte.

        *Saludos cordiales,*
        Equipo Copier Company
        
        📧 info@copiercompanysac.com
        🌐 https://copiercompanysac.com"""

                        with open(temp_pdf_path, 'rb') as pdf_file:
                            files = {
                                'file': (filename, pdf_file, 'application/pdf')
                            }
                            
                            data = {
                                'phone': phone,
                                'type': 'media',
                                'message': message
                            }

                            _logger.info("Enviando a WhatsApp API - Datos: %s", data)

                            response = requests.post(
                                WHATSAPP_API_URL,
                                data=data,
                                files=files
                            )

                            _logger.info("Respuesta API: Status=%s, Contenido=%s", 
                                    response.status_code, response.text)

                            response_data = response.json()
                            if response.status_code == 200 and response_data.get('success'):
                                success_count += 1
                                self.message_post(
                                    body=f"✅ Propuesta comercial enviada por WhatsApp al número {phone}.",
                                    message_type='notification'
                                )
                            else:
                                raise Exception(response_data.get('message', 'Error en la API'))

                    except Exception as e:
                        _logger.error(f"Error al enviar WhatsApp a {phone}: {str(e)}")
                        self.message_post(
                            body=f"❌ Error al enviar WhatsApp al número {phone}: {str(e)}",
                            message_type='notification'
                        )

            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
                    _logger.info(f"Archivo temporal eliminado: {temp_pdf_path}")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f"Propuesta comercial enviada por WhatsApp a {success_count} número(s).",
                    'type': 'success' if success_count > 0 else 'warning',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.exception("Error en el envío del reporte:")
            raise UserError(f"Error al enviar el reporte: {str(e)}")

    # Campos de alquiler
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler", tracking=True)
    duracion_alquiler_id = fields.Many2one('copier.duracion', string="Duración del Alquiler",
                                          default=lambda self: self.env.ref('copier_company.duracion_1_año').id,
                                          tracking=True)
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)
    
    # Campos financieros
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                 default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1))
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", 
                                      currency_field='currency_id', 
                                      default=0.20)
    costo_copia_bn = fields.Float(string="Costo por Copia (B/N)", 
                             digits=(16,3),  # 16 dígitos en total, 3 decimales
                             default=0.04)
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")
    renta_mensual_color = fields.Monetary(string="Renta Mensual (Color)", 
                                        compute='_compute_renta_mensual',
                                        currency_field='currency_id',
                                        store=True)
    renta_mensual_bn = fields.Monetary(string="Renta Mensual (B/N)", 
                                     compute='_compute_renta_mensual',
                                     currency_field='currency_id',
                                     store=True)
    total_facturar_mensual = fields.Monetary(string="Total a Facturar Mensual",
                                           compute='_compute_renta_mensual',
                                           currency_field='currency_id',
                                           store=True)
    igv = fields.Float(string='IGV (%)', default=18.0)

    precio_bn_incluye_igv = fields.Boolean(
        'Precio B/N Incluye IGV',
        default=False,
        tracking=True,
        help="Si está marcado, el precio B/N ingresado ya incluye IGV"
    )

    precio_color_incluye_igv = fields.Boolean(
        'Precio Color Incluye IGV',
        default=False,
        tracking=True,
        help="Si está marcado, el precio Color ingresado ya incluye IGV"
    )
    descuento = fields.Float(string='Descuento (%)', default=0.0)
    dia_facturacion = fields.Integer(string='Día de Facturación', default=30)
    # Campos técnicos
    detalles = fields.Text(string='Detalles técnicos')
    qr_code = fields.Binary(string='Código QR', readonly=True, attachment=True)
    
    @api.onchange('tipo')
    def _onchange_tipo(self):
        if self.tipo == 'monocroma':
            self.es_color = False
            self.volumen_mensual_color = 0
        else:
            self.es_color = True

    @api.onchange('identificacion')
    def _onchange_identificacion(self):
        if not self.identificacion:
            return
            
        partner = self.env['res.partner'].search([('vat', '=', self.identificacion)], limit=1)
        if partner:
            self.cliente_id = partner.id
            self.tipo_identificacion = partner.l10n_latam_identification_type_id.id
            return
            
        new_partner = self.env['res.partner'].create({
            'vat': self.identificacion,
            'name': self.identificacion,
            'l10n_latam_identification_type_id': self.tipo_identificacion.id
        })
        new_partner._doc_number_change()
        self.cliente_id = new_partner.id
        self.tipo_identificacion = new_partner.l10n_latam_identification_type_id.id

    @api.depends('volumen_mensual_color', 'volumen_mensual_bn', 'costo_copia_color', 
             'costo_copia_bn', 'igv', 'descuento', 'tipo_calculo', 
             'monto_mensual_bn', 'monto_mensual_color', 'monto_mensual_total')
    def _compute_renta_mensual(self):
        for record in self:
            # Caso 1: Cálculo automático por costo unitario
            if record.tipo_calculo == 'auto':
                # Cálculo estándar por costos unitarios
                renta_color = record.volumen_mensual_color * record.costo_copia_color
                renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
                
            # Caso 2: Cálculo con montos fijos para B/N
            elif record.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn']:
                if record.tipo_calculo == 'manual_sin_igv_bn':
                    renta_bn = record.monto_mensual_bn
                else:  # manual_con_igv_bn
                    renta_bn = record.monto_mensual_bn / (1 + (record.igv / 100))
                
                # Mantener el cálculo normal para color
                renta_color = record.volumen_mensual_color * record.costo_copia_color
            
            # Caso 3: Cálculo con montos fijos para Color
            elif record.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color']:
                if record.tipo_calculo == 'manual_sin_igv_color':
                    renta_color = record.monto_mensual_color
                else:  # manual_con_igv_color
                    renta_color = record.monto_mensual_color / (1 + (record.igv / 100))
                
                # Mantener el cálculo normal para B/N
                renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
            
            # Caso 4: Cálculo con montos fijos para el total
            elif record.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
                # Determinar monto sin IGV total
                if record.tipo_calculo == 'manual_sin_igv_total':
                    monto_total = record.monto_mensual_total
                else:  # manual_con_igv_total
                    monto_total = record.monto_mensual_total / (1 + (record.igv / 100))
                
                # Distribuir el monto según los costos unitarios calculados
                volumen_total = record.volumen_mensual_bn + record.volumen_mensual_color
                
                if volumen_total > 0:
                    # Usar los costos unitarios ya calculados
                    renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
                    renta_color = record.volumen_mensual_color * record.costo_copia_color
                    
                    # Ajustar si es necesario para asegurar que la suma sea exactamente el monto deseado
                    factor_ajuste = monto_total / (renta_bn + renta_color) if (renta_bn + renta_color) > 0 else 1
                    renta_bn = renta_bn * factor_ajuste
                    renta_color = renta_color * factor_ajuste
                else:
                    # Si no hay volumen, asignar todo a B/N
                    renta_bn = monto_total
                    renta_color = 0
            
            # Común para todos los casos: cálculo de totales
            subtotal = renta_color + renta_bn
            
            # Aplicar descuento
            descuento_valor = subtotal * (record.descuento / 100.0)
            subtotal_con_descuento = subtotal - descuento_valor
            
            # Calcular IGV
            igv_valor = subtotal_con_descuento * (record.igv / 100.0)
            
            # Asignar valores a los campos
            record.renta_mensual_color = renta_color
            record.renta_mensual_bn = renta_bn
            record.subtotal_sin_igv = subtotal_con_descuento
            record.monto_igv = igv_valor
            record.total_facturar_mensual = subtotal_con_descuento + igv_valor


    @api.depends('fecha_inicio_alquiler', 'duracion_alquiler_id')
    def _calcular_fecha_fin(self):
        for record in self:
            if not (record.fecha_inicio_alquiler and record.duracion_alquiler_id):
                continue
                
            start_date = fields.Date.from_string(record.fecha_inicio_alquiler)
            duracion = record.duracion_alquiler_id.name
            
            if duracion == '6 Meses':
                record.fecha_fin_alquiler = start_date + relativedelta(months=+6)
            elif duracion == '1 Año':
                record.fecha_fin_alquiler = start_date + relativedelta(years=+1)
            elif duracion == '2 Años':
                record.fecha_fin_alquiler = start_date + relativedelta(years=+2)

    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket'].create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            'name': f"Servicio técnico - {self.name.name}",
            'description': f"Máquina: {self.name.name}\nSerie: {self.serie_id}\nUbicación: {self.ubicacion}"
        })
        
        return {
            'name': 'Ticket de Servicio',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    qr_code_filename = fields.Char(
    string="Nombre archivo QR",
    compute='_compute_qr_filename'
)   

    # Agregar después de la línea que define qr_code_filename
    sticker_corporativo = fields.Binary(
        string='Sticker Corporativo', 
        readonly=True, 
        attachment=True
    )

    sticker_filename = fields.Char(
        string="Nombre archivo Sticker",
        compute='_compute_sticker_filename'
    )

    @api.depends('secuencia', 'serie_id')
    def _compute_sticker_filename(self):
        for record in self:
            record.sticker_filename = f'sticker_corporativo_{record.secuencia or "new"}_{record.serie_id or "serie"}.png'
   




    def _fallback_html_to_image(self, html_content, layout='horizontal'):
        """Método alternativo usando PIL - Diseño limpio tipo Canon"""
        try:
            # Información dinámica del registro
            serie = getattr(self, 'serie_id', None) or "____________________"
            modelo = getattr(self.name, 'name', None) if hasattr(self, 'name') else "Modelo no especificado"
            
            # Crear imagen base con dimensiones según layout - ALTA RESOLUCIÓN
            if layout == 'vertical':
                width, height = 708, 1181  # 6cm x 10cm a 300 DPI
            else:
                width, height = 1181, 708  # 10cm x 6cm a 300 DPI
            
            img = Image.new('RGB', (width, height), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Cargar fuentes con tamaños proporcionales a la alta resolución
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font_title = font_subtitle = font_normal = font_small = ImageFont.load_default()
            
            # Colores
            primary_color = '#1e40af'
            text_color = '#374151'
            light_blue = '#dbeafe'
            border_color = '#3b82f6'
            
            if layout == 'horizontal':
                # === DISEÑO HORIZONTAL TIPO CANON ===
                margin = 30
                
                # LOGO - Esquina superior izquierda
                logo_width = 200
                logo_height = 80
                logo_x = margin
                logo_y = margin
                
                logo_base64 = self._get_company_logo_base64()
                if logo_base64:
                    try:
                        logo_data = base64.b64decode(logo_base64)
                        logo_img = Image.open(io.BytesIO(logo_data))
                        logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
                        
                        if logo_img.mode == 'RGBA':
                            img.paste(logo_img, (logo_x, logo_y), logo_img)
                        else:
                            img.paste(logo_img, (logo_x, logo_y))
                    except:
                        # Fallback: texto simple
                        draw.text((logo_x, logo_y), "COPIER COMPANY", fill=primary_color, font=font_subtitle)
                else:
                    # Fallback: texto simple
                    draw.text((logo_x, logo_y), "COPIER COMPANY", fill=primary_color, font=font_subtitle)
                
                # TÍTULO PRINCIPAL - Centrado arriba
                title_y = margin + 10
                draw.text((width//2, title_y), "ALQUILER DE FOTOCOPIADORAS", fill=primary_color, font=font_title, anchor="mt")
                
                # LÍNEA SEPARADORA
                line_y = title_y + 50
                draw.rectangle([margin, line_y, width-margin, line_y + 2], fill=border_color)
                
                # === INFORMACIÓN EN COLUMNAS ===
                content_start_y = line_y + 30
                col_width = (width - 3*margin) // 2  # Dividir en 2 columnas principales
                
                # COLUMNA IZQUIERDA - Información del equipo
                left_col_x = margin
                info_y = content_start_y
                
                # MODELO
                draw.text((left_col_x, info_y), "MODELO:", fill=primary_color, font=font_small)
                draw.text((left_col_x, info_y + 25), modelo, fill=text_color, font=font_normal)
                
                # SERIE  
                info_y += 70
                draw.text((left_col_x, info_y), "SERIE:", fill=primary_color, font=font_small)
                draw.text((left_col_x, info_y + 25), str(serie), fill=text_color, font=font_normal)
                
                # === SECCIÓN DE CONTACTO CENTRAL ===
                contact_y = content_start_y + 150
                contact_width = width - 2*margin - 250  # Dejar espacio para QR
                
                # Título de soporte
                draw.text((margin, contact_y), "PARA SOPORTE TÉCNICO:", fill=primary_color, font=font_subtitle)
                contact_y += 40
                
                # Cajas de contacto estilo Canon
                box_height = 35
                box_spacing = 10
                
                # EMAIL
                email_box = [margin, contact_y, margin + contact_width, contact_y + box_height]
                draw.rectangle(email_box, fill=light_blue, outline=border_color, width=2)
                draw.text((margin + 10, contact_y + 5), "EMAIL:", fill=primary_color, font=font_small)
                draw.text((margin + 10, contact_y + 20), "info@copiercompanysac.com", fill=text_color, font=font_small)
                
                contact_y += box_height + box_spacing
                
                # WHATSAPP
                whatsapp_box = [margin, contact_y, margin + contact_width, contact_y + box_height]
                draw.rectangle(whatsapp_box, fill=light_blue, outline=border_color, width=2)
                draw.text((margin + 10, contact_y + 5), "WHATSAPP:", fill=primary_color, font=font_small)
                draw.text((margin + 10, contact_y + 20), "975399303", fill=text_color, font=font_small)
                
                contact_y += box_height + box_spacing
                
                # WEBSITE
                website_box = [margin, contact_y, margin + contact_width, contact_y + box_height]
                draw.rectangle(website_box, fill=light_blue, outline=border_color, width=2)
                draw.text((margin + 10, contact_y + 5), "WEBSITE:", fill=primary_color, font=font_small)
                draw.text((margin + 10, contact_y + 20), "copiercompanysac.com", fill=text_color, font=font_small)
                
                # === QR CODE - Esquina superior derecha ===
                qr_size = 200
                qr_x = width - qr_size - margin
                qr_y = content_start_y
                
                # Etiqueta QR
                draw.text((qr_x + qr_size//2, qr_y - 25), "ESCANÉAME", fill='#0ea5e9', font=font_small, anchor="mm")
                
            else:
                # === DISEÑO VERTICAL ===
                margin = 30
                
                # LOGO - Centrado arriba
                logo_width = 300
                logo_height = 100
                logo_x = (width - logo_width) // 2
                logo_y = margin
                
                logo_base64 = self._get_company_logo_base64()
                if logo_base64:
                    try:
                        logo_data = base64.b64decode(logo_base64)
                        logo_img = Image.open(io.BytesIO(logo_data))
                        logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
                        
                        if logo_img.mode == 'RGBA':
                            img.paste(logo_img, (logo_x, logo_y), logo_img)
                        else:
                            img.paste(logo_img, (logo_x, logo_y))
                    except:
                        draw.text((width//2, logo_y + logo_height//2), "COPIER COMPANY", fill=primary_color, font=font_subtitle, anchor="mm")
                else:
                    draw.text((width//2, logo_y + logo_height//2), "COPIER COMPANY", fill=primary_color, font=font_subtitle, anchor="mm")
                
                # TÍTULO
                title_y = logo_y + logo_height + 30
                draw.text((width//2, title_y), "ALQUILER DE", fill=primary_color, font=font_title, anchor="mm")
                draw.text((width//2, title_y + 40), "FOTOCOPIADORAS", fill=primary_color, font=font_title, anchor="mm")
                
                # LÍNEA SEPARADORA
                line_y = title_y + 90
                draw.rectangle([margin, line_y, width-margin, line_y + 2], fill=border_color)
                
                # INFORMACIÓN DEL EQUIPO
                info_y = line_y + 40
                box_width = width - 2*margin
                box_height = 50
                
                # MODELO
                model_box = [margin, info_y, margin + box_width, info_y + box_height]
                draw.rectangle(model_box, fill=light_blue, outline=border_color, width=2)
                draw.text((margin + 15, info_y + 10), "MODELO:", fill=primary_color, font=font_small)
                draw.text((margin + 15, info_y + 30), modelo, fill=text_color, font=font_normal)
                
                info_y += box_height + 15
                
                # SERIE
                serie_box = [margin, info_y, margin + box_width, info_y + box_height]
                draw.rectangle(serie_box, fill=light_blue, outline=border_color, width=2)
                draw.text((margin + 15, info_y + 10), "SERIE:", fill=primary_color, font=font_small)
                draw.text((margin + 15, info_y + 30), str(serie), fill=text_color, font=font_normal)
                
                # SOPORTE TÉCNICO
                info_y += box_height + 40
                draw.text((width//2, info_y), "PARA SOPORTE TÉCNICO:", fill=primary_color, font=font_subtitle, anchor="mm")
                
                info_y += 40
                contact_box_height = 40
                
                # EMAIL
                email_box = [margin, info_y, margin + box_width, info_y + contact_box_height]
                draw.rectangle(email_box, fill=light_blue, outline=border_color, width=2)
                draw.text((width//2, info_y + 8), "EMAIL", fill=primary_color, font=font_small, anchor="mm")
                draw.text((width//2, info_y + 25), "info@copiercompanysac.com", fill=text_color, font=font_small, anchor="mm")
                
                info_y += contact_box_height + 10
                
                # WHATSAPP
                whatsapp_box = [margin, info_y, margin + box_width, info_y + contact_box_height]
                draw.rectangle(whatsapp_box, fill=light_blue, outline=border_color, width=2)
                draw.text((width//2, info_y + 8), "WHATSAPP", fill=primary_color, font=font_small, anchor="mm")
                draw.text((width//2, info_y + 25), "975399303", fill=text_color, font=font_small, anchor="mm")
                
                info_y += contact_box_height + 10
                
                # WEBSITE
                website_box = [margin, info_y, margin + box_width, info_y + contact_box_height]
                draw.rectangle(website_box, fill=light_blue, outline=border_color, width=2)
                draw.text((width//2, info_y + 8), "WEBSITE", fill=primary_color, font=font_small, anchor="mm")
                draw.text((width//2, info_y + 25), "copiercompanysac.com", fill=text_color, font=font_small, anchor="mm")
                
                # QR CODE - Al final
                qr_size = 180
                qr_x = (width - qr_size) // 2
                qr_y = height - qr_size - 80
                
                # Etiqueta QR
                draw.text((width//2, qr_y - 25), "ESCANÉAME", fill='#0ea5e9', font=font_small, anchor="mm")
            
            # === GENERAR Y AGREGAR QR CODE ===
            qr_base64 = self._generate_modern_qr((qr_size, qr_size))
            if qr_base64:
                try:
                    qr_data = base64.b64decode(qr_base64)
                    qr_img = Image.open(io.BytesIO(qr_data))
                    
                    # Marco blanco para el QR
                    frame_size = 8
                    draw.rectangle([qr_x - frame_size, qr_y - frame_size, 
                                qr_x + qr_size + frame_size, qr_y + qr_size + frame_size], 
                                fill='white', outline='#d1d5db', width=2)
                    
                    # QR Code
                    img.paste(qr_img, (qr_x, qr_y))
                    
                except Exception as e:
                    _logger.error(f"Error agregando QR: {str(e)}")
                    # Fallback QR placeholder
                    draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], 
                                fill='#f3f4f6', outline='#d1d5db', width=2)
                    draw.text((qr_x + qr_size//2, qr_y + qr_size//2), "QR CODE", 
                            fill='#6b7280', font=font_normal, anchor="mm")
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=100, dpi=(300, 300))
            return base64.b64encode(buffer.getvalue())
            
        except Exception as e:
            _logger.error(f"Error en fallback method: {str(e)}")
            raise UserError(f"Error generando sticker con PIL: {str(e)}")


    def _chrome_headless_method(self, html_content, layout='horizontal'):
        """Método alternativo usando Chrome headless con mejor resolución"""
        try:
            # Dimensiones según layout para alta resolución
            if layout == 'vertical':
                window_size = '708,1181'
            else:
                window_size = '1181,708'
                
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
                html_file.write(html_content)
                html_file.flush()
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
                    cmd = [
                        'google-chrome', '--headless', '--disable-gpu',
                        f'--window-size={window_size}',
                        '--hide-scrollbars',
                        '--disable-web-security',
                        '--force-device-scale-factor=3',
                        '--run-all-compositor-stages-before-draw',
                        f'--screenshot={img_file.name}',
                        f'file://{html_file.name}'
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists(img_file.name):
                        with open(img_file.name, 'rb') as f:
                            return base64.b64encode(f.read())
                    else:
                        raise Exception(f"Chrome headless error: {result.stderr}")
                        
        except Exception as e:
            _logger.warning(f"Chrome headless failed: {str(e)}, using fallback PIL method")
            return self._fallback_html_to_image(html_content, layout)
        finally:
            try:
                os.unlink(html_file.name)
                os.unlink(img_file.name)
            except:
                pass


    def _generate_modern_qr(self, size=(150, 150)):
        """Genera un QR code moderno con mejor calidad"""
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            
            # Crear QR con mejor calidad
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(f"{base_url}/public/helpdesk_ticket?copier_company_id={self.id}")
            qr.make(fit=True)
            
            # Generar imagen QR con mejor calidad
            qr_img = qr.make_image(fill_color="#2C3E50", back_color="white")
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            
            # Convertir a base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG', quality=100)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            _logger.error(f"Error generando QR: {str(e)}")
            return None


    def _get_company_logo_base64(self):
        """Obtiene el logo de la compañía en base64"""
        try:
            company = self.env.user.company_id
            if company.logo:
                return company.logo.decode('utf-8')
            return None
        except Exception as e:
            _logger.error(f"Error obteniendo logo: {str(e)}")
            return None


    def _create_html_template(self, qr_base64, logo_base64, layout='horizontal'):
        """Template HTML limpio estilo Canon"""
        
        # Información dinámica del registro
        serie = getattr(self, 'serie_id', None) or "____________________"
        modelo = getattr(self.name, 'name', None) if hasattr(self, 'name') else "Modelo no especificado"
        
        # Dimensiones en alta resolución (300 DPI)
        if layout == 'vertical':
            width, height = "708px", "1181px"
        else:
            width, height = "1181px", "708px"
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sticker Corporativo</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    width: {width};
                    height: {height};
                    font-family: 'Arial', sans-serif;
                    background: white;
                    overflow: hidden;
                    position: relative;
                }}
                
                .container {{
                    width: 100%;
                    height: 100%;
                    padding: 30px;
                    {"display: flex; flex-direction: column;" if layout == 'vertical' else "display: grid; grid-template-columns: 1fr 1fr 250px; grid-template-rows: auto 1fr;"}
                }}
                
                .header {{
                    {"text-align: center; margin-bottom: 20px;" if layout == 'vertical' else "grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;"}
                }}
                
                .logo {{
                    {"width: 300px; height: 100px; margin: 0 auto 20px;" if layout == 'vertical' else "width: 200px; height: 80px;"}
                    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 8px;
                }}
                
                .logo img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                }}
                
                .logo-text {{
                    color: white;
                    font-size: {"24px" if layout == 'vertical' else "20px"};
                    font-weight: bold;
                }}
                
                .title {{
                    color: #1e40af;
                    font-size: {"36px" if layout == 'vertical' else "32px"};
                    font-weight: bold;
                    text-transform: uppercase;
                    {"text-align: center;" if layout == 'vertical' else "text-align: left; flex-grow: 1; margin-left: 30px;"}
                }}
                
                .divider {{
                    width: 100%;
                    height: 2px;
                    background: #3b82f6;
                    margin: 20px 0;
                }}
                
                .content {{
                    {"flex-grow: 1;" if layout == 'vertical' else "grid-column: 1 / 3; display: flex; flex-direction: column; gap: 20px;"}
                }}
                
                .equipment-info {{
                    margin-bottom: 30px;
                }}
                
                .info-item {{
                    background: #dbeafe;
                    border: 2px solid #3b82f6;
                    padding: 12px 15px;
                    margin-bottom: 15px;
                    border-radius: 6px;
                }}
                
                .info-label {{
                    color: #1e40af;
                    font-size: 16px;
                    font-weight: bold;
                    text-transform: uppercase;
                    margin-bottom: 4px;
                }}
                
                .info-value {{
                    color: #374151;
                    font-size: 20px;
                    font-weight: normal;
                }}
                
                .contact-section {{
                    margin-top: 20px;
                }}
                
                .contact-title {{
                    color: #1e40af;
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    text-transform: uppercase;
                }}
                
                .contact-item {{
                    background: #dbeafe;
                    border: 2px solid #3b82f6;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    border-radius: 4px;
                }}
                
                .contact-type {{
                    color: #1e40af;
                    font-size: 14px;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                
                .contact-value {{
                    color: #374151;
                    font-size: 16px;
                    font-weight: normal;
                }}
                
                .qr-section {{
                    {"text-align: center; margin-top: 30px;" if layout == 'vertical' else "grid-column: 3; grid-row: 1 / -1; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 60px;"}
                }}
                
                .qr-label {{
                    color: #0ea5e9;
                    font-size: 16px;
                    font-weight: bold;
                    text-transform: uppercase;
                    margin-bottom: 10px;
                }}
                
                .qr-code {{
                    {"width: 180px; height: 180px;" if layout == 'vertical' else "width: 200px; height: 200px;"}
                    background: white;
                    border: 2px solid #d1d5db;
                    border-radius: 8px;
                    padding: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                
                .qr-code img {{
                    width: 100%;
                    height: 100%;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        {f'<img src="data:image/png;base64,{logo_base64}" alt="Logo">' if logo_base64 else '<div class="logo-text">COPIER COMPANY</div>'}
                    </div>
                    <div class="title">Alquiler de Fotocopiadoras</div>
                </div>
                
                <div class="divider"></div>
                
                <div class="content">
                    <div class="equipment-info">
                        <div class="info-item">
                            <div class="info-label">Modelo</div>
                            <div class="info-value">{modelo}</div>
                        </div>
                        
                        <div class="info-item">
                            <div class="info-label">Serie</div>
                            <div class="info-value">{serie}</div>
                        </div>
                    </div>
                    
                    <div class="contact-section">
                        <div class="contact-title">Para Soporte Técnico:</div>
                        
                        <div class="contact-item">
                            <div class="contact-type">Email</div>
                            <div class="contact-value">info@copiercompanysac.com</div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-type">WhatsApp</div>
                            <div class="contact-value">975399303</div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-type">Website</div>
                            <div class="contact-value">copiercompanysac.com</div>
                        </div>
                    </div>
                </div>
                
                <div class="qr-section">
                    <div class="qr-label">Escanéame</div>
                    <div class="qr-code">
                        {f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code">' if qr_base64 else '<div style="background: #f3f4f6; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #6b7280; border-radius: 4px;">QR CODE</div>'}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template


    def _html_to_image(self, html_content, layout='horizontal'):
        """Conversión con resolución mejorada"""
        try:
            # Dimensiones según layout
            if layout == 'vertical':
                width, height = '708', '1181'
            else:
                width, height = '1181', '708'
                
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
                html_file.write(html_content)
                html_file.flush()
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
                    cmd = [
                        'wkhtmltoimage',
                        '--width', width,
                        '--height', height,
                        '--quality', '100',
                        '--format', 'png',
                        '--margin-top', '0',
                        '--margin-bottom', '0', 
                        '--margin-left', '0',
                        '--margin-right', '0',
                        '--disable-smart-shrinking',
                        '--crop-h', height,
                        '--crop-w', width,
                        '--crop-x', '0',
                        '--crop-y', '0',
                        '--enable-local-file-access',
                        '--dpi', '300',
                        '--image-quality', '100',
                        html_file.name,
                        img_file.name
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        with open(img_file.name, 'rb') as f:
                            return base64.b64encode(f.read())
                    else:
                        raise Exception(f"wkhtmltoimage error: {result.stderr}")
                        
        except Exception as e:
            _logger.warning(f"wkhtmltoimage failed: {str(e)}, using fallback")
            return self._fallback_html_to_image(html_content, layout)
        finally:
            try:
                os.unlink(html_file.name)
                os.unlink(img_file.name) 
            except:
                pass


    def generar_sticker_corporativo(self, layout='horizontal'):
        """Genera sticker estilo Canon - limpio y profesional"""
        try:
            for record in self:
                # QR de alta resolución
                qr_base64 = record._generate_modern_qr((400, 400))
                
                # Logo de la compañía
                logo_base64 = record._get_company_logo_base64()
                
                # HTML optimizado estilo Canon
                html_content = record._create_html_template(qr_base64, logo_base64, layout)
                
                # Convertir con alta resolución
                image_base64 = record._html_to_image(html_content, layout)
                
                # Guardar
                record.sticker_corporativo = image_base64
                
                orientation = "vertical (6x10cm)" if layout == 'vertical' else "horizontal (10x6cm)"
                record.message_post(
                    body=f"✅ Sticker profesional {orientation} generado - Estilo Canon (300 DPI)",
                    message_type='notification'
                )
                
        except Exception as e:
            _logger.error(f"Error generando sticker: {str(e)}")
            raise UserError(f"Error al generar el sticker: {str(e)}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Sticker corporativo estilo Canon generado correctamente',
                'type': 'success',
                'sticky': False,
            }
        }







    @api.depends('secuencia')
    def _compute_qr_filename(self):
        for record in self:
            record.qr_code_filename = f'qr_code_{record.secuencia}.png'
    def generar_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_path = get_module_resource('copier_company', 'static', 'src', 'img', 'logo.png')
        
        if not os.path.isfile(logo_path):
            raise FileNotFoundError(f"Logo no encontrado: {logo_path}")
            
        logo = Image.open(logo_path)
        logo_size = (100, int((float(logo.size[1]) * float(100/float(logo.size[0])))))
        # Primer cambio aquí
        try:
            resampling_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resampling_filter = Image.ANTIALIAS
        logo = logo.resize(logo_size, resampling_filter)
        
        for record in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr.add_data(f"{base_url}/public/helpdesk_ticket?copier_company_id={record.id}")
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo)
            
            # Segundo cambio aquí (mismo filtro de remuestreo)
            qr_img = qr_img.resize((qr_img.size[0] // 2, qr_img.size[1] // 2), resampling_filter)
            
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            record.qr_code = base64.b64encode(buffer.getvalue())

    def action_print_report(self):
        return self.env.ref('copier_company.action_report_report_cotizacion_alquiler').report_action(self)

    # Campo compute para el contador
    counter_count = fields.Integer(
        string='Lecturas',
        compute='_compute_counter_count'
    )
    
    def _compute_counter_count(self):
        for record in self:
            record.counter_count = self.env['copier.counter'].search_count([
                ('maquina_id', '=', record.id)
            ])
    
    # Acción para el botón
    def action_view_counters(self):
        self.ensure_one()
        return {
            'name': 'Lecturas',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.counter',
            'view_mode': 'list,form',
            'domain': [('maquina_id', '=', self.id)],
            'context': {'default_maquina_id': self.id},
        }
    # Nuevos campos para manejar renovaciones
    estado_renovacion = fields.Selection([
        ('vigente', 'Contrato Vigente'),
        ('por_vencer', 'Por Vencer'),
        ('renovado', 'Renovado'),
        ('finalizado', 'Finalizado')
    ], string='Estado de Renovación', default='vigente', tracking=True)
    
    dias_notificacion = fields.Integer(
        string='Días para Notificación', 
        default=30,
        help='Días antes del vencimiento para comenzar las notificaciones'
    )
    
    responsable_id = fields.Many2one(
        'res.users', 
        string='Responsable de Renovación',
        tracking=True
    )
    historial_renovaciones = fields.One2many(
        'copier.renewal.history',
        'copier_id',
        string='Historial de Renovaciones'
    )

    @api.model
    def _cron_check_contract_expiration(self):
        """
        Cron job que se ejecuta diariamente para verificar contratos próximos a vencer
        y notificar al equipo interno
        """
        _logger.info("Iniciando verificación de contratos próximos a vencer")
        
        hoy = fields.Date.today()
        # Buscar contratos que no estén finalizados
        contratos = self.search([
            ('estado_renovacion', 'in', ['vigente', 'por_vencer']),
            ('fecha_fin_alquiler', '!=', False)
        ])
        
        _logger.info(f"Encontrados {len(contratos)} contratos para revisar")
        
        for contrato in contratos:
            try:
                dias_restantes = (contrato.fecha_fin_alquiler - hoy).days
                _logger.info(f"Contrato {contrato.name.name} - Días restantes: {dias_restantes}")
                
                # Si está dentro del período de notificación y aún no está marcado como por vencer
                if 0 < dias_restantes <= contrato.dias_notificacion and contrato.estado_renovacion != 'por_vencer':
                    _logger.info(f"Marcando contrato {contrato.name.name} como por vencer")
                    contrato.estado_renovacion = 'por_vencer'
                    
                    # Crear nota en el chatter
                    contrato.message_post(
                        body=f"""
                        🔔 ALERTA DE VENCIMIENTO DE CONTRATO
                        
                        El contrato está próximo a vencer:
                        • Cliente: {contrato.cliente_id.name}
                        • Máquina: {contrato.name.name}
                        • Serie: {contrato.serie_id}
                        • Días restantes: {dias_restantes}
                        • Fecha de vencimiento: {contrato.fecha_fin_alquiler}
                        
                        Por favor, gestionar la renovación del contrato.
                        """,
                        message_type='notification'
                    )
                    
                    # Crear actividad para el responsable o equipo de ventas
                    if contrato.responsable_id:
                        contrato._crear_actividad_renovacion(contrato.responsable_id)
                    else:
                        grupo_ventas = self.env.ref('sales_team.group_sale_salesman', False)
                        if grupo_ventas and grupo_ventas.users:
                            for usuario in grupo_ventas.users:
                                contrato._crear_actividad_renovacion(usuario)
                
                # Si el contrato ya venció
                elif dias_restantes <= 0 and contrato.estado_renovacion != 'finalizado':
                    _logger.info(f"Marcando contrato {contrato.name.name} como finalizado")
                    contrato.estado_renovacion = 'finalizado'
                    contrato.message_post(
                        body="⚠️ CONTRATO VENCIDO\nEl contrato ha llegado a su fecha de finalización.",
                        message_type='notification'
                    )
                    
            except Exception as e:
                _logger.error(f"Error procesando contrato {contrato.name.name}: {str(e)}")
                
        _logger.info("Finalizada la verificación de contratos")
    def _crear_actividad_renovacion(self, usuario):
        """Crea una actividad para la renovación del contrato"""
        try:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Renovación de Contrato - {self.name.name}',
                'note': f'''
                    📅 Contrato próximo a vencer
                    
                    • Cliente: {self.cliente_id.name}
                    • Máquina: {self.name.name}
                    • Serie: {self.serie_id}
                    • Fecha de vencimiento: {self.fecha_fin_alquiler}
                    • Días restantes: {(self.fecha_fin_alquiler - fields.Date.today()).days}
                    
                    Por favor, gestionar la renovación del contrato.
                ''',
                'user_id': usuario.id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('copier.company').id,
                'date_deadline': fields.Date.today() + timedelta(days=5)
            })
            _logger.info(f"Actividad creada para el usuario {usuario.name}")
        except Exception as e:
            _logger.error(f"Error creando actividad: {str(e)}")
    def _crear_nota_vencimiento(self, dias_restantes):
        """Crea una nota en el chatter sobre el vencimiento próximo"""
        self.message_post(
            body=f'''
            🔔 ALERTA DE VENCIMIENTO DE CONTRATO
            
            El contrato está próximo a vencer:
            • Cliente: {self.cliente_id.name}
            • Máquina: {self.name.name}
            • Serie: {self.serie_id}
            • Días restantes: {dias_restantes}
            • Fecha de vencimiento: {self.fecha_fin_alquiler}
            
            Se ha creado una actividad para gestionar la renovación.
            ''',
            message_type='notification'
        )

    def action_renovar_contrato(self):
        """
        Acción para renovar el contrato y registrar en el historial
        """
        self.ensure_one()
        _logger.info(f"Iniciando renovación de contrato para {self.name.name}")
        
        try:
            # Crear registro en el historial de renovaciones
            self.env['copier.renewal.history'].create({
                'copier_id': self.id,
                'fecha_anterior': self.fecha_inicio_alquiler,
                'fecha_fin_anterior': self.fecha_fin_alquiler,
                'duracion_anterior_id': self.duracion_alquiler_id.id,
                'notas': f'Renovación desde {self.fecha_inicio_alquiler} hasta {self.fecha_fin_alquiler}'
            })
            _logger.info("Historial de renovación creado exitosamente")
            
            # Actualizar fechas del contrato
            antigua_fecha_fin = self.fecha_fin_alquiler
            self.fecha_inicio_alquiler = antigua_fecha_fin + relativedelta(days=1)
            self._calcular_fecha_fin()
            
            # Actualizar estado
            self.estado_renovacion = 'renovado'
            
            # Registrar en el chatter
            self.message_post(
                body=f"""
                ✅ CONTRATO RENOVADO
                
                Se ha renovado el contrato:
                • Período anterior: {antigua_fecha_fin}
                • Nuevo período: {self.fecha_inicio_alquiler} - {self.fecha_fin_alquiler}
                • Duración: {self.duracion_alquiler_id.name}
                """,
                message_type='notification'
            )
            
            _logger.info(f"Renovación completada exitosamente para {self.name.name}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': 'El contrato ha sido renovado exitosamente',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error durante la renovación del contrato: {str(e)}")
            raise UserError(f"Error al renovar el contrato: {str(e)}")


    def get_precio_bn_sin_igv(self, precio):
        self.ensure_one()
        if self.precio_bn_incluye_igv:
            return precio / 1.18
        return precio

    def get_precio_color_sin_igv(self, precio):
        self.ensure_one()
        if self.precio_color_incluye_igv:
            return precio / 1.18
        return precio
    # Agregar después de los campos financieros existentes
    producto_facturable_bn_id = fields.Many2one(
        'product.product',
        string='Producto a Facturar B/N',
        help='Producto que se facturará para las copias en blanco y negro'
    )

    producto_facturable_color_id = fields.Many2one(
        'product.product',
        string='Producto a Facturar Color',
        help='Producto que se facturará para las copias a color'
    )

    # Campo computed para mantener compatibilidad (opcional)
    producto_facturable_id = fields.Many2one(
        'product.product',
        string='Producto Principal',
        compute='_compute_producto_principal',
        help='Producto principal (B/N para monocromas, B/N para color)'
    )

    @api.depends('tipo', 'producto_facturable_bn_id', 'producto_facturable_color_id')
    def _compute_producto_principal(self):
        """Determina el producto principal según el tipo de máquina"""
        for record in self:
            if record.tipo == 'monocroma':
                record.producto_facturable_id = record.producto_facturable_bn_id
            else:  # color
                record.producto_facturable_id = record.producto_facturable_bn_id or record.producto_facturable_color_id

   
    @api.onchange('tipo', 'es_color')
    def _onchange_tipo_producto(self):
        """Sugiere productos basados en el tipo de máquina"""
        
        # Limpiar productos primero
        self.producto_facturable_bn_id = False
        self.producto_facturable_color_id = False
        
        if self.tipo == 'monocroma':
            # Para monocromas: solo producto B/N
            producto_mono = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Blanco y Negro'),
                ('name', 'ilike', 'Alquiler%Blanco%Negro')
            ], limit=1)
            if producto_mono:
                self.producto_facturable_bn_id = producto_mono.id
                
        elif self.tipo == 'color':
            # Para color: ambos productos
            
            # Producto B/N (mismo que monocromas)
            producto_bn = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Blanco y Negro'),
                ('name', 'ilike', 'Alquiler%Blanco%Negro')
            ], limit=1)
            if producto_bn:
                self.producto_facturable_bn_id = producto_bn.id
            
            # Producto Color
            producto_color = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Color'),
                ('name', 'ilike', 'Alquiler%Color')
            ], limit=1)
            if producto_color:
                self.producto_facturable_color_id = producto_color.id
                
        # Mensaje informativo al usuario
        if self.tipo == 'color' and (not self.producto_facturable_bn_id or not self.producto_facturable_color_id):
            return {
                'warning': {
                    'title': 'Productos no encontrados',
                    'message': 'No se encontraron todos los productos necesarios para máquinas color. '
                            'Asegúrate de tener creados:\n'
                            '- Alquiler de Máquina Fotocopiadora Blanco y Negro\n'
                            '- Alquiler de Máquina Fotocopiadora Color'
                }
            }


class CopierRenewalHistory(models.Model):
    _name = 'copier.renewal.history'
    _description = 'Historial de Renovaciones de Contratos'
    _order = 'fecha_renovacion desc'

    copier_id = fields.Many2one('copier.company', string='Máquina', required=True, ondelete='cascade')
    fecha_renovacion = fields.Date(string='Fecha de Renovación', default=fields.Date.today)
    fecha_anterior = fields.Date(string='Fecha Inicio Anterior', required=True)
    fecha_fin_anterior = fields.Date(string='Fecha Fin Anterior', required=True)
    duracion_anterior_id = fields.Many2one('copier.duracion', string='Duración Anterior', required=True)
    notas = fields.Text(string='Notas')

class CotizacionAlquilerReport(models.AbstractModel):
    _name = 'report.copier_company.cotizacion_view'
    _description = 'Reporte de Cotización de Alquiler'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara los valores para el reporte"""
        # Obtener los registros directamente
        docs = self.env['copier.company'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'copier.company',
            'docs': docs,
            'data': data,
            'company': self.env.company,
            # Helper functions
            'format_currency': lambda amount: '{:,.2f}'.format(amount or 0.0),
            'format_number': lambda number: '{:,}'.format(number or 0),
        }

        
