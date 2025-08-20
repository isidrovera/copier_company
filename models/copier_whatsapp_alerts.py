# models/copier_whatsapp_alerts.py
from odoo import api, fields, models, _, exceptions
from datetime import datetime, timedelta
import logging
import requests
import json

_logger = logging.getLogger(__name__)

class CopierWhatsappAlert(models.Model):
    _name = 'copier.whatsapp.alert'
    _description = 'Gestión de Alertas WhatsApp para Stock de Máquinas'
    _order = 'create_date desc'

    # Información básica
    partner_id = fields.Many2one(
        'res.partner', 
        string='Distribuidor', 
        required=True,
        domain=[('is_distributor', '=', True)]
    )
    
    machine_id = fields.Many2one(
        'copier.stock', 
        string='Máquina Relacionada'
    )
    
    # Tipo de alerta
    alert_type = fields.Selection([
        ('new_stock', 'Nueva Máquina Disponible'),
        ('reservation_expiry', 'Reserva por Expirar'),
        ('machine_released', 'Máquina Liberada'),
        ('purchase_confirmed', 'Compra Confirmada'),
        ('weekly_catalog', 'Catálogo Semanal'),
        ('price_change', 'Cambio de Precio'),
    ], string='Tipo de Alerta', required=True)
    
    # Estado del envío
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='pending')
    
    # Detalles del mensaje
    message = fields.Text(string='Mensaje Enviado')
    phone_number = fields.Char(string='Número de Teléfono')
    sent_date = fields.Datetime(string='Fecha de Envío')
    error_message = fields.Text(string='Mensaje de Error')
    
    # Campos adicionales
    priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='normal')
    
    scheduled_date = fields.Datetime(string='Programado Para')
    attempts = fields.Integer(string='Intentos de Envío', default=0)
    max_attempts = fields.Integer(string='Máximo Intentos', default=3)

    def send_alert(self):
        """Enviar alerta por WhatsApp"""
        self.ensure_one()
        
        if self.status == 'sent':
            _logger.warning(f"Alerta {self.id} ya fue enviada")
            return False
            
        if self.attempts >= self.max_attempts:
            self.status = 'failed'
            self.error_message = 'Máximo número de intentos alcanzado'
            return False
        
        try:
            # Incrementar contador de intentos
            self.attempts += 1
            
            # Obtener número de teléfono
            phone = self._get_formatted_phone()
            if not phone:
                raise Exception('Número de teléfono no válido')
            
            # Preparar mensaje
            message = self._generate_message()
            if not message:
                raise Exception('No se pudo generar el mensaje')
            
            # Enviar por WhatsApp API
            success = self._send_whatsapp_message(phone, message)
            
            if success:
                self.write({
                    'status': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'phone_number': phone,
                    'message': message
                })
                _logger.info(f"Alerta {self.id} enviada exitosamente a {phone}")
                return True
            else:
                raise Exception('Error en el envío por API')
                
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"Error enviando alerta {self.id}: {error_msg}")
            
            self.write({
                'status': 'failed' if self.attempts >= self.max_attempts else 'pending',
                'error_message': error_msg
            })
            return False

    def _get_formatted_phone(self):
        """Obtener y formatear número de teléfono"""
        if not self.partner_id:
            return False
            
        # Usar whatsapp_phone si está disponible, sino mobile
        phone = self.partner_id.whatsapp_phone or self.partner_id.mobile
        if not phone:
            return False
            
        # Formatear número (eliminar espacios, + y caracteres especiales)
        phone = phone.strip().replace(' ', '').replace('+', '')
        phone = ''.join(filter(str.isdigit, phone))
        
        # Si no empieza con 51 y tiene 9 dígitos, agregar 51 (Perú)
        if not phone.startswith('51') and len(phone) == 9:
            phone = f'51{phone}'
            
        return phone if len(phone) >= 10 else False

    def _generate_message(self):
        """Generar mensaje según el tipo de alerta"""
        if self.alert_type == 'new_stock':
            return self._generate_new_stock_message()
        elif self.alert_type == 'reservation_expiry':
            return self._generate_expiry_message()
        elif self.alert_type == 'machine_released':
            return self._generate_released_message()
        elif self.alert_type == 'purchase_confirmed':
            return self._generate_purchase_message()
        elif self.alert_type == 'weekly_catalog':
            return self._generate_weekly_catalog()
        elif self.alert_type == 'price_change':
            return self._generate_price_change_message()
        return False

    def _generate_new_stock_message(self):
        """Mensaje para nueva máquina disponible"""
        if not self.machine_id:
            return False
            
        machine = self.machine_id
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = f"{base_url}/stock-maquinas/{machine.id}"
        
        return f"""🚨 ¡NUEVA MÁQUINA DISPONIBLE!

Hola {self.partner_id.name}!

Nueva máquina en stock:

📱 Marca: {machine.marca_id.name}
🖨️ Modelo: {machine.modelo_id.name}
💰 Precio: ${machine.sale_price:,.0f}
📊 Contómetro: {machine.contometro:,} copias
🎨 Tipo: {dict(machine._fields['tipo'].selection).get(machine.tipo)}
📍 Estado: Disponible

Ver detalles: {link}

¡Primera oportunidad para distribuidores!
Copier Company SAC"""

    def _generate_expiry_message(self):
        """Mensaje para reserva por expirar"""
        if not self.machine_id:
            return False
            
        machine = self.machine_id
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        payment_link = f"{base_url}/stock-maquinas/{machine.id}/payment"
        
        return f"""⚠️ TU RESERVA EXPIRA PRONTO

Hola {self.partner_id.name}!

Tu reserva está por vencer:

📱 Máquina: {machine.marca_id.name} {machine.modelo_id.name}
📋 Ref: {machine.name}
⏰ Expira en: {machine.days_left} día(s)

Para mantener tu reserva:
💳 Sube tu comprobante: {payment_link}
📞 Contáctanos: +51 999 888 777

¡No pierdas tu máquina!
Copier Company SAC"""

    def _generate_released_message(self):
        """Mensaje para máquina liberada"""
        if not self.machine_id:
            return False
            
        machine = self.machine_id
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = f"{base_url}/stock-maquinas/{machine.id}"
        
        return f"""🔄 MÁQUINA DISPONIBLE NUEVAMENTE

Hola {self.partner_id.name}!

Una máquina que estaba reservada ya está disponible:

📱 {machine.marca_id.name} {machine.modelo_id.name}
💰 Precio: ${machine.sale_price:,.0f}
📊 Contómetro: {machine.contometro:,}
🎨 {dict(machine._fields['tipo'].selection).get(machine.tipo)}

¡Corre! Los primeros tendrán la oportunidad.

Reservar: {link}

Copier Company SAC"""

    def _generate_purchase_message(self):
        """Mensaje de confirmación de compra"""
        if not self.machine_id:
            return False
            
        machine = self.machine_id
        
        return f"""✅ COMPRA CONFIRMADA

¡Felicidades {self.partner_id.name}!

Tu compra ha sido confirmada:

📱 Máquina: {machine.marca_id.name} {machine.modelo_id.name}
📋 Ref: {machine.name}
💰 Precio: ${machine.sale_price:,.0f}
📅 Fecha: {machine.sold_date.strftime('%d/%m/%Y')}

Próximos pasos:
📦 Coordinación de entrega
📋 Documentos de transferencia

Nuestro equipo se contactará contigo.

¡Gracias por confiar en nosotros!
Copier Company SAC"""

    def _generate_weekly_catalog(self):
        """Mensaje de catálogo semanal"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        catalog_link = f"{base_url}/stock-maquinas"
        
        # Obtener máquinas disponibles
        available_machines = self.env['copier.stock'].search([
            ('state', '=', 'available')
        ], order='tipo, marca_id, sale_price')
        
        if not available_machines:
            return f"""📋 CATÁLOGO SEMANAL

