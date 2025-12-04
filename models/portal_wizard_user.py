# -*- coding: utf-8 -*-
import logging

from odoo import models  # 👈 ESTE IMPORT FALTABA
from odoo.exceptions import MissingError, UserError

_logger = logging.getLogger(__name__)


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _safe_super_call(self, method_name):
        """
        Ejecuta el método original de Odoo (action_grant_access / action_invite_again)
        solo sobre los registros que todavía existen, y traga el MissingError para
        evitar el popup 'Record does not exist or has been deleted'.
        """
        existing = self.exists()

        if not existing:
            _logger.info(
                "PortalWizardUser._safe_super_call: no existing records, nothing to do "
                "for method %s", method_name
            )
            return True

        method = getattr(super(PortalWizardUser, existing), method_name)

        try:
            _logger.info(
                "PortalWizardUser._safe_super_call: calling super(%s) on ids %s",
                method_name, existing.ids
            )
            # Aquí se ejecuta la lógica estándar de Odoo:
            # - crea/activa usuario portal
            # - llama a _send_email()
            return method()
        except MissingError:
            _logger.exception(
                "PortalWizardUser._safe_super_call: MissingError ignored for ids %s",
                existing.ids
            )
            return True

    def action_grant_access(self):
        """Parche de 'Conceder acceso' que evita el error de registro faltante."""
        return self._safe_super_call("action_grant_access")

    def action_invite_again(self):
        """Parche de 'Reenviar invitación' que evita el error de registro faltante."""
        return self._safe_super_call("action_invite_again")

    def _send_email(self):
        """Enviar correo de invitación al portal (mismo comportamiento que Odoo),
        pero con logs para poder depurar.
        """
        self.ensure_one()

        _logger.info(
            "COPIER_PORTAL: preparando envío de email de portal para wizard_user %s "
            "(partner_id=%s, email=%s)",
            self.id, self.partner_id.id, self.email,
        )

        template = self.env.ref(
            'auth_signup.portal_set_password_email',
            raise_if_not_found=False,
        )
        if not template:
            _logger.error(
                "COPIER_PORTAL: plantilla 'auth_signup.portal_set_password_email' "
                "NO encontrada."
            )
            raise UserError(
                'The template "Portal: new user" not found for sending email to the portal user.'
            )

        user = self.user_id.sudo()
        if not user:
            _logger.error(
                "COPIER_PORTAL: _send_email llamado sin user_id para wizard_user %s "
                "(partner_id=%s)",
                self.id, self.partner_id.id,
            )
            return True

        lang = user.lang
        partner = user.partner_id
        partner.signup_prepare()

        _logger.info(
            "COPIER_PORTAL: enviando mail de portal a user %s login=%s email=%s lang=%s",
            user.id, user.login, user.email, lang,
        )

        template.with_context(
            dbname=self.env.cr.dbname,
            lang=lang,
            welcome_message=self.wizard_id.welcome_message,
            medium='portalinvite',
        ).send_mail(user.id, force_send=True)

        _logger.info(
            "COPIER_PORTAL: correo de portal enviado/queueado para user %s",
            user.id,
        )

        return True
