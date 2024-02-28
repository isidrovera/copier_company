from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import hashlib

class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token', readonly=True)

    def generate_password_digest(self, username, password, digest):
        # Generar el password digest como sha1(password + sha1(lowercase(username)) + digest)
        sha1_of_username = hashlib.sha1(username.lower().encode('utf-8')).hexdigest()
        password_digest = hashlib.sha1((password + sha1_of_username + digest).encode('utf-8')).hexdigest()
        return password_digest

    def action_connect(self):
        # En este punto, necesitarías capturar el username y password del usuario de manera segura
        # Por ejemplo, podrían ser almacenados temporalmente en el modelo o introducidos por el usuario
        username = 'USUARIO'
        password = 'CONTRASEÑA'

        # Obtener el digest para la autenticación
        digest_response = requests.get('https://api.pcloud.com/getdigest')
        digest_data = digest_response.json()
        digest = digest_data.get('digest')

        # Generar el password digest
        password_digest = self.generate_password_digest(username, password, digest)

        # Llamar al método userinfo con los parámetros para autenticación
        auth_params = {
            'getauth': 1,
            'logout': 1,
            'username': username,
            'passworddigest': password_digest,
        }
        auth_response = requests.get('https://api.pcloud.com/userinfo', params=auth_params)
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            if auth_data.get('result') == 0:
                # Guardar el token de autenticación
                self.access_token = auth_data.get('auth')
            else:
                raise UserError(_('No se pudo obtener el token de autenticación de pCloud.'))
        else:
            raise UserError(_('Error de conexión con pCloud.'))

    def action_disconnect(self):
        # Usar el token de acceso para desconectar la sesión en pCloud
        if self.access_token:
            logout_response = requests.get('https://api.pcloud.com/logout', params={'auth': self.access_token})
            if logout_response.status_code == 200:
                # Limpiar el token de acceso después de cerrar la sesión exitosamente
                self.access_token = False
            else:
                raise UserError(_('Error al desconectar de pCloud.'))
        else:
            raise UserError(_('No hay una sesión activa de pCloud para desconectar.'))
