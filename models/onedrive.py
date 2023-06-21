import pcloud
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class PcloudFiles(models.Model):
    _name = 'pcloud.files'
    
    name = fields.Char('Nombre')
    size = fields.Integer('Tamaño')
    
    @api.model
    def get_files(self):
        _logger.info('Iniciando la función get_files')
        client = pcloud.Client("verapolo@icloud.com", "system05VP$$")
        client.auth()
        _logger.info('Autenticación exitosa')
        files = client.listfolder(0)['metadata']
        _logger.info('Archivos encontrados: %s', files)
        for file in files:
            self.create({
                'name': file['name'],
                'size': file['size']
            })
            _logger.info('Registro creado: %s', file)
        _logger.info('Registros creados exitosamente')
        records = self.search([])
        _logger.info('Registros encontrados: %s', records)
        return records


