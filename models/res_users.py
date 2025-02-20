from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Definir campos nuevos
    signup_ip = fields.Char(
        string='IP de registro',
        help='IP desde donde se registró el usuario'
    )
    
    signup_attempts = fields.Integer(
        string='Intentos de registro',
        default=0,
        help='Número de intentos de registro'
    )

    # Sobreescribir método de signup
    @api.model
    def signup(self, values, token=None):
        ip_address = self.env['ir.http'].get_ip()
        if values.get('login'):
            # Validar correo
            email = values['login'].lower()
            if not self._validate_signup_email(email):
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo"))
            
            # Validar IP si está disponible
            if ip_address:
                # Verificar registros previos
                if self._check_signup_ip(ip_address):
                    values.update({
                        'signup_ip': ip_address,
                        'signup_attempts': 1
                    })
                else:
                    raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas"))

        return super().signup(values, token)

    def _validate_signup_email(self, email):
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
        domain = email.split('@')[-1].lower()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return domain in allowed_domains and bool(re.match(pattern, email))

    def _check_signup_ip(self, ip_address):
        recent_signups = self.sudo().search_count([
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ])
        return recent_signups == 0