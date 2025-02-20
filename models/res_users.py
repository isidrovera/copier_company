from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ResUsers(models.Model):
    _inherit = 'res.users'

    signup_ip = fields.Char('IP de registro')
    
    @api.model
    def _get_ip_attempts(self, ip):
        param_name = f'signup_attempts_{ip}'
        attempts = self.env['ir.config_parameter'].sudo().get_param(param_name, '0')
        return int(attempts)

    @api.model
    def _record_signup_attempt(self, ip):
        param_name = f'signup_attempts_{ip}'
        attempts = self._get_ip_attempts(ip)
        self.env['ir.config_parameter'].sudo().set_param(param_name, str(attempts + 1))

    @api.model
    def _clean_old_attempts(self):
        """Limpiar intentos más antiguos de 1 hora"""
        params = self.env['ir.config_parameter'].sudo().search([
            ('key', 'like', 'signup_attempts_%')
        ])
        params.unlink()

    @api.constrains('login')
    def _check_email_domain(self):
        for user in self:
            if user.login:
                allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
                domain = user.login.split('@')[-1].lower()
                if domain not in allowed_domains:
                    raise ValidationError('Use un correo de Gmail, Hotmail, Outlook o Yahoo')