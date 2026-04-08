# -*- coding: utf-8 -*-
# Archivo: copier_company/controllers/purchase_api.py
# Agregar en __manifest__.py: 'controllers/purchase_api.py' en data o importar en __init__.py

import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class PurchaseApiController(http.Controller):

    @http.route('/copier/crear_compra', type='json', auth='bearer', methods=['POST'], csrf=False)
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
        try:
            data = request.get_json_data()

            # 1. Buscar o crear proveedor por RUC (campo vat)
            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([('vat', '=', data.get('supplier_ruc'))], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': data.get('supplier_name', 'Proveedor sin nombre'),
                    'vat': data.get('supplier_ruc'),
                    'supplier_rank': 1,
                    'country_id': request.env.ref('base.pe').id,
                })
                _logger.info('Proveedor creado: %s (RUC: %s)', partner.name, partner.vat)
            else:
                _logger.info('Proveedor encontrado: %s (ID: %s)', partner.name, partner.id)

            # 2. Buscar moneda
            Currency = request.env['res.currency'].sudo()
            currency = Currency.search([('name', '=', data.get('currency', 'USD'))], limit=1)
            currency_id = currency.id if currency else False

            # 3. Buscar o crear producto
            Product = request.env['product.product'].sudo()
            description = data.get('description', '')
            product = Product.search([('name', 'ilike', description[:40])], limit=1)
            if not product:
                template = request.env['product.template'].sudo().create({
                    'name': description,
                    'type': 'product',
                    'purchase_ok': True,
                    'sale_ok': False,
                    'uom_id': request.env.ref('uom.product_uom_unit').id,
                    'uom_po_id': request.env.ref('uom.product_uom_unit').id,
                })
                product = Product.search([('product_tmpl_id', '=', template.id)], limit=1)
                _logger.info('Producto creado: %s', description[:60])
            else:
                _logger.info('Producto encontrado: %s (ID: %s)', product.name, product.id)

            # 4. Buscar impuesto IGV 18% compras
            Tax = request.env['account.tax'].sudo()
            igv = Tax.search([
                ('amount', '=', 18),
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True),
            ], limit=1)
            tax_ids = [(4, igv.id)] if igv else []

            # 5. Preparar fecha
            issue_date = data.get('issue_date', '')
            due_date = data.get('due_date', issue_date)

            # 6. Crear Purchase Order
            PO = request.env['purchase.order'].sudo()
            po = PO.create({
                'partner_id': partner.id,
                'currency_id': currency_id or False,
                'date_order': issue_date + ' 00:00:00' if issue_date else False,
                'date_planned': due_date + ' 00:00:00' if due_date else False,
                'partner_ref': data.get('invoice_id', ''),
                'notes': 'Factura: %s | Vencimiento: %s' % (
                    data.get('invoice_id', ''), due_date
                ),
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': description,
                    'product_qty': float(data.get('quantity', 1)),
                    'price_unit': float(data.get('unit_price', 0)),
                    'taxes_id': tax_ids,
                    'date_planned': due_date + ' 00:00:00' if due_date else False,
                })],
            })
            _logger.info('PO creada: %s (ID: %s)', po.name, po.id)

            # 7. Adjuntar PDF
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

            # 8. Adjuntar XML
            if data.get('xml_base64'):
                Attachment.create({
                    'name': data.get('invoice_id', 'factura') + '.xml',
                    'type': 'binary',
                    'datas': data.get('xml_base64'),
                    'res_model': 'purchase.order',
                    'res_id': po.id,
                    'mimetype': 'application/xml',
                })

            return {
                'success': True,
                'po_id': po.id,
                'po_name': po.name,
                'po_url': '/odoo/purchase/%d' % po.id,
                'partner_id': partner.id,
                'partner_name': partner.name,
                'product_id': product.id,
                'invoice_id': data.get('invoice_id'),
            }

        except Exception as e:
            _logger.error('Error creando PO desde API: %s', str(e), exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }