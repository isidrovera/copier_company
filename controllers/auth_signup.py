# controllers/main.py
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
import requests

class ExtendedAuthSignup(AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        if request.httprequest.method == 'POST':
            error = self._validate_signup_form(kw)
            if error:
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = error
                return request.render('auth_signup.signup', qcontext)

        return super().web_auth_signup(*args, **kw)

    def _validate_signup_form(self, data):
        # Validar reCAPTCHA
        if not self._verify_recaptcha():
            return _("Por favor complete el reCAPTCHA")

        # Validar términos y condiciones
        if not data.get('terms'):
            return _("Debe aceptar los términos y condiciones")

        # Validar nombre
        name = data.get('name', '').strip()
        if not name or len(name) < 3:
            return _("El nombre debe tener al menos 3 caracteres")
        
        if not all(c.isalpha() or c.isspace() for c in name):
            return _("El nombre solo debe contener letras y espacios")

        return None

    def _verify_recaptcha(self):
        recaptcha_response = request.params.get('g-recaptcha-response')
        if not recaptcha_response:
            return False

        try:
            secret_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha.secret_key')
            response = requests.post('https://www.google.com/recaptcha/api.siteverify', {
                'secret': secret_key,
                'response': recaptcha_response,
                'remoteip': request.httprequest.remote_addr
            })
            return response.json().get('success', False)
        except Exception:
            return False