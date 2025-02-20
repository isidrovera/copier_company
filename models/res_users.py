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
        store=True,
        help='IP desde donde se registró el usuario'
    )
    signup_attempts = fields.Integer(
        string='Intentos de registro',
        default=0,
        readonly=True,
        copy=False,
        store=True,
        help='Número de intentos de registro'
    )

    def _get_signup_attempts_key(self, ip_address):
        """Obtener clave para almacenar intentos por IP"""
        return f'signup_attempts_{ip_address}'

    @api.model
    def _check_signup_attempts(self, ip_address):
        """Verificar y actualizar intentos de registro por IP"""
        if not ip_address:
            return True

        ICP = self.env['ir.config_parameter'].sudo()
        attempts_key = self._get_signup_attempts_key(ip_address)
        current_attempts = int(ICP.get_param(attempts_key, '0'))

        # Incrementar intentos
        ICP.set_param(attempts_key, str(current_attempts + 1))

        # Si supera 5 intentos en una hora, bloquear
        if current_attempts >= 5:
            return False
        return True

    @api.model
    def _check_ip_history(self, ip_address):
        """Verificar historial de registros por IP"""
        recent_signups = self.sudo().search_count([
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ])
        return recent_signups < 1

    @api.model
    def _validate_email_domain(self, email):
        """Validar dominio del correo electrónico"""
        if not email:
            return False

        email = email.lower()
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
        domain = email.split('@')[-1]

        return domain in allowed_domains

    @api.model
    def signup(self, values, token=None):
        """Proceso de registro con validaciones"""
        # Obtener IP
        ip_address = self.env['ir.http'].get_ip()

        if ip_address:
            # Verificar intentos de registro
            if not self._check_signup_attempts(ip_address):
                raise ValidationError(_("Demasiados intentos. Por favor espere una hora."))

            # Verificar historial de IP
            if not self._check_ip_history(ip_address):
                raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))

            # Actualizar valores con IP
            values.update({
                'signup_ip': ip_address,
                'signup_attempts': 1
            })

        # Validar email
        if values.get('login'):
            if not self._validate_email_domain(values['login']):
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo."))

            # Validar formato del email
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, values['login'].lower()):
                raise ValidationError(_("Formato de correo electrónico inválido."))

        # Continuar con el proceso de registro
        return super().signup(values, token)

    @api.model
    def reset_signup_attempts(self):
        """Cron job para resetear intentos de registro"""
        ICP = self.env['ir.config_parameter'].sudo()
        attempt_params = ICP.search([('key', 'like', 'signup_attempts_%')])
        attempt_params.unlink()