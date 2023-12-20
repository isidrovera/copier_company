from odoo import models, fields, api, _


class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Maquina')
    serie_id = fields.Char(
    related='producto_id.serie_id', 
    string='Serie',
    
    readonly=True,
 
    )
    

    def name_get(self):
        result = []
        for record in self:
            # Esto comprueba si el ticket tiene una máquina asociada y utiliza su full_name
            if record.producto_id:
                name = record.producto_id.full_name
            else:
                # Si no hay una máquina asociada, utiliza el nombre estándar del ticket
                name = super(TicketCopier, self).name_get()[0][1]
            result.append((record.id, name))
        return result