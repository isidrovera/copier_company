from odoo import models, fields, api
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json

SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveIntegration(models.Model):
    _name = 'google.drive.integration'
    _description = 'Google Drive Integration'

    name = fields.Char('Description')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    redirect_uri = fields.Char('Redirect URI', compute='_compute_redirect_uri', store=True)
    authorized = fields.Boolean('Authorized', default=False)

    @api.depends('client_id', 'client_secret')
    def _compute_redirect_uri(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.redirect_uri = f"{base_url}/auth/google/callback"

    def authorize_google_drive(self):
        creds = None
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        token_file = '/mnt/extra-addons/google_drive_integration/token.json'

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    client_config, SCOPES)
                authorization_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true')
                return {
                    'type': 'ir.actions.act_url',
                    'url': authorization_url,
                    'target': 'new'
                }
        self.authorized = True
        return True
