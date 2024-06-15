from odoo import models, fields, api
import requests
import os
import datetime
import logging
import subprocess
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
            return

        odoo_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        db_name = self.env.cr.dbname
        username = self.env.user.login
        backup_config = self.env['backup.config.settings'].search([], limit=1)
        password = backup_config.odoo_password

        # Generar la copia de seguridad utilizando pg_dump
        backup_file = f"{db_name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"
        backup_path = f"/ruta/a/copias/seguridad/{backup_file}"
        dump_cmd = f"pg_dump -Fc -h localhost -U {username} {db_name} -f {backup_path}"

        try:
            result = subprocess.run(dump_cmd, shell=True, check=True, text=True, capture_output=True)
            _logger.info(f"Backup command output: {result.stdout}")

            # Subir la copia de seguridad a pCloud
            pcloud_token = pcloud_config.access_token
            pcloud_url = f"{pcloud_config.hostname}/uploadfile"
            folder_id = backup_config.pcloud_folder_id

            with open(backup_path, 'rb') as file:
                response = requests.post(
                    pcloud_url,
                    params={'access_token': pcloud_token, 'folderid': folder_id},
                    files={'file': (backup_file, file)}
                )

            if response.status_code == 200:
                self.write({'status': 'completed'})
            else:
                self.write({'status': 'failed'})
                _logger.error(f"Failed to upload backup: {response.content}")
                return

            # Eliminar la copia de seguridad local
            os.remove(backup_path)
        except subprocess.CalledProcessError as e:
            self.write({'status': 'failed'})
            _logger.error(f"Backup creation failed: {e}")
            raise e

    @api.model
    def update_cron_frequency(self):
        backup_config = self.env['backup.config.settings'].search([], limit=1)
        cron_frequency = backup_config.cron_frequency
        cron = self.env.ref('my_backup_module.ir_cron_backup')
        
        if cron_frequency == 'minutes':
            cron.write({'interval_number': 1, 'interval_type': 'minutes'})
        elif cron_frequency == 'hours':
            cron.write({'interval_number': 1, 'interval_type': 'hours'})
        else:
            cron.write({'interval_number': 1, 'interval_type': 'days'})
