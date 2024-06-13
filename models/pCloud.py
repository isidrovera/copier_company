from odoo import models, fields, api
import requests

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

    def list_pcloud_files(self, folder_id=0):
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
                contents = response.json()['metadata']['contents']
                return [item for item in contents if item['isfolder'] == False]
            else:
                raise Exception("Failed to list files")

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
