import pcloud
from odoo import models, fields, api
class PcloudFiles(models.Model):
    _name = 'pcloud.files'
    
    name = fields.Char('Nombre')
    size = fields.Integer('Tamaño')
    
    @api.model
    def get_files(self):
        client = pcloud.Client("verapolo@icloud.com", "system05VP$$")
        client.auth()
        files = client.listfolder(0)['metadata']
        for file in files:
            self.create({
                'name': file['name'],
                'size': file['size']
            })
        return self.search([])

