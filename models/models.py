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
        """Método alternativo usando PIL para crear la imagen sin márgenes"""
        try:
            # Información dinámica del registro
            serie = getattr(self, 'serie_id', None) or "____________________"
            modelo = getattr(self.name, 'name', None) if hasattr(self, 'name') else "Modelo no especificado"
            
            # Crear imagen base con dimensiones según layout
            if layout == 'vertical':
                width, height = 227, 378  # 6cm x 10cm a 96 DPI
            else:
                width, height = 378, 227  # 10cm x 6cm a 96 DPI
            
            img = Image.new('RGB', (width, height), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Intentar cargar fuentes
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
            except:
                font_title = font_normal = font_small = ImageFont.load_default()
            
            # Colores
            primary_color = '#1e40af'
            text_color = '#374151'
            
            if layout == 'vertical':
                # Layout vertical - Logo arriba sin margen
                logo_y = 0  # Sin margen superior
                logo_size = 50
                logo_x = (width - logo_size*2) // 2  # Centrado horizontalmente
                
                # Logo pegado arriba
                logo_base64 = self._get_company_logo_base64()
                if logo_base64:
                    try:
                        logo_data = base64.b64decode(logo_base64)
                        logo_img = Image.open(io.BytesIO(logo_data))
                        logo_img = logo_img.resize((logo_size*2, logo_size), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
                        
                        if logo_img.mode == 'RGBA':
                            img.paste(logo_img, (logo_x, logo_y), logo_img)
                        else:
                            img.paste(logo_img, (logo_x, logo_y))
                    except:
                        # Fallback: dibujar rectángulo como logo
                        draw.rectangle([logo_x, logo_y, logo_x+logo_size*2, logo_y+logo_size], fill=primary_color)
                        draw.text((logo_x+logo_size, logo_y+logo_size//2), "CC", fill='white', font=font_title, anchor="mm")
                else:
                    # Fallback: dibujar rectángulo como logo
                    draw.rectangle([logo_x, logo_y, logo_x+logo_size*2, logo_y+logo_size], fill=primary_color)
                    draw.text((logo_x+logo_size, logo_y+logo_size//2), "CC", fill='white', font=font_title, anchor="mm")
                
                # Título inmediatamente después del logo
                y = logo_y + logo_size + 5
                title_text = "ALQUILER DE"
                title_text2 = "FOTOCOPIADORAS"
                draw.text((width//2, y), title_text, fill=primary_color, font=font_title, anchor="mm")
                draw.text((width//2, y+15), title_text2, fill=primary_color, font=font_title, anchor="mm")
                
                # Texto de soporte
                y += 35
                support_text = "Para soporte técnico:"
                draw.rectangle([5, y-2, width-5, y+12], fill='#f0f9ff', outline='#e0f2fe')
                draw.rectangle([5, y-2, 8, y+12], fill='#0ea5e9')
                draw.text((width//2, y+5), support_text, fill=text_color, font=font_small, anchor="mm")
                
                # Información del equipo
                y += 20
                info_items = [
                    ("Modelo:", modelo),
                    ("Serie:", serie)
                ]
                
                for label, value in info_items:
                    # Fondo para cada item
                    draw.rectangle([5, y-1, width-5, y+11], fill='#f8fafc', outline='#e2e8f0')
                    draw.rectangle([5, y-1, 8, y+11], fill='#3b82f6')
                    
                    # Texto
                    draw.text((10, y), label, fill=primary_color, font=font_small)
                    draw.text((10, y+6), value[:25], fill=text_color, font=font_small)  # Truncar si es muy largo
                    y += 18
                
                # Contactos
                y += 5
                contacts = [
                    ("Correo:", "info@copiercompanysac.com"),
                    ("WhatsApp:", "975399303")
                ]
                
                for label, value in contacts:
                    # Fondo para cada contacto
                    draw.rectangle([5, y-1, width-5, y+11], fill='#f8fafc', outline='#e2e8f0')
                    draw.rectangle([5, y-1, 8, y+11], fill='#3b82f6')
                    
                    # Texto
                    draw.text((10, y), label, fill=primary_color, font=font_small)
                    draw.text((10, y+6), value, fill=text_color, font=font_small)
                    y += 18
                
                # Website
                y += 5
                draw.rectangle([5, y-1, width-5, y+11], fill='#e0f2fe', outline='#0ea5e9')
                web_text = "copiercompanysac.com"
                draw.text((width//2, y+5), web_text, fill=primary_color, font=font_normal, anchor="mm")
                
                # QR Code al final
                y += 20
                qr_size = 80
                qr_x = (width - qr_size) // 2
                qr_y = y
                
            else:
                # Layout horizontal - Logo arriba izquierda sin margen
                logo_y = 0  # Sin margen superior
                logo_size = 50
                logo_x = 0  # Sin margen izquierdo
                
                # Logo pegado arriba izquierda
                logo_base64 = self._get_company_logo_base64()
                if logo_base64:
                    try:
                        logo_data = base64.b64decode(logo_base64)
                        logo_img = Image.open(io.BytesIO(logo_data))
                        logo_img = logo_img.resize((logo_size*2, logo_size), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
                        
                        if logo_img.mode == 'RGBA':
                            img.paste(logo_img, (logo_x, logo_y), logo_img)
                        else:
                            img.paste(logo_img, (logo_x, logo_y))
                    except:
                        # Fallback: dibujar rectángulo como logo
                        draw.rectangle([logo_x, logo_y, logo_x+logo_size*2, logo_y+logo_size], fill=primary_color)
                        draw.text((logo_x+logo_size, logo_y+logo_size//2), "CC", fill='white', font=font_title, anchor="mm")
                else:
                    # Fallback: dibujar rectángulo como logo
                    draw.rectangle([logo_x, logo_y, logo_x+logo_size*2, logo_y+logo_size], fill=primary_color)
                    draw.text((logo_x+logo_size, logo_y+logo_size//2), "CC", fill='white', font=font_title, anchor="mm")
                
                # Título al lado del logo
                title_x = logo_x + logo_size*2 + 10
                title_y = logo_y + 10
                title_text = "ALQUILER DE FOTOCOPIADORAS"
                draw.text((title_x, title_y), title_text, fill=primary_color, font=font_title)
                
                # Texto de soporte debajo del título
                y = logo_y + logo_size + 5
                support_text = "Para soporte técnico, escanea el QR o contáctanos:"
                draw.rectangle([5, y-2, 250, y+12], fill='#f0f9ff', outline='#e0f2fe')
                draw.rectangle([5, y-2, 8, y+12], fill='#0ea5e9')
                draw.text((10, y+5), support_text, fill=text_color, font=font_small)
                
                # Información en dos columnas
                y += 20
                left_info = [
                    f"Modelo: {modelo}",
                    "Correo: info@copiercompanysac.com"
                ]
                
                right_info = [
                    f"Serie: {serie}",
                    "WhatsApp: 975399303"
                ]
                
                # Columna izquierda
                for i, info in enumerate(left_info):
                    y_pos = y + i * 15
                    draw.rectangle([5, y_pos-1, 180, y_pos+11], fill='#f8fafc', outline='#e2e8f0')
                    draw.rectangle([5, y_pos-1, 8, y_pos+11], fill='#3b82f6')
                    draw.text((10, y_pos+5), info, fill=text_color, font=font_small)
                
                # Columna derecha
                for i, info in enumerate(right_info):
                    y_pos = y + i * 15
                    draw.rectangle([185, y_pos-1, 280, y_pos+11], fill='#f8fafc', outline='#e2e8f0')
                    draw.rectangle([185, y_pos-1, 188, y_pos+11], fill='#3b82f6')
                    draw.text((190, y_pos+5), info, fill=text_color, font=font_small)
                
                # Website abajo
                y += 40
                draw.rectangle([5, y-1, 280, y+11], fill='#e0f2fe', outline='#0ea5e9')
                web_text = "https://copiercompanysac.com"
                draw.text((10, y+5), web_text, fill=primary_color, font=font_normal)
                
                # QR Code a la derecha sin margen
                qr_size = 120
                qr_x = width - qr_size  # Sin margen derecho
                qr_y = 0  # Sin margen superior
            
            # Generar QR Code
            qr_base64 = self._generate_modern_qr((qr_size, qr_size))
            if qr_base64:
                try:
                    qr_data = base64.b64decode(qr_base64)
                    qr_img = Image.open(io.BytesIO(qr_data))
                    
                    # Fondo blanco para el QR sin margen extra
                    draw.rectangle([qr_x, qr_y, qr_x+qr_size, qr_y+qr_size], 
                                fill='white', outline='#e2e8f0', width=1)
                    
                    img.paste(qr_img, (qr_x, qr_y))
                    
                    # Etiqueta "Escanéame"
                    if layout == 'vertical':
                        label_y = qr_y + qr_size + 2
                        if label_y < height - 10:  # Solo si hay espacio
                            draw.text((qr_x + qr_size//2, label_y), "Escanéame", 
                                    fill=primary_color, font=font_small, anchor="mm")
                    else:
                        # En horizontal, etiqueta dentro del QR
                        draw.rectangle([qr_x, qr_y+qr_size-15, qr_x+qr_size, qr_y+qr_size], 
                                    fill='white', outline=None)
                        draw.text((qr_x + qr_size//2, qr_y+qr_size-7), "Escanéame", 
                                fill=primary_color, font=font_small, anchor="mm")
                except Exception as e:
                    _logger.error(f"Error agregando QR: {str(e)}")
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=95)
            return base64.b64encode(buffer.getvalue())
            
        except Exception as e:
            _logger.error(f"Error en fallback method: {str(e)}")
            raise UserError(f"Error generando sticker con PIL: {str(e)}")


    def _chrome_headless_method(self, html_content, layout='horizontal'):
        """Método alternativo usando Chrome headless - también necesita el parámetro layout"""
        try:
            # Dimensiones según layout
            if layout == 'vertical':
                window_size = '227,378'
            else:
                window_size = '378,227'
                
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
                html_file.write(html_content)
                html_file.flush()
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
                    cmd = [
                        'google-chrome', '--headless', '--disable-gpu',
                        f'--window-size={window_size}',
                        '--hide-scrollbars',
                        '--disable-web-security',
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
        """Genera un QR code moderno con esquinas redondeadas"""
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            
            # Crear QR con mejor calidad
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=8,
                border=2,
            )
            qr.add_data(f"{base_url}/public/helpdesk_ticket?copier_company_id={self.id}")
            qr.make(fit=True)
            
            # Generar imagen QR
            qr_img = qr.make_image(fill_color="#2C3E50", back_color="white")
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            
            # Convertir a base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
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
        """Template HTML con alta resolución y mejor distribución"""
        
        # Información dinámica del registro
        serie = getattr(self, 'serie_id', None) or "____________________"
        modelo = getattr(self.name, 'name', None) if hasattr(self, 'name') else "Modelo no especificado"
        
        # Dimensiones en alta resolución (300 DPI)
        if layout == 'vertical':
            width, height = "708px", "1181px"  # 6cm x 10cm a 300 DPI
            grid_areas = '''
                "logo"
                "title"
                "support"
                "modelo"
                "serie"  
                "correo"
                "telefono"
                "website"
                "qr"
            '''
            grid_columns = "1fr"
            grid_rows = "120px 60px 40px 35px 35px 35px 35px 40px 200px"
            qr_size = "180px"
            logo_height = "100px"
        else:
            # Layout horizontal mejorado
            width, height = "1181px", "708px"  # 10cm x 6cm a 300 DPI
            grid_areas = '''
                "logo logo logo qr"
                "title title title qr"
                "support support support qr"
                "info1 info2 info3 qr"
                "website website website qr"
            '''
            grid_columns = "1fr 1fr 1fr 200px"
            grid_rows = "120px 60px 50px 80px 40px"
            qr_size = "180px"
            logo_height = "100px"
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sticker Corporativo HD</title>
            <style>
                *, *::before, *::after {{
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box;
                }}
                
                html, body {{
                    margin: 0 !important;
                    padding: 0 !important;
                    width: 100% !important;
                    height: 100% !important;
                    overflow: hidden;
                    font-family: 'Arial', 'Helvetica', sans-serif;
                    background: white;
                }}
                
                .sticker {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: {width};
                    height: {height};
                    background: white;
                    border: none !important;
                    overflow: hidden;
                    padding: 0 !important;
                    margin: 0 !important;
                    display: grid;
                    grid-template-areas: {grid_areas};
                    grid-template-columns: {grid_columns};
                    grid-template-rows: {grid_rows};
                    gap: 15px;
                    align-content: start;
                }}
                
                .header-logo {{
                    grid-area: logo;
                    display: flex;
                    justify-content: flex-start;
                    align-items: flex-start;
                    padding: 0 !important;
                    margin: 0 !important;
                }}
                
                .logo {{
                    height: {logo_height};
                    max-width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 !important;
                    padding: 0 !important;
                }}
                
                .logo img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    margin: 0 !important;
                    padding: 0 !important;
                }}
                
                .logo-fallback {{
                    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                    color: white;
                    font-weight: 700;
                    font-size: 32px;
                    text-align: center;
                    width: 200px;
                    height: {logo_height};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 12px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    margin: 0 !important;
                    padding: 0 !important;
                }}
                
                .title-section {{
                    grid-area: title;
                    text-align: center;
                    margin: 0 !important;
                    padding: 0 !important;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .title-section h2 {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e40af;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin: 0 !important;
                    padding: 0 !important;
                    line-height: 1.2;
                }}
                
                .support-text {{
                    grid-area: support;
                    font-size: 20px;
                    color: #374151;
                    font-weight: 600;
                    text-align: center;
                    background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
                    padding: 12px 16px !important;
                    border-radius: 8px;
                    border-left: 6px solid #0ea5e9;
                    margin: 0 !important;
                    line-height: 1.4;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                /* Layout horizontal - información en columnas */
                .info1 {{ grid-area: info1; }}
                .info2 {{ grid-area: info2; }}
                .info3 {{ grid-area: info3; }}
                
                .info-item {{
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    font-size: 18px;
                    color: #374151;
                    line-height: 1.4;
                    padding: 8px !important;
                    background: #f8fafc;
                    border-radius: 6px;
                    border-left: 4px solid #3b82f6;
                    margin: 0 !important;
                }}
                
                .info-label {{
                    font-weight: 700;
                    color: #1e40af;
                    font-size: 16px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .info-value {{
                    font-weight: 500;
                    color: #374151;
                    word-break: break-word;
                }}
                
                /* Layout vertical - información apilada */
                .modelo {{ grid-area: modelo; }}
                .serie {{ grid-area: serie; }}
                .correo {{ grid-area: correo; }}
                .telefono {{ grid-area: telefono; }}
                
                .info-row {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 18px;
                    padding: 8px 12px !important;
                    background: #f8fafc;
                    border-radius: 6px;
                    border-left: 4px solid #3b82f6;
                    margin: 0 !important;
                }}
                
                .info-row .label {{
                    font-weight: 700;
                    color: #1e40af;
                    min-width: 80px;
                    text-transform: uppercase;
                    font-size: 16px;
                }}
                
                .info-row .value {{
                    font-weight: 500;
                    color: #374151;
                    flex: 1;
                }}
                
                .website {{
                    grid-area: website;
                    text-align: center;
                    font-size: 20px;
                    color: #1e40af;
                    font-weight: 700;
                    padding: 8px 0 !important;
                    border-top: 2px solid #e2e8f0;
                    margin: 0 !important;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .qr-section {{
                    grid-area: qr;
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    justify-content: flex-start;
                    gap: 10px;
                    padding: 0 !important;
                    margin: 0 !important;
                }}
                
                .qr-label {{
                    font-size: 16px;
                    font-weight: 700;
                    color: #0ea5e9;
                    text-align: center;
                    margin: 0 !important;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                .qr-code {{
                    width: {qr_size};
                    height: {qr_size};
                    border-radius: 12px;
                    overflow: hidden;
                    background: white;
                    padding: 8px !important;
                    border: 3px solid #e2e8f0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    margin: 0 !important;
                }}
                
                .qr-code img {{
                    width: 100%;
                    height: 100%;
                    border-radius: 8px;
                }}
                
                @media print {{
                    html, body {{
                        margin: 0 !important;
                        padding: 0 !important;
                        width: auto !important;
                        height: auto !important;
                    }}
                    
                    .sticker {{
                        border: none !important;
                        box-shadow: none !important;
                        margin: 0 !important;
                        padding: 0 !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="sticker">
                <div class="header-logo">
                    <div class="logo">
                        {f'<img src="data:image/png;base64,{logo_base64}" alt="Logo">' if logo_base64 else '<div class="logo-fallback">COPIER COMPANY</div>'}
                    </div>
                </div>
                
                <div class="title-section">
                    <h2>ALQUILER DE FOTOCOPIADORAS</h2>
                </div>
                
                <div class="support-text">
                    Para soporte técnico, escanea el QR o contáctanos:
                </div>
                
                {f'''
                <!-- Layout Vertical -->
                <div class="modelo info-row">
                    <span class="label">Modelo:</span>
                    <span class="value">{modelo}</span>
                </div>
                
                <div class="serie info-row">
                    <span class="label">Serie:</span>
                    <span class="value">{serie}</span>
                </div>
                
                <div class="correo info-row">
                    <span class="label">Correo:</span>
                    <span class="value">info@copiercompanysac.com</span>
                </div>
                
                <div class="telefono info-row">
                    <span class="label">Teléfono:</span>
                    <span class="value">975399303</span>
                </div>
                ''' if layout == 'vertical' else f'''
                <!-- Layout Horizontal -->
                <div class="info1 info-item">
                    <div class="info-label">Modelo</div>
                    <div class="info-value">{modelo}</div>
                </div>
                
                <div class="info2 info-item">
                    <div class="info-label">Serie</div>
                    <div class="info-value">{serie}</div>
                </div>
                
                <div class="info3 info-item">
                    <div class="info-label">Contacto</div>
                    <div class="info-value">
                        info@copiercompanysac.com<br>
                        WhatsApp: 975399303
                    </div>
                </div>
                '''}
                
                <div class="website">
                    https://copiercompanysac.com
                </div>
                
                <div class="qr-section">
                    <div class="qr-label">Escanéame</div>
                    <div class="qr-code">
                        {f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code">' if qr_base64 else '<div style="background: #f3f4f6; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #6b7280;">QR</div>'}
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
                width, height = '708', '1181'  # 6x10cm a 300 DPI
            else:
                width, height = '1181', '708'  # 10x6cm a 300 DPI
                
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
                        '--dpi', '300',  # Alta resolución
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
        """Genera sticker en alta resolución"""
        try:
            for record in self:
                # QR de alta resolución
                qr_base64 = record._generate_modern_qr((300, 300))
                
                # Logo de la compañía
                logo_base64 = record._get_company_logo_base64()
                
                # HTML en alta resolución
                html_content = record._create_html_template(qr_base64, logo_base64, layout)
                
                # Convertir con alta resolución
                image_base64 = record._html_to_image(html_content, layout)
                
                # Guardar
                record.sticker_corporativo = image_base64
                
                orientation = "vertical (6x10cm)" if layout == 'vertical' else "horizontal (10x6cm)"
                record.message_post(
                    body=f"✅ Sticker HD {orientation} generado (300 DPI)",
                    message_type='notification'
                )
                
        except Exception as e:
            _logger.error(f"Error generando sticker HD: {str(e)}")
            raise UserError(f"Error al generar el sticker: {str(e)}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Sticker corporativo HD generado correctamente',
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

        
