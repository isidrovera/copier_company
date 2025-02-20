from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    signup_ip = fields.Char('IP de registro')
    signup_date = fields.Datetime('Fecha de registro')
    signup_attempts = fields.Integer('Intentos de registro', default=0, readonly=True)

    @api.model
    def _get_ip_attempts_key(self, ip_address):
        return f'signup_attempts_{ip_address}'

    @api.model
    def _check_signup_ip(self, ip_address):
        ICP = self.env['ir.config_parameter'].sudo()
        
        # Verificar intentos en la última hora
        attempts_key = self._get_signup_attempts_key(ip_address)
        attempts = int(ICP.get_param(attempts_key, '0'))
        
        if attempts >= 5:  # Máximo 5 intentos por hora
            raise ValidationError(_("Demasiados intentos. Por favor espere una hora."))

        # Verificar registros exitosos en las últimas 24 horas
        recent_signups = self.sudo().search_count([
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ])
        
        if recent_signups > 0:
            raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))
        
        return True

    @api.model
    def _increment_signup_attempts(self, ip_address):
        ICP = self.env['ir.config_parameter'].sudo()
        attempts_key = self._get_signup_attempts_key(ip_address)
        current_attempts = int(ICP.get_param(attempts_key, '0'))
        ICP.set_param(attempts_key, str(current_attempts + 1))

    @api.model
    def signup(self, values, token=None):
        # Obtener IP
        ip_address = self.env['ir.http'].get_ip()
        
        # Validar IP y dominio de correo
        self._check_signup_ip(ip_address)
        
        # Validar formato de email
        if 'login' in values:
            email = values['login'].lower()
            pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com$'
            if not re.match(pattern, email):
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo"))
        
        # Actualizar datos del registro
        values.update({
            'signup_ip': ip_address,
            'signup_date': fields.Datetime.now(),
        })
        
        # Incrementar contador de intentos
        self._increment_signup_attempts(ip_address)
        
        return super(ResUsers, self).signup(values, token)