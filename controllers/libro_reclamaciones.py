# -*- coding: utf-8 -*-

import base64
import binascii
import logging
import mimetypes
import re

from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class LibroReclamacionesController(http.Controller):

    # ============================================================
    # CONFIGURACIÓN
    # ============================================================

    MAX_ATTACHMENTS = 5
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB por archivo

    ALLOWED_MIMETYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    # ============================================================
    # HELPERS GENERALES
    # ============================================================

    def _get_company(self):
        """
        Obtiene la empresa asociada al website actual.

        Si el website tiene empresa configurada se utiliza esa.
        De lo contrario se utiliza la empresa activa.
        """
        website = request.website

        if website and website.company_id:
            return website.company_id.sudo()

        return request.env.company.sudo()

    def _get_website(self):
        if request.website:
            return request.website.sudo()

        return False

    def _clean_text(self, value, max_length=None):
        value = str(value or "").strip()

        if max_length:
            value = value[:max_length]

        return value

    def _clean_email(self, value):
        return self._clean_text(
            value,
            254,
        ).lower()

    def _clean_document(self, value):
        return self._clean_text(
            value,
            30,
        )

    def _clean_phone(self, value):
        return self._clean_text(
            value,
            50,
        )

    def _parse_boolean(self, value):
        return str(
            value or ""
        ).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
            "si",
            "sí",
        )

    def _parse_float(self, value):
        """
        Acepta por ejemplo:

        1500
        1500.50
        1500,50
        1,500.50
        """

        value = str(
            value or ""
        ).strip()

        if not value:
            return 0.0

        value = value.replace(" ", "")

        if "," in value and "." in value:

            # 1,500.50
            if value.rfind(".") > value.rfind(","):
                value = value.replace(",", "")

            # 1.500,50
            else:
                value = value.replace(".", "")
                value = value.replace(",", ".")

        elif "," in value:
            value = value.replace(",", ".")

        try:
            return float(value)

        except (TypeError, ValueError):
            return 0.0

    def _is_valid_email(self, email):
        if not email:
            return False

        return bool(
            re.fullmatch(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                email,
            )
        )

    # ============================================================
    # IP / NAVEGADOR
    # ============================================================

    def _get_client_ip(self):
        """
        Compatible con proxy / nginx.

        X-Forwarded-For puede contener:
        cliente, proxy1, proxy2
        """

        httprequest = request.httprequest

        forwarded_for = (
            httprequest.headers.get(
                "X-Forwarded-For"
            )
        )

        if forwarded_for:
            return (
                forwarded_for
                .split(",")[0]
                .strip()[:64]
            )

        return (
            httprequest.remote_addr
            or ""
        )[:64]

    def _get_user_agent(self):
        return (
            request.httprequest.headers.get(
                "User-Agent",
                "",
            )
            or ""
        )[:1000]

    # ============================================================
    # FIRMA DEL CONSUMIDOR
    # ============================================================

    def _decode_signature(self, signature_data):
        """
        Espera una firma generada con canvas:

        data:image/png;base64,AAAAAAA...

        Devuelve bytes binarios.

        Si la firma no es válida devuelve False.
        """

        signature_data = str(
            signature_data or ""
        ).strip()

        if not signature_data:
            return False

        encoded = signature_data

        if "," in signature_data:
            header, encoded = signature_data.split(
                ",",
                1,
            )

            if not header.startswith(
                "data:image/"
            ):
                return False

        try:
            binary = base64.b64decode(
                encoded,
                validate=True,
            )

        except (
            ValueError,
            TypeError,
            binascii.Error,
        ):
            return False

        if not binary:
            return False

        # Máximo 3 MB para firma.
        if len(binary) > (
            3 * 1024 * 1024
        ):
            return False

        return binary

    # ============================================================
    # ARCHIVOS ADJUNTOS
    # ============================================================

    def _prepare_uploads(self, uploads):
        """
        Valida archivos antes de crear ir.attachment.

        Permitidos:
        - PDF
        - JPG
        - PNG
        - WEBP
        """

        prepared = []

        if not uploads:
            return prepared

        uploads = uploads[
            : self.MAX_ATTACHMENTS
        ]

        for upload in uploads:

            if not upload:
                continue

            filename = self._clean_text(
                getattr(
                    upload,
                    "filename",
                    "",
                ),
                255,
            )

            if not filename:
                continue

            content = upload.read()

            if not content:
                continue

            if len(content) > (
                self.MAX_ATTACHMENT_SIZE
            ):
                raise ValidationError(
                    _(
                        "El archivo '%s' supera "
                        "el máximo permitido de 10 MB."
                    )
                    % filename
                )

            mimetype = (
                getattr(
                    upload,
                    "content_type",
                    False,
                )
                or mimetypes.guess_type(
                    filename
                )[0]
                or "application/octet-stream"
            )

            if (
                mimetype
                not in self.ALLOWED_MIMETYPES
            ):
                raise ValidationError(
                    _(
                        "El archivo '%s' tiene un formato "
                        "no permitido. Solo puede adjuntar "
                        "PDF, JPG, PNG o WEBP."
                    )
                    % filename
                )

            prepared.append(
                {
                    "name": filename,
                    "mimetype": mimetype,
                    "data": content,
                }
            )

        return prepared

    # ============================================================
    # BUSCAR RECLAMACIÓN POR TOKEN
    # ============================================================

    def _get_reclamation_by_token(
        self,
        token,
    ):
        """
        Para acceso público nunca usamos ID de Odoo.

        Utilizamos exclusivamente public_token.
        """

        token = self._clean_text(
            token,
            128,
        )

        if not token:
            return False

        reclamacion = (
            request.env[
                "libro.reclamaciones"
            ]
            .sudo()
            .search(
                [
                    (
                        "public_token",
                        "=",
                        token,
                    ),
                    (
                        "active",
                        "=",
                        True,
                    ),
                ],
                limit=1,
            )
        )

        return reclamacion

    # ============================================================
    # FORMULARIO PÚBLICO
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=True,
    )
    def libro_reclamaciones_form(
        self,
        **kwargs,
    ):

        company = self._get_company()
        website = self._get_website()

        values = {
            "company": company,
            "website": website,
            "error": False,
            "form_data": {},
        }

        return request.render(
            "copier_company.libro_reclamaciones_form",
            values,
        )

    # ============================================================
    # CONSULTAR DNI
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/consultar-dni",
        type="jsonrpc",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=False,
    )
    def libro_reclamaciones_consultar_dni(
        self,
        numero_documento=None,
        **kwargs,
    ):
        """
        Consulta DNI usando el método definido en:

        libro.reclamaciones.consultar_dni_publico()

        El token Decolecta NUNCA llega al navegador.
        """

        numero = self._clean_document(
            numero_documento
        )

        if not re.fullmatch(
            r"\d{8}",
            numero,
        ):
            return {
                "ok": False,
                "manual": True,
                "error": "invalid_document",
                "message": (
                    "El DNI debe contener "
                    "exactamente 8 dígitos."
                ),
            }

        try:

            resultado = (
                request.env[
                    "libro.reclamaciones"
                ]
                .sudo()
                .consultar_dni_publico(
                    numero
                )
            )

        except Exception as exc:

            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "Error consulta DNI=%s error=%s",
                numero,
                exc,
            )

            return {
                "ok": False,
                "manual": True,
                "error": "internal_error",
                "message": (
                    "No fue posible consultar el DNI "
                    "en este momento. Puede ingresar "
                    "el nombre manualmente."
                ),
            }

        if resultado.get("ok"):

            return {
                "ok": True,
                "manual": False,
                "numero_documento": numero,
                "nombre": (
                    resultado.get("nombre")
                    or ""
                ),
            }

        return {
            "ok": False,
            "manual": True,
            "error": (
                resultado.get("error")
                or "lookup_error"
            ),
            "message": (
                resultado.get("message")
                or (
                    "No fue posible consultar el DNI. "
                    "Ingrese el nombre manualmente."
                )
            ),
        }

    # ============================================================
    # REGISTRAR RECLAMACIÓN
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/enviar",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def libro_reclamaciones_submit(
        self,
        **post,
    ):

        company = self._get_company()
        website = self._get_website()

        # ========================================================
        # DATOS DEL CONSUMIDOR
        # ========================================================

        tipo_documento = (
            self._clean_text(
                post.get(
                    "tipo_documento"
                ),
                10,
            )
        )

        numero_documento = (
            self._clean_document(
                post.get(
                    "numero_documento"
                )
            )
        )

        nombre_consumidor = (
            self._clean_text(
                post.get(
                    "nombre_consumidor"
                ),
                250,
            )
        )

        domicilio_consumidor = (
            self._clean_text(
                post.get(
                    "domicilio_consumidor"
                ),
                500,
            )
        )

        telefono = self._clean_phone(
            post.get("telefono")
        )

        email = self._clean_email(
            post.get("email")
        )

        es_menor_edad = (
            self._parse_boolean(
                post.get(
                    "es_menor_edad"
                )
            )
        )

        representante_menor_nombre = (
            self._clean_text(
                post.get(
                    "representante_menor_nombre"
                ),
                250,
            )
        )

        # ========================================================
        # BIEN CONTRATADO
        # ========================================================

        tipo_bien = self._clean_text(
            post.get(
                "tipo_bien"
            ),
            20,
        )

        monto_reclamado = (
            self._parse_float(
                post.get(
                    "monto_reclamado"
                )
            )
        )

        descripcion_bien = (
            self._clean_text(
                post.get(
                    "descripcion_bien"
                ),
                10000,
            )
        )

        numero_documento_comercial = (
            self._clean_text(
                post.get(
                    "numero_documento_comercial"
                ),
                100,
            )
        )

        # ========================================================
        # RECLAMACIÓN
        # ========================================================

        tipo_reclamacion = (
            self._clean_text(
                post.get(
                    "tipo_reclamacion"
                ),
                20,
            )
        )

        detalle = self._clean_text(
            post.get(
                "detalle"
            ),
            20000,
        )

        pedido_consumidor = (
            self._clean_text(
                post.get(
                    "pedido_consumidor"
                ),
                20000,
            )
        )

        acepta_declaracion = (
            self._parse_boolean(
                post.get(
                    "acepta_declaracion"
                )
            )
        )

        acepta_privacidad = (
            self._parse_boolean(
                post.get(
                    "acepta_privacidad"
                )
            )
        )

        # ========================================================
        # VALIDACIONES
        # ========================================================

        errores = []

        if tipo_documento not in (
            "dni",
            "ce",
        ):
            errores.append(
                "Seleccione DNI o Carné "
                "de Extranjería."
            )

        if tipo_documento == "dni":

            if not re.fullmatch(
                r"\d{8}",
                numero_documento,
            ):
                errores.append(
                    "El DNI debe contener "
                    "exactamente 8 dígitos."
                )

        elif tipo_documento == "ce":

            if len(
                numero_documento
            ) < 4:
                errores.append(
                    "Ingrese un Carné de "
                    "Extranjería válido."
                )

        if not nombre_consumidor:
            errores.append(
                "Ingrese el nombre "
                "del consumidor."
            )

        if not domicilio_consumidor:
            errores.append(
                "Ingrese su domicilio."
            )

        if not telefono:
            errores.append(
                "Ingrese su teléfono."
            )

        if not email:
            errores.append(
                "Ingrese su correo electrónico."
            )

        elif not self._is_valid_email(
            email
        ):
            errores.append(
                "Ingrese un correo "
                "electrónico válido."
            )

        if (
            es_menor_edad
            and not representante_menor_nombre
        ):
            errores.append(
                "Ingrese el nombre del padre, "
                "madre o apoderado."
            )

        if tipo_bien not in (
            "producto",
            "servicio",
        ):
            errores.append(
                "Seleccione Producto "
                "o Servicio."
            )

        if not descripcion_bien:
            errores.append(
                "Ingrese la descripción "
                "del producto o servicio."
            )

        if tipo_reclamacion not in (
            "reclamo",
            "queja",
        ):
            errores.append(
                "Seleccione Reclamo "
                "o Queja."
            )

        if not detalle:
            errores.append(
                "Ingrese el detalle "
                "de la reclamación."
            )

        if not pedido_consumidor:
            errores.append(
                "Ingrese el pedido "
                "del consumidor."
            )

        if not acepta_declaracion:
            errores.append(
                "Debe aceptar la declaración "
                "antes de registrar."
            )

        # ========================================================
        # FIRMA
        # ========================================================

        firma_binaria = (
            self._decode_signature(
                post.get(
                    "firma_consumidor"
                )
            )
        )

        if not firma_binaria:
            errores.append(
                "Debe registrar su firma."
            )

        # ========================================================
        # ADJUNTOS
        # ========================================================

        prepared_uploads = []

        try:

            uploads = (
                request
                .httprequest
                .files
                .getlist(
                    "attachment_ids"
                )
            )

            prepared_uploads = (
                self._prepare_uploads(
                    uploads
                )
            )

        except ValidationError as exc:

            errores.append(
                str(exc)
            )

        # ========================================================
        # SI EXISTEN ERRORES
        # ========================================================

        if errores:

            return request.render(
                "copier_company.libro_reclamaciones_form",
                {
                    "company": company,
                    "website": website,
                    "error": errores,
                    "form_data": post,
                },
            )

        # ========================================================
        # VALIDAR DNI NUEVAMENTE EN SERVIDOR
        # ========================================================

        documento_consultado = False
        documento_encontrado = False

        ingreso_manual = True

        consulta_estado = "manual"

        consulta_mensaje = (
            "Datos ingresados manualmente."
        )

        nombres = False
        apellido_paterno = False
        apellido_materno = False

        if tipo_documento == "dni":

            documento_consultado = True

            try:

                resultado_dni = (
                    request.env[
                        "libro.reclamaciones"
                    ]
                    .sudo()
                    .consultar_dni_publico(
                        numero_documento
                    )
                )

                if resultado_dni.get(
                    "ok"
                ):

                    documento_encontrado = True

                    ingreso_manual = False

                    consulta_estado = "found"

                    consulta_mensaje = (
                        "Datos obtenidos "
                        "automáticamente."
                    )

                    nombres = (
                        resultado_dni.get(
                            "nombres"
                        )
                        or False
                    )

                    apellido_paterno = (
                        resultado_dni.get(
                            "apellido_paterno"
                        )
                        or False
                    )

                    apellido_materno = (
                        resultado_dni.get(
                            "apellido_materno"
                        )
                        or False
                    )

                    nombre_api = (
                        resultado_dni.get(
                            "nombre"
                        )
                        or ""
                    ).strip()

                    if nombre_api:
                        nombre_consumidor = (
                            nombre_api
                        )

                else:

                    documento_encontrado = False

                    ingreso_manual = True

                    consulta_estado = (
                        "not_found"
                        if resultado_dni.get(
                            "error"
                        )
                        == "not_found"
                        else "error"
                    )

                    consulta_mensaje = (
                        resultado_dni.get(
                            "message"
                        )
                        or (
                            "Datos ingresados "
                            "manualmente."
                        )
                    )

            except Exception as exc:

                _logger.exception(
                    "[LIBRO RECLAMACIONES] "
                    "Error validando DNI=%s: %s",
                    numero_documento,
                    exc,
                )

                documento_encontrado = False
                ingreso_manual = True
                consulta_estado = "error"

                consulta_mensaje = (
                    "La consulta automática "
                    "no estuvo disponible. "
                    "Datos ingresados manualmente."
                )

        # ========================================================
        # VALORES DEL MODELO
        # ========================================================

        vals = {

            # ----------------------------------------------------
            # EMPRESA / WEBSITE
            # ----------------------------------------------------

            "company_id": (
                company.id
            ),

            "website_id": (
                website.id
                if website
                else False
            ),

            # ----------------------------------------------------
            # CONSUMIDOR
            # ----------------------------------------------------

            "tipo_documento": (
                tipo_documento
            ),

            "numero_documento": (
                numero_documento
            ),

            "nombre_consumidor": (
                nombre_consumidor
            ),

            "nombres": nombres,

            "apellido_paterno": (
                apellido_paterno
            ),

            "apellido_materno": (
                apellido_materno
            ),

            "domicilio_consumidor": (
                domicilio_consumidor
            ),

            "telefono": telefono,

            "email": email,

            "es_menor_edad": (
                es_menor_edad
            ),

            "representante_menor_nombre": (
                representante_menor_nombre
                if es_menor_edad
                else False
            ),

            # ----------------------------------------------------
            # BIEN
            # ----------------------------------------------------

            "tipo_bien": (
                tipo_bien
            ),

            "monto_reclamado": (
                monto_reclamado
            ),

            "descripcion_bien": (
                descripcion_bien
            ),

            "numero_documento_comercial": (
                numero_documento_comercial
                or False
            ),

            # ----------------------------------------------------
            # RECLAMACIÓN
            # ----------------------------------------------------

            "tipo_reclamacion": (
                tipo_reclamacion
            ),

            "detalle": detalle,

            "pedido_consumidor": (
                pedido_consumidor
            ),

            "firma_consumidor": (
                base64.b64encode(
                    firma_binaria
                )
            ),

            "firma_consumidor_filename": (
                "firma_consumidor.png"
            ),

            # ----------------------------------------------------
            # DECLARACIONES
            # ----------------------------------------------------

            "acepta_declaracion": (
                acepta_declaracion
            ),

            "acepta_privacidad": (
                acepta_privacidad
            ),

            # ----------------------------------------------------
            # CONSULTA DNI
            # ----------------------------------------------------

            "documento_consultado": (
                documento_consultado
            ),

            "documento_encontrado": (
                documento_encontrado
            ),

            "ingreso_manual": (
                ingreso_manual
            ),

            "consulta_documento_estado": (
                consulta_estado
            ),

            "consulta_documento_mensaje": (
                consulta_mensaje
            ),

            "fecha_consulta_documento": (
                fields.Datetime.now()
                if documento_consultado
                else False
            ),

            # ----------------------------------------------------
            # AUDITORÍA
            # ----------------------------------------------------

            "origen": "website",

            "ip_address": (
                self._get_client_ip()
            ),

            "user_agent": (
                self._get_user_agent()
            ),

            "state": "draft",
        }

        # ========================================================
        # CREAR
        # ========================================================

        try:

            Reclamacion = (
                request.env[
                    "libro.reclamaciones"
                ]
                .sudo()
            )

            reclamacion = (
                Reclamacion.create(
                    vals
                )
            )

            # Ejecutamos validación final
            # definida en el modelo.
            reclamacion._validar_para_registro()

            reclamacion.write(
                {
                    "state": "submitted",
                }
            )

        except (
            UserError,
            ValidationError,
        ) as exc:

            _logger.warning(
                "[LIBRO RECLAMACIONES] "
                "Validación formulario: %s",
                exc,
            )

            return request.render(
                "copier_company.libro_reclamaciones_form",
                {
                    "company": company,
                    "website": website,
                    "error": [
                        str(exc)
                    ],
                    "form_data": post,
                },
            )

        except Exception as exc:

            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "Error creando reclamación: %s",
                exc,
            )

            return request.render(
                "copier_company.libro_reclamaciones_form",
                {
                    "company": company,
                    "website": website,
                    "error": [
                        (
                            "No fue posible registrar "
                            "la reclamación. "
                            "Intente nuevamente."
                        )
                    ],
                    "form_data": post,
                },
            )

        # ========================================================
        # CREAR ADJUNTOS
        # ========================================================

        attachment_ids = []

        Attachment = (
            request.env[
                "ir.attachment"
            ]
            .sudo()
        )

        for upload in prepared_uploads:

            try:

                attachment = (
                    Attachment.create(
                        {
                            "name": (
                                upload["name"]
                            ),

                            "type": "binary",

                            "datas": (
                                base64.b64encode(
                                    upload["data"]
                                )
                            ),

                            "mimetype": (
                                upload[
                                    "mimetype"
                                ]
                            ),

                            "res_model": (
                                "libro.reclamaciones"
                            ),

                            "res_id": (
                                reclamacion.id
                            ),
                        }
                    )
                )

                attachment_ids.append(
                    attachment.id
                )

            except Exception:

                _logger.exception(
                    "[LIBRO RECLAMACIONES] "
                    "Error creando adjunto "
                    "reclamacion=%s archivo=%s",
                    reclamacion.id,
                    upload.get(
                        "name"
                    ),
                )

        if attachment_ids:

            reclamacion.write(
                {
                    "attachment_ids": [
                        (
                            6,
                            0,
                            attachment_ids,
                        )
                    ]
                }
            )

        # ========================================================
        # CHATTER
        # ========================================================

        try:

            reclamacion.message_post(
                body=_(
                    "Hoja de Reclamación "
                    "registrada desde la página web."
                )
            )

        except Exception:

            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "No se pudo registrar mensaje "
                "en chatter. Reclamo=%s",
                reclamacion.id,
            )

        # ========================================================
        # REDIRECCIÓN
        # ========================================================

        return request.redirect(
            "/libro-de-reclamaciones/confirmacion/%s"
            % reclamacion.public_token
        )

    # ============================================================
    # CONFIRMACIÓN
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/confirmacion/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def libro_reclamaciones_confirmation(
        self,
        token,
        **kwargs,
    ):

        reclamacion = (
            self._get_reclamation_by_token(
                token
            )
        )

        if not reclamacion:
            return request.not_found()

        return request.render(
            "copier_company.libro_reclamaciones_confirmation",
            {
                "reclamacion": (
                    reclamacion
                ),
                "company": (
                    reclamacion.company_id
                ),
            },
        )

    # ============================================================
    # VER CONSTANCIA EN HTML
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/constancia/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def libro_reclamaciones_constancia(
        self,
        token,
        **kwargs,
    ):

        reclamacion = (
            self._get_reclamation_by_token(
                token
            )
        )

        if not reclamacion:
            return request.not_found()

        return request.render(
            "copier_company.libro_reclamaciones_constancia",
            {
                "reclamacion": (
                    reclamacion
                ),
                "company": (
                    reclamacion.company_id
                ),
            },
        )

    # ============================================================
    # GENERAR PDF PÚBLICO
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/pdf/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def libro_reclamaciones_pdf(
        self,
        token,
        download=None,
        **kwargs,
    ):

        reclamacion = (
            self._get_reclamation_by_token(
                token
            )
        )

        if not reclamacion:
            return request.not_found()

        # ========================================================
        # BUSCAR ACCIÓN DEL REPORTE
        # ========================================================

        try:

            report = (
                request.env.ref(
                    "copier_company.action_report_libro_reclamaciones"
                )
                .sudo()
            )

        except Exception:

            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "No existe la acción del reporte."
            )

            return request.make_response(
                "El reporte del Libro de "
                "Reclamaciones no está configurado.",
                headers=[
                    (
                        "Content-Type",
                        "text/plain; charset=utf-8",
                    ),
                ],
                status=500,
            )

        # ========================================================
        # GENERAR PDF
        # ========================================================

        try:

            pdf_content, _ = (
                request.env[
                    "ir.actions.report"
                ]
                .sudo()
                ._render_qweb_pdf(
                    report.report_name,
                    res_ids=[
                        reclamacion.id
                    ],
                )
            )

        except Exception as exc:

            _logger.exception(
                "[LIBRO RECLAMACIONES] "
                "Error generando PDF "
                "reclamacion=%s error=%s",
                reclamacion.id,
                exc,
            )

            return request.make_response(
                "No fue posible generar el PDF.",
                headers=[
                    (
                        "Content-Type",
                        "text/plain; charset=utf-8",
                    ),
                ],
                status=500,
            )

        # ========================================================
        # NOMBRE DEL ARCHIVO
        # ========================================================

        filename = "%s.pdf" % (
            reclamacion.name
            or "libro_reclamaciones"
        )

        # ========================================================
        # INLINE O DESCARGA
        # ========================================================

        force_download = (
            self._parse_boolean(
                download
            )
        )

        if force_download:
            disposition = "attachment"
        else:
            disposition = "inline"

        headers = [
            (
                "Content-Type",
                "application/pdf",
            ),
            (
                "Content-Length",
                str(
                    len(
                        pdf_content
                    )
                ),
            ),
            (
                "Content-Disposition",
                '%s; filename="%s"'
                % (
                    disposition,
                    filename,
                ),
            ),
            (
                "X-Content-Type-Options",
                "nosniff",
            ),
        ]

        return request.make_response(
            pdf_content,
            headers=headers,
        )

    # ============================================================
    # DESCARGAR PDF
    # ============================================================

    @http.route(
        "/libro-de-reclamaciones/descargar/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def libro_reclamaciones_download(
        self,
        token,
        **kwargs,
    ):

        return self.libro_reclamaciones_pdf(
            token=token,
            download="1",
        )