import os
import tempfile
import shutil
import json
import subprocess
import zipfile
import requests
import base64

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
import odoo

import logging
_logger = logging.getLogger(__name__)


class BackupConfigSettings(models.Model):
    _name = 'backup.config.settings'
    _description = 'Configuración de Backup'

    name = fields.Char('Nombre de Configuración', required=True)
    db_name = fields.Char('Nombre de la Base de Datos', required=True)
    db_user = fields.Char('Usuario de la Base de Datos', required=True)
    db_password = fields.Char('Contraseña de la Base de Datos', required=True)
    db_host = fields.Char('Host de la Base de Datos', required=True, default='db')
    db_port = fields.Integer('Puerto de la Base de Datos', required=True, default=5432)
    pcloud_folder_id = fields.Char('ID de Carpeta en pCloud', required=True)
    cron_frequency = fields.Selection([
        ('minutes', 'Minutos'),
        ('hours', 'Horas'),
        ('days', 'Días'),
    ], string="Frecuencia del Cron", default='days', required=True)
    
    def test_db_connection(self):
        try:
            self.env.cr.execute("SELECT 1")
            message = "¡Conexión a la base de datos exitosa!"
            notification_type = 'success'
        except Exception as e:
            message = f"¡Conexión a la base de datos fallida! Error: {str(e)}"
            notification_type = 'danger'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Prueba de Conexión a la Base de Datos',
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }

    def create_backup(self):
        self.ensure_one()
        
        db_name = self.db_name
        db_user = self.db_user
        db_password = self.db_password
        db_host = self.db_host
        db_port = self.db_port

        temp_dir = tempfile.mkdtemp()
        try:
            dump_file = os.path.join(temp_dir, 'dump.sql')
            dump_cmd = f"PGPASSWORD={db_password} pg_dump -Fc -h {db_host} -p {db_port} -U {db_user} {db_name} -f {dump_file}"
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)

            if result.returncode != 0:
                error_message = f"¡Falló el volcado de la base de datos! Error: {str(result.stderr)}"
                raise UserError(error_message)

            filestore_path = tools.config.filestore(db_name)
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

            self.upload_to_pcloud(backup_file_path, self.pcloud_folder_id)

            shutil.rmtree(temp_dir)
            os.remove(backup_file_path)

            self.env['backup.history'].create({
                'name': f"{db_name}_backup_{fields.Datetime.now().strftime('%Y-%m-%d %H%M%S')}",
                'backup_data': base64.b64encode(open(backup_file_path, 'rb').read()),
            })

            _logger.info("Backup creado y subido a pCloud con éxito.")
        except subprocess.CalledProcessError as e:
            error_message = f"¡Backup fallido! Error: {str(e)}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            _logger.error(error_message)
            raise UserError(error_message)

    def upload_to_pcloud(self, backup_file_path, pcloud_folder_id):
        config = self.env['pcloud.config'].search([], limit=1)
        if not config:
            raise UserError("No se encontró la configuración de pCloud. Asegúrese de que la configuración de pCloud esté creada y configurada correctamente.")
        if not config.access_token:
            raise UserError("pCloud no está conectado. Por favor, conéctese a pCloud primero.")

        url = f"{config.hostname}/uploadfile"
        params = {
            'access_token': config.access_token,
            'folderid': pcloud_folder_id,
            'filename': os.path.basename(backup_file_path),
        }
        with open(backup_file_path, 'rb') as file:
            files = {'file': (os.path.basename(backup_file_path), file)}
            response = requests.post(url, params=params, files=files)
            if response.status_code != 200:
                _logger.error("No se pudo subir el backup a pCloud. Respuesta: %s", response.text)
                raise UserError("No se pudo subir el backup a pCloud. Por favor, revise su configuración.")

    def update_cron_frequency(self):
        self.ensure_one()
        
        cron_frequency = self.cron_frequency
        cron = self.env.ref('copier_company.ir_cron_backup')

        if cron_frequency == 'minutes':
            cron.write({'interval_number': 1, 'interval_type': 'minutes'})
        elif cron_frequency == 'hours':
            cron.write({'interval_number': 1, 'interval_type': 'hours'})
        else:
            cron.write({'interval_number': 1, 'interval_type': 'days'})


class BackupHistory(models.Model):
    _name = 'backup.history'
    _description = 'Historial de Backups'

    name = fields.Char(string="Nombre del Backup", required=True)
    backup_data = fields.Binary(string="Datos del Backup")
    backup_date = fields.Datetime(string="Fecha del Backup", default=fields.Datetime.now, readonly=True)
