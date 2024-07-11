from odoo import http
from odoo.http import request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveController(http.Controller):

    @http.route('/auth/google/callback', type='http', auth='public', csrf=False)
    def google_auth_callback(self, **kw):
        state = request.params.get('state')
        flow = InstalledAppFlow.from_client_secrets_file(
            '/mnt/extra-addons/google_drive_integration/credentials.json', SCOPES, state=state)
        flow.fetch_token(authorization_response=request.httprequest.url)
        credentials = flow.credentials
        with open('/mnt/extra-addons/google_drive_integration/token.json', 'w') as token:
            token.write(credentials.to_json())
        return request.render('google_drive_integration.auth_callback', {})
