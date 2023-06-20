from odoo import models, fields, api
import xmlrpc.client
import requests
class PCloudAPI:
    def __init__(self, username, password):
        self.username = 'verapolo@icloud.com'
        self.password = 'system05VP$$'
        self.auth = None
        self.api_url = 'https://api.pcloud.com/gettreepublink'
        self.odoo_url = 'http://localhost:8069'
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.odoo_url))
        self.uid = self.common.authenticate('demo', self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.odoo_url))

    def login(self):
        response = requests.post('{}/userinfo'.format(self.api_url), data={
            'username': self.username,
            'password': self.password
        })
        if response.status_code == 200:
            self.auth = response.json()['auth']
            return True
        else:
            return False
    def list_files(self, folder_id):
        if not self.auth:
            self.login()
        response = requests.get('{}/listfolder'.format(self.api_url), params={
            'auth': self.auth,
            'folderid': folder_id
        })
        if response.status_code == 200:
            return response.json()['metadata']
        else:
            return None
    def download_file(self, file_id):
        if not self.auth:
            self.login()
        response = requests.get('{}/getfilelink'.format(self.api_url), params={
            'auth': self.auth,
            'fileid': file_id
        })
        if response.status_code == 200:
            return response.json()['hosts'][0] + response.json()['path']
        else:
            return None
class PCloudFiles(models.Model):
    _name = 'pcloud.files'
    _description = 'pCloud Files'

    name = fields.Char(string='File Name')
    size = fields.Float(string='File Size')
    download_link = fields.Char(string='Download Link')

    @api.model
    def get_pcloud_files(self):
        pcloud_api = PCloudAPI('verapolo@icloud.com', 'system05VP$$')
        files_metadata = pcloud_api.list_files(folder_id='canon')
        files = []
        for file_metadata in files_metadata:
            file = {
                'name': file_metadata['name'],
                'size': file_metadata['size'],
                'download_link': pcloud_api.download_file(file_metadata['fileid'])
            }
            files.append(file)
        return files
