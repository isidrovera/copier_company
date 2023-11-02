from odoo import models, fields, api

class ModelosMaquinas(models.Model):
    _name = 'modelos.maquinas'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El modelo de la máquina debe ser único!')
    ]
    name = fields.Char(string='Modelo', required=True, index=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca')
    active = fields.Boolean(string="Activo", default=True)
    
class MarcasMaquinas(models.Model):
    _name = 'marcas.maquinas'
    name = fields.Char(string='Marca')
    