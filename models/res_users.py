# models/res_users.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    signup_ip = fields.Char(
        string='IP de registro',
        readonly=True,
        copy=False,
        store=True
    )
    signup_attempts = fields.Integer(
        string='Intentos de registro',
        default=0,
        readonly=True,
        copy=False,
        store=True
    )
    signup_blocked_until = fields.Datetime(
        string='Bloqueado hasta',
        readonly=True,
        copy=False,
        store=True
    )

    @api.model
    def signup(self, values, token=None):
        ip_address = self.env['ir.http'].get_ip()
        
        # Validar restricciones de IP
        self._validate_signup_ip(ip_address)
        
        # Validar email
        if values.get('login'):
            self._validate_signup_email(values['login'])

        # Registrar IP y contador
        values.update({
            'signup_ip': ip_address,
            'signup_attempts': 1
        })

        return super().signup(values, token)

    def _validate_signup_ip(self, ip_address):
        if not ip_address:
            return

        # Verificar si la IP está bloqueada
        blocked_user = self.sudo().search([
            ('signup_ip', '=', ip_address),
            ('signup_blocked_until', '>', fields.Datetime.now())
        ], limit=1)
        
        if blocked_user:
            raise ValidationError(_("Esta IP está temporalmente bloqueada por demasiados intentos. Por favor intente más tarde."))

        # Verificar registros en las últimas 24 horas
        recent_signups = self.sudo().search_count([
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ])

        if recent_signups >= 1:
            raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))

        # Verificar intentos fallidos
        failed_attempts = self.sudo().search([
            ('signup_ip', '=', ip_address),
            ('signup_attempts', '>', 0),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
        ])

        if len(failed_attempts) >= 5:
            # Bloquear IP por 1 hora
            blocked_until = fields.Datetime.now() + timedelta(hours=1)
            failed_attempts.write({'signup_blocked_until': blocked_until})
            raise ValidationError(_("Demasiados intentos de registro. IP bloqueada por 1 hora."))

    def _validate_signup_email(self, email):
        if not email:
            raise ValidationError(_("El correo electrónico es requerido."))

        email = email.lower()
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
        domain = email.split('@')[-1]

        if domain not in allowed_domains:
            raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo."))

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(_("Formato de correo electrónico inválido."))