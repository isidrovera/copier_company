# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class CopierCompany(http.Controller):

    @http.route('/copier_company/form', type='http', auth="public", website=True)
    def copier_company_form(self, **kwargs):
        marcas = request.env['marcas.maquinas'].sudo().search([])
        tipos_identificacion = request.env['l10n_latam.identification.type'].sudo().search([])
        return request.render('copier_company.copier_company_form_template', {
            'marcas': marcas,
            'tipos_identificacion': tipos_identificacion
        })

    @http.route('/copier_company/get_customer_data', type='json', auth="public")
    def get_customer_data(self, **kwargs):
        tipo_identificacion = kwargs.get('tipo_identificacion')
        identificacion = kwargs.get('identificacion')
        partner = request.env['res.partner'].sudo().search([
            ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', tipo_identificacion),
            ('vat', '=', identificacion)
        ], limit=1)
        if partner:
            return {
                'jsonrpc': '2.0',
                'result': {
                    'success': True,
                    'name': partner.name,
                    'phone': partner.phone,
                    'email': partner.email
                }
            }
        return {
            'jsonrpc': '2.0',
            'result': {'success': False}
        }

    @http.route('/copier_company/submit', type='http', auth="public", website=True)
    def copier_company_submit(self, **kwargs):
        # Implementa la lógica para procesar y guardar los datos del formulario
        return request.render('copier_company.confirmacion_template')
