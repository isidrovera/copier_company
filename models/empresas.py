from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    allow_downloads = fields.Boolean(
        string='Permitir Descargas',
        default=False,
        help='Indica si este contacto tiene permiso para realizar descargas'
    )