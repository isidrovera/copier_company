# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging


class copier_company(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se veran los archivos de onedrive'
    _inherit = ['mail.thread', 'mail.activity.mixin']
       
    name = fields.Many2one('modelos.maquinas',string='Maquina')
    
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca', required=True,related='name.marca_id')
    cliente_id = fields.Many2one('res.partner',string='Cliente', required=True, )
    
    full_name = fields.Char(string='Nombre Completo', compute='_compute_full_name', store=True)

    @api.depends('name.name', 'serie_id')
    def _compute_full_name(self):
        for record in self:
            # Concatenación del nombre del modelo y el número de serie
            modelo_maquina = record.name.name if record.name else ''
            serie = record.serie_id or ''
            record.full_name = '{} Serie: {}'.format(modelo_maquina, serie)

    def name_get(self):
        result = []
        for record in self:
            # Se utiliza el campo computado full_name para la representación del nombre
            result.append((record.id, record.full_name))
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
        


