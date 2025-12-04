# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import MissingError


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _safe_super_call(self, method_name):
        """
        Ejecuta el método del padre únicamente sobre los registros que aún existen.
        Evita el error 'Record does not exist' cuando Odoo elimina el wizard
        automáticamente después de procesarlo.
        """
        # Filtrar registros que sí existen (Odoo borra los transient muy rápido)
        existing = self.exists()

        # Si ya no existen, simplemente no hacemos nada.
        if not existing:
            return True

        # Obtener referencia al método original sobre los registros existentes
        method = getattr(super(PortalWizardUser, existing), method_name)

        try:
            # Ejecutar el método original (envía correo de invitación)
            return method()
        except MissingError:
            # Si aún así falla por un race condition, ignoramos el error
            return True

    def action_grant_access(self):
        """
        Otorga acceso al portal SIN romper la interfaz ni generar el popup.
        """
        return self._safe_super_call("action_grant_access")

    def action_invite_again(self):
        """
        Reenvía invitación SIN generar el error de registro inexistente.
        """
        return self._safe_super_call("action_invite_again")
