from odoo import http
from odoo.http import request
import base64
from werkzeug import exceptions
import werkzeug
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)




class ExternalPageController(http.Controller):
    @http.route('/external/login', auth='public', type='http', website=True)
    def render_external_login(self, **kw):
        # URL externa a la que quieres redirigir
        external_url = "https://app.printtrackerpro.com/auth/login"
        return request.redirect(external_url)
