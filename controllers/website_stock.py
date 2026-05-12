# -*- coding: utf-8 -*-
import base64
import logging

from odoo import http, _
from odoo.http import request
from odoo.fields import Datetime
from odoo.osv import expression
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


# ============================================================
# PORTAL HOME - CONTADORES PARA TARJETAS DEL PORTAL
# ============================================================
class CustomerPortalStock(CustomerPortal):
    """
    Agrega contadores al portal principal para el modelo copier.stock.

    IMPORTANTE:
    - Esto NO pertenece a alquiler.
    - Esto pertenece al modelo separado copier.stock.
    - Usa res.partner.is_distributor para definir si el usuario ve más estados.
    """

    def _get_current_partner(self):
        return request.env.user.partner_id

    def _is_stock_distributor(self):
        """
        Determina si el usuario logueado es distribuidor.

        Campo existente en res.partner:
            is_distributor
        """
        partner = self._get_current_partner()
        return bool(partner.is_distributor)

    def _get_portal_stock_domain(self):
        """
        Dominio base para contar máquinas visibles en el portal.

        Cliente normal:
            Solo ve máquinas disponibles.

        Distribuidor:
            Puede ver máquinas disponibles, en importación y en descarga.
        """
        if self._is_stock_distributor():
            return [
                ('active', '=', True),
                ('state', 'in', ['importing', 'unloading', 'available']),
            ]

        return [
            ('active', '=', True),
            ('state', '=', 'available'),
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        Stock = request.env['copier.stock'].sudo()
        partner = self._get_current_partner()

        if 'stock_machine_count' in counters:
            values['stock_machine_count'] = Stock.search_count(
                self._get_portal_stock_domain()
            )

        if 'my_stock_machine_count' in counters:
            values['my_stock_machine_count'] = Stock.search_count([
                ('active', '=', True),
                ('reserved_by', '=', partner.id),
                ('state', 'in', ['reserved', 'pending_payment', 'sold']),
            ])

        return values


# ============================================================
# WEBSITE / PORTAL STOCK
# ============================================================
class WebsiteStock(http.Controller):
    """
    Controlador web para el modelo independiente copier.stock.

    Rutas principales:
        /stock-maquinas
        /stock-maquinas/page/<int:page>
        /stock-maquinas/<machine>
        /stock-maquinas/<machine>/reserve
        /stock-maquinas/<machine>/payment
        /stock-maquinas/<machine>/upload_payment
        /mis-maquinas
    """

    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def _get_current_partner(self):
        return request.env.user.partner_id

    def _is_stock_distributor(self):
        """
        Usa el campo real existente:
            res.partner.is_distributor
        """
        partner = self._get_current_partner()
        return bool(partner.is_distributor)

    def _get_visible_stock_domain(self):
        """
        Dominio base para listado de stock.

        Cliente normal:
            Solo ve máquinas disponibles.

        Distribuidor:
            Puede ver:
                - En Importación
                - En Descarga
                - Disponible

        No mostramos reservadas, pendientes de pago ni vendidas
        dentro del catálogo general.
        """
        if self._is_stock_distributor():
            return [
                ('active', '=', True),
                ('state', 'in', ['importing', 'unloading', 'available']),
            ]

        return [
            ('active', '=', True),
            ('state', '=', 'available'),
        ]

    def _can_access_machine(self, machine):
        """
        Valida si el usuario puede ver el detalle de una máquina.

        Cliente normal:
            - Puede ver disponibles.
            - Puede ver sus propias reservadas, pendientes o vendidas.

        Distribuidor:
            - Puede ver importación, descarga y disponibles.
            - También sus propias reservadas, pendientes o vendidas.
        """
        if not machine or not machine.exists() or not machine.active:
            return False

        partner = self._get_current_partner()
        is_owner = machine.reserved_by.id == partner.id
        is_distributor = self._is_stock_distributor()

        if is_owner and machine.state in ['reserved', 'pending_payment', 'sold']:
            return True

        if is_distributor and machine.state in ['importing', 'unloading', 'available']:
            return True

        if machine.state == 'available':
            return True

        return False

    def _can_manage_payment(self, machine):
        """
        Solo el usuario que reservó la máquina puede subir/ver su comprobante.
        """
        partner = self._get_current_partner()

        return bool(
            machine
            and machine.exists()
            and machine.reserved_by.id == partner.id
            and machine.state in ['reserved', 'pending_payment']
        )

    def _build_stock_domain_from_kwargs(self, kwargs):
        """
        Construye el dominio del listado usando filtros de la página.
        """
        domain = list(self._get_visible_stock_domain())

        # -----------------------------
        # Filtro por marca
        # -----------------------------
        marca_param = kwargs.get('marca') or ''
        try:
            selected_marca = int(marca_param) if marca_param else 0
        except ValueError:
            selected_marca = 0
            _logger.warning(
                "[PORTAL STOCK] Parámetro marca inválido: %s",
                marca_param,
            )

        if selected_marca:
            domain.append(('marca_id', '=', selected_marca))

        # -----------------------------
        # Filtro por tipo
        # -----------------------------
        selected_tipo = kwargs.get('tipo') or ''
        if selected_tipo in ['monocroma', 'color']:
            domain.append(('tipo', '=', selected_tipo))
        else:
            selected_tipo = ''

        # -----------------------------
        # Filtro por estado
        # -----------------------------
        selected_estado = kwargs.get('estado') or ''
        available_only = kwargs.get('available_only')

        allowed_states = ['available']
        if self._is_stock_distributor():
            allowed_states = ['importing', 'unloading', 'available']

        if selected_estado and selected_estado in allowed_states:
            domain.append(('state', '=', selected_estado))
        elif available_only == 'on':
            domain.append(('state', '=', 'available'))
        else:
            selected_estado = ''

        # -----------------------------
        # Filtro por búsqueda
        # Busca por referencia, serie y modelo.
        # -----------------------------
        search = (kwargs.get('search') or '').strip()

        if search:
            search_domain = expression.OR([
                [('name', 'ilike', search)],
                [('serie', 'ilike', search)],
                [('modelo_id.name', 'ilike', search)],
                [('marca_id.name', 'ilike', search)],
            ])
            domain = expression.AND([domain, search_domain])

        values = {
            'domain': domain,
            'selected_marca': selected_marca,
            'selected_tipo': selected_tipo,
            'selected_estado': selected_estado,
            'available_only': available_only,
            'search': search,
        }

        return values

    # ------------------------------------------------------------
    # LISTADO DE STOCK
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas', '/stock-maquinas/page/<int:page>'],
        type='http',
        auth='user',
        website=True
    )
    def list_stock(self, page=1, **kwargs):
        """
        Lista máquinas del modelo copier.stock.

        Cliente normal:
            Solo ve disponibles.

        Distribuidor:
            Ve disponibles, en importación y en descarga.

        Incluye:
            - filtros
            - búsqueda
            - paginación
            - variables para portal/breadcrumb
        """
        _logger.info(
            "[PORTAL STOCK] Ingreso a listado /stock-maquinas | user=%s | kwargs=%s",
            request.env.user.login,
            kwargs,
        )

        Stock = request.env['copier.stock'].sudo()
        Marca = request.env['marcas.maquinas'].sudo()

        filter_values = self._build_stock_domain_from_kwargs(kwargs)
        domain = filter_values['domain']

        marcas = Marca.search([], order='name asc')

        stock_count = Stock.search_count(domain)

        url_args = {
            'marca': filter_values['selected_marca'] or '',
            'tipo': filter_values['selected_tipo'] or '',
            'estado': filter_values['selected_estado'] or '',
            'available_only': filter_values['available_only'] or '',
            'search': filter_values['search'] or '',
        }

        pager = portal_pager(
            url='/stock-maquinas',
            total=stock_count,
            page=page,
            step=20,
            url_args=url_args,
        )

        machines = Stock.search(
            domain,
            limit=20,
            offset=pager['offset'],
            order='id desc',
        )

        _logger.info(
            "[PORTAL STOCK] Máquinas encontradas=%s | página=%s | distribuidor=%s | domain=%s",
            stock_count,
            page,
            self._is_stock_distributor(),
            domain,
        )

        return request.render('copier_company.copier_list', {
            # Datos principales
            'machines': machines,
            'marcas': marcas,
            'pager': pager,

            # Filtros
            'selected_marca': filter_values['selected_marca'],
            'selected_tipo': filter_values['selected_tipo'],
            'selected_estado': filter_values['selected_estado'],
            'available_only': filter_values['available_only'],
            'search': filter_values['search'],

            # Portal / UI
            'user': request.env.user,
            'page_name': 'stock_maquinas',
            'is_stock_distributor': self._is_stock_distributor(),
            'stock_count': stock_count,
        })

    # ------------------------------------------------------------
    # DETALLE DE MÁQUINA
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/<model("copier.stock"):machine>'],
        type='http',
        auth='user',
        website=True
    )
    def detail_stock(self, machine, **kwargs):
        """
        Ver detalle de una máquina específica.
        """
        if not self._can_access_machine(machine.sudo()):
            _logger.warning(
                "[PORTAL STOCK] Acceso denegado a detalle | user=%s | machine_id=%s",
                request.env.user.login,
                machine.id if machine else None,
            )
            return request.not_found()

        machine = machine.sudo()

        return request.render('copier_company.copier_detail', {
            'machine': machine,
            'user': request.env.user,
            'page_name': 'stock_maquinas',
            'is_stock_distributor': self._is_stock_distributor(),
        })

    # ------------------------------------------------------------
    # RESERVAR MÁQUINA
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/<model("copier.stock"):machine>/reserve'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True
    )
    def reserve_stock(self, machine, **post):
        """
        Reservar una máquina.

        Según el modelo copier.stock, action_reserve permite reservar:
            - available
            - importing
            - unloading

        Pero el cliente normal solo puede ver available.
        El distribuidor puede ver importing/unloading/available.
        """
        machine = machine.sudo()

        if not self._can_access_machine(machine):
            _logger.warning(
                "[PORTAL STOCK] Reserva denegada por acceso | user=%s | machine_id=%s",
                request.env.user.login,
                machine.id,
            )
            return request.not_found()

        if machine.state not in ['available', 'importing', 'unloading']:
            _logger.warning(
                "[PORTAL STOCK] Máquina no disponible para reserva | machine=%s | state=%s",
                machine.display_name,
                machine.state,
            )
            return request.render('copier_company.machine_not_available', {
                'machine': machine,
                'page_name': 'stock_maquinas',
            })

        try:
            machine.action_reserve()

            _logger.info(
                "[PORTAL STOCK] Máquina reservada | user=%s | partner=%s | machine=%s",
                request.env.user.login,
                request.env.user.partner_id.display_name,
                machine.display_name,
            )

            return request.redirect('/stock-maquinas/%s/payment' % machine.id)

        except Exception as e:
            _logger.exception(
                "[PORTAL STOCK] Error al reservar máquina %s: %s",
                machine.id,
                e,
            )
            return request.render('copier_company.machine_not_available', {
                'machine': machine,
                'error': _("No se pudo reservar la máquina. Intente nuevamente."),
                'page_name': 'stock_maquinas',
            })

    # ------------------------------------------------------------
    # IMAGEN PRINCIPAL
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/image/<int:machine_id>'],
        type='http',
        auth='user',
        website=True
    )
    def get_machine_image(self, machine_id, **kwargs):
        """
        Servir imagen principal de la máquina.
        """
        machine = request.env['copier.stock'].sudo().browse(machine_id)

        if not self._can_access_machine(machine):
            return request.not_found()

        if not machine.image:
            return request.not_found()

        try:
            image_data = base64.b64decode(machine.image)
        except Exception:
            _logger.exception(
                "[PORTAL STOCK] Error decodificando imagen machine_id=%s",
                machine_id,
            )
            return request.not_found()

        return request.make_response(
            image_data,
            headers=[
                ('Content-Type', 'image/png'),
                ('Cache-Control', 'public, max-age=86400'),
            ]
        )

    # ------------------------------------------------------------
    # COMPROBANTE DE PAGO
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/payment-proof/<int:machine_id>'],
        type='http',
        auth='user',
        website=True
    )
    def get_payment_proof(self, machine_id, **kwargs):
        """
        Servir comprobante de pago.

        Seguridad:
            Solo el partner que reservó la máquina puede ver su comprobante.
        """
        machine = request.env['copier.stock'].sudo().browse(machine_id)
        partner = self._get_current_partner()

        if not machine.exists() or not machine.payment_proof:
            return request.not_found()

        if machine.reserved_by.id != partner.id:
            _logger.warning(
                "[PORTAL STOCK] Intento de ver comprobante ajeno | user=%s | machine_id=%s",
                request.env.user.login,
                machine_id,
            )
            return request.not_found()

        try:
            file_data = base64.b64decode(machine.payment_proof)
        except Exception:
            _logger.exception(
                "[PORTAL STOCK] Error decodificando comprobante machine_id=%s",
                machine_id,
            )
            return request.not_found()

        filename = machine.payment_proof_filename or 'comprobante_pago'

        return request.make_response(
            file_data,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', 'inline; filename="%s"' % filename),
            ]
        )

    # ------------------------------------------------------------
    # PÁGINA PARA SUBIR COMPROBANTE
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/<model("copier.stock"):machine>/payment'],
        type='http',
        auth='user',
        website=True
    )
    def payment_page(self, machine, **kwargs):
        """
        Página para subir comprobante de pago.

        Solo el usuario que reservó la máquina puede acceder.
        """
        machine = machine.sudo()

        if not self._can_manage_payment(machine):
            _logger.warning(
                "[PORTAL STOCK] Acceso denegado a pago | user=%s | machine_id=%s",
                request.env.user.login,
                machine.id,
            )
            return request.redirect('/stock-maquinas')

        return request.render('copier_company.payment_upload', {
            'machine': machine,
            'page_name': 'stock_maquinas',
        })

    # ------------------------------------------------------------
    # PROCESAR COMPROBANTE DE PAGO
    # ------------------------------------------------------------
    @http.route(
        ['/stock-maquinas/<model("copier.stock"):machine>/upload_payment'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
        csrf=True
    )
    def upload_payment(self, machine, **post):
        """
        Procesar la subida del comprobante de pago.

        Mantengo tu lógica actual:
            - Guarda comprobante
            - Cambia a sold
            - Coloca sold_date
            - Marca payment_verified

        Nota:
            Si más adelante quieres que primero pase a pending_payment
            y gerencia valide manualmente, aquí se cambia state a pending_payment.
        """
        machine = machine.sudo()

        if not self._can_manage_payment(machine):
            _logger.warning(
                "[PORTAL STOCK] Upload pago denegado | user=%s | machine_id=%s",
                request.env.user.login,
                machine.id,
            )
            return request.redirect('/stock-maquinas')

        file = post.get('payment_proof')

        if not file:
            return request.render('copier_company.payment_upload', {
                'machine': machine,
                'error': _("Por favor suba un comprobante de pago."),
                'page_name': 'stock_maquinas',
            })

        try:
            data = file.read()
            filename = file.filename or 'comprobante_pago'

            if not data:
                return request.render('copier_company.payment_upload', {
                    'machine': machine,
                    'error': _("El archivo está vacío. Por favor suba un comprobante válido."),
                    'page_name': 'stock_maquinas',
                })

            machine.write({
                'payment_proof': base64.b64encode(data),
                'payment_proof_filename': filename,
                'state': 'sold',
                'sold_date': Datetime.now(),
                'payment_verified': True,
                'reservation_expiry_date': False,
            })

            _logger.info(
                "[PORTAL STOCK] Comprobante subido y venta confirmada | user=%s | machine=%s | file=%s",
                request.env.user.login,
                machine.display_name,
                filename,
            )

            return request.render('copier_company.payment_success', {
                'machine': machine,
                'page_name': 'stock_maquinas',
            })

        except Exception as e:
            _logger.exception(
                "[PORTAL STOCK] Error al procesar comprobante | machine_id=%s | error=%s",
                machine.id,
                e,
            )
            return request.render('copier_company.payment_upload', {
                'machine': machine,
                'error': _("Ocurrió un error al procesar su comprobante. Por favor intente nuevamente."),
                'page_name': 'stock_maquinas',
            })

    # ------------------------------------------------------------
    # MIS RESERVAS / COMPRAS
    # ------------------------------------------------------------
    @http.route(
        ['/mis-maquinas'],
        type='http',
        auth='user',
        website=True
    )
    def my_machines(self, **kwargs):
        """
        Ver máquinas reservadas, pendientes de pago o compradas por el usuario.

        Aunque la ruta se llame /mis-maquinas, esta vista pertenece
        al flujo independiente de copier.stock.
        """
        partner = self._get_current_partner()
        Stock = request.env['copier.stock'].sudo()

        reserved_machines = Stock.search([
            ('active', '=', True),
            ('reserved_by', '=', partner.id),
            ('state', 'in', ['reserved', 'pending_payment']),
        ], order='reserved_date desc, id desc')

        purchased_machines = Stock.search([
            ('active', '=', True),
            ('reserved_by', '=', partner.id),
            ('state', '=', 'sold'),
        ], order='sold_date desc, id desc')

        _logger.info(
            "[PORTAL STOCK] Mis máquinas | user=%s | reserved=%s | purchased=%s",
            request.env.user.login,
            len(reserved_machines),
            len(purchased_machines),
        )

        return request.render('copier_company.my_machines', {
            'reserved_machines': reserved_machines,
            'purchased_machines': purchased_machines,
            'page_name': 'mis_maquinas_stock',
            'is_stock_distributor': self._is_stock_distributor(),
        })