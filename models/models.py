# -*- coding: utf-8 -*-

from odoo import models, fields, api


class copier_company(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se veran los archivos de onedrive'
    _inherit = ['mail.thread', 'mail.activity.mixin']
       
    name = fields.Many2one('modelos.maquinas',string='Maquina')
    
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca', required=True,)
    cliente_id = fields.Many2one('res.partner',string='Cliente', required=True, )
    
    _rec_name = 'serie_id'

    def name_get(self):
        result = []
        for record in self:
            name = '[  ' + record.name.name + '  ]   ' + \
                'Serie: ' + record.serie_id
            result.append((record.id, name))
        return result  
    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket']
        ticket_id = ticket.create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            

        })
        return {
            'name': 'Registro',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',

        }
        


