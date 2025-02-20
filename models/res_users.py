# models/res_users.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import re

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        ip_address = self.env['ir.http'].get_ip()
        
        # Validar límite por IP usando create_date
        if ip_address:
            # Verificar registros en las últimas 24 horas
            recent_signups = self.sudo().search_count([
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ])

            if recent_signups >= 1:
                raise ValidationError(_("Ya existe un registro desde esta IP en las últimas 24 horas."))

        # Validar email
        if values.get('login'):
            email = values['login'].lower()
            allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
            domain = email.split('@')[-1]

            if domain not in allowed_domains:
                raise ValidationError(_("Por favor use un correo de Gmail, Hotmail, Outlook o Yahoo."))

            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                raise ValidationError(_("Formato de correo electrónico inválido."))

        return super().signup(values, token)