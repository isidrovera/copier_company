# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/purchase_api.py

import json
import logging
import uuid
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

NOTIFICATION_EMAIL = 'isidro@copiercompanysac.com'


class PurchaseApiController(http.Controller):

    # =========================================================================
    # ENDPOINT PRINCIPAL
    # =========================================================================
    @http.route('/copier/crear_compra', type='jsonrpc', auth='bearer', methods=['POST'], csrf=False)
    def crear_compra(self, **kwargs):
        _logger.info('=' * 70)
        _logger.info('[crear_compra] === Inicio de request ===')
        try:
            raw = request.get_json_data()
            if isinstance(raw, dict) and 'params' in raw:
                data = raw['params']
            else:
                data = raw

            invoice_id = data.get('invoice_id', '')
            supplier_ruc = data.get('supplier_ruc', '')
            currency_name = data.get('currency', 'USD')

            _logger.info('[crear_compra] Factura: %s | RUC: %s | Moneda: %s',
                         invoice_id, supplier_ruc, currency_name)

            # ---------- Normalizar líneas ----------
            lines_data = data.get('lines') or []
            if not lines_data and data.get('description'):
                _logger.info('[crear_compra] Payload sin "lines", usando campos sueltos (compat)')
                lines_data = [{
                    'description': data.get('description', ''),
                    'quantity': data.get('quantity', 1),
                    'unit_price': data.get('unit_price', 0),
                    'unit_price_with_igv': data.get('unit_price_with_igv', 0),
                    'line_amount': data.get('line_amount', 0),
                    'tax_amount': data.get('tax_amount', 0),
                }]

            _logger.info('[crear_compra] Total líneas a procesar: %s', len(lines_data))
            for idx, ln in enumerate(lines_data, start=1):
                _logger.info('[crear_compra]   Línea %s: "%s" | qty=%s | price=%s',
                             idx, (ln.get('description') or '')[:50],
                             ln.get('quantity'), ln.get('unit_price'))

            if not lines_data:
                _logger.error('[crear_compra] Payload sin líneas. Abortando.')
                return {'success': False, 'error': 'Payload sin líneas de factura.'}

            # ---------- Idempotencia 1: PO ya existe para esta factura ----------
            existing_po = request.env['purchase.order'].sudo().search(
                [('partner_ref', '=', invoice_id)], limit=1
            )
            if existing_po:
                _logger.warning('[crear_compra] Factura %s ya tiene PO: %s — abortando duplicado',
                                invoice_id, existing_po.name)
                return {
                    'success': True,
                    'duplicate': True,
                    'po_id': existing_po.id,
                    'po_name': existing_po.name,
                    'po_url': '/odoo/purchase/%d' % existing_po.id,
                    'message': 'La factura ya fue procesada previamente.',
                }

            # ---------- Idempotencia 2: ya hay pendientes abiertos para esta factura ----------
            existing_pending = request.env['purchase.product.pending'].sudo().search([
                ('invoice_id', '=', invoice_id),
                ('state', '=', 'pending'),
            ])
            if existing_pending:
                group_token = existing_pending[0].group_token
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                resolver_url = '%s/copier/resolver-producto/%s' % (base_url, group_token)
                _logger.warning('[crear_compra] Factura %s ya tiene %s pendientes (group_token=%s) — abortando',
                                invoice_id, len(existing_pending), group_token)
                return {
                    'success': False,
                    'pending': True,
                    'duplicate_pending': True,
                    'group_token': group_token,
                    'resolver_url': resolver_url,
                    'pending_count': len(existing_pending),
                    'message': 'La factura ya tiene productos pendientes de resolución.',
                }

            # ---------- 1. Proveedor ----------
            partner = self._buscar_o_crear_proveedor(data)

            # ---------- 2. Moneda ----------
            currency = self._buscar_moneda(currency_name)
            currency_id = currency.id if currency else False

            # ---------- 3. Resolver cada línea ----------
            resolved_lines = []   # [{'product': product_obj, 'line_data': {...}}, ...]
            unknown_lines = []    # [{'line_data': {...}, 'index': N}, ...]

            for idx, line in enumerate(lines_data):
                line_desc = (line.get('description') or '').strip()
                _logger.info('[crear_compra] --- Resolviendo línea %s/%s: "%s" ---',
                             idx + 1, len(lines_data), line_desc[:60])

                product = self._buscar_producto(line_desc)

                if product:
                    _logger.info('[crear_compra]   ✓ Producto resuelto: %s (ID: %s)',
                                 product.name, product.id)
                    resolved_lines.append({'product': product, 'line_data': line})
                else:
                    _logger.warning('[crear_compra]   ✗ Producto DESCONOCIDO: "%s"', line_desc[:60])
                    unknown_lines.append({'line_data': line, 'index': idx})

            _logger.info('[crear_compra] Resumen — resueltas: %s | desconocidas: %s',
                         len(resolved_lines), len(unknown_lines))

            # ---------- 4. Si hay desconocidos: crear pendientes y NO crear PO ----------
            if unknown_lines:
                _logger.info('[crear_compra] Hay %s desconocidos. PO en espera hasta resolver todos.',
                             len(unknown_lines))

                group_token = str(uuid.uuid4())
                _logger.info('[crear_compra] group_token generado: %s', group_token)

                pendings = []
                for item in unknown_lines:
                    pending = self._crear_pendiente(data, item['line_data'], item['index'], group_token)
                    pendings.append(pending)

                self._enviar_notificacion_grupo(data, pendings, resolved_lines, group_token)

                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                resolver_url = '%s/copier/resolver-producto/%s' % (base_url, group_token)

                return {
                    'success': False,
                    'pending': True,
                    'group_token': group_token,
                    'resolver_url': resolver_url,
                    'pending_count': len(pendings),
                    'resolved_count': len(resolved_lines),
                    'unknown_count': len(unknown_lines),
                    'invoice_id': invoice_id,
                    'message': '%s producto(s) desconocido(s). PO no se creó hasta resolver todos.' % len(pendings),
                }

            # ---------- 5. Todas las líneas resueltas → crear PO completa ----------
            _logger.info('[crear_compra] Todas las líneas resueltas. Creando PO...')

            issue_date = self._parse_date(data.get('issue_date', ''))
            due_date = self._parse_date(data.get('due_date', '')) or issue_date
            tax_ids = self._buscar_tax_ids()

            result = self._crear_y_confirmar_po(
                data, partner, currency_id, resolved_lines, tax_ids,
                issue_date, due_date,
            )
            _logger.info('[crear_compra] === Fin exitoso: %s ===', result.get('po_name'))
            _logger.info('=' * 70)
            return result

        except Exception as e:
            _logger.error('[crear_compra] === ERROR: %s ===', str(e), exc_info=True)
            _logger.info('=' * 70)
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # HELPERS DE BÚSQUEDA / CREACIÓN
    # =========================================================================
    def _buscar_o_crear_proveedor(self, data):
        ruc = data.get('supplier_ruc', '')
        Partner = request.env['res.partner'].sudo()
        partner = Partner.search([('vat', '=', ruc)], limit=1)
        if not partner:
            partner = Partner.create({
                'name': data.get('supplier_name', 'Proveedor sin nombre'),
                'vat': ruc,
                'supplier_rank': 1,
                'country_id': request.env.ref('base.pe').id,
            })
            _logger.info('[crear_compra]   Proveedor CREADO: %s (ID: %s, RUC: %s)',
                         partner.name, partner.id, partner.vat)
        else:
            _logger.info('[crear_compra]   Proveedor ENCONTRADO: %s (ID: %s)',
                         partner.name, partner.id)
        return partner

    def _buscar_moneda(self, currency_name):
        Currency = request.env['res.currency'].sudo()
        currency = Currency.search([('name', '=', currency_name)], limit=1)
        if currency:
            _logger.info('[crear_compra]   Moneda: %s (ID: %s)', currency.name, currency.id)
        else:
            _logger.warning('[crear_compra]   Moneda NO encontrada: %s', currency_name)
        return currency

    def _buscar_producto(self, description):
        if not description:
            return False

        Product = request.env['product.product'].sudo()
        product = Product.search([('name', '=', description)], limit=1)
        if product:
            return product

        # Búsqueda por alias
        desc_lower = description.lower()
        alias = request.env['product.name.alias'].sudo().search(
            [('name', '=', desc_lower)], limit=1
        )
        if alias:
            product = Product.search(
                [('product_tmpl_id', '=', alias.product_id.id)], limit=1
            )
            if product:
                _logger.info('[crear_compra]   Encontrado por alias: "%s" → %s',
                             desc_lower, product.name)
                return product

        return False

    def _buscar_tax_ids(self):
        Tax = request.env['account.tax'].sudo()
        igv = Tax.search([
            ('amount', '=', 18),
            ('type_tax_use', '=', 'purchase'),
            ('active', '=', True),
        ], limit=1)
        if igv:
            _logger.info('[crear_compra]   IGV: %s (ID: %s)', igv.name, igv.id)
        else:
            _logger.warning('[crear_compra]   IGV 18%% NO encontrado')
        return [(4, igv.id)] if igv else []

    def _parse_date(self, date_str):
        if not date_str:
            return datetime.now()
        try:
            return datetime.strptime(date_str.strip(), '%Y-%m-%d')
        except Exception:
            return datetime.now()

    # =========================================================================
    # PURCHASE ORDER (con N líneas)
    # =========================================================================
    def _crear_y_confirmar_po(self, data, partner, currency_id, resolved_lines,
                              tax_ids, date_order, date_planned):
        """Crea la PO con TODAS las líneas resueltas, la confirma y gestiona recepción."""
        _logger.info('[crear_compra] _crear_y_confirmar_po — %s líneas', len(resolved_lines))

        order_lines_vals = []
        for idx, item in enumerate(resolved_lines, start=1):
            product = item['product']
            line = item['line_data']
            qty = float(line.get('quantity', 1))
            price = float(line.get('unit_price', 0))
            desc = line.get('description', '')

            order_lines_vals.append((0, 0, {
                'product_id': product.id,
                'name': desc,
                'product_qty': qty,
                'price_unit': price,
                'tax_ids': tax_ids,
                'date_planned': date_planned,
            }))
            _logger.info('[crear_compra]   Línea PO %s: %s | qty=%s | price=%s',
                         idx, product.name, qty, price)

        PO = request.env['purchase.order'].sudo()
        po = PO.create({
            'partner_id': partner.id,
            'currency_id': currency_id or False,
            'date_order': date_order,
            'date_planned': date_planned,
            'partner_ref': data.get('invoice_id', ''),
            'note': 'Factura: %s | Vencimiento: %s' % (
                data.get('invoice_id', ''), data.get('due_date', '')
            ),
            'order_line': order_lines_vals,
        })
        _logger.info('[crear_compra] PO CREADA: %s (ID: %s) con %s líneas',
                     po.name, po.id, len(order_lines_vals))

        po.button_confirm()
        _logger.info('[crear_compra] PO CONFIRMADA: %s — estado: %s', po.name, po.state)

        # Adjuntar PDF y XML
        self._adjuntar_archivos(po, data)

        # Validar recepción de líneas sin tracking
        reception_state = self._validar_recepciones(po, resolved_lines)

        return {
            'success': True,
            'po_id': po.id,
            'po_name': po.name,
            'po_state': po.state,
            'po_url': '/odoo/purchase/%d' % po.id,
            'partner_id': partner.id,
            'partner_name': partner.name,
            'invoice_id': data.get('invoice_id'),
            'lines_count': len(resolved_lines),
            'reception_state': reception_state,
        }

    def _adjuntar_archivos(self, po, data):
        Attachment = request.env['ir.attachment'].sudo()
        invoice_id = data.get('invoice_id', 'factura')

        if data.get('pdf_base64'):
            att = Attachment.create({
                'name': invoice_id + '.pdf',
                'type': 'binary',
                'datas': data.get('pdf_base64'),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'mimetype': 'application/pdf',
            })
            _logger.info('[crear_compra]   PDF adjuntado (ID: %s)', att.id)

        if data.get('xml_base64'):
            att = Attachment.create({
                'name': invoice_id + '.xml',
                'type': 'binary',
                'datas': data.get('xml_base64'),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'mimetype': 'application/xml',
            })
            _logger.info('[crear_compra]   XML adjuntado (ID: %s)', att.id)

    def _validar_recepciones(self, po, resolved_lines):
        """
        Valida automáticamente la recepción de los moves cuyo producto NO requiere serie.
        Los que requieren serie quedan pendientes para ingreso manual.
        Si hay mezcla, deja la recepción tal cual para que el usuario la procese.
        """
        pickings = po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
        if not pickings:
            _logger.warning('[crear_compra] No hay picking para validar')
            return 'no_picking'

        picking = pickings[0]
        _logger.info('[crear_compra] Picking: %s (%s moves)', picking.name, len(picking.move_ids))

        # ¿Algún producto requiere serie?
        has_tracked = any(
            m.product_id.product_tmpl_id.tracking != 'none'
            for m in picking.move_ids
        )

        if has_tracked:
            _logger.info('[crear_compra] Hay productos con tracking — recepción queda pendiente')
            return 'pending_serial'

        # Mapa product_id → qty pedida (suma si producto repetido)
        qty_por_producto = {}
        for item in resolved_lines:
            pid = item['product'].id
            qty = float(item['line_data'].get('quantity', 1))
            qty_por_producto[pid] = qty_por_producto.get(pid, 0) + qty

        for move in picking.move_ids:
            qty = qty_por_producto.get(move.product_id.id, move.product_qty)
            move.quantity = qty
            _logger.info('[crear_compra]   Move %s: producto %s, qty=%s',
                         move.id, move.product_id.name, qty)

        picking.with_context(skip_backorder=True, skip_immediate=True).button_validate()
        _logger.info('[crear_compra] Recepción VALIDADA: %s — estado: %s',
                     picking.name, picking.state)
        return 'done'

    # =========================================================================
    # PENDIENTES Y NOTIFICACIÓN
    # =========================================================================
    def _crear_pendiente(self, data, line, line_index, group_token):
        """Crea UN pendiente para UNA línea desconocida."""
        pending = request.env['purchase.product.pending'].sudo().create({
            'group_token': group_token,
            'description_proveedor': line.get('description', ''),
            'line_index': line_index,
            'line_quantity': float(line.get('quantity', 0) or 0),
            'line_unit_price': float(line.get('unit_price', 0) or 0),
            'supplier_name': data.get('supplier_name', ''),
            'supplier_ruc': data.get('supplier_ruc', ''),
            'invoice_id': data.get('invoice_id', ''),
            'currency_name': data.get('currency', 'USD'),
            'invoice_payload': json.dumps(data),
            'state': 'pending',
        })
        _logger.info('[crear_compra]   Pendiente CREADO: ID=%s, line_index=%s, token=%s, desc="%s"',
                     pending.id, line_index, pending.token, line.get('description', '')[:50])
        return pending

    def _enviar_notificacion_grupo(self, data, pendings, resolved_lines, group_token):
        """Envía UN solo email con todas las líneas desconocidas de la factura."""
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        resolver_url = '%s/copier/resolver-producto/%s' % (base_url, group_token)

        # Filas de productos desconocidos
        unknown_rows = ''
        for p in pendings:
            unknown_rows += '''
                <tr>
                    <td style="padding:10px; border-bottom:1px solid #eee;">
                        <strong style="color:#c0392b;">%s</strong><br>
                        <span style="color:#666; font-size:13px;">Cantidad: %s &nbsp;|&nbsp; Precio: %s %s</span>
                    </td>
                </tr>
            ''' % (
                p.description_proveedor,
                p.line_quantity,
                p.line_unit_price,
                data.get('currency', 'USD'),
            )

        # Filas de productos ya resueltos (informativo)
        resolved_rows = ''
        if resolved_lines:
            for item in resolved_lines:
                resolved_rows += '''
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #eee; color:#27ae60;">
                            ✓ %s <span style="color:#666;">(qty: %s)</span>
                        </td>
                    </tr>
                ''' % (
                    item['product'].name,
                    item['line_data'].get('quantity', ''),
                )

        subject = 'Productos desconocidos en factura %s — Acción requerida' % data.get('invoice_id', '')
        body = '''
        <div style="font-family: Arial, sans-serif; max-width:600px;">
            <p>Hola Isidro,</p>
            <p>La factura <strong>%s</strong> de <strong>%s</strong> tiene
               <strong style="color:#c0392b;">%s producto(s) desconocido(s)</strong>
               que necesitan resolución antes de crear la orden de compra.</p>

            <h3 style="color:#c0392b; margin-top:24px;">Productos a resolver:</h3>
            <table style="border-collapse:collapse; width:100%%; background:#fff8f8; border:1px solid #f5c6cb; border-radius:4px;">
                %s
            </table>

            %s

            <p style="margin-top:24px;">
                <a href="%s" style="background:#875A7B; color:white; padding:14px 28px;
                   text-decoration:none; border-radius:4px; display:inline-block; font-weight:bold;">
                   Resolver todos los productos
                </a>
            </p>
            <p style="color:#666; font-size:12px; margin-top:16px;">O copia este link: %s</p>

            <hr style="margin-top:24px; border:none; border-top:1px solid #eee;">
            <p style="color:#999; font-size:11px;">
                Factura: %s &middot; RUC: %s &middot; Fecha emisión: %s
            </p>
        </div>
        ''' % (
            data.get('invoice_id', ''),
            data.get('supplier_name', ''),
            len(pendings),
            unknown_rows,
            ('<h4 style="color:#27ae60; margin-top:24px;">Ya resueltos automáticamente:</h4>'
             '<table style="border-collapse:collapse; width:100%%; background:#f0f9f0; border:1px solid #c3e6c3; border-radius:4px;">'
             + resolved_rows + '</table>') if resolved_rows else '',
            resolver_url,
            resolver_url,
            data.get('invoice_id', ''),
            data.get('supplier_ruc', ''),
            data.get('issue_date', ''),
        )

        mail = request.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_to': NOTIFICATION_EMAIL,
            'auto_delete': True,
        })
        mail.send()
        _logger.info('[crear_compra] Email enviado a %s — group_token=%s, pendientes=%s',
                     NOTIFICATION_EMAIL, group_token, len(pendings))