# -*- coding: utf-8 -*-
import logging

from werkzeug.exceptions import Forbidden, NotFound

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
    pager as portal_pager,
)


_logger = logging.getLogger(__name__)


class PortalComercialController(CustomerPortal):
    """
    Portal comercial exclusivo para ejecutivas portal.

    Permite:

    - Ver solamente sus cotizaciones y pedidos.
    - Crear cotizaciones.
    - Agregar, modificar y retirar productos.
    - Enviar cotizaciones.
    - Confirmar pedidos.
    - Crear facturas en borrador.
    - Ver facturas propias.
    - Descargar y enviar facturas publicadas.

    No permite:

    - Publicar facturas.
    - Registrar pagos.
    - Crear notas de crédito.
    - Acceder a documentos de otras ejecutivas.
    """

    PAGE_SIZE = 20

    # =========================================================
    # VALIDACIONES DE SEGURIDAD
    # =========================================================

    def _check_portal_executive(self):
        """Comprueba que el usuario tenga el grupo autorizado."""

        if not request.env.user.has_group(
            'copier_company.group_portal_commercial_executive'
        ):
            raise Forbidden(
                _('No tiene acceso al Portal Comercial.')
            )

    def _get_executive_partner(self):
        """Devuelve el contacto correspondiente al usuario portal."""

        self._check_portal_executive()
        return request.env.user.partner_id

    def _get_owned_order(self, order_id):
        """
        Obtiene un pedido solamente cuando pertenece a la ejecutiva.

        Aunque se utiliza sudo(), el documento se busca simultáneamente
        por ID y por portal_executive_id. Esto impide abrir pedidos
        ajenos cambiando el ID de la URL.
        """

        executive = self._get_executive_partner()

        order = request.env['sale.order'].sudo().search([
            ('id', '=', int(order_id)),
            ('portal_executive_id', '=', executive.id),
        ], limit=1)

        if not order:
            raise NotFound()

        return order

    def _get_owned_invoice(self, invoice_id):
        """Obtiene únicamente facturas pertenecientes a la ejecutiva."""

        executive = self._get_executive_partner()

        invoice = request.env['account.move'].sudo().search([
            ('id', '=', int(invoice_id)),
            ('portal_executive_id', '=', executive.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ], limit=1)

        if not invoice:
            raise NotFound()

        return invoice

    def _get_available_customers(self):
        """
        Clientes que se pueden utilizar desde el portal.

        No devuelve contactos privados ni registros archivados.
        """

        return request.env['res.partner'].sudo().search([
            ('active', '=', True),
            ('customer_rank', '>', 0),
            ('type', '!=', 'private'),
        ], order='name asc', limit=1000)

    def _get_available_products(self, query=''):
        """Busca productos vendibles por nombre o referencia interna."""

        domain = [
            ('active', '=', True),
            ('sale_ok', '=', True),
        ]

        query = (query or '').strip()

        if query:
            domain += [
                '|',
                ('name', 'ilike', query),
                ('default_code', 'ilike', query),
            ]

        return request.env['product.product'].sudo().search(
            domain,
            order='name asc',
            limit=80,
        )

    # =========================================================
    # PREPARACIÓN DEL DETALLE DEL PEDIDO
    # =========================================================

    def _render_order_detail(
        self,
        order,
        error=None,
        success=None,
    ):
        """Renderiza el detalle del pedido."""

        query = (request.params.get('q') or '').strip()

        values = {
            'page_name': 'portal_commercial_order',
            'order': order,
            'products': self._get_available_products(query),
            'product_query': query,
            'can_edit': order.state in ('draft', 'sent'),
            'can_invoice': (
                order.state == 'sale'
                and order.invoice_status == 'to invoice'
            ),
            'error': error,
            'success': success,
        }

        return request.render(
            'copier_company.portal_commercial_order_detail',
            values,
        )

    # =========================================================
    # INICIO DEL PORTAL COMERCIAL
    # =========================================================

    @http.route(
        '/my/commercial',
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_home(self, **kwargs):
        """Panel principal de la ejecutiva."""

        executive = self._get_executive_partner()

        SaleOrder = request.env['sale.order'].sudo()
        AccountMove = request.env['account.move'].sudo()

        order_domain = [
            ('portal_executive_id', '=', executive.id),
        ]

        invoice_domain = [
            ('portal_executive_id', '=', executive.id),
            ('move_type', '=', 'out_invoice'),
        ]

        values = {
            'page_name': 'portal_commercial_home',

            'quotation_count': SaleOrder.search_count(
                order_domain + [
                    ('state', 'in', ('draft', 'sent')),
                ]
            ),

            'order_count': SaleOrder.search_count(
                order_domain + [
                    ('state', '=', 'sale'),
                ]
            ),

            'invoice_count': AccountMove.search_count(
                invoice_domain
            ),

            'draft_invoice_count': AccountMove.search_count(
                invoice_domain + [
                    ('state', '=', 'draft'),
                ]
            ),
        }

        return request.render(
            'copier_company.portal_commercial_home',
            values,
        )

    # =========================================================
    # LISTADO DE COTIZACIONES Y PEDIDOS
    # =========================================================

    @http.route(
        [
            '/my/commercial/orders',
            '/my/commercial/orders/page/<int:page>',
        ],
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_orders(self, page=1, **kwargs):
        """Lista únicamente pedidos de la ejecutiva conectada."""

        executive = self._get_executive_partner()

        domain = [
            ('portal_executive_id', '=', executive.id),
        ]

        SaleOrder = request.env['sale.order'].sudo()

        total = SaleOrder.search_count(domain)

        pager = portal_pager(
            url='/my/commercial/orders',
            total=total,
            page=page,
            step=self.PAGE_SIZE,
        )

        orders = SaleOrder.search(
            domain,
            order='date_order desc, id desc',
            limit=self.PAGE_SIZE,
            offset=pager['offset'],
        )

        return request.render(
            'copier_company.portal_commercial_orders',
            {
                'page_name': 'portal_commercial_orders',
                'orders': orders,
                'pager': pager,
            },
        )

    # =========================================================
    # CREAR COTIZACIÓN
    # =========================================================

    @http.route(
        '/my/commercial/orders/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
    )
    def portal_commercial_order_new(self, **post):
        """Crea una cotización asignada a la ejecutiva portal."""

        executive = self._get_executive_partner()
        customers = self._get_available_customers()

        if request.httprequest.method == 'POST':
            try:
                partner_id = int(post.get('partner_id') or 0)
            except (TypeError, ValueError):
                partner_id = 0

            customer = customers.filtered(
                lambda partner: partner.id == partner_id
            )[:1]

            if not customer:
                return request.render(
                    'copier_company.portal_commercial_order_new',
                    {
                        'page_name': 'portal_commercial_order_new',
                        'customers': customers,
                        'error': _('Seleccione un cliente válido.'),
                    },
                )

            order = request.env['sale.order'].sudo().create({
                'partner_id': customer.id,
                'portal_executive_id': executive.id,
                'company_id': request.env.company.id,
                'origin': _(
                    'Portal Comercial - %s'
                ) % executive.display_name,
            })

            return request.redirect(
                '/my/commercial/orders/%s' % order.id
            )

        return request.render(
            'copier_company.portal_commercial_order_new',
            {
                'page_name': 'portal_commercial_order_new',
                'customers': customers,
            },
        )

    # =========================================================
    # DETALLE DEL PEDIDO
    # =========================================================

    @http.route(
        '/my/commercial/orders/<int:order_id>',
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_order_detail(
        self,
        order_id,
        **kwargs
    ):
        order = self._get_owned_order(order_id)
        return self._render_order_detail(order)

    # =========================================================
    # AGREGAR PRODUCTO
    # =========================================================

    @http.route(
        '/my/commercial/orders/<int:order_id>/line/add',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_line_add(
        self,
        order_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state not in ('draft', 'sent'):
            raise Forbidden(
                _('El pedido ya no puede editarse.')
            )

        try:
            product_id = int(post.get('product_id') or 0)
            quantity = float(post.get('quantity') or 0)
        except (TypeError, ValueError):
            return self._render_order_detail(
                order,
                error=_('Producto o cantidad inválidos.'),
            )

        product = request.env['product.product'].sudo().search([
            ('id', '=', product_id),
            ('active', '=', True),
            ('sale_ok', '=', True),
        ], limit=1)

        if not product:
            return self._render_order_detail(
                order,
                error=_('El producto seleccionado no es válido.'),
            )

        if quantity <= 0:
            return self._render_order_detail(
                order,
                error=_(
                    'La cantidad debe ser mayor que cero.'
                ),
            )

        description = (
            product.get_product_multiline_description_sale()
            or product.display_name
        )

        price_unit = order.pricelist_id._get_product_price(
            product,
            quantity,
            currency=order.currency_id,
            uom=product.uom_id,
            date=order.date_order,
        )

        request.env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'name': description,
            'price_unit': price_unit,
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    # =========================================================
    # ACTUALIZAR CANTIDAD
    # =========================================================

    @http.route(
        (
            '/my/commercial/orders/<int:order_id>'
            '/line/<int:line_id>/update'
        ),
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_line_update(
        self,
        order_id,
        line_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state not in ('draft', 'sent'):
            raise Forbidden(
                _('El pedido ya no puede editarse.')
            )

        line = order.order_line.filtered(
            lambda item: item.id == line_id
        )[:1]

        if not line or line.display_type:
            raise NotFound()

        try:
            quantity = float(
                post.get('quantity') or 0
            )
        except (TypeError, ValueError):
            quantity = 0

        if quantity <= 0:
            return self._render_order_detail(
                order,
                error=_(
                    'La cantidad debe ser mayor que cero.'
                ),
            )

        line.sudo().write({
            'product_uom_qty': quantity,
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    # =========================================================
    # ELIMINAR LÍNEA
    # =========================================================

    @http.route(
        (
            '/my/commercial/orders/<int:order_id>'
            '/line/<int:line_id>/delete'
        ),
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_line_delete(
        self,
        order_id,
        line_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state not in ('draft', 'sent'):
            raise Forbidden(
                _('El pedido ya no puede editarse.')
            )

        line = order.order_line.filtered(
            lambda item: item.id == line_id
        )[:1]

        if not line:
            raise NotFound()

        line.sudo().unlink()

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    # =========================================================
    # ENVIAR COTIZACIÓN
    # =========================================================

    @http.route(
        '/my/commercial/orders/<int:order_id>/send',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_order_send(
        self,
        order_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state not in ('draft', 'sent'):
            raise Forbidden(
                _('La cotización ya no puede enviarse.')
            )

        lines = order.order_line.filtered(
            lambda line: not line.display_type
        )

        if not lines:
            return self._render_order_detail(
                order,
                error=_(
                    'Debe agregar al menos un producto.'
                ),
            )

        if not order.partner_id.email:
            return self._render_order_detail(
                order,
                error=_(
                    'El cliente no tiene correo electrónico.'
                ),
            )

        template = request.env.ref(
            'sale.email_template_edi_sale',
            raise_if_not_found=False,
        )

        if not template:
            return self._render_order_detail(
                order,
                error=_(
                    'No se encontró la plantilla de cotización.'
                ),
            )

        template.sudo().send_mail(
            order.id,
            force_send=True,
            email_values={
                'email_to': order.partner_id.email,
            },
        )

        if order.state == 'draft':
            order.sudo().write({
                'state': 'sent',
            })

        return self._render_order_detail(
            order,
            success=_(
                'La cotización fue enviada correctamente.'
            ),
        )

    # =========================================================
    # CONFIRMAR PEDIDO
    # =========================================================

    @http.route(
        '/my/commercial/orders/<int:order_id>/confirm',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_order_confirm(
        self,
        order_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state not in ('draft', 'sent'):
            raise Forbidden(
                _('La cotización no puede confirmarse.')
            )

        lines = order.order_line.filtered(
            lambda line: not line.display_type
        )

        if not lines:
            return self._render_order_detail(
                order,
                error=_(
                    'Debe agregar al menos un producto.'
                ),
            )

        try:
            order.sudo().action_confirm()
        except (UserError, ValidationError) as error:
            return self._render_order_detail(
                order,
                error=str(error),
            )

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    # =========================================================
    # CREAR FACTURA EN BORRADOR
    # =========================================================

    @http.route(
        '/my/commercial/orders/<int:order_id>/invoice',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_create_invoice(
        self,
        order_id,
        **post
    ):
        order = self._get_owned_order(order_id)

        if order.state != 'sale':
            raise Forbidden(
                _('Primero debe confirmar el pedido.')
            )

        if order.invoice_status != 'to invoice':
            return self._render_order_detail(
                order,
                error=_(
                    'El pedido no tiene cantidades disponibles '
                    'para facturar.'
                ),
            )

        try:
            invoices = order.sudo()._create_invoices()
        except (UserError, ValidationError) as error:
            return self._render_order_detail(
                order,
                error=str(error),
            )

        if not invoices:
            return self._render_order_detail(
                order,
                error=_(
                    'No fue posible crear la factura.'
                ),
            )

        # La factura permanece en borrador.
        invoices.sudo().write({
            'portal_executive_id': (
                order.portal_executive_id.id
            ),
        })

        invoice = invoices[0]

        if invoice.state != 'draft':
            _logger.error(
                'La factura %s no fue creada en borrador.',
                invoice.id,
            )
            raise Forbidden(
                _(
                    'La factura no quedó en borrador. '
                    'Contacte al administrador.'
                )
            )

        return request.redirect(
            '/my/commercial/invoices/%s'
            % invoice.id
        )

    # =========================================================
    # LISTADO DE FACTURAS
    # =========================================================

    @http.route(
        [
            '/my/commercial/invoices',
            '/my/commercial/invoices/page/<int:page>',
        ],
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_invoices(
        self,
        page=1,
        **kwargs
    ):
        executive = self._get_executive_partner()

        domain = [
            ('portal_executive_id', '=', executive.id),
            (
                'move_type',
                'in',
                ('out_invoice', 'out_refund'),
            ),
        ]

        AccountMove = request.env[
            'account.move'
        ].sudo()

        total = AccountMove.search_count(domain)

        pager = portal_pager(
            url='/my/commercial/invoices',
            total=total,
            page=page,
            step=self.PAGE_SIZE,
        )

        invoices = AccountMove.search(
            domain,
            order='invoice_date desc, id desc',
            limit=self.PAGE_SIZE,
            offset=pager['offset'],
        )

        return request.render(
            'copier_company.portal_commercial_invoices',
            {
                'page_name': 'portal_commercial_invoices',
                'invoices': invoices,
                'pager': pager,
            },
        )

    # =========================================================
    # DETALLE DE FACTURA
    # =========================================================

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>',
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_invoice_detail(
        self,
        invoice_id,
        **kwargs
    ):
        invoice = self._get_owned_invoice(invoice_id)

        return request.render(
            'copier_company.portal_commercial_invoice_detail',
            {
                'page_name': 'portal_commercial_invoice',
                'invoice': invoice,
            },
        )

    # =========================================================
    # ENVIAR FACTURA PUBLICADA
    # =========================================================

    @http.route(
        (
            '/my/commercial/invoices/'
            '<int:invoice_id>/send'
        ),
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def portal_commercial_invoice_send(
        self,
        invoice_id,
        **post
    ):
        invoice = self._get_owned_invoice(invoice_id)

        if invoice.state != 'posted':
            raise Forbidden(
                _(
                    'Solamente puede enviar facturas '
                    'publicadas por un usuario interno.'
                )
            )

        if not invoice.partner_id.email:
            return request.render(
                (
                    'copier_company.'
                    'portal_commercial_invoice_detail'
                ),
                {
                    'page_name': (
                        'portal_commercial_invoice'
                    ),
                    'invoice': invoice,
                    'error': _(
                        'El cliente no tiene correo '
                        'electrónico.'
                    ),
                },
            )

        template = request.env.ref(
            'account.email_template_edi_invoice',
            raise_if_not_found=False,
        )

        if not template:
            raise UserError(
                _(
                    'No se encontró la plantilla '
                    'de factura.'
                )
            )

        template.sudo().send_mail(
            invoice.id,
            force_send=True,
            email_values={
                'email_to': invoice.partner_id.email,
            },
        )

        return request.render(
            (
                'copier_company.'
                'portal_commercial_invoice_detail'
            ),
            {
                'page_name': (
                    'portal_commercial_invoice'
                ),
                'invoice': invoice,
                'success': _(
                    'La factura fue enviada correctamente.'
                ),
            },
        )

    # =========================================================
    # DESCARGAR FACTURA PUBLICADA
    # =========================================================

    @http.route(
        (
            '/my/commercial/invoices/'
            '<int:invoice_id>/pdf'
        ),
        type='http',
        auth='user',
        website=True,
    )
    def portal_commercial_invoice_pdf(
        self,
        invoice_id,
        **kwargs
    ):
        invoice = self._get_owned_invoice(invoice_id)

        if invoice.state != 'posted':
            raise Forbidden(
                _(
                    'La factura todavía no ha sido '
                    'publicada.'
                )
            )

        report = request.env.ref(
            'account.account_invoices',
            raise_if_not_found=False,
        )

        if not report:
            raise NotFound()

        pdf_content, _ = report.sudo().render_qweb_pdf(
            [invoice.id]
        )

        filename = '%s.pdf' % (
            invoice.name or 'Factura'
        )

        return request.make_response(
            pdf_content,
            headers=[
                (
                    'Content-Type',
                    'application/pdf',
                ),
                (
                    'Content-Length',
                    len(pdf_content),
                ),
                (
                    'Content-Disposition',
                    content_disposition(filename),
                ),
            ],
        )