# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import MissingError


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _safe_super_call(self, method_name):
        """
        Ejecuta el método original de Odoo (action_grant_access / action_invite_again)
        solo sobre los registros que todavía existen, y traga el MissingError para
        evitar el popup 'Record does not exist or has been deleted'.
        """
        # Filtrar solo los registros que siguen existiendo en BD
        existing = self.exists()

        # Si ya no hay ninguno, no hacemos nada (y por tanto no se envía correo)
        if not existing:
            return True

        # Buscar el método original sobre ese recordset
        method = getattr(super(PortalWizardUser, existing), method_name)

        try:
            # Aquí se ejecuta la lógica estándar:
            # - crea/activa usuario portal
            # - llama a _send_email() con la plantilla auth_signup.portal_set_password_email
            return method()
        except MissingError:
            # Si aun así Odoo lanza MissingError por un registro fantasma, no rompemos la UI
            return True

    def action_grant_access(self):
        """Parche de 'Conceder acceso' que evita el error de registro faltante."""
        return self._safe_super_call("action_grant_access")

    def action_invite_again(self):
        """Parche de 'Reenviar invitación' que evita el error de registro faltante."""
        return self._safe_super_call("action_invite_again")
