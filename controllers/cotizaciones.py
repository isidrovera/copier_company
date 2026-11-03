# -*- coding: utf-8 -*-
"""Formulario público rápido Copier Company SAC (Odoo 19).

Rutas existentes: /cotizacion/form, /copier_company/buscar_cliente,
/cotizacion/submit. No altera datos de contactos existentes.
"""
import logging
import re
import uuid
from html import escape

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CopierCompany(http.Controller):
    DESTINATARIO = 'outsourcing@copiercompanysac.com'
    TIPOS = {'alquiler': 'Alquiler', 'venta': 'Venta', 'servicio': 'Servicio'}

    @staticmethod
    def _clean(value, limit=250):
        return str(value or '').strip()[:limit]

    @staticmethod
    def _masked(number):
        number = str(number or '')
        return ('*' * max(0, len(number) - 3)) + number[-3:]

    def _lookup_document(self, kind, number, trace):
        """Usa la integración ya disponible en res.partner.

        Consulta primero la BD. El registro auxiliar se elimina incluso cuando
        el proveedor externo falla. No entrega IDs ni datos de contacto ajenos.
        """
        code = '1' if kind == 'dni' else '6'
        pattern = r'\d{8}' if kind == 'dni' else r'\d{11}'
        if not re.fullmatch(pattern, number):
            _logger.warning('[COTIZACION][%s] Documento inválido | tipo=%s', trace, kind)
            return False

        Partner = request.env['res.partner'].sudo()
        _logger.info('[COTIZACION][%s] Inicio consulta | tipo=%s | documento=%s',
                     trace, kind, self._masked(number))
        try:
            existing = Partner.search([
                ('vat', '=', number),
                ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', code),
            ], limit=1)
            if existing:
                _logger.info('[COTIZACION][%s] Documento encontrado en BD | partner_id=%s',
                             trace, existing.id)
                return existing.name

            doc_type = request.env['l10n_latam.identification.type'].sudo().search([
                ('l10n_pe_vat_code', '=', code),
            ], limit=1)
            if not doc_type:
                _logger.error('[COTIZACION][%s] Tipo de identificación no configurado | code=%s',
                              trace, code)
                return False

            # La consulta original de SUNAT/RENIEC se ejecuta a través de
            # _doc_number_change; no se crea un contacto permanente por buscar.
            with request.env.cr.savepoint():
                temporary = Partner.create({
                    'name': 'Temporal',
                    'vat': number,
                    'l10n_latam_identification_type_id': doc_type.id,
                })
                _logger.info('[COTIZACION][%s] Consultando API mediante _doc_number_change', trace)
                try:
                    temporary._doc_number_change()
                    name = self._clean(temporary.name, 250)
                finally:
                    temporary.unlink()
            if name and name not in ('Temporal', number):
                _logger.info('[COTIZACION][%s] API devolvió nombre | tipo=%s', trace, kind)
                return name
            _logger.warning('[COTIZACION][%s] API sin datos | tipo=%s', trace, kind)
            return False
        except Exception:
            _logger.exception('[COTIZACION][%s] Error durante consulta %s', trace, kind)
            return False

    @http.route('/cotizacion/form', type='http', auth='public', website=True,
                methods=['GET'])
    def copier_company_form(self, **kwargs):
        trace = uuid.uuid4().hex[:10]
        _logger.info('[COTIZACION][%s] GET /cotizacion/form | iniciando render', trace)
        try:
            result = request.render('copier_company.copier_company_form_template', {
                'form_values': {}, 'error_message': False,
            })
            _logger.info('[COTIZACION][%s] Formulario renderizado', trace)
            return result
        except Exception:
            _logger.exception('[COTIZACION][%s] Error al renderizar formulario', trace)
            raise

    @http.route('/copier_company/buscar_cliente', type='jsonrpc', auth='public',
                website=True, methods=['POST'])
    def buscar_cliente(self, tipo_identificacion=None, identificacion=None, **kwargs):
        trace = uuid.uuid4().hex[:10]
        code = self._clean(tipo_identificacion, 5).lower()
        number = self._clean(identificacion, 20)
        kind = {'1': 'dni', '6': 'ruc', 'dni': 'dni', 'ruc': 'ruc'}.get(code)
        _logger.info('[COTIZACION][%s] POST buscar_cliente | tipo=%s', trace, code)
        if not kind:
            _logger.warning('[COTIZACION][%s] Tipo de documento no reconocido', trace)
            return {'success': False, 'found': False,
                    'message': 'Tipo de documento no válido.'}
        if not re.fullmatch(r'\d{8}' if kind == 'dni' else r'\d{11}', number):
            _logger.warning('[COTIZACION][%s] Formato de número inválido | tipo=%s',
                            trace, kind)
            return {'success': False, 'found': False,
                    'message': 'Número de documento inválido.'}
        name = self._lookup_document(kind, number, trace)
        _logger.info('[COTIZACION][%s] Fin buscar_cliente | encontrado=%s', trace, bool(name))
        return {
            'success': True, 'found': bool(name),
            'data': {'name': name} if name else {},
            'message': '' if name else 'No se encontraron datos; escriba el nombre manualmente.',
        }

    @http.route('/cotizacion/submit', type='http', auth='public', website=True,
                csrf=True, methods=['POST'])
    def copier_company_submit(self, **kwargs):
        trace = uuid.uuid4().hex[:10]
        _logger.info('[COTIZACION][%s] POST submit | inicio | campos=%s', trace,
                     sorted(set(kwargs) - {'csrf_token'}))

        def form_error(message):
            _logger.warning('[COTIZACION][%s] Validación fallida | motivo=%s', trace, message)
            return request.render('copier_company.copier_company_form_template', {
                'error_message': message,
                'form_values': {
                    k: self._clean(v, 1800) for k, v in kwargs.items()
                    if k in ('solicitud_tipo', 'dni_contacto', 'contacto',
                             'ruc_empresa', 'razon_social', 'correo', 'telefono',
                             'detalles', 'manual_contacto')
                },
            })

        if self._clean(kwargs.get('website_note')):
            _logger.warning('[COTIZACION][%s] Honeypot completado', trace)
            return form_error('No se pudo procesar la solicitud.')

        tipo = self._clean(kwargs.get('solicitud_tipo'), 15).lower()
        dni = self._clean(kwargs.get('dni_contacto'), 20)
        contacto = self._clean(kwargs.get('contacto'), 150)
        ruc = self._clean(kwargs.get('ruc_empresa'), 20)
        razon_social = self._clean(kwargs.get('razon_social'), 200)
        correo = self._clean(kwargs.get('correo'), 254)
        telefono = self._clean(kwargs.get('telefono'), 35)
        descripcion = self._clean(kwargs.get('detalles'), 1800)
        manual = kwargs.get('manual_contacto') == '1'

        _logger.info('[COTIZACION][%s] Datos recibidos | tipo=%s | manual=%s | '
                     'dni=%s | ruc=%s | email_presente=%s | celular_presente=%s',
                     trace, tipo, manual, self._masked(dni), self._masked(ruc),
                     bool(correo), bool(telefono))

        if tipo not in self.TIPOS:
            return form_error('Seleccione Alquiler, Venta o Servicio.')
        if not contacto or not razon_social or not correo or not telefono:
            return form_error('Complete nombre, empresa, correo y celular.')
        if not manual and not re.fullmatch(r'\d{8}', dni):
            return form_error('Ingrese un DNI de 8 dígitos o seleccione ingreso manual.')
        if dni and not re.fullmatch(r'\d{8}', dni):
            return form_error('El DNI debe tener 8 dígitos.')
        if not re.fullmatch(r'\d{11}', ruc):
            return form_error('Ingrese un RUC válido de 11 dígitos.')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo):
            return form_error('Ingrese un correo electrónico válido.')
        if len(re.sub(r'\D', '', telefono)) < 6:
            return form_error('Ingrese un celular o teléfono válido.')
        if kwargs.get('acepta_privacidad') != '1':
            return form_error('Debe aceptar la política de privacidad.')

        try:
            Partner = request.env['res.partner'].sudo()
            _logger.info('[COTIZACION][%s] Buscando empresa existente', trace)
            company = Partner.search([('vat', '=', ruc)], limit=1)
            if company:
                _logger.info('[COTIZACION][%s] Empresa existente | partner_id=%s',
                             trace, company.id)
            else:
                company_vals = {'name': razon_social, 'vat': ruc, 'is_company': True}
                doc = request.env['l10n_latam.identification.type'].sudo().search([
                    ('l10n_pe_vat_code', '=', '6'),
                ], limit=1)
                if doc:
                    company_vals['l10n_latam_identification_type_id'] = doc.id
                _logger.info('[COTIZACION][%s] Creando nuevo partner empresa', trace)
                company = Partner.create(company_vals)
                _logger.info('[COTIZACION][%s] Empresa creada | partner_id=%s',
                             trace, company.id)

            details = (
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

            # 'name' es Many2one opcional en el modelo copier.company compartido.
            _logger.info('[COTIZACION][%s] Creando copier.company | partner_id=%s',
                         trace, company.id)
            quotation = request.env['copier.company'].sudo().create({
                'cliente_id': company.id,
                'contacto': contacto,
                'correo': correo,
                'celular': telefono,
                'detalles': details,
            })
            _logger.info('[COTIZACION][%s] Solicitud creada | id=%s | secuencia=%s',
                         trace, quotation.id, quotation.secuencia)

            safe = lambda value: escape(str(value or ''))
            body = '''<div style="font-family:Arial,sans-serif;line-height:1.55">
                <h2>Nueva solicitud web: %s</h2>
                <p><strong>Número:</strong> %s</p>
                <p><strong>Contacto:</strong> %s<br/><strong>DNI:</strong> %s<br/>
                <strong>RUC:</strong> %s<br/><strong>Empresa:</strong> %s<br/>
                <strong>Correo:</strong> %s<br/><strong>Celular:</strong> %s</p>
                <h3>Descripción</h3><p>%s</p>
                <p>Origen: formulario web de cotización</p></div>''' % (
                    safe(self.TIPOS[tipo]), safe(quotation.secuencia), safe(contacto),
                    safe(dni or 'Ingreso manual'), safe(ruc), safe(razon_social),
                    safe(correo), safe(telefono), safe(descripcion).replace('\n', '<br/>'))

            _logger.info('[COTIZACION][%s] Creando mail.mail | destinatario=%s',
                         trace, self.DESTINATARIO)
            mail = request.env['mail.mail'].sudo().create({
                'subject': 'Solicitud %s - %s - %s' % (
                    quotation.secuencia, self.TIPOS[tipo], razon_social),
                'email_to': self.DESTINATARIO,
                'reply_to': correo,
                'body_html': body,
                'auto_delete': False,
            })
            _logger.info('[COTIZACION][%s] Correo en cola | mail_id=%s', trace, mail.id)
            try:
                with request.env.cr.savepoint():
                    _logger.info('[COTIZACION][%s] Intentando envío SMTP | mail_id=%s',
                                 trace, mail.id)
                    mail.send(raise_exception=True)
                _logger.info('[COTIZACION][%s] Resultado correo | mail_id=%s | estado=%s',
                             trace, mail.id, mail.state)
            except Exception:
                _logger.exception('[COTIZACION][%s] Falló envío SMTP | mail_id=%s | '
                                  'solicitud_id=%s', trace, mail.id, quotation.id)
                _logger.warning('[COTIZACION][%s] Solicitud creada, revisar correo saliente',
                                trace)

            _logger.info('[COTIZACION][%s] Renderizando confirmación | solicitud_id=%s',
                         trace, quotation.id)
            return request.render('copier_company.confirmacion_template', {
                'cotizacion': quotation,
                'solicitud_tipo': self.TIPOS[tipo],
                'empresa_nombre': razon_social,
            })
        except Exception:
            _logger.exception('[COTIZACION][%s] ERROR registrando solicitud | tipo=%s',
                              trace, tipo)
            return form_error('No fue posible registrar la solicitud. Inténtelo nuevamente.')
