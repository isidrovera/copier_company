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
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Términos de pago',
        help='Términos de pago para esta transacción'
    )

    def debug_urgente_company(self):
        """Debug urgente para identificar el problema real"""
        _logger.info("🔍 === DEBUG URGENTE COPIER.COMPANY ===")
        self.ensure_one()
        
        # Forzar recálculo
        self._compute_renta_mensual()
        
        _logger.info("DATOS BÁSICOS:")
        _logger.info("- ID: %s", self.id)
        _logger.info("- Secuencia: %s", self.secuencia)
        _logger.info("- Tipo cálculo: %s", self.tipo_calculo)
        
        _logger.info("VOLÚMENES:")
        _logger.info("- Volumen B/N: %s", self.volumen_mensual_bn)
        _logger.info("- Volumen Color: %s", self.volumen_mensual_color)
        
        _logger.info("COSTOS:")
        _logger.info("- Costo B/N: %s", self.costo_copia_bn)
        _logger.info("- Costo Color: %s", self.costo_copia_color)
        
        _logger.info("CONFIGURACIÓN:")
        _logger.info("- Descuento: %s%%", self.descuento)
        _logger.info("- IGV: %s%%", self.igv)
        
        _logger.info("CAMPOS MANUALES:")
        _logger.info("- Monto mensual B/N: %s", self.monto_mensual_bn)
        _logger.info("- Monto mensual Color: %s", self.monto_mensual_color)
        _logger.info("- Monto mensual Total: %s", self.monto_mensual_total)
        
        _logger.info("RESULTADOS COMPANY:")
        _logger.info("- Renta mensual B/N: %s", self.renta_mensual_bn)
        _logger.info("- Renta mensual Color: %s", self.renta_mensual_color)
        _logger.info("- Subtotal sin IGV: %s", self.subtotal_sin_igv)
        _logger.info("- Monto IGV: %s", self.monto_igv)
        _logger.info("- Total facturar: %s", self.total_facturar_mensual)
        
        # CÁLCULO MANUAL PARA VERIFICAR
        _logger.info("🧮 VERIFICACIÓN MANUAL:")
        if self.tipo_calculo == 'auto':
            calc_bn = self.volumen_mensual_bn * self.costo_copia_bn
            calc_color = self.volumen_mensual_color * self.costo_copia_color
            _logger.info("- Cálculo manual B/N: %s × %s = %s", self.volumen_mensual_bn, self.costo_copia_bn, calc_bn)
            _logger.info("- Cálculo manual Color: %s × %s = %s", self.volumen_mensual_color, self.costo_copia_color, calc_color)
            subtotal_manual = calc_bn + calc_color
            igv_manual = subtotal_manual * (self.igv / 100.0)
            total_manual = subtotal_manual + igv_manual
            _logger.info("- Subtotal manual: %s", subtotal_manual)
            _logger.info("- IGV manual: %s", igv_manual)
            _logger.info("- Total manual: %s", total_manual)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug Company Completado',
                'message': f'Total: {self.total_facturar_mensual}. Ver logs para análisis completo.',
                'type': 'info',
                'sticky': True,
            }
        }

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


   

    def generar_sticker_corporativo(self, layout='horizontal'):
        """Abre el sticker en nueva ventana"""
        self.ensure_one()
        url = f'/sticker/generate/{self.id}?layout={layout}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
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
            
            qr.add_data(f"{base_url}/public/equipment_menu?copier_company_id={record.id}")
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

        
# Agregar al final del archivo models.py, después de la clase CopierRenewalHistory

