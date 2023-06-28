# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OnedriveDocumentos(models.Model):
    _name = 'onedrive.documentos'
    _inherit = ['mail.thread']
    _description = 'Aqui se puede ver y descargar los archivos de onedrive'
    client_id = fields.Char(string='TU_CLIENT_ID')
    client_secret = fields.Char(string='TU_CLIENT_SECRET')
    redirect_uri = fields.Char(string='TU_REDIRECT_URI')
    auth_url = fields.Char(string='auth_url')
    token_url = fields.Char(string='token_url')
    scope = fields.Char(string='scope')
    
    