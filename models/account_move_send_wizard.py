import base64
import logging
import requests

from odoo import models, _
from odoo.exceptions import UserError

from odoo.addons.odoo_onedrive_integration.services.graph_service import GraphService

_logger = logging.getLogger(__name__)


class AccountMoveSendWizard(models.TransientModel):
    _inherit = "account.move.send.wizard"

    # ---------------------------------------------------------
    # ABRIR SELECTOR (lanza el dialogo OWL)
    # ---------------------------------------------------------
    def action_open_onedrive_browser(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "onedrive_selector_dialog",
            "params": {
                "wizard_id": self.id,
                "move_id": self.move_id.id,
            },
        }

    # ---------------------------------------------------------
    # ADJUNTAR MULTIPLES ARCHIVOS
    # ---------------------------------------------------------
    def action_attach_onedrive_files(self, item_ids):
        """
        Recibe una lista de item_ids de OneDrive, descarga cada archivo,
        crea los ir.attachment ligados al account.move y devuelve la
        info necesaria para que el wizard refresque su lista de adjuntos.
        """
        self.ensure_one()
        if not item_ids:
            return {"attachment_ids": []}

        account = self.env["onedrive.account"].search([], limit=1)
        if not account:
            raise UserError(_("No hay cuenta OneDrive configurada"))

        service = GraphService(account)
        created_ids = []
        errors = []

        for item_id in item_ids:
            try:
                item = service.get_item(item_id)
                if "folder" in item:
                    errors.append(_("'%s' es una carpeta") % item.get("name"))
                    continue

                url = item.get("@microsoft.graph.downloadUrl")
                if not url:
                    errors.append(_("Sin URL de descarga: %s") % item.get("name"))
                    continue

                r = requests.get(url, timeout=120)
                if r.status_code != 200:
                    errors.append(_("Error descargando: %s") % item.get("name"))
                    continue

                attachment = self.env["ir.attachment"].create({
                    "name": item.get("name"),
                    "datas": base64.b64encode(r.content),
                    "res_model": "account.move",
                    "res_id": self.move_id.id,
                    "mimetype": (item.get("file") or {}).get("mimeType")
                                or "application/octet-stream",
                })
                created_ids.append(attachment.id)
            except Exception as e:
                _logger.exception("Error adjuntando item %s", item_id)
                errors.append(str(e))

        # Recalcular el widget de adjuntos del wizard.
        # En Odoo 19 el wizard arma mail_attachments_widget a partir
        # de los attachments del move + plantilla; basta con invalidar
        # el cache del campo computado para que se refresque.
        self.invalidate_recordset(["mail_attachments_widget"])

        return {
            "attachment_ids": created_ids,
            "errors": errors,
        }