# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from PIL import Image, ImageDraw, ImageFont
import logging
import qrcode
import base64
import io
from dateutil.relativedelta import relativedelta

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se registran las maquinas que estan en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']
       
    name = fields.Many2one('modelos.maquinas',string='Maquina')
    
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca', required=True,related='name.marca_id')
    cliente_id = fields.Many2one('res.partner',string='Cliente', required=True, )
    ubicacion = fields.Char(string='Ubicación')
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado_maquina = fields.Selection([
        ('disponible', 'Disponible'),
        ('alquilada', 'Alquilada'),
        ('mantenimiento', 'En Mantenimiento')
    ], string="Estado de la Máquina", default='disponible', tracking=True)
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler")
    duracion_alquiler = fields.Selection([
        ('6_meses', '6 Meses'),
        ('1_año', '1 Año'),
        ('2_años', '2 Años')
    ], string="Duración del Alquiler", default='1_año')
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)
    @api.model
    def _default_currency(self):
        # Aquí puedes incluir lógica para elegir la moneda basada en otros aspectos, como el cliente.
        # Ejemplo: seleccionar la moneda del país del cliente si está disponible
        client_country = self.env['res.partner'].browse(self._context.get('default_cliente_id', False)).country_id
        if client_country:
            currency = self.env['res.currency'].search([('country_ids', '=', client_country.id)], limit=1)
            if currency:
                return currency.id
        return self.env.company.currency_id.id

    moneda_id = fields.Many2one('res.currency', string='Moneda', default=_default_currency)
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", currency_field='moneda_id')
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", currency_field='moneda_id')
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")

    @api.depends('fecha_inicio_alquiler', 'duracion_alquiler')
    def _calcular_fecha_fin(self):
        for record in self:
            if record.fecha_inicio_alquiler and record.duracion_alquiler:
                start_date = fields.Date.from_string(record.fecha_inicio_alquiler)
                if record.duracion_alquiler == '6_meses':
                    record.fecha_fin_alquiler = start_date + relativedelta(months=+6)
                elif record.duracion_alquiler == '1_año':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+1)
                elif record.duracion_alquiler == '2_años':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+2)


    
    
    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket']
        ticket_id = ticket.create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            'name':"Actualizar",
            

        })
        return {
            'name': 'Registro',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',

        }
        


    qr_code = fields.Binary(string='Código QR', readonly=True)
    def generar_qr_code(self):
        base_url = "https://copiercompanysac.com//public/helpdesk_ticket"
        # Asumiendo una impresión de 300 DPI, calcula el box_size para un tamaño de 1.5 pulgadas
        # Para una cuarta parte de ese tamaño, dividimos por 4
        dpi = 300
        inches_for_qr = 1.5 / 4  # Una cuarta parte de 1.5 pulgadas
        pixels_for_qr = int(dpi * inches_for_qr)
        
        # El tamaño del código QR debe ser suficiente para que quepan todos los datos
        # La versión 1 de QR (21x21) podría ser muy pequeña para algunos datos
        # Puede que necesites ajustar la versión para que quepa tu URL
        version_size = 21  # Tamaño de la versión 1 de QR
        box_size = max(1, pixels_for_qr // (version_size + (2 * 4)))  # Asegurarse de que box_size no sea 0

        for record in self:
            data_to_encode = f"{base_url}?copier_company_id={record.id}"

            qr = qrcode.QRCode(
                version=1,  # Puede que necesites aumentar esto si el QR no genera correctamente
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=4,  # Un borde típico
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

            record.qr_code = qr_image_base64