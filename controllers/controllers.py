from odoo import http
from odoo.http import request
import json
import base64
from werkzeug import exceptions
from odoo.exceptions import UserError
from urllib.parse import quote
import logging
_logger = logging.getLogger(__name__)

class DescargaArchivosController(http.Controller):
    @http.route('/descarga/archivos', type='http', auth='user', website=True)
    def descarga_archivos(self, page=1, search='', **kw):
        # Convertir 'page' a un entero
        try:
            page = int(page)
        except ValueError:
            page = 1  # En caso de error, reiniciar a la primera página

        partner = request.env.user.partner_id
        items_per_page = 20

        # Verificar suscripciones activas
        subscriptions_in_progress = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('subscription_state', '=', '3_progress')
        ])

        if subscriptions_in_progress:
            domain = []
            if search:
                domain = ['|', '|',
                          ('name', 'ilike', '%' + search + '%'),
                          ('observacion', 'ilike', '%' + search + '%'),
                          ('modelo.name', 'ilike', '%' + search + '%')]
            
            # Si hay término de búsqueda, reiniciar la paginación a la primera página
            if search:
                page = 1
            
            total_docs = request.env['descarga.archivos'].sudo().search_count(domain)
            total_pages = ((total_docs - 1) // items_per_page) + 1
            page = max(min(page, total_pages), 1)
            offset = (page - 1) * items_per_page

            docs = request.env['descarga.archivos'].sudo().search(
                domain, offset=offset, limit=items_per_page
            )

            return request.render('copier_company.Descargas', {
                'docs': docs,
                'page': page,
                'total_pages': total_pages,
                'search': search
            })
        else:
            # Mostrar mensaje de suscripción expirada
            return request.render('copier_company.no_subscription_message')

    @http.route('/descarga/cloud', type='http', auth='user', website=True)
    def vista_nube(self, **kw):
        # Aquí simplemente renderizas una nueva plantilla que contendrá el iframe o la integración que prefieras
        return request.render('copier_company.Cloud', {})





class PortalAlquilerController(http.Controller):
    
    @http.route('/portal/alquiler', auth='public', website=True)
    def portal_alquiler_form(self, **kwargs):
        marcas = request.env['marcas.maquinas'].sudo().search([])
        # Elimina la siguiente línea, ya que no estás utilizando 'alquiler_id'
        # alquiler = request.env['cotizacion.alquiler'].sudo().browse(alquiler_id)
        return request.render('copier_company.portal_alquiler_form', {
            'marcas': marcas
        })

    @http.route('/portal/alquiler/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_alquiler_submit(self, **post):
        alquiler_vals = {
            'marca_id': int(post.get('marca_id')),
            'tipo': post.get('tipo'),
            'cantidad': post.get('cantidad'),
            'empresa': post.get('empresa'),
            'contacto': post.get('contacto'),
            'celular': post.get('celular'),
            'correo': post.get('correo'),
            'detalles': post.get('detalles'),
            'formato': post.get('formato'),
        }
        nuevo_alquiler = request.env['cotizacion.alquiler'].sudo().create(alquiler_vals)
        # Aquí, puedes redirigir al usuario a una página de confirmación o de vuelta al formulario con un mensaje de éxito
        return request.redirect('/ruta_de_confirmacion')
    @http.route('/ruta_de_confirmacion', auth='public', website=True)
    def confirmacion(self, **kwargs):
        return request.render('copier_company.confirmacion_template', {})





class HelpdeskTicketController(http.Controller):

    @http.route('/helpdesk/ticket/form', type='http', auth="public", website=True)
    def ticket_form(self, **kw):
        productos = request.env['copier.company'].sudo().search([])
        response = super(HelpdeskTicketController, self).ticket_form()
        response.qcontext.update({
            'productos': productos
        })
        return response






class PublicHelpdeskController(http.Controller):
    @http.route('/public/helpdesk_ticket', type='http', auth='public', website=True)
    def public_helpdesk_ticket(self, copier_company_id=None, **kwargs):
        copier_company = None
        partner_name = ''
        product_name = ''
        serie_id = ''
        sede = ''
        ubicacion = ''
        if copier_company_id:
            try:
                copier_company = request.env['copier.company'].sudo().browse(int(copier_company_id))
                if copier_company.exists():
                    partner_name = copier_company.cliente_id.name
                    product_name = copier_company.name
                    serie_id = copier_company.serie_id
                    sede = copier_company.sede
                    ubicacion = copier_company.ubicacion
            except ValueError:
                return request.redirect('/error')  # Redirige a una página de error en caso de un ID no válido

        return request.render("copier_company.public_helpdesk_ticket_form", {
            'copier_company_id': copier_company_id,
            'partner_name': partner_name,
            'product_name': product_name,
            'serie_id': serie_id,
            'sede' : sede,
            'ubicacion' : ubicacion

        })



    @http.route('/public/helpdesk_ticket_submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_helpdesk_ticket(self, **post):
        try:
            # Asegúrate de que el ID de copier_company es válido
            copier_company_id = post.get('copier_company_id')
            copier_company = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not copier_company.exists():
                return request.redirect('/public/helpdesk_ticket')  # Redirige de nuevo al formulario

            # Procesa la imagen cargada si existe
            image_content = None
            if 'image' in post and post['image']:
                image_field = post['image']
                if image_field.filename:
                    image_content = base64.b64encode(image_field.read())

            # Crea el ticket con los valores recibidos
            ticket_values = {
                'name': post.get('description'),
                'partner_id': copier_company.cliente_id.id,
                'producto_id': copier_company.id,
                'image': image_content,
                'nombre_reporta': post.get('nombre_reporta'),
            }
            new_ticket = request.env['helpdesk.ticket'].sudo().create(ticket_values)

            # Log para depuración
            _logger.info('Ticket creado con ID: %s', new_ticket.id)

            # Redirige a la página de confirmación con el ID del ticket
            return request.redirect('/public/helpdesk_ticket_confirmation?ticket_id={}'.format(new_ticket.id))

        except werkzeug.exceptions.HTTPException as e:
            return request.redirect('/error?message={}'.format(e.description))
        except Exception as e:
            error_message = "Se produjo un error inesperado. Por favor, intente de nuevo más tarde."
            return request.redirect('/error?message={}'.format(error_message))


    @http.route('/public/helpdesk_ticket_confirmation', type='http', auth='public', website=True)
    def confirmation(self, **kwargs):
        # Usar request.params para acceder a los parámetros de la solicitud
        ticket_id = request.params.get('ticket_id')
        ticket = request.env['helpdesk.ticket'].sudo().search([('id', '=', ticket_id)], limit=1)
        if ticket:
            mensaje = f"Hola, soy {ticket.nombre_reporta} de {ticket.partner_id.name}, ubicado en {ticket.ubicacion}. He reportado un problema con el equipo: {ticket.producto_id.name.name}, serie: {ticket.serie_id}. Por favor, revisen los detalles del ticket y pónganse en contacto conmigo para la asistencia correspondiente. Gracias."
            _logger.info('Ticket recuperado con éxito: %s', ticket_id)
        else:
            mensaje = "Hola, he reportado una incidencia pero parece que hubo un problema con el registro del ticket. Por favor, contacten conmigo directamente. Gracias."
            _logger.warning('No se encontró el ticket con ID: %s', ticket_id)

        mensaje_codificado = quote(mensaje)
        numero_destino = '+51975399303'
        whatsapp_url = f'https://api.whatsapp.com/send?phone={numero_destino}&text={mensaje_codificado}'

        script = f"""
        <script>
            setTimeout(function() {{
                window.open("{whatsapp_url}", '_blank');
            }}, 3000);
        </script>
        """

        response = request.render("copier_company.helpdesk_ticket_confirmation", {'whatsapp_script': script})
        return response
class PCloudController(http.Controller):
    @http.route('/pcloud/callback', type='http', auth='public', csrf=False)
    def pcloud_authenticate(self, **kw):
        if 'code' not in kw:
            return "No code provided by pCloud."
        
        pcloud_config = request.env['pcloud.config'].sudo().search([], limit=1)
        if not pcloud_config:
            return "PCloud configuration not found."
        
        try:
            pcloud_config.exchange_code_for_token(kw['code'])
            # Redirige al usuario a alguna página después de la autenticación exitosa
            return http.request.redirect('/my/pcloud/folders')
        except UserError as e:
            return str(e)

    @http.route(['/my/pcloud/folders'], type='http', auth='user', website=True)
    def list_pcloud_folders(self, **kwargs):
        pcloud_config_record = request.env['pcloud.config'].sudo().search([], limit=1)
        if not pcloud_config_record:
            return request.render('copier_company.no_pcloud_config')
        
        if not pcloud_config_record.access_token:
            # Redirige al usuario a la página de autenticación si no se encuentra el token
            auth_url = pcloud_config_record.generate_authorization_url()
            return http.request.redirect(auth_url)
        
        try:
            folder_list = pcloud_config_record.get_folder_list()
            return request.render('copier_company.pcloud_folder_list_template', {
                'folder_list': folder_list,
            })
        except UserError as e:
            # Maneja la posibilidad de un token caducado y necesita renovación
            if "token ha caducado" in str(e) or "No hay token de acceso disponible" in str(e):
                # Intenta renovar el token automáticamente si es posible
                try:
                    pcloud_config_record.refresh_access_token()
                    # Intenta obtener la lista de carpetas nuevamente después de la renovación del token
                    folder_list = pcloud_config_record.get_folder_list()
                    return request.render('copier_company.pcloud_folder_list_template', {
                        'folder_list': folder_list,
                    })
                except UserError as e2:
                    # Si la renovación falla, redirige para autenticación nuevamente
                    auth_url = pcloud_config_record.generate_authorization_url()
                    return http.request.redirect(auth_url)
            return str(e)  # Retorna el mensaje de error original si no es un problema de token caducado
class ExternalPageController(http.Controller):
    @http.route('/external/login', auth='public', website=True)
    def render_external_login(self, **kw):
        # Aquí se debe ingresar la URL real de la página que quieres mostrar en el iframe
        external_url = "https://app.printtrackerpro.com/auth/login"
        return request.render('copier_company.external_login_page_template', {'external_url': external_url})