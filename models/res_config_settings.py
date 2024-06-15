from odoo import models, fields, api
import subprocess

class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Backup Config Settings'

    name = fields.Char(string="Configuration Name", required=True)
    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    odoo_password = fields.Char(string="Odoo Password", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)

    def test_db_connection(self):
        db_name = self.env.cr.dbname
        username = self.env.user.login
        password = self.odoo_password

        test_cmd = f"pg_isready -h localhost -U {username} -d {db_name}"

        try:
            result = subprocess.run(test_cmd, shell=True, check=True, text=True, capture_output=True)
            if result.returncode == 0:
                message = "Database connection is successful!"
                notification_type = 'success'
            else:
                message = f"Database connection failed! Error: {result.stderr}"
                notification_type = 'danger'
        except subprocess.CalledProcessError as e:
            message = f"Database connection test failed! Error: {e.stderr}"
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
