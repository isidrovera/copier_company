from odoo import models, fields, api
import os
import subprocess
import tempfile
import shutil
import zipfile
import json
import requests
from odoo.exceptions import UserError
import logging
import psycopg2
from psycopg2 import OperationalError

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
        if not self._test_db_connection():
            raise UserError("Database connection cannot be established with provided credentials.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Database Connection Test',
                'message': 'Database connection is successful!',
                'type': 'success',
                'sticky': False,
            }
        }

    def _test_db_connection(self):
        try:
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host='db',  # Using the service name from docker-compose as hostname
                port=5433   # Port as configured in docker-compose
            )
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            connection.close()
            return True
        except OperationalError as e:
            _logger.error(f"Connection failed: {e}")
            return False

    @api.model
    def create_backup(self):
        if not self._test_db_connection():
            _logger.error("Database connection cannot be established with provided credentials.")
            return

        temp_dir = tempfile.mkdtemp()
        try:
            # Dump the database
            dump_file = os.path.join(temp_dir, 'dump.sql')
            dump_cmd = f"PGPASSWORD={self.db_password} pg_dump -Fp -h db -U {self.db_user} {self.db_name} -f {dump_file}"
            result = subprocess.run(dump_cmd, shell=True, check=True, capture_output=True)
            if result.returncode != 0:
                raise UserError(f"Database dump failed! Error: {result.stderr.decode()}")

            # Copy filestore
            filestore_path = os.path.join('/var/lib/odoo', 'filestore', self.db_name)
            filestore_backup_path = os.path.join(temp_dir, 'filestore')
            shutil.copytree(filestore_path, filestore_backup_path)

            # Create a zip file
            backup_file_path = f"/mnt/cloud/{self.db_name}_backup_{fields.Date.today()}.zip"
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        backup_zip.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

            # Upload the backup to pCloud
            self.upload_to_pcloud(backup_file_path)

        finally:
            shutil.rmtree(temp_dir)

    def upload_to_pcloud(self, backup_file_path):
        config = self.env['pcloud.config'].search([], limit=1)
        if not config or not config.access_token:
            raise UserError("pCloud configuration not found or not connected.")

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
            _logger.error(f"Failed to upload backup to pCloud. Response: {response.text}")
            raise UserError("Failed to upload backup to pCloud. Please check your configuration.")

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
        if cron:
            cron.write({
                'interval_number': 1,
                'interval_type': self.cron_frequency,
            })
