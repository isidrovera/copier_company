from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
import requests

class ExtendedAuthSignup(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_signup(self, *args, **kw):
        if request.httprequest.method == 'POST':
            # Verificar reCAPTCHA
            if not self._verify_recaptcha():
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = _("Por favor complete el reCAPTCHA")
                response = request.render('auth_signup.signup', qcontext)
                return response

            # Verificar términos y condiciones
            if not kw.get('terms'):
                qcontext = self.get_auth_signup_qcontext()
                qcontext['error'] = _("Debe aceptar los términos y condiciones")
                response = request.render('auth_signup.signup', qcontext)
                return response

        return super(ExtendedAuthSignup, self).web_signup(*args, **kw)

    def _verify_recaptcha(self):
        recaptcha_response = request.params.get('g-recaptcha-response')
        if not recaptcha_response:
            return False

        try:
            secret_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha.secret_key')
            response = requests.post('https://www.google.com/recaptcha/api.siteverify', {
                'secret': secret_key,
                'response': recaptcha_response,
            })
            result = response.json()
            return result.get('success', False)
        except Exception:
            return False