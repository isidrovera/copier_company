from odoo import models, fields, api
import os
import base64
import subprocess
from odoo.service.db import dump_db
from io import BytesIO
import requests
from odoo.exceptions import UserError

class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Backup Config Settings'

    name = fields.Char(string="Configuration Name", required=True)
    db_name = fields.Char(string="Database Name", required=True)
    db_user = fields.Char(string="Database User", required=True)
    db_password = fields.Char(string="Database Password", required=True)
    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    pcloud_token = fields.Char(string="pCloud Access Token", required=True)
    pcloud_hostname = fields.Char(string="pCloud Hostname", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)

    def test_db_connection(self):
        db_name = self.db_name
        user = self.db_user
        password = self.db_password

        try:
            # Intentar conectarse a la base de datos
            self.env.cr.execute("SELECT 1")
            message = "Database connection is successful!"
            notification_type = 'success'
        except Exception as e:
            message = f"Database connection failed! Error: {str(e)}"
            notification_type = 'danger'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Database Connection Test',
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }

    @api.model
    def create(self, vals):
        res = super(BackupConfigSettings, self).create(vals)
        res.update_cron_frequency()
        return res

    def write(self, vals):
        res = super(BackupConfigSettings, self).write(vals)
        self.update_cron_frequency()
        return res

class BackupHistory(models.Model):
    _name = 'backup.history'
    _description = 'Backup History'

    name = fields.Char(string="Backup Name", required=True)
    backup_data = fields.Binary(string="Backup Data")
    backup_date = fields.Datetime(string="Backup Date", default=fields.Datetime.now, readonly=True)