from odoo import models, fields, api
import requests

class ConfiguracionPCloud(models.Model):
    _name = 'configuracion.pcloud'
    _description = 'Configuración de pCloud'

    api_key = fields.Char('API Key', required=True)
    usuario = fields.Char('Usuario pCloud', required=True)
    password = fields.Char('Contraseña pCloud')
    token = fields.Char('Token de Acceso', readonly=True)

    
    def obtener_token_pcloud(self):
        url = "https://api.pcloud.com/oauth2_token"
        payload = {
            'client_id': self.api_key,
            'username': self.usuario,
            'password': self.password,
            'grant_type': 'password',
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            self.token = response.json().get('access_token')
        else:
            raise UserError('Error de autenticación con pCloud')
    
    
    def conectar_pcloud(self):
        self.ensure_one()
        self.obtener_token_pcloud()

    
    def sincronizar_pcloud(self):
        self.ensure_one()
        # Lógica para sincronizar datos con pCloud
        # Esto puede incluir listar archivos, revisar estados, etc.

    def subir_archivo_pcloud(self, file_path):
        token = self.token
        url = "https://api.pcloud.com/uploadfile"
        params = {'auth': token, 'folderid': 0}
        files = {'file': open(file_path, 'rb')}
        response = requests.post(url, files=files, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise UserError('Error al subir el archivo a pCloud')

    def descargar_archivo_pcloud(self, file_id):
        token = self.token
        url = f"https://api.pcloud.com/getfilelink?fileid={file_id}&auth={token}"
        response = requests.get(url)
        if response.status_code == 200:
            download_link = response.json().get('path')
            file_response = requests.get(f"https://api.pcloud.com{download_link}")
            if file_response.status_code == 200:
                return file_response.content
            else:
                raise UserError('Error al descargar el archivo de pCloud')
        else:
            raise UserError('Error al obtener el enlace de descarga de pCloud')

    def eliminar_archivo_pcloud(self, file_id):
        token = self.token
        url = "https://api.pcloud.com/deletefile"
        params = {'auth': token, 'fileid': file_id}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return True
        else:
            raise UserError('Error al eliminar el archivo en pCloud')

    def renombrar_archivo_pcloud(self, file_id, nuevo_nombre):
        token = self.token
        url = "https://api.pcloud.com/renamefile"
        params = {'auth': token, 'fileid': file_id, 'toname': nuevo_nombre}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return True
        else:
            raise UserError('Error al renombrar el archivo en pCloud')
