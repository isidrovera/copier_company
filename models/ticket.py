from odoo import models, fields, api, _


class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Serie')
    serie_id = fields.Char(
    related='producto_id.name.name', 
    string='Modelo',
    
    readonly=True,
 
    )
    