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
    authorized = fields.Boolean('Authorized', default=False)

    def authorize_google_drive(self):
        creds = None
        if os.path.exists('/mnt/extra-addons/google_drive_integration/token.json'):
            creds = Credentials.from_authorized_user_file('/mnt/extra-addons/google_drive_integration/token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/mnt/extra-addons/google_drive_integration/credentials.json', SCOPES)
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
