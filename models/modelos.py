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
    imagen = fields.Binary(string='Imagen', attachment=True, 
    store=True
    )
    imagen_url = fields.Char(
        string='URL de la imagen',
        help="Ingrese la URL de la imagen de la máquina"
    )
    imagen_mostrar = fields.Binary(
        string='Vista previa',
        compute='_compute_imagen_desde_url',
        store=True
    )

    @api.depends('imagen_url')
    def _compute_imagen_desde_url(self):
        for record in self:
            if record.imagen_url:
                try:
                    import requests
                    response = requests.get(record.imagen_url)
                    if response.status_code == 200:
                        record.imagen_mostrar = base64.b64encode(response.content)
                except Exception:
                    record.imagen_mostrar = False
            else:
                record.imagen_mostrar = False
    
    
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
    