from odoo import http
from odoo.http import request

import json
import logging
import secrets
import traceback


_logger = logging.getLogger(__name__)


class PowerAppsAPI(http.Controller):
    """
    API CENTRAL PARA POWER APPS

    Endpoint único:
        POST /api/powerapps

    Headers:
        X-API-Key
        X-User-Email
        Content-Type: application/json

    Body:
        {
            "action": "customers",
            "data": {}
        }

    Power Apps puede enviar "data" como:
        {}
    o como:
        "{}"

    Este controlador acepta ambas formas.
    """

    # ============================================================
    # CONFIGURACIÓN
    # ============================================================

    API_CONFIG_KEY = 'copier.powerapps.api_key'

    # Opcional:
    # Si este parámetro está vacío, cualquier correo con API Key
    # válida podrá consumir la API.
    #
    # Ejemplo:
    # info@copiercompanysac.com,ventas@copiercompanysac.com
    ALLOWED_EMAILS_CONFIG_KEY = 'copier.powerapps.allowed_emails'

    DEFAULT_LIMIT = 100
    MAX_LIMIT = 500

    # ============================================================
    # RESPUESTA JSON
    # ============================================================

    def _json_response(self, data, status=200):
        """
        Devuelve siempre JSON válido y agrega cabeceras CORS.
        """

        try:
            body = json.dumps(
                data,
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            _logger.exception(
                '[POWERAPPS API] Error serializando respuesta JSON'
            )

            body = json.dumps({
                'ok': False,
                'error': 'Error serializando respuesta',
            })

            status = 500

        return request.make_response(
            body,
            headers=[
                (
                    'Content-Type',
                    'application/json; charset=utf-8'
                ),
                (
                    'Access-Control-Allow-Origin',
                    '*'
                ),
                (
                    'Access-Control-Allow-Headers',
                    'Content-Type, X-API-Key, X-User-Email'
                ),
                (
                    'Access-Control-Allow-Methods',
                    'POST, OPTIONS'
                ),
                (
                    'Cache-Control',
                    'no-store'
                ),
            ],
            status=status,
        )

    # ============================================================
    # HELPERS GENERALES
    # ============================================================

    def _get_external_email(self):
        email = (
            request.httprequest.headers.get('X-User-Email')
            or ''
        )

        return email.strip().lower()

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
            result = max(result, minimum)

        if maximum is not None:
            result = min(result, maximum)

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
            result = max(result, minimum)

        if maximum is not None:
            result = min(result, maximum)

        return result

    def _safe_str(self, value):
        if value is None:
            return ''

        return str(value).strip()

    def _get_limit(self, data):
        limit = self._safe_int(
            data.get('limit'),
            default=self.DEFAULT_LIMIT,
            minimum=1,
            maximum=self.MAX_LIMIT,
        )

        return limit

    # ============================================================
    # SEGURIDAD
    # ============================================================

    def _check_api_key(self):
        """
        Valida la API Key usando comparación segura.
        """

        configured_key = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param(self.API_CONFIG_KEY)
        )

        received_key = (
            request.httprequest.headers.get('X-API-Key')
            or ''
        )

        if not configured_key:
            _logger.error(
                '[POWERAPPS API] '
                'No está configurado el parámetro %s',
                self.API_CONFIG_KEY,
            )

            return False, 'API Key no configurada en Odoo'

        if not received_key:
            _logger.warning(
                '[POWERAPPS API] '
                'Solicitud sin X-API-Key'
            )

            return False, 'Falta encabezado X-API-Key'

        try:
            valid = secrets.compare_digest(
                str(received_key),
                str(configured_key),
            )
        except Exception:
            valid = received_key == configured_key

        if not valid:
            _logger.warning(
                '[POWERAPPS API] API Key inválida'
            )

            return False, 'API Key inválida'

        return True, None

    def _check_external_email(self, email):
        """
        Permite opcionalmente limitar qué cuentas Microsoft
        pueden consumir la API.

        Parámetro:
            copier.powerapps.allowed_emails

        Ejemplo:
            info@copiercompanysac.com,
            ventas@copiercompanysac.com

        Si el parámetro está vacío, no restringe por correo.
        """

        configured = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param(self.ALLOWED_EMAILS_CONFIG_KEY)
            or ''
        ).strip()

        if not configured:
            return True, None

        allowed_emails = {
            item.strip().lower()
            for item in configured.split(',')
            if item.strip()
        }

        if not email:
            return False, 'Falta X-User-Email'

        if email not in allowed_emails:
            _logger.warning(
                '[POWERAPPS API] '
                'Correo no autorizado | email=%s',
                email,
            )

            return False, 'Usuario no autorizado'

        return True, None

    # ============================================================
    # PARSEO DEL REQUEST
    # ============================================================

    def _parse_payload(self):
        """
        Lee y normaliza el JSON.

        Power Apps puede convertir "data" en texto:

            "data": "{}"

        Este método lo vuelve a convertir en diccionario.
        """

        raw_data = request.httprequest.data or b''

        if not raw_data:
            return None, 'No se recibió información'

        try:
            payload = json.loads(
                raw_data.decode('utf-8')
            )
        except Exception as exc:
            _logger.warning(
                '[POWERAPPS API] JSON inválido | error=%s',
                exc,
            )

            return None, 'JSON inválido'

        if not isinstance(payload, dict):
            return None, 'El cuerpo debe ser un objeto JSON'

        action = self._safe_str(
            payload.get('action')
        )

        if not action:
            return None, 'Falta action'

        data = payload.get('data', {})

        # --------------------------------------------------------
        # Power Apps puede mandar data como string
        # --------------------------------------------------------

        if isinstance(data, str):
            data = data.strip()

            if not data:
                data = {}

            else:
                try:
                    data = json.loads(data)

                except Exception as exc:
                    _logger.warning(
                        '[POWERAPPS API] '
                        'data contiene JSON inválido | '
                        'action=%s | error=%s',
                        action,
                        exc,
                    )

                    return (
                        None,
                        'El campo data contiene JSON inválido'
                    )

        if data is None:
            data = {}

        if not isinstance(data, dict):
            return (
                None,
                'El campo data debe ser un objeto JSON'
            )

        return {
            'action': action,
            'data': data,
        }, None

    # ============================================================
    # LOG DE REQUEST
    # ============================================================

    def _log_request(
        self,
        action,
        email,
        data,
    ):
        """
        No imprime API Key ni información sensible.
        """

        safe_data = {}

        try:
            for key, value in data.items():

                if key.lower() in {
                    'password',
                    'api_key',
                    'token',
                    'secret',
                }:
                    safe_data[key] = '***'
                else:
                    safe_data[key] = value

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
            request.httprequest.remote_addr,
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
    def powerapps_options(self, **kwargs):

        return request.make_response(
            '',
            headers=[
                (
                    'Access-Control-Allow-Origin',
                    '*'
                ),
                (
                    'Access-Control-Allow-Headers',
                    'Content-Type, X-API-Key, X-User-Email'
                ),
                (
                    'Access-Control-Allow-Methods',
                    'POST, OPTIONS'
                ),
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
        save_session=False,
    )
    def powerapps_execute(self, **kwargs):

        # --------------------------------------------------------
        # API KEY
        # --------------------------------------------------------

        valid, error = self._check_api_key()

        if not valid:
            return self._json_response(
                {
                    'ok': False,
                    'error': error,
                },
                status=401,
            )

        # --------------------------------------------------------
        # CORREO MICROSOFT
        # --------------------------------------------------------

        email = self._get_external_email()

        valid_email, email_error = (
            self._check_external_email(email)
        )

        if not valid_email:
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

        payload, payload_error = (
            self._parse_payload()
        )

        if payload_error:
            return self._json_response(
                {
                    'ok': False,
                    'error': payload_error,
                },
                status=400,
            )

        action = payload['action']
        data = payload['data']

        self._log_request(
            action,
            email,
            data,
        )

        # --------------------------------------------------------
        # ROUTER
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

            'convert_quotation':
                self._action_convert_quotation,
        }

        handler = actions.get(action)

        if not handler:
            _logger.warning(
                '[POWERAPPS API] '
                'Acción desconocida | '
                'action=%s | email=%s',
                action,
                email,
            )

            return self._json_response(
                {
                    'ok': False,
                    'error': (
                        f'Acción no válida: {action}'
                    ),
                },
                status=400,
            )

        # --------------------------------------------------------
        # EJECUTAR
        # --------------------------------------------------------

        try:

            result = handler(
                data=data,
                email=email,
            )

            if not isinstance(result, dict):
                result = {
                    'ok': True,
                    'result': result,
                }

            if 'ok' not in result:
                result['ok'] = True

            _logger.info(
                '[POWERAPPS API] RESPONSE OK | '
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
                '[POWERAPPS API] VALIDATION ERROR | '
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
                '[POWERAPPS API] INTERNAL ERROR | '
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
                    'error': 'Error interno en Odoo',
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
            'message': 'Conexión correcta con Odoo',
            'user_email': email,
        }

    # ============================================================
    # CLIENTES
    # ============================================================

    def _action_customers(
        self,
        data,
        email,
    ):

        search_text = self._safe_str(
            data.get('search')
        )

        limit = self._get_limit(data)

        domain = [
            ('active', '=', True),
        ]

        # Si quieres únicamente empresas, Power Apps puede mandar:
        #
        # {
        #     "only_companies": true
        # }

        only_companies = bool(
            data.get('only_companies', False)
        )

        if only_companies:
            domain.append(
                ('is_company', '=', True)
            )

        if search_text:

            domain += [
                '|',
                '|',
                '|',

                (
                    'name',
                    'ilike',
                    search_text
                ),

                (
                    'vat',
                    'ilike',
                    search_text
                ),

                (
                    'email',
                    'ilike',
                    search_text
                ),

                (
                    'phone',
                    'ilike',
                    search_text
                ),
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

        values = []

        for partner in partners:

            values.append({
                'id':
                    partner.id,

                'name':
                    partner.name or '',

                'display_name':
                    partner.display_name or '',

                'vat':
                    partner.vat or '',

                'email':
                    partner.email or '',

                'phone':
                    partner.phone or '',

                'mobile':
                    partner.mobile or '',

                'street':
                    partner.street or '',

                'street2':
                    partner.street2 or '',

                'city':
                    partner.city or '',

                'state':
                    (
                        partner.state_id.name
                        if partner.state_id
                        else ''
                    ),

                'country':
                    (
                        partner.country_id.name
                        if partner.country_id
                        else ''
                    ),

                'is_company':
                    partner.is_company,
            })

        _logger.info(
            '[POWERAPPS API] CUSTOMERS | '
            'email=%s | search=%s | count=%s',
            email,
            search_text,
            len(values),
        )

        return {
            'ok': True,
            'action': 'customers',
            'count': len(values),
            'customers': values,
        }

    # ============================================================
    # DETALLE CLIENTE
    # ============================================================

    def _action_customer_detail(
        self,
        data,
        email,
    ):

        customer_id = self._safe_int(
            data.get('customer_id'),
            default=0,
        )

        if not customer_id:
            raise ValueError(
                'customer_id es obligatorio'
            )

        partner = (
            request.env['res.partner']
            .sudo()
            .browse(customer_id)
        )

        if not partner.exists():
            raise ValueError(
                'Cliente no encontrado'
            )

        return {
            'ok': True,

            'action':
                'customer_detail',

            'customer': {

                'id':
                    partner.id,

                'name':
                    partner.name or '',

                'vat':
                    partner.vat or '',

                'email':
                    partner.email or '',

                'phone':
                    partner.phone or '',

                'mobile':
                    partner.mobile or '',

                'street':
                    partner.street or '',

                'street2':
                    partner.street2 or '',

                'city':
                    partner.city or '',

                'zip':
                    partner.zip or '',

                'state':
                    (
                        partner.state_id.name
                        if partner.state_id
                        else ''
                    ),

                'country':
                    (
                        partner.country_id.name
                        if partner.country_id
                        else ''
                    ),
            },
        }

    # ============================================================
    # EQUIPOS
    # ============================================================

    def _action_equipment(
        self,
        data,
        email,
    ):

        search_text = self._safe_str(
            data.get('search')
        )

        limit = self._get_limit(data)

        domain = []

        if search_text:

            domain += [
                '|',

                (
                    'name',
                    'ilike',
                    search_text
                ),

                (
                    'marca_id.name',
                    'ilike',
                    search_text
                ),
            ]

        records = (
            request.env['modelos.maquinas']
            .sudo()
            .search(
                domain,
                order='name asc',
                limit=limit,
            )
        )

        values = []

        for rec in records:

            values.append({

                'id':
                    rec.id,

                'name':
                    rec.name or '',

                'brand_id':
                    (
                        rec.marca_id.id
                        if rec.marca_id
                        else False
                    ),

                'brand':
                    (
                        rec.marca_id.name
                        if rec.marca_id
                        else ''
                    ),

                'has_image':
                    bool(rec.imagen),
            })

        _logger.info(
            '[POWERAPPS API] EQUIPMENT | '
            'email=%s | search=%s | count=%s',
            email,
            search_text,
            len(values),
        )

        return {
            'ok': True,
            'action': 'equipment',
            'count': len(values),
            'equipment': values,
        }

    # ============================================================
    # DETALLE EQUIPO
    # ============================================================

    def _action_equipment_detail(
        self,
        data,
        email,
    ):

        equipment_id = self._safe_int(
            data.get('equipment_id'),
            default=0,
        )

        if not equipment_id:
            raise ValueError(
                'equipment_id es obligatorio'
            )

        machine = (
            request.env['modelos.maquinas']
            .sudo()
            .browse(equipment_id)
        )

        if not machine.exists():
            raise ValueError(
                'Equipo no encontrado'
            )

        return {
            'ok': True,

            'action':
                'equipment_detail',

            'equipment': {

                'id':
                    machine.id,

                'name':
                    machine.name or '',

                'brand':
                    (
                        machine.marca_id.name
                        if machine.marca_id
                        else ''
                    ),

                'specifications':
                    machine.especificaciones or '',

                'has_image':
                    bool(machine.imagen),
            },
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
            request.env['copier.payment.mode']
            .sudo()
            .search(
                [
                    ('activo', '=', True),
                ],
                order='frecuencia_meses asc',
            )
        )

        values = []

        for rec in records:

            values.append({

                'id':
                    rec.id,

                'name':
                    rec.name or '',

                'description':
                    rec.descripcion or '',

                'months':
                    rec.frecuencia_meses,

                'discount':
                    rec.descuento_porcentaje,
            })

        return {
            'ok': True,
            'action': 'payment_modes',
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

                'id':
                    rec.id,

                'name':
                    rec.name or '',

                'symbol':
                    rec.symbol or '',

                'position':
                    rec.position or '',
            })

        return {
            'ok': True,
            'action': 'currencies',
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
            request.env['copier.duracion']
            .sudo()
            .search(
                [],
                order='id asc',
            )
        )

        values = []

        for rec in records:

            values.append({
                'id':
                    rec.id,

                'name':
                    rec.name or '',
            })

        return {
            'ok': True,
            'action': 'durations',
            'durations': values,
        }

    # ============================================================
    # LISTAR COTIZACIONES
    # ============================================================

    def _action_quotations(
        self,
        data,
        email,
    ):

        limit = self._get_limit(data)

        search_text = self._safe_str(
            data.get('search')
        )

        estado = self._safe_str(
            data.get('estado')
        )

        domain = []

        if estado:
            domain.append(
                ('estado', '=', estado)
            )

        if search_text:

            domain += [
                '|',
                '|',

                (
                    'name',
                    'ilike',
                    search_text
                ),

                (
                    'cliente_id.name',
                    'ilike',
                    search_text
                ),

                (
                    'cliente_id.vat',
                    'ilike',
                    search_text
                ),
            ]

        records = (
            request.env['copier.quotation']
            .sudo()
            .search(
                domain,
                order='id desc',
                limit=limit,
            )
        )

        values = []

        for rec in records:

            values.append({

                'id':
                    rec.id,

                'name':
                    rec.name or '',

                'customer_id':
                    (
                        rec.cliente_id.id
                        if rec.cliente_id
                        else False
                    ),

                'customer':
                    (
                        rec.cliente_id.name
                        if rec.cliente_id
                        else ''
                    ),

                'date':
                    rec.fecha_cotizacion,

                'expiration_date':
                    rec.fecha_vencimiento,

                'currency':
                    (
                        rec.currency_id.name
                        if rec.currency_id
                        else ''
                    ),

                'currency_symbol':
                    (
                        rec.currency_id.symbol
                        if rec.currency_id
                        else ''
                    ),

                'monthly_total':
                    rec.total_mensual,

                'total':
                    rec.total_por_modalidad,

                'state':
                    rec.estado,

                'equipment_count':
                    len(
                        rec.linea_equipos_ids
                    ),
            })

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

        quotation_id = self._safe_int(
            data.get('quotation_id'),
            default=0,
        )

        if not quotation_id:
            raise ValueError(
                'quotation_id es obligatorio'
            )

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .browse(quotation_id)
        )

        if not quotation.exists():
            raise ValueError(
                'Cotización no encontrada'
            )

        lines = []

        for line in quotation.linea_equipos_ids:

            lines.append({

                'id':
                    line.id,

                'sequence':
                    line.sequence,

                'equipment_id':
                    line.equipo_id.id,

                'equipment':
                    line.equipo_id.name or '',

                'brand':
                    (
                        line.marca_id.name
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
                    line.observaciones or '',
            })

        return {

            'ok':
                True,

            'action':
                'quotation_detail',

            'quotation': {

                'id':
                    quotation.id,

                'name':
                    quotation.name or '',

                'customer_id':
                    quotation.cliente_id.id,

                'customer':
                    quotation.cliente_id.name or '',

                'vat':
                    quotation.cliente_id.vat or '',

                'contact':
                    quotation.contacto or '',

                'phone':
                    quotation.telefono or '',

                'email':
                    quotation.email or '',

                'address':
                    quotation.direccion or '',

                'branch':
                    quotation.sede or '',

                'currency_id':
                    quotation.currency_id.id,

                'currency':
                    quotation.currency_id.name or '',

                'currency_symbol':
                    quotation.currency_id.symbol or '',

                'payment_mode_id':
                    (
                        quotation.modalidad_pago_id.id
                        if quotation.modalidad_pago_id
                        else False
                    ),

                'payment_mode':
                    (
                        quotation.modalidad_pago_id.name
                        if quotation.modalidad_pago_id
                        else ''
                    ),

                'duration_id':
                    (
                        quotation.duracion_contrato_id.id
                        if quotation.duracion_contrato_id
                        else False
                    ),

                'duration':
                    (
                        quotation.duracion_contrato_id.name
                        if quotation.duracion_contrato_id
                        else ''
                    ),

                'quotation_date':
                    quotation.fecha_cotizacion,

                'validity_days':
                    quotation.validez_dias,

                'expiration_date':
                    quotation.fecha_vencimiento,

                'proposed_start':
                    quotation.fecha_inicio_propuesta,

                'proposed_end':
                    quotation.fecha_fin_propuesta,

                'general_discount':
                    quotation.descuento_general,

                'igv':
                    quotation.igv,

                'monthly_subtotal':
                    quotation.subtotal_mensual,

                'monthly_discount':
                    quotation.descuento_mensual,

                'monthly_igv':
                    quotation.igv_mensual,

                'monthly_total':
                    quotation.total_mensual,

                'final_subtotal':
                    quotation.subtotal_final,

                'final_igv':
                    quotation.igv_final,

                'total':
                    quotation.total_por_modalidad,

                'annual_total':
                    quotation.total_anual,

                'state':
                    quotation.estado,

                'notes':
                    quotation.observaciones or '',

                'equipment':
                    lines,
            },
        }

    # ============================================================
    # CREAR COTIZACIÓN
    # ============================================================

    def _action_create_quotation(
        self,
        data,
        email,
    ):

        customer_id = self._safe_int(
            data.get('cliente_id')
            or data.get('customer_id'),
            default=0,
        )

        payment_mode_id = self._safe_int(
            data.get('modalidad_pago_id')
            or data.get('payment_mode_id'),
            default=0,
        )

        duration_id = self._safe_int(
            data.get('duracion_contrato_id')
            or data.get('duration_id'),
            default=0,
        )

        equipment_data = (
            data.get('equipos')
            or data.get('equipment')
            or []
        )

        if not customer_id:
            raise ValueError(
                'cliente_id es obligatorio'
            )

        if not payment_mode_id:
            raise ValueError(
                'modalidad_pago_id es obligatorio'
            )

        if not isinstance(
            equipment_data,
            list,
        ):
            raise ValueError(
                'equipos debe ser una lista'
            )

        if not equipment_data:
            raise ValueError(
                'Debe incluir al menos un equipo'
            )

        # --------------------------------------------------------
        # Cliente
        # --------------------------------------------------------

        partner = (
            request.env['res.partner']
            .sudo()
            .browse(customer_id)
        )

        if not partner.exists():
            raise ValueError(
                'Cliente no encontrado'
            )

        # --------------------------------------------------------
        # Modalidad
        # --------------------------------------------------------

        payment_mode = (
            request.env['copier.payment.mode']
            .sudo()
            .browse(payment_mode_id)
        )

        if not payment_mode.exists():
            raise ValueError(
                'Modalidad de pago no encontrada'
            )

        # --------------------------------------------------------
        # Moneda
        # --------------------------------------------------------

        currency_code = (
            self._safe_str(
                data.get('currency')
            )
            or 'PEN'
        ).upper()

        currency = (
            request.env['res.currency']
            .sudo()
            .search(
                [
                    ('name', '=', currency_code),
                ],
                limit=1,
            )
        )

        if not currency:
            raise ValueError(
                f'Moneda no encontrada: '
                f'{currency_code}'
            )

        # --------------------------------------------------------
        # Duración
        # --------------------------------------------------------

        duration = False

        if duration_id:

            duration = (
                request.env['copier.duracion']
                .sudo()
                .browse(duration_id)
            )

            if not duration.exists():
                raise ValueError(
                    'Duración no encontrada'
                )

        # --------------------------------------------------------
        # Líneas
        # --------------------------------------------------------

        lines = []

        for index, item in enumerate(
            equipment_data,
            start=1,
        ):

            if not isinstance(item, dict):
                raise ValueError(
                    f'Equipo #{index}: '
                    f'formato inválido'
                )

            machine_id = self._safe_int(
                item.get('equipo_id')
                or item.get('equipment_id'),
                default=0,
            )

            if not machine_id:
                raise ValueError(
                    f'Equipo #{index}: '
                    f'falta equipo_id'
                )

            machine = (
                request.env['modelos.maquinas']
                .sudo()
                .browse(machine_id)
            )

            if not machine.exists():
                raise ValueError(
                    f'Equipo #{index}: '
                    f'modelo no encontrado'
                )

            quantity = self._safe_int(
                item.get('cantidad')
                or item.get('quantity'),
                default=1,
                minimum=1,
            )

            equipment_type = (
                self._safe_str(
                    item.get('tipo_equipo')
                    or item.get('equipment_type')
                )
                or 'monocroma'
            )

            if equipment_type not in {
                'monocroma',
                'color',
            }:
                raise ValueError(
                    f'Equipo #{index}: '
                    f'tipo_equipo inválido'
                )

            format_value = (
                self._safe_str(
                    item.get('formato')
                    or item.get('format')
                )
                or 'a4'
            )

            if format_value not in {
                'a4',
                'a3',
            }:
                raise ValueError(
                    f'Equipo #{index}: '
                    f'formato inválido'
                )

            monthly_bw = self._safe_int(
                item.get('volumen_mensual_bn')
                or item.get('monthly_bw'),
                default=0,
                minimum=0,
            )

            monthly_color = self._safe_int(
                item.get('volumen_mensual_color')
                or item.get('monthly_color'),
                default=0,
                minimum=0,
            )

            if equipment_type == 'monocroma':
                monthly_color = 0

            price_bw = self._safe_float(
                item.get('precio_bn')
                or item.get('price_bw'),
                default=0.0,
                minimum=0.0,
            )

            price_color = self._safe_float(
                item.get('precio_color')
                or item.get('price_color'),
                default=0.0,
                minimum=0.0,
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
                            monthly_bw,

                        'volumen_mensual_color':
                            monthly_color,

                        'precio_bn':
                            price_bw,

                        'precio_color':
                            price_color,

                        'observaciones':
                            self._safe_str(
                                item.get('observaciones')
                                or item.get('notes')
                            ),
                    },
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
                    data.get('contacto')
                    or data.get('contact')
                ),

            'telefono':
                self._safe_str(
                    data.get('telefono')
                    or data.get('phone')
                ),

            'email':
                self._safe_str(
                    data.get('email')
                ),

            'direccion':
                self._safe_str(
                    data.get('direccion')
                    or data.get('address')
                ),

            'sede':
                self._safe_str(
                    data.get('sede')
                    or data.get('branch')
                ),

            'validez_dias':
                self._safe_int(
                    data.get('validez_dias')
                    or data.get('validity_days'),
                    default=30,
                    minimum=1,
                    maximum=365,
                ),

            'descuento_general':
                self._safe_float(
                    data.get('descuento_general')
                    or data.get('general_discount'),
                    default=0.0,
                    minimum=0.0,
                    maximum=100.0,
                ),

            'igv':
                self._safe_float(
                    data.get('igv'),
                    default=18.0,
                    minimum=0.0,
                    maximum=100.0,
                ),

            'observaciones':
                self._safe_str(
                    data.get('observaciones')
                    or data.get('notes')
                ),

            'linea_equipos_ids':
                lines,
        }

        if duration:
            vals[
                'duracion_contrato_id'
            ] = duration.id

        if data.get(
            'fecha_inicio_propuesta'
        ):
            vals[
                'fecha_inicio_propuesta'
            ] = data[
                'fecha_inicio_propuesta'
            ]

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .create(vals)
        )

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION CREATED | '
            'id=%s | '
            'name=%s | '
            'cliente=%s | '
            'email=%s | '
            'total=%s',
            quotation.id,
            quotation.name,
            partner.name,
            email,
            quotation.total_por_modalidad,
        )

        return {

            'ok':
                True,

            'action':
                'create_quotation',

            'message':
                'Cotización creada correctamente',

            'quotation': {

                'id':
                    quotation.id,

                'name':
                    quotation.name,

                'customer':
                    partner.name,

                'currency':
                    currency.name,

                'monthly_subtotal':
                    quotation.subtotal_mensual,

                'monthly_igv':
                    quotation.igv_mensual,

                'monthly_total':
                    quotation.total_mensual,

                'final_subtotal':
                    quotation.subtotal_final,

                'final_igv':
                    quotation.igv_final,

                'total':
                    quotation.total_por_modalidad,

                'quotation_date':
                    quotation.fecha_cotizacion,

                'expiration_date':
                    quotation.fecha_vencimiento,

                'state':
                    quotation.estado,

                'created_by_email':
                    email,
            },
        }

    # ============================================================
    # ACTUALIZAR COTIZACIÓN
    # ============================================================

    def _action_update_quotation(
        self,
        data,
        email,
    ):

        quotation_id = self._safe_int(
            data.get('quotation_id'),
            default=0,
        )

        if not quotation_id:
            raise ValueError(
                'quotation_id es obligatorio'
            )

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .browse(quotation_id)
        )

        if not quotation.exists():
            raise ValueError(
                'Cotización no encontrada'
            )

        if quotation.estado not in {
            'borrador',
            'rechazado',
        }:
            raise ValueError(
                'Solo se pueden modificar '
                'cotizaciones en borrador o rechazadas'
            )

        vals = {}

        simple_fields = {

            'contacto':
                'contacto',

            'telefono':
                'telefono',

            'email':
                'email',

            'direccion':
                'direccion',

            'sede':
                'sede',

            'fecha_inicio_propuesta':
                'fecha_inicio_propuesta',

            'observaciones':
                'observaciones',
        }

        for source, target in simple_fields.items():

            if source in data:
                vals[target] = data[source]

        if 'validez_dias' in data:

            vals['validez_dias'] = (
                self._safe_int(
                    data.get('validez_dias'),
                    default=30,
                    minimum=1,
                    maximum=365,
                )
            )

        if 'descuento_general' in data:

            vals['descuento_general'] = (
                self._safe_float(
                    data.get(
                        'descuento_general'
                    ),
                    default=0,
                    minimum=0,
                    maximum=100,
                )
            )

        if 'igv' in data:

            vals['igv'] = (
                self._safe_float(
                    data.get('igv'),
                    default=18,
                    minimum=0,
                    maximum=100,
                )
            )

        if 'currency' in data:

            currency_code = (
                self._safe_str(
                    data.get('currency')
                )
                .upper()
            )

            currency = (
                request.env['res.currency']
                .sudo()
                .search(
                    [
                        (
                            'name',
                            '=',
                            currency_code
                        ),
                    ],
                    limit=1,
                )
            )

            if not currency:
                raise ValueError(
                    'Moneda no encontrada'
                )

            vals['currency_id'] = (
                currency.id
            )

        if 'modalidad_pago_id' in data:

            payment_mode_id = (
                self._safe_int(
                    data.get(
                        'modalidad_pago_id'
                    ),
                    default=0,
                )
            )

            payment_mode = (
                request.env[
                    'copier.payment.mode'
                ]
                .sudo()
                .browse(payment_mode_id)
            )

            if not payment_mode.exists():
                raise ValueError(
                    'Modalidad de pago '
                    'no encontrada'
                )

            vals[
                'modalidad_pago_id'
            ] = payment_mode.id

        if 'duracion_contrato_id' in data:

            duration_id = self._safe_int(
                data.get(
                    'duracion_contrato_id'
                ),
                default=0,
            )

            duration = (
                request.env['copier.duracion']
                .sudo()
                .browse(duration_id)
            )

            if not duration.exists():
                raise ValueError(
                    'Duración no encontrada'
                )

            vals[
                'duracion_contrato_id'
            ] = duration.id

        if vals:
            quotation.write(vals)

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION UPDATED | '
            'id=%s | name=%s | email=%s',
            quotation.id,
            quotation.name,
            email,
        )

        return {
            'ok': True,
            'action': 'update_quotation',
            'message': (
                'Cotización actualizada correctamente'
            ),
            'quotation_id': quotation.id,
            'name': quotation.name,
        }

    # ============================================================
    # ELIMINAR COTIZACIÓN
    # ============================================================

    def _action_delete_quotation(
        self,
        data,
        email,
    ):

        quotation_id = self._safe_int(
            data.get('quotation_id'),
            default=0,
        )

        if not quotation_id:
            raise ValueError(
                'quotation_id es obligatorio'
            )

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .browse(quotation_id)
        )

        if not quotation.exists():
            raise ValueError(
                'Cotización no encontrada'
            )

        if quotation.estado != 'borrador':
            raise ValueError(
                'Solo se pueden eliminar '
                'cotizaciones en borrador'
            )

        name = quotation.name

        quotation.unlink()

        _logger.info(
            '[POWERAPPS API] '
            'QUOTATION DELETED | '
            'name=%s | email=%s',
            name,
            email,
        )

        return {
            'ok': True,
            'action': 'delete_quotation',
            'message': (
                'Cotización eliminada correctamente'
            ),
        }

    # ============================================================
    # ENVIAR COTIZACIÓN
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
            'action': 'send_quotation',
            'message': (
                'Cotización marcada como enviada'
            ),
            'state': quotation.estado,
        }

    # ============================================================
    # APROBAR COTIZACIÓN
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
            'action': 'approve_quotation',
            'message': (
                'Cotización aprobada correctamente'
            ),
            'state': quotation.estado,
        }

    # ============================================================
    # CONVERTIR COTIZACIÓN A CONTRATOS
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

        if quotation.estado != 'aprobado':
            raise ValueError(
                'La cotización debe estar aprobada '
                'antes de convertirla'
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
            'action': 'convert_quotation',
            'message': (
                'Cotización convertida a contratos'
            ),
            'state': quotation.estado,
        }

    # ============================================================
    # HELPER COTIZACIÓN
    # ============================================================

    def _get_quotation_from_data(
        self,
        data,
    ):

        quotation_id = self._safe_int(
            data.get('quotation_id'),
            default=0,
        )

        if not quotation_id:
            raise ValueError(
                'quotation_id es obligatorio'
            )

        quotation = (
            request.env['copier.quotation']
            .sudo()
            .browse(quotation_id)
        )

        if not quotation.exists():
            raise ValueError(
                'Cotización no encontrada'
            )

        return quotation