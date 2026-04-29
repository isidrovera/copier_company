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
    # ABRIR SELECTOR
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
        Descarga archivos de OneDrive, crea ir.attachment y los liga al
        wizard escribiendo en `mail_attachments_widget` con el formato
        que Odoo 19 espera para que el correo los envíe realmente.

        Estructura de cada item del Json (según account_move_send.py):
            {
                'id': int,            # ID del ir.attachment (NO string)
                'name': str,
                'mimetype': str,
                'placeholder': False, # es archivo real
                'manual': True,       # preservado por _compute
            }
        """
        self.ensure_one()
        if not item_ids:
            return {"attachment_ids": [], "mail_attachments_widget": self.mail_attachments_widget}

        account = self.env["onedrive.account"].search([], limit=1)
        if not account:
            raise UserError(_("No hay cuenta OneDrive configurada"))

        service = GraphService(account)
        created_attachments = self.env["ir.attachment"]
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
                created_attachments |= attachment
            except Exception as e:
                _logger.exception("Error adjuntando item %s", item_id)
                errors.append(str(e))

        # ---------------------------------------------------------
        # Inyectar en mail_attachments_widget con el formato correcto
        # ---------------------------------------------------------
        if created_attachments:
            current = list(self.mail_attachments_widget or [])

            # Evitar duplicar si ya estaba ligado
            existing_ids = set()
            for item in current:
                try:
                    existing_ids.add(int(item.get("id")))
                except (TypeError, ValueError):
                    continue

            for att in created_attachments:
                if att.id in existing_ids:
                    continue
                current.append({
                    "id": att.id,
                    "name": att.name,
                    "mimetype": att.mimetype or "application/octet-stream",
                    "placeholder": False,
                    "manual": True,
                })

            self.mail_attachments_widget = current
            _logger.info(
                "OneDrive: %s attachment(s) añadidos a mail_attachments_widget del wizard %s",
                len(created_attachments), self.id,
            )

        return {
            "attachment_ids": created_attachments.ids,
            "errors": errors,
            # Devolvemos el widget actualizado para que el front
            # pueda refrescar el wizard sin recargar.
            "mail_attachments_widget": self.mail_attachments_widget or [],
        }