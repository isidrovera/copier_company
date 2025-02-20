from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
import requests
import re

class ExtendedAuthSignup(AuthSignupHome):
    @http.route()
    def web_auth_signup(self, *args, **kw):
        ip_address = request.httprequest.remote_addr
        
        # Validar intentos por IP
        if not self._check_ip_attempts(ip_address):
            return request.render('auth_signup.signup', {
                'error': 'Demasiados intentos desde esta IP. Intente más tarde.'
            })

        # Validar reCAPTCHA
        if not self._validate_recaptcha():
            return request.render('auth_signup.signup', {
                'error': 'Por favor complete el reCAPTCHA'
            })

        # Validar email
        email = kw.get('login')
        if not self._validate_email_domain(email):
            return request.render('auth_signup.signup', {
                'error': 'Use un correo de Gmail, Hotmail, Outlook o Yahoo'
            })

        # Registrar intento
        self._record_signup_attempt(ip_address)
        
        try:
            return super().web_auth_signup(*args, **kw)
        except Exception as e:
            return request.render('auth_signup.signup', {
                'error': str(e)
            })

    def _check_ip_attempts(self, ip):
        attempts = request.env['res.users'].sudo()._get_ip_attempts(ip)
        return attempts <= 5

    def _validate_recaptcha(self):
        recaptcha_response = request.params.get('g-recaptcha-response')
        if not recaptcha_response:
            return False
        
        try:
            secret_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha.secret_key')
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
                'secret': secret_key,
                'response': recaptcha_response
            })
            return r.json().get('success', False)
        except:
            return False

    def _validate_email_domain(self, email):
        if not email:
            return False
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
        domain = email.split('@')[-1].lower()
        return domain in allowed_domains

    def _record_signup_attempt(self, ip):
        request.env['res.users'].sudo()._record_signup_attempt(ip)