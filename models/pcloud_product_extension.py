from odoo import models, fields

class ProductTemplatePCloud(models.Model):
    _inherit = 'product.template'

    pcloud_folder_id = fields.Char(
        string='pCloud Folder ID',
        help='ID de la carpeta en pCloud vinculada a este producto digital',
    )