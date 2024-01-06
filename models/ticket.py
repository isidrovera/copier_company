from odoo import models, fields, api, _
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(related='producto_id.serie_id', string='Serie', readonly=True,)
    image = fields.Binary("Imagen", attachment=True, help="Imagen relacionada con el ticket.")
    nombre_reporta  = fields.Char(
    string='Nombre de quien reporto'
    )

    @api.model
    def create(self, vals):
        # Llamar al método 'create' original para crear el ticket
        ticket = super(TicketCopier, self).create(vals)
        
        # Enviar correo electrónico utilizando la plantilla
        template = self.env.ref('copier_company.email_template_helpdesk_ticket_created', raise_if_not_found=False)
        if template:
            self.env['mail.template'].browse(template.id).send_mail(ticket.id, force_send=True)
        else:
            _logger.error(_('No se encontró la plantilla de correo electrónico.'))
        
        return ticket