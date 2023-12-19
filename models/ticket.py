from odoo import models, fields, api

class TicketCopier(models.Model):
    _inherit = 'helpdesk.ticket'
    
    producto_id = fields.Many2one('copier.company', string='Máquina')
    producto_display_name = fields.Char(string='Nombre de Máquina', compute='_compute_producto_display_name')

    @api.depends('producto_id')
    def _compute_producto_display_name(self):
        for record in self:
            if record.producto_id:
                record.producto_display_name = f"{record.producto_id.name} Serie: {record.producto_id.serie_id}"
            else:
                record.producto_display_name = ''
