from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64
import logging

_logger = logging.getLogger(__name__)


class PCloudExplorerLine(models.TransientModel):
    _name = 'pcloud.explorer.line'
    _description = 'pCloud Explorer Line'
    _order = 'is_folder desc, name asc'

    explorer_id = fields.Many2one('pcloud.explorer', ondelete='cascade')
    name = fields.Char(string='Nombre', readonly=True)
    is_folder = fields.Boolean(string='Es carpeta', readonly=True)
    item_id = fields.Integer(string='ID pCloud', readonly=True)
    size = fields.Char(string='Tamaño', readonly=True)
    modified = fields.Char(string='Modificado', readonly=True)

    def action_navigate(self):
        """Entrar a una carpeta"""
        self.ensure_one()
        if not self.is_folder:
            return
        explorer = self.explorer_id
        # Guardar historial
        if explorer.current_folder_id != 0:
            history = explorer.breadcrumb_ids.mapped('folder_id')
        explorer.write({
            'current_folder_id': self.item_id,
            'current_folder_name': self.name,
        })
        explorer._load_contents()
        return explorer._reload()

    def action_delete(self):
        """Eliminar archivo o carpeta"""
        self.ensure_one()
        explorer = self.explorer_id
        config = explorer.config_id

        if self.is_folder:
            endpoint = '/deletefolderrecursive'
            param_key = 'folderid'
        else:
            endpoint = '/deletefile'
            param_key = 'fileid'

        url = f"{config.hostname}{endpoint}"
        try:
            response = requests.get(url, params={
                'access_token': config.access_token,
                param_key: self.item_id,
            }, timeout=30)
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"Error pCloud: {data.get('error', 'desconocido')}")
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Error al eliminar: {str(e)}")

        explorer._load_contents()
        return explorer._reload()

    def action_open_rename(self):
        """Abrir diálogo de renombrado"""
        self.ensure_one()
        explorer = self.explorer_id
        explorer.write({
            'rename_item_id': self.item_id,
            'rename_item_name': self.name,
            'rename_is_folder': self.is_folder,
        })
        return explorer._reload()


class PCloudExplorerBreadcrumb(models.TransientModel):
    _name = 'pcloud.explorer.breadcrumb'
    _description = 'pCloud Breadcrumb'
    _order = 'sequence asc'

    explorer_id = fields.Many2one('pcloud.explorer', ondelete='cascade')
    sequence = fields.Integer()
    folder_id = fields.Integer(string='Folder ID')
    name = fields.Char(string='Nombre')

    def action_navigate_breadcrumb(self):
        self.ensure_one()
        explorer = self.explorer_id
        # Eliminar breadcrumbs posteriores a este
        explorer.breadcrumb_ids.filtered(
            lambda b: b.sequence > self.sequence
        ).unlink()
        explorer.write({
            'current_folder_id': self.folder_id,
            'current_folder_name': self.name,
        })
        explorer._load_contents()
        return explorer._reload()


class PCloudExplorer(models.TransientModel):
    _name = 'pcloud.explorer'
    _description = 'pCloud File Explorer'

    config_id = fields.Many2one('pcloud.config', string='Config', required=True)
    current_folder_id = fields.Integer(default=0)
    current_folder_name = fields.Char(string='Ubicación', default='Raíz')

    line_ids = fields.One2many('pcloud.explorer.line', 'explorer_id', string='Contenido')
    breadcrumb_ids = fields.One2many(
        'pcloud.explorer.breadcrumb', 'explorer_id', string='Ruta'
    )

    # Campos para crear carpeta
    new_folder_name = fields.Char(string='Nombre de carpeta')

    # Campos para subir archivo
    upload_file = fields.Binary(string='Archivo')
    upload_filename = fields.Char(string='Nombre')

    # Campos para renombrar
    rename_item_id = fields.Integer()
    rename_item_name = fields.Char(string='Nuevo nombre')
    rename_is_folder = fields.Boolean()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        return res

    def _load_contents(self):
        """Recarga las líneas con el contenido de la carpeta actual"""
        self.ensure_one()
        self.line_ids.unlink()

        try:
            items = self.config_id.list_pcloud_contents(self.current_folder_id)
        except Exception as e:
            _logger.error('Error loading pCloud contents: %s', str(e))
            return

        lines = []
        for item in items:
            is_folder = item.get('isfolder', False)
            size_bytes = item.get('size', 0)
            lines.append({
                'explorer_id': self.id,
                'name': item.get('name', 'Sin nombre'),
                'is_folder': is_folder,
                'item_id': item.get('folderid') if is_folder else item.get('fileid'),
                'size': self._format_size(size_bytes) if not is_folder else '',
                'modified': item.get('modified', ''),
            })

        self.env['pcloud.explorer.line'].create(lines)

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pcloud.explorer',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'edit'},
        }

    def action_go_root(self):
        self.ensure_one()
        self.breadcrumb_ids.unlink()
        self.write({
            'current_folder_id': 0,
            'current_folder_name': 'Raíz',
        })
        self._load_contents()
        return self._reload()

    def action_create_folder(self):
        self.ensure_one()
        if not self.new_folder_name:
            raise UserError('Ingresa un nombre para la carpeta.')

        config = self.config_id
        url = f"{config.hostname}/createfolder"
        try:
            response = requests.get(url, params={
                'access_token': config.access_token,
                'name': self.new_folder_name,
                'folderid': self.current_folder_id,
            }, timeout=30)
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"Error pCloud: {data.get('error', 'desconocido')}")
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Error al crear carpeta: {str(e)}")

        self.new_folder_name = False
        self._load_contents()
        return self._reload()

    def action_upload_file(self):
        self.ensure_one()
        if not self.upload_file or not self.upload_filename:
            raise UserError('Selecciona un archivo.')

        config = self.config_id
        file_content = base64.b64decode(self.upload_file)

        url = f"{config.hostname}/uploadfile"
        try:
            response = requests.post(url, params={
                'access_token': config.access_token,
                'folderid': self.current_folder_id,
            }, files={
                'file': (self.upload_filename, file_content),
            }, timeout=120)
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"Error pCloud: {data.get('error', 'desconocido')}")
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Error al subir archivo: {str(e)}")

        self.write({'upload_file': False, 'upload_filename': False})
        self._load_contents()
        return self._reload()

    def action_rename_item(self):
        self.ensure_one()
        if not self.rename_item_name:
            raise UserError('Ingresa un nuevo nombre.')

        config = self.config_id
        endpoint = '/renamefolder' if self.rename_is_folder else '/renamefile'
        param_key = 'folderid' if self.rename_is_folder else 'fileid'

        url = f"{config.hostname}{endpoint}"
        try:
            response = requests.get(url, params={
                'access_token': config.access_token,
                param_key: self.rename_item_id,
                'toname': self.rename_item_name,
            }, timeout=30)
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"Error pCloud: {data.get('error', 'desconocido')}")
        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Error al renombrar: {str(e)}")

        self.write({
            'rename_item_id': 0,
            'rename_item_name': False,
            'rename_is_folder': False,
        })
        self._load_contents()
        return self._reload()

    def action_cancel_rename(self):
        self.ensure_one()
        self.write({
            'rename_item_id': 0,
            'rename_item_name': False,
            'rename_is_folder': False,
        })
        return self._reload()