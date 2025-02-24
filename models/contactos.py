from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    has_license = fields.Boolean(string='Tiene Licencia', default=False)
