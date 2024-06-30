# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class CotizacionAlquiler(models.Model):
    _name = 'cotizacion.alquiler'
    _inherit = ['mail.thread']
    _description = 'En este formulario se crearan cotizaciones de alquiler'

    marca_id = fields.Many2one('marcas.maquinas', string='Marca', help='Indique que marca en especifica esta interesado')
    tipo = fields.Selection(string='Tipo de impresora', selection=[('monocroma', 'Blanco y negro'), ('color', 'Color')],
                            default='monocroma', help='Aqui elija que tipo de equipo multifuncional necesita si blanco y negro o color.')
    cantidad = fields.Char(string='Cantidad mensual', help='Indique la cantidad que realiza mensual, copias + impresión')
    name = fields.Char('Formulario N°', default='New', copy=False, required=True, readonly=True)
    empresa = fields.Many2one('res.partner', string='Nombre de empresa')
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Telefono')
    correo = fields.Char(string='Correo')
    detalles = fields.Text(string='Detalle')
    formato = fields.Selection(string='Formato', selection=[('a4', 'A4'), ('a3', 'A3')], default='a3', help='Elija el formato de papel')
    identificacion_type = fields.Selection([
        ('ruc', 'RUC'),
        ('dni', 'DNI')
    ], string="Tipo de identificación", required=True)
    identificacion_number = fields.Char(string='Número de Identificación', required=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cotizacion.alquiler') or '/'
        return super(CotizacionAlquiler, self).create(vals)

    @api.onchange('identificacion_type', 'identificacion_number')
    def _onchange_identificacion(self):
        if self.identificacion_type and self.identificacion_number:
            if self.identificacion_type == 'ruc':
                self._fetch_data_from_sunat()
            elif self.identificacion_type == 'dni':
                self._fetch_data_from_reniec()

    def _fetch_data_from_sunat(self):
        if not self.identificacion_number:
            return
        try:
            response = requests.get(f"https://api.sunat.cloud/ruc/{self.identificacion_number}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    existing_partner = self.env['res.partner'].search([('vat', '=', self.identificacion_number)], limit=1)
                    if existing_partner:
                        self.empresa = existing_partner.id
                        return {
                            'warning': {
                                'title': "Cliente existente",
                                'message': "El cliente ya existe en el sistema.",
                            }
                        }
                    else:
                        partner_vals = {
                            'name': data['razon_social'],
                            'street': data['domicilio_fiscal']['direccion'],
                            'vat': self.identificacion_number,
                        }
                        partner = self.env['res.partner'].create(partner_vals)
                        self.empresa = partner.id
                        self.contacto = data['representante_legal']['nombre']
        except Exception as e:
            _logger.error(f"Error fetching data from SUNAT: {e}")

    def _fetch_data_from_reniec(self):
        if not self.identificacion_number:
            return
        try:
            response = requests.get(f"https://api.apis.net.pe/v1/dni?numero={self.identificacion_number}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    existing_partner = self.env['res.partner'].search([('vat', '=', self.identificacion_number)], limit=1)
                    if existing_partner:
                        self.empresa = existing_partner.id
                        return {
                            'warning': {
                                'title': "Cliente existente",
                                'message': "El cliente ya existe en el sistema.",
                            }
                        }
                    else:
                        partner_vals = {
                            'name': f"{data['nombres']} {data['apellidoPaterno']} {data['apellidoMaterno']}",
                            'vat': self.identificacion_number,
                        }
                        partner = self.env['res.partner'].create(partner_vals)
                        self.empresa = partner.id
                        self.contacto = f"{data['nombres']} {data['apellidoPaterno']} {data['apellidoMaterno']}"
        except Exception as e:
            _logger.error(f"Error fetching data from RENIEC: {e}")
