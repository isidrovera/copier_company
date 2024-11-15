# security_management/controllers/main.py
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Database, Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import AccessDenied
import logging
_logger = logging.getLogger(__name__)

class SecureDatabase(Database):
    @http.route('/web/database/selector', type='http', auth="none")
    def selector(self, **kwargs):
        security = request.env['security.control'].sudo().get_security_settings()
        client_ip = request.httprequest.remote_addr
        
        if not security.check_db_access(client_ip):
            _logger.warning(f'Acceso bloqueado al selector DB - IP: {client_ip}')
            return request.not_found()
            
        return super(SecureDatabase, self).selector(**kwargs)

class SecureAuth(AuthSignupHome):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kwargs):
        security = request.env['security.control'].sudo().get_security_settings()
        if not security.check_public_signup():
            return request.not_found()
        return super(SecureAuth, self).web_auth_signup(*args, **kwargs)
        
    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kwargs):
        security = request.env['security.control'].sudo().get_security_settings()
        if not security.check_password_reset():
            return request.not_found()
        return super(SecureAuth, self).web_auth_reset_password(*args, **kwargs)

class SecureHome(Home):
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kwargs):
        security = request.env['security.control'].sudo().get_security_settings()
        client_ip = request.httprequest.remote_addr
        
        if not security.check_login_access(client_ip):
            _logger.warning(f'Acceso bloqueado al login - IP: {client_ip}')
            return request.not_found()
            
        # Control de intentos de login
        attempts = request.session.get('login_attempts', {})
        if client_ip in attempts:
            if attempts[client_ip].get('count', 0) >= security.max_login_attempts:
                _logger.warning(f'Máximo de intentos excedido - IP: {client_ip}')
                return request.not_found()
                
        response = super(SecureHome, self).web_login(redirect=redirect, **kwargs)
        
        # Registrar intento fallido
        if request.params.get('login_success') is False:
            if client_ip not in attempts:
                attempts[client_ip] = {'count': 0}
            attempts[client_ip]['count'] = attempts[client_ip].get('count', 0) + 1
            request.session['login_attempts'] = attempts
            
        return response