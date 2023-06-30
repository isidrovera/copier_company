# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CotizacionAlquiler(models.Model):
    _name = 'cotizacion.alquiler'
    _inherit = ['mail.thread']
    _description = 'En este formulario se crearan cotizaciones de alquiler'
    marca_id = fields.Many2one('marcas.maquinas',string='Marca', help='Indique que marca en especifica esta interesado')
    tipo = fields.Selection(string='Tipo de impresora', selection=[('monocroma', 'Blanco y negro'),('color','Color')],
    default='monocroma',    help='Aqui elija que tipo de equipo multifuncional necesita si blanco y negro o colo.'  )
    cantidad = fields.Char(string='Cantidad mensual',help='Indique la cantidad que realiza mensual, copias + impresión')
    name = fields.Char( 'Formulario N°', default='New',
        copy=False,
        required=True,
        readonly=True)
    
    @api.model
    def create(self, vals):
        # We generate a standard reference
        vals['name'] = self.env['ir.sequence'].next_by_code('cotizacion.alquiler')or '/'
        return super(CotizacionAlquiler,self).create(vals)  
    empresa = fields.Char(string='Nombre de empresa')
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Telefono')
    correo = fields.Char(string='Correo')
    detalles = fields.Text(string='Detalle')
    formato = fields.Selection(string='Formato', selection=[('a4', 'A4'),('a3','A3')], default='a3',  help='Elija el formato de papel ')
    @api.model
    def create_cotizacion(self):
        vals = {
            'marca_id': self.marca_id.id,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'name': self.name,
            'empresa': self.empresa,
            'contacto': self.contacto,
            'celular': self.celular,
            'correo': self.correo,
            'detalles': self.detalles,
            'formato': self.formato,
        }
        self.env['cotizacion.alquiler'].create(vals)