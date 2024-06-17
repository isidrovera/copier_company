from odoo import models, fields, api
import os
import base64
import subprocess
import shutil
import zipfile
import json
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
        db_name = self.db_name
        db_user = self.db_user
        db_password = self.db_password
        pcloud_folder_id = self.pcloud_folder_id

        temp_dir = f"/tmp/{db_name}_backup_temp"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            dump_file = os.path.join(temp_dir, 'dump.sql')
            dump_cmd = f"PGPASSWORD={db_password} pg_dump -Fp -h localhost -U {db_user} {db_name} > {dump_file}"
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

            # Upload the backup to pCloud
            pcloud_config = self.env['pcloud.config'].search([], limit=1)
            if not pcloud_config:
                raise UserError("No pCloud configuration found.")
            pcloud_config.upload_file_to_pcloud(backup_file_path, pcloud_folder_id)

            shutil.rmtree(temp_dir)
            os.remove(backup_file_path)

            _logger.info("Backup created and uploaded to pCloud successfully.")

        except subprocess.CalledProcessError as e:
            error_message = f"Backup failed! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            _logger.error(error_message)
            raise UserError(error_message)
