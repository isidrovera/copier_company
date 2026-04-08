# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/purchase_api.py

import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

NOTIFICATION_EMAIL = 'isidro@copiercompanysac.com'


class PurchaseApiController(http.Controller):

    @http.route('/copier/crear_compra', type='jsonrpc', auth='bearer', methods=['POST'], csrf=False)
    def crear_compra(self, **kwargs):
        _logger.info('=== [crear_compra] Inicio de request ===')
        try:
            raw = request.get_json_data()
            # Soporta payload plano o envuelto en jsonrpc {params: {...}}
            if isinstance(raw, dict) and 'params' in raw:
                data = raw['params']
            else:
                data = raw

            _logger.info('[crear_compra] Payload recibido: invoice_id=%s, supplier_ruc=%s, currency=%s, qty=%s, unit_price=%s',
                data.get('invoice_id'), data.get('supplier_ruc'), data.get('currency'),
                data.get('quantity'), data.get('unit_price'))

            # 1. Buscar o crear proveedor por RUC
            _logger.info('[crear_compra] Buscando proveedor por RUC: %s', data.get('supplier_ruc'))
            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([('vat', '=', data.get('supplier_ruc'))], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': data.get('supplier_name', 'Proveedor sin nombre'),
                    'vat': data.get('supplier_ruc'),
                    'supplier_rank': 1,
                    'country_id': request.env.ref('base.pe').id,
                })
                _logger.info('[crear_compra] Proveedor CREADO: %s (ID: %s, RUC: %s)',
                    partner.name, partner.id, partner.vat)
            else:
                _logger.info('[crear_compra] Proveedor ENCONTRADO: %s (ID: %s)',
                    partner.name, partner.id)

            # 2. Buscar moneda
            currency_name = data.get('currency', 'USD')
            Currency = request.env['res.currency'].sudo()
            currency = Currency.search([('name', '=', currency_name)], limit=1)
            if currency:
                _logger.info('[crear_compra] Moneda encontrada: %s (ID: %s)', currency.name, currency.id)
            else:
                _logger.warning('[crear_compra] Moneda NO encontrada: %s', currency_name)
            currency_id = currency.id if currency else False

            # 3. Buscar producto — primero por nombre exacto, luego por alias exacto
            description = data.get('description', '')
            _logger.info('[crear_compra] Buscando producto por descripción exacta: "%s"', description[:60])

            Product = request.env['product.product'].sudo()
            product = Product.search([('name', '=', description)], limit=1)

            if not product:
                _logger.info('[crear_compra] No encontrado por nombre exacto, buscando por alias...')
                description_lower = description.strip().lower()
                alias = request.env['product.name.alias'].sudo().search(
                    [('name', '=', description_lower)], limit=1
                )
                if alias:
                    product = Product.search(
                        [('product_tmpl_id', '=', alias.product_id.id)], limit=1
                    )
                    _logger.info('[crear_compra] Producto encontrado por ALIAS "%s": %s (ID: %s)',
                        alias.name, product.name, product.id)

            if not product:
                # Producto desconocido — crear registro pendiente y notificar
                _logger.warning('[crear_compra] Producto DESCONOCIDO: "%s" — creando pendiente', description[:60])
                pending = self._crear_pendiente(data)
                self._enviar_notificacion(pending, data)
                return {
                    'success': False,
                    'pending': True,
                    'pending_id': pending.id,
                    'token': pending.token,
                    'message': 'Producto desconocido. Se envió notificación para resolución manual.',
                    'description': description,
                }

            _logger.info('[crear_compra] Producto ENCONTRADO: %s (ID: %s)', product.name, product.id)

            # 4. Buscar IGV 18%
            _logger.info('[crear_compra] Buscando impuesto IGV 18%% compras...')
            Tax = request.env['account.tax'].sudo()
            igv = Tax.search([
                ('amount', '=', 18),
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True),
            ], limit=1)
            if igv:
                _logger.info('[crear_compra] IGV encontrado: %s (ID: %s)', igv.name, igv.id)
            else:
                _logger.warning('[crear_compra] IGV 18%% NO encontrado')
            tax_ids = [(4, igv.id)] if igv else []

            # 5. Preparar fechas
            issue_date = data.get('issue_date', '')
            due_date = data.get('due_date', issue_date)
            _logger.info('[crear_compra] Fechas — emisión: %s | vencimiento: %s', issue_date, due_date)

            def parse_date(date_str):
                if not date_str:
                    return datetime.now()
                try:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d')
                except Exception:
                    return datetime.now()

            # 6. Crear PO y confirmar
            result = self._crear_y_confirmar_po(
                data, partner, currency_id, product, tax_ids,
                parse_date(issue_date), parse_date(due_date), description
            )
            _logger.info('=== [crear_compra] Fin exitoso: %s ===', result)
            return result

        except Exception as e:
            _logger.error('=== [crear_compra] ERROR: %s ===', str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    def _crear_y_confirmar_po(self, data, partner, currency_id, product, tax_ids,
                               date_order, date_planned, description):
        """Crea la PO, la confirma y gestiona la recepción según tracking del producto."""
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
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': description,
                'product_qty': float(data.get('quantity', 1)),
                'price_unit': float(data.get('unit_price', 0)),
                'tax_ids': tax_ids,
                'date_planned': date_planned,
            })],
        })
        _logger.info('[crear_compra] PO CREADA: %s (ID: %s)', po.name, po.id)

        # Confirmar PO → genera WH/IN automáticamente
        po.button_confirm()
        _logger.info('[crear_compra] PO CONFIRMADA: %s — estado: %s', po.name, po.state)

        # Adjuntar PDF
        Attachment = request.env['ir.attachment'].sudo()
        if data.get('pdf_base64'):
            att = Attachment.create({
                'name': data.get('invoice_id', 'factura') + '.pdf',
                'type': 'binary',
                'datas': data.get('pdf_base64'),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'mimetype': 'application/pdf',
            })
            _logger.info('[crear_compra] PDF adjuntado (attachment ID: %s)', att.id)

        # Adjuntar XML
        if data.get('xml_base64'):
            att = Attachment.create({
                'name': data.get('invoice_id', 'factura') + '.xml',
                'type': 'binary',
                'datas': data.get('xml_base64'),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'mimetype': 'application/xml',
            })
            _logger.info('[crear_compra] XML adjuntado (attachment ID: %s)', att.id)

        # Gestionar recepción según tracking del producto
        tracking = product.product_tmpl_id.tracking
        _logger.info('[crear_compra] Tracking del producto: %s', tracking)

        reception_state = 'pending_serial'
        if tracking == 'none':
            # Sin serie → validar recepción automáticamente
            reception_state = self._validar_recepcion(po, float(data.get('quantity', 1)))
        else:
            _logger.info('[crear_compra] Producto requiere serie/lote — recepción queda en Listo para ingreso manual')

        return {
            'success': True,
            'po_id': po.id,
            'po_name': po.name,
            'po_state': po.state,
            'po_url': '/odoo/purchase/%d' % po.id,
            'partner_id': partner.id,
            'partner_name': partner.name,
            'product_id': product.id,
            'product_tracking': tracking,
            'invoice_id': data.get('invoice_id'),
            'reception_state': reception_state,
        }

    def _validar_recepcion(self, po, quantity):
        """Valida automáticamente la recepción cuando el producto no requiere serie."""
        pickings = po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
        if not pickings:
            _logger.warning('[crear_compra] No se encontró recepción pendiente para PO %s', po.name)
            return 'no_picking'

        picking = pickings[0]
        _logger.info('[crear_compra] Validando recepción: %s (ID: %s)', picking.name, picking.id)

        for move in picking.move_ids:
            move.quantity = quantity
            _logger.info('[crear_compra] Cantidad seteada en move %s: %s', move.id, quantity)

        # Validar sin backorder
        picking.with_context(skip_backorder=True, skip_immediate=True).button_validate()
        _logger.info('[crear_compra] Recepción VALIDADA: %s — estado: %s', picking.name, picking.state)
        return 'done'

    def _crear_pendiente(self, data):
        """Crea un registro pendiente para resolución manual."""
        pending = request.env['purchase.product.pending'].sudo().create({
            'description_proveedor': data.get('description', ''),
            'supplier_name': data.get('supplier_name', ''),
            'supplier_ruc': data.get('supplier_ruc', ''),
            'invoice_id': data.get('invoice_id', ''),
            'invoice_payload': json.dumps(data),
            'state': 'pending',
        })
        _logger.info('[crear_compra] Pendiente CREADO: ID %s, token: %s', pending.id, pending.token)
        return pending

    def _enviar_notificacion(self, pending, data):
        """Envía email de notificación a isidro con link para resolver."""
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        resolver_url = '%s/copier/resolver-producto/%s' % (base_url, pending.token)

        subject = 'Producto desconocido en factura %s — Acción requerida' % data.get('invoice_id', '')
        body = '''
        <p>Hola Isidro,</p>
        <p>Se recibió una factura con un producto que no existe en Odoo y no tiene alias registrado.</p>
        <table style="border-collapse:collapse; width:100%%; margin:16px 0;">
            <tr><td style="padding:8px; font-weight:bold; background:#f5f5f5;">N° Factura</td>
                <td style="padding:8px;">%s</td></tr>
            <tr><td style="padding:8px; font-weight:bold; background:#f5f5f5;">Proveedor</td>
                <td style="padding:8px;">%s (RUC: %s)</td></tr>
            <tr><td style="padding:8px; font-weight:bold; background:#f5f5f5;">Producto en factura</td>
                <td style="padding:8px;"><strong>%s</strong></td></tr>
            <tr><td style="padding:8px; font-weight:bold; background:#f5f5f5;">Cantidad</td>
                <td style="padding:8px;">%s</td></tr>
            <tr><td style="padding:8px; font-weight:bold; background:#f5f5f5;">Precio unitario</td>
                <td style="padding:8px;">%s %s</td></tr>
        </table>
        <p>Por favor ingresa al siguiente enlace para resolver:</p>
        <p><a href="%s" style="background:#875A7B; color:white; padding:12px 24px; text-decoration:none; border-radius:4px;">
            Resolver producto
        </a></p>
        <p>O copia este link: %s</p>
        ''' % (
            data.get('invoice_id', ''),
            data.get('supplier_name', ''), data.get('supplier_ruc', ''),
            data.get('description', ''),
            data.get('quantity', ''),
            data.get('unit_price', ''), data.get('currency', 'USD'),
            resolver_url, resolver_url,
        )

        mail = request.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_to': NOTIFICATION_EMAIL,
            'auto_delete': True,
        })
        mail.send()
        _logger.info('[crear_compra] Email de notificación enviado a %s para pendiente ID %s',
            NOTIFICATION_EMAIL, pending.id)