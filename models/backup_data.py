from odoo import models, fields, api, tools
import odoo  # Importar odoo correctamente
import requests
import os
import datetime
import logging
import subprocess
import zipfile
import shutil
import json

_logger = logging.getLogger(__name__)

class BackupData(models.Model):
    _name = 'backup.data'
    _description = 'Backup Data Record'

    name = fields.Char(string='Backup Name', required=True)
    backup_date = fields.Datetime(string='Backup Date', default=fields.Datetime.now)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending', string='Status')

    @api.model
    def create_backup(self):
        # Obtener configuración de pCloud
        pcloud_config = self.env['pcloud.config'].search([], limit=1)
        if not pcloud_config:
            _logger.error("No pCloud configuration found.")
            self.create({'name': 'Backup', 'status': 'failed'})
            return

        backup_config = self.env['backup.config.settings'].search([], limit=1)
        if not backup_config:
            _logger.error("No backup configuration settings found.")
            self.create({'name': 'Backup', 'status': 'failed'})
            return

        db_name = backup_config.database_name
        db_user = backup_config.database_user
        db_password = backup_config.database_password

        # Crear directorio temporal para la copia de seguridad
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
            filestore_path = tools.config.filestore(db_name)
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
            backup_file_path = f"/tmp/{db_name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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

            self.create({'name': 'Backup', 'status': 'completed'})

        except subprocess.CalledProcessError as e:
            self.create({'name': 'Backup', 'status': 'failed'})
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
            'folderid': self.env['backup.config.settings'].search([], limit=1).pcloud_folder_id,
            'filename': os.path.basename(backup_file_path),
        }
        with open(backup_file_path, 'rb') as file:
            files = {'file': (os.path.basename(backup_file_path), file)}
            response = requests.post(url, params=params, files=files)

        if response.status_code != 200:
            raise UserError("Failed to upload backup to pCloud. Please check your configuration.")

    @api.model
    def update_cron_frequency(self):
        backup_config = self.env['backup.config.settings'].search([], limit=1)
        if not backup_config:
            _logger.error("No backup configuration settings found.")
            return
        cron_frequency = backup_config.cron_frequency
        cron = self.env.ref('copier_company.ir_cron_backup')

        if cron_frequency == 'minutes':
            cron.write({'interval_number': 1, 'interval_type': 'minutes'})
        elif cron_frequency == 'hours':
            cron.write({'interval_number': 1, 'interval_type': 'hours'})
        else:
            cron.write({'interval_number': 1, 'interval_type': 'days'})
