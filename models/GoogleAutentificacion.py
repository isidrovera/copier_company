from odoo import models, fields, api
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

class GoogleDriveIntegration(models.Model):
    _name = 'google.drive.integration'
    _description = 'Google Drive Integration'

    name = fields.Char('Description')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    redirect_uri = fields.Char('Redirect URI', compute='_compute_redirect_uri', store=True)
    authorized = fields.Boolean('Authorized', default=False)
    access_token = fields.Text('Access Token')
    refresh_token = fields.Text('Refresh Token')
    token_uri = fields.Char('Token URI', default='https://oauth2.googleapis.com/token')

    @api.depends('client_id', 'client_secret')
    def _compute_redirect_uri(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.redirect_uri = f"{base_url}/google_drive/authentication"
            print(f"Computed redirect URI: {record.redirect_uri}")  # Depuración

    def authorize_google_drive(self):
        creds = None
        if self.access_token and self.refresh_token:
            creds = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri=self.token_uri,
                client_id=self.client_id,
                client_secret=self.client_secret
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.access_token = creds.token
                self.refresh_token = creds.refresh_token
            else:
                client_config = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [self.redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                authorization_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true'
                )
                print(f"Authorization URL: {authorization_url}")  # Depuración
                return {
                    'type': 'ir.actions.act_url',
                    'url': authorization_url,
                    'target': 'new'
                }
        self.authorized = True
        return True

    def save_credentials(self, creds):
        self.access_token = creds.token
        self.refresh_token = creds.refresh_token
        self.authorized = True
        self.save()

    def list_files(self):
        creds = Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items
