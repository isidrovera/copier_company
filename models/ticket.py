from odoo import models, fields, api, _
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(related='producto_id.serie_id', string='Serie', readonly=True,)
    image = fields.Binary("Imagen", attachment=True, help="Imagen relacionada con el ticket.")
    nombre_reporta  = fields.Char(string='Nombre de quien reporto')
    ubicacion = fields.Char(related='producto_id.ubicacion', readonly=True, store=True, string='Ubicacion')
    celular_reporta = fields.Char(string='Celular')
 