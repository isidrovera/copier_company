from odoo import models, fields, api

class ModelosMaquinas(models.Model):
    _name = 'modelos.maquinas'
    name = fields.Char(string='Modelo')
    marca_id = fields.Many2one('marcas.maquinas',string='Marca')
    active = fields.Boolean(string="Activo", default=True)
    
class MarcasMaquinas(models.Model):
    _name = 'marcas.maquinas'
    name = fields.Char(string='Marca')
    