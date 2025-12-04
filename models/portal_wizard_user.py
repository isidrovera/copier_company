# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import MissingError

class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _safe_super_call(self, method_name):
        """
        Ejecuta un método del padre solo sobre registros que realmente existen.
        Si los registros ya no existen (cron o rollback), no rompe la UI.
        """
        existing = self.exists()
        if not existing:
            # Nada que hacer: el wizard ya no existe
            return True

        # Llamada segura al super sobre el recordset existente
        method = getattr(super(PortalWizardUser, existing), method_name)
        try:
            return method()
        except MissingError:
            # Si aun así se produce un MissingError, ignoramos la llamada
            return True

    def action_grant_access(self):
        """
        Parche para evitar el popup 'Record does not exist'
        al conceder acceso al portal.
        """
        return self._safe_super_call("action_grant_access")

    def action_invite_again(self):
        """
        Parche para evitar el popup 'Record does not exist'
        al reenviar la invitación al portal.
        """
        return self._safe_super_call("action_invite_again")
