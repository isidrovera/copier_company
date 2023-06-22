import requests
from odoo import models, fields, api
from odoo.http import request, Response
class DescargaArchivos(models.Model):
    _name = 'descarga.archivos'
    
    name = fields.Char(string='Nombre del archivo')
    url = fields.Char(string='URL del archivo')
    prueba = fields.Html(string="Prueba")
    
    def descargar_archivo(self):
        url = self.url
        response = requests.get(url, stream=True)
        nombre_archivo = url.split("/")[-1]
        headers = dict(response.headers)
        tipo_contenido = headers.get("content-type")
        tamano_archivo = headers.get("content-length")
        if response.status_code == 200:
            response.raw.decode_content = True
            with open(nombre_archivo, "wb") as archivo:
                shutil.copyfileobj(response.raw, archivo)
            return "Archivo descargado exitosamente"
        else:
            return "Error al descargar el archivo"
