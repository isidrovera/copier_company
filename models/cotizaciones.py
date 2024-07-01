# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import requests
from odoo.exceptions import UserError
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
        if len(self.identificacion_number) != 11:
            raise UserError(_('El número de RUC debe tener 11 dígitos.'))
        try:
            response = requests.get(f"https://api.sunat.cloud/ruc/{self.identificacion_number}")
            if response.status_code == 200:
                data = response.json()
                if 'razonSocial' in data:
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
                            'name': data['razonSocial'],
                            'street': data.get('direccion', ''),
                            'vat': self.identificacion_number,
                        }
                        partner = self.env['res.partner'].create(partner_vals)
                        self.empresa = partner.id
                        self.contacto = data.get('nombre', '')
                else:
                    _logger.warning(f"Datos no encontrados para el RUC: {self.identificacion_number}")
                    raise UserError(_('Datos no encontrados para el RUC proporcionado.'))
            else:
                _logger.error(f"Error al consultar el RUC en SUNAT: {response.text}")
                raise UserError(_('Error al consultar el RUC en SUNAT.'))
        except Exception as e:
            _logger.error(f"Error fetching data from SUNAT: {e}")
            raise UserError(_('Error al consultar el RUC en SUNAT.'))

    def _fetch_data_from_reniec(self):
        if not self.identificacion_number:
            return
        if len(self.identificacion_number) != 8:
            raise UserError(_('El número de DNI debe tener 8 dígitos.'))
        try:
            response = requests.get(f"https://api.apis.net.pe/v1/dni?numero={self.identificacion_number}")
            if response.status_code == 200:
                data = response.json()
                if 'nombres' in data and 'apellidoPaterno' in data and 'apellidoMaterno' in data:
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
                else:
                    _logger.warning(f"Datos no encontrados para el DNI: {self.identificacion_number}")
                    raise UserError(_('Datos no encontrados para el DNI proporcionado.'))
            else:
                _logger.error(f"Error al consultar el DNI en RENIEC: {response.text}")
                raise UserError(_('Error al consultar el DNI en RENIEC.'))
        except Exception as e:
            _logger.error(f"Error fetching data from RENIEC: {e}")
            raise UserError(_('Error al consultar el DNI en RENIEC.'))
