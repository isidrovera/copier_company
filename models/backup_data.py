from odoo import models, fields, api
import requests
import os
import datetime
import logging
import subprocess
import zipfile

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

        db_name = self.env.cr.dbname
        backup_config = self.env['backup.config.settings'].search([], limit=1)
        if not backup_config:
            _logger.error("No backup configuration settings found.")
            self.create({'name': 'Backup', 'status': 'failed'})
            return

        password = backup_config.odoo_password

        # Generar la copia de seguridad utilizando pg_dump
        backup_file = f"{db_name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"
        backup_path = f"/tmp/{backup_file}"
        dump_cmd = f"pg_dump -Fc -h localhost -U odoo {db_name} -f {backup_path}"

        try:
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)
            _logger.info(f"Backup command output: {result.stdout}")
            if result.returncode != 0:
                _logger.error(f"Backup command failed with return code {result.returncode}: {result.stderr}")
                self.create({'name': 'Backup', 'status': 'failed'})
                return

            # Comprimir el archivo de copia de seguridad en un archivo ZIP
            zip_file = f"{db_name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = f"/tmp/{zip_file}"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))

            # Eliminar el archivo de copia de seguridad original
            os.remove(backup_path)

            # Subir la copia de seguridad comprimida a pCloud
            pcloud_token = pcloud_config.access_token
            pcloud_url = f"{pcloud_config.hostname}/uploadfile"
            folder_id = backup_config.pcloud_folder_id

            with open(zip_path, 'rb') as file:
                response = requests.post(
                    pcloud_url,
                    params={'access_token': pcloud_token, 'folderid': folder_id},
                    files={'file': (zip_file, file)}
                )

            if response.status_code == 200:
                self.create({'name': 'Backup', 'status': 'completed'})
            else:
                self.create({'name': 'Backup', 'status': 'failed'})
                _logger.error(f"Failed to upload backup: {response.content}")
                return

            # Eliminar la copia de seguridad comprimida local
            os.remove(zip_path)
        except subprocess.CalledProcessError as e:
            self.create({'name': 'Backup', 'status': 'failed'})
            _logger.error(f"Backup creation failed: {e.stderr}")
            raise e
        except Exception as e:
            self.create({'name': 'Backup', 'status': 'failed'})
            _logger.error(f"Unexpected error: {e}")
            raise e

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
