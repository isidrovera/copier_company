# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from PIL import Image, ImageDraw, ImageFont
import logging
import qrcode
import base64
import io


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
   # _rec_name = 'serie_id'

    
    
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