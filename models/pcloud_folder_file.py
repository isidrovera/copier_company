from odoo import models, fields

class PCloudFolderFile(models.TransientModel):
    _name = 'pcloud.folder.file'
    _description = 'Temporary model to store pCloud folders and files'

    name = fields.Char(string='Name', required=True)
    is_folder = fields.Boolean(string='Is Folder')
    pcloud_config_id = fields.Many2one('pcloud.config', string='pCloud Config', required=True)
