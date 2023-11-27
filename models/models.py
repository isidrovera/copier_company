# -*- coding: utf-8 -*-

from odoo import models, fields, api


class copier_company(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se veran los archivos de onedrive'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'serie_id'
    name = fields.Many2one('modelos.maquinas',string='Maquina')
    
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca', required=True,related='name.marca_id')
    cliente_id = fields.Many2one('res.partner',string='Cliente', required=True, )
    
    def name_get(self):
        result = []
        for record in self:
            # Asumiendo que el modelo relacionado 'modelos.maquinas' tiene un campo 'display_name' o 'name'.
            maquina_name = record.name.display_name if record.name else ''
            serie = record.serie_id or ''
            # Combina el nombre de la máquina y la serie para mostrar.
            name_combined = f"[{maquina_name}] Serie: {serie}"
            result.append((record.id, name_combined))
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
        


