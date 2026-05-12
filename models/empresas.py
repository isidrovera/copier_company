from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    allow_downloads = fields.Boolean(
        string='Permitir Descargas',
        default=False,
        help='Indica si este contacto tiene permiso para realizar descargas'
    )

    portal_empresa_ids = fields.Many2many(
        'res.partner',
        'res_partner_portal_empresa_rel',
        'contacto_id',
        'empresa_id',
        string='Empresas visibles en portal',
        domain=[('is_company', '=', True)],
        help='Empresas adicionales cuyos equipos podrá ver este contacto en el portal.'
    )