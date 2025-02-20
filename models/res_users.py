# models/res_users.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Definimos los campos que queremos añadir
    signup_ip = fields.Char('IP de registro', readonly=True, copy=False)
    signup_date = fields.Datetime('Fecha de registro', readonly=True, copy=False)
    signup_attempts = fields.Integer('Intentos de registro', default=0, readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Obtener IP actual
            ip_address = self.env['ir.http'].get_ip() if self.env['ir.http'] else False
            if ip_address:
                vals.update({
                    'signup_ip': ip_address,
                    'signup_date': fields.Datetime.now(),
                    'signup_attempts': 1,
                })
        return super().create(vals_list)

    @api.model
    def _get_signup_attempts_key(self, ip_address):
        """Obtener clave para los intentos de registro"""
        return f'signup_attempts_{ip_address}'

    @api.model
    def _check_signup_ip(self, ip_address):
        """Verificar restricciones de IP"""
        if not ip_address:
            return True

        ICP = self.env['ir.config_parameter'].sudo()
        
        # Verificar intentos en la última hora
        attempts_key = self._get_signup_attempts_key(ip_address)
        attempts = int(ICP.get_param(attempts_key, '0'))
        
        if attempts >= 5:
            raise ValidationError(_("Demasiados intentos. Por favor espere una hora."))

        # Verificar registros exitosos en las últimas 24 horas
        domain = [
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ]
        recent_signups = self.sudo().search_count(domain)
        
        if recent_signups > 0:
            raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))
        
        return True

    @api.model
    def _increment_signup_attempts(self, ip_address):
        """Incrementar contador de intentos"""
        if not ip_address:
            return

        ICP = self.env['ir.config_parameter'].sudo()
        attempts_key = self._get_signup_attempts_key(ip_address)
        current_attempts = int(ICP.get_param(attempts_key, '0'))
        ICP.set_param(attempts_key, str(current_attempts + 1))

    @api.model
    def signup(self, values, token=None):
        """Sobreescribir método de registro"""
        # Obtener IP
        ip_address = self.env['ir.http'].get_ip() if self.env['ir.http'] else False
        
        # Validar IP si está disponible
        if ip_address:
            self._check_signup_ip(ip_address)
            self._increment_signup_attempts(ip_address)
        
        # Validar formato de email
        if values.get('login'):
            email = values['login'].lower()
            pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com$'
            if not re.match(pattern, email):
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo"))
        
        return super(ResUsers, self).signup(values, token)