# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import requests
import socket
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
       
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Telefono')
    correo = fields.Char(string='Correo')
    detalles = fields.Text(string='Detalle')
    formato = fields.Selection(string='Formato', selection=[('a4', 'A4'), ('a3', 'A3')], default='a3', help='Elija el formato de papel')
    