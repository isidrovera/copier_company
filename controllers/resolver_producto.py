# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/resolver_producto.py

import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class ResolverProductoController(http.Controller):

    # =========================================================================
    # PÁGINA PRINCIPAL: muestra TODAS las líneas pendientes del grupo
    # =========================================================================
    @http.route('/copier/resolver-producto/<string:token>', type='http', auth='public', methods=['GET'], csrf=False)
    def resolver_producto_page(self, token, **kwargs):
        """
        Muestra todas las líneas pendientes de la factura.
        El `token` recibido puede ser:
          - un group_token (preferido, agrupa todas las líneas)
          - un token individual (compatibilidad: se redirige al group)
        """
        _logger.info('[resolver] GET resolver-producto token=%s', token)

        Pending = request.env['purchase.product.pending'].sudo()

        # Buscar primero por group_token
        pendings = Pending.search([('group_token', '=', token)], order='line_index asc')

        if not pendings:
            # Fallback: buscar por token individual y redirigir al grupo
            individual = Pending.search([('token', '=', token)], limit=1)
            if individual:
                pendings = Pending.search(
                    [('group_token', '=', individual.group_token)],
                    order='line_index asc'
                )
                _logger.info('[resolver] Token individual → redirigiendo a group_token=%s',
                             individual.group_token)

        if not pendings:
            _logger.warning('[resolver] No se encontraron pendientes para token=%s', token)
            return request.render('copier_company.resolver_producto_invalid', {})

        # Si todos ya están resueltos
        pending_open = pendings.filtered(lambda p: p.state == 'pending')
        if not pending_open:
            _logger.info('[resolver] Todos los pendientes del grupo ya están resueltos')
            po = pendings[0].resolved_po_id
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return request.render('copier_company.resolver_producto_already_resolved', {
                'pendings': pendings,
                'po_name': po.name if po else '',
                'po_url': ('%s/odoo/purchase/%d' % (base_url, po.id)) if po else '',
                'invoice_id': pendings[0].invoice_id,
            })

        payload = json.loads(pendings[0].invoice_payload)
        group_token = pendings[0].group_token

        _logger.info('[resolver] Renderizando %s pendientes (%s abiertos) para factura %s',
                     len(pendings), len(pending_open), pendings[0].invoice_id)

        return request.render('copier_company.resolver_producto_page', {
            'pendings': pendings,
            'pending_open': pending_open,
            'payload': payload,
            'group_token': group_token,
            'invoice_id': pendings[0].invoice_id,
            'supplier_name': pendings[0].supplier_name,
            'supplier_ruc': pendings[0].supplier_ruc,
            'currency_name': pendings[0].currency_name,
            'lines_total': len(payload.get('lines', [])),
            'lines_pending': len(pending_open),
            'lines_resolved': len(payload.get('lines', [])) - len(pending_open),
        })

    # =========================================================================
    # AUTOCOMPLETADO de productos
    # =========================================================================
    @http.route('/copier/resolver-producto/buscar-productos', type='http', auth='public', methods=['GET'], csrf=False)
    def buscar_productos(self, q='', **kwargs):
        """JSON con productos que coinciden con el query."""
        if not q or len(q) < 2:
            return Response(json.dumps([]), content_type='application/json')

        products = request.env['product.template'].sudo().search([
            ('name', 'ilike', q),
            ('purchase_ok', '=', True),
            ('active', '=', True),
        ], limit=15)

        result = [{
            'id': p.id,
            'name': p.name,
            'default_code': p.default_code or '',
        } for p in products]
        return Response(json.dumps(result), content_type='application/json')

    # =========================================================================
    # CONFIRMAR: procesa TODAS las decisiones del usuario y crea la PO completa
    # =========================================================================
    @http.route('/copier/resolver-producto/confirmar', type='http', auth='public', methods=['POST'], csrf=False)
    def confirmar_resolucion(self, **kwargs):
        """
        Procesa la decisión del usuario para CADA línea pendiente.
        Espera en kwargs:
          - group_token
          - accion_<token>: 'new' | 'existing'  (uno por cada pendiente)
          - product_id_<token>: ID si accion=existing
          - nuevo_nombre_<token>: nombre si accion=new
        Cuando todas las líneas se resuelven, crea la PO completa.
        """
        _logger.info('=' * 70)
        _logger.info('[resolver] === POST confirmar ===')
        _logger.info('[resolver] kwargs keys: %s', list(kwargs.keys()))

        group_token = kwargs.get('group_token', '')
        if not group_token:
            _logger.error('[resolver] Falta group_token')
            return request.render('copier_company.resolver_producto_error', {
                'error': 'Falta el token de grupo.',
                'token': '',
            })

        Pending = request.env['purchase.product.pending'].sudo()
        all_pendings = Pending.search(
            [('group_token', '=', group_token)],
            order='line_index asc'
        )
        if not all_pendings:
            _logger.error('[resolver] No se encontró el grupo: %s', group_token)
            return request.render('copier_company.resolver_producto_invalid', {})

        pending_open = all_pendings.filtered(lambda p: p.state == 'pending')
        if not pending_open:
            _logger.warning('[resolver] Todos los pendientes ya estaban resueltos')
            return request.render('copier_company.resolver_producto_invalid', {})

        payload = json.loads(all_pendings[0].invoice_payload)

        try:
            # ===== 1. Procesar cada línea pendiente =====
            # resolved_map: line_index → product.product
            resolved_map = {}

            for pending in pending_open:
                token = pending.token
                accion = kwargs.get('accion_%s' % token, '').strip()
                _logger.info('[resolver] Pendiente token=%s, line_index=%s, accion=%s',
                             token, pending.line_index, accion)

                if accion == 'new':
                    nombre = (kwargs.get('nuevo_nombre_%s' % token, '') or '').strip()
                    if not nombre:
                        nombre = pending.description_proveedor or 'Producto sin nombre'
                    _logger.info('[resolver]   → Crear NUEVO: "%s"', nombre)

                    template = request.env['product.template'].sudo().create({
                        'name': nombre,
                        'type': 'consu',
                        'purchase_ok': True,
                        'sale_ok': False,
                    })
                    product = request.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', template.id)], limit=1
                    )
                    pending.write({
                        'state': 'resolved',
                        'resolved_product_id': template.id,
                        'resolution_type': 'new',
                    })
                    _logger.info('[resolver]   ✓ Producto creado: %s (template=%s, product=%s)',
                                 nombre, template.id, product.id)

                elif accion == 'existing':
                    product_id_str = kwargs.get('product_id_%s' % token, '')
                    if not product_id_str:
                        raise ValueError('Falta product_id para línea "%s".' % pending.description_proveedor)

                    template = request.env['product.template'].sudo().browse(int(product_id_str))
                    if not template.exists():
                        raise ValueError('Producto no encontrado para "%s".' % pending.description_proveedor)

                    product = request.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', template.id)], limit=1
                    )
                    pending.write({
                        'state': 'resolved',
                        'resolved_product_id': template.id,
                        'resolution_type': 'existing',
                    })
                    _logger.info('[resolver]   ✓ Producto existente: %s (template=%s, product=%s)',
                                 template.name, template.id, product.id)
                else:
                    raise ValueError('Acción inválida para línea "%s".' % pending.description_proveedor)

                # Guardar alias para futuras compras
                desc_lower = (pending.description_proveedor or '').strip().lower()
                if desc_lower:
                    Alias = request.env['product.name.alias'].sudo()
                    existing_alias = Alias.search([('name', '=', desc_lower)], limit=1)
                    if not existing_alias:
                        Alias.create({
                            'name': desc_lower,
                            'product_id': template.id,
                        })
                        _logger.info('[resolver]   Alias guardado: "%s" → %s',
                                     desc_lower, template.name)
                    else:
                        _logger.info('[resolver]   Alias ya existía: "%s"', desc_lower)

                resolved_map[pending.line_index] = product

            # ===== 2. Reconstruir todas las líneas (resueltas + recién resueltas) =====
            _logger.info('[resolver] Reconstruyendo líneas completas para PO...')
            all_lines = payload.get('lines', [])

            # Buscar productos para las líneas que NO estaban en pendientes
            # (es decir, las que el controlador original ya pudo resolver)
            api_helper = request.env['ir.http']  # placeholder; usamos el helper local
            from odoo.addons.copier_company.controllers.purchase_api import PurchaseApiController
            api = PurchaseApiController()

            resolved_lines = []
            for idx, line in enumerate(all_lines):
                if idx in resolved_map:
                    product = resolved_map[idx]
                    _logger.info('[resolver]   Línea %s: producto recién resuelto → %s',
                                 idx, product.name)
                else:
                    desc = (line.get('description') or '').strip()
                    product = api._buscar_producto(desc)
                    if not product:
                        # Edge case: una línea que era conocida ahora no se encuentra
                        # (alguien borró el producto entre la creación del pendiente y ahora)
                        raise ValueError(
                            'La línea "%s" no se puede resolver. ¿Se borró el producto?' % desc
                        )
                    _logger.info('[resolver]   Línea %s: producto pre-existente → %s',
                                 idx, product.name)

                resolved_lines.append({'product': product, 'line_data': line})

            # ===== 3. Crear PO completa =====
            _logger.info('[resolver] Creando PO con %s líneas...', len(resolved_lines))

            partner = api._buscar_o_crear_proveedor(payload)
            currency = api._buscar_moneda(payload.get('currency', 'USD'))
            currency_id = currency.id if currency else False
            tax_ids = api._buscar_tax_ids()
            issue_date = api._parse_date(payload.get('issue_date', ''))
            due_date = api._parse_date(payload.get('due_date', '')) or issue_date

            result = api._crear_y_confirmar_po(
                payload, partner, currency_id, resolved_lines, tax_ids,
                issue_date, due_date,
            )

            po_id = result.get('po_id')
            po_name = result.get('po_name')
            _logger.info('[resolver] PO creada: %s (ID: %s)', po_name, po_id)

            # ===== 4. Asignar PO a TODOS los pendientes del grupo =====
            all_pendings.write({'resolved_po_id': po_id})
            _logger.info('[resolver] PO asignada a %s pendientes del grupo', len(all_pendings))

            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            po_url = '%s/odoo/purchase/%d' % (base_url, po_id)

            _logger.info('[resolver] === Fin exitoso: %s ===', po_name)
            _logger.info('=' * 70)

            return request.render('copier_company.resolver_producto_success', {
                'po_name': po_name,
                'po_url': po_url,
                'invoice_id': payload.get('invoice_id', ''),
                'lines_count': len(resolved_lines),
                'pendings_resolved': len(pending_open),
            })

        except Exception as e:
            _logger.error('[resolver] === ERROR: %s ===', str(e), exc_info=True)
            _logger.info('=' * 70)
            return request.render('copier_company.resolver_producto_error', {
                'error': str(e),
                'token': group_token,
            })