# -*- coding: utf-8 -*-
import base64
import logging
import re
import uuid
from datetime import timedelta

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LibroReclamaciones(models.Model):
    _name = "libro.reclamaciones"
    _description = "Libro de Reclamaciones"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_reclamo desc, id desc"

    name = fields.Char(string="N.º Hoja", default="Nuevo", readonly=True, copy=False, index=True, tracking=True)
    active = fields.Boolean(string="Activo", default=True)
    tipo_hoja = fields.Selection([("virtual", "Hoja de Reclamación Virtual")], string="Tipo de hoja", default="virtual", required=True, tracking=True)
    state = fields.Selection([("draft", "Borrador"), ("submitted", "Registrado"), ("review", "En revisión"), ("answered", "Respondido"), ("closed", "Cerrado"), ("cancelled", "Anulado")], string="Estado", default="draft", required=True, tracking=True, index=True)

    company_id = fields.Many2one("res.company", string="Empresa", default=lambda self: self.env.company, required=True, tracking=True)
    website_id = fields.Many2one("website", string="Sitio web", copy=False)
    proveedor_razon_social = fields.Char(string="Proveedor", related="company_id.name", store=True, readonly=True)
    proveedor_ruc = fields.Char(string="RUC", related="company_id.vat", store=True, readonly=True)
    proveedor_domicilio = fields.Char(string="Domicilio del proveedor", compute="_compute_proveedor_domicilio", store=True)

    fecha_reclamo = fields.Datetime(string="Fecha de reclamación", default=fields.Datetime.now, required=True, readonly=True, tracking=True)
    fecha_reclamo_date = fields.Date(string="Fecha", compute="_compute_fecha_reclamo_date", store=True, index=True)
    fecha_limite_respuesta = fields.Date(string="Fecha límite de respuesta", compute="_compute_fecha_limite_respuesta", store=True, index=True)
    dias_para_vencer = fields.Integer(string="Días para vencer", compute="_compute_plazo")
    vencido = fields.Boolean(string="Vencido", compute="_compute_plazo")

    tipo_documento = fields.Selection([("dni", "DNI"), ("ruc", "RUC"), ("ce", "Carné de extranjería"), ("pasaporte", "Pasaporte")], string="Tipo de documento", default="dni", required=True, tracking=True)
    numero_documento = fields.Char(string="Número de documento", required=True, tracking=True, index=True)
    nombre_consumidor = fields.Char(string="Nombre completo", required=True, tracking=True)
    nombres = fields.Char(string="Nombres", readonly=True)
    apellido_paterno = fields.Char(string="Apellido paterno", readonly=True)
    apellido_materno = fields.Char(string="Apellido materno", readonly=True)
    domicilio_consumidor = fields.Char(string="Domicilio", required=True)
    telefono = fields.Char(string="Teléfono", required=True)
    email = fields.Char(string="Correo electrónico", required=True)
    representante_menor_nombre = fields.Char(string="Padre, madre o apoderado")
    es_menor_edad = fields.Boolean(string="Reclamante menor de edad", compute="_compute_es_menor_edad", store=True)
    partner_id = fields.Many2one("res.partner", string="Contacto", copy=False)

    documento_consultado = fields.Boolean(string="Documento consultado", default=False, readonly=True)
    documento_encontrado = fields.Boolean(string="Documento encontrado", default=False, readonly=True)
    ingreso_manual = fields.Boolean(string="Ingreso manual", default=False, readonly=True)
    consulta_documento_estado = fields.Selection([("sin_consulta", "Sin consulta"), ("ok", "Encontrado"), ("no_encontrado", "No encontrado"), ("error", "Error")], string="Estado consulta", default="sin_consulta", readonly=True)
    consulta_documento_mensaje = fields.Char(string="Mensaje consulta", readonly=True)
    fecha_consulta_documento = fields.Datetime(string="Fecha consulta", readonly=True)

    tipo_bien = fields.Selection([("producto", "Producto"), ("servicio", "Servicio")], string="Bien contratado", required=True, tracking=True)
    currency_id = fields.Many2one("res.currency", string="Moneda", required=True, default=lambda self: self._default_currency())
    monto_reclamado = fields.Monetary(string="Monto reclamado", currency_field="currency_id", digits=(16, 2), tracking=True)
    descripcion_bien = fields.Text(string="Descripción", required=True)
    product_id = fields.Many2one("product.product", string="Producto / Servicio")
    numero_documento_comercial = fields.Char(string="Comprobante / documento")

    tipo_reclamacion = fields.Selection([("reclamo", "Reclamo"), ("queja", "Queja")], string="Tipo", required=True, tracking=True)
    detalle = fields.Text(string="Detalle", required=True)
    pedido_consumidor = fields.Text(string="Pedido del consumidor", required=True)
    firma_consumidor = fields.Binary(string="Firma del consumidor", attachment=True, required=True)
    firma_consumidor_filename = fields.Char(string="Nombre archivo firma consumidor")

    responsable_id = fields.Many2one("res.users", string="Responsable", tracking=True)
    fecha_inicio_revision = fields.Datetime(string="Inicio de revisión", readonly=True)
    observaciones_proveedor = fields.Html(string="Observaciones del proveedor")
    acciones_adoptadas = fields.Html(string="Acciones adoptadas")
    respuesta = fields.Html(string="Respuesta")
    fecha_comunicacion_respuesta = fields.Datetime(string="Fecha de comunicación", readonly=True, tracking=True)
    usuario_respuesta_id = fields.Many2one("res.users", string="Respondido por", readonly=True)
    firma_proveedor = fields.Binary(string="Firma del proveedor", attachment=True)
    firma_proveedor_filename = fields.Char(string="Nombre archivo firma proveedor")
    respuesta_enviada = fields.Boolean(string="Respuesta enviada", default=False, readonly=True)
    respuesta_email = fields.Char(string="Correo de respuesta", readonly=True)
    fecha_cierre = fields.Datetime(string="Fecha de cierre", readonly=True)

    attachment_ids = fields.Many2many("ir.attachment", "libro_reclamaciones_attachment_rel", "reclamacion_id", "attachment_id", string="Adjuntos")

    constancia_enviada = fields.Boolean(string="Constancia enviada", default=False, readonly=True)
    fecha_envio_constancia = fields.Datetime(string="Fecha envío constancia", readonly=True)

    acepta_declaracion = fields.Boolean(string="Acepta declaración", default=False)
    acepta_privacidad = fields.Boolean(string="Acepta privacidad", default=False)

    origen = fields.Selection([("website", "Página web"), ("backend", "Interno")], string="Origen", default="backend", required=True, readonly=True)
    ip_address = fields.Char(string="IP", readonly=True)
    user_agent = fields.Char(string="Navegador", readonly=True)
    public_token = fields.Char(string="Token público", copy=False, index=True, readonly=True)

    @api.model
    def _default_currency(self):
        currency = self.env["res.currency"].search([("name", "=", "PEN")], limit=1)
        return currency or self.env.company.currency_id

    @api.depends("company_id", "company_id.street", "company_id.street2", "company_id.city", "company_id.state_id", "company_id.country_id")
    def _compute_proveedor_domicilio(self):
        for record in self:
            company = record.company_id
            parts = [company.street, company.street2, company.city, company.state_id.name if company.state_id else False, company.country_id.name if company.country_id else False]
            record.proveedor_domicilio = ", ".join([p for p in parts if p])

    @api.depends("fecha_reclamo")
    def _compute_fecha_reclamo_date(self):
        for record in self:
            record.fecha_reclamo_date = fields.Date.to_date(record.fecha_reclamo) if record.fecha_reclamo else False

    @api.depends("representante_menor_nombre")
    def _compute_es_menor_edad(self):
        for record in self:
            record.es_menor_edad = bool((record.representante_menor_nombre or "").strip())

    @api.depends("fecha_reclamo_date")
    def _compute_fecha_limite_respuesta(self):
        for record in self:
            if not record.fecha_reclamo_date:
                record.fecha_limite_respuesta = False
                continue
            date_cursor = record.fecha_reclamo_date
            business_days = 0
            while business_days < 15:
                date_cursor += timedelta(days=1)
                if date_cursor.weekday() < 5:
                    business_days += 1
            record.fecha_limite_respuesta = date_cursor

    @api.depends("fecha_limite_respuesta", "state")
    def _compute_plazo(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.fecha_limite_respuesta:
                record.dias_para_vencer = 0
                record.vencido = False
                continue
            delta = (record.fecha_limite_respuesta - today).days
            record.dias_para_vencer = delta
            record.vencido = delta < 0 and record.state in ("submitted", "review")

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nuevo":
                vals["name"] = sequence.next_by_code("libro.reclamaciones") or "Nuevo"
            if not vals.get("public_token"):
                vals["public_token"] = uuid.uuid4().hex
        return super().create(vals_list)

    def _decolecta_token(self):
        return self.env["ir.config_parameter"].sudo().get_param("pc_l10n_pe_vat_sunat.decolecta_token")

    @api.model
    def consultar_dni(self, numero):
        numero = re.sub(r"\D", "", numero or "")
        if len(numero) != 8:
            return {"ok": False, "message": "Ingrese un DNI válido de 8 dígitos."}
        token = self._decolecta_token()
        if not token:
            return {"ok": False, "message": "La consulta de DNI no está disponible temporalmente."}
        try:
            response = requests.get("https://api.decolecta.com/v1/reniec/dni", params={"numero": numero}, headers={"Authorization": "Bearer %s" % token}, timeout=15)
            _logger.info("[LIBRO RECLAMACIONES] Decolecta endpoint=/v1/reniec/dni HTTP=%s", response.status_code)
            if response.status_code != 200:
                return {"ok": False, "message": "No fue posible consultar el DNI."}
            data = response.json() or {}
            full_name = (data.get("full_name") or "").strip()
            if not full_name:
                full_name = " ".join(filter(None, [data.get("first_name"), data.get("first_last_name"), data.get("second_last_name")])).strip()
            if not full_name:
                return {"ok": False, "message": "No se encontró información para el DNI ingresado."}
            return {
                "ok": True,
                "numero": data.get("document_number") or numero,
                "nombre": full_name,
                "nombres": data.get("first_name") or "",
                "apellido_paterno": data.get("first_last_name") or "",
                "apellido_materno": data.get("second_last_name") or "",
            }
        except Exception:
            _logger.exception("[LIBRO RECLAMACIONES] Error consultando DNI")
            return {"ok": False, "message": "No fue posible consultar el DNI en este momento."}


    @api.model
    def consultar_ruc(self, numero):
        numero = re.sub(r"\D", "", numero or "")
        if len(numero) != 11:
            return {"ok": False, "message": "Ingrese un RUC válido de 11 dígitos."}

        token = self._decolecta_token()
        if not token:
            return {"ok": False, "message": "La consulta de RUC no está disponible temporalmente."}

        try:
            response = requests.get(
                "https://api.decolecta.com/v1/sunat/ruc",
                params={"numero": numero},
                headers={"Authorization": "Bearer %s" % token},
                timeout=15,
            )
            _logger.info(
                "[LIBRO RECLAMACIONES] Decolecta endpoint=/v1/sunat/ruc HTTP=%s",
                response.status_code,
            )

            if response.status_code != 200:
                return {"ok": False, "message": "No fue posible consultar el RUC."}

            data = response.json() or {}
            razon_social = (data.get("razon_social") or "").strip()
            direccion = (
                data.get("direccion")
                or data.get("dirección")
                or ""
            ).strip()

            if not razon_social:
                return {"ok": False, "message": "No se encontró información para el RUC ingresado."}

            return {
                "ok": True,
                "numero": data.get("numero_documento") or numero,
                "nombre": razon_social,
                "razon_social": razon_social,
                "direccion": direccion,
                "estado": data.get("estado") or "",
                "condicion": data.get("condicion") or "",
            }

        except Exception:
            _logger.exception("[LIBRO RECLAMACIONES] Error consultando RUC")
            return {"ok": False, "message": "No fue posible consultar el RUC en este momento."}

    def action_consultar_documento(self):
        self.ensure_one()

        if self.tipo_documento == "dni":
            result = self.consultar_dni(self.numero_documento)
        elif self.tipo_documento == "ruc":
            result = self.consultar_ruc(self.numero_documento)
        else:
            self.write({
                "documento_consultado": False,
                "documento_encontrado": False,
                "ingreso_manual": True,
                "consulta_documento_estado": "sin_consulta",
                "consulta_documento_mensaje": "El documento se registra manualmente.",
            })
            return True
        vals = {
            "documento_consultado": True,
            "documento_encontrado": bool(result.get("ok")),
            "ingreso_manual": not bool(result.get("ok")),
            "fecha_consulta_documento": fields.Datetime.now(),
            "consulta_documento_estado": "ok" if result.get("ok") else "no_encontrado",
            "consulta_documento_mensaje": result.get("message") or "",
        }
        if result.get("ok"):
            vals.update({
                "nombre_consumidor": result.get("nombre"),
                "nombres": result.get("nombres") or "",
                "apellido_paterno": result.get("apellido_paterno") or "",
                "apellido_materno": result.get("apellido_materno") or "",
            })
            if self.tipo_documento == "ruc" and result.get("direccion"):
                vals["domicilio_consumidor"] = result.get("direccion")
        self.write(vals)
        return True

    def _validar_para_registro(self):
        for record in self:
            missing = []
            checks = [
                ("Tipo de documento", record.tipo_documento),
                ("Número de documento", record.numero_documento),
                ("Nombre completo", record.nombre_consumidor),
                ("Domicilio", record.domicilio_consumidor),
                ("Teléfono", record.telefono),
                ("Correo electrónico", record.email),
                ("Producto o servicio", record.tipo_bien),
                ("Descripción", record.descripcion_bien),
                ("Tipo de reclamación", record.tipo_reclamacion),
                ("Detalle", record.detalle),
                ("Pedido", record.pedido_consumidor),
                ("Firma", record.firma_consumidor),
            ]
            for label, value in checks:
                if not value:
                    missing.append(label)
            if not record.acepta_declaracion:
                missing.append("Declaración")
            if not record.acepta_privacidad:
                missing.append("Política de privacidad")
            if missing:
                raise ValidationError(_("Falta completar: %s") % ", ".join(missing))

    def action_submit(self):
        for record in self:
            record._validar_para_registro()
            record.write({"state": "submitted"})
        return True

    def action_start_review(self):
        for record in self:
            record.write({"state": "review", "fecha_inicio_revision": fields.Datetime.now(), "responsable_id": record.responsable_id.id or self.env.user.id})
        return True

    def action_marcar_respondido(self):
        for record in self:
            if not record.respuesta:
                raise UserError(_("Debe registrar la respuesta al consumidor."))
            record.write({"state": "answered", "fecha_comunicacion_respuesta": fields.Datetime.now(), "usuario_respuesta_id": self.env.user.id})
        return True

    def action_enviar_respuesta_email(self):
        for record in self:
            if not record.email:
                raise UserError(_("El consumidor no tiene correo electrónico."))
            if not record.respuesta:
                raise UserError(_("Debe registrar la respuesta antes de enviarla."))
            body = record.respuesta
            mail = self.env["mail.mail"].sudo().create({
                "subject": "Respuesta - %s" % record.name,
                "email_to": record.email,
                "body_html": body,
                "auto_delete": True,
            })
            mail.send()
            record.write({
                "respuesta_enviada": True,
                "respuesta_email": record.email,
                "fecha_comunicacion_respuesta": fields.Datetime.now(),
                "usuario_respuesta_id": self.env.user.id,
                "state": "answered",
            })
        return True

    def action_close(self):
        self.write({"state": "closed", "fecha_cierre": fields.Datetime.now()})
        return True

    def action_reopen(self):
        self.write({"state": "review", "fecha_cierre": False})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    @api.model
    def _cron_alertar_reclamos_por_vencer(self):
        today = fields.Date.context_today(self)
        limit_date = today + timedelta(days=3)
        records = self.search([("state", "in", ("submitted", "review")), ("fecha_limite_respuesta", ">=", today), ("fecha_limite_respuesta", "<=", limit_date)])
        for record in records:
            if record.responsable_id:
                record.activity_schedule("mail.mail_activity_data_todo", user_id=record.responsable_id.id, summary="Reclamación próxima a vencer", note="La reclamación %s vence el %s." % (record.name, record.fecha_limite_respuesta))
        return True

    @api.model
    def _cron_alertar_reclamos_vencidos(self):
        today = fields.Date.context_today(self)
        records = self.search([("state", "in", ("submitted", "review")), ("fecha_limite_respuesta", "<", today)])
        for record in records:
            if record.responsable_id:
                record.activity_schedule("mail.mail_activity_data_todo", user_id=record.responsable_id.id, summary="Reclamación vencida", note="La reclamación %s superó la fecha límite de respuesta." % record.name)
        return True
