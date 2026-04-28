import base64
import requests
import logging

from odoo import models
from odoo.exceptions import UserError
from odoo.addons.odoo_onedrive_integration.services.graph_service import GraphService

_logger = logging.getLogger(__name__)


class AccountMoveSendWizard(models.TransientModel):
    _inherit = "account.move.send.wizard"

    # ---------------------------------------
    # ABRIR SELECTOR
    # ---------------------------------------
    def action_open_onedrive_browser(self):
        return {
            "type": "ir.actions.client",
            "tag": "onedrive_selector_dialog",
            "params": {
                "wizard_id": self.id,
            },
        }

    # ---------------------------------------
    # ADJUNTAR ARCHIVO
    # ---------------------------------------
    def action_attach_onedrive_file(self, item_id):
        self.ensure_one()

        account = self.env["onedrive.account"].search([], limit=1)
        if not account:
            raise UserError("No hay cuenta OneDrive configurada")

        service = GraphService(account)

        item = service.get_item(item_id)

        if "folder" in item:
            raise UserError("No puedes adjuntar carpetas")

        url = item.get("@microsoft.graph.downloadUrl")

        r = requests.get(url)
        if r.status_code != 200:
            raise UserError("Error descargando archivo")

        attachment = self.env["ir.attachment"].create({
            "name": item.get("name"),
            "datas": base64.b64encode(r.content),
            "res_model": "account.move",
            "res_id": self.move_id.id,
        })

        return True