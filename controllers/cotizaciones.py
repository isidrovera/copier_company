# -*- coding: utf-8 -*-
"""Formulario público de solicitud rápida para Odoo 19.
No modifica fichas de contactos existentes ni exige un modelo de equipo.
"""
import logging
import re
from html import escape

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CopierCompany(http.Controller):
    DESTINATARIO = 'outsourcing@copiercompanysac.com'
    TIPOS = {'alquiler': 'Alquiler', 'venta': 'Venta', 'servicio': 'Servicio'}

    @staticmethod
    def _clean(value, limit=250):
        return str(value or '').strip()[:limit]

    @staticmethod
    def _lookup_document(kind, number):
        """Consulta con la integración YA EXISTENTE en res.partner.
        Un savepoint permite eliminar siempre el partner provisional.
        No expone identificadores internos ni datos de contacto de terceros.
        """
        code = '1' if kind == 'dni' else '6'
        if not re.fullmatch(r'\d{8}' if kind == 'dni' else r'\d{11}', number):
            return False
        Partner = request.env['res.partner'].sudo()
        existing = Partner.search([
            ('vat', '=', number),
            ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', code),
        ], limit=1)
        if existing:
            return existing.name
        doc_type = request.env['l10n_latam.identification.type'].sudo().search([
            ('l10n_pe_vat_code', '=', code)
        ], limit=1)
        if not doc_type:
            return False
        temp = False
        try:
            with request.env.cr.savepoint():
                temp = Partner.create({
                    'name': 'Temporal', 'vat': number,
                    'l10n_latam_identification_type_id': doc_type.id,
                })
                temp._doc_number_change()
                name = (temp.name or '').strip()
                temp.unlink()
                return name if name and name not in ('Temporal', number) else False
        except Exception:
            _logger.warning('No fue posible consultar el documento %s.', kind, exc_info=True)
            return False

    @http.route('/cotizacion/form', type='http', auth='public', website=True, methods=['GET'])
    def copier_company_form(self, **kwargs):
        return request.render('copier_company.copier_company_form_template', {'form_values': {}, 'error_message': False})

    @http.route('/copier_company/buscar_cliente', type='jsonrpc', auth='public', website=True)
    def buscar_cliente(self, tipo_identificacion=None, identificacion=None, **kwargs):
        code = self._clean(tipo_identificacion, 5)
        number = self._clean(identificacion, 20)
        kind = {'1': 'dni', '6': 'ruc', 'dni': 'dni', 'ruc': 'ruc'}.get(code)
        if not kind:
            return {'success': False, 'found': False, 'message': 'Tipo de documento no válido.'}
        if not re.fullmatch(r'\d{8}' if kind == 'dni' else r'\d{11}', number):
            return {'success': False, 'found': False, 'message': 'Número de documento inválido.'}
        name = self._lookup_document(kind, number)
        return {
            'success': True, 'found': bool(name),
            'data': {'name': name} if name else {},
            'message': '' if name else 'No se encontraron datos; escriba el nombre manualmente.',
        }

    @http.route('/cotizacion/submit', type='http', auth='public', website=True,
                csrf=True, methods=['POST'])
    def copier_company_submit(self, **kwargs):
        def error(message):
            return request.render('copier_company.copier_company_form_template', {
                'error_message': message,
                'form_values': {k: self._clean(v, 1500) for k, v in kwargs.items()
                                if k in ('solicitud_tipo', 'dni_contacto', 'contacto',
                                         'ruc_empresa', 'razon_social', 'correo',
                                         'telefono', 'detalles', 'manual_contacto')},
            })

        if self._clean(kwargs.get('website_note')):
            return error('No se pudo procesar la solicitud.')

        tipo = self._clean(kwargs.get('solicitud_tipo'), 15).lower()
        dni = self._clean(kwargs.get('dni_contacto'), 20)
        contacto = self._clean(kwargs.get('contacto'), 150)
        ruc = self._clean(kwargs.get('ruc_empresa'), 20)
        razon_social = self._clean(kwargs.get('razon_social'), 200)
        correo = self._clean(kwargs.get('correo'), 254)
        telefono = self._clean(kwargs.get('telefono'), 35)
        descripcion = self._clean(kwargs.get('detalles'), 1800)
        manual = kwargs.get('manual_contacto') == '1'

        if tipo not in self.TIPOS:
            return error('Seleccione Alquiler, Venta o Servicio.')
        if not contacto or not razon_social or not correo or not telefono:
            return error('Complete nombre, empresa, correo y celular.')
        if not manual and not re.fullmatch(r'\d{8}', dni):
            return error('Ingrese un DNI de 8 dígitos o seleccione ingreso manual.')
        if dni and not re.fullmatch(r'\d{8}', dni):
            return error('El DNI debe tener 8 dígitos.')
        if not re.fullmatch(r'\d{11}', ruc):
            return error('Ingrese un RUC válido de 11 dígitos.')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo):
            return error('Ingrese un correo electrónico válido.')
        if len(re.sub(r'\D', '', telefono)) < 6:
            return error('Ingrese un celular o teléfono válido.')
        if kwargs.get('acepta_privacidad') != '1':
            return error('Debe aceptar la política de privacidad.')

        try:
            # No confiar en IDs de partners enviados por el navegador.
            # Buscar únicamente por el RUC verificado sintácticamente.
            Partner = request.env['res.partner'].sudo()
            company = Partner.search([('vat', '=', ruc)], limit=1)
            if not company:
                company_vals = {'name': razon_social, 'vat': ruc, 'is_company': True}
                doc = request.env['l10n_latam.identification.type'].sudo().search([
                    ('l10n_pe_vat_code', '=', '6')
                ], limit=1)
                if doc:
                    company_vals['l10n_latam_identification_type_id'] = doc.id
                company = Partner.create(company_vals)

            detalles = (
                'SOLICITUD WEB - GOOGLE ADS\n'
                'Tipo de solicitud: %s\n'
                'Contacto: %s\n'
                'DNI: %s\n'
                'Empresa declarada: %s\n'
                'RUC: %s\n'
                'Correo: %s\n'
                'Celular: %s\n\n'
                'Descripción:\n%s'
            ) % (self.TIPOS[tipo], contacto, dni or 'Sin DNI (manual)',
                 razon_social, ruc, correo, telefono, descripcion or 'No indicada')

            # name (modelo de máquina) es Many2one NO obligatorio en el modelo compartido.
            # No asignar tipo de impresión ni alterar precios/volúmenes.
            cotizacion = request.env['copier.company'].sudo().create({
                'cliente_id': company.id,
                'contacto': contacto,
                'correo': correo,
                'celular': telefono,
                'detalles': detalles,
            })

            safe = lambda s: escape(str(s or ''))
            body = '''<div style="font-family:Arial,sans-serif;line-height:1.55">
                <h2>Nueva solicitud web: %s</h2>
                <p><strong>Número:</strong> %s</p>
                <p><strong>Contacto:</strong> %s<br/><strong>DNI:</strong> %s<br/>
                <strong>RUC:</strong> %s<br/><strong>Empresa:</strong> %s<br/>
                <strong>Correo:</strong> %s<br/><strong>Celular:</strong> %s</p>
                <h3>Descripción</h3><p>%s</p>
                <p>Origen: formulario web de cotización</p></div>''' % (
                    safe(self.TIPOS[tipo]), safe(cotizacion.secuencia), safe(contacto),
                    safe(dni or 'Ingreso manual'), safe(ruc), safe(razon_social),
                    safe(correo), safe(telefono), safe(descripcion).replace('\n', '<br/>'))
            # Registrar el correo incluso si el servidor SMTP está temporalmente caído.
            mail = request.env['mail.mail'].sudo().create({
                'subject': 'Solicitud %s - %s - %s' % (
                    cotizacion.secuencia, self.TIPOS[tipo], razon_social),
                'email_to': self.DESTINATARIO,
                'reply_to': correo,
                'body_html': body,
                'auto_delete': False,
            })
            try:
                with request.env.cr.savepoint():
                    mail.send(raise_exception=True)
            except Exception:
                _logger.exception('La solicitud %s se creó pero no se pudo enviar el correo.',
                                  cotizacion.secuencia)
            return request.render('copier_company.confirmacion_template', {
                'cotizacion': cotizacion,
                'solicitud_tipo': self.TIPOS[tipo],
                'empresa_nombre': razon_social,
            })
        except Exception:
            _logger.exception('Error creando solicitud de cotización web')
            return error('No fue posible registrar la solicitud. Inténtelo nuevamente.')