class RemoteAssistanceRequest(models.Model):
    _name = 'remote.assistance.request'
    _description = 'Solicitudes de Asistencia Remota'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'
    _rec_name = 'display_name'

    # Campo computed para el nombre del registro
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('equipment_id', 'contact_name', 'assistance_type')
    def _compute_display_name(self):
        """Calcula el nombre a mostrar del registro"""
        _logger.info("=== INICIANDO _compute_display_name para asistencia remota ===")
        for record in self:
            try:
                equipment_name = record.equipment_id.name.name if record.equipment_id and record.equipment_id.name else 'Sin equipo'
                contact_name = record.contact_name or 'Sin contacto'
                assistance_type = dict(record._fields['assistance_type'].selection).get(record.assistance_type, 'Sin tipo')
                
                record.display_name = f"{equipment_name} - {contact_name} ({assistance_type})"
                _logger.info("Display name calculado para registro ID %s: %s", record.id, record.display_name)
            except Exception as e:
                _logger.error("Error calculando display_name para registro ID %s: %s", record.id, str(e))
                record.display_name = f"Solicitud {record.id or 'Nueva'}"

    # Campos básicos
    equipment_id = fields.Many2one(
        'copier.company',
        string='Equipo',
        required=True,
        tracking=True,
        help='Equipo para el cual se solicita asistencia remota'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='equipment_id.cliente_id',
        store=True,
        readonly=True
    )
    
    request_date = fields.Datetime(
        string='Fecha de Solicitud',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    secuencia = fields.Char(
        string='Número de Solicitud',
        default='New',
        copy=False,
        required=True,
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Sobrescribe create para asignar secuencia automática"""
        _logger.info("=== INICIANDO create para RemoteAssistanceRequest ===")
        _logger.info("Valores recibidos: %s", vals)
        
        try:
            # Asignar secuencia si es nueva
            if vals.get('secuencia', 'New') == 'New':
                vals['secuencia'] = self.env['ir.sequence'].next_by_code('remote.assistance.request') or 'RAR/001'
                _logger.info("Secuencia asignada: %s", vals['secuencia'])
            
            # Crear el registro
            result = super(RemoteAssistanceRequest, self).create(vals)
            _logger.info("Solicitud de asistencia remota creada: ID=%s, Secuencia=%s", result.id, result.secuencia)
            
            # Crear nota en el chatter
            try:
                result.message_post(
                    body=f"""
                    🆕 <b>Nueva Solicitud de Asistencia Remota</b><br/>
                    • <b>Equipo:</b> {result.equipment_id.name.name if result.equipment_id.name else 'Sin nombre'}<br/>
                    • <b>Serie:</b> {result.equipment_id.serie_id or 'Sin serie'}<br/>
                    • <b>Cliente:</b> {result.partner_id.name if result.partner_id else 'Sin cliente'}<br/>
                    • <b>Contacto:</b> {result.contact_name}<br/>
                    • <b>Tipo:</b> {dict(result._fields['assistance_type'].selection).get(result.assistance_type, 'Sin tipo')}<br/>
                    • <b>Estado:</b> Pendiente
                    """,
                    message_type='notification'
                )
                _logger.info("Nota creada en chatter para solicitud ID %s", result.id)
            except Exception as e:
                _logger.error("Error creando nota en chatter: %s", str(e))
            
            return result
            
        except Exception as e:
            _logger.exception("Error en create de RemoteAssistanceRequest: %s", str(e))
            raise

    # Información del contacto
    contact_name = fields.Char(
        string='Nombre de Contacto',
        required=True,
        tracking=True,
        help='Nombre completo de la persona que solicita asistencia'
    )
    
    contact_email = fields.Char(
        string='Email de Contacto',
        required=True,
        tracking=True,
        help='Email para contactar durante la asistencia'
    )
    
    contact_phone = fields.Char(
        string='Teléfono de Contacto',
        tracking=True,
        help='Teléfono para contactar si es necesario'
    )

    # Datos de acceso remoto
    anydesk_id = fields.Char(
        string='ID de AnyDesk',
        tracking=True,
        help='ID de AnyDesk del equipo (ej: 123456789)'
    )
    
    username = fields.Char(
        string='Usuario del Equipo',
        tracking=True,
        help='Nombre de usuario para acceder al equipo'
    )
    
    user_password = fields.Char(
        string='Clave de Usuario',
        help='Contraseña del usuario (se almacena de forma segura)'
    )

    # Para escáneres por correo
    scanner_email = fields.Char(
        string='Email del Escáner',
        tracking=True,
        help='Dirección de email configurada en el escáner'
    )
    
    scanner_password = fields.Char(
        string='Clave del Email del Escáner',
        help='Contraseña del email del escáner'
    )

    # Detalles del problema
    problem_description = fields.Text(
        string='Descripción del Problema',
        required=True,
        tracking=True,
        help='Descripción detallada del problema que requiere asistencia'
    )
    
    assistance_type = fields.Selection([
        ('general', 'Asistencia General'),
        ('scanner_email', 'Configuración Escáner por Email'),
        ('network', 'Problemas de Red'),
        ('drivers', 'Instalación de Drivers'),
        ('printing', 'Problemas de Impresión'),
        ('scanning', 'Problemas de Escaneo'),
        ('maintenance', 'Mantenimiento Preventivo'),
        ('other', 'Otro')
    ], string='Tipo de Asistencia', required=True, tracking=True, default='general')

    # Estado y gestión
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('scheduled', 'Programado'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Fallido')
    ], string='Estado', default='pending', tracking=True)

    priority = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='medium', tracking=True)

    # Técnico asignado
    technician_id = fields.Many2one(
        'res.users',
        string='Técnico Asignado',
        tracking=True,
        help='Técnico responsable de brindar la asistencia'
    )

    # Programación
    scheduled_datetime = fields.Datetime(
        string='Fecha/Hora Programada',
        tracking=True,
        help='Fecha y hora programada para la asistencia'
    )
    
    estimated_duration = fields.Float(
        string='Duración Estimada (horas)',
        default=1.0,
        tracking=True,
        help='Tiempo estimado para completar la asistencia'
    )

    # Seguimiento de la sesión
    session_start_time = fields.Datetime(
        string='Inicio de Sesión',
        tracking=True
    )
    
    session_end_time = fields.Datetime(
        string='Fin de Sesión',
        tracking=True
    )
    
    actual_duration = fields.Float(
        string='Duración Real (horas)',
        compute='_compute_actual_duration',
        store=True,
        help='Duración real de la sesión de asistencia'
    )

    @api.depends('session_start_time', 'session_end_time')
    def _compute_actual_duration(self):
        """Calcula la duración real de la sesión"""
        _logger.info("=== INICIANDO _compute_actual_duration ===")
        for record in self:
            try:
                if record.session_start_time and record.session_end_time:
                    delta = record.session_end_time - record.session_start_time
                    record.actual_duration = delta.total_seconds() / 3600.0  # Convertir a horas
                    _logger.info("Duración calculada para solicitud %s: %.2f horas", record.secuencia, record.actual_duration)
                else:
                    record.actual_duration = 0.0
                    _logger.info("Duración no calculable para solicitud %s (faltan fechas)", record.secuencia)
            except Exception as e:
                _logger.error("Error calculando duración para solicitud %s: %s", record.secuencia, str(e))
                record.actual_duration = 0.0

    # Notas y seguimiento
    internal_notes = fields.Text(
        string='Notas del Técnico',
        help='Notas internas para el equipo técnico'
    )
    
    remote_session_notes = fields.Text(
        string='Notas de la Sesión Remota',
        tracking=True,
        help='Detalles de lo realizado durante la sesión remota'
    )
    
    solution_description = fields.Text(
        string='Descripción de la Solución',
        tracking=True,
        help='Descripción de la solución implementada'
    )

    # Campos de auditoría
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
    )
    
    estimated_cost = fields.Monetary(
        string='Costo Estimado',
        currency_field='currency_id',
        help='Costo estimado de la asistencia (si aplica)'
    )
    
    actual_cost = fields.Monetary(
        string='Costo Real',
        currency_field='currency_id',
        tracking=True,
        help='Costo real de la asistencia'
    )

    # Campos relacionados para facilitar búsquedas
    equipment_serie = fields.Char(
        string='Serie del Equipo',
        related='equipment_id.serie_id',
        store=True,
        readonly=True
    )
    
    equipment_location = fields.Char(
        string='Ubicación del Equipo',
        related='equipment_id.ubicacion',
        store=True,
        readonly=True
    )

    # Métodos para cambiar estado
    def action_schedule(self):
        """Marca la solicitud como programada"""
        _logger.info("=== INICIANDO action_schedule para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'scheduled'
            self.message_post(
                body=f"📅 Solicitud programada para {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M') if self.scheduled_datetime else 'fecha por definir'}",
                message_type='notification'
            )
            _logger.info("Solicitud %s marcada como programada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_schedule para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_start_session(self):
        """Inicia la sesión de asistencia remota"""
        _logger.info("=== INICIANDO action_start_session para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'in_progress'
            self.session_start_time = fields.Datetime.now()
            self.message_post(
                body=f"🚀 Sesión de asistencia remota iniciada a las {self.session_start_time.strftime('%d/%m/%Y %H:%M')}",
                message_type='notification'
            )
            _logger.info("Sesión iniciada para solicitud %s", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_start_session para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_end_session(self):
        """Finaliza la sesión de asistencia remota"""
        _logger.info("=== INICIANDO action_end_session para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.session_end_time = fields.Datetime.now()
            duration_text = f"{self.actual_duration:.2f} horas" if self.actual_duration else "duración no calculable"
            self.message_post(
                body=f"✅ Sesión de asistencia remota finalizada a las {self.session_end_time.strftime('%d/%m/%Y %H:%M')} (Duración: {duration_text})",
                message_type='notification'
            )
            _logger.info("Sesión finalizada para solicitud %s, duración: %s", self.secuencia, duration_text)
        except Exception as e:
            _logger.exception("Error en action_end_session para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_complete(self):
        """Marca la solicitud como completada"""
        _logger.info("=== INICIANDO action_complete para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            if not self.session_end_time:
                self.session_end_time = fields.Datetime.now()
            self.state = 'completed'
            self.message_post(
                body="✅ Asistencia remota completada exitosamente",
                message_type='notification'
            )
            _logger.info("Solicitud %s marcada como completada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_complete para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_cancel(self):
        """Cancela la solicitud de asistencia"""
        _logger.info("=== INICIANDO action_cancel para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'cancelled'
            self.message_post(
                body="❌ Solicitud de asistencia remota cancelada",
                message_type='notification'
            )
            _logger.info("Solicitud %s cancelada", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_cancel para solicitud %s: %s", self.secuencia, str(e))
            raise

    def action_reset_to_pending(self):
        """Regresa la solicitud a estado pendiente"""
        _logger.info("=== INICIANDO action_reset_to_pending para solicitud %s ===", self.secuencia)
        try:
            self.ensure_one()
            self.state = 'pending'
            self.session_start_time = False
            self.session_end_time = False
            self.message_post(
                body="🔄 Solicitud regresada a estado pendiente",
                message_type='notification'
            )
            _logger.info("Solicitud %s regresada a pendiente", self.secuencia)
        except Exception as e:
            _logger.exception("Error en action_reset_to_pending para solicitud %s: %s", self.secuencia, str(e))
            raise

    @api.model
    def create_from_public_form(self, vals):
        """Método específico para crear desde formulario público"""
        _logger.info("=== INICIANDO create_from_public_form ===")
        _logger.info("Valores del formulario público: %s", vals)
        
        try:
            # Validaciones específicas para formulario público
            required_fields = ['equipment_id', 'contact_name', 'contact_email', 'problem_description', 'assistance_type']
            missing_fields = [field for field in required_fields if not vals.get(field)]
            
            if missing_fields:
                error_msg = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # Buscar o crear partner basado en email
            partner = self.env['res.partner'].sudo().search([('email', '=', vals['contact_email'])], limit=1)
            if partner:
                _logger.info("Partner encontrado para email %s: ID=%s", vals['contact_email'], partner.id)
            else:
                try:
                    partner = self.env['res.partner'].sudo().create({
                        'name': vals['contact_name'],
                        'email': vals['contact_email'],
                        'phone': vals.get('contact_phone', ''),
                        'is_company': False
                    })
                    _logger.info("Nuevo partner creado: ID=%s", partner.id)
                except Exception as e:
                    _logger.error("Error creando partner: %s", str(e))
            
            # Crear la solicitud
            assistance_request = self.create(vals)
            _logger.info("Solicitud de asistencia remota creada desde formulario público: ID=%s", assistance_request.id)
            
            # Crear actividad para el equipo técnico
            try:
                self._create_technical_activity(assistance_request)
            except Exception as e:
                _logger.error("Error creando actividad técnica: %s", str(e))
            
            return assistance_request
            
        except Exception as e:
            _logger.exception("Error en create_from_public_form: %s", str(e))
            raise

    def _create_technical_activity(self, assistance_request):
        """Crea una actividad para el equipo técnico"""
        _logger.info("=== INICIANDO _create_technical_activity para solicitud %s ===", assistance_request.secuencia)
        
        try:
            # Buscar usuarios del grupo técnico o asignar al técnico si ya está definido
            if assistance_request.technician_id:
                assignee = assistance_request.technician_id
                _logger.info("Asignando actividad al técnico definido: %s", assignee.name)
            else:
                # Buscar grupo técnico (esto depende de cómo tengas configurados los grupos)
                tech_group = self.env.ref('base.group_user', False)  # Ajustar según tu configuración
                if tech_group and tech_group.users:
                    assignee = tech_group.users[0]  # Asignar al primer usuario del grupo
                    _logger.info("Asignando actividad al primer usuario del grupo técnico: %s", assignee.name)
                else:
                    assignee = self.env.user
                    _logger.info("Asignando actividad al usuario actual: %s", assignee.name)
            
            activity_vals = {
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Nueva Solicitud de Asistencia Remota - {assistance_request.secuencia}',
                'note': f'''
                    🖥️ <b>Nueva Solicitud de Asistencia Remota</b><br/><br/>
                    
                    <b>Equipo:</b> {assistance_request.equipment_id.name.name if assistance_request.equipment_id.name else 'Sin nombre'}<br/>
                    <b>Serie:</b> {assistance_request.equipment_id.serie_id or 'Sin serie'}<br/>
                    <b>Cliente:</b> {assistance_request.partner_id.name if assistance_request.partner_id else 'Sin cliente'}<br/>
                    <b>Ubicación:</b> {assistance_request.equipment_location or 'Sin ubicación'}<br/><br/>
                    
                    <b>Contacto:</b> {assistance_request.contact_name}<br/>
                    <b>Email:</b> {assistance_request.contact_email}<br/>
                    <b>Teléfono:</b> {assistance_request.contact_phone or 'No proporcionado'}<br/><br/>
                    
                    <b>Tipo de Asistencia:</b> {dict(assistance_request._fields['assistance_type'].selection).get(assistance_request.assistance_type, 'Sin tipo')}<br/>
                    <b>Prioridad:</b> {dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media')}<br/><br/>
                    
                    <b>Descripción del Problema:</b><br/>
                    {assistance_request.problem_description}<br/><br/>
                    
                    <b>Datos de Acceso:</b><br/>
                    {'• AnyDesk ID: ' + assistance_request.anydesk_id + '<br/>' if assistance_request.anydesk_id else ''}
                    {'• Usuario: ' + assistance_request.username + '<br/>' if assistance_request.username else ''}
                    {'• Email Escáner: ' + assistance_request.scanner_email + '<br/>' if assistance_request.scanner_email else ''}
                    
                    Por favor, revisar y programar la asistencia remota.
                ''',
                'user_id': assignee.id,
                'res_id': assistance_request.id,
                'res_model_id': self.env['ir.model']._get('remote.assistance.request').id,
                'date_deadline': fields.Date.today() + timedelta(days=1)  # Plazo de 1 día
            }
            
            activity = self.env['mail.activity'].create(activity_vals)
            _logger.info("Actividad técnica creada: ID=%s para usuario %s", activity.id, assignee.name)
            
        except Exception as e:
            _logger.exception("Error en _create_technical_activity: %s", str(e))
            raise

    # Constrains para validaciones
    @api.constrains('contact_email')
    def _check_contact_email(self):
        """Valida el formato del email de contacto"""
        for record in self:
            if record.contact_email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.contact_email):
                    _logger.error("Email inválido para solicitud %s: %s", record.secuencia, record.contact_email)
                    raise ValidationError(f"El email '{record.contact_email}' no tiene un formato válido.")

    @api.constrains('scheduled_datetime')
    def _check_scheduled_datetime(self):
        """Valida que la fecha programada no sea en el pasado"""
        for record in self:
            if record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                _logger.error("Fecha programada en el pasado para solicitud %s: %s", record.secuencia, record.scheduled_datetime)
                raise ValidationError("La fecha programada no puede ser en el pasado.")

    @api.constrains('session_start_time', 'session_end_time')
    def _check_session_times(self):
        """Valida que la hora de fin sea posterior a la de inicio"""
        for record in self:
            if record.session_start_time and record.session_end_time:
                if record.session_end_time <= record.session_start_time:
                    _logger.error("Horas de sesión inválidas para solicitud %s: inicio=%s, fin=%s", 
                                record.secuencia, record.session_start_time, record.session_end_time)
                    raise ValidationError("La hora de fin de sesión debe ser posterior a la hora de inicio.")

