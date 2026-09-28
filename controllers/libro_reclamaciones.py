# -*- coding: utf-8 -*-
import base64
import binascii
import logging
import re

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LibroReclamacionesController(http.Controller):

    @staticmethod
    def _clean(value):
        return (value or "").strip()

    @staticmethod
    def _data_url_to_base64(value):
        value = (value or "").strip()
        if not value:
            return False
        match = re.match(r"^data:image/(?:png|jpeg|jpg);base64,(.+)$", value, flags=re.I | re.S)
        if not match:
            return False
        payload = match.group(1).strip()
        try:
            base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            return False
        return payload.encode("ascii")

    @staticmethod
    def _currency_from_code(code):
        code = (code or "PEN").strip().upper()
        if code not in ("PEN", "USD"):
            code = "PEN"
        return request.env["res.currency"].sudo().search([("name", "=", code), ("active", "=", True)], limit=1)

    @http.route("/libro-de-reclamaciones", type="http", auth="public", website=True, methods=["GET"], sitemap=True)
    def libro_reclamaciones_form(self, **kwargs):
        currencies = request.env["res.currency"].sudo().search([("name", "in", ["PEN", "USD"]), ("active", "=", True)])
        currency_map = {c.name: c for c in currencies}
        values = {
            "currency_pen": currency_map.get("PEN"),
            "currency_usd": currency_map.get("USD"),
            "error": kwargs.get("error"),
        }
        return request.render("copier_company.libro_reclamaciones_form", values)

    @http.route("/libro-de-reclamaciones/consultar-dni", type="jsonrpc", auth="public", website=True, csrf=False)
    def libro_reclamaciones_consultar_dni(self, numero=None, **kwargs):
        return request.env["libro.reclamaciones"].sudo().consultar_dni(numero)

    @http.route("/libro-de-reclamaciones/enviar", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def libro_reclamaciones_enviar(self, **post):
        Reclamacion = request.env["libro.reclamaciones"].sudo()

        tipo_documento = self._clean(post.get("tipo_documento")).lower()
        if tipo_documento not in ("dni", "ce", "pasaporte"):
            tipo_documento = "dni"

        numero_documento = self._clean(post.get("numero_documento"))
        nombre_consumidor = self._clean(post.get("nombre_consumidor"))
        currency = self._currency_from_code(post.get("currency_code"))

        try:
            monto = float((self._clean(post.get("monto_reclamado")) or "0").replace(",", ""))
        except ValueError:
            monto = 0.0

        signature = self._data_url_to_base64(post.get("firma_consumidor_data"))

        if not signature:
            currencies = request.env["res.currency"].sudo().search([("name", "in", ["PEN", "USD"]), ("active", "=", True)])
            currency_map = {c.name: c for c in currencies}
            return request.render("copier_company.libro_reclamaciones_form", {
                "currency_pen": currency_map.get("PEN"),
                "currency_usd": currency_map.get("USD"),
                "error": "Debe registrar su firma antes de enviar la reclamación.",
                "form_data": post,
            })

        dni_data = {}
        if tipo_documento == "dni" and len(re.sub(r"\D", "", numero_documento)) == 8:
            dni_data = Reclamacion.consultar_dni(numero_documento)
            if dni_data.get("ok") and not nombre_consumidor:
                nombre_consumidor = dni_data.get("nombre") or ""

        vals = {
            "state": "draft",
            "origen": "website",
            "website_id": request.website.id if request.website else False,
            "company_id": request.website.company_id.id if request.website and request.website.company_id else request.env.company.id,
            "fecha_reclamo": fields.Datetime.now(),
            "tipo_documento": tipo_documento,
            "numero_documento": numero_documento,
            "nombre_consumidor": nombre_consumidor,
            "nombres": dni_data.get("nombres") or "",
            "apellido_paterno": dni_data.get("apellido_paterno") or "",
            "apellido_materno": dni_data.get("apellido_materno") or "",
            "domicilio_consumidor": self._clean(post.get("domicilio_consumidor")),
            "telefono": self._clean(post.get("telefono")),
            "email": self._clean(post.get("email")),
            "representante_menor_nombre": self._clean(post.get("representante_menor_nombre")),
            "tipo_bien": self._clean(post.get("tipo_bien")),
            "currency_id": currency.id if currency else request.env.company.currency_id.id,
            "monto_reclamado": monto,
            "descripcion_bien": self._clean(post.get("descripcion_bien")),
            "numero_documento_comercial": self._clean(post.get("numero_documento_comercial")),
            "tipo_reclamacion": self._clean(post.get("tipo_reclamacion")),
            "detalle": self._clean(post.get("detalle")),
            "pedido_consumidor": self._clean(post.get("pedido_consumidor")),
            "firma_consumidor": signature,
            "firma_consumidor_filename": "firma_consumidor.png",
            "acepta_declaracion": post.get("acepta_declaracion") == "1",
            "acepta_privacidad": post.get("acepta_privacidad") == "1",
            "ip_address": request.httprequest.remote_addr,
            "user_agent": request.httprequest.headers.get("User-Agent", ""),
            "documento_consultado": tipo_documento == "dni",
            "documento_encontrado": bool(dni_data.get("ok")) if tipo_documento == "dni" else False,
            "ingreso_manual": tipo_documento != "dni" or not bool(dni_data.get("ok")),
            "consulta_documento_estado": "ok" if dni_data.get("ok") else ("no_encontrado" if tipo_documento == "dni" else "sin_consulta"),
            "consulta_documento_mensaje": dni_data.get("message") or "",
            "fecha_consulta_documento": fields.Datetime.now() if tipo_documento == "dni" else False,
        }

        try:
            with request.env.cr.savepoint():
                reclamacion = Reclamacion.create(vals)
                reclamacion._validar_para_registro()

                attachments = []
                uploaded_files = request.httprequest.files.getlist("adjuntos")
                for upload in uploaded_files[:10]:
                    if not upload or not upload.filename:
                        continue
                    content = upload.read()
                    if not content:
                        continue
                    if len(content) > 10 * 1024 * 1024:
                        continue
                    attachment = request.env["ir.attachment"].sudo().create({
                        "name": upload.filename,
                        "datas": base64.b64encode(content),
                        "res_model": "libro.reclamaciones",
                        "res_id": reclamacion.id,
                        "mimetype": upload.mimetype,
                    })
                    attachments.append(attachment.id)

                if attachments:
                    reclamacion.write({"attachment_ids": [(6, 0, attachments)]})

                reclamacion.action_submit()

        except Exception as exc:
            _logger.exception("[LIBRO RECLAMACIONES] No se pudo registrar la reclamación")
            currencies = request.env["res.currency"].sudo().search([("name", "in", ["PEN", "USD"]), ("active", "=", True)])
            currency_map = {c.name: c for c in currencies}
            message = getattr(exc, "name", False) or str(exc) or "No fue posible registrar la reclamación."
            return request.render("copier_company.libro_reclamaciones_form", {
                "currency_pen": currency_map.get("PEN"),
                "currency_usd": currency_map.get("USD"),
                "error": message,
                "form_data": post,
            })

        return request.redirect("/libro-de-reclamaciones/confirmacion/%s" % reclamacion.public_token)

    @http.route("/libro-de-reclamaciones/confirmacion/<string:token>", type="http", auth="public", website=True, methods=["GET"])
    def libro_reclamaciones_confirmacion(self, token, **kwargs):
        reclamacion = request.env["libro.reclamaciones"].sudo().search([("public_token", "=", token)], limit=1)
        if not reclamacion:
            return request.not_found()
        return request.render("copier_company.libro_reclamaciones_confirmacion", {"reclamacion": reclamacion})

    @http.route("/libro-de-reclamaciones/constancia/<string:token>", type="http", auth="public", website=True, methods=["GET"])
    def libro_reclamaciones_constancia(self, token, **kwargs):
        reclamacion = request.env["libro.reclamaciones"].sudo().search([("public_token", "=", token)], limit=1)
        if not reclamacion:
            return request.not_found()
        return request.render("copier_company.libro_reclamaciones_constancia", {"reclamacion": reclamacion})

    @http.route("/libro-de-reclamaciones/pdf/<string:token>", type="http", auth="public", website=True, methods=["GET"])
    def libro_reclamaciones_pdf(self, token, **kwargs):
        reclamacion = request.env["libro.reclamaciones"].sudo().search([("public_token", "=", token)], limit=1)
        if not reclamacion:
            return request.not_found()
        report = request.env.ref("copier_company.action_report_libro_reclamaciones").sudo()
        pdf_content, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(report.report_name, res_ids=[reclamacion.id])
        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf_content)),
            ("Content-Disposition", 'inline; filename="%s.pdf"' % reclamacion.name.replace("/", "-")),
        ]
        return request.make_response(pdf_content, headers=headers)

    @http.route("/libro-de-reclamaciones/descargar/<string:token>", type="http", auth="public", website=True, methods=["GET"])
    def libro_reclamaciones_descargar(self, token, **kwargs):
        reclamacion = request.env["libro.reclamaciones"].sudo().search([("public_token", "=", token)], limit=1)
        if not reclamacion:
            return request.not_found()
        report = request.env.ref("copier_company.action_report_libro_reclamaciones").sudo()
        pdf_content, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(report.report_name, res_ids=[reclamacion.id])
        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf_content)),
            ("Content-Disposition", 'attachment; filename="%s.pdf"' % reclamacion.name.replace("/", "-")),
        ]
        return request.make_response(pdf_content, headers=headers)
