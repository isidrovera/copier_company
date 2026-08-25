from odoo import http, fields
from odoo.http import request

import json
import logging
import secrets
import traceback


_logger = logging.getLogger(__name__)


class PowerAppsAPI(http.Controller):
    """
    ============================================================
    API CENTRAL POWER APPS <-> ODOO
    ============================================================

    Endpoint único:

        POST /api/powerapps

    Headers:

        X-API-Key: <clave>
        X-User-Email: usuario@dominio.com
        Content-Type: application/json

    Body:

        {
            "action": "customers",
            "data": {}
        }

    IMPORTANTE:

    Microsoft Power Apps puede enviar `data` como objeto:

        "data": {}

    o como string JSON:

        "data": "{}"

    Esta API acepta ambos formatos.

    ============================================================
    ACCIONES DISPONIBLES
    ============================================================

    SISTEMA
    -------
    ping

    CLIENTES
    --------
    customers
    customer_detail

    EQUIPOS / MODELOS
    -----------------
    equipment
    equipment_detail

    CONFIGURACIÓN
    -------------
    payment_modes
    currencies
    durations

    COTIZACIONES
    ------------
    quotations
    quotation_detail
    create_quotation
    update_quotation
    delete_quotation
    send_quotation
    approve_quotation
    reject_quotation
    convert_quotation

    ============================================================
    """

    API_CONFIG_KEY = 'copier.powerapps.api_key'

    ALLOWED_EMAILS_CONFIG_KEY = (
        'copier.powerapps.allowed_emails'
    )

    DEFAULT_LIMIT = 100
    MAX_LIMIT = 500

    # ============================================================
    # JSON RESPONSE
    # ============================================================

    def _json_response(
        self,
        data,
        status=200,
    ):
        """
        Todas las respuestas de la API pasan por aquí.
        """

        try:
            body = json.dumps(
                data,
                ensure_ascii=False,
                default=str,
            )

        except Exception as exc:

            _logger.exception(
                '[POWERAPPS API] '
                'ERROR SERIALIZANDO JSON | error=%s',
                exc,
            )

            body = json.dumps(
                {
                    'ok': False,
                    'error': (
                        'No se pudo serializar '
                        'la respuesta'
                    ),
                }
            )

            status = 500

        return request.make_response(
            body,
            headers=[
                (
                    'Content-Type',
                    'application/json; charset=utf-8',
                ),
                (
                    'Access-Control-Allow-Origin',
                    '*',
                ),
                (
                    'Access-Control-Allow-Headers',
                    (
                        'Content-Type, '
                        'X-API-Key, '
                        'X-User-Email'
                    ),
                ),
                (
                    'Access-Control-Allow-Methods',
                    'POST, OPTIONS',
                ),
                (
                    'Cache-Control',
                    'no-store',
                ),
            ],
            status=status,
        )

    # ============================================================
    # HELPERS BÁSICOS
    # ============================================================

    def _safe_str(
        self,
        value,
        default='',
    ):
        if value is None:
            return default

        try:
            return str(value).strip()
        except Exception:
            return default

    def _safe_int(
        self,
        value,
        default=0,
        minimum=None,
        maximum=None,
    ):
        try:
            result = int(value)

        except (TypeError, ValueError):
            result = default

        if minimum is not None:
            result = max(
                result,
                minimum,
            )

        if maximum is not None:
            result = min(
                result,
                maximum,
            )

        return result

    def _safe_float(
        self,
        value,
        default=0.0,
        minimum=None,
        maximum=None,
    ):
        try:
            result = float(value)

        except (TypeError, ValueError):
            result = default

        if minimum is not None:
            result = max(
                result,
                minimum,
            )

        if maximum is not None:
            result = min(
                result,
                maximum,
            )

        return result

    def _safe_bool(
        self,
        value,
        default=False,
    ):
        if isinstance(value, bool):
            return value

        if value is None:
            return default

        if isinstance(
            value,
            (int, float),
        ):
            return bool(value)

        text = str(
            value
        ).strip().lower()

        if text in {
            'true',
            '1',
            'yes',
            'si',
            'sí',
        }:
            return True

        if text in {
            'false',
            '0',
            'no',
        }:
            return False

        return default

    # ============================================================
    # HELPER SEGURO PARA CAMPOS ODOO
    # ============================================================

    def _field_exists(
        self,
        record,
        field_name,
    ):
        """
        Comprueba si un campo existe realmente en el modelo.
        """

        try:
            return (
                field_name
                in record._fields
            )

        except Exception:
            return False

    def _field_value(
        self,
        record,
        field_name,
        default=False,
    ):
        """
        Obtiene un campo únicamente si existe.

        Evita errores como:

            'res.partner' object
            has no attribute 'mobile'
        """

        if not record:
            return default

        if not self._field_exists(
            record,
            field_name,
        ):
            return default

        try:
            value = record[
                field_name
            ]

            if value is None:
                return default

            return value

        except Exception:
            return default

    def _char_field(
        self,
        record,
        field_name,
        default='',
    ):
        value = self._field_value(
            record,
            field_name,
            default,
        )

        if not value:
            return default

        return str(value)

    def _m2o_name(
        self,
        record,
        field_name,
    ):
        value = self._field_value(
            record,
            field_name,
            False,
        )

        if not value:
            return ''

        return (
            value.display_name
            or value.name
            or ''
        )

    def _m2o_id(
        self,
        record,
        field_name,
    ):
        value = self._field_value(
            record,
            field_name,
            False,
        )

        if not value:
            return False

        return value.id

    # ============================================================
    # LIMIT
    # ============================================================

    def _get_limit(
        self,
        data,
    ):
        return self._safe_int(
            data.get('limit'),
            default=self.DEFAULT_LIMIT,
            minimum=1,
            maximum=self.MAX_LIMIT,
        )

    # ============================================================
    # EMAIL EXTERNO
    # ============================================================

    def _get_external_email(self):
        return (
            request
            .httprequest
            .headers
            .get(
                'X-User-Email',
                '',
            )
            .strip()
            .lower()
        )

    # ============================================================
    # API KEY
    # ============================================================

    def _check_api_key(self):
        configured_key = (
            request.env[
                'ir.config_parameter'
            ]
            .sudo()
            .get_param(
                self.API_CONFIG_KEY
            )
        )

        received_key = (
            request
            .httprequest
            .headers
            .get(
                'X-API-Key',
                '',
            )
        )

        if not configured_key:

            _logger.error(
                '[POWERAPPS API] '
                'API KEY NO CONFIGURADA | '
                'parametro=%s',
                self.API_CONFIG_KEY,
            )

            return (
                False,
                'API Key no configurada en Odoo',
            )

        if not received_key:

            _logger.warning(
                '[POWERAPPS API] '
                'REQUEST SIN X-API-KEY'
            )

            return (
                False,
                'Falta encabezado X-API-Key',
            )

        try:
            valid = secrets.compare_digest(
                str(received_key),
                str(configured_key),
            )

        except Exception:

            valid = (
                received_key
                == configured_key
            )

        if not valid:

            _logger.warning(
                '[POWERAPPS API] '
                'API KEY INCORRECTA | '
                'ip=%s',
                request
                .httprequest
                .remote_addr,
            )

            return (
                False,
                'API Key inválida',
            )

        return True, None

    # ============================================================
    # USUARIOS AUTORIZADOS
    # ============================================================

    def _check_external_email(
        self,
        email,
    ):
        """
        Parámetro opcional:

        copier.powerapps.allowed_emails

        Ejemplo:

        info@copiercompanysac.com,
        ventas1@copiercompanysac.com,
        ventas2@copiercompanysac.com

        Si está vacío:
            la API Key es suficiente.

        Si está configurado:
            además se valida el correo.
        """

        configured = (
            request.env[
                'ir.config_parameter'
            ]
            .sudo()
            .get_param(
                self.ALLOWED_EMAILS_CONFIG_KEY
            )
            or ''
        ).strip()

        if not configured:
            return True, None

        allowed = {
            item.strip().lower()
            for item
            in configured.split(',')
            if item.strip()
        }

        if not email:

            return (
                False,
                'Falta X-User-Email',
            )

        if email not in allowed:

            _logger.warning(
                '[POWERAPPS API] '
                'EMAIL NO AUTORIZADO | '
                'email=%s',
                email,
            )

            return (
                False,
                'Usuario no autorizado',
            )

        return True, None

    # ============================================================
    # PARSEO DEL BODY
    # ============================================================

    def _parse_payload(self):
        raw_data = (
            request
            .httprequest
            .data
            or b''
        )

        if not raw_data:
            return (
                None,
                'No se recibió información',
            )

        try:

            payload = json.loads(
                raw_data.decode(
                    'utf-8'
                )
            )

        except Exception as exc:

            _logger.warning(
                '[POWERAPPS API] '
                'JSON GENERAL INVÁLIDO | '
                'error=%s',
                exc,
            )

            return (
                None,
                'JSON inválido',
            )

        if not isinstance(
            payload,
            dict,
        ):

            return (
                None,
                (
                    'El cuerpo debe ser '
                    'un objeto JSON'
                ),
            )

        action = self._safe_str(
            payload.get('action')
        )

        if not action:

            return (
                None,
                'Falta action',
            )

        data = payload.get(
            'data',
            {},
        )

        # ========================================================
        # POWER APPS ENVÍA data COMO STRING
        # ========================================================

        if isinstance(
            data,
            str,
        ):

            data = data.strip()

            if not data:
                data = {}

            else:

                try:

                    data = json.loads(
                        data
                    )

                except Exception as exc:

                    _logger.warning(
                        '[POWERAPPS API] '
                        'DATA JSON INVÁLIDO | '
                        'action=%s | '
                        'data=%s | '
                        'error=%s',
                        action,
                        data,
                        exc,
                    )

                    return (
                        None,
                        (
                            'El campo data '
                            'contiene JSON inválido'
                        ),
                    )

        if data is None:
            data = {}

        if not isinstance(
            data,
            dict,
        ):

            return (
                None,
                (
                    'El campo data debe '
                    'ser un objeto JSON'
                ),
            )

        return (
            {
                'action': action,
                'data': data,
            },
            None,
        )

    # ============================================================
    # LOG REQUEST
    # ============================================================

    def _log_request(
        self,
        action,
        email,
        data,
    ):
        safe_data = {}

        blocked_fields = {
            'password',
            'password_confirmation',
            'api_key',
            'apikey',
            'token',
            'secret',
        }

        try:

            for key, value in data.items():

                if (
                    str(key)
                    .lower()
                    in blocked_fields
                ):

                    safe_data[
                        key
                    ] = '***'

                else:

                    safe_data[
                        key
                    ] = value

        except Exception:

            safe_data = {}

        _logger.info(
            '[POWERAPPS API] REQUEST | '
            'action=%s | '
            'email=%s | '
            'ip=%s | '
            'data=%s',
            action,
            email or '-',
            request
            .httprequest
            .remote_addr,
            safe_data,
        )

    # ============================================================
    # CORS
    # ============================================================

    @http.route(
        '/api/powerapps',
        type='http',
        auth='none',
        methods=['OPTIONS'],
        csrf=False,
        save_session=False,
    )
    def powerapps_options(
        self,
        **kwargs,
    ):

        return request.make_response(
            '',
            headers=[
                (
                    'Access-Control-Allow-Origin',
                    '*',
                ),
                (
                    'Access-Control-Allow-Headers',
                    (
                        'Content-Type, '
                        'X-API-Key, '
                        'X-User-Email'
                    ),
                ),
                (
                    'Access-Control-Allow-Methods',
                    'POST, OPTIONS',
                ),
            ],
            status=200,
        )

    # ============================================================
    # ENDPOINT ÚNICO
    # ============================================================

    @http.route(
        '/api/powerapps',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def powerapps_execute(
        self,
        **kwargs,
    ):

        # --------------------------------------------------------
        # API KEY
        # --------------------------------------------------------

        valid, error = (
            self._check_api_key()
        )

        if not valid:

            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        # --------------------------------------------------------
        # EMAIL
        # --------------------------------------------------------

        email = (
            self._get_external_email()
        )

        email_valid, email_error = (
            self._check_external_email(
                email
            )
        )

        if not email_valid:

            return self._json_response(
                {
                    'ok': False,
                    'error': email_error,
                },
                status=403,
            )

        # --------------------------------------------------------
        # BODY
        # --------------------------------------------------------

        payload, error = (
            self._parse_payload()
        )

        if error:

            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=400,
            )

        action = payload[
            'action'
        ]

        data = payload[
            'data'
        ]

        self._log_request(
            action,
            email,
            data,
        )

        # --------------------------------------------------------
        # ROUTER CENTRAL
        # --------------------------------------------------------

        actions = {

            # Sistema
            'ping':
                self._action_ping,

            # Clientes
            'customers':
                self._action_customers,

            'customer_detail':
                self._action_customer_detail,

            # Equipos
            'equipment':
                self._action_equipment,

            'equipment_detail':
                self._action_equipment_detail,

            # Configuración
            'payment_modes':
                self._action_payment_modes,

            'currencies':
                self._action_currencies,

            'durations':
                self._action_durations,

            # Cotizaciones
            'quotations':
                self._action_quotations,

            'quotation_detail':
                self._action_quotation_detail,

            'create_quotation':
                self._action_create_quotation,

            'update_quotation':
                self._action_update_quotation,

            'delete_quotation':
                self._action_delete_quotation,

            'send_quotation':
                self._action_send_quotation,

            'approve_quotation':
                self._action_approve_quotation,

            'reject_quotation':
                self._action_reject_quotation,

            'convert_quotation':
                self._action_convert_quotation,
        }

        handler = actions.get(
            action
        )

        if not handler:

            _logger.warning(
                '[POWERAPPS API] '
                'ACTION DESCONOCIDA | '
                'action=%s | '
                'email=%s',
                action,
                email,
            )

            return self._json_response(
                {
                    'ok': False,
                    'error': (
                        f'Acción no válida: '
                        f'{action}'
                    ),
                },
                status=400,
            )

        # --------------------------------------------------------
        # EJECUCIÓN
        # --------------------------------------------------------

        try:

            result = handler(
                data=data,
                email=email,
            )

            if not isinstance(
                result,
                dict,
            ):

                result = {
                    'ok': True,
                    'result': result,
                }

            if (
                'ok'
                not in result
            ):

                result[
                    'ok'
                ] = True

            _logger.info(
                '[POWERAPPS API] '
                'RESPONSE OK | '
                'action=%s | '
                'email=%s',
                action,
                email,
            )

            return self._json_response(
                result,
                status=200,
            )

        except ValueError as exc:

            _logger.warning(
                '[POWERAPPS API] '
                'VALIDATION ERROR | '
                'action=%s | '
                'email=%s | '
                'error=%s',
                action,
                email,
                exc,
            )

            return self._json_response(
                {
                    'ok': False,
                    'action': action,
                    'error': str(exc),
                },
                status=400,
            )

        except Exception as exc:

            _logger.error(
                '[POWERAPPS API] '
                'INTERNAL ERROR | '
                'action=%s | '
                'email=%s | '
                'error=%s\n%s',
                action,
                email,
                exc,
                traceback.format_exc(),
            )

            return self._json_response(
                {
                    'ok': False,
                    'action': action,
                    'error': (
                        'Error interno en Odoo'
                    ),
                    'detail': str(exc),
                },
                status=500,
            )

    # ============================================================
    # PING
    # ============================================================

    def _action_ping(
        self,
        data,
        email,
    ):

        return {
            'ok': True,
            'action': 'ping',
            'message': (
                'Conexión correcta con Odoo'
            ),
            'user_email': email,
            'server_date': fields.Date.today(),
        }

    # ============================================================
    # SERIALIZAR CLIENTE
    # ============================================================

    def _serialize_customer(
        self,
        partner,
    ):
        """
        Campos verificados para res.partner:

        name
        vat
        email
        phone
        street
        street2
        city
        zip
        state_id
        country_id

        NO usamos mobile.
        """

        return {
            'id':
                partner.id,

            'name':
                self._char_field(
                    partner,
                    'name',
                ),

            'display_name':
                partner.display_name
                or '',

            'vat':
                self._char_field(
                    partner,
                    'vat',
                ),

            'email':
                self._char_field(
                    partner,
                    'email',
                ),

            'phone':
                self._char_field(
                    partner,
                    'phone',
                ),

            'street':
                self._char_field(
                    partner,
                    'street',
                ),

            'street2':
                self._char_field(
                    partner,
                    'street2',
                ),

            'city':
                self._char_field(
                    partner,
                    'city',
                ),

            'zip':
                self._char_field(
                    partner,
                    'zip',
                ),

            'state_id':
                self._m2o_id(
                    partner,
                    'state_id',
                ),

            'state':
                self._m2o_name(
                    partner,
                    'state_id',
                ),

            'country_id':
                self._m2o_id(
                    partner,
                    'country_id',
                ),

            'country':
                self._m2o_name(
                    partner,
                    'country_id',
                ),

            'is_company':
                bool(
                    self._field_value(
                        partner,
                        'is_company',
                        False,
                    )
                ),
        }

    # ============================================================
    # CLIENTES
    # ============================================================

    def _action_customers(
        self,
        data,
        email,
    ):

        search_text = (
            self._safe_str(
                data.get(
                    'search'
                )
            )
        )

        limit = self._get_limit(
            data
        )

        only_companies = (
            self._safe_bool(
                data.get(
                    'only_companies'
                ),
                default=False,
            )
        )

        domain = [
            (
                'active',
                '=',
                True,
            ),
        ]

        if only_companies:

            domain.append(
                (
                    'is_company',
                    '=',
                    True,
                )
            )

        if search_text:

            domain += [
                '|',
                '|',
                '|',

                (
                    'name',
                    'ilike',
                    search_text,
                ),

                (
                    'vat',
                    'ilike',
                    search_text,
                ),

                (
                    'email',
                    'ilike',
                    search_text,
                ),

                (
                    'phone',
                    'ilike',
                    search_text,
                ),
            ]

        partners = (
            request.env[
                'res.partner'
            ]
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=limit,
            )
        )

        customers = [
            self._serialize_customer(
                partner
            )
            for partner
            in partners
        ]

        _logger.info(
            '[POWERAPPS API] '
            'CUSTOMERS | '
            'email=%s | '
            'search=%s | '
            'only_companies=%s | '
            'count=%s',
            email,
            search_text,
            only_companies,
            len(customers),
        )

        return {
            'ok': True,
            'action': 'customers',
            'count': len(
                customers
            ),
            'customers': customers,
        }

    # ============================================================
    # DETALLE CLIENTE
    # ============================================================

    def _action_customer_detail(
        self,
        data,
        email,
    ):

        customer_id = (
            self._safe_int(
                data.get(
                    'customer_id'
                )
                or data.get(
                    'cliente_id'
                ),
                default=0,
            )
        )

        if not customer_id:

            raise ValueError(
                'customer_id es obligatorio'
            )

        partner = (
            request.env[
                'res.partner'
            ]
            .sudo()
            .browse(
                customer_id
            )
        )

        if not partner.exists():

            raise ValueError(
                'Cliente no encontrado'
            )

        return {
            'ok': True,
            'action': (
                'customer_detail'
            ),
            'customer': (
                self._serialize_customer(
                    partner
                )
            ),
        }

    # ============================================================
    # SERIALIZAR EQUIPO
    # ============================================================

    def _serialize_equipment(
        self,
        machine,
        include_detail=False,
    ):

        result = {
            'id':
                machine.id,

            'name':
                self._char_field(
                    machine,
                    'name',
                ),

            'brand_id':
                self._m2o_id(
                    machine,
                    'marca_id',
                ),

            'brand':
                self._m2o_name(
                    machine,
                    'marca_id',
                ),

            'has_image':
                bool(
                    self._field_value(
                        machine,
                        'imagen',
                        False,
                    )
                ),
        }

        if include_detail:

            result[
                'specifications'
            ] = self._char_field(
                machine,
                'especificaciones',
            )

        return result

    # ============================================================
    # EQUIPOS
    # ============================================================

    def _action_equipment(
        self,
        data,
        email,
    ):

        search_text = (
            self._safe_str(
                data.get(
                    'search'
                )
            )
        )

        limit = self._get_limit(
            data
        )

        domain = []

        if search_text:

            domain += [
                '|',

                (
                    'name',
                    'ilike',
                    search_text,
                ),

                (
                    'marca_id.name',
                    'ilike',
                    search_text,
                ),
            ]

        records = (
            request.env[
                'modelos.maquinas'
            ]
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=limit,
            )
        )

        equipment = [
            self._serialize_equipment(
                rec
            )
            for rec
            in records
        ]

        _logger.info(
            '[POWERAPPS API] '
            'EQUIPMENT | '
            'email=%s | '
            'search=%s | '
            'count=%s',
            email,
            search_text,
            len(equipment),
        )

        return {
            'ok': True,
            'action': 'equipment',
            'count': len(
                equipment
            ),
            'equipment': equipment,
        }

    # ============================================================
    # DETALLE EQUIPO
    # ============================================================

    def _action_equipment_detail(
        self,
        data,
        email,
    ):

        equipment_id = (
            self._safe_int(
                data.get(
                    'equipment_id'
                )
                or data.get(
                    'equipo_id'
                ),
                default=0,
            )
        )

        if not equipment_id:

            raise ValueError(
                'equipment_id es obligatorio'
            )

        machine = (
            request.env[
                'modelos.maquinas'
            ]
            .sudo()
            .browse(
                equipment_id
            )
        )

        if not machine.exists():

            raise ValueError(
                'Equipo no encontrado'
            )

        return {
            'ok': True,
            'action': (
                'equipment_detail'
            ),
            'equipment': (
                self._serialize_equipment(
                    machine,
                    include_detail=True,
                )
            ),
        }

    # ============================================================
    # MODALIDADES DE PAGO
    # ============================================================

    def _action_payment_modes(
        self,
        data,
        email,
    ):

        records = (
            request.env[
                'copier.payment.mode'
            ]
            .sudo()
            .search(
                [
                    (
                        'activo',
                        '=',
                        True,
                    ),
                ],
                order=(
                    'frecuencia_meses asc'
                ),
            )
        )

        values = []

        for rec in records:

            values.append(
                {
                    'id':
                        rec.id,

                    'name':
                        rec.name
                        or '',

                    'description':
                        rec.descripcion
                        or '',

                    'months':
                        rec.frecuencia_meses,

                    'discount':
                        rec.descuento_porcentaje,
                }
            )

        return {
            'ok': True,
            'action': (
                'payment_modes'
            ),
            'count': len(values),
            'payment_modes': values,
        }

    # ============================================================
    # MONEDAS
    # ============================================================

    def _action_currencies(
        self,
        data,
        email,
    ):

        records = (
            request.env[
                'res.currency'
            ]
            .sudo()
            .search(
                [
                    (
                        'active',
                        '=',
                        True,
                    ),
                    (
                        'name',
                        'in',
                        [
                            'PEN',
                            'USD',
                        ],
                    ),
                ],
                order='name asc',
            )
        )

        values = []

        for rec in records:

            values.append(
                {
                    'id':
                        rec.id,

                    'name':
                        rec.name
                        or '',

                    'symbol':
                        rec.symbol
                        or '',

                    'position':
                        rec.position
                        or '',
                }
            )

        return {
            'ok': True,
            'action': (
                'currencies'
            ),
            'count': len(values),
            'currencies': values,
        }

    # ============================================================
    # DURACIONES
    # ============================================================

    def _action_durations(
        self,
        data,
        email,
    ):

        records = (
            request.env[
                'copier.duracion'
            ]
            .sudo()
            .search(
                [],
                order='id asc',
            )
        )

        values = [
            {
                'id':
                    rec.id,

                'name':
                    rec.name
                    or '',
            }
            for rec
            in records
        ]

        return {
            'ok': True,
            'action': 'durations',
            'count': len(values),
            'durations': values,
        }

    # ============================================================
    # SERIALIZAR COTIZACIÓN SIMPLE
    # ============================================================

    def _serialize_quotation_summary(
        self,
        quotation,
    ):

        return {
            'id':
                quotation.id,

            'name':
                quotation.name
                or '',

            'customer_id':
                (
                    quotation
                    .cliente_id
                    .id
                    if quotation.cliente_id
                    else False
                ),

            'customer':
                (
                    quotation
                    .cliente_id
                    .name
                    if quotation.cliente_id
                    else ''
                ),

            'vat':
                (
                    quotation
                    .cliente_id
                    .vat
                    or ''
                    if quotation.cliente_id
                    else ''
                ),

            'date':
                quotation.fecha_cotizacion,

            'expiration_date':
                quotation.fecha_vencimiento,

            'currency':
                (
                    quotation
                    .currency_id
                    .name
                    if quotation.currency_id
                    else ''
                ),

            'currency_symbol':
                (
                    quotation
                    .currency_id
                    .symbol
                    if quotation.currency_id
                    else ''
                ),

            'monthly_total':
                quotation.total_mensual,

            'total':
                quotation.total_por_modalidad,

            'state':
                quotation.estado,

            'equipment_count':
                len(
                    quotation
                    .linea_equipos_ids
                ),
        }

    # ============================================================
    # LISTAR COTIZACIONES
    # ============================================================

    def _action_quotations(
        self,
        data,
        email,
    ):

        limit = self._get_limit(
            data
        )

        search_text = (
            self._safe_str(
                data.get(
                    'search'
                )
            )
        )

        state = (
            self._safe_str(
                data.get(
                    'estado'
                )
                or data.get(
                    'state'
                )
            )
        )

        domain = []

        if state:

            domain.append(
                (
                    'estado',
                    '=',
                    state,
                )
            )

        if search_text:

            domain += [
                '|',
                '|',

                (
                    'name',
                    'ilike',
                    search_text,
                ),

                (
                    'cliente_id.name',
                    'ilike',
                    search_text,
                ),

                (
                    'cliente_id.vat',
                    'ilike',
                    search_text,
                ),
            ]

        quotations = (
            request.env[
                'copier.quotation'
            ]
            .sudo()
            .search(
                domain,
                order='id desc',
                limit=limit,
            )
        )

        values = [
            self._serialize_quotation_summary(
                quotation
            )
            for quotation
            in quotations
        ]

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATIONS | '
            'email=%s | '
            'search=%s | '
            'state=%s | '
            'count=%s',
            email,
            search_text,
            state,
            len(values),
        )

        return {
            'ok': True,
            'action': 'quotations',
            'count': len(values),
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

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        equipment = []

        for line in (
            quotation
            .linea_equipos_ids
        ):

            equipment.append(
                {
                    'id':
                        line.id,

                    'sequence':
                        line.sequence,

                    'equipment_id':
                        line.equipo_id.id,

                    'equipment':
                        line.equipo_id.name
                        or '',

                    'brand':
                        (
                            line
                            .marca_id
                            .name
                            if line.marca_id
                            else ''
                        ),

                    'quantity':
                        line.cantidad,

                    'equipment_type':
                        line.tipo_equipo,

                    'format':
                        line.formato,

                    'monthly_bw':
                        line.volumen_mensual_bn,

                    'monthly_color':
                        line.volumen_mensual_color,

                    'price_bw':
                        line.precio_bn,

                    'price_color':
                        line.precio_color,

                    'subtotal_bw':
                        line.subtotal_bn,

                    'subtotal_color':
                        line.subtotal_color,

                    'subtotal':
                        line.subtotal_linea,

                    'notes':
                        line.observaciones
                        or '',
                }
            )

        return {
            'ok': True,
            'action': (
                'quotation_detail'
            ),

            'quotation': {

                'id':
                    quotation.id,

                'name':
                    quotation.name
                    or '',

                'customer_id':
                    quotation
                    .cliente_id
                    .id,

                'customer':
                    quotation
                    .cliente_id
                    .name
                    or '',

                'vat':
                    quotation
                    .cliente_id
                    .vat
                    or '',

                'contact':
                    quotation.contacto
                    or '',

                'phone':
                    quotation.telefono
                    or '',

                'email':
                    quotation.email
                    or '',

                'address':
                    quotation.direccion
                    or '',

                'branch':
                    quotation.sede
                    or '',

                'currency_id':
                    quotation
                    .currency_id
                    .id,

                'currency':
                    quotation
                    .currency_id
                    .name
                    or '',

                'currency_symbol':
                    quotation
                    .currency_id
                    .symbol
                    or '',

                'payment_mode_id':
                    (
                        quotation
                        .modalidad_pago_id
                        .id
                        if quotation
                        .modalidad_pago_id
                        else False
                    ),

                'payment_mode':
                    (
                        quotation
                        .modalidad_pago_id
                        .name
                        if quotation
                        .modalidad_pago_id
                        else ''
                    ),

                'duration_id':
                    (
                        quotation
                        .duracion_contrato_id
                        .id
                        if quotation
                        .duracion_contrato_id
                        else False
                    ),

                'duration':
                    (
                        quotation
                        .duracion_contrato_id
                        .name
                        if quotation
                        .duracion_contrato_id
                        else ''
                    ),

                'quotation_date':
                    quotation
                    .fecha_cotizacion,

                'validity_days':
                    quotation
                    .validez_dias,

                'expiration_date':
                    quotation
                    .fecha_vencimiento,

                'proposed_start':
                    quotation
                    .fecha_inicio_propuesta,

                'proposed_end':
                    quotation
                    .fecha_fin_propuesta,

                'general_discount':
                    quotation
                    .descuento_general,

                'igv':
                    quotation.igv,

                'monthly_subtotal':
                    quotation
                    .subtotal_mensual,

                'monthly_discount':
                    quotation
                    .descuento_mensual,

                'monthly_igv':
                    quotation
                    .igv_mensual,

                'monthly_total':
                    quotation
                    .total_mensual,

                'final_subtotal':
                    quotation
                    .subtotal_final,

                'final_igv':
                    quotation
                    .igv_final,

                'total':
                    quotation
                    .total_por_modalidad,

                'annual_total':
                    quotation
                    .total_anual,

                'state':
                    quotation.estado,

                'notes':
                    quotation
                    .observaciones
                    or '',

                'equipment':
                    equipment,
            },
        }

    # ============================================================
    # HELPER MONEDA
    # ============================================================

    def _get_currency(
        self,
        currency_code,
    ):

        currency_code = (
            self._safe_str(
                currency_code,
                'PEN',
            )
            or 'PEN'
        ).upper()

        currency = (
            request.env[
                'res.currency'
            ]
            .sudo()
            .search(
                [
                    (
                        'name',
                        '=',
                        currency_code,
                    ),
                ],
                limit=1,
            )
        )

        if not currency:

            raise ValueError(
                (
                    'Moneda no encontrada: '
                    f'{currency_code}'
                )
            )

        return currency

    # ============================================================
    # PREPARAR LÍNEAS
    # ============================================================

    def _prepare_equipment_lines(
        self,
        equipment_data,
    ):

        if not isinstance(
            equipment_data,
            list,
        ):

            raise ValueError(
                'equipos debe ser una lista'
            )

        if not equipment_data:

            raise ValueError(
                (
                    'Debe incluir al menos '
                    'un equipo'
                )
            )

        lines = []

        for index, item in enumerate(
            equipment_data,
            start=1,
        ):

            if not isinstance(
                item,
                dict,
            ):

                raise ValueError(
                    (
                        f'Equipo #{index}: '
                        'formato inválido'
                    )
                )

            machine_id = (
                self._safe_int(
                    item.get(
                        'equipo_id'
                    )
                    or item.get(
                        'equipment_id'
                    ),
                    default=0,
                )
            )

            if not machine_id:

                raise ValueError(
                    (
                        f'Equipo #{index}: '
                        'falta equipo_id'
                    )
                )

            machine = (
                request.env[
                    'modelos.maquinas'
                ]
                .sudo()
                .browse(
                    machine_id
                )
            )

            if not machine.exists():

                raise ValueError(
                    (
                        f'Equipo #{index}: '
                        'modelo no encontrado'
                    )
                )

            quantity = (
                self._safe_int(
                    item.get(
                        'cantidad'
                    )
                    or item.get(
                        'quantity'
                    ),
                    default=1,
                    minimum=1,
                )
            )

            equipment_type = (
                self._safe_str(
                    item.get(
                        'tipo_equipo'
                    )
                    or item.get(
                        'equipment_type'
                    )
                )
                or 'monocroma'
            )

            if equipment_type not in {
                'monocroma',
                'color',
            }:

                raise ValueError(
                    (
                        f'Equipo #{index}: '
                        'tipo_equipo inválido'
                    )
                )

            format_value = (
                self._safe_str(
                    item.get(
                        'formato'
                    )
                    or item.get(
                        'format'
                    )
                )
                or 'a4'
            )

            if format_value not in {
                'a4',
                'a3',
            }:

                raise ValueError(
                    (
                        f'Equipo #{index}: '
                        'formato inválido'
                    )
                )

            volume_bw = (
                self._safe_int(
                    item.get(
                        'volumen_mensual_bn'
                    )
                    or item.get(
                        'monthly_bw'
                    ),
                    default=0,
                    minimum=0,
                )
            )

            volume_color = (
                self._safe_int(
                    item.get(
                        'volumen_mensual_color'
                    )
                    or item.get(
                        'monthly_color'
                    ),
                    default=0,
                    minimum=0,
                )
            )

            if (
                equipment_type
                == 'monocroma'
            ):

                volume_color = 0

            price_bw = (
                self._safe_float(
                    item.get(
                        'precio_bn'
                    )
                    or item.get(
                        'price_bw'
                    ),
                    default=0.0,
                    minimum=0.0,
                )
            )

            price_color = (
                self._safe_float(
                    item.get(
                        'precio_color'
                    )
                    or item.get(
                        'price_color'
                    ),
                    default=0.0,
                    minimum=0.0,
                )
            )

            lines.append(
                (
                    0,
                    0,
                    {
                        'sequence':
                            index * 10,

                        'equipo_id':
                            machine.id,

                        'cantidad':
                            quantity,

                        'tipo_equipo':
                            equipment_type,

                        'formato':
                            format_value,

                        'volumen_mensual_bn':
                            volume_bw,

                        'volumen_mensual_color':
                            volume_color,

                        'precio_bn':
                            price_bw,

                        'precio_color':
                            price_color,

                        'observaciones':
                            self._safe_str(
                                item.get(
                                    'observaciones'
                                )
                                or item.get(
                                    'notes'
                                )
                            ),
                    },
                )
            )

        return lines

    # ============================================================
    # CREAR COTIZACIÓN
    # ============================================================

    def _action_create_quotation(
        self,
        data,
        email,
    ):

        customer_id = (
            self._safe_int(
                data.get(
                    'cliente_id'
                )
                or data.get(
                    'customer_id'
                ),
                default=0,
            )
        )

        payment_mode_id = (
            self._safe_int(
                data.get(
                    'modalidad_pago_id'
                )
                or data.get(
                    'payment_mode_id'
                ),
                default=0,
            )
        )

        duration_id = (
            self._safe_int(
                data.get(
                    'duracion_contrato_id'
                )
                or data.get(
                    'duration_id'
                ),
                default=0,
            )
        )

        equipment_data = (
            data.get(
                'equipos'
            )
            or data.get(
                'equipment'
            )
            or []
        )

        if not customer_id:

            raise ValueError(
                'cliente_id es obligatorio'
            )

        if not payment_mode_id:

            raise ValueError(
                (
                    'modalidad_pago_id '
                    'es obligatorio'
                )
            )

        partner = (
            request.env[
                'res.partner'
            ]
            .sudo()
            .browse(
                customer_id
            )
        )

        if not partner.exists():

            raise ValueError(
                'Cliente no encontrado'
            )

        payment_mode = (
            request.env[
                'copier.payment.mode'
            ]
            .sudo()
            .browse(
                payment_mode_id
            )
        )

        if not payment_mode.exists():

            raise ValueError(
                (
                    'Modalidad de pago '
                    'no encontrada'
                )
            )

        currency = (
            self._get_currency(
                data.get(
                    'currency'
                )
                or 'PEN'
            )
        )

        duration = False

        if duration_id:

            duration = (
                request.env[
                    'copier.duracion'
                ]
                .sudo()
                .browse(
                    duration_id
                )
            )

            if not duration.exists():

                raise ValueError(
                    (
                        'Duración '
                        'no encontrada'
                    )
                )

        lines = (
            self._prepare_equipment_lines(
                equipment_data
            )
        )

        vals = {

            'cliente_id':
                partner.id,

            'modalidad_pago_id':
                payment_mode.id,

            'currency_id':
                currency.id,

            'contacto':
                self._safe_str(
                    data.get(
                        'contacto'
                    )
                    or data.get(
                        'contact'
                    )
                ),

            'telefono':
                self._safe_str(
                    data.get(
                        'telefono'
                    )
                    or data.get(
                        'phone'
                    )
                ),

            'email':
                self._safe_str(
                    data.get(
                        'email'
                    )
                ),

            'direccion':
                self._safe_str(
                    data.get(
                        'direccion'
                    )
                    or data.get(
                        'address'
                    )
                ),

            'sede':
                self._safe_str(
                    data.get(
                        'sede'
                    )
                    or data.get(
                        'branch'
                    )
                ),

            'validez_dias':
                self._safe_int(
                    data.get(
                        'validez_dias'
                    )
                    or data.get(
                        'validity_days'
                    ),
                    default=30,
                    minimum=1,
                    maximum=365,
                ),

            'descuento_general':
                self._safe_float(
                    data.get(
                        'descuento_general'
                    )
                    or data.get(
                        'general_discount'
                    ),
                    default=0.0,
                    minimum=0.0,
                    maximum=100.0,
                ),

            'igv':
                self._safe_float(
                    data.get(
                        'igv'
                    ),
                    default=18.0,
                    minimum=0.0,
                    maximum=100.0,
                ),

            'observaciones':
                self._safe_str(
                    data.get(
                        'observaciones'
                    )
                    or data.get(
                        'notes'
                    )
                ),

            'linea_equipos_ids':
                lines,
        }

        if duration:

            vals[
                'duracion_contrato_id'
            ] = duration.id

        start_date = (
            data.get(
                'fecha_inicio_propuesta'
            )
            or data.get(
                'proposed_start'
            )
        )

        if start_date:

            vals[
                'fecha_inicio_propuesta'
            ] = start_date

        quotation = (
            request.env[
                'copier.quotation'
            ]
            .sudo()
            .create(
                vals
            )
        )

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION CREATED | '
            'id=%s | '
            'name=%s | '
            'customer=%s | '
            'user_email=%s | '
            'currency=%s | '
            'monthly_total=%s | '
            'total=%s',
            quotation.id,
            quotation.name,
            partner.name,
            email,
            currency.name,
            quotation.total_mensual,
            quotation.total_por_modalidad,
        )

        return {
            'ok': True,
            'action': (
                'create_quotation'
            ),
            'message': (
                'Cotización creada '
                'correctamente'
            ),
            'quotation': (
                self._serialize_quotation_summary(
                    quotation
                )
            ),
        }

    # ============================================================
    # ACTUALIZAR COTIZACIÓN
    # ============================================================

    def _action_update_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        if (
            quotation.estado
            not in {
                'borrador',
                'rechazado',
            }
        ):

            raise ValueError(
                (
                    'Solo se pueden modificar '
                    'cotizaciones en borrador '
                    'o rechazadas'
                )
            )

        vals = {}

        text_mapping = {
            'contacto':
                'contacto',

            'contact':
                'contacto',

            'telefono':
                'telefono',

            'phone':
                'telefono',

            'email':
                'email',

            'direccion':
                'direccion',

            'address':
                'direccion',

            'sede':
                'sede',

            'branch':
                'sede',

            'observaciones':
                'observaciones',

            'notes':
                'observaciones',
        }

        for source, target in (
            text_mapping.items()
        ):

            if source in data:

                vals[
                    target
                ] = self._safe_str(
                    data.get(
                        source
                    )
                )

        if (
            'fecha_inicio_propuesta'
            in data
        ):

            vals[
                'fecha_inicio_propuesta'
            ] = data.get(
                'fecha_inicio_propuesta'
            )

        elif (
            'proposed_start'
            in data
        ):

            vals[
                'fecha_inicio_propuesta'
            ] = data.get(
                'proposed_start'
            )

        if (
            'validez_dias'
            in data
            or 'validity_days'
            in data
        ):

            vals[
                'validez_dias'
            ] = self._safe_int(
                data.get(
                    'validez_dias'
                )
                or data.get(
                    'validity_days'
                ),
                default=30,
                minimum=1,
                maximum=365,
            )

        if (
            'descuento_general'
            in data
            or 'general_discount'
            in data
        ):

            vals[
                'descuento_general'
            ] = self._safe_float(
                data.get(
                    'descuento_general'
                )
                or data.get(
                    'general_discount'
                ),
                default=0,
                minimum=0,
                maximum=100,
            )

        if 'igv' in data:

            vals[
                'igv'
            ] = self._safe_float(
                data.get(
                    'igv'
                ),
                default=18,
                minimum=0,
                maximum=100,
            )

        if 'currency' in data:

            currency = (
                self._get_currency(
                    data.get(
                        'currency'
                    )
                )
            )

            vals[
                'currency_id'
            ] = currency.id

        if (
            'modalidad_pago_id'
            in data
            or 'payment_mode_id'
            in data
        ):

            payment_mode_id = (
                self._safe_int(
                    data.get(
                        'modalidad_pago_id'
                    )
                    or data.get(
                        'payment_mode_id'
                    ),
                    default=0,
                )
            )

            payment_mode = (
                request.env[
                    'copier.payment.mode'
                ]
                .sudo()
                .browse(
                    payment_mode_id
                )
            )

            if (
                not payment_mode.exists()
            ):

                raise ValueError(
                    (
                        'Modalidad de pago '
                        'no encontrada'
                    )
                )

            vals[
                'modalidad_pago_id'
            ] = payment_mode.id

        if (
            'duracion_contrato_id'
            in data
            or 'duration_id'
            in data
        ):

            duration_id = (
                self._safe_int(
                    data.get(
                        'duracion_contrato_id'
                    )
                    or data.get(
                        'duration_id'
                    ),
                    default=0,
                )
            )

            duration = (
                request.env[
                    'copier.duracion'
                ]
                .sudo()
                .browse(
                    duration_id
                )
            )

            if not duration.exists():

                raise ValueError(
                    (
                        'Duración '
                        'no encontrada'
                    )
                )

            vals[
                'duracion_contrato_id'
            ] = duration.id

        # ========================================================
        # REEMPLAZAR LÍNEAS SI SE ENVÍAN EQUIPOS
        # ========================================================

        if (
            'equipos'
            in data
            or 'equipment'
            in data
        ):

            equipment_data = (
                data.get(
                    'equipos'
                )
                or data.get(
                    'equipment'
                )
                or []
            )

            lines = (
                self._prepare_equipment_lines(
                    equipment_data
                )
            )

            vals[
                'linea_equipos_ids'
            ] = [
                (
                    5,
                    0,
                    0,
                ),
                *lines,
            ]

        if vals:

            quotation.write(
                vals
            )

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION UPDATED | '
            'id=%s | '
            'name=%s | '
            'email=%s | '
            'fields=%s',
            quotation.id,
            quotation.name,
            email,
            list(
                vals.keys()
            ),
        )

        return {
            'ok': True,
            'action': (
                'update_quotation'
            ),
            'message': (
                'Cotización actualizada '
                'correctamente'
            ),
            'quotation': (
                self._serialize_quotation_summary(
                    quotation
                )
            ),
        }

    # ============================================================
    # ELIMINAR COTIZACIÓN
    # ============================================================

    def _action_delete_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        if (
            quotation.estado
            != 'borrador'
        ):

            raise ValueError(
                (
                    'Solo se pueden eliminar '
                    'cotizaciones en borrador'
                )
            )

        quotation_id = (
            quotation.id
        )

        quotation_name = (
            quotation.name
        )

        quotation.unlink()

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION DELETED | '
            'id=%s | '
            'name=%s | '
            'email=%s',
            quotation_id,
            quotation_name,
            email,
        )

        return {
            'ok': True,
            'action': (
                'delete_quotation'
            ),
            'message': (
                'Cotización eliminada '
                'correctamente'
            ),
        }

    # ============================================================
    # ENVIAR
    # ============================================================

    def _action_send_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        quotation.action_enviar_cotizacion()

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION SENT | '
            'id=%s | '
            'name=%s | '
            'email=%s',
            quotation.id,
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': (
                'send_quotation'
            ),
            'message': (
                'Cotización marcada '
                'como enviada'
            ),
            'state':
                quotation.estado,
        }

    # ============================================================
    # APROBAR
    # ============================================================

    def _action_approve_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        quotation.action_aprobar_cotizacion()

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION APPROVED | '
            'id=%s | '
            'name=%s | '
            'email=%s',
            quotation.id,
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': (
                'approve_quotation'
            ),
            'message': (
                'Cotización aprobada'
            ),
            'state':
                quotation.estado,
        }

    # ============================================================
    # RECHAZAR
    # ============================================================

    def _action_reject_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        quotation.write(
            {
                'estado':
                    'rechazado',
            }
        )

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION REJECTED | '
            'id=%s | '
            'name=%s | '
            'email=%s',
            quotation.id,
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': (
                'reject_quotation'
            ),
            'message': (
                'Cotización rechazada'
            ),
            'state':
                quotation.estado,
        }

    # ============================================================
    # CONVERTIR A CONTRATO
    # ============================================================

    def _action_convert_quotation(
        self,
        data,
        email,
    ):

        quotation = (
            self._get_quotation_from_data(
                data
            )
        )

        if (
            quotation.estado
            != 'aprobado'
        ):

            raise ValueError(
                (
                    'La cotización debe '
                    'estar aprobada antes '
                    'de convertirla'
                )
            )

        quotation.action_convertir_contratos()

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION CONVERTED | '
            'id=%s | '
            'name=%s | '
            'email=%s',
            quotation.id,
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': (
                'convert_quotation'
            ),
            'message': (
                'Cotización convertida '
                'a contratos'
            ),
            'state':
                quotation.estado,
        }

    # ============================================================
    # OBTENER COTIZACIÓN
    # ============================================================

    def _get_quotation_from_data(
        self,
        data,
    ):

        quotation_id = (
            self._safe_int(
                data.get(
                    'quotation_id'
                )
                or data.get(
                    'cotizacion_id'
                ),
                default=0,
            )
        )

        if not quotation_id:

            raise ValueError(
                (
                    'quotation_id '
                    'es obligatorio'
                )
            )

        quotation = (
            request.env[
                'copier.quotation'
            ]
            .sudo()
            .browse(
                quotation_id
            )
        )

        if not quotation.exists():

            raise ValueError(
                'Cotización no encontrada'
            )

        return quotation