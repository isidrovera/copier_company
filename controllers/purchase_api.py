# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/purchase_api.py

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PurchaseApiController(http.Controller):

    @http.route('/copier/crear_compra', type='jsonrpc', auth='bearer', methods=['POST'], csrf=False)
    def crear_compra(self, **kwargs):
        """
        Crea una Orden de Compra desde n8n a partir de datos de factura electrónica.

        Payload esperado:
        {
            "invoice_id":    "F101-0015297",
            "issue_date":    "2026-04-06",
            "due_date":      "2026-04-21",
            "currency":      "USD",
            "supplier_ruc":  "20514724033",
            "supplier_name": "CORPORACION ANDES PRODUCTS S.A",
            "description":   "FOTOCONDUTOR FUJI COLOR IR ...",
            "quantity":      2.0,
            "unit_price":    27.54,
            "line_amount":   55.08,
            "tax_amount":    9.92,
            "total":         65.0,
            "pdf_base64":    "...",
            "xml_base64":    "..."
        }
        """
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

            # 1. Buscar o crear proveedor por RUC (campo vat)
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
            _logger.info('[crear_compra] Buscando moneda: %s', currency_name)
            Currency = request.env['res.currency'].sudo()
            currency = Currency.search([('name', '=', currency_name)], limit=1)
            if currency:
                _logger.info('[crear_compra] Moneda encontrada: %s (ID: %s)', currency.name, currency.id)
            else:
                _logger.warning('[crear_compra] Moneda NO encontrada: %s — se usará la moneda por defecto', currency_name)
            currency_id = currency.id if currency else False

            # 3. Buscar o crear producto
            description = data.get('description', '')
            _logger.info('[crear_compra] Buscando producto por descripción: "%s"', description[:60])
            Product = request.env['product.product'].sudo()
            product = Product.search([('name', 'ilike', description[:40])], limit=1)
            if not product:
                _logger.info('[crear_compra] Producto no encontrado, creando nuevo...')
                # uom_po_id NO existe en este Odoo — solo uom_id
                template = request.env['product.template'].sudo().create({
                    'name': description,
                    'type': 'consu',        # consu = consumible, no requiere config de stock
                    'purchase_ok': True,
                    'sale_ok': False,
                    'uom_id': request.env.ref('uom.product_uom_unit').id,
                })
                product = Product.search([('product_tmpl_id', '=', template.id)], limit=1)
                _logger.info('[crear_compra] Producto CREADO: "%s" (template_id: %s, product_id: %s)',
                    description[:60], template.id, product.id)
            else:
                _logger.info('[crear_compra] Producto ENCONTRADO: %s (ID: %s)', product.name, product.id)

            # 4. Buscar impuesto IGV 18% compras
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
                _logger.warning('[crear_compra] IGV 18%% NO encontrado — línea se creará sin impuesto')
            # En Odoo 17+: tax_ids (no taxes_id)
            tax_ids = [(4, igv.id)] if igv else []

            # 5. Preparar fechas
            issue_date = data.get('issue_date', '')
            due_date = data.get('due_date', issue_date)
            _logger.info('[crear_compra] Fechas — emisión: %s | vencimiento: %s', issue_date, due_date)

            from odoo.fields import Datetime as OdooDatetime
            from datetime import datetime

            def parse_date(date_str):
                if not date_str:
                    return datetime.now()
                try:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d')
                except Exception:
                    return datetime.now()

            date_order_str = parse_date(issue_date)
            date_planned_str = parse_date(due_date)

            # 6. Crear Purchase Order
            _logger.info('[crear_compra] Creando Purchase Order...')
            PO = request.env['purchase.order'].sudo()
            po = PO.create({
                'partner_id': partner.id,
                'currency_id': currency_id or False,
                'date_order': date_order_str,
                'date_planned': date_planned_str,
                'partner_ref': data.get('invoice_id', ''),
                'note': 'Factura: %s | Vencimiento: %s' % (        # campo validado: 'note' existe
                    data.get('invoice_id', ''), due_date
                ),
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': description,
                    'product_qty': float(data.get('quantity', 1)),
                    'price_unit': float(data.get('unit_price', 0)),
                    'tax_ids': tax_ids,                             # corregido: tax_ids (no taxes_id)
                    'date_planned': date_planned_str,
                })],
            })
            _logger.info('[crear_compra] PO CREADA: %s (ID: %s)', po.name, po.id)

            # 7. Adjuntar PDF
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
            else:
                _logger.info('[crear_compra] Sin PDF en payload, omitiendo adjunto')

            # 8. Adjuntar XML
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
            else:
                _logger.info('[crear_compra] Sin XML en payload, omitiendo adjunto')

            result = {
                'success': True,
                'po_id': po.id,
                'po_name': po.name,
                'po_url': '/odoo/purchase/%d' % po.id,
                'partner_id': partner.id,
                'partner_name': partner.name,
                'product_id': product.id,
                'invoice_id': data.get('invoice_id'),
            }
            _logger.info('=== [crear_compra] Fin exitoso: %s ===', result)
            return result

        except Exception as e:
            _logger.error('=== [crear_compra] ERROR: %s ===', str(e), exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }