from odoo import models, fields, api
import os
import base64
import subprocess
import shutil
import zipfile
import json
import requests
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Backup Config Settings'

    name = fields.Char(string="Configuration Name", required=True)
    db_name = fields.Char(string="Database Name", required=True)
    db_user = fields.Char(string="Database User", required=True)
    db_password = fields.Char(string="Database Password", required=True)
    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)

    def test_db_connection(self):
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

    @api.model
    def create(self, vals):
        res = super(BackupConfigSettings, self).create(vals)
        res._update_cron()
        return res

    def write(self, vals):
        res = super(BackupConfigSettings, self).write(vals)
        self._update_cron()
        return res

    def _update_cron(self):
        cron = self.env.ref('copier_company.ir_cron_backup')
        interval_type = self.cron_frequency
        interval_number = 1

        if cron:
            cron.write({
                'interval_number': interval_number,
                'interval_type': interval_type,
            })

    def create_backup(self):
        # Verificar si las credenciales de la base de datos están configuradas
        if not self.db_name or not self.db_user or not self.db_password:
            raise UserError("Database credentials are not set properly in the configuration settings.")

        db_name = self.db_name
        db_user = self.db_user
        db_password = self.db_password

        temp_dir = f"/tmp/{db_name}_backup_temp"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            dump_file = os.path.join(temp_dir, 'dump.sql')
            dump_cmd = f"PGPASSWORD={db_password} pg_dump -Fc -h localhost -U {db_user} {db_name} -f {dump_file}"
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)

            if result.returncode != 0:
                error_message = f"Database dump failed! Error: {str(result.stderr)}"
                raise UserError(error_message)

            filestore_path = os.path.join(self.env['ir.config_parameter'].sudo().get_param('data_dir'), 'filestore', db_name)
            filestore_backup_path = os.path.join(temp_dir, 'filestore')
            shutil.copytree(filestore_path, filestore_backup_path)

            manifest = {
                'db_name': db_name,
                'version': odoo.release.version,
                'backup_date': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            with open(os.path.join(temp_dir, 'manifest.json'), 'w') as manifest_file:
                json.dump(manifest, manifest_file)

            backup_file_path = f"/tmp/{db_name}_backup_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        backup_zip.write(os.path.join(root, file),
                                         os.path.relpath(os.path.join(root, file),
                                                         os.path.join(temp_dir, '..')))

            self.upload_to_pcloud(backup_file_path)

            shutil.rmtree(temp_dir)
            os.remove(backup_file_path)

            self.env['backup.history'].create({
                'name': f"{db_name}_backup_{fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'backup_data': base64.b64encode(open(backup_file_path, 'rb').read()),
            })

            _logger.info("Backup created and uploaded to pCloud successfully.")
        except subprocess.CalledProcessError as e:
            error_message = f"Backup failed! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            _logger.error(error_message)
            raise UserError(error_message)

    def upload_to_pcloud(self, backup_file_path):
        config = self.env['pcloud.config'].search([], limit=1)
        if not config:
            raise UserError("No pCloud configuration found.")

        if not config.access_token:
            raise UserError("pCloud is not connected. Please connect to pCloud first.")

        url = f"{config.hostname}/uploadfile"
        params = {
            'access_token': config.access_token,
            'folderid': self.pcloud_folder_id,
            'filename': os.path.basename(backup_file_path),
        }
        with open(backup_file_path, 'rb') as file:
            files = {'file': (os.path.basename(backup_file_path), file)}
            response = requests.post(url, params=params, files=files)
            if response.status_code != 200:
                _logger.error("Failed to upload backup to pCloud. Response: %s", response.text)
                raise UserError("Failed to upload backup to pCloud. Please check your configuration.")

class BackupHistory(models.Model):
    _name = 'backup.history'
    _description = 'Backup History'

    name = fields.Char(string="Backup Name", required=True)
    backup_data = fields.Binary(string="Backup Data")
    backup_date = fields.Datetime(string="Backup Date", default=fields.Datetime.now, readonly=True)
