from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import werkzeug

class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token', readonly=True)

    def generate_authorization_url(self):
        authorize_url = 'https://my.pcloud.com/oauth2/authorize'
        authorize_params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': 'https://copiercompanysac.com/pcloud/callback',
        }
        return werkzeug.urls.url_join(authorize_url, '?' + werkzeug.urls.url_encode(authorize_params))

    def exchange_code_for_token(self, authorization_code):
        token_url = 'https://api.pcloud.com/oauth2_token'
        token_params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': 'https://copiercompanysac.com/pcloud/callback',
            'grant_type': 'authorization_code',
        }
        response = requests.post(token_url, data=token_params)
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                self.write({'access_token': access_token})
            else:
                raise UserError(_("Authentication with pCloud failed. No access token returned."))
        else:
            raise UserError(_("Failed to exchange authorization code for access token. Error: %s") % response.text)

    @api.model
    def authenticate_with_pcloud(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.generate_authorization_url(),
            'target': 'new',
        }

    @api.model
    def action_connect_to_pcloud(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.generate_authorization_url(),
            'target': 'new',
        }

    @api.multi
    def action_disconnect_from_pcloud(self):
        self.ensure_one()
        if self.access_token:
            try:
                # Desconectar sesión en pCloud utilizando el token de acceso
                # Aquí debes implementar la lógica para desconectar la sesión de pCloud
                # Por ahora, solo borramos el token de acceso
                self.write({'access_token': False})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Disconnected!'),
                        'message': _('You have been successfully disconnected from pCloud.'),
                        'sticky': False,  # True si quieres que la notificación permanezca hasta que el usuario la cierre
                    }
                }
            except Exception as e:
                raise UserError(_("Failed to disconnect from pCloud: %s" % str(e)))
        else:
            raise UserError(_("No active pCloud session to disconnect."))
