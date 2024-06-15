from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pcloud_folder_id = fields.Char(string="pCloud Folder ID", config_parameter='my_backup_module.pcloud_folder_id')
    odoo_password = fields.Char(string="Odoo Password", config_parameter='my_backup_module.odoo_password')
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", config_parameter='my_backup_module.cron_frequency', default='days')
