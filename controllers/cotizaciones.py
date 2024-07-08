import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class CopierCompany(http.Controller):

    @http.route('/copier_company/form', type='http', auth="public", website=True)
    def copier_company_form(self, **kwargs):
        try:
            marcas = request.env['marcas.maquinas'].sudo().search([])
            tipos_identificacion = request.env['l10n_latam.identification.type'].sudo().search([])
            _logger.info('Form loaded with %s marcas and %s tipos_identificacion', len(marcas), len(tipos_identificacion))
            return request.render('copier_company.copier_company_form_template', {
                'marcas': marcas,
                'tipos_identificacion': tipos_identificacion
            })
        except Exception as e:
            _logger.error('Failed to load form: %s', str(e))
            return request.render('web.http_error', {'status_code': 'Error', 'status_message': str(e)})

    @http.route('/copier_company/get_customer_data', type='json', auth="public")
    def get_customer_data(self, **kwargs):
        tipo_identificacion = kwargs.get('tipo_identificacion')
        identificacion = kwargs.get('identificacion')
        _logger.debug('Searching for customer with ID type %s and ID %s', tipo_identificacion, identificacion)
        try:
            partner = request.env['res.partner'].sudo().search([
                ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', tipo_identificacion),
                ('vat', '=', identificacion)
            ], limit=1)
            if partner:
                _logger.info('Customer found: %s', partner.name)
                return {
                    'jsonrpc': '2.0',
                    'result': {
                        'success': True,
                        'name': partner.name,
                        'phone': partner.phone,
                        'email': partner.email
                    }
                }
            else:
                # Crear un nuevo cliente si no existe
                _logger.info('Customer not found, creating a new one')
                new_partner = request.env['res.partner'].sudo().create({
                    'vat': identificacion,
                    'l10n_latam_identification_type_id': request.env['l10n_latam.identification.type'].search([('l10n_pe_vat_code', '=', tipo_identificacion)], limit=1).id,
                    'name': 'Cargando...',
                })
                # Actualizar el nombre y otros datos del nuevo cliente
                new_partner._doc_number_change()
                if new_partner.name == 'Cargando...':
                    new_partner.name = identificacion
                
                return {
                    'jsonrpc': '2.0',
                    'result': {
                        'success': True,
                        'name': new_partner.name,
                        'phone': new_partner.phone,
                        'email': new_partner.email
                    }
                }
        except Exception as e:
            _logger.error('Error searching or creating customer: %s', str(e))
            return {'jsonrpc': '2.0', 'error': {'code': 500, 'message': 'Internal Server Error', 'data': str(e)}}

    @http.route('/copier_company/submit', type='http', auth="public", website=True)
    def copier_company_submit(self, **kwargs):
        _logger.info('Processing form submission')
        return request.render('copier_company.confirmacion_template')
