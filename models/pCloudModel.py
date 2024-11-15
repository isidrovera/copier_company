from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token', readonly=True)
    redirect_uri = fields.Char(string='Redirect URI', required=True)
    hostname = fields.Char(string='Hostname', readonly=True)

    def get_authorization_url(self):
        for record in self:
            url = "https://my.pcloud.com/oauth2/authorize"
            params = {
                'client_id': record.client_id,
                'response_type': 'code',
                'redirect_uri': record.redirect_uri,
                'state': 'random_state'
            }
            return requests.Request('GET', url, params=params).prepare().url

    def get_access_token(self, code):
        for record in self:
            url = "https://api.pcloud.com/oauth2_token"
            params = {
                'client_id': record.client_id,
                'client_secret': record.client_secret,
                'code': code,
                'redirect_uri': record.redirect_uri
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                record.access_token = data['access_token']
                record.hostname = data.get('hostname', 'https://api.pcloud.com')
            else:
                raise Exception("Failed to get access token")

    def create_pcloud_folder(self, folder_name):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")
            
            url = f"{record.hostname}/createfolder"
            params = {
                'access_token': record.access_token,
                'name': folder_name,
                'folderid': 0  # 0 para crear en la raíz
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()['metadata']['folderid']
            else:
                raise Exception("Failed to create folder")

    def upload_file_to_pcloud(self, file_path, folder_id):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")
            
            url = f"{record.hostname}/uploadfile"
            params = {
                'access_token': record.access_token,
                'folderid': folder_id,
            }
            files = {'file': open(file_path, 'rb')}
            response = requests.post(url, params=params, files=files)
            if response.status_code == 200:
                return response.json()['metadata'][0]['fileid']
            else:
                raise Exception("Failed to upload file")

    def list_pcloud_folders(self, folder_id=0):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")
            
            url = f"{record.hostname}/listfolder"
            params = {
                'access_token': record.access_token,
                'folderid': folder_id,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()['metadata']['contents']
            else:
                raise Exception("Failed to list folders")

    def list_pcloud_contents(self, folder_id=0):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")
            
            url = f"{record.hostname}/listfolder"
            params = {
                'access_token': record.access_token,
                'folderid': folder_id,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()['metadata']['contents']
            else:
                raise Exception("Failed to list folders")

    def action_connect_to_pcloud(self):
        for record in self:
            authorization_url = record.get_authorization_url()
            return {
                'type': 'ir.actions.act_url',
                'url': authorization_url,
                'target': 'new',
            }

    def action_disconnect_from_pcloud(self):
        for record in self:
            record.access_token = False
            record.hostname = False

    def action_list_folders(self):
        for record in self:
            # Limpiar los registros anteriores
            self.env['pcloud.folder.file'].search([]).unlink()
            folders = record.list_pcloud_folders()
            for folder in folders:
                self.env['pcloud.folder.file'].create({
                    'name': folder['name'],
                    'is_folder': folder['isfolder'],
                    'pcloud_config_id': record.id
                })
            return {
                'type': 'ir.actions.act_window',
                'name': 'pCloud Folders and Files',
                'res_model': 'pcloud.folder.file',
                'view_mode': 'tree,form',
                'target': 'current',
            }

    def action_list_files(self):
        for record in self:
            # Limpiar los registros anteriores
            self.env['pcloud.folder.file'].search([]).unlink()
            files = record.list_pcloud_files()
            for file in files:
                self.env['pcloud.folder.file'].create({
                    'name': file['name'],
                    'is_folder': file['isfolder'],
                    'pcloud_config_id': record.id
                })
            return {
                'type': 'ir.actions.act_window',
                'name': 'pCloud Folders and Files',
                'res_model': 'pcloud.folder.file',
                'view_mode': 'tree,form',
                'target': 'current',
            }
    def get_pcloud_file_info(self, file_id):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")
            
            url = f"{record.hostname}/getfilelink"
            params = {
                'access_token': record.access_token,
                'fileid': file_id,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception("Failed to get file info")

    def download_pcloud_file(self, file_id):
        for record in self:
            if not record.access_token:
                raise Exception("No access token found. Please connect to pCloud first.")

            url = f"{record.hostname}/getfilelink"
            params = {
                'access_token': record.access_token,
                'fileid': file_id,
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                _logger.info('API Response: %s', data)  # Log the API response for debugging
                download_url = data.get('hosts')[0] + data.get('path')
                if not download_url:
                    raise Exception("Failed to get file download link")
                return download_url
            else:
                raise Exception("Failed to get file download link")


    def get_folder_path(self, folder_id):
        """
        Obtiene la ruta completa de una carpeta hasta la raíz
        """
        if not self.access_token:
            raise Exception("No access token found. Please connect to pCloud first.")
        
        folder_path = []
        current_id = folder_id
        
        while current_id != 0:
            url = f"{self.hostname}/listfolder"
            params = {
                'access_token': self.access_token,
                'folderid': current_id,
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    folder_info = response.json()['metadata']
                    folder_path.insert(0, {
                        'id': current_id,
                        'name': folder_info.get('name', 'Unknown'),
                        'parentfolderid': folder_info.get('parentfolderid', 0)
                    })
                    current_id = folder_info.get('parentfolderid', 0)
                else:
                    break
            except Exception as e:
                _logger.error('Error getting folder info: %s', str(e))
                break
                
        return folder_path