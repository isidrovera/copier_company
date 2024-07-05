from odoo import http
from odoo.http import request

class CopierCompany(http.Controller):

    @http.route('/copier_company/form', type='http', auth='public', website=True)
    def copier_form(self, **kw):
        marcas = request.env['marcas.maquinas'].sudo().search([])
        return request.render('copier_company.copier_company_form_template', {'marcas': marcas})

    @http.route('/copier_company/submit', type='http', auth='public', methods=['POST'], website=True)
    def copier_submit(self, **post):
        cliente = request.env['res.partner'].sudo().search([('vat', '=', post.get('identificacion'))], limit=1)
        if not cliente:
            cliente = request.env['res.partner'].sudo().create({
                'name': post.get('cliente_name'),
                'vat': post.get('identificacion'),
                'l10n_latam_identification_type_id': int(post.get('tipo_identificacion')),
            })
        request.env['copier.company'].sudo().create({
            'name': post.get('name'),
            'serie_id': post.get('serie_id'),
            'cliente_id': cliente.id,
            'tipo': post.get('tipo'),
            'contacto': post.get('contacto'),
            'celular': post.get('celular'),
            'correo': post.get('correo'),
            'detalles': post.get('detalles'),
            'formato': post.get('formato'),
            'volumen_mensual_color': post.get('volumen_mensual_color'),
            'volumen_mensual_bn': post.get('volumen_mensual_bn'),
        })
        return request.redirect('/copier_company/thank_you')

    @http.route('/copier_company/get_customer_data', type='json', auth='public', methods=['GET'])
    def get_customer_data(self, tipo_identificacion, identificacion):
        partner = request.env['res.partner'].sudo().search([
            ('vat', '=', identificacion),
            ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', tipo_identificacion)
        ], limit=1)
        if partner:
            return {
                'success': True,
                'name': partner.name,
                'contact': partner.phone,
                'email': partner.email,
            }
        else:
            return {'success': False}
