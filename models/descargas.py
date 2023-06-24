from odoo import models, fields, api,http

class DescargaArchivos(models.Model):
    _name = 'descarga.archivos'
    
    url = fields.Char(string='URL del archivo'     )
    name = fields.Char(string="Nombre de archivo"    )
    modelo = fields.Many2one('modelos.maquinas',string="Modelo de maquina"    )
    observacion = fields.Text(string="Descripción"    )
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'El nombre del archivo debe ser único.')
    ]
    
    
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


