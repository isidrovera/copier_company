from odoo import models, fields, api

class ModelosMaquinas(models.Model):
    _name = 'modelos.maquinas'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El modelo de la máquina debe ser único!')
    ]
    name = fields.Char(string='Modelo', required=True, index=True)
    marca_id = fields.Many2one('marcas.maquinas',string='Marca')
    especificaciones = fields.Html(string="Especificaciones")
    active = fields.Boolean(string="Activo", default=True)
    
class MarcasMaquinas(models.Model):
    _name = 'marcas.maquinas'
    name = fields.Char(string='Marca')
    
class AccesoriosMaquinas(models.Model):
    _name = 'accesorios.maquinas'
    name = fields.Char(string='Accesorio')
class CopierEstados(models.Model):
    _name = 'copier.estados'
    _description = 'Copier States'

    name = fields.Char(string="Name", required=True)

class CopierDuracionAlquiler(models.Model):
    
    _name='copier.duracion'
    _description = 'Aqui se crean el tiempo de duracion de alquiler'
    name = fields.Char(string='Duración')
    