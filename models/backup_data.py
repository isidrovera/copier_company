from odoo import models, fields, api
import logging

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

        db_name = backup_config.db_name
        db_user = backup_config.db_user
        db_password = backup_config.db_password

        try:
            temp_dir = backup_config._create_backup_files(db_name, db_user, db_password)
            backup_file_path = backup_config._create_zip_file(temp_dir, db_name)
            backup_config._upload_to_pcloud(backup_file_path, pcloud_config, backup_config.pcloud_folder_id)
            backup_config._cleanup_files(temp_dir, backup_file_path)

            self.create({'name': 'Backup', 'status': 'completed'})
        except Exception as e:
            self.create({'name': 'Backup', 'status': 'failed'})
            raise e
