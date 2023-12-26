from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

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
            _logger.info("Token de pCloud obtenido con éxito.")
            return self.token
        else:
            error_msg = f"Error al obtener token de pCloud: {response.text}"
            _logger.error(error_msg)
            raise UserError(error_msg)

  
    def conectar_pcloud(self):
        self.ensure_one()
        try:
            token = self.obtener_token_pcloud()
            if token:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Conexión Exitosa',
                        'message': 'Conexión con pCloud establecida.',
                        'type': 'success',
                    }
                }
        except Exception as e:
            raise exceptions.UserError('Error al conectar con pCloud: %s' % str(e))





    def subir_archivo_pcloud(self, file_path):
        if not self.token:
            raise UserError("No se ha establecido la conexión con pCloud.")

        url = "https://api.pcloud.com/uploadfile"
        params = {'auth': self.token, 'folderid': 0}
        files = {'file': open(file_path, 'rb')}
        response = requests.post(url, files=files, params=params)
        if response.status_code == 200:
            _logger.info("Archivo subido con éxito a pCloud.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Archivo subido exitosamente a pCloud.'),
                    'type': 'success',
                }
            }
        else:
            error_msg = f"Error al subir archivo a pCloud: {response.text}"
            _logger.error(error_msg)
            raise UserError(error_msg)


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
    def obtener_archivos_pcloud(self):
        if not self.token:
            raise UserError("La conexión con pCloud no está establecida.")

        url = "https://api.pcloud.com/listfolder"
        params = {'auth': self.token, 'folderid': 0}  # Usando la carpeta raíz como ejemplo
        response = requests.get(url, params=params)

        if response.status_code == 200:
            archivos = response.json().get('contents', [])
            return archivos
        else:
            error_msg = "Error al obtener archivos de pCloud: {}".format(response.text)
            _logger.error(error_msg)
            raise UserError(error_msg)
            raise UserError(error_msg)


    class PCloudArchivo(models.Model):
        _name = 'pcloud.archivo'
        _description = 'Archivo de pCloud'

        name = fields.Char("Nombre", required=True)
        size = fields.Integer("Tamaño")
        isfolder = fields.Boolean("Es Carpeta")