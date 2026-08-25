from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class PowerAppsQuotationAPI(http.Controller):

    # ============================================================
    # HELPERS
    # ============================================================

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, ensure_ascii=False, default=str),
            headers=[
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, X-User-Email'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ],
            status=status,
        )

    def _check_api_key(self):
        """
        Valida la API Key configurada en:
        Ajustes > Parámetros del sistema

        Clave:
        copier.powerapps.api_key
        """

        configured_key = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('copier.powerapps.api_key')
        )

        received_key = request.httprequest.headers.get('X-API-Key')

        if not configured_key:
            _logger.error(
                "No existe el parámetro copier.powerapps.api_key"
            )
            return False, 'API Key no configurada en Odoo'

        if not received_key:
            return False, 'Falta encabezado X-API-Key'

        if received_key != configured_key:
            return False, 'API Key inválida'

        return True, None

    def _get_external_user_email(self):
        return (
            request.httprequest.headers.get('X-User-Email')
            or ''
        ).strip().lower()

    # ============================================================
    # CORS
    # ============================================================

    @http.route(
        '/api/powerapps/<path:any_path>',
        type='http',
        auth='none',
        methods=['OPTIONS'],
        csrf=False,
    )
    def powerapps_options(self, any_path=None, **kwargs):
        return request.make_response(
            '',
            headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, X-User-Email'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ],
            status=200,
        )

    # ============================================================
    # TEST DE CONEXIÓN
    # ============================================================

    @http.route(
        '/api/powerapps/ping',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False,
    )
    def ping(self, **kwargs):

        valid, error = self._check_api_key()

        if not valid:
            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        email = self._get_external_user_email()

        return self._json_response({
            'ok': True,
            'message': 'Conexión correcta con Odoo',
            'user_email': email,
        })

    # ============================================================
    # CLIENTES
    # ============================================================

    @http.route(
        '/api/powerapps/customers',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False,
    )
    def customers(self, **kwargs):

        valid, error = self._check_api_key()

        if not valid:
            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        search_text = (
            request.httprequest.args.get('search')
            or ''
        ).strip()

        domain = [
            ('active', '=', True),
        ]

        if search_text:
            domain += [
                '|',
                '|',
                ('name', 'ilike', search_text),
                ('vat', 'ilike', search_text),
                ('email', 'ilike', search_text),
            ]

        partners = (
            request.env['res.partner']
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=100,
            )
        )

        results = []

        for partner in partners:
            results.append({
                'id': partner.id,
                'name': partner.name or '',
                'vat': partner.vat or '',
                'email': partner.email or '',
                'phone': partner.phone or partner.mobile or '',
                'street': partner.street or '',
                'city': partner.city or '',
            })

        return self._json_response({
            'ok': True,
            'count': len(results),
            'customers': results,
        })

    # ============================================================
    # MODELOS / EQUIPOS
    # ============================================================

    @http.route(
        '/api/powerapps/equipment',
        type='http',
        auth='none',
        methods=['GET'],
        csrf=False,
    )
    def equipment(self, **kwargs):

        valid, error = self._check_api_key()

        if not valid:
            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        search_text = (
            request.httprequest.args.get('search')
            or ''
        ).strip()

        domain = []

        if search_text:
            domain += [
                ('name', 'ilike', search_text),
            ]

        models = (
            request.env['modelos.maquinas']
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=100,
            )
        )

        results = []

        for machine in models:

            marca = ''

            if machine.marca_id:
                marca = machine.marca_id.name or ''

            results.append({
                'id': machine.id,
                'name': machine.name or '',
                'brand': marca,
            })

        return self._json_response({
            'ok': True,
            'count': len(results),
            'equipment': results,
        })

    # ============================================================
    # CREAR COTIZACIÓN
    # ============================================================

    @http.route(
        '/api/powerapps/quotations',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def create_quotation(self, **kwargs):

        valid, error = self._check_api_key()

        if not valid:
            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        try:

            raw_data = request.httprequest.data

            if not raw_data:
                return self._json_response(
                    {
                        'ok': False,
                        'error': 'No se recibió información',
                    },
                    status=400,
                )

            data = json.loads(
                raw_data.decode('utf-8')
            )

        except Exception as e:
            _logger.exception(
                "Error leyendo JSON de Power Apps"
            )

            return self._json_response(
                {
                    'ok': False,
                    'error': 'JSON inválido',
                    'detail': str(e),
                },
                status=400,
            )

        # --------------------------------------------------------
        # DATOS OBLIGATORIOS
        # --------------------------------------------------------

        cliente_id = data.get('cliente_id')
        modalidad_pago_id = data.get('modalidad_pago_id')
        equipos = data.get('equipos') or []

        if not cliente_id:
            return self._json_response(
                {
                    'ok': False,
                    'error': 'cliente_id es obligatorio',
                },
                status=400,
            )

        if not modalidad_pago_id:
            return self._json_response(
                {
                    'ok': False,
                    'error': 'modalidad_pago_id es obligatorio',
                },
                status=400,
            )

        if not equipos:
            return self._json_response(
                {
                    'ok': False,
                    'error': 'Debe incluir al menos un equipo',
                },
                status=400,
            )

        # --------------------------------------------------------
        # VALIDAR CLIENTE
        # --------------------------------------------------------

        partner = (
            request.env['res.partner']
            .sudo()
            .browse(int(cliente_id))
        )

        if not partner.exists():
            return self._json_response(
                {
                    'ok': False,
                    'error': 'Cliente no encontrado',
                },
                status=404,
            )

        # --------------------------------------------------------
        # VALIDAR MODALIDAD
        # --------------------------------------------------------

        payment_mode = (
            request.env['copier.payment.mode']
            .sudo()
            .browse(int(modalidad_pago_id))
        )

        if not payment_mode.exists():
            return self._json_response(
                {
                    'ok': False,
                    'error': 'Modalidad de pago no encontrada',
                },
                status=404,
            )

        # --------------------------------------------------------
        # MONEDA
        # --------------------------------------------------------

        currency_code = (
            data.get('currency')
            or 'PEN'
        ).upper()

        currency = (
            request.env['res.currency']
            .sudo()
            .search(
                [('name', '=', currency_code)],
                limit=1,
            )
        )

        if not currency:
            return self._json_response(
                {
                    'ok': False,
                    'error': f'Moneda {currency_code} no encontrada',
                },
                status=404,
            )

        # --------------------------------------------------------
        # LÍNEAS
        # --------------------------------------------------------

        lines = []

        for index, item in enumerate(equipos, start=1):

            equipo_id = item.get('equipo_id')

            if not equipo_id:
                return self._json_response(
                    {
                        'ok': False,
                        'error': f'Equipo #{index}: falta equipo_id',
                    },
                    status=400,
                )

            equipment = (
                request.env['modelos.maquinas']
                .sudo()
                .browse(int(equipo_id))
            )

            if not equipment.exists():
                return self._json_response(
                    {
                        'ok': False,
                        'error': f'Equipo #{index} no encontrado',
                    },
                    status=404,
                )

            cantidad = int(
                item.get('cantidad')
                or 1
            )

            if cantidad <= 0:
                return self._json_response(
                    {
                        'ok': False,
                        'error': f'Equipo #{index}: cantidad inválida',
                    },
                    status=400,
                )

            tipo_equipo = (
                item.get('tipo_equipo')
                or 'monocroma'
            )

            if tipo_equipo not in [
                'monocroma',
                'color',
            ]:
                return self._json_response(
                    {
                        'ok': False,
                        'error': f'Equipo #{index}: tipo_equipo inválido',
                    },
                    status=400,
                )

            lines.append(
                (
                    0,
                    0,
                    {
                        'sequence': index * 10,
                        'equipo_id': equipment.id,
                        'cantidad': cantidad,
                        'tipo_equipo': tipo_equipo,
                        'formato': item.get('formato') or 'a4',

                        'volumen_mensual_bn': int(
                            item.get('volumen_mensual_bn')
                            or 0
                        ),

                        'volumen_mensual_color': int(
                            item.get('volumen_mensual_color')
                            or 0
                        ),

                        'precio_bn': float(
                            item.get('precio_bn')
                            or 0
                        ),

                        'precio_color': float(
                            item.get('precio_color')
                            or 0
                        ),

                        'observaciones': (
                            item.get('observaciones')
                            or ''
                        ),
                    },
                )
            )

        # --------------------------------------------------------
        # CREACIÓN
        # --------------------------------------------------------

        external_email = self._get_external_user_email()

        vals = {
            'cliente_id': partner.id,
            'modalidad_pago_id': payment_mode.id,
            'currency_id': currency.id,

            'contacto': data.get('contacto') or '',
            'telefono': data.get('telefono') or '',
            'email': data.get('email') or '',

            'direccion': data.get('direccion') or '',
            'sede': data.get('sede') or '',

            'validez_dias': int(
                data.get('validez_dias')
                or 30
            ),

            'descuento_general': float(
                data.get('descuento_general')
                or 0
            ),

            'igv': float(
                data.get('igv')
                or 18
            ),

            'observaciones': data.get('observaciones') or '',

            'linea_equipos_ids': lines,
        }

        try:

            quotation = (
                request.env['copier.quotation']
                .sudo()
                .create(vals)
            )

            _logger.info(
                "Cotización Power Apps creada | "
                "id=%s | numero=%s | email=%s",
                quotation.id,
                quotation.name,
                external_email,
            )

        except Exception as e:

            _logger.exception(
                "Error creando cotización desde Power Apps"
            )

            return self._json_response(
                {
                    'ok': False,
                    'error': 'No se pudo crear la cotización',
                    'detail': str(e),
                },
                status=500,
            )

        return self._json_response(
            {
                'ok': True,

                'quotation': {
                    'id': quotation.id,
                    'name': quotation.name,

                    'cliente': (
                        quotation.cliente_id.name
                        or ''
                    ),

                    'currency': (
                        quotation.currency_id.name
                        or ''
                    ),

                    'subtotal_mensual': quotation.subtotal_mensual,
                    'igv_mensual': quotation.igv_mensual,
                    'total_mensual': quotation.total_mensual,

                    'subtotal_final': quotation.subtotal_final,
                    'igv_final': quotation.igv_final,
                    'total': quotation.total_por_modalidad,

                    'fecha_cotizacion': quotation.fecha_cotizacion,
                    'fecha_vencimiento': quotation.fecha_vencimiento,

                    'estado': quotation.estado,

                    'asesora_email': external_email,
                },
            },
            status=201,
        )