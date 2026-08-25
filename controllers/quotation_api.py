from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class PowerAppsAPI(http.Controller):

    # ============================================================
    # RESPUESTA JSON
    # ============================================================

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, ensure_ascii=False, default=str),
            headers=[
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, X-User-Email'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
            ],
            status=status,
        )

    # ============================================================
    # SEGURIDAD
    # ============================================================

    def _check_api_key(self):
        configured_key = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('copier.powerapps.api_key')
        )

        received_key = request.httprequest.headers.get('X-API-Key')

        if not configured_key:
            return False, 'API Key no configurada en Odoo'

        if not received_key:
            return False, 'Falta encabezado X-API-Key'

        if received_key != configured_key:
            return False, 'API Key inválida'

        return True, None

    def _get_external_email(self):
        return (
            request.httprequest.headers.get('X-User-Email')
            or ''
        ).strip().lower()

    # ============================================================
    # CORS
    # ============================================================

    @http.route(
        '/api/powerapps',
        type='http',
        auth='none',
        methods=['OPTIONS'],
        csrf=False,
    )
    def powerapps_options(self, **kwargs):
        return request.make_response(
            '',
            headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, X-User-Email'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
            ],
            status=200,
        )

    # ============================================================
    # ENDPOINT CENTRAL
    # ============================================================

    @http.route(
        '/api/powerapps',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def powerapps_execute(self, **kwargs):

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
            raw_data = request.httprequest.data or b'{}'
            payload = json.loads(raw_data.decode('utf-8'))

        except Exception as e:
            return self._json_response(
                {
                    'ok': False,
                    'error': 'JSON inválido',
                    'detail': str(e),
                },
                status=400,
            )

        action = (payload.get('action') or '').strip()
        data = payload.get('data') or {}

        if not action:
            return self._json_response(
                {
                    'ok': False,
                    'error': 'Falta action',
                },
                status=400,
            )

        email = self._get_external_email()

        try:

            # ----------------------------------------------------
            # ROUTER
            # ----------------------------------------------------

            actions = {
                'ping': self._action_ping,
                'customers': self._action_customers,
                'equipment': self._action_equipment,
                'payment_modes': self._action_payment_modes,
                'currencies': self._action_currencies,
                'create_quotation': self._action_create_quotation,
                'quotations': self._action_quotations,
                'quotation_detail': self._action_quotation_detail,
            }

            handler = actions.get(action)

            if not handler:
                return self._json_response(
                    {
                        'ok': False,
                        'error': f'Acción no válida: {action}',
                    },
                    status=400,
                )

            result = handler(
                data=data,
                email=email,
            )

            return self._json_response(result)

        except Exception as e:

            _logger.exception(
                "Power Apps API error | action=%s | email=%s",
                action,
                email,
            )

            return self._json_response(
                {
                    'ok': False,
                    'error': 'Error interno en Odoo',
                    'detail': str(e),
                },
                status=500,
            )

    # ============================================================
    # PING
    # ============================================================

    def _action_ping(self, data, email):

        return {
            'ok': True,
            'action': 'ping',
            'message': 'Conexión correcta con Odoo',
            'user_email': email,
        }

    # ============================================================
    # CLIENTES
    # ============================================================

    def _action_customers(self, data, email):

        search_text = (
            data.get('search')
            or ''
        ).strip()

        limit = int(
            data.get('limit')
            or 100
        )

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
                limit=limit,
            )
        )

        customers = []

        for partner in partners:
            customers.append({
                'id': partner.id,
                'name': partner.name or '',
                'vat': partner.vat or '',
                'email': partner.email or '',
                'phone': partner.phone or partner.mobile or '',
                'street': partner.street or '',
                'city': partner.city or '',
            })

        return {
            'ok': True,
            'action': 'customers',
            'count': len(customers),
            'customers': customers,
        }

    # ============================================================
    # EQUIPOS / MODELOS
    # ============================================================

    def _action_equipment(self, data, email):

        search_text = (
            data.get('search')
            or ''
        ).strip()

        limit = int(
            data.get('limit')
            or 100
        )

        domain = []

        if search_text:
            domain.append(
                ('name', 'ilike', search_text)
            )

        machines = (
            request.env['modelos.maquinas']
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=limit,
            )
        )

        equipment = []

        for machine in machines:

            equipment.append({
                'id': machine.id,
                'name': machine.name or '',
                'brand': (
                    machine.marca_id.name
                    if machine.marca_id
                    else ''
                ),
            })

        return {
            'ok': True,
            'action': 'equipment',
            'count': len(equipment),
            'equipment': equipment,
        }

    # ============================================================
    # MODALIDADES DE PAGO
    # ============================================================

    def _action_payment_modes(self, data, email):

        records = (
            request.env['copier.payment.mode']
            .sudo()
            .search(
                [('activo', '=', True)],
                order='frecuencia_meses asc',
            )
        )

        values = []

        for rec in records:
            values.append({
                'id': rec.id,
                'name': rec.name or '',
                'frecuencia_meses': rec.frecuencia_meses,
                'descuento_porcentaje': rec.descuento_porcentaje,
                'descripcion': rec.descripcion or '',
            })

        return {
            'ok': True,
            'action': 'payment_modes',
            'payment_modes': values,
        }

    # ============================================================
    # MONEDAS
    # ============================================================

    def _action_currencies(self, data, email):

        records = (
            request.env['res.currency']
            .sudo()
            .search(
                [
                    ('active', '=', True),
                    ('name', 'in', ['PEN', 'USD']),
                ],
                order='name asc',
            )
        )

        values = []

        for rec in records:
            values.append({
                'id': rec.id,
                'name': rec.name,
                'symbol': rec.symbol or '',
            })

        return {
            'ok': True,
            'action': 'currencies',
            'currencies': values,
        }

    # ============================================================
    # CREAR COTIZACIÓN
    # ============================================================

    def _action_create_quotation(self, data, email):

        cliente_id = data.get('cliente_id')
        modalidad_pago_id = data.get('modalidad_pago_id')

        equipos = data.get('equipos') or []

        if not cliente_id:
            raise ValueError('cliente_id es obligatorio')

        if not modalidad_pago_id:
            raise ValueError(
                'modalidad_pago_id es obligatorio'
            )

        if not equipos:
            raise ValueError(
                'Debe incluir al menos un equipo'
            )

        partner = (
            request.env['res.partner']
            .sudo()
            .browse(int(cliente_id))
        )

        if not partner.exists():
            raise ValueError(
                'Cliente no encontrado'
            )

        payment_mode = (
            request.env['copier.payment.mode']
            .sudo()
            .browse(int(modalidad_pago_id))
        )

        if not payment_mode.exists():
            raise ValueError(
                'Modalidad de pago no encontrada'
            )

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
            raise ValueError(
                f'Moneda {currency_code} no encontrada'
            )

        lines = []

        for index, item in enumerate(
            equipos,
            start=1,
        ):

            equipo_id = item.get('equipo_id')

            if not equipo_id:
                raise ValueError(
                    f'Equipo #{index}: falta equipo_id'
                )

            machine = (
                request.env['modelos.maquinas']
                .sudo()
                .browse(int(equipo_id))
            )

            if not machine.exists():
                raise ValueError(
                    f'Equipo #{index}: no encontrado'
                )

            lines.append(
                (
                    0,
                    0,
                    {
                        'sequence': index * 10,

                        'equipo_id': machine.id,

                        'cantidad': int(
                            item.get('cantidad')
                            or 1
                        ),

                        'tipo_equipo': (
                            item.get('tipo_equipo')
                            or 'monocroma'
                        ),

                        'formato': (
                            item.get('formato')
                            or 'a4'
                        ),

                        'volumen_mensual_bn': int(
                            item.get(
                                'volumen_mensual_bn'
                            )
                            or 0
                        ),

                        'volumen_mensual_color': int(
                            item.get(
                                'volumen_mensual_color'
                            )
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

        vals = {
            'cliente_id': partner.id,

            'modalidad_pago_id': (
                payment_mode.id
            ),

            'currency_id': currency.id,

            'contacto': (
                data.get('contacto')
                or ''
            ),

            'telefono': (
                data.get('telefono')
                or ''
            ),

            'email': (
                data.get('email')
                or ''
            ),

            'direccion': (
                data.get('direccion')
                or ''
            ),

            'sede': (
                data.get('sede')
                or ''
            ),

            'validez_dias': int(
                data.get('validez_dias')
                or 30
            ),

            'descuento_general': float(
                data.get(
                    'descuento_general'
                )
                or 0
            ),

            'igv': float(
                data.get('igv')
                or 18
            ),

            'observaciones': (
                data.get('observaciones')
                or ''
            ),

            'linea_equipos_ids': lines,
        }

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .create(vals)
        )

        _logger.info(
            "Cotización creada desde Power Apps | "
            "numero=%s | asesora=%s",
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': 'create_quotation',

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

                'subtotal_mensual': (
                    quotation.subtotal_mensual
                ),

                'igv_mensual': (
                    quotation.igv_mensual
                ),

                'total_mensual': (
                    quotation.total_mensual
                ),

                'total': (
                    quotation.total_por_modalidad
                ),

                'fecha_cotizacion': (
                    quotation.fecha_cotizacion
                ),

                'fecha_vencimiento': (
                    quotation.fecha_vencimiento
                ),

                'estado': quotation.estado,

                'asesora_email': email,
            },
        }

    # ============================================================
    # LISTAR COTIZACIONES
    # ============================================================

    def _action_quotations(self, data, email):

        limit = int(
            data.get('limit')
            or 100
        )

        quotations = (
            request.env['copier.quotation']
            .sudo()
            .search(
                [],
                order='id desc',
                limit=limit,
            )
        )

        values = []

        for q in quotations:

            values.append({
                'id': q.id,
                'name': q.name,

                'cliente': (
                    q.cliente_id.name
                    or ''
                ),

                'fecha': (
                    q.fecha_cotizacion
                ),

                'vencimiento': (
                    q.fecha_vencimiento
                ),

                'currency': (
                    q.currency_id.name
                    or ''
                ),

                'total': (
                    q.total_por_modalidad
                ),

                'estado': q.estado,
            })

        return {
            'ok': True,
            'action': 'quotations',
            'quotations': values,
        }

    # ============================================================
    # DETALLE COTIZACIÓN
    # ============================================================

    def _action_quotation_detail(
        self,
        data,
        email,
    ):

        quotation_id = data.get(
            'quotation_id'
        )

        if not quotation_id:
            raise ValueError(
                'quotation_id es obligatorio'
            )

        q = (
            request.env['copier.quotation']
            .sudo()
            .browse(int(quotation_id))
        )

        if not q.exists():
            raise ValueError(
                'Cotización no encontrada'
            )

        lines = []

        for line in q.linea_equipos_ids:

            lines.append({
                'id': line.id,

                'equipo_id': (
                    line.equipo_id.id
                ),

                'equipo': (
                    line.equipo_id.name
                    or ''
                ),

                'cantidad': line.cantidad,

                'tipo_equipo': (
                    line.tipo_equipo
                ),

                'volumen_mensual_bn': (
                    line.volumen_mensual_bn
                ),

                'volumen_mensual_color': (
                    line.volumen_mensual_color
                ),

                'precio_bn': (
                    line.precio_bn
                ),

                'precio_color': (
                    line.precio_color
                ),

                'subtotal': (
                    line.subtotal_linea
                ),
            })

        return {
            'ok': True,
            'action': 'quotation_detail',

            'quotation': {
                'id': q.id,
                'name': q.name,

                'cliente_id': (
                    q.cliente_id.id
                ),

                'cliente': (
                    q.cliente_id.name
                    or ''
                ),

                'contacto': (
                    q.contacto
                    or ''
                ),

                'telefono': (
                    q.telefono
                    or ''
                ),

                'email': (
                    q.email
                    or ''
                ),

                'direccion': (
                    q.direccion
                    or ''
                ),

                'sede': (
                    q.sede
                    or ''
                ),

                'currency': (
                    q.currency_id.name
                    or ''
                ),

                'estado': q.estado,

                'subtotal_mensual': (
                    q.subtotal_mensual
                ),

                'igv_mensual': (
                    q.igv_mensual
                ),

                'total_mensual': (
                    q.total_mensual
                ),

                'total': (
                    q.total_por_modalidad
                ),

                'equipos': lines,
            },
        }