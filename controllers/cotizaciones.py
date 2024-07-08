import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class CopierCompany(http.Controller):

    @http.route('/cotizacion/form', type='http', auth="public", website=True)
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
                        'id': partner.id,
                        'name': partner.name,
                        'phone': partner.phone or '',
                        'email': partner.email or ''
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
                        'id': new_partner.id,
                        'name': new_partner.name,
                        'phone': '',
                        'email': ''
                    }
                }
        except Exception as e:
            _logger.error('Error searching or creating customer: %s', str(e))
            return {'jsonrpc': '2.0', 'error': {'code': 500, 'message': 'Internal Server Error', 'data': str(e)}}

    @http.route('/cotizacion/submit', type='http', auth="public", website=True, csrf=True)
    def copier_company_submit(self, **kwargs):
        _logger.info('Processing form submission')
        try:
            cliente_id = int(kwargs.get('cliente_id'))
            cliente = request.env['res.partner'].sudo().browse(cliente_id)
            if cliente.exists():
                cliente.write({
                    'phone': kwargs.get('telefono'),
                    'email': kwargs.get('correo'),
                    'name': kwargs.get('cliente_name')
                })
                # Crear registro en copier.company
                request.env['copier.company'].sudo().create({
                    'name': int(kwargs.get('name')),                    
                    'cliente_id': cliente_id,
                    'tipo': kwargs.get('tipo'),                    
                    'detalles': kwargs.get('detalles'),
                    'formato': kwargs.get('formato'),
                    'volumen_mensual_color': kwargs.get('volumen_mensual_color'),
                    'volumen_mensual_bn': kwargs.get('volumen_mensual_bn')
                })
            return request.render('copier_company.confirmacion_template')
        except Exception as e:
            _logger.error('Error processing form submission: %s', str(e))
            return request.render('web.http_error', {'status_code': 'Error', 'status_message': str(e)})

