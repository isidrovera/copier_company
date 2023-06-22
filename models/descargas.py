import requests
from odoo import models, fields, api
from odoo.http import request, Response
class DescargaArchivos(models.Model):
    _name = 'descarga.archivos'
    
    name = fields.Char(string='Nombre del archivo')
    url = fields.Char(string='URL del archivo')
    modelo = fields.Char(string="Modelo")
    
    def descargar_archivo(self):
        url = self.url
        
