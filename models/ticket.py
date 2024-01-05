from odoo import models, fields, api, _


class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(related='producto_id.name.name', string='Serie', readonly=True,)
    image = fields.Binary("Imagen", attachment=True, help="Imagen relacionada con el ticket.")
    nombre_reporta  = fields.Char(
    string='Nombre de quien reporto'
    )