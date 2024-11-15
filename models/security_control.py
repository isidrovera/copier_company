# security_management/models/security_control.py
from odoo import models, fields, api
from odoo.exceptions import AccessDenied
import logging
_logger = logging.getLogger(__name__)

class SecurityControl(models.Model):
    _name = 'security.control'
    _description = 'Control de Seguridad'

    name = fields.Char('Nombre', required=True, default='Configuración de Seguridad')
    active = fields.Boolean('Activo', default=True)
    
    # Control de Base de Datos
    hide_db_selector = fields.Boolean('Ocultar Selector BD', default=True)
    allowed_db_ips = fields.Text(
        'IPs Permitidas BD',
        help='Una IP por línea. Vacío permite todas las IPs.'
    )
    
    # Control de Login
    hide_public_signup = fields.Boolean('Ocultar Registro Público', default=True)
    hide_password_reset = fields.Boolean('Ocultar Reset Contraseña', default=False)
    max_login_attempts = fields.Integer('Máx. Intentos Login', default=5)
    block_time = fields.Integer('Tiempo Bloqueo (min)', default=30)
    allowed_login_ips = fields.Text(
        'IPs Permitidas Login',
        help='Una IP por línea. Vacío permite todas las IPs.'
    )
    
    # Control de Usuarios
    allow_public_signup = fields.Boolean('Permitir Registro Público', default=False)
    public_signup_template = fields.Many2one(
        'res.groups',
        string='Plantilla Permisos Usuario Público'
    )
    password_reset_expiry = fields.Integer(
        'Expiración Reset (horas)',
        default=24
    )
    
    @api.model
    def get_security_settings(self):
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({'name': 'Configuración Principal'})
        return settings
        
    def _is_ip_allowed(self, ip, ip_list):
        if not ip_list:
            return True
        allowed_ips = [x.strip() for x in ip_list.split('\n') if x.strip()]
        return ip in allowed_ips
        
    def check_db_access(self, ip):
        self.ensure_one()
        if self.hide_db_selector:
            return False
        return self._is_ip_allowed(ip, self.allowed_db_ips)
        
    def check_login_access(self, ip):
        self.ensure_one()
        return self._is_ip_allowed(ip, self.allowed_login_ips)
        
    def check_password_reset(self):
        self.ensure_one()
        return not self.hide_password_reset
        
    def check_public_signup(self):
        self.ensure_one()
        return not self.hide_public_signup and self.allow_public_signup

    def apply_security_settings(self):
        self.ensure_one()
        # Aplicar configuraciones de seguridad
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param('auth_signup.allow_uninvited', 
                                 'true' if self.allow_public_signup else 'false')
        config_parameter.set_param('auth_signup.reset_password', 
                                 'true' if not self.hide_password_reset else 'false')
        return True