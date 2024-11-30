from odoo import api, fields, models
import requests
import logging
import base64

_logger = logging.getLogger(__name__)

class ImageFromURLMixin(models.AbstractModel):
    _name = 'image.url.mixin'
    _description = 'Mixin para cargar imágenes desde URL'

    def get_image_from_url(self, url):
        """
        Obtiene y convierte una imagen desde una URL a base64
        :param url: URL de la imagen
        :return: Imagen codificada en base64
        """
        data = False
        if not url:
            return data
        try:
            response = requests.get(url.strip())
            if response.status_code == 200:
                data = base64.b64encode(response.content)
        except Exception as e:
            _logger.warning("No se pudo cargar la imagen desde la URL %s" % url)
            _logger.exception(e)
        return data

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
        store=True,
        attachment=True
    )

    @api.depends('imagen_url')
    def _compute_imagen_desde_url(self):
        for record in self:
            record.imagen_mostrar = self.get_image_from_url(record.imagen_url)

    
    
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
    
