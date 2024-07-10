from odoo import models, fields, api
import logging
import requests
import json
from datetime import datetime
import pytz

_logger = logging.getLogger(__name__)

class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(related='producto_id.serie_id', string='Serie', readonly=True)
    image = fields.Binary("Imagen", attachment=True, help="Imagen relacionada con el ticket.")
    nombre_reporta = fields.Char(string='Nombre de quien reporto')
    ubicacion = fields.Char(related='producto_id.ubicacion', readonly=True, store=True, string='Ubicacion')
    celular_reporta = fields.Char(string='Celular')
    responsable_mobile_clean = fields.Char(string='Número de celular (limpio)', compute='_compute_responsable_mobile_clean', store=True)

    @api.depends('celular_reporta')
    def _compute_responsable_mobile_clean(self):
        for record in self:
            if record.celular_reporta:
                phone = record.celular_reporta.replace('+', '').replace(' ', '')
                if not phone.startswith('51'):
                    phone = '51' + phone
                record.responsable_mobile_clean = phone
            else:
                record.responsable_mobile_clean = ''

    def send_whatsapp_message(self, phone, message):
        url = 'https://whatsappapi.copiercompanysac.com/lead'
        data = {
            'phone': phone,
            'message': message
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=data)
        
        _logger.info("Código de estado: %s", response.status_code)
        _logger.info("Respuesta de la API: %s", response.text)
        
        try:
            response_json = response.json()
            _logger.info("Respuesta JSON: %s", response_json)
            return response_json
        except json.JSONDecodeError as e:
            error_msg = f"La respuesta no contiene un JSON válido: {str(e)}"
            _logger.error(error_msg)
            return {"error": error_msg}

    @api.model
    def create(self, vals):
        ticket = super(TicketCopier, self).create(vals)
        if ticket.celular_reporta:
            lima_tz = pytz.timezone('America/Lima')
            current_time = datetime.now(lima_tz)
            current_hour = current_time.hour

            if 5 <= current_hour < 12:
                saludo = "👋 Buenos días"
            elif 12 <= current_hour < 18:
                saludo = "👋 Buenas tardes"
            else:
                saludo = "👋 Buenas noches"

            message = (f"*🏢 Copier Company*\n\n"
                       f"{saludo}, {ticket.nombre_reporta}.\n\n"
                       f"Hemos recibido su reporte sobre el equipo:\n"
                       f"🖨️ *Modelo:* {ticket.producto_id.name.name}\n"
                       f"🔢 *Serie:* {ticket.serie_id}\n"
                       f"⚠️ *Problema:* {ticket.name}\n\n"
                       f"Nuestro equipo de soporte técnico se pondrá en contacto con usted pronto para brindarle la asistencia necesaria.\n"
                       f"Gracias por confiar en Copier Company.\n\n"
                       f"Atentamente,\n"
                       f"📞 Soporte Técnico Copier Company\n"
                       f"☎️ Tel: +51975399303\n"
                       f"📧 Email: soporte@copiercompany.com")

            phone = ticket.responsable_mobile_clean
            ticket.send_whatsapp_message(phone, message)
        return ticket
