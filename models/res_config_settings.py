from odoo import models, fields, api
import subprocess
import os
import psycopg2

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

        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=username,
                password=password,
                host='localhost'
            )
            conn.close()
            message = "Database connection is successful!"
            notification_type = 'success'
        except psycopg2.OperationalError as e:
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
