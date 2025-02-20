from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
import requests

class ExtendedAuthSignup(AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        if request.httprequest.method == 'POST':
            # Verificar términos y condiciones
            if not kw.get('terms'):
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = _("Debe aceptar los términos y condiciones")
                return request.render('auth_signup.signup', qcontext)

            # Verificar reCAPTCHA
            if not self._verify_recaptcha():
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = _("Por favor complete el reCAPTCHA")
                return request.render('auth_signup.signup', qcontext)

            try:
                # Verificar IP
                request.env['res.users'].sudo()._check_signup_ip(request.httprequest.remote_addr)
            except Exception as e:
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = str(e)
                return request.render('auth_signup.signup', qcontext)

        return super().web_auth_signup(*args, **kw)

    def _verify_recaptcha(self):
        """Verificar respuesta del reCAPTCHA"""
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
            result = response.json()
            return result.get('success', False)
        except Exception:
            return False