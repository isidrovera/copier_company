from odoo import models, fields, api
import logging
import requests
import json
from datetime import datetime
import pytz

_logger = logging.getLogger(__name__)

class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    # Campos existentes
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(related='producto_id.serie_id', string='Serie', readonly=True)
    contometro_black = fields.Char('Contometro black')
    contometro_color = fields.Char('Contometro color')
    image = fields.Binary("Imagen", attachment=True, help="Imagen relacionada con el ticket.")
    nombre_reporta = fields.Char(string='Nombre de quien reporto')
    ubicacion = fields.Char(related='producto_id.ubicacion', readonly=True, store=True, string='Ubicacion')
    celular_reporta = fields.Char(string='Celular')
    responsable_mobile_clean = fields.Char(string='Número de celular (limpio)', compute='_compute_responsable_mobile_clean', store=True)
    
    # CAMPOS NUEVOS PARA EL FORMULARIO
    problem_type = fields.Selection([
        ('printing', 'Problemas de Impresión'),
        ('scanning', 'Problemas de Escaneo'),
        ('paper_jam', 'Atasco de Papel'),
        ('toner', 'Problemas de Toner'),
        ('network', 'Problemas de Red'),
        ('maintenance', 'Mantenimiento'),
        ('general', 'Otro Problema')
    ], string='Tipo de Problema', required=True, tracking=True)
    
    urgency = fields.Selection([
        ('low', 'Baja - Puede esperar'),
        ('medium', 'Media - Normal'),
        ('high', 'Alta - Urgente'),
        ('urgent', 'Crítica - Muy urgente')
    ], string='Nivel de Urgencia', default='medium', tracking=True)
    
    # Campo computed para descripción automática
    auto_description = fields.Text(
        string='Descripción Automática',
        compute='_compute_auto_description',
        store=True
    )
    
    # Campo para descripción adicional solo cuando es "general"
    additional_description = fields.Text(
        string='Descripción Adicional',
        help='Descripción detallada necesaria solo para "Otro Problema"'
    )
    
    @api.depends('problem_type')
    def _compute_auto_description(self):
        """Genera descripción automática basada en el tipo de problema"""
        problem_descriptions = {
            'printing': 'El equipo presenta problemas de impresión. Se requiere revisión técnica para identificar y solucionar la falla en el sistema de impresión.',
            'scanning': 'Se reportan problemas en la función de escaneo del equipo. Es necesaria una revisión técnica del módulo de escaneado.',
            'paper_jam': 'El equipo presenta atascos de papel frecuentes. Se requiere revisión del sistema de alimentación de papel y limpieza de rodillos.',
            'toner': 'Problemas relacionados con el toner o calidad de impresión. Puede requerir reemplazo de toner o revisión del sistema de impresión.',
            'network': 'El equipo presenta problemas de conectividad de red. Se requiere revisión de la configuración de red y conectividad.',
            'maintenance': 'Se solicita mantenimiento preventivo del equipo según el plan de mantenimiento programado.',
            'general': 'Problema general que requiere evaluación técnica específica.'
        }
        
        for record in self:
            if record.problem_type:
                record.auto_description = problem_descriptions.get(record.problem_type, 'Problema técnico reportado.')
            else:
                record.auto_description = False

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

    @api.model
    def create(self, vals):
        """Override create para manejar la descripción del ticket"""
        _logger.info("=== INICIANDO create de TicketCopier ===")
        _logger.info("Valores recibidos: %s", vals)
        
        try:
            # Si no hay descripción pero hay tipo de problema, usar la descripción automática
            if not vals.get('description') and vals.get('problem_type'):
                problem_descriptions = {
                    'printing': 'El equipo presenta problemas de impresión. Se requiere revisión técnica para identificar y solucionar la falla en el sistema de impresión.',
                    'scanning': 'Se reportan problemas en la función de escaneo del equipo. Es necesaria una revisión técnica del módulo de escaneado.',
                    'paper_jam': 'El equipo presenta atascos de papel frecuentes. Se requiere revisión del sistema de alimentación de papel y limpieza de rodillos.',
                    'toner': 'Problemas relacionados con el toner o calidad de impresión. Puede requerir reemplazo de toner o revisión del sistema de impresión.',
                    'network': 'El equipo presenta problemas de conectividad de red. Se requiere revisión de la configuración de red y conectividad.',
                    'maintenance': 'Se solicita mantenimiento preventivo del equipo según el plan de mantenimiento programado.',
                    'general': 'Problema general que requiere evaluación técnica específica.'
                }
                
                base_description = problem_descriptions.get(vals['problem_type'], 'Problema técnico reportado.')
                
                # Si es "general" y hay descripción adicional, combinar ambas
                if vals['problem_type'] == 'general' and vals.get('additional_description'):
                    vals['description'] = f"{base_description}\n\nDetalles adicionales:\n{vals['additional_description']}"
                else:
                    vals['description'] = base_description
                
                _logger.info("Descripción generada automáticamente: %s", vals['description'])
            
            # Si es tipo "general" pero hay descripción adicional, asegurar que se incluya
            elif vals.get('problem_type') == 'general' and vals.get('additional_description'):
                if vals.get('description'):
                    vals['description'] = f"{vals['description']}\n\nDetalles adicionales:\n{vals['additional_description']}"
                else:
                    vals['description'] = f"Problema general reportado.\n\nDetalles:\n{vals['additional_description']}"
            
            # Crear el ticket
            ticket = super(TicketCopier, self).create(vals)
            _logger.info("Ticket creado exitosamente: ID=%s", ticket.id)
            
            # Log de información del ticket creado
            _logger.info("Detalles del ticket - Tipo: %s, Urgencia: %s, Producto: %s", 
                        ticket.problem_type, ticket.urgency, 
                        ticket.producto_id.name.name if ticket.producto_id and ticket.producto_id.name else 'Sin producto')
            
            return ticket
            
        except Exception as e:
            _logger.exception("Error en create de TicketCopier: %s", str(e))
            raise

    def send_whatsapp_message(self, phone, message):
        url = 'https://whatsappapi.copiercompanysac.com/api/message'
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

    def send_confirmation_mail(self):
        """Envía el correo de confirmación de forma inmediata usando la plantilla definida."""
        # Se asume que la plantilla tiene external_id 'helpdesk.new_ticket_request_email_template'
        template = self.env.ref('helpdesk.new_ticket_request_email_template')
        if template:
            template.sudo().send_mail(self.id, force_send=True)
            # Forzamos el commit para que el correo se envíe de inmediato
            self.env.cr.commit()
        else:
            _logger.warning("No se encontró la plantilla de correo 'helpdesk.new_ticket_request_email_template'")

    def send_whatsapp_confirmation(self):
        """Envía el mensaje de WhatsApp de forma inmediata usando la lógica definida."""
        if self.celular_reporta:
            lima_tz = pytz.timezone('America/Lima')
            current_time = datetime.now(lima_tz)
            current_hour = current_time.hour

            if 5 <= current_hour < 12:
                saludo = "👋 Buenos días"
            elif 12 <= current_hour < 18:
                saludo = "👋 Buenas tardes"
            else:
                saludo = "👋 Buenas noches"

            # Mapear tipo de problema para el mensaje
            problem_names = {
                'printing': 'Problemas de Impresión',
                'scanning': 'Problemas de Escaneo', 
                'paper_jam': 'Atasco de Papel',
                'toner': 'Problemas de Toner',
                'network': 'Problemas de Red',
                'maintenance': 'Mantenimiento',
                'general': 'Problema General'
            }
            
            problem_name = problem_names.get(self.problem_type, 'Problema Técnico')

            message = (
                f"*🏢 Copier Company*\n\n"
                f"{saludo}, {self.nombre_reporta}.\n\n"
                f"Hemos recibido su reporte sobre el equipo:\n"
                f"🖨️ *Modelo:* {self.producto_id.name.name if self.producto_id and self.producto_id.name else 'No especificado'}\n"
                f"🔢 *Serie:* {self.serie_id or 'No especificada'}\n"
                f"⚠️ *Tipo de Problema:* {problem_name}\n"
                f"🚨 *Urgencia:* {dict(self._fields['urgency'].selection).get(self.urgency, 'Media')}\n\n"
                f"Nuestro equipo de soporte técnico se pondrá en contacto con usted pronto para brindarle la asistencia necesaria.\n"
                f"Gracias por confiar en Copier Company.\n\n"
                f"Atentamente,\n"
                f"📞 Soporte Técnico Copier Company\n"
                f"☎️ Tel: +51975399303\n"
                f"📧 Email: soporte@copiercompany.com"
            )
            phone = self.responsable_mobile_clean
            self.send_whatsapp_message(phone, message)