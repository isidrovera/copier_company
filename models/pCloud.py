from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import werkzeug
import logging

_logger = logging.getLogger(__name__)

class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token', readonly=True)
    refresh_token = fields.Char(string='Refresh Token', readonly=True)

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
            'grant_type': 'authorization_code',
        }
        response = requests.post(token_url, data=token_params)
        if response.status_code == 200:
            response_data = response.json()
            # Actualiza el registro actual con los nuevos tokens
            self.write({
                'access_token': response_data.get('access_token'),
                'refresh_token': response_data.get('refresh_token'),  # Asegúrate de que tu modelo tiene este campo
            })
            _logger.info("Access and refresh tokens stored successfully.")
        else:
            _logger.error("Failed to obtain access token: %s", response.text)
            raise UserError(_("Failed to obtain access token: %s") % response.text)

    def refresh_access_token(self):
        _logger.info("Refrescando el token de acceso de pCloud")
        refresh_url = 'https://api.pcloud.com/oauth2_token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(refresh_url, data=params)
        if response.status_code == 200:
            response_data = response.json()
            # Actualiza el registro actual con los nuevos tokens
            self.write({
                'access_token': response_data.get('access_token'),
                # Asegúrate de actualizar refresh_token si la API lo devuelve
                'refresh_token': response_data.get('refresh_token', self.refresh_token),
            })
            _logger.info("Token de acceso renovado y almacenado correctamente.")
        else:
            _logger.error("Error al refrescar el token: %s", response.text)
            raise UserError(_("Error al refrescar el token: %s") % response.text)


    @api.model
    def authenticate_with_pcloud(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.generate_authorization_url(),
            'target': 'new',
        }

    def action_connect_to_pcloud(self):
        self.ensure_one()  # Asegurarse de que el método se llama para un solo registro
        return {
            'type': 'ir.actions.act_url',
            'url': self.generate_authorization_url(),
            'target': 'new',
        }


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
    def get_folder_list(self):
        _logger.info("Obteniendo lista de carpetas desde pCloud")
        if not self.access_token:
            raise UserError(_("No hay token de acceso disponible. Por favor, autentíquese primero."))
        
        url = "https://api.pcloud.com/listfolder"
        params = {
            'auth': self.access_token,
            'folderid': 0,  # Raíz de pCloud por defecto
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['result'] == 0:
                return data['metadata']['contents']
            else:
                # Si el token ha caducado o es inválido, refrescar el token
                if data['result'] == 2000:
                    self.refresh_access_token()
                    return self.get_folder_list()
                else:
                    _logger.error("Error desde API de pCloud: %s", data.get('error'))
                    raise UserError(_("Error desde API de pCloud: %s") % data.get('error'))
        else:
            _logger.error("Falló la comunicación con API de pCloud. Código de estado: %s", response.status_code)
            raise UserError(_("Falló la comunicación con API de pCloud: %s") % response.status_code)