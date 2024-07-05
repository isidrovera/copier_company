from odoo import http
from odoo.http import request

class CopierCompanyController(http.Controller):

    @http.route('/copier_company/form', type='http', auth='public', website=True)
    def copier_company_form(self, **kwargs):
        # Renderizar el formulario
        marcas = request.env['marcas.maquinas'].search([])
        return request.render('copier_company.copier_company_form_template', {
            'marcas': marcas
        })

    @http.route('/copier_company/submit', type='http', auth='public', website=True, csrf=True, methods=['POST'])
    def copier_company_submit(self, **post):
        # Procesar los datos del formulario y crear el registro
        cliente = request.env['res.partner'].search([('vat', '=', post['identificacion'])], limit=1)
        if not cliente:
            cliente = request.env['res.partner'].create({
                'vat': post['identificacion'],
                'name': 'Cargando...',
                'l10n_latam_identification_type_id': int(post['tipo_identificacion'])
            })
            cliente._doc_number_change()

        request.env['copier.company'].create({
            'name': int(post['name']),
            'serie_id': post['serie_id'],
            'marca_id': int(post['marca_id']),
            'cliente_id': cliente.id,
            'tipo_identificacion': int(post['tipo_identificacion']),
            'identificacion': post['identificacion'],
            'tipo': post['tipo'],
            'contacto': post['contacto'],
            'celular': post['celular'],
            'correo': post['correo'],
            'detalles': post['detalles'],
            'formato': post['formato'],
            'volumen_mensual_color': int(post['volumen_mensual_color']),
            'volumen_mensual_bn': int(post['volumen_mensual_bn']),
        })

        return request.redirect('/copier_company/form')

    @http.route('/copier_company/fetch_cliente', type='json', auth='public')
    def fetch_cliente(self, identificacion):
        cliente = request.env['res.partner'].search([('vat', '=', identificacion)], limit=1)
        if cliente:
            return {
                'success': True,
                'name': cliente.name,
                'tipo_identificacion': cliente.l10n_latam_identification_type_id.id,
            }
        else:
            return {'success': False}
