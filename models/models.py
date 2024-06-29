# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
from PIL import Image, ImageDraw, ImageFont
import logging
import qrcode
import base64
import io
from dateutil.relativedelta import relativedelta

class CopierDuracion(models.Model):
    _name = 'copier.duracion'
    _description = 'Duración del Alquiler'

    name = fields.Char(string='Duración', required=True)

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se registran las maquinas que estan en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Many2one('modelos.maquinas', string='Maquina')
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas', string='Marca', required=True, related='name.marca_id')
    contometro = fields.Char(string='Contometro Inicial')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    ubicacion = fields.Char(string='Ubicación')
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado = fields.Many2one('copier.estados', string='Estado')
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler")
    duracion_alquiler = fields.Many2one('copier.duracion', string="Duración del Alquiler")
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)
    
    moneda_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self._default_currency())
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", currency_field='moneda_id')
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", currency_field='moneda_id')
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")
    qr_code = fields.Binary(string='Código QR', readonly=True)
    
    @api.model
    def _default_currency(self):
        client_country = self.env['res.partner'].browse(self._context.get('default_cliente_id', False)).country_id
        if client_country:
            currency = self.env['res.currency'].search([('country_ids', '=', client_country.id)], limit=1)
            if currency:
                return currency.id
        return self.env.company.currency_id.id

    @api.depends('fecha_inicio_alquiler', 'duracion_alquiler')
    def _calcular_fecha_fin(self):
        for record in self:
            if record.fecha_inicio_alquiler and record.duracion_alquiler:
                start_date = fields.Date.from_string(record.fecha_inicio_alquiler)
                if record.duracion_alquiler.name == '6_meses':
                    record.fecha_fin_alquiler = start_date + relativedelta(months=+6)
                elif record.duracion_alquiler.name == '1_año':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+1)
                elif record.duracion_alquiler.name == '2_años':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+2)

    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket']
        ticket_id = ticket.create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            'name': "Actualizar",
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

    def generar_qr_code(self):
        base_url = "https://copiercompanysac.com/public/helpdesk_ticket"
        dpi = 300
        inches_for_qr = 1.5 / 4
        pixels_for_qr = int(dpi * inches_for_qr)
        version_size = 21
        box_size = max(1, pixels_for_qr // (version_size + (2 * 4)))
        
        for record in self:
            data_to_encode = f"{base_url}?copier_company_id={record.id}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
            record.qr_code = qr_image_base64

def migrate_duracion_alquiler(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    duracion_model = env['copier.duracion']
    
    duraciones = [
        {'name': '6_meses'},
        {'name': '1_año'},
        {'name': '2_años'}
    ]
    for duracion in duraciones:
        duracion_model.create(duracion)

    records = env['copier.company'].search([])
    for record in records:
        if record.duracion_alquiler == '6_meses':
            duracion_id = duracion_model.search([('name', '=', '6_meses')], limit=1)
        elif record.duracion_alquiler == '1_año':
            duracion_id = duracion_model.search([('name', '=', '1_año')], limit=1)
        elif record.duracion_alquiler == '2_años':
            duracion_id = duracion_model.search([('name', '=', '2_años')], limit=1)
        
        if duracion_id:
            record.duracion_alquiler = duracion_id.id

def pre_init_hook(cr):
    migrate_duracion_alquiler(cr, registry)