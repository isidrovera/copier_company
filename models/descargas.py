from odoo import models, fields, api,http

class DescargaArchivos(models.Model):
    _name = 'descarga.archivos'
    
    url = fields.Char(string='URL del archivo'     )
    name = fields.Char(string="Nombre de archivo"    )
    modelo = fields.Many2many('modelos.maquinas',string="Modelo de maquina"    )
    observacion = fields.Text(string="Descripción"    )
    tipo = fields.Selection(string='Tipo', selection=[('base', 'Base'),('especial','Especial')])
    icono = fields.Binary()
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'El nombre del archivo debe ser único.')
    ]
    adjunto = fields.Binary(
    string='Adjunto'
    
    )
    fecha = fields.Date(string='Fecha')
    
    def open_url(self):
        for record in self:
            return {
                'type': 'ir.actions.act_url',
                'url': record.url,
                'target': 'new',
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Descarga exitosa',
                'message': 'La descarga se realizó correctamente. Este archivo no debe ser revendido.',
                'type': 'success',
            },
        }


