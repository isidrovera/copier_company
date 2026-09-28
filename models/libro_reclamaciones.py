# -*- coding: utf-8 -*-

import base64
import logging
import re
import uuid
from datetime import datetime, time, timedelta

import requests
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class LibroReclamaciones(models.Model):
    _name = "libro.reclamaciones"
    _description = "Libro de Reclamaciones"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "fecha_reclamo desc, id desc"

    # ============================================================
    # HOJA DE RECLAMACIÓN
    # ============================================================

    name = fields.Char(
        string="N.º de Hoja",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _("Nuevo"),
        tracking=True,
        index=True,
    )

    active = fields.Boolean(
        string="Activo",
        default=True,
    )

    tipo_hoja = fields.Selection(
        [
            ("virtual", "Hoja de Reclamación Virtual"),
        ],
        string="Tipo de hoja",
        required=True,
        default="virtual",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("submitted", "Registrado"),
            ("review", "En revisión"),
            ("answered", "Respondido"),
            ("closed", "Cerrado"),
            ("cancelled", "Anulado"),
        ],
        string="Estado",
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    # ============================================================
    # EMPRESA / PROVEEDOR
    # ============================================================

    company_id = fields.Many2one(
        "res.company",
        string="Proveedor",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        index=True,
    )

    proveedor_razon_social = fields.Char(
        string="Razón Social",
        related="company_id.name",
        readonly=True,
        store=True,
    )

    proveedor_ruc = fields.Char(
        string="RUC",
        related="company_id.vat",
        readonly=True,
        store=True,
    )

    proveedor_domicilio = fields.Char(
        string="Domicilio del proveedor",
        compute="_compute_proveedor_domicilio",
        store=True,
    )

    website_id = fields.Many2one(
        "website",
        string="Sitio web",
        index=True,
        help="Sitio web desde donde se presentó la reclamación.",
    )

    # ============================================================
    # FECHA
    # ============================================================

    fecha_reclamo = fields.Datetime(
        string="Fecha y hora",
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
        index=True,
    )

    fecha_reclamo_date = fields.Date(
        string="Fecha",
        compute="_compute_fecha_reclamo_date",
        store=True,
        index=True,
    )

    fecha_limite_respuesta = fields.Date(
        string="Fecha límite de respuesta",
        compute="_compute_fecha_limite_respuesta",
        store=True,
        tracking=True,
        help="Plazo referencial de 15 días hábiles desde el registro.",
    )

    dias_para_vencer = fields.Integer(
        string="Días para vencer",
        compute="_compute_estado_vencimiento",
    )

    vencido = fields.Boolean(
        string="Vencido",
        compute="_compute_estado_vencimiento",
    )

    # ============================================================
    # 1. IDENTIFICACIÓN DEL CONSUMIDOR
    # ============================================================

    tipo_documento = fields.Selection(
        [
            ("dni", "DNI"),
            ("ce", "Carné de Extranjería"),
        ],
        string="Tipo de documento",
        required=True,
        default="dni",
        tracking=True,
    )

    numero_documento = fields.Char(
        string="DNI / CE",
        required=True,
        tracking=True,
        index=True,
    )

    nombre_consumidor = fields.Char(
        string="Nombre del consumidor",
        required=True,
        tracking=True,
        index=True,
    )

    # Campos internos obtenidos desde la consulta DNI.
    # No es necesario mostrarlos en el formulario público.
    nombres = fields.Char(
        string="Nombres",
        readonly=True,
    )

    apellido_paterno = fields.Char(
        string="Apellido paterno",
        readonly=True,
    )

    apellido_materno = fields.Char(
        string="Apellido materno",
        readonly=True,
    )

    domicilio_consumidor = fields.Char(
        string="Domicilio",
        required=True,
        tracking=True,
    )

    telefono = fields.Char(
        string="Teléfono",
        required=True,
        tracking=True,
    )

    email = fields.Char(
        string="E-mail",
        required=True,
        tracking=True,
        index=True,
    )

    es_menor_edad = fields.Boolean(
        string="Es menor de edad",
        default=False,
        tracking=True,
    )

    representante_menor_nombre = fields.Char(
        string="Padre, madre o apoderado",
        tracking=True,
    )

    # ============================================================
    # CONSULTA DNI
    # ============================================================

    documento_consultado = fields.Boolean(
        string="Consulta automática realizada",
        readonly=True,
        default=False,
    )

    documento_encontrado = fields.Boolean(
        string="Documento encontrado",
        readonly=True,
        default=False,
    )

    ingreso_manual = fields.Boolean(
        string="Ingreso manual",
        readonly=True,
        default=False,
    )

    consulta_documento_estado = fields.Selection(
        [
            ("not_requested", "No consultado"),
            ("found", "Encontrado"),
            ("not_found", "No encontrado"),
            ("error", "Error"),
            ("manual", "Ingreso manual"),
        ],
        string="Estado de consulta",
        default="not_requested",
        readonly=True,
        tracking=True,
    )

    consulta_documento_mensaje = fields.Char(
        string="Resultado de consulta",
        readonly=True,
    )

    fecha_consulta_documento = fields.Datetime(
        string="Fecha de consulta",
        readonly=True,
    )

    # ============================================================
    # 2. IDENTIFICACIÓN DEL BIEN CONTRATADO
    # ============================================================

    tipo_bien = fields.Selection(
        [
            ("producto", "Producto"),
            ("servicio", "Servicio"),
        ],
        string="Bien contratado",
        required=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )

    monto_reclamado = fields.Monetary(
        string="Monto reclamado",
        currency_field="currency_id",
        tracking=True,
    )

    descripcion_bien = fields.Text(
        string="Descripción del producto o servicio",
        required=True,
        tracking=True,
    )

    # Opcionales internos para relacionar el reclamo con Odoo.
    product_id = fields.Many2one(
        "product.product",
        string="Producto relacionado",
        tracking=True,
    )

    numero_documento_comercial = fields.Char(
        string="Pedido / Factura / Cotización",
        tracking=True,
    )

    # ============================================================
    # 3. DETALLE DE LA RECLAMACIÓN
    # ============================================================

    tipo_reclamacion = fields.Selection(
        [
            ("reclamo", "Reclamo"),
            ("queja", "Queja"),
        ],
        string="Tipo",
        required=True,
        tracking=True,
        index=True,
        help=(
            "Reclamo: disconformidad relacionada con productos o servicios. "
            "Queja: malestar o descontento respecto de la atención al público "
            "u otra situación no relacionada directamente con el producto "
            "o servicio."
        ),
    )

    detalle = fields.Text(
        string="Detalle",
        required=True,
        tracking=True,
    )

    pedido_consumidor = fields.Text(
        string="Pedido del consumidor",
        required=True,
        tracking=True,
    )

    firma_consumidor = fields.Binary(
        string="Firma del consumidor",
        attachment=True,
    )

    firma_consumidor_filename = fields.Char(
        string="Archivo de firma del consumidor",
        default="firma_consumidor.png",
    )

    # ============================================================
    # 4. OBSERVACIONES Y ACCIONES DEL PROVEEDOR
    # ============================================================

    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        tracking=True,
        domain=[("share", "=", False)],
    )

    fecha_inicio_revision = fields.Datetime(
        string="Inicio de revisión",
        readonly=True,
        tracking=True,
    )

    observaciones_proveedor = fields.Html(
        string="Observaciones del proveedor",
        sanitize=True,
        tracking=True,
    )

    acciones_adoptadas = fields.Html(
        string="Acciones adoptadas",
        sanitize=True,
        tracking=True,
    )

    respuesta = fields.Html(
        string="Respuesta al consumidor",
        sanitize=True,
        tracking=True,
    )

    fecha_comunicacion_respuesta = fields.Datetime(
        string="Fecha de comunicación de la respuesta",
        readonly=True,
        tracking=True,
    )

    usuario_respuesta_id = fields.Many2one(
        "res.users",
        string="Respondido por",
        readonly=True,
        tracking=True,
    )

    firma_proveedor = fields.Binary(
        string="Firma del proveedor",
        attachment=True,
    )

    firma_proveedor_filename = fields.Char(
        string="Archivo de firma del proveedor",
        default="firma_proveedor.png",
    )

    respuesta_enviada = fields.Boolean(
        string="Respuesta enviada",
        default=False,
        readonly=True,
        tracking=True,
    )

    respuesta_email = fields.Char(
        string="E-mail de respuesta",
        readonly=True,
    )

    fecha_cierre = fields.Datetime(
        string="Fecha de cierre",
        readonly=True,
        tracking=True,
    )

    # ============================================================
    # ARCHIVOS ADJUNTOS
    # ============================================================

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "libro_reclamaciones_attachment_rel",
        "reclamacion_id",
        "attachment_id",
        string="Archivos adjuntos",
    )

    # ============================================================
    # CONTACTO ODOO
    # ============================================================

    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto relacionado",
        tracking=True,
        index=True,
    )

    # ============================================================
    # CONSTANCIA
    # ============================================================

    constancia_enviada = fields.Boolean(
        string="Constancia enviada",
        default=False,
        readonly=True,
    )

    fecha_envio_constancia = fields.Datetime(
        string="Fecha de envío de constancia",
        readonly=True,
    )

    # ============================================================
    # DECLARACIONES
    # ============================================================

    acepta_declaracion = fields.Boolean(
        string="Declaración de veracidad",
        default=False,
    )

    acepta_privacidad = fields.Boolean(
        string="Aceptó política de privacidad",
        default=False,
    )

    # ============================================================
    # AUDITORÍA WEB
    # ============================================================

    origen = fields.Selection(
        [
            ("website", "Página web"),
            ("backend", "Odoo"),
            ("import", "Importado"),
        ],
        string="Origen",
        required=True,
        default="backend",
        readonly=True,
        index=True,
    )

    ip_address = fields.Char(
        string="Dirección IP",
        readonly=True,
    )

    user_agent = fields.Char(
        string="Navegador / Dispositivo",
        readonly=True,
    )

    public_token = fields.Char(
        string="Token público",
        readonly=True,
        copy=False,
        index=True,
    )

    # ============================================================
    # COMPUTE: PROVEEDOR
    # ============================================================

    @api.depends(
        "company_id.street",
        "company_id.street2",
        "company_id.city",
        "company_id.state_id",
        "company_id.country_id",
    )
    def _compute_proveedor_domicilio(self):
        for record in self:
            company = record.company_id

            partes = []

            if company.street:
                partes.append(company.street)

            if company.street2:
                partes.append(company.street2)

            if company.city:
                partes.append(company.city)

            if company.state_id:
                partes.append(company.state_id.name)

            if company.country_id:
                partes.append(company.country_id.name)

            record.proveedor_domicilio = ", ".join(
                parte.strip()
                for parte in partes
                if parte
            )

    # ============================================================
    # COMPUTE: FECHA
    # ============================================================

    @api.depends("fecha_reclamo")
    def _compute_fecha_reclamo_date(self):
        for record in self:
            record.fecha_reclamo_date = (
                fields.Date.to_date(record.fecha_reclamo)
                if record.fecha_reclamo
                else False
            )

    @api.depends(
        "fecha_reclamo",
        "company_id",
    )
    def _compute_fecha_limite_respuesta(self):
        for record in self:
            if not record.fecha_reclamo:
                record.fecha_limite_respuesta = False
                continue

            fecha_inicio = fields.Date.to_date(
                record.fecha_reclamo
            )

            record.fecha_limite_respuesta = (
                record._sumar_dias_habiles(
                    fecha_inicio,
                    15,
                )
            )

    @api.depends(
        "fecha_limite_respuesta",
        "state",
    )
    def _compute_estado_vencimiento(self):
        hoy = fields.Date.context_today(self)

        for record in self:
            if (
                not record.fecha_limite_respuesta
                or record.state in (
                    "answered",
                    "closed",
                    "cancelled",
                )
            ):
                record.dias_para_vencer = 0
                record.vencido = False
                continue

            diferencia = (
                record.fecha_limite_respuesta - hoy
            ).days

            record.dias_para_vencer = diferencia
            record.vencido = diferencia < 0

    # ============================================================
    # DÍAS HÁBILES
    # ============================================================

    def _sumar_dias_habiles(
        self,
        fecha_inicio,
        cantidad,
    ):
        """
        Calcula días hábiles.

        - Excluye sábados y domingos.
        - Si el calendario de la empresa tiene días no laborables
          globales configurados, también los excluye.
        """

        self.ensure_one()

        fecha = fecha_inicio
        contador = 0

        while contador < cantidad:
            fecha += timedelta(days=1)

            if fecha.weekday() >= 5:
                continue

            if self._es_dia_no_laborable(fecha):
                continue

            contador += 1

        return fecha

    def _es_dia_no_laborable(self, fecha):
        """
        Comprueba si el calendario de la empresa tiene un día
        no laborable global que cubra la fecha.
        """

        self.ensure_one()

        calendar = self.company_id.resource_calendar_id

        if not calendar:
            return False

        tz_name = (
            calendar.tz
            or self.env.user.tz
            or "UTC"
        )

        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC

        inicio_local = tz.localize(
            datetime.combine(
                fecha,
                time.min,
            )
        )

        fin_local = tz.localize(
            datetime.combine(
                fecha,
                time.max,
            )
        )

        inicio_utc = inicio_local.astimezone(
            pytz.UTC
        ).replace(tzinfo=None)

        fin_utc = fin_local.astimezone(
            pytz.UTC
        ).replace(tzinfo=None)

        Leave = self.env[
            "resource.calendar.leaves"
        ].sudo()

        dominio = [
            ("calendar_id", "=", calendar.id),
            ("resource_id", "=", False),
            ("date_from", "<=", fin_utc),
            ("date_to", ">=", inicio_utc),
        ]

        return bool(
            Leave.search_count(dominio)
        )

    # ============================================================
    # VALIDACIONES DOCUMENTO
    # ============================================================

    @api.constrains(
        "tipo_documento",
        "numero_documento",
    )
    def _check_documento(self):
        for record in self:
            numero = (
                record.numero_documento
                or ""
            ).strip()

            if not numero:
                continue

            if record.tipo_documento == "dni":
                if not re.fullmatch(
                    r"\d{8}",
                    numero,
                ):
                    raise ValidationError(
                        _(
                            "El DNI debe contener "
                            "exactamente 8 dígitos."
                        )
                    )

            elif record.tipo_documento == "ce":
                if len(numero) < 4:
                    raise ValidationError(
                        _(
                            "Ingrese un número de Carné "
                            "de Extranjería válido."
                        )
                    )

    @api.constrains("email")
    def _check_email(self):
        patron = re.compile(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        for record in self:
            if record.email:
                email = record.email.strip()

                if not patron.match(email):
                    raise ValidationError(
                        _(
                            "Ingrese un correo electrónico válido."
                        )
                    )

    @api.constrains(
        "es_menor_edad",
        "representante_menor_nombre",
    )
    def _check_menor(self):
        for record in self:
            if (
                record.es_menor_edad
                and not record.representante_menor_nombre
            ):
                raise ValidationError(
                    _(
                        "Debe ingresar el nombre del padre, "
                        "madre o apoderado."
                    )
                )

    # ============================================================
    # ONCHANGE DOCUMENTO
    # ============================================================

    @api.onchange("tipo_documento")
    def _onchange_tipo_documento(self):
        for record in self:
            record.documento_consultado = False
            record.documento_encontrado = False
            record.ingreso_manual = False
            record.consulta_documento_mensaje = False
            record.fecha_consulta_documento = False

            if record.tipo_documento == "ce":
                record.consulta_documento_estado = "manual"
                record.ingreso_manual = True

                record.consulta_documento_mensaje = (
                    "Ingrese los datos manualmente."
                )

            else:
                record.consulta_documento_estado = (
                    "not_requested"
                )

    # ============================================================
    # SECUENCIA
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env[
            "ir.sequence"
        ]

        for vals in vals_list:
            if (
                not vals.get("name")
                or vals.get("name") == _("Nuevo")
            ):
                vals["name"] = (
                    sequence.next_by_code(
                        "libro.reclamaciones"
                    )
                    or _("Nuevo")
                )

            if not vals.get("public_token"):
                vals["public_token"] = (
                    uuid.uuid4().hex
                )

        return super().create(vals_list)

    # ============================================================
    # DECOLECTA
    # ============================================================

    @api.model
    def _get_decolecta_token(self):
        """
        Reutiliza exactamente el parámetro que ya utiliza
        el módulo de consulta DNI/RUC.
        """

        return (
            self.env[
                "ir.config_parameter"
            ]
            .sudo()
            .get_param(
                "pc_l10n_pe_vat_sunat.decolecta_token",
                "",
            )
            .strip()
        )

    @api.model
    def _decolecta_request(
        self,
        endpoint,
        params,
    ):
        """
        La consulta nunca debe impedir registrar una reclamación.

        Si Decolecta falla, devolvemos una respuesta controlada
        para permitir ingreso manual.
        """

        token = self._get_decolecta_token()

        if not token:
            _logger.error(
                "[LIBRO RECLAMACIONES] "
                "Token Decolecta no configurado."
            )

            return {
                "ok": False,
                "error": "token_missing",
                "message": (
                    "No fue posible consultar el DNI "
                    "automáticamente. Ingrese el nombre "
                    "manualmente."
                ),
            }

        url = (
            "https://api.decolecta.com%s"
            % endpoint
        )

        headers = {
            "Authorization": (
                "Bearer %s" % token
            ),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=(5, 20),
            )

        except requests.Timeout:
            _logger.warning(
                "[LIBRO RECLAMACIONES] "
                "Timeout Decolecta endpoint=%s",
                endpoint,
            )

            return {
                "ok": False,
                "error": "timeout",
                "message": (
                    "La consulta demoró demasiado. "
                    "Ingrese el nombre manualmente."
                ),
            }

        except requests.RequestException as exc:
            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "Error conexión Decolecta: %s",
                exc,
            )

            return {
                "ok": False,
                "error": "connection",
                "message": (
                    "No se pudo conectar con el servicio "
                    "de consulta. Ingrese el nombre "
                    "manualmente."
                ),
            }

        status = response.status_code

        _logger.info(
            "[LIBRO RECLAMACIONES] "
            "Decolecta endpoint=%s HTTP=%s",
            endpoint,
            status,
        )

        if status == 404:
            return {
                "ok": False,
                "error": "not_found",
                "message": (
                    "No se encontraron datos para el DNI. "
                    "Ingrese el nombre manualmente."
                ),
            }

        if status in (401, 403):
            _logger.error(
                "[LIBRO RECLAMACIONES] "
                "Decolecta autorización HTTP=%s",
                status,
            )

            return {
                "ok": False,
                "error": "authorization",
                "message": (
                    "No fue posible consultar el DNI. "
                    "Ingrese el nombre manualmente."
                ),
            }

        if status == 422:
            return {
                "ok": False,
                "error": "invalid_document",
                "message": (
                    "El DNI no pudo validarse. "
                    "Ingrese los datos manualmente."
                ),
            }

        if status == 429:
            return {
                "ok": False,
                "error": "rate_limit",
                "message": (
                    "El servicio de consulta no está "
                    "disponible temporalmente. "
                    "Ingrese el nombre manualmente."
                ),
            }

        if status >= 500:
            return {
                "ok": False,
                "error": "server_error",
                "message": (
                    "El servicio de consulta no está "
                    "disponible temporalmente. "
                    "Ingrese el nombre manualmente."
                ),
            }

        if status != 200:
            return {
                "ok": False,
                "error": "http_error",
                "message": (
                    "No fue posible consultar el DNI. "
                    "Ingrese el nombre manualmente."
                ),
            }

        try:
            data = response.json()

        except ValueError:
            _logger.error(
                "[LIBRO RECLAMACIONES] "
                "Respuesta Decolecta no JSON."
            )

            return {
                "ok": False,
                "error": "invalid_json",
                "message": (
                    "No fue posible procesar la consulta. "
                    "Ingrese el nombre manualmente."
                ),
            }

        if not isinstance(data, dict):
            return {
                "ok": False,
                "error": "invalid_format",
                "message": (
                    "No fue posible procesar la consulta. "
                    "Ingrese el nombre manualmente."
                ),
            }

        return {
            "ok": True,
            "data": data,
        }

    # ============================================================
    # CONSULTAR DNI
    # ============================================================

    @api.model
    def consultar_dni_publico(
        self,
        numero_documento,
    ):
        """
        Método preparado para ser llamado por el controller web.

        Ejemplo:
            libro.reclamaciones
                .sudo()
                .consultar_dni_publico("70619052")
        """

        numero = (
            str(numero_documento or "")
            .strip()
        )

        if not re.fullmatch(
            r"\d{8}",
            numero,
        ):
            return {
                "ok": False,
                "manual": True,
                "error": "invalid_length",
                "message": (
                    "El DNI debe contener exactamente "
                    "8 dígitos."
                ),
            }

        resultado = self._decolecta_request(
            "/v1/reniec/dni",
            {
                "numero": numero,
            },
        )

        if not resultado.get("ok"):
            resultado["manual"] = True
            return resultado

        data = (
            resultado.get("data")
            or {}
        )

        first_name = (
            data.get("first_name")
            or data.get("nombres")
            or ""
        ).strip()

        first_last_name = (
            data.get("first_last_name")
            or data.get("apellido_paterno")
            or data.get("apellidoPaterno")
            or ""
        ).strip()

        second_last_name = (
            data.get("second_last_name")
            or data.get("apellido_materno")
            or data.get("apellidoMaterno")
            or ""
        ).strip()

        full_name = (
            data.get("full_name")
            or ""
        ).strip()

        document_number = str(
            data.get("document_number")
            or ""
        ).strip()

        if (
            document_number
            and document_number != numero
        ):
            _logger.error(
                "[LIBRO DNI] "
                "Documento no coincide. "
                "solicitado=%s recibido=%s",
                numero,
                document_number,
            )

            return {
                "ok": False,
                "manual": True,
                "error": "document_mismatch",
                "message": (
                    "La respuesta recibida no corresponde "
                    "al DNI consultado. Ingrese los datos "
                    "manualmente."
                ),
            }

        nombre_completo = " ".join(
            valor
            for valor in [
                first_name,
                first_last_name,
                second_last_name,
            ]
            if valor
        ).strip()

        if not nombre_completo:
            nombre_completo = full_name

        if not nombre_completo:
            _logger.error(
                "[LIBRO DNI] "
                "DNI=%s sin nombres. data=%s",
                numero,
                data,
            )

            return {
                "ok": False,
                "manual": True,
                "error": "empty_name",
                "message": (
                    "El servicio encontró el DNI, pero "
                    "no devolvió el nombre. Ingréselo "
                    "manualmente."
                ),
            }

        return {
            "ok": True,
            "manual": False,
            "numero_documento": numero,
            "nombre": nombre_completo,
            "nombres": first_name,
            "apellido_paterno": first_last_name,
            "apellido_materno": second_last_name,
        }

    # ============================================================
    # CONSULTA DESDE BACKEND
    # ============================================================

    def action_consultar_documento(self):
        self.ensure_one()

        numero = (
            self.numero_documento
            or ""
        ).strip()

        if not numero:
            raise UserError(
                _(
                    "Ingrese el número de documento."
                )
            )

        # CE siempre manual
        if self.tipo_documento == "ce":
            self.write(
                {
                    "documento_consultado": False,
                    "documento_encontrado": False,
                    "ingreso_manual": True,
                    "consulta_documento_estado": "manual",
                    "consulta_documento_mensaje": (
                        "Ingrese los datos manualmente."
                    ),
                }
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Ingreso manual"),
                    "message": _(
                        "Para Carné de Extranjería "
                        "ingrese el nombre manualmente."
                    ),
                    "type": "info",
                    "sticky": False,
                },
            }

        resultado = self.consultar_dni_publico(
            numero
        )

        vals = {
            "documento_consultado": True,
            "fecha_consulta_documento": (
                fields.Datetime.now()
            ),
        }

        if not resultado.get("ok"):
            vals.update(
                {
                    "documento_encontrado": False,
                    "ingreso_manual": True,
                    "consulta_documento_estado": (
                        "not_found"
                        if resultado.get("error")
                        == "not_found"
                        else "error"
                    ),
                    "consulta_documento_mensaje": (
                        resultado.get("message")
                    ),
                }
            )

            self.write(vals)

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _(
                        "Ingrese el nombre manualmente"
                    ),
                    "message": (
                        resultado.get("message")
                    ),
                    "type": "warning",
                    "sticky": False,
                },
            }

        vals.update(
            {
                "nombre_consumidor": (
                    resultado["nombre"]
                ),
                "nombres": (
                    resultado.get("nombres")
                ),
                "apellido_paterno": (
                    resultado.get(
                        "apellido_paterno"
                    )
                ),
                "apellido_materno": (
                    resultado.get(
                        "apellido_materno"
                    )
                ),
                "documento_encontrado": True,
                "ingreso_manual": False,
                "consulta_documento_estado": "found",
                "consulta_documento_mensaje": (
                    "Datos obtenidos automáticamente."
                ),
            }
        )

        self.write(vals)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _(
                    "DNI encontrado"
                ),
                "message": _(
                    "El nombre fue cargado "
                    "automáticamente."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    # ============================================================
    # REGISTRO DEL RECLAMO
    # ============================================================

    def action_submit(self):
        for record in self:
            record._validar_para_registro()

            record.write(
                {
                    "state": "submitted",
                }
            )

            record.message_post(
                body=_(
                    "La Hoja de Reclamación "
                    "%s fue registrada."
                )
                % record.name
            )

        return True

    def _validar_para_registro(self):
        self.ensure_one()

        faltantes = []

        if not self.nombre_consumidor:
            faltantes.append(
                _("Nombre del consumidor")
            )

        if not self.tipo_documento:
            faltantes.append(
                _("Tipo de documento")
            )

        if not self.numero_documento:
            faltantes.append(
                _("DNI / CE")
            )

        if not self.domicilio_consumidor:
            faltantes.append(
                _("Domicilio")
            )

        if not self.telefono:
            faltantes.append(
                _("Teléfono")
            )

        if not self.email:
            faltantes.append(
                _("E-mail")
            )

        if (
            self.es_menor_edad
            and not self.representante_menor_nombre
        ):
            faltantes.append(
                _(
                    "Padre, madre o apoderado"
                )
            )

        if not self.tipo_bien:
            faltantes.append(
                _("Producto o servicio")
            )

        if not self.descripcion_bien:
            faltantes.append(
                _(
                    "Descripción del producto "
                    "o servicio"
                )
            )

        if not self.tipo_reclamacion:
            faltantes.append(
                _("Reclamo o queja")
            )

        if not self.detalle:
            faltantes.append(
                _("Detalle")
            )

        if not self.pedido_consumidor:
            faltantes.append(
                _("Pedido del consumidor")
            )

        if not self.firma_consumidor:
            faltantes.append(
                _("Firma del consumidor")
            )

        if not self.acepta_declaracion:
            faltantes.append(
                _("Declaración de veracidad")
            )

        if faltantes:
            raise ValidationError(
                _(
                    "Debe completar los siguientes "
                    "campos:\n\n- %s"
                )
                % "\n- ".join(faltantes)
            )

        return True

    # ============================================================
    # REVISIÓN
    # ============================================================

    def action_start_review(self):
        for record in self:
            if record.state not in (
                "submitted",
                "review",
            ):
                raise UserError(
                    _(
                        "Solo puede iniciar la revisión "
                        "de una reclamación registrada."
                    )
                )

            vals = {
                "state": "review",
            }

            if not record.fecha_inicio_revision:
                vals[
                    "fecha_inicio_revision"
                ] = fields.Datetime.now()

            if not record.responsable_id:
                vals[
                    "responsable_id"
                ] = self.env.user.id

            record.write(vals)

        return True

    # ============================================================
    # RESPUESTA
    # ============================================================

    def action_marcar_respondido(self):
        for record in self:
            if not record.respuesta:
                raise UserError(
                    _(
                        "Debe ingresar la respuesta "
                        "al consumidor."
                    )
                )

            if not record.acciones_adoptadas:
                raise UserError(
                    _(
                        "Debe registrar las acciones "
                        "adoptadas por el proveedor."
                    )
                )

            if not record.firma_proveedor:
                raise UserError(
                    _(
                        "Debe registrar la firma "
                        "del proveedor."
                    )
                )

            record.write(
                {
                    "state": "answered",
                    "fecha_comunicacion_respuesta": (
                        fields.Datetime.now()
                    ),
                    "usuario_respuesta_id": (
                        self.env.user.id
                    ),
                }
            )

            record.message_post(
                body=_(
                    "La Hoja de Reclamación "
                    "fue marcada como respondida."
                )
            )

        return True

    # ============================================================
    # ENVIAR RESPUESTA POR CORREO
    # ============================================================

    def action_enviar_respuesta_email(self):
        self.ensure_one()

        if not self.email:
            raise UserError(
                _(
                    "El consumidor no tiene "
                    "correo electrónico."
                )
            )

        if not self.respuesta:
            raise UserError(
                _(
                    "Ingrese la respuesta antes "
                    "de enviarla."
                )
            )

        if not self.acciones_adoptadas:
            raise UserError(
                _(
                    "Ingrese las acciones adoptadas "
                    "antes de enviar la respuesta."
                )
            )

        asunto = (
            "Respuesta Libro de Reclamaciones - %s"
            % self.name
        )

        body = """
            <p>Estimado(a) %s:</p>

            <p>
                En atención a su Hoja de Reclamación
                <strong>%s</strong>, presentamos nuestra
                respuesta:
            </p>

            %s

            <p><strong>Acciones adoptadas:</strong></p>

            %s

            <p>
                Atentamente,<br/>
                <strong>%s</strong>
            </p>
        """ % (
            self.nombre_consumidor,
            self.name,
            self.respuesta or "",
            self.acciones_adoptadas or "",
            self.company_id.name,
        )

        email_from = (
            self.company_id.email
            or self.env.user.email_formatted
        )

        if not email_from:
            raise UserError(
                _(
                    "Configure un correo electrónico "
                    "para la empresa."
                )
            )

        mail = self.env[
            "mail.mail"
        ].sudo().create(
            {
                "subject": asunto,
                "body_html": body,
                "email_to": self.email,
                "email_from": email_from,
                "auto_delete": False,
            }
        )

        try:
            mail.send()

        except Exception:
            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "Error enviando respuesta reclamo=%s",
                self.name,
            )

            raise UserError(
                _(
                    "No fue posible enviar la respuesta "
                    "por correo. Revise la configuración "
                    "del servidor de correo."
                )
            )

        ahora = fields.Datetime.now()

        self.write(
            {
                "state": "answered",
                "respuesta_enviada": True,
                "respuesta_email": self.email,
                "fecha_comunicacion_respuesta": ahora,
                "usuario_respuesta_id": (
                    self.env.user.id
                ),
            }
        )

        self.message_post(
            body=_(
                "Respuesta enviada al consumidor "
                "al correo %s."
            )
            % self.email
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Respuesta enviada"),
                "message": _(
                    "La respuesta fue enviada "
                    "correctamente al consumidor."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    # ============================================================
    # CERRAR
    # ============================================================

    def action_close(self):
        for record in self:
            if record.state != "answered":
                raise UserError(
                    _(
                        "La reclamación debe haber sido "
                        "respondida antes de cerrarla."
                    )
                )

            record.write(
                {
                    "state": "closed",
                    "fecha_cierre": (
                        fields.Datetime.now()
                    ),
                }
            )

        return True

    # ============================================================
    # REABRIR
    # ============================================================

    def action_reopen(self):
        for record in self:
            record.write(
                {
                    "state": "review",
                    "fecha_cierre": False,
                }
            )

        return True

    # ============================================================
    # ANULAR
    # ============================================================

    def action_cancel(self):
        for record in self:
            record.write(
                {
                    "state": "cancelled",
                }
            )

        return True

    # ============================================================
    # CONTACTO ODOO
    # ============================================================

    def action_create_or_link_partner(self):
        self.ensure_one()

        Partner = self.env[
            "res.partner"
        ].sudo()

        partner = False

        numero = (
            self.numero_documento or ""
        ).strip()

        if numero:
            partner = Partner.search(
                [
                    ("vat", "=", numero),
                ],
                limit=1,
            )

        if not partner and self.email:
            partner = Partner.search(
                [
                    (
                        "email",
                        "=ilike",
                        self.email.strip(),
                    ),
                ],
                limit=1,
            )

        if not partner:
            partner = Partner.create(
                {
                    "name": (
                        self.nombre_consumidor
                    ),
                    "company_type": "person",
                    "vat": numero,
                    "email": self.email,
                    "phone": self.telefono,
                    "street": (
                        self.domicilio_consumidor
                    ),
                }
            )

        self.partner_id = partner.id

        return partner

    # ============================================================
    # MARCAR CONSTANCIA ENVIADA
    # ============================================================

    def marcar_constancia_enviada(self):
        for record in self:
            record.write(
                {
                    "constancia_enviada": True,
                    "fecha_envio_constancia": (
                        fields.Datetime.now()
                    ),
                }
            )

        return True

    # ============================================================
    # CRON: PRÓXIMOS A VENCER
    # ============================================================

    @api.model
    def _cron_alertar_reclamos_por_vencer(self):
        hoy = fields.Date.context_today(self)

        limite = hoy + timedelta(days=3)

        reclamaciones = self.search(
            [
                (
                    "state",
                    "in",
                    [
                        "submitted",
                        "review",
                    ],
                ),
                (
                    "fecha_limite_respuesta",
                    "<=",
                    limite,
                ),
                (
                    "fecha_limite_respuesta",
                    ">=",
                    hoy,
                ),
            ]
        )

        activity_type = self.env.ref(
            "mail.mail_activity_data_todo",
            raise_if_not_found=False,
        )

        if not activity_type:
            return True

        Activity = self.env[
            "mail.activity"
        ]

        for record in reclamaciones:
            responsable = (
                record.responsable_id
                or self.env.user
            )

            existe = Activity.search(
                [
                    (
                        "res_model",
                        "=",
                        self._name,
                    ),
                    (
                        "res_id",
                        "=",
                        record.id,
                    ),
                    (
                        "activity_type_id",
                        "=",
                        activity_type.id,
                    ),
                    (
                        "summary",
                        "=",
                        "Libro de Reclamaciones por vencer",
                    ),
                ],
                limit=1,
            )

            if existe:
                continue

            record.activity_schedule(
                activity_type_id=(
                    activity_type.id
                ),
                user_id=responsable.id,
                date_deadline=(
                    record.fecha_limite_respuesta
                ),
                summary=(
                    "Libro de Reclamaciones "
                    "por vencer"
                ),
                note=(
                    "La Hoja de Reclamación "
                    "%s debe ser revisada."
                    % record.name
                ),
            )

        return True

    # ============================================================
    # CRON: VENCIDOS
    # ============================================================

    @api.model
    def _cron_alertar_reclamos_vencidos(self):
        hoy = fields.Date.context_today(self)

        reclamaciones = self.search(
            [
                (
                    "state",
                    "in",
                    [
                        "submitted",
                        "review",
                    ],
                ),
                (
                    "fecha_limite_respuesta",
                    "<",
                    hoy,
                ),
            ]
        )

        activity_type = self.env.ref(
            "mail.mail_activity_data_todo",
            raise_if_not_found=False,
        )

        if not activity_type:
            return True

        Activity = self.env[
            "mail.activity"
        ]

        for record in reclamaciones:
            responsable = (
                record.responsable_id
                or self.env.user
            )

            existe = Activity.search(
                [
                    (
                        "res_model",
                        "=",
                        self._name,
                    ),
                    (
                        "res_id",
                        "=",
                        record.id,
                    ),
                    (
                        "summary",
                        "=",
                        "Libro de Reclamaciones vencido",
                    ),
                ],
                limit=1,
            )

            if existe:
                continue

            record.activity_schedule(
                activity_type_id=(
                    activity_type.id
                ),
                user_id=responsable.id,
                date_deadline=hoy,
                summary=(
                    "Libro de Reclamaciones vencido"
                ),
                note=(
                    "La Hoja de Reclamación "
                    "%s superó su fecha límite "
                    "de respuesta."
                    % record.name
                ),
            )

        return True