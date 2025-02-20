from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request

class ExtendedAuthSignup(AuthSignupHome):
    
    @http.route()
    def web_auth_signup(self, *args, **kw):
        providers = request.env['auth.oauth.provider'].sudo().search([('enabled', '=', True)])
        values = {
            'providers': providers,
        }
        
        # Validar reCAPTCHA si está presente
        if request.httprequest.method == 'POST':
            if not self._validate_recaptcha():
                values['error'] = 'Por favor complete el reCAPTCHA'
                return request.render('auth_signup.signup', values)
        
        response = super().web_auth_signup(*args, **kw)
        
        # Si la respuesta es un dict o QWeb, añadir los providers
        if isinstance(response, (dict, http.Response)):
            if isinstance(response, dict):
                response.update(values)
            return response
            
        return response

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