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
        
        # Configuración de tamaño
        dpi = 300  # puntos por pulgada
        size_in_inches = 1.5  # tamaño deseado en pulgadas
        total_size_in_pixels = size_in_inches * dpi

        # Establecer bordes y calcular el tamaño de cada caja
        border = 4
        num_boxes_per_side = 21 + (2 * border)  # 21 cajas para la versión 1 del QR más los bordes
        box_size = (total_size_in_pixels - (2 * border * dpi / 25.4)) // num_boxes_per_side

        for record in self:
            data_to_encode = f"{base_url}?copier_company_id={record.id}"

            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)

            # Crear la imagen del código QR
            img = qr.make_image(fill_color="black", back_color="white")

            # Convertir la imagen a una cadena de bytes y almacenarla
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

            # Almacenar la imagen en el campo qr_code del registro
            record.qr_code = qr_image_base64