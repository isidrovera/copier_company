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
        


    qr_code = fields.Binary(string='Código QR', readonly=True)
    def generar_qr_code(self):
        icon_path = "D:\\copier_company\\static\\src\\img\\icono.png"  # Ruta al ícono
        base_url = "https://copiercompanysac.com//public/helpdesk_ticket"
        
        for record in self:
            # Datos para codificar en el código QR con URL completa
            data_to_encode = f"{base_url}?copier_company_id={record.id}"

            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Cargar el ícono y colocarlo en el centro del QR
            icon = Image.open(icon_path)
            icon_w, icon_h = icon.size
            qr_w, qr_h = qr_img.size
            icon_x = (qr_w - icon_w) // 2
            icon_y = (qr_h - icon_h) // 2
            qr_img.paste(icon, (icon_x, icon_y), icon)

            # Crear imagen para la etiqueta
            etiqueta = Image.new('RGB', (qr_w, qr_h + 60), 'white')
            draw = ImageDraw.Draw(etiqueta)

            # Usar la fuente predeterminada
            font = ImageFont.load_default()

            # Texto mejorado para la etiqueta
            texto_incidencias = ("Para reportar incidencias, escanee este código QR\n"
                                 "o contacte a nuestro equipo de soporte técnico.\n"
                                 "Correo: soporte@copiercompanysac.com\n"
                                 "Celular: +51 987 654 321\n"
                                 "WhatsApp: +51 987 654 321")

            # Dibujar texto en la parte inferior del QR
            draw.text((10, qr_h + 10), texto_incidencias, (0, 0, 0), font=font)

            # Pegar el QR en la etiqueta
            etiqueta.paste(qr_img, (0, 0))

            # Convertir a base64
            temp_buffer = io.BytesIO()
            etiqueta.save(temp_buffer, format="PNG")
            qr_base64 = base64.b64encode(temp_buffer.getvalue()).decode("utf-8")

            # Almacenar en el campo qr_code
            record.qr_code = qr_base64
