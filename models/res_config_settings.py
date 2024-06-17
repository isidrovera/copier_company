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
    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    odoo_password = fields.Char(string="Odoo Password", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)

    def test_db_connection(self):
        db_name = self.env.cr.dbname
        user = self.env.user.login
        password = self.odoo_password

        try:
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

    def create_backup(self):
        db_name = self.env.cr.dbname
        backup_file_path = f"/tmp/{db_name}_backup_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"
        dump_cmd = f"pg_dump -Fc -h db -U odoo {db_name} -f {backup_file_path}"
        
        try:
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)
            backup_data = open(backup_file_path, 'rb').read()
            backup_file_name = f"{db_name}_backup.zip"

            # Guardar la copia de seguridad en pCloud
            self.upload_to_pcloud(backup_data, backup_file_name)

            # Guardar la información de la copia de seguridad en un registro de Odoo
            self.env['backup.history'].create({
                'name': backup_file_name,
                'backup_data': base64.b64encode(backup_data),
            })

            # Eliminar el archivo temporal
            os.remove(backup_file_path)

        except subprocess.CalledProcessError as e:
            error_message = f"Backup failed! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            raise UserError(error_message)

    def upload_to_pcloud(self, data, file_name):
        config = self.env['pcloud.config'].search([], limit=1)
        if not config:
            raise UserError("No pCloud configuration found.")

        if not config.access_token:
            raise UserError("pCloud is not connected. Please connect to pCloud first.")

        url = f"{config.hostname}/uploadfile"
        params = {
            'access_token': config.access_token,
            'folderid': self.pcloud_folder_id,
            'filename': file_name,
        }
        files = {'file': (file_name, data)}
        response = requests.post(url, params=params, files=files)
        if response.status_code != 200:
            raise UserError("Failed to upload backup to pCloud. Please check your configuration.")

    def _update_cron(self):
        cron = self.env.ref('copier_company.ir_cron_backup')
        interval_type = self.cron_frequency
        interval_number = 1

        if cron:
            cron.write({
                'interval_number': interval_number,
                'interval_type': interval_type,
            })

    @api.model
    def create(self, vals):
        res = super(BackupConfigSettings, self).create(vals)
        res._update_cron()
        return res

    def write(self, vals):
        res = super(BackupConfigSettings, self).write(vals)
        self._update_cron()
        return res

class BackupHistory(models.Model):
    _name = 'backup.history'
    _description = 'Backup History'

    name = fields.Char(string="Backup Name", required=True)
    backup_data = fields.Binary(string="Backup Data")
    backup_date = fields.Datetime(string="Backup Date", default=fields.Datetime.now, readonly=True)