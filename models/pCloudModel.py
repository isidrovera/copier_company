from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token')
    redirect_uri = fields.Char(string='Redirect URI', required=True)
    hostname = fields.Char(string='Hostname')

    def _get_api_url(self):
        """
        Retorna el hostname normalizado.
        pCloud no devuelve hostname en oauth2_token,
        así que usamos el valor guardado o el default.
        """
        self.ensure_one()
        hostname = self.hostname or 'api.pcloud.com'
        if not hostname.startswith('http'):
            hostname = 'https://' + hostname
        return hostname.rstrip('/')

    def get_authorization_url(self):
        self.ensure_one()
        url = "https://my.pcloud.com/oauth2/authorize"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': 'random_state',
        }
        return requests.Request('GET', url, params=params).prepare().url

    def get_access_token(self, code):
        self.ensure_one()
        url = "https://api.pcloud.com/oauth2_token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            _logger.info('pCloud oauth2_token status: %s body: %s',
                         response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con pCloud: {str(e)}")

        if response.status_code != 200:
            raise UserError(f"pCloud HTTP {response.status_code}: {response.text}")

        data = response.json()
        if data.get('result', 0) != 0:
            raise UserError(f"pCloud error {data.get('result')}: {data.get('error', 'desconocido')}")

        access_token = data.get('access_token')
        if not access_token:
            raise UserError(f"pCloud no devolvió access_token. Respuesta: {data}")

        # pCloud oauth2_token NO devuelve hostname — se deja el valor
        # configurado manualmente o el default api.pcloud.com
        self.write({
            'access_token': access_token,
            'hostname': self.hostname or 'api.pcloud.com',
        })
        _logger.info('pCloud token guardado correctamente para config ID %s', self.id)

    def create_pcloud_folder(self, folder_name, parent_folder_id=0):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/createfolder"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'name': folder_name,
            'folderid': parent_folder_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata']['folderid']
        raise UserError("Error al crear carpeta en pCloud")

    def upload_file_to_pcloud(self, file_path, folder_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/uploadfile"
        with open(file_path, 'rb') as f:
            response = requests.post(url, params={
                'access_token': self.access_token,
                'folderid': folder_id,
            }, files={'file': f}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata'][0]['fileid']
        raise UserError("Error al subir archivo a pCloud")

    def list_pcloud_contents(self, folder_id=0):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/listfolder"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'folderid': folder_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata']['contents']
        raise UserError("Error al listar contenido de pCloud")

    # Alias para compatibilidad con código existente
    def list_pcloud_folders(self, folder_id=0):
        return self.list_pcloud_contents(folder_id)

    def get_pcloud_file_info(self, file_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/getfilelink"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'fileid': file_id,
        }, timeout=30)
        if response.status_code == 200:
            return response.json()
        raise UserError("Error al obtener info del archivo")

    def download_pcloud_file(self, file_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/getfilelink"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'fileid': file_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            _logger.info('pCloud getfilelink response: %s', data)
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            hosts = data.get('hosts', [])
            path = data.get('path', '')
            if not hosts or not path:
                raise UserError("pCloud no devolvió hosts/path para descarga")
            download_url = hosts[0] + path
            if not download_url.startswith('http'):
                download_url = 'https://' + download_url
            return download_url
        raise UserError("Error al obtener link de descarga")

    def get_folder_path(self, folder_id):
        """Obtiene la ruta completa de una carpeta hasta la raíz"""
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")

        folder_path = []
        current_id = folder_id
        max_depth = 20

        while current_id != 0 and len(folder_path) < max_depth:
            url = f"{self._get_api_url()}/listfolder"
            try:
                response = requests.get(url, params={
                    'access_token': self.access_token,
                    'folderid': current_id,
                }, timeout=30)
                if response.status_code == 200:
                    folder_info = response.json().get('metadata', {})
                    folder_path.insert(0, {
                        'id': current_id,
                        'name': folder_info.get('name', 'Unknown'),
                        'parentfolderid': folder_info.get('parentfolderid', 0),
                    })
                    current_id = folder_info.get('parentfolderid', 0)
                else:
                    break
            except Exception as e:
                _logger.error('Error getting folder path: %s', str(e))
                break

        return folder_path

    def action_connect_to_pcloud(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_authorization_url(),
            'target': 'new',
        }

    def action_disconnect_from_pcloud(self):
        self.ensure_one()
        self.write({
            'access_token': False,
        })

    def action_open_explorer(self):
        self.ensure_one()
        if not self.access_token:
            raise UserError('Conéctate a pCloud primero.')
        wizard = self.env['pcloud.explorer'].create({
            'config_id': self.id,
        })
        wizard._load_contents()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pcloud.explorer',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'edit'},
        }