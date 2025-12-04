from odoo.tools import email_normalize
from odoo.exceptions import UserError


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def _send_email(self):
        """Enviar correo de invitación al portal (mismo comportamiento que Odoo),
        pero con logs para poder depurar.
        """
        self.ensure_one()

        _logger.info(
            "COPIER_PORTAL: preparando envío de email de portal para wizard_user %s (partner_id=%s, email=%s)",
            self.id, self.partner_id.id, self.email,
        )

        # Misma plantilla que el core
        template = self.env.ref('auth_signup.portal_set_password_email', raise_if_not_found=False)
        if not template:
            _logger.error(
                "COPIER_PORTAL: plantilla 'auth_signup.portal_set_password_email' NO encontrada."
            )
            # Mantenemos el mismo comportamiento que el core
            raise UserError(_('The template "Portal: new user" not found for sending email to the portal user.'))

        # user_id debería estar calculado a partir de partner.user_ids
        user = self.user_id.sudo()
        if not user:
            _logger.error(
                "COPIER_PORTAL: _send_email llamado sin user_id para wizard_user %s (partner_id=%s)",
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

        # Este send_mail crea un mail.mail y lo deja en cola o lo envía (force_send=True)
        template.with_context(
            dbname=self.env.cr.dbname,
            lang=lang,
            welcome_message=self.wizard_id.welcome_message,
            medium='portalinvite',
        ).send_mail(user.id, force_send=True)

        _logger.info("COPIER_PORTAL: correo de portal enviado/queueado para user %s", user.id)

        return True
