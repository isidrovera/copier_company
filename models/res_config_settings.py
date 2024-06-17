from odoo import models, fields, api
import os
import base64
import subprocess
import tempfile
import shutil
import json
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
        db_name = self.db_name
        db_user = self.db_user
        db_password = self.db_password
        backup_file_path = f"/tmp/{db_name}_backup_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"
        dump_cmd = f"PGPASSWORD={db_password} pg_dump -Fc -h db -U {db_user} {db_name} -f {backup_file_path}"
        
        try:
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)
            temp_dir = tempfile.mkdtemp()
            filestore_path = odoo.tools.config.filestore(db_name)
            shutil.copytree(filestore_path, os.path.join(temp_dir, 'filestore'))
            with open(os.path.join(temp_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(self._dump_db_manifest(cr), fh, indent=4)
            shutil.copy(backup_file_path, os.path.join(temp_dir, 'db.dump'))

            # Crear archivo ZIP
            zip_file = f"{db_name}_backup_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join("/tmp", zip_file)
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)

            # Guardar la copia de seguridad en pCloud
            with open(zip_path, 'rb') as file:
                backup_data = file.read()
                self.upload_to_pcloud(backup_data, zip_file)

            # Guardar la información de la copia de seguridad en un registro de Odoo
            self.env['backup.history'].create({
                'name': zip_file,
                'backup_data': base64.b64encode(backup_data),
            })

            # Limpiar archivos temporales
            shutil.rmtree(temp_dir)
            os.remove(backup_file_path)

        except subprocess.CalledProcessError as e:
            error_message = f"Backup failed! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            raise UserError(error_message)

    def _dump_db_manifest(self, cr):
        pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': odoo.release.version,
            'version_info': odoo.release.version_info,
            'major_version': odoo.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest

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
