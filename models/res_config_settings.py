from odoo import models, fields

class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Backup Config Settings'

    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    odoo_password = fields.Char(string="Odoo Password", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)
