from odoo import http
from odoo.http import request
import base64
from werkzeug import exceptions
import werkzeug
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PublicHelpdeskController(http.Controller):
    
    @http.route('/public/helpdesk_ticket_submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_helpdesk_ticket(self, **post):
        try:
            copier_company_id = post.get('copier_company_id')
            if not copier_company_id:
                raise UserError('ID de empresa no proporcionado')
            
            copier_company = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not copier_company.exists():
                return request.redirect('/public/helpdesk_ticket')

            image_content = None
            if 'image' in post and post['image']:
                image_field = post['image']
                if image_field.filename:
                    image_content = base64.b64encode(image_field.read())

            ticket_values = {
                'name': post.get('description'),
                'partner_id': copier_company.cliente_id.id,
                'producto_id': copier_company.id,
                'image': image_content,
                'nombre_reporta': post.get('nombre_reporta'),
                'celular_reporta': post.get('celular_reporta'),
            }
            new_ticket = request.env['helpdesk.ticket'].sudo().create(ticket_values)

            _logger.info('Ticket creado con ID: %s', new_ticket.id)

            # Enviar el correo de confirmación de forma inmediata
            new_ticket.send_confirmation_mail()
            # Luego, enviar el mensaje de WhatsApp
            new_ticket.send_whatsapp_confirmation()

            return request.redirect('/public/helpdesk_ticket_confirmation?ticket_id={}'.format(new_ticket.id))

        except werkzeug.exceptions.HTTPException as e:
            return request.redirect('/error?message={}'.format(e.description))
        except Exception as e:
            error_message = "Se produjo un error inesperado. Por favor, intente de nuevo más tarde."
            return request.redirect('/error?message={}'.format(error_message))

    @http.route('/public/helpdesk_ticket_confirmation', type='http', auth='public', website=True)
    def confirmation(self, **kwargs):
        ticket_id = request.params.get('ticket_id')
        ticket = request.env['helpdesk.ticket'].sudo().search([('id', '=', ticket_id)], limit=1)
        if ticket:
            _logger.info('Ticket recuperado con éxito: %s', ticket_id)
        else:
            _logger.warning('No se encontró el ticket con ID: %s', ticket_id)

        return request.render("copier_company.helpdesk_ticket_confirmation")


class ExternalPageController(http.Controller):
    @http.route('/external/login', auth='public', type='http', website=True)
    def render_external_login(self, **kw):
        # URL externa a la que quieres redirigir
        external_url = "https://app.printtrackerpro.com/auth/login"
        return request.redirect(external_url)
