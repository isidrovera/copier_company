import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class CopierCompany(http.Controller):

    @http.route('/cotizacion/form', type='http', auth="public", website=True)
    def copier_company_form(self, **kwargs):
        try:
            marcas = request.env['marcas.maquinas'].sudo().search([])
            modelos = request.env['modelos.maquinas'].sudo().search([])
            tipos_identificacion = request.env['l10n_latam.identification.type'].sudo().search([])
            
            _logger.info(
                'Form loaded with %s marcas, %s modelos and %s tipos_identificacion',
                len(marcas), len(modelos), len(tipos_identificacion)
            )
            
            return request.render('copier_company.copier_company_form_template', {
                'marcas': marcas,
                'modelos': modelos,
                'tipos_identificacion': tipos_identificacion
            })
        except Exception as e:
            _logger.error('Failed to load form: %s', str(e))
            return request.render('web.http_error', {
                'status_code': 'Error',
                'status_message': str(e)
            })

    @http.route('/copier_company/buscar_cliente', type='jsonrpc', auth="public")  # ← CAMBIADO DE type='json'
    def buscar_cliente(self, tipo_identificacion, identificacion):
        """
        Busca cliente en BD y en APIs externas (SUNAT/RENIEC)
        Retorna los datos encontrados o indica que se debe ingresar manual
        """
        try:
            _logger.info(f'Buscando cliente: {tipo_identificacion} - {identificacion}')
            
            # 1. Buscar primero en la base de datos
            partner = request.env['res.partner'].sudo().search([
                ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', tipo_identificacion),
                ('vat', '=', identificacion)
            ], limit=1)

            if partner:
                _logger.info(f'Cliente encontrado en BD: {partner.name}')
                return {
                    'success': True,
                    'found': True,
                    'source': 'database',
                    'data': {
                        'id': partner.id,
                        'name': partner.name,
                        'phone': partner.phone or '',
                        'mobile': partner.mobile or '',
                        'email': partner.email or ''
                    }
                }

            # 2. Si no existe en BD, intentar buscar en API externa
            _logger.info('Cliente no encontrado en BD, buscando en API externa...')
            
            # Crear registro temporal para usar el método _doc_number_change
            temp_partner = request.env['res.partner'].sudo().create({
                'vat': identificacion,
                'l10n_latam_identification_type_id': request.env[
                    'l10n_latam.identification.type'
                ].sudo().search([('l10n_pe_vat_code', '=', tipo_identificacion)], limit=1).id,
                'name': 'Temporal',
            })

            # Ejecutar búsqueda en API (SUNAT/RENIEC)
            temp_partner._doc_number_change()

            # Verificar si se obtuvo información
            if temp_partner.name and temp_partner.name != 'Temporal' and temp_partner.name != identificacion:
                _logger.info(f'Cliente encontrado en API externa: {temp_partner.name}')
                result = {
                    'success': True,
                    'found': True,
                    'source': 'api',
                    'data': {
                        'id': temp_partner.id,
                        'name': temp_partner.name,
                        'phone': temp_partner.phone or '',
                        'mobile': temp_partner.mobile or '',
                        'email': temp_partner.email or ''
                    }
                }
            else:
                # No se encontró en API, eliminar registro temporal
                _logger.info('No se encontró información en API externa')
                temp_partner.unlink()
                result = {
                    'success': True,
                    'found': False,
                    'source': 'none',
                    'message': 'No se encontraron datos. Por favor ingrese manualmente.'
                }

            return result

        except Exception as e:
            _logger.error(f'Error buscando cliente: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al buscar cliente. Por favor ingrese los datos manualmente.'
            }

    @http.route('/cotizacion/submit', type='http', auth="public", website=True, csrf=True, methods=['POST'])
    def copier_company_submit(self, **kwargs):
        _logger.info('Processing form submission')
        _logger.info(f'Datos recibidos: {kwargs}')
        
        try:
            # Obtener o crear el cliente
            cliente_id = kwargs.get('cliente_id')
            
            if cliente_id and cliente_id.isdigit():
                # Cliente existente
                cliente_id = int(cliente_id)
                cliente = request.env['res.partner'].sudo().browse(cliente_id)
                
                if cliente.exists():
                    # Actualizar datos del cliente
                    cliente.write({
                        'phone': kwargs.get('telefono'),
                        'mobile': kwargs.get('telefono'),
                        'email': kwargs.get('correo'),
                        'name': kwargs.get('cliente_name')
                    })
                else:
                    raise Exception('Cliente no encontrado')
            else:
                # Crear nuevo cliente
                tipo_id_obj = request.env['l10n_latam.identification.type'].sudo().search([
                    ('l10n_pe_vat_code', '=', kwargs.get('tipo_identificacion'))
                ], limit=1)
                
                cliente = request.env['res.partner'].sudo().create({
                    'name': kwargs.get('cliente_name'),
                    'vat': kwargs.get('identificacion'),
                    'l10n_latam_identification_type_id': tipo_id_obj.id if tipo_id_obj else False,
                    'phone': kwargs.get('telefono'),
                    'mobile': kwargs.get('telefono'),
                    'email': kwargs.get('correo'),
                })
                cliente_id = cliente.id

            # Crear registro en copier.company
            modelo_id = kwargs.get('modelo_id')
            if not modelo_id:
                raise Exception('Debe seleccionar un modelo de máquina')

            cotizacion = request.env['copier.company'].sudo().create({
                'name': int(modelo_id),  # ID del modelo de máquina
                'cliente_id': cliente_id,
                'contacto': kwargs.get('contacto'),
                'celular': kwargs.get('telefono'),
                'correo': kwargs.get('correo'),
                'tipo': kwargs.get('tipo'),
                'detalles': kwargs.get('detalles'),
                'formato': kwargs.get('formato'),
                'volumen_mensual_color': int(kwargs.get('volumen_mensual_color', 0)),
                'volumen_mensual_bn': int(kwargs.get('volumen_mensual_bn', 0))
            })

            _logger.info(f'Cotización creada exitosamente: {cotizacion.secuencia}')

            return request.render('copier_company.confirmacion_template', {
                'cotizacion': cotizacion
            })

        except Exception as e:
            _logger.error(f'Error processing form submission: {str(e)}')
            return request.render('web.http_error', {
                'status_code': 'Error',
                'status_message': f'Error al procesar la cotización: {str(e)}'
            })