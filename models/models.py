from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource
import qrcode
import base64
import io
from dateutil import tz
from datetime import datetime
from PIL import Image
import os
import re
from odoo.exceptions import UserError

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
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", 
                                   currency_field='currency_id',
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
    descuento = fields.Float(string='Descuento (%)', default=0.0)
    
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
                'costo_copia_bn', 'igv', 'descuento')
    def _compute_renta_mensual(self):
        for record in self:
            renta_color = record.volumen_mensual_color * record.costo_copia_color
            renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
            subtotal = renta_color + renta_bn
            
            descuento = subtotal * (record.descuento / 100.0)
            subtotal_con_descuento = subtotal - descuento
            igv = subtotal_con_descuento * (record.igv / 100.0)
            
            record.renta_mensual_color = renta_color
            record.renta_mensual_bn = renta_bn
            record.total_facturar_mensual = subtotal_con_descuento + igv

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

    def generar_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_path = get_module_resource('copier_company', 'static', 'src', 'img', 'logo.png')
        
        if not os.path.isfile(logo_path):
            raise FileNotFoundError(f"Logo no encontrado: {logo_path}")
            
        logo = Image.open(logo_path)
        logo_size = (100, int((float(logo.size[1]) * float(100/float(logo.size[0])))))
        logo = logo.resize(logo_size, Image.ANTIALIAS)
        
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
            
            # Reducir tamaño del QR
            qr_img = qr_img.resize((qr_img.size[0] // 2, qr_img.size[1] // 2), Image.ANTIALIAS)
            
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            record.qr_code = base64.b64encode(buffer.getvalue())

    def action_print_report(self):
        return self.env.ref('copier_company.action_report_report_cotizacion_alquiler').report_action(self)
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
