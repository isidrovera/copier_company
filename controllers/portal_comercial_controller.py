# -*- coding: utf-8 -*-
from datetime import timedelta

from werkzeug.exceptions import Forbidden, NotFound

from odoo import _, fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
    pager as portal_pager,
)


class PortalComercialController(CustomerPortal):
    PAGE_SIZE = 20

    def _executive(self):
        user = request.env.user
        if not user.has_group(
            'copier_company.group_portal_commercial_executive'
        ):
            raise Forbidden(_('No tiene acceso al portal comercial.'))
        return user.partner_id

    def _order(self, order_id):
        executive = self._executive()
        order = request.env['sale.order'].sudo().search([
            ('id', '=', order_id),
            ('portal_executive_id', '=', executive.id),
        ], limit=1)
        if not order:
            raise NotFound()
        return order

    def _invoice(self, invoice_id):
        executive = self._executive()
        invoice = request.env['account.move'].sudo().search([
            ('id', '=', invoice_id),
            ('portal_executive_id', '=', executive.id),
            ('move_type', '=', 'out_invoice'),
        ], limit=1)
        if not invoice:
            raise NotFound()
        return invoice

    def _editable_order(self, order_id):
        order = self._order(order_id)
        if order.state not in ('draft', 'sent'):
            raise Forbidden(_('Esta cotización ya no puede editarse.'))
        return order

    def _editable_invoice(self, invoice_id):
        invoice = self._invoice(invoice_id)
        if invoice.state != 'draft':
            raise Forbidden(_('Solo puede editar facturas en borrador.'))
        return invoice

    def _customers(self):
        return request.env['res.partner'].sudo().search([
            ('active', '=', True),
            ('customer_rank', '>', 0),
        ], order='name', limit=1000)

    def _products(self, query=''):
        domain = [
            ('active', '=', True),
            ('sale_ok', '=', True),
        ]
        if query:
            domain += [
                '|',
                ('name', 'ilike', query),
                ('default_code', 'ilike', query),
            ]
        return request.env['product.product'].sudo().search(
            domain, order='name', limit=100
        )

    def _pricelists(self, company):
        return request.env['product.pricelist'].sudo().search([
            ('active', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ], order='name')

    def _taxes(self, company):
        return request.env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'sale'),
            ('active', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ], order='sequence, name')

    def _chosen_taxes(self, company):
        """Solo acepta impuestos de venta existentes para la compañía."""
        submitted = request.httprequest.form.getlist('tax_ids')
        if any(not value.isdigit() for value in submitted):
            raise ValidationError(_('Impuestos inválidos.'))

        tax_ids = {int(value) for value in submitted}
        available = set(self._taxes(company).ids)

        if not tax_ids.issubset(available):
            raise Forbidden(_('Uno de los impuestos no está permitido.'))

        return list(tax_ids)

    def _number(self, value, label, minimum=0, maximum=None):
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValidationError(_('%s no es válido.') % label)

        if number < minimum or (
            maximum is not None and number > maximum
        ):
            raise ValidationError(_('%s está fuera del rango permitido.') % label)

        return number

    def _order_page(self, order, error=None, success=None):
        query = (request.params.get('q') or '').strip()
        validity_days = 15

        if order.validity_date:
            validity_days = max(
                1,
                (order.validity_date - fields.Date.today()).days,
            )

        return request.render(
            'copier_company.portal_commercial_order_detail',
            {
                'page_name': 'portal_commercial_order',
                'order': order,
                'customers': self._customers(),
                'pricelists': self._pricelists(order.company_id),
                'products': self._products(query),
                'product_query': query,
                'taxes': self._taxes(order.company_id),
                'validity_days': validity_days,
                'can_edit': order.state in ('draft', 'sent'),
                'can_invoice': (
                    order.state == 'sale'
                    and order.invoice_status == 'to invoice'
                ),
                'error': error,
                'success': success,
            },
        )

    def _invoice_page(self, invoice, error=None, success=None):
        query = (request.params.get('q') or '').strip()

        return request.render(
            'copier_company.portal_commercial_invoice_detail',
            {
                'page_name': 'portal_commercial_invoice',
                'invoice': invoice,
                'customers': self._customers(),
                'products': self._products(query),
                'product_query': query,
                'taxes': self._taxes(invoice.company_id),
                'currencies': request.env['res.currency'].sudo().search([
                    ('active', '=', True),
                ], order='name'),
                'can_edit': invoice.state == 'draft',
                'error': error,
                'success': success,
            },
        )

    @http.route(
        '/my/commercial',
        type='http',
        auth='user',
        website=True,
    )
    def commercial_home(self, **kwargs):
        executive = self._executive()
        orders = request.env['sale.order'].sudo()
        invoices = request.env['account.move'].sudo()

        owned_orders = [('portal_executive_id', '=', executive.id)]
        owned_invoices = [
            ('portal_executive_id', '=', executive.id),
            ('move_type', '=', 'out_invoice'),
        ]

        return request.render(
            'copier_company.portal_commercial_home',
            {
                'page_name': 'portal_commercial_home',
                'quotation_count': orders.search_count(
                    owned_orders + [('state', 'in', ('draft', 'sent'))]
                ),
                'order_count': orders.search_count(
                    owned_orders + [('state', '=', 'sale')]
                ),
                'invoice_count': invoices.search_count(owned_invoices),
                'draft_invoice_count': invoices.search_count(
                    owned_invoices + [('state', '=', 'draft')]
                ),
            },
        )

    @http.route(
        [
            '/my/commercial/orders',
            '/my/commercial/orders/page/<int:page>',
        ],
        type='http',
        auth='user',
        website=True,
    )
    def commercial_orders(self, page=1, **kwargs):
        executive = self._executive()
        model = request.env['sale.order'].sudo()
        domain = [('portal_executive_id', '=', executive.id)]

        pager = portal_pager(
            url='/my/commercial/orders',
            total=model.search_count(domain),
            page=page,
            step=self.PAGE_SIZE,
        )

        return request.render(
            'copier_company.portal_commercial_orders',
            {
                'page_name': 'portal_commercial_orders',
                'orders': model.search(
                    domain,
                    order='date_order desc, id desc',
                    limit=self.PAGE_SIZE,
                    offset=pager['offset'],
                ),
                'pager': pager,
            },
        )

    @http.route(
        '/my/commercial/orders/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def commercial_order_new(self, **post):
        executive = self._executive()
        company = request.env.company
        customers = self._customers()
        pricelists = self._pricelists(company)

        values = {
            'page_name': 'portal_commercial_order_new',
            'customers': customers,
            'pricelists': pricelists,
            'error': None,
        }

        if request.httprequest.method == 'GET':
            return request.render(
                'copier_company.portal_commercial_order_new',
                values,
            )

        try:
            customer_id = int(post.get('partner_id') or 0)
            pricelist_id = int(post.get('pricelist_id') or 0)
            days = int(post.get('validity_days') or 15)
        except (TypeError, ValueError):
            values['error'] = _('Seleccione cliente y lista de precios válidos.')
            return request.render(
                'copier_company.portal_commercial_order_new',
                values,
            )

        customer = customers.filtered(
            lambda partner: partner.id == customer_id
        )[:1]
        pricelist = pricelists.filtered(
            lambda item: item.id == pricelist_id
        )[:1]

        if not customer or not pricelist or not 1 <= days <= 365:
            values['error'] = _('Revise cliente, moneda y vigencia.')
            return request.render(
                'copier_company.portal_commercial_order_new',
                values,
            )

        order = request.env['sale.order'].sudo().create({
            'partner_id': customer.id,
            'company_id': company.id,
            'pricelist_id': pricelist.id,
            'validity_date': fields.Date.today() + timedelta(days=days),
            'portal_executive_id': executive.id,
            'origin': _('Portal Comercial - %s') % executive.display_name,
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>',
        type='http',
        auth='user',
        website=True,
    )
    def commercial_order_detail(self, order_id, **kwargs):
        return self._order_page(self._order(order_id))

    @http.route(
        '/my/commercial/orders/<int:order_id>/settings',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_settings(self, order_id, **post):
        order = self._editable_order(order_id)

        try:
            customer_id = int(post.get('partner_id') or 0)
            pricelist_id = int(post.get('pricelist_id') or 0)
            days = int(post.get('validity_days') or 15)
        except (TypeError, ValueError):
            return self._order_page(
                order, error=_('Datos de cotización inválidos.')
            )

        customer = self._customers().filtered(
            lambda partner: partner.id == customer_id
        )[:1]
        pricelist = self._pricelists(order.company_id).filtered(
            lambda item: item.id == pricelist_id
        )[:1]

        if not customer or not pricelist or not 1 <= days <= 365:
            return self._order_page(
                order, error=_('Revise cliente, moneda y vigencia.')
            )

        order.sudo().write({
            'partner_id': customer.id,
            'pricelist_id': pricelist.id,
            'validity_date': fields.Date.today() + timedelta(days=days),
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/line/add',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_line_add(self, order_id, **post):
        order = self._editable_order(order_id)

        try:
            product_id = int(post.get('product_id') or 0)
            quantity = self._number(
                post.get('quantity'), _('Cantidad'), minimum=0.01
            )
            discount = self._number(
                post.get('discount') or 0,
                _('Descuento'),
                maximum=100,
            )
            taxes = self._chosen_taxes(order.company_id)
        except (TypeError, ValueError, ValidationError) as error:
            return self._order_page(order, error=str(error))

        product = request.env['product.product'].sudo().search([
            ('id', '=', product_id),
            ('active', '=', True),
            ('sale_ok', '=', True),
        ], limit=1)

        if not product:
            return self._order_page(
                order, error=_('Seleccione un producto válido.')
            )

        if post.get('price_unit') not in (None, ''):
            try:
                price = self._number(
                    post['price_unit'], _('Precio'), minimum=0
                )
            except ValidationError as error:
                return self._order_page(order, error=str(error))
        else:
            price = product.lst_price

        description = (
            (post.get('description') or '').strip()
            or product.get_product_multiline_description_sale()
            or product.display_name
        )

        request.env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'product_uom_qty': quantity,
            'name': description,
            'price_unit': price,
            'discount': discount,
            'tax_ids': [(6, 0, taxes)],
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/line/<int:line_id>/update',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_line_update(self, order_id, line_id, **post):
        order = self._editable_order(order_id)
        line = order.order_line.filtered(
            lambda item: item.id == line_id and not item.display_type
        )[:1]

        if not line:
            raise NotFound()

        try:
            quantity = self._number(
                post.get('quantity'), _('Cantidad'), minimum=0.01
            )
            price = self._number(
                post.get('price_unit'), _('Precio')
            )
            discount = self._number(
                post.get('discount') or 0,
                _('Descuento'),
                maximum=100,
            )
            taxes = self._chosen_taxes(order.company_id)
        except ValidationError as error:
            return self._order_page(order, error=str(error))

        line.sudo().write({
            'product_uom_qty': quantity,
            'price_unit': price,
            'discount': discount,
            'name': (post.get('description') or '').strip() or line.name,
            'tax_ids': [(6, 0, taxes)],
        })

        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/line/<int:line_id>/delete',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_line_delete(self, order_id, line_id, **post):
        order = self._editable_order(order_id)
        line = order.order_line.filtered(
            lambda item: item.id == line_id and not item.display_type
        )[:1]

        if not line:
            raise NotFound()

        line.sudo().unlink()
        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/send',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_send(self, order_id, **post):
        order = self._editable_order(order_id)

        if not order.order_line:
            return self._order_page(
                order, error=_('Agregue productos antes de enviar.')
            )

        if not order.partner_id.email:
            return self._order_page(
                order, error=_('El cliente no tiene correo.')
            )

        template = request.env.ref(
            'sale.email_template_edi_sale',
            raise_if_not_found=False,
        )

        if not template:
            return self._order_page(
                order, error=_('No existe la plantilla de cotización.')
            )

        template.sudo().send_mail(
            order.id,
            force_send=True,
            email_values={'email_to': order.partner_id.email},
        )

        if order.state == 'draft':
            order.sudo().write({'state': 'sent'})

        return self._order_page(
            order, success=_('Cotización enviada.')
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/confirm',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_order_confirm(self, order_id, **post):
        order = self._editable_order(order_id)

        if not order.order_line:
            return self._order_page(
                order, error=_('Agregue productos antes de confirmar.')
            )

        order.sudo().action_confirm()
        return request.redirect(
            '/my/commercial/orders/%s' % order.id
        )

    @http.route(
        '/my/commercial/orders/<int:order_id>/invoice',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_create_invoice(self, order_id, **post):
        order = self._order(order_id)

        if order.state != 'sale':
            raise Forbidden(_('Primero confirme el pedido.'))

        try:
            invoices = order.sudo()._create_invoices()
        except UserError as error:
            return self._order_page(order, error=str(error))

        if not invoices:
            return self._order_page(
                order, error=_('No hay líneas pendientes de facturación.')
            )

        if any(invoice.state != 'draft' for invoice in invoices):
            raise Forbidden(
                _('La creación produjo una factura fuera de borrador.')
            )

        invoices.sudo().write({
            'portal_executive_id': self._executive().id,
        })

        return request.redirect(
            '/my/commercial/invoices/%s' % invoices[0].id
        )

    @http.route(
        [
            '/my/commercial/invoices',
            '/my/commercial/invoices/page/<int:page>',
        ],
        type='http',
        auth='user',
        website=True,
    )
    def commercial_invoices(self, page=1, **kwargs):
        executive = self._executive()
        model = request.env['account.move'].sudo()
        domain = [
            ('portal_executive_id', '=', executive.id),
            ('move_type', '=', 'out_invoice'),
        ]

        pager = portal_pager(
            url='/my/commercial/invoices',
            total=model.search_count(domain),
            page=page,
            step=self.PAGE_SIZE,
        )

        return request.render(
            'copier_company.portal_commercial_invoices',
            {
                'page_name': 'portal_commercial_invoices',
                'invoices': model.search(
                    domain,
                    order='id desc',
                    limit=self.PAGE_SIZE,
                    offset=pager['offset'],
                ),
                'pager': pager,
            },
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>',
        type='http',
        auth='user',
        website=True,
    )
    def commercial_invoice_detail(self, invoice_id, **kwargs):
        return self._invoice_page(self._invoice(invoice_id))

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/settings',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_invoice_settings(self, invoice_id, **post):
        invoice = self._editable_invoice(invoice_id)

        try:
            partner_id = int(post.get('partner_id') or 0)
            currency_id = int(post.get('currency_id') or 0)
        except (TypeError, ValueError):
            return self._invoice_page(
                invoice, error=_('Cliente o moneda inválidos.')
            )

        customer = self._customers().filtered(
            lambda item: item.id == partner_id
        )[:1]
        currency = request.env['res.currency'].sudo().search([
            ('id', '=', currency_id),
            ('active', '=', True),
        ], limit=1)

        if not customer or not currency:
            return self._invoice_page(
                invoice, error=_('Cliente o moneda inválidos.')
            )

        values = {
            'partner_id': customer.id,
            'currency_id': currency.id,
            'invoice_payment_term_id': False,
        }

        if post.get('invoice_date'):
            values['invoice_date'] = post['invoice_date']

        if post.get('invoice_date_due'):
            values['invoice_date_due'] = post['invoice_date_due']

        try:
            invoice.sudo().write(values)
        except (ValueError, ValidationError, UserError) as error:
            return self._invoice_page(invoice, error=str(error))

        return request.redirect(
            '/my/commercial/invoices/%s' % invoice.id
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/line/add',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_invoice_line_add(self, invoice_id, **post):
        invoice = self._editable_invoice(invoice_id)

        try:
            product_id = int(post.get('product_id') or 0)
            quantity = self._number(
                post.get('quantity'), _('Cantidad'), minimum=0.01
            )
            price = self._number(
                post.get('price_unit'), _('Precio')
            )
            discount = self._number(
                post.get('discount') or 0,
                _('Descuento'),
                maximum=100,
            )
            taxes = self._chosen_taxes(invoice.company_id)
        except (TypeError, ValueError, ValidationError) as error:
            return self._invoice_page(invoice, error=str(error))

        product = request.env['product.product'].sudo().search([
            ('id', '=', product_id),
            ('active', '=', True),
            ('sale_ok', '=', True),
        ], limit=1)

        if not product:
            return self._invoice_page(
                invoice, error=_('Producto inválido.')
            )

        invoice.sudo().write({
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'name': (
                    (post.get('description') or '').strip()
                    or product.display_name
                ),
                'quantity': quantity,
                'price_unit': price,
                'discount': discount,
                'tax_ids': [(6, 0, taxes)],
            })],
        })

        return request.redirect(
            '/my/commercial/invoices/%s' % invoice.id
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/line/<int:line_id>/update',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_invoice_line_update(
        self, invoice_id, line_id, **post
    ):
        invoice = self._editable_invoice(invoice_id)
        line = invoice.invoice_line_ids.filtered(
            lambda item: item.id == line_id and not item.display_type
        )[:1]

        if not line:
            raise NotFound()

        try:
            quantity = self._number(
                post.get('quantity'), _('Cantidad'), minimum=0.01
            )
            price = self._number(
                post.get('price_unit'), _('Precio')
            )
            discount = self._number(
                post.get('discount') or 0,
                _('Descuento'),
                maximum=100,
            )
            taxes = self._chosen_taxes(invoice.company_id)
        except ValidationError as error:
            return self._invoice_page(invoice, error=str(error))

        line.sudo().write({
            'name': (post.get('description') or '').strip() or line.name,
            'quantity': quantity,
            'price_unit': price,
            'discount': discount,
            'tax_ids': [(6, 0, taxes)],
        })

        return request.redirect(
            '/my/commercial/invoices/%s' % invoice.id
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/line/<int:line_id>/delete',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_invoice_line_delete(
        self, invoice_id, line_id, **post
    ):
        invoice = self._editable_invoice(invoice_id)
        line = invoice.invoice_line_ids.filtered(
            lambda item: item.id == line_id and not item.display_type
        )[:1]

        if not line:
            raise NotFound()

        line.sudo().unlink()
        return request.redirect(
            '/my/commercial/invoices/%s' % invoice.id
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/send',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def commercial_invoice_send(self, invoice_id, **post):
        invoice = self._invoice(invoice_id)

        if invoice.state != 'posted':
            raise Forbidden(
                _('Un usuario interno debe publicar primero la factura.')
            )

        if not invoice.partner_id.email:
            return self._invoice_page(
                invoice, error=_('El cliente no tiene correo.')
            )

        template = request.env.ref(
            'account.email_template_edi_invoice',
            raise_if_not_found=False,
        )

        if not template:
            return self._invoice_page(
                invoice, error=_('No existe la plantilla de factura.')
            )

        template.sudo().send_mail(
            invoice.id,
            force_send=True,
            email_values={'email_to': invoice.partner_id.email},
        )

        return self._invoice_page(
            invoice, success=_('Factura enviada.')
        )

    @http.route(
        '/my/commercial/invoices/<int:invoice_id>/pdf',
        type='http',
        auth='user',
        website=True,
    )
    def commercial_invoice_pdf(self, invoice_id, **kwargs):
        invoice = self._invoice(invoice_id)

        if invoice.state != 'posted':
            raise Forbidden(_('La factura aún no está publicada.'))

        report = request.env.ref(
            'account.account_invoices',
            raise_if_not_found=False,
        )
        if not report:
            raise NotFound()

        pdf, unused_format = (
            request.env['ir.actions.report']
            .sudo()
            ._render_qweb_pdf(report.report_name, [invoice.id])
        )

        filename = '%s.pdf' % (invoice.name or 'Factura')
        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
                (
                    'Content-Disposition',
                    http.content_disposition(filename),
                ),
            ],
        )