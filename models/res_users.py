from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Definición de campos usando fields
    signup_ip = fields.Char(
        string='IP de registro',
        readonly=True,
        copy=False,
        store=True,
        help='IP desde donde se registró el usuario'
    )
    
    signup_date = fields.Datetime(
        string='Fecha de registro',
        readonly=True,
        copy=False,
        store=True,
        help='Fecha y hora del registro'
    )
    
    signup_attempts = fields.Integer(
        string='Intentos de registro',
        default=0,
        readonly=True,
        copy=False,
        store=True,
        help='Número de intentos de registro'
    )

    @api.model
    def _check_signup_ip(self, ip_address):
        if not ip_address:
            return True
            
        ICP = self.env['ir.config_parameter'].sudo()
        attempts_key = f'signup_attempts_{ip_address}'
        attempts = int(ICP.get_param(attempts_key, '0'))
        
        if attempts >= 5:
            raise ValidationError(_("Demasiados intentos. Por favor espere una hora."))

        recent_signups = self.sudo().search_count([
            ('signup_ip', '=', ip_address),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
        ])
        
        if recent_signups > 0:
            raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))
        
        return True

    @api.model
    def signup(self, values, token=None):
        ip_address = self.env['ir.http'].get_ip()
        
        if ip_address:
            self._check_signup_ip(ip_address)
            values.update({
                'signup_ip': ip_address,
                'signup_date': fields.Datetime.now(),
                'signup_attempts': 1,
            })
            
        # Validación de email
        if values.get('login'):
            email = values['login'].lower()
            pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com$'
            if not re.match(pattern, email):
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo"))

        return super().signup(values, token)