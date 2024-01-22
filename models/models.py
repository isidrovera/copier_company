# -*- coding: utf-8 -*-

from odoo import models, fields, api
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
        


    qr_code_with_icon = fields.Binary(string='Código QR con Icono', readonly=True)

    def generar_qr_con_icono(self):
        icon_path = "copier_company/static/src/img/icono.png"  # Actualiza con la ruta real al icono
        base_url = "https://copiercompanysac.com//public/helpdesk_ticket"
        
        for record in self:
            # Datos para codificar en el código QR con URL completa
            data_to_encode = f"{base_url}?copier_company_id={record.id}"

            # Generar el código QR con un espacio en el centro para el ícono
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Cargar el ícono y redimensionarlo
            icon = Image.open(icon_path)
            factor = 4  # Factor de reducción; ajusta según el tamaño del QR y el icono
            icon_size = (qr_img.size[0] // factor, qr_img.size[1] // factor)
            icon.thumbnail(icon_size, Image.ANTIALIAS)

            # Calcular la posición para centrar el ícono
            icon_pos = ((qr_img.size[0] - icon.size[0]) // 2, (qr_img.size[1] - icon.size[1]) // 2)

            # Insertar el ícono en el QR
            qr_img.paste(icon, icon_pos, icon)

            # Crear una imagen para el texto debajo del código QR
            texto_incidencias = ("Para reportar incidencias, escanee este código QR\n"
                                "o contacte a nuestro equipo de soporte técnico.\n"
                                "Correo: soporte@copiercompanysac.com\n"
                                "Celular: +51 987 654 321\n"
                                "WhatsApp: +51 987 654 321")
            # Definir la fuente y tamaño del texto
            font = ImageFont.load_default()
            # Si quieres usar una fuente específica, descomenta la siguiente línea y asegúrate de tener la ruta correcta
            # font = ImageFont.truetype("arial.ttf", 15)

            # Crear un objeto 'draw' para dibujar texto en la imagen
            draw = ImageDraw.Draw(qr_img)
            # Calcular el tamaño del texto
            text_size = draw.textsize(texto_incidencias, font=font)
            # Calcular la posición para el texto debajo del código QR
            text_x = (qr_img.size[0] - text_size[0]) // 2
            text_y = qr_img.size[1] - text_size[1]
            # Dibujar el texto en la imagen
            draw.text((text_x, text_y), texto_incidencias, font=font, fill="black")

            # Convertir la imagen del QR a Base64 para almacenamiento
            temp_buffer = io.BytesIO()
            qr_img.save(temp_buffer, format="PNG")
            qr_img_base64 = base64.b64encode(temp_buffer.getvalue()).decode("utf-8")

            # Almacenar en el campo qr_code_with_icon
            record.qr_code_with_icon = qr_img_base64
