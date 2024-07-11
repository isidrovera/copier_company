from odoo import http
from odoo.http import request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveController(http.Controller):

    @http.route('/auth/google/callback', type='http', auth='public', csrf=False)
    def google_auth_callback(self, **kw):
        integration = request.env['google.drive.integration'].search([], limit=1)
        if not integration:
            return "No integration configuration found"

        client_config = {
            "web": {
                "client_id": integration.client_id,
                "client_secret": integration.client_secret,
                "redirect_uris": [integration.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        state = request.params.get('state')
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES, state=state)
        flow.fetch_token(authorization_response=request.httprequest.url)
        credentials = flow.credentials
        integration.save_credentials(credentials)
        
        return request.render('google_drive_integration.auth_callback', {})
