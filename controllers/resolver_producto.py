# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/resolver_producto.py

import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class ResolverProductoController(http.Controller):

    @http.route('/copier/resolver-producto/<string:token>', type='http', auth='public', methods=['GET'], csrf=False)
    def resolver_producto_page(self, token, **kwargs):
        """Página web para resolver producto desconocido."""
        pending = request.env['purchase.product.pending'].sudo().search(
            [('token', '=', token), ('state', '=', 'pending')], limit=1
        )
        if not pending:
            return request.render('copier_company.resolver_producto_invalid', {})

        payload = json.loads(pending.invoice_payload)
        return request.render('copier_company.resolver_producto_page', {
            'pending': pending,
            'payload': payload,
            'token': token,
        })

    @http.route('/copier/resolver-producto/buscar-productos', type='http', auth='public', methods=['GET'], csrf=False)
    def buscar_productos(self, q='', **kwargs):
        """Endpoint JSON para autocompletado de productos."""
        if not q or len(q) < 2:
            return Response(json.dumps([]), content_type='application/json')

        products = request.env['product.template'].sudo().search([
            ('name', 'ilike', q),
            ('purchase_ok', '=', True),
            ('active', '=', True),
        ], limit=15)

        result = [{'id': p.id, 'name': p.name} for p in products]
        return Response(json.dumps(result), content_type='application/json')

    @http.route('/copier/resolver-producto/confirmar', type='http', auth='public', methods=['POST'], csrf=False)
    def confirmar_resolucion(self, **kwargs):
        """Procesa la decisión del usuario: crear nuevo o usar existente."""
        token = kwargs.get('token', '')
        accion = kwargs.get('accion', '')  # 'new' o 'existing'
        product_id = kwargs.get('product_id', '')
        nuevo_nombre = kwargs.get('nuevo_nombre', '')

        pending = request.env['purchase.product.pending'].sudo().search(
            [('token', '=', token), ('state', '=', 'pending')], limit=1
        )
        if not pending:
            return request.render('copier_company.resolver_producto_invalid', {})

        data = json.loads(pending.invoice_payload)

        try:
            if accion == 'new':
                # Crear nuevo producto
                nombre = nuevo_nombre.strip() or data.get('description', 'Producto nuevo')
                _logger.info('[resolver] Creando nuevo producto: "%s"', nombre)
                template = request.env['product.template'].sudo().create({
                    'name': nombre,
                    'type': 'consu',
                    'purchase_ok': True,
                    'sale_ok': False,
                })
                Product = request.env['product.product'].sudo()
                product = Product.search([('product_tmpl_id', '=', template.id)], limit=1)
                resolution_type = 'new'
                _logger.info('[resolver] Producto CREADO: %s (ID: %s)', nombre, template.id)

            elif accion == 'existing':
                # Usar producto existente
                if not product_id:
                    return request.render('copier_company.resolver_producto_error', {
                        'error': 'Debe seleccionar un producto existente.',
                        'token': token,
                    })
                template = request.env['product.template'].sudo().browse(int(product_id))
                if not template.exists():
                    return request.render('copier_company.resolver_producto_error', {
                        'error': 'Producto no encontrado.',
                        'token': token,
                    })
                Product = request.env['product.product'].sudo()
                product = Product.search([('product_tmpl_id', '=', template.id)], limit=1)
                resolution_type = 'existing'
                _logger.info('[resolver] Usando producto existente: %s (ID: %s)', template.name, template.id)
            else:
                return request.render('copier_company.resolver_producto_error', {
                    'error': 'Acción no válida.',
                    'token': token,
                })

            # Guardar alias para futuras compras
            desc_lower = data.get('description', '').strip().lower()
            if desc_lower:
                existing_alias = request.env['product.name.alias'].sudo().search(
                    [('name', '=', desc_lower)], limit=1
                )
                if not existing_alias:
                    request.env['product.name.alias'].sudo().create({
                        'name': desc_lower,
                        'product_id': template.id,
                    })
                    _logger.info('[resolver] Alias GUARDADO: "%s" → %s', desc_lower, template.name)

            # Buscar datos necesarios para crear PO
            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([('vat', '=', data.get('supplier_ruc'))], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': data.get('supplier_name', 'Proveedor sin nombre'),
                    'vat': data.get('supplier_ruc'),
                    'supplier_rank': 1,
                    'country_id': request.env.ref('base.pe').id,
                })

            Currency = request.env['res.currency'].sudo()
            currency = Currency.search([('name', '=', data.get('currency', 'USD'))], limit=1)
            currency_id = currency.id if currency else False

            Tax = request.env['account.tax'].sudo()
            igv = Tax.search([
                ('amount', '=', 18),
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True),
            ], limit=1)
            tax_ids = [(4, igv.id)] if igv else []

            def parse_date(date_str):
                if not date_str:
                    return datetime.now()
                try:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d')
                except Exception:
                    return datetime.now()

            issue_date = parse_date(data.get('issue_date', ''))
            due_date = parse_date(data.get('due_date', ''))
            description = data.get('description', '')

            # Crear y confirmar PO
            api_controller = request.env['ir.http']  # solo para acceder al método
            PO = request.env['purchase.order'].sudo()
            po = PO.create({
                'partner_id': partner.id,
                'currency_id': currency_id or False,
                'date_order': issue_date,
                'date_planned': due_date,
                'partner_ref': data.get('invoice_id', ''),
                'note': 'Factura: %s | Vencimiento: %s' % (
                    data.get('invoice_id', ''), data.get('due_date', '')
                ),
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': description,
                    'product_qty': float(data.get('quantity', 1)),
                    'price_unit': float(data.get('unit_price', 0)),
                    'tax_ids': tax_ids,
                    'date_planned': due_date,
                })],
            })
            po.button_confirm()
            _logger.info('[resolver] PO CREADA y CONFIRMADA: %s (ID: %s)', po.name, po.id)

            # Adjuntar PDF y XML si existen
            Attachment = request.env['ir.attachment'].sudo()
            if data.get('pdf_base64'):
                Attachment.create({
                    'name': data.get('invoice_id', 'factura') + '.pdf',
                    'type': 'binary',
                    'datas': data.get('pdf_base64'),
                    'res_model': 'purchase.order',
                    'res_id': po.id,
                    'mimetype': 'application/pdf',
                })
            if data.get('xml_base64'):
                Attachment.create({
                    'name': data.get('invoice_id', 'factura') + '.xml',
                    'type': 'binary',
                    'datas': data.get('xml_base64'),
                    'res_model': 'purchase.order',
                    'res_id': po.id,
                    'mimetype': 'application/xml',
                })

            # Gestionar recepción
            tracking = product.product_tmpl_id.tracking
            if tracking == 'none':
                pickings = po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
                if pickings:
                    picking = pickings[0]
                    for move in picking.move_ids:
                        move.quantity = float(data.get('quantity', 1))
                    picking.with_context(skip_backorder=True, skip_immediate=True).button_validate()
                    _logger.info('[resolver] Recepción validada automáticamente: %s', picking.name)

            # Marcar pendiente como resuelto
            pending.write({
                'state': 'resolved',
                'resolved_product_id': template.id,
                'resolved_po_id': po.id,
                'resolution_type': resolution_type,
            })

            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            po_url = '%s/odoo/purchase/%d' % (base_url, po.id)

            return request.render('copier_company.resolver_producto_success', {
                'po_name': po.name,
                'po_url': po_url,
                'product_name': template.name,
                'invoice_id': data.get('invoice_id', ''),
                'resolution_type': resolution_type,
                'alias_saved': desc_lower,
            })

        except Exception as e:
            _logger.error('[resolver] ERROR: %s', str(e), exc_info=True)
            return request.render('copier_company.resolver_producto_error', {
                'error': str(e),
                'token': token,
            })