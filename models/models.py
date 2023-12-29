# -*- coding: utf-8 -*-

from odoo import models, fields, api
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
        for record in self:
            # Crear una cadena de datos que quieras codificar en el código QR
            data_to_encode = f"Registro de Máquina: {record.serie_id}, Cliente: {record.cliente_id.name}"

            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)

            # Crear una imagen del código QR en formato PNG
            img = qr.make_image(fill_color="black", back_color="white")

            # Convertir la imagen en una cadena de bytes y almacenarla en el campo qr_code
            qr_image = img.get_image()
            img_byte_array = io.BytesIO()
            qr_image.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
            record.qr_code = qr_image_base64
