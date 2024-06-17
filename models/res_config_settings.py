from odoo import models, fields, api
import os
import base64
import subprocess
from odoo.exceptions import UserError
import requests
import shutil
import zipfile

class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Backup Config Settings'

    name = fields.Char(string="Configuration Name", required=True)
    database_name = fields.Char(string="Database Name", required=True)
    database_user = fields.Char(string="Database User", required=True)
    database_password = fields.Char(string="Database Password", required=True)
    pcloud_folder_id = fields.Char(string="pCloud Folder ID", required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string="Cron Frequency", default='days', required=True)

    def test_db_connection(self):
        db_name = self.database_name
        user = self.database_user
        password = self.database_password

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
        db_name = self.database_name
        db_user = self.database_user
        db_password = self.database_password

        backup_file_path = f"/tmp/{db_name}_backup_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        filestore_path = odoo.tools.config.filestore(db_name)
        temp_dir = f"/tmp/{db_name}_backup_temp"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Dump the database
            dump_cmd = f"PGPASSWORD={db_password} pg_dump -Fc -h db -U {db_user} {db_name} -f {temp_dir}/db.dump"
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)

            if result.returncode != 0:
                error_message = f"Database dump failed! Error: {str(result.stderr)}"
                raise UserError(error_message)

            # Copy filestore
            shutil.copytree(filestore_path, f"{temp_dir}/filestore")

            # Create a manifest file
            manifest = {
                'db_name': db_name,
                'version': odoo.release.version,
                'backup_date': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            with open(f"{temp_dir}/manifest.json", 'w') as manifest_file:
                json.dump(manifest, manifest_file)

            # Create a zip file
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        backup_zip.write(os.path.join(root, file),
                                         os.path.relpath(os.path.join(root, file),
                                                         os.path.join(temp_dir, '..')))

            # Upload the backup to pCloud
            self.upload_to_pcloud(backup_file_path)

            # Clean up temporary files
            shutil.rmtree(temp_dir)
            os.remove(backup_file_path)

        except subprocess.CalledProcessError as e:
            error_message = f"Backup failed! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
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
