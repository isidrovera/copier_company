from odoo import models, fields, api, _
from odoo.exceptions import UserError
from pcloud import PyCloud

class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token', readonly=True)

    @api.model
    def authenticate_with_pcloud(self, username, password):
        try:
            # Autenticación con pCloud utilizando OAuth 2.0
            pc = PyCloud.oauth2_authorize(client_id=self.client_id, client_secret=self.client_secret)
            # Realizar alguna operación de prueba, como listar carpetas
            folder_list = pc.listfolder(folderid=0)
            if folder_list:
                # Si la autenticación y la operación tienen éxito, guardar el token de acceso
                self.access_token = pc.token
            else:
                raise UserError(_("Failed to authenticate with pCloud."))
        except Exception as e:
            raise UserError(_("Failed to authenticate with pCloud: %s" % str(e)))

    @api.model
    def disconnect_from_pcloud(self):
        if self.access_token:
            try:
                # Desconectar sesión en pCloud utilizando el token de acceso
                pc = PyCloud(auth=self.access_token)
                logout_response = pc.logout()
                if logout_response.get('result', -1) == 0:
                    # Limpiar el token de acceso después de cerrar la sesión exitosamente
                    self.access_token = False
                else:
                    raise UserError(_("Failed to disconnect from pCloud."))
            except Exception as e:
                raise UserError(_("Failed to disconnect from pCloud: %s" % str(e)))
        else:
            raise UserError(_("No active pCloud session to disconnect."))

    @api.model
    def test_connection(self):
        if self.access_token:
            try:
                # Realizar una operación de prueba para verificar la conexión activa
                pc = PyCloud(auth=self.access_token)
                folder_list = pc.listfolder(folderid=0)
                if folder_list:
                    return True
                else:
                    return False
            except Exception:
                return False
        else:
            return False