Hola {self.partner_id.name}!

Actualmente no tenemos máquinas disponibles en stock.

Próximamente estarán llegando nuevas máquinas.

Te notificaremos tan pronto estén disponibles.

Copier Company SAC"""
        
        # Separar por tipo
        monocromas = available_machines.filtered(lambda m: m.tipo == 'monocroma')
        color = available_machines.filtered(lambda m: m.tipo == 'color')
        
        message = f"""📋 CATÁLOGO SEMANAL

¡Hola {self.partner_id.name}! Máquinas disponibles:

"""
        
        # Sección monocromas
        if monocromas:
            message += f"""🖨️ MONOCROMAS ({len(monocromas)})
"""
            for machine in monocromas[:8]:  # Limitar a 8 para no hacer muy largo
                message += f"• {machine.modelo_id.name} - {machine.contometro:,} copias - ${machine.sale_price:,.0f}\n"
            
            if len(monocromas) > 8:
                message += f"• ... y {len(monocromas) - 8} más\n"
            message += "\n"
        
        # Sección color
        if color:
            message += f"""🎨 COLOR ({len(color)})
"""
            for machine in color[:8]:  # Limitar a 8
                message += f"• {machine.modelo_id.name} - {machine.contometro:,} copias - ${machine.sale_price:,.0f}\n"
            
            if len(color) > 8:
                message += f"• ... y {len(color) - 8} más\n"
            message += "\n"
        
        message += f"""📊 Total disponibles: {len(available_machines)}
