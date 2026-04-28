import base64
import logging
import requests

from odoo import models, fields
from odoo.exceptions import UserError

# IMPORTANTE: usa tu servicio existente
from odoo.addons.odoo_onedrive_integration.services.graph_service import GraphService

_logger = logging.getLogger(__name__)


class AccountMoveSendWizard(models.TransientModel):
    _inherit = "account.move.send.wizard"

    # ---------------------------------------
    # CAMPOS
    # ---------------------------------------

    onedrive_item_id = fields.Char("Archivo OneDrive")
    onedrive_filename = fields.Char("Nombre archivo")

    # ---------------------------------------
    # DESCARGAR ARCHIVO DESDE ONEDRIVE
    # ---------------------------------------

    def _fetch_onedrive_file(self):
        self.ensure_one()

        if not self.onedrive_item_id:
            return None

        account = self.env['onedrive.account'].search([], limit=1)
        if not account:
            raise UserError("No hay cuenta OneDrive configurada")

        service = GraphService(account)

        # Obtener metadata del archivo
        item = service.get_item(self.onedrive_item_id)

        download_url = item.get("@microsoft.graph.downloadUrl")
        filename = item.get("name")

        if not download_url:
            raise UserError("No se pudo obtener la URL de descarga")

        _logger.info("Descargando archivo OneDrive: %s", filename)

        response = requests.get(download_url, timeout=60)

        if response.status_code != 200:
            raise UserError("Error descargando archivo desde OneDrive")

        return filename, base64.b64encode(response.content)

    # ---------------------------------------
    # INYECTAR ADJUNTO EN EL CORREO
    # ---------------------------------------

    def _get_mail_values(self, res_ids):
        result = super()._get_mail_values(res_ids)

        for res_id in res_ids:
            if self.onedrive_item_id:

                file_data = self._fetch_onedrive_file()

                if file_data:
                    filename, data = file_data

                    attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'datas': data,
                        'res_model': 'account.move',
                        'res_id': res_id,
                        'type': 'binary',
                    })

                    _logger.info("Adjunto creado desde OneDrive: %s", filename)

                    # Añadir al correo
                    result[res_id]['attachment_ids'] = result[res_id].get('attachment_ids', []) + [(4, attachment.id)]

        return result


    def action_load_onedrive_file(self):
        self.ensure_one()

        file_data = self._fetch_onedrive_file()

        if not file_data:
            return

        filename, data = file_data

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': data,
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'type': 'binary',
        })

        # 🔥 esto lo agrega al widget de adjuntos en vivo
        self.message_main_attachment_id = attachment.id

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }