# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import MissingError


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _safe_super_call(self, method_name, force_reset_password=False):
        """
        Ejecuta un método del padre solo sobre registros que realmente existen.
        Opcionalmente, fuerza el envío de correo de reset/invitación
        para los usuarios portal asociados a los partners del wizard.
        """
        existing = self.exists()
        Users = self.env['res.users'].sudo()

        # 1) Si ya no hay registros, no hay nada que hacer
        if not existing:
            return True

        # 2) Llamar al método original de Odoo
        try:
            method = getattr(super(PortalWizardUser, existing), method_name)
            res = method()
        except MissingError:
            # Si revienta por un registro huérfano, no rompemos la UI
            res = True

        # 3) (Opcional) Forzar envío de correo de creación/reset de contraseña
        if force_reset_password:
            for wiz in existing:
                # Lo ideal es que user_id ya esté puesto por el super()
                user = wiz.user_id
                if not user:
                    # Respaldo: buscar usuario por partner, por si acaso
                    user = Users.search([
                        ('partner_id', '=', wiz.partner_id.id)
                    ], limit=1)

                if user and user.email:
                    try:
                        user.action_reset_password()
                    except Exception:
                        # No rompemos todo si falla el SMTP o similar
                        continue

        return res

    def action_grant_access(self):
        """
        Parche para evitar el popup 'Record does not exist'
        al conceder acceso al portal, y forzar envío del correo.
        """
        # Aquí decimos: usa _safe_super_call y obliga reset_password
        return self._safe_super_call("action_grant_access", force_reset_password=True)

    def action_invite_again(self):
        """
        Parche para evitar el popup 'Record does not exist'
        al reenviar la invitación al portal, y reenviar el correo.
        """
        return self._safe_super_call("action_invite_again", force_reset_password=True)