💰 Rango precios: ${min(available_machines.mapped('sale_price')):,.0f} - ${max(available_machines.mapped('sale_price')):,.0f}

Ver catálogo completo: {catalog_link}

Copier Company SAC"""
        
        return message

    def _generate_price_change_message(self):
        """Mensaje para cambio de precio"""
        if not self.machine_id:
            return False
            
        machine = self.machine_id
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = f"{base_url}/stock-maquinas/{machine.id}"
        
        # Nota: Aquí necesitarías implementar lógica para guardar precios anteriores
        return f"""💰 PRECIO ACTUALIZADO!

¡Hola {self.partner_id.name}!

La máquina que viste tiene nuevo precio:

📱 {machine.marca_id.name} {machine.modelo_id.name}
💸 Precio actual: ${machine.sale_price:,.0f}

Detalles: {link}

¡Aprovecha esta oportunidad!
Copier Company SAC"""

    def _send_whatsapp_message(self, phone, message):
        """Enviar mensaje por WhatsApp API"""
        try:
            WHATSAPP_API_URL = 'https://whatsappapi.copiercompanysac.com/api/message'
            
            data = {
                'phone': phone,
                'type': 'text',
                'message': message
            }
            
            _logger.info("Enviando mensaje WhatsApp - Teléfono: %s", phone)
            
            response = requests.post(WHATSAPP_API_URL, data=data, timeout=30)
            
            _logger.info("Respuesta API WhatsApp: Status=%s, Contenido=%s", 
                        response.status_code, response.text)
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get('success', False)
            else:
                return False
                
        except Exception as e:
            _logger.error(f"Error en API WhatsApp: {str(e)}")
            return False

    @api.model
    def create_new_stock_alerts(self, machine_id):
        """Crear alertas para nueva máquina en stock"""
        machine = self.env['copier.stock'].browse(machine_id)
        if not machine.exists():
            return
            
        # Buscar distribuidores interesados
        distributors = self.env['res.partner'].search([
            ('is_distributor', '=', True),
            ('notify_new_stock', '=', True),
            ('active', '=', True)
        ])
        
        alerts = []
        for distributor in distributors:
            # Verificar si el distribuidor está interesado en este tipo de máquina
            if self._distributor_interested_in_machine(distributor, machine):
                alert_vals = {
                    'partner_id': distributor.id,
                    'machine_id': machine.id,
                    'alert_type': 'new_stock',
                    'priority': 'high',
                    'scheduled_date': fields.Datetime.now()
                }
                alerts.append(alert_vals)
        
        if alerts:
            created_alerts = self.create(alerts)
            # Enviar inmediatamente
            for alert in created_alerts:
                alert.send_alert()
                
        _logger.info(f"Creadas {len(alerts)} alertas para nueva máquina {machine.name}")

    @api.model
    def create_expiry_alerts(self):
        """Crear alertas para reservas por expirar (ejecutar diario)"""
        # Buscar máquinas que expiran en 2 días
        expiry_date = fields.Datetime.now() + timedelta(days=2)
        machines_expiring = self.env['copier.stock'].search([
            ('state', '=', 'reserved'),
            ('reservation_expiry_date', '!=', False),
            ('reservation_expiry_date', '<=', expiry_date),
            ('reservation_expiry_date', '>', fields.Datetime.now())
        ])
        
        alerts = []
        for machine in machines_expiring:
            if machine.reserved_by:
                # Verificar que no se haya enviado alerta reciente
                existing_alert = self.search([
                    ('partner_id', '=', machine.reserved_by.id),
                    ('machine_id', '=', machine.id),
                    ('alert_type', '=', 'reservation_expiry'),
                    ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24)),
                    ('status', '=', 'sent')
                ])
                
                if not existing_alert:
                    alert_vals = {
                        'partner_id': machine.reserved_by.id,
                        'machine_id': machine.id,
                        'alert_type': 'reservation_expiry',
                        'priority': 'urgent',
                        'scheduled_date': fields.Datetime.now()
                    }
                    alerts.append(alert_vals)
        
        if alerts:
            created_alerts = self.create(alerts)
            for alert in created_alerts:
                alert.send_alert()
                
        _logger.info(f"Creadas {len(alerts)} alertas de expiración")

    @api.model
    def create_weekly_catalog_alerts(self):
        """Crear alertas de catálogo semanal (ejecutar lunes)"""
        distributors = self.env['res.partner'].search([
            ('is_distributor', '=', True),
            ('notify_new_stock', '=', True),
            ('active', '=', True)
        ])
        
        alerts = []
        for distributor in distributors:
            alert_vals = {
                'partner_id': distributor.id,
                'alert_type': 'weekly_catalog',
                'priority': 'low',
                'scheduled_date': fields.Datetime.now()
            }
            alerts.append(alert_vals)
        
        if alerts:
            created_alerts = self.create(alerts)
            for alert in created_alerts:
                alert.send_alert()
                
        _logger.info(f"Creadas {len(alerts)} alertas de catálogo semanal")

    def _distributor_interested_in_machine(self, distributor, machine):
        """Verificar si el distribuidor está interesado en la máquina"""
        # Verificar tipo de máquina
        if distributor.preferred_types == 'monocroma' and machine.tipo != 'monocroma':
            return False
        elif distributor.preferred_types == 'color' and machine.tipo != 'color':
            return False
        
        # Por ahora no verificamos marcas preferidas ya que el campo está comentado
        # TODO: Descomentar cuando se active preferred_brands
        # if distributor.preferred_brands and machine.marca_id not in distributor.preferred_brands:
        #     return False
            
        return True

    @api.model
    def process_pending_alerts(self):
        """Procesar alertas pendientes (ejecutar cada 15 minutos)"""
        pending_alerts = self.search([
            ('status', '=', 'pending'),
            '|',
            ('scheduled_date', '<=', fields.Datetime.now()),
            ('scheduled_date', '=', False)
        ], limit=50)  # Procesar máximo 50 por vez
        
        for alert in pending_alerts:
            alert.send_alert()
            
        _logger.info(f"Procesadas {len(pending_alerts)} alertas pendientes")


# Extender modelo copier.stock para triggers automáticos
class CopierStock(models.Model):
    _inherit = 'copier.stock'

    @api.model
    def create(self, vals):
        """Override create para notificar nueva máquina"""
        result = super().create(vals)
        
        # Si se crea directamente como disponible, notificar
        if result.state == 'available':
            self.env['copier.whatsapp.alert'].create_new_stock_alerts(result.id)
            
        return result

    def write(self, vals):
        """Override write para detectar cambios de estado"""
        result = super().write(vals)
        
        # Detectar cambios a disponible
        if 'state' in vals and vals['state'] == 'available':
            for record in self:
                # Si era una máquina reservada que se liberó
                if record.reserved_by:
                    # Crear alerta de máquina liberada para otros distribuidores
                    self._create_machine_released_alerts(record)
                else:
                    # Nueva máquina disponible
                    self.env['copier.whatsapp.alert'].create_new_stock_alerts(record.id)
        
        # Detectar ventas confirmadas
        if 'state' in vals and vals['state'] == 'sold':
            for record in self:
                if record.reserved_by:
                    # Crear alerta de compra confirmada
                    self.env['copier.whatsapp.alert'].create([{
                        'partner_id': record.reserved_by.id,
                        'machine_id': record.id,
                        'alert_type': 'purchase_confirmed',
                        'priority': 'normal',
                        'scheduled_date': fields.Datetime.now()
                    }]).send_alert()
        
        return result

    def _create_machine_released_alerts(self, machine):
        """Crear alertas cuando se libera una máquina"""
        distributors = self.env['res.partner'].search([
            ('is_distributor', '=', True),
            ('notify_new_stock', '=', True),
            ('active', '=', True),
            ('id', '!=', machine.reserved_by.id)  # Excluir quien la tenía reservada
        ])
        
        alerts = []
        alert_model = self.env['copier.whatsapp.alert']
        for distributor in distributors:
            if alert_model._distributor_interested_in_machine(distributor, machine):
                alert_vals = {
                    'partner_id': distributor.id,
                    'machine_id': machine.id,
                    'alert_type': 'machine_released',
                    'priority': 'high',
                    'scheduled_date': fields.Datetime.now()
                }
                alerts.append(alert_vals)
        
        if alerts:
            created_alerts = alert_model.create(alerts)
            for alert in created_alerts:
                alert.send_alert()


# Extender res.partner para agregar relación con alertas (campos ya existen)
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    whatsapp_alert_ids = fields.One2many(
        'copier.whatsapp.alert',
        'partner_id',
        string='Alertas WhatsApp'
    )
    
    whatsapp_alert_count = fields.Integer(
        string='Total Alertas',
        compute='_compute_whatsapp_alert_count'
    )

    @api.depends('whatsapp_alert_ids')
    def _compute_whatsapp_alert_count(self):
        for partner in self:
            partner.whatsapp_alert_count = len(partner.whatsapp_alert_ids)

    def action_view_whatsapp_alerts(self):
        """Ver alertas WhatsApp de este distribuidor"""
        self.ensure_one()
        
        return {
            'name': f'Alertas WhatsApp - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.whatsapp.alert',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }