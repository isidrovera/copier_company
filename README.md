Gestión de Fotocopiadoras — Copier Company

Módulo Odoo | Versión 0.1 | Licencia LGPL-3

Autor: Isidro · Web: copiercompanysac.com

Tabla de Contenidos

- Descripción General

- Requisitos del Sistema

- Arquitectura y Estructura del Módulo

- Modelos de Datos

- Lógica de Negocio y Cálculos Financieros

- Gestión de Servicios Técnicos

- Control de Contadores

- Stock de Máquinas de Segunda Mano

- Portal Web y Sitio Web

- Integraciones Externas

- Sistema de Notificaciones WhatsApp

- Almacenamiento en la Nube (pCloud)

- Manuales y Documentación PDF Segura

- Cotizaciones y Facturación

- Reportes e Impresión

- Seguridad y Control de Accesos

- Automatizaciones y Cron Jobs

- Activos Frontend (JS/CSS)

- Guía de Instalación y Configuración

- Flujos de Trabajo Principales

- Referencia de la API Interna

- Glosario

1. Descripción General

Gestión de Fotocopiadoras es un módulo Odoo diseñado específicamente para empresas que alquilan, venden y dan soporte técnico a máquinas fotocopiadoras y equipos multifuncionales. El módulo cubre el ciclo de vida completo de un contrato de alquiler, desde la cotización inicial hasta la facturación mensual por lecturas de contador, pasando por la gestión de servicios técnicos, el inventario de máquinas y la comunicación con el cliente.

Funcionalidades Principales

El módulo proporciona un conjunto completo de herramientas organizadas en seis grandes áreas funcionales. La primera es la Gestión de Contratos de Alquiler, que permite registrar máquinas en alquiler con todos sus datos técnicos y financieros, calcular rentas mensuales de forma automática o manual, gestionar duraciones de contrato y renovaciones, y generar alertas de vencimiento automáticas. La segunda área es el Control de Contadores, mediante la cual se registran lecturas de contador mensuales (blanco y negro, y color), se calculan automáticamente las copias facturables, se generan facturas individuales o consolidadas, y se integra con PrintTracker Pro para lectura remota de contadores. La tercera área es la Gestión de Servicios Técnicos, que implementa un sistema de tickets de soporte con flujo de estados completo, asignación de técnicos, control de SLA, notificaciones automáticas al cliente, y evaluación de satisfacción post-servicio. La cuarta área es el Inventario de Stock, para gestión de máquinas de segunda mano con checklist de revisión, estados de disponibilidad, reservas, y catálogo público en el sitio web. La quinta área son las Integraciones y Comunicaciones, incluyendo envío de mensajes y documentos por WhatsApp a través de Baileys API, integración con pCloud para almacenamiento de documentos, y lectura remota de contadores con PrintTracker Pro. Finalmente, la sexta área es el Portal y Sitio Web, que ofrece un portal de cliente para consultar contratos y equipos, formularios públicos de solicitud de servicio y tóner, seguimiento de tickets en tiempo real, y catálogo de máquinas en venta.

2. Requisitos del Sistema

Dependencias de Módulos Odoo

El módulo declara las siguientes dependencias en __manifest__.py:

MóduloPropósito

baseModelos fundamentales de Odoo

webFramework de interfaz web

mailSistema de mensajería y seguimiento (chatter)

contactsGestión de contactos (res.partner)

helpdeskBase para tickets de soporte técnico

sale_managementGestión de ventas y cotizaciones

portalPortal web para clientes

sale_subscriptionGestión de suscripciones y contratos recurrentes

websiteSitio web público

Dependencias Python Externas

requests          # Comunicación HTTP con APIs externas (WhatsApp, PrintTracker, pCloud)
requests_toolbelt # Envío de archivos multipart
qrcode            # Generación de códigos QR para etiquetas
PIL (Pillow)      # Procesamiento de imágenes

Dependencias del Sistema

wkhtmltoimage     # Generación de imágenes de stickers (binario del sistema)

Dependencias JavaScript Externas (CDN)

PDF.js 3.11.174           # Visor de PDFs en el navegador (seguro, sin descarga)
Lucide 0.451.0            # Librería de iconos vectoriales
Chart.js 3.9.1            # Gráficos interactivos de contadores

3. Arquitectura y Estructura del Módulo

copier_company/
├── __manifest__.py                  # Configuración del módulo
├── __init__.py                      # Inicialización del paquete
├── models/                          # Lógica de negocio (ORM)
│   ├── __init__.py
│   ├── models.py                    # CopierCompany (contrato de alquiler)
│   ├── modelos.py                   # ModelosMaquinas, MarcasMaquinas, etc.
│   ├── contadores.py                # CopierCounter (lecturas de contador)
│   ├── copier_soporte.py            # CopierServiceRequest (servicio técnico)
│   ├── copier_stock.py              # CopierStock (inventario 2ª mano)
│   ├── copier_stock_extend.py       # Extensión de CopierStock
│   ├── copier_stock_whatsapp_extend.py  # WhatsApp en stock
│   ├── copier_whatsapp_alerts.py    # Alertas WhatsApp
│   ├── whatsapp_config.py           # Configuración API Baileys
│   ├── whatsapp_service_notifications.py  # Notificaciones de servicio
│   ├── whatsapp_send_quotation_wizard.py  # Wizard envío de cotización
│   ├── whatsapp_quotation_phone_line.py   # Línea de teléfono
│   ├── whatsapp_send_multi_quotation_wizard.py  # Wizard múltiple
│   ├── whatsapp_multi_quotation_phone_line.py
│   ├── printtracker_config.py       # Integración PrintTracker Pro
│   ├── pCloudModel.py               # Integración pCloud
│   ├── pcloud_folder_file.py        # Carpetas y archivos pCloud
│   ├── manuals.py                   # Manuales PDF seguros
│   ├── cotizacion_hinerid.py        # Cotizaciones extendidas
│   ├── cotizaciones_multiples.py    # Cotizaciones múltiples
│   ├── counter_web.py               # Envío de lecturas desde web
│   ├── toner_web.py                 # Solicitudes de tóner desde web
│   ├── remote_printer.py            # Asistencia remota
│   ├── stock_move_inherit.py        # Extensión de movimientos de stock
│   ├── security_control.py          # Control de seguridad
│   ├── empresas.py                  # Extensión de res.partner
│   └── res_partner_extend.py        # Campo allow_downloads en contactos
├── controllers/                     # Rutas HTTP (web/portal)
│   ├── __init__.py
│   ├── portal.py                    # Portal del cliente
│   ├── portal_counters.py           # Portal de contadores
│   ├── service_request.py           # Solicitudes de servicio
│   ├── controllers.py               # Controladores generales
│   ├── controladores_web.py         # Rutas de sitio web
│   ├── cotizaciones.py              # Cotizaciones web
│   ├── cotizaciones_multiples.py    # Cotizaciones múltiples web
│   ├── manuals.py                   # Descarga segura de manuales
│   ├── cloud.py                     # Rutas pCloud
│   ├── PcloudPublico.py             # pCloud público
│   ├── sticker_controller.py        # Generación de etiquetas
│   ├── sticker_print.py             # Impresión de etiquetas
│   └── website_stock.py             # Catálogo web de stock
├── views/                           # Vistas XML (backend y frontend)
│   ├── views.xml                    # Vista principal CopierCompany
│   ├── marcas.xml                   # Marcas de máquinas
│   ├── modelos.xml                  # Modelos de máquinas
│   ├── contadores.xml               # Lecturas de contador
│   ├── copier_soporte.xml           # Servicio técnico
│   ├── copier_stock_views.xml       # Stock
│   ├── ajustes_copier.xml           # Configuración del módulo
│   ├── menus_actions.xml            # Menús y acciones
│   ├── portal_templates.xml         # Plantillas portal cliente
│   ├── homepage_template.xml        # Página de inicio web
│   ├── whatsapp_config_views.xml    # Configuración WhatsApp
│   ├── printtracker_config_views.xml  # Configuración PrintTracker
│   └── ...                          # (más de 40 vistas adicionales)
├── report/                          # Reportes QWeb
│   ├── copier_company_report.xml    # Cotización de alquiler
│   ├── counter_report.xml           # Reporte de lecturas
│   ├── sticker_report.xml           # Etiquetas de máquinas
│   ├── cotizacion_multiples.xml     # Cotizaciones múltiples
│   ├── report_counter_portal.xml    # Reporte portal contadores
│   └── report_service_request.xml   # Reporte servicio técnico
├── data/                            # Datos iniciales
│   ├── copier_company_data.xml      # Estados y duraciones de alquiler
│   ├── ir.secuencia.xml             # Secuencias de numeración
│   ├── cron.xml                     # Tareas programadas
│   ├── plantillas_mail.xml          # Plantillas de correo
│   ├── copier_soporte_mail.xml      # Correos de soporte técnico
│   ├── checklist_items_data.xml     # Items de checklist
│   └── whatsapp_service_templates.xml  # Plantillas WhatsApp
├── security/
│   └── ir.model.access.csv          # Permisos de acceso
└── static/                          # Recursos estáticos
    ├── src/
    │   ├── css/                     # Hojas de estilo
    │   ├── js/                      # Scripts JavaScript
    │   ├── scss/                    # SCSS para reportes
    │   └── xml/                     # Plantillas QWeb frontend
    ├── img/                         # Imágenes (logos de marcas)
    └── lib/                         # Librerías empaquetadas (Bootstrap, PDF.js)

4. Modelos de Datos

4.1 CopierCompany (copier.company)

Es el modelo central del módulo y representa un contrato de alquiler de máquina fotocopiadora. Hereda de mail.thread y mail.activity.mixin para tener chatter y actividades.

Campos Principales

GrupoCampoTipoDescripción

IdentificaciónsecuenciaCharNúmero de cotización auto-generado (ej: CT-000001)

MáquinanameMany2one → modelos.maquinasModelo de la máquina

serie_idCharNúmero de serie

marca_idMany2one → marcas.maquinasMarca (related de name.marca_id)

tipoSelectionmonocroma / color

formatoSelectiona4 / a3

accesorios_idsMany2many → accesorios.maquinasAccesorios incluidos

imagen_idBinaryImagen del modelo (related)

Clientecliente_idMany2one → res.partnerCliente

contactoCharNombre del contacto

celularCharTeléfono

correoCharEmail

ubicacionCharDirección de instalación

sedeCharSede o sucursal

ip_idCharDirección IP de la máquina

Contratofecha_inicio_alquilerDateInicio del contrato

duracion_alquiler_idMany2one → copier.duracionDuración (6 meses, 1 año, 2 años)

fecha_fin_alquilerDate (computed)Fin calculado automáticamente

estado_maquina_idMany2one → copier.estadosEstado actual

estado_renovacionSelectionvigente / por_vencer / renovado / finalizado

dias_notificacionIntegerDías antes del vencimiento para alertar (default: 30)

Financierocurrency_idMany2one → res.currencyMoneda (default: PEN)

costo_copia_bnFloat (3 dec.)Costo por copia B/N

costo_copia_colorMonetaryCosto por copia color

volumen_mensual_bnIntegerVolumen mensual contratado B/N

volumen_mensual_colorIntegerVolumen mensual contratado color

igvFloatPorcentaje IGV (default: 18%)

descuentoFloatDescuento (%)

tipo_calculoSelectionTipo de cálculo financiero

renta_mensual_bnMonetary (computed)Renta mensual B/N

renta_mensual_colorMonetary (computed)Renta mensual color

subtotal_sin_igvMonetary (computed)Subtotal antes de IGV

monto_igvMonetary (computed)Monto del IGV

total_facturar_mensualMonetary (computed)Total mensual a facturar

Facturacióndia_facturacionIntegerDía del mes para facturar (default: 30)

payment_term_idMany2one → account.payment.termTérminos de pago

producto_facturable_bn_idMany2one → product.productProducto para facturas B/N

producto_facturable_color_idMany2one → product.productProducto para facturas color

PrintTrackerpt_device_idCharID del dispositivo en PrintTracker Pro

pt_last_syncDatetimeFecha de última sincronización

QRqr_codeBinaryImagen del código QR generado

Historialhistorial_renovacionesOne2many → copier.renewal.historyHistorial de renovaciones

Secuencias Generadas Automáticamente

La secuencia copier.company genera números con formato CT-XXXXXX y se asigna en el método create().

4.2 CopierCounter (copier.counter)

Representa una lectura mensual de contador de una máquina en alquiler. Cada lectura registra los valores actuales de las impresiones y calcula las copias a facturar.

Campos de Contadores

CampoTipoDescripción

nameCharReferencia auto-generada (secuencia)

maquina_idMany2one → copier.companyMáquina medida (solo "Alquilada")

fechaDateFecha de la lectura

fecha_facturacionDateFecha de facturación objetivo

fecha_emision_facturaDateFecha real de la factura emitida

mes_facturacionChar (computed)Ej: "Enero 2025"

contador_anterior_bnIntegerLectura anterior B/N

contador_actual_bnIntegerLectura actual B/N

total_copias_bnInteger (computed)Diferencia B/N

exceso_bnInteger (computed)Copias sobre el volumen contratado B/N

copias_facturables_bnInteger (computed)Máximo entre real y volumen mínimo

contador_anterior_colorIntegerLectura anterior color

contador_actual_colorIntegerLectura actual color

total_copias_colorInteger (computed)Diferencia color

copias_facturables_colorInteger (computed)Máximo entre real y volumen mínimo

subtotal_bnMonetary (computed)Subtotal sin IGV para B/N

subtotal_colorMonetary (computed)Subtotal sin IGV para color

igv_bnMonetary (computed)IGV para B/N

igv_colorMonetary (computed)IGV para color

total_bnMonetary (computed)Total con IGV para B/N

total_colorMonetary (computed)Total con IGV para color

subtotalMonetary (computed)Subtotal total con descuento

igvMonetary (computed)IGV total

totalMonetary (computed)Total a facturar

stateSelectiondraft / confirmed / invoiced / cancelled

informe_por_usuarioBooleanActivar detalle por usuario interno

usuario_detalle_idsOne2many → copier.counter.user.detailDetalle por usuario

pt_updatedBooleanActualizado desde PrintTracker

pt_last_reading_dateDatetimeFecha de lectura en PrintTracker

Estados del Contador

draft (Borrador)  →  confirmed (Confirmado)  →  invoiced (Facturado)
                                              ↓
                                         cancelled (Cancelado)

4.3 CopierServiceRequest (copier.service.request)

Modelo para solicitudes de servicio técnico. Gestiona el ciclo completo desde la creación de un ticket hasta su resolución y evaluación.

Campos Clave

GrupoCampoTipoDescripción

BásicosnameCharNúmero de servicio (secuencia)

maquina_idMany2one → copier.companyEquipo de la solicitud

cliente_idMany2one → res.partnerCliente (related de la máquina)

Solicitudproblema_reportadoTextDescripción del problema

tipo_problema_idMany2one → copier.service.problem.typeCategoría del problema

origen_solicitudSelectionportal / whatsapp / telefono / email / interno

prioridadSelection0 Baja / 1 Normal / 2 Alta / 3 Crítica

estadoSelectionEstado del ciclo de vida

Técnicotecnico_idMany2one → res.partnerTécnico asignado

fecha_programadaDatetimeFecha y hora de visita programada

vehicle_plateCharPlaca del vehículo

vehicle_infoChar (computed)Info completa del vehículo

Ejecuciónfecha_inicioDatetimeCheck-in del técnico

fecha_finDatetimeCompletado del servicio

trabajo_realizadoTextDescripción del trabajo

solucion_aplicadaSelectionTipo de solución

contador_bnIntegerContador B/N al momento del servicio

contador_colorIntegerContador color al momento del servicio

Evidenciasfoto_antesBinaryFoto antes del servicio

foto_despuesBinaryFoto después del servicio

firma_clienteBinaryFirma digital del cliente

conformidad_clienteBooleanConformidad del cliente

SLAsla_limite_1Float (computed)Horas límite según prioridad

tiempo_respuestaFloat (computed)Horas hasta asignación

tiempo_resolucionFloat (computed)Horas hasta completado

sla_cumplidoBoolean (computed)Si se cumplió el SLA

EvaluacióncalificacionSelection1 a 5 estrellas

comentario_clienteTextComentario del cliente

Tokenstracking_tokenCharToken único de seguimiento público

evaluation_tokenCharToken único de evaluación pública

tracking_urlChar (computed)URL pública de seguimiento

evaluation_urlChar (computed)URL pública de evaluación

Ciclo de Vida del Servicio

nuevo → asignado → confirmado → en_ruta → en_sitio → completado
                                                   ↓
                                              cancelado
                                                   ↑
                               (pausado puede regresar al flujo)

Límites SLA por Prioridad

PrioridadLímite en horas

Crítica (3)2 horas

Alta (2)4 horas

Normal (1)24 horas

Baja (0)48 horas

4.4 ModelosMaquinas (modelos.maquinas)

Catálogo de modelos de máquinas. Cada modelo puede tener una imagen, especificaciones HTML, y puede crear automáticamente un producto de inventario en Odoo (con número de serie, categoría y cuentas contables).

CampoTipoDescripción

nameCharNombre del modelo (único)

marca_idMany2one → marcas.maquinasMarca

tipo_maquinaSelectionfotocopiadora / impresora / multifuncional / otro

especificacionesHtmlEspecificaciones técnicas

imagenBinaryImagen del modelo

product_idMany2one → product.productProducto de inventario asociado

producto_nameChar (computed)Nombre generado: {tipo} {marca} {modelo}

4.5 CopierStock (copier.stock)

Gestiona el inventario de máquinas de segunda mano disponibles para venta.

CampoTipoDescripción

nameCharReferencia (secuencia)

modelo_idMany2one → modelos.maquinasModelo

serieCharNúmero de serie

contometroIntegerLectura actual del contómetro

tipoSelectionmonocroma / color

reparacionSelectionEstado de reparación

stateSelectionEstado de la unidad

sale_priceFloatPrecio de venta

checklist_idsOne2many → copier.checklist.lineChecklist de revisión

reserved_byMany2one → res.partnerReservada por

payment_proofBinaryComprobante de pago

payment_verifiedBooleanPago verificado

Estados de Stock

importing (En Importación) → unloading (En Descarga) → available (Disponible)
     ↓                                                         ↓
     └─────────────────────────────────────────→ reserved (Reservada)
                                                         ↓
                                                  pending_payment (Pendiente de Pago)
                                                         ↓
                                                   sold (Vendida)

4.6 Modelos de Catálogo

MarcasMaquinas (marcas.maquinas)

Catálogo de marcas con validación de unicidad. Ejemplos incluidos: Canon, Konica Minolta, Ricoh.

AccesoriosMaquinas (accesorios.maquinas)

Catálogo de accesorios (bandejas, ADF, finisher, etc.) con validación de unicidad.

CopierEstados (copier.estados)

Estados de una máquina: Disponible, Enviado, Alquilada, En Mantenimiento, Vendida, Con problemas.

CopierDuracion (copier.duracion)

Duraciones de contrato: 6 Meses, 1 Año, 2 Años.

4.7 CopierRenewalHistory (copier.renewal.history)

Historial inmutable de renovaciones de contratos.

CampoTipoDescripción

copier_idMany2one → copier.companyContrato renovado

fecha_renovacionDateFecha de la renovación

fecha_anteriorDateInicio del período anterior

fecha_fin_anteriorDateFin del período anterior

duracion_anterior_idMany2one → copier.duracionDuración del período anterior

notasTextNotas del proceso de renovación

4.8 CopierMachineUser (copier.machine.user)

Registro de usuarios internos de una máquina (empresas o departamentos que comparten un equipo). Se usa para el informe detallado de copias por usuario en el contador.

4.9 CopierServiceProblemType (copier.service.problem.type)

Catálogo de tipos de problemas técnicos con icono emoji, descripción y secuencia de ordenamiento.

4.10 Manual / Category (secure_pdf_viewer.manual / secure_pdf_viewer.category)

Almacena manuales en formato PDF con visualización segura (sin posibilidad de descarga directa desde el cliente). Incluye contador de accesos.

5. Lógica de Negocio y Cálculos Financieros

5.1 Tipos de Cálculo (tipo_calculo)

El modelo CopierCompany soporta siete modos de cálculo de la renta mensual:

ValorDescripción

autoCálculo automático: copias × costo_unitario

manual_sin_igv_bnMonto mensual fijo B/N (sin IGV)

manual_con_igv_bnMonto mensual fijo B/N (con IGV incluido)

manual_sin_igv_colorMonto mensual fijo color (sin IGV)

manual_con_igv_colorMonto mensual fijo color (con IGV incluido)

manual_sin_igv_totalMonto mensual total (sin IGV) con distribución proporcional

manual_con_igv_totalMonto mensual total (con IGV) con distribución proporcional

5.2 Cálculo Automático (auto)

renta_bn    = volumen_mensual_bn    × costo_copia_bn
renta_color = volumen_mensual_color × costo_copia_color

# Si el precio ya incluye IGV:
renta_bn    = (volumen × precio_con_igv) / (1 + igv/100)

5.3 Cálculo Manual con Distribución Proporcional (tipo total)

Cuando se usa manual_sin_igv_total o manual_con_igv_total con ambos tipos de copias, el sistema distribuye el monto total proporcionalmente usando una relación fija de 4:1 entre color y B/N:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

ratio_precio = 4  # color ≈ 4 veces B/N

denominador = volumen_bn + (4 × volumen_color)

precio_bn    = monto_sin_igv / denominador

precio_color = precio_bn × 4

5.4 Cálculo de Totales

subtotal     = renta_bn + renta_color
descuento    = subtotal × (descuento% / 100)
subtotal_neto = subtotal - descuento
igv_monto    = subtotal_neto × (igv% / 100)
total        = subtotal_neto + igv_monto

5.5 Sincronización de Costos Unitarios (Cálculo Inverso)

Cuando se ingresa un monto mensual fijo, el sistema calcula automáticamente los costos unitarios equivalentes para que el contador pueda usarlos:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

# Ejemplo: manual_sin_igv_bn con volumen de 10,000 copias B/N y monto de S/ 400

costo_copia_bn = 400 / 10,000 = 0.040 (S/ por copia)

Este cálculo se ejecuta en _get_costos_unitarios_vals() tanto al crear como al guardar el registro (con protección skip_recalc_costos para evitar recursión infinita).

5.6 Cálculo de Copias Facturables en el Contador

El contador siempre factura el máximo entre las copias reales y el volumen mensual contratado (garantía de renta mínima):

copias_facturables_bn    = max(total_copias_bn,    volumen_mensual_bn)
copias_facturables_color = max(total_copias_color, volumen_mensual_color)

5.7 Cálculo de Fecha de Facturación

El sistema calcula automáticamente la siguiente fecha de facturación basada en el dia_facturacion configurado en la máquina:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

# 1. Tomar el día configurado (ej: día 30)

# 2. Ajustar al último día del mes si no existe ese día

# 3. Si ya pasó la fecha en el mes actual, mover al siguiente mes

# 4. Si cae domingo, mover al sábado anterior

6. Gestión de Servicios Técnicos

6.1 Flujo Completo de un Servicio

Paso 1: Creación (desde portal, QR, o internamente). Al crear, el sistema automáticamente completa los datos de contacto desde el cliente de la máquina, asigna una secuencia numérica, genera tokens únicos de seguimiento y evaluación, y envía un email de confirmación al cliente.

Paso 2: Asignación del Técnico (action_asignar_tecnico()). Requiere tecnico_id configurado. Cambia el estado a asignado, crea actividades en Odoo para el supervisor y el técnico (si tiene cuenta de usuario), y notifica al técnico por el chatter.

Paso 3: Confirmar Visita (action_confirmar_visita()). Requiere fecha_programada. Cambia el estado a confirmado y envía email al cliente con el técnico y la fecha asignados.

Paso 4: En Ruta (action_iniciar_ruta()). El técnico indica que está en camino. Cambia el estado a en_ruta.

Paso 5: En Sitio (action_iniciar_servicio()). Check-in del técnico. Registra fecha_inicio y cambia el estado a en_sitio.

Paso 6: Completar (action_completar_servicio()). Requiere trabajo_realizado. Registra fecha_fin, calcula duración real y SLA, opcionalmente crea una lectura de contador, y envía email de servicio completado.

Evaluación Post-Servicio: El cliente recibe un enlace único (token) para evaluar el servicio de 1 a 5 estrellas. Solo puede evaluarse una vez.

6.2 Seguimiento Público

Cualquier persona con el token de seguimiento puede ver el estado actual del servicio en /service/track/{token} sin necesidad de autenticarse. La página muestra la línea de tiempo completa del servicio.

6.3 Datos de Color para Vistas Kanban/Lista

El campo color (computed) asigna colores de Odoo según la prioridad y estado:

CondiciónColor OdooVisual

Prioridad Crítica1Rojo

Prioridad Alta3Naranja

Completado + SLA cumplido10Verde

Completado + SLA no cumplido9Rosa

Cancelado4Azul claro

Pausado5Amarillo

Normal0Sin color

7. Control de Contadores

7.1 Registro Manual de Lecturas

El usuario accede al menú de Contadores, selecciona la máquina, e ingresa el contador_actual_bn y contador_actual_color. El sistema automáticamente recupera el contador anterior de la última lectura confirmada o facturada.

7.2 Actualización Automática desde PrintTracker

Si la máquina está mapeada con PrintTracker Pro (pt_device_id configurado), el botón "Actualizar desde PrintTracker" realiza los siguientes pasos:

- Obtiene la configuración activa de PrintTracker.

- Busca el dispositivo en el endpoint /currentMeter usando paginación (100 registros por página, máximo 10 páginas).

- Extrae totalBlack y totalColor de la estructura pageCounts.default.

- Valida que los nuevos valores no sean inferiores a los anteriores.

- Detecta si es primera lectura (contadores en 0) y omite la validación de incrementos.

- Actualiza los campos contador_actual_bn y contador_actual_color.

- Registra la actualización en el chatter.

7.3 Generación de Lecturas Automáticas (Cron)

El cron generate_monthly_readings se ejecuta diariamente y crea lecturas en estado borrador para todas las máquinas cuya fecha de facturación coincida con el día actual.

7.4 Confirmación y Validaciones

Al confirmar (action_confirm()), el sistema valida que:

- contador_actual_bn >= contador_anterior_bn

- contador_actual_color >= contador_anterior_color

- Si está habilitado informe_por_usuario: la suma de copias por usuario coincide exactamente con el total del contador

7.5 Creación de Facturas

Factura individual (action_create_invoice()): Crea una factura (account.move) con líneas separadas para B/N y color. La fecha de la factura usa fecha_emision_factura (si existe) o la fecha actual.

Factura consolidada (action_create_multiple_invoices()): Agrupa múltiples lecturas del mismo cliente en una sola factura, con una línea por equipo y tipo de copia.

Los precios de las líneas de factura usan los subtotales calculados por el contador (subtotal_bn, subtotal_color), que ya incluyen el descuento proporcionalmente distribuido pero excluyen el IGV.

7.6 Informe Detallado por Usuarios Internos

Si una máquina tiene usuarios internos registrados (copier.machine.user), se puede activar el informe por usuario en la lectura. El usuario carga los usuarios con el botón "Cargar Usuarios Asociados" y luego ingresa la cantidad de copias de cada departamento/empresa. Al confirmar, el sistema valida que la suma de copias por usuario coincida con el total del contador.

8. Stock de Máquinas de Segunda Mano

8.1 Proceso de Importación y Preparación

Las máquinas de segunda mano siguen un flujo de preparación antes de estar disponibles para venta: importación → descarga → revisión (checklist) → disponible → reservada → venta.

8.2 Checklist de Revisión

Cada máquina en stock tiene un checklist configurable con items precargados desde data/checklist_items_data.xml. Los items se clasifican en tres tipos: componente, función, y apariencia, y pueden aplicar a todas las máquinas, solo color, o solo monocromas.

8.3 Catálogo Web Público

Las máquinas disponibles se publican automáticamente en el sitio web en /equipos-disponibles con fotos, especificaciones y precio. Los visitantes pueden reservar máquinas desde el sitio web sin necesidad de registrarse.

8.4 Gestión de Reservas con Temporizador

Al reservar, el sistema registra reserved_by y reserved_date. Si el pago no se verifica en el tiempo establecido, el sistema puede liberar la reserva automáticamente.

9. Portal Web y Sitio Web

9.1 Portal del Cliente (/my/copier/equipments)

El portal permite al cliente autenticado ver sus equipos en alquiler, filtrar por estado de contrato (todos, activos, vencidos), acceder al detalle de cada equipo (especificaciones, series, contrato), enviar solicitudes de servicio técnico, consultar el historial de lecturas de contador, y descargar reportes de lecturas en PDF.

9.2 Formulario Público de Solicitud de Servicio (/public/service_request)

Accesible sin autenticación, diseñado para ser accedido desde el código QR de la etiqueta de la máquina. Muestra información del equipo, permite seleccionar el tipo de problema, ingresar datos de contacto, y enviar la solicitud.

9.3 Seguimiento Público de Servicio (/service/track/{token})

Página pública que muestra el estado actual del ticket, la línea de tiempo de eventos, los datos del técnico asignado y el vehículo, y el enlace de evaluación una vez completado.

9.4 Evaluación Pública (/service/evaluate/{token})

Formulario de una sola página (sin autenticación) para que el cliente evalúe el servicio de 1 a 5 estrellas con comentario opcional. El token solo puede usarse una vez.

9.5 Catálogo de Stock Web

El sitio web publica las máquinas disponibles para venta con vista de lista y vista kanban, filtros por marca y tipo, y formulario de contacto/reserva.

9.6 Solicitudes de Tóner (/toner_request)

Formulario web para que los clientes soliciten tóner para sus máquinas sin necesidad de llamar.

9.7 Portal de Contadores

Vista especial para el cliente donde puede ver el historial de sus lecturas de contador, el resumen de copias del período, y los totales calculados.

9.8 Menú Público de Equipo (/public/equipment_menu)

Página de menú accesible desde el QR de la máquina que muestra opciones rápidas: solicitar servicio técnico, solicitar tóner, asistencia remota, ver contadores, y descargar manuales.

10. Integraciones Externas

10.1 PrintTracker Pro

PrintTracker Pro es un servicio de monitoreo remoto de impresoras que lee automáticamente los contadores de las máquinas a través de un agente de software instalado en la red del cliente.

Configuración (copier.printtracker.config)

CampoDescripción

api_urlURL base: https://papi.printtrackerpro.com/v1

api_keyToken de autenticación

entity_bbbb_idID de la entidad raíz en PrintTracker

timeout_secondsTimeout de peticiones (default: 30s)

max_retriesReintentos ante fallo (default: 3)

Mapeo de Máquinas

Para vincular una máquina de Odoo con PrintTracker, se usa el botón "Mapear con PrintTracker" en el formulario del contrato. El sistema busca el dispositivo por número de serie usando paginación en el endpoint /entity/{id}/device, con lotes de 100 dispositivos por página y hasta 50 páginas.

Estructura de Datos PrintTracker

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

{

  "deviceKey": "abc123...",

  "serialNumber": "SERIE123",

  "pageCounts": {

    "default": {

      "totalBlack": { "value": 125000 },

      "totalColor": { "value": 45000 }

    }

  },

  "timestamp": "2025-01-15T10:30:00.000Z"

}

11. Sistema de Notificaciones WhatsApp

11.1 Configuración de la API Baileys

El módulo integra WhatsApp a través de Baileys API, una implementación no oficial del protocolo de WhatsApp que funciona como servidor local.

Configuración (whatsapp.config)

CampoDescripción

api_urlURL local del servidor Baileys (ej: http://localhost:3000)

api_keyClave de autenticación

session_nameNombre de sesión de WhatsApp

is_connectedEstado de conexión

auto_verify_numbersVerificar números antes de enviar

log_messagesRegistrar envíos en logs del servidor

Solo puede haber una configuración activa por compañía. Al activar una, las demás se desactivan automáticamente.

Endpoints de la API Utilizada

EndpointMétodoUso

/api/statusGETVerificar estado de conexión

/api/check-numberPOSTVerificar si número existe en WhatsApp

/api/send/textPOSTEnviar mensaje de texto

/api/send/documentPOSTEnviar PDF u otro documento

/api/send/imagePOSTEnviar imagen

/api/send/videoPOSTEnviar video

/api/send/audioPOSTEnviar audio

/qrGETPágina para escanear QR de sesión

11.2 Normalización de Números de Teléfono

El método clean_phone_number() normaliza cualquier formato al estándar internacional (código de país Perú 51 + 9 dígitos):

"987654321"      → "51987654321"  ✅
"+51 987 654 321" → "51987654321"  ✅
"0987654321"     → "51987654321"  ✅
"51987654321"    → "51987654321"  ✅

11.3 Envío de Cotizaciones por WhatsApp

El botón "Enviar por WhatsApp" en el formulario de cotización abre el wizard whatsapp.send.quotation.wizard, que permite seleccionar uno o varios números de teléfono, adjuntar el PDF de la cotización generado por el sistema de reportes, y añadir un mensaje personalizado. El wizard multi-cotización permite enviar varias cotizaciones a la vez a múltiples destinatarios.

11.4 Plantillas de Mensajes para Servicios

Las plantillas de notificación de servicio se configuran en whatsapp.service.template y se usan para enviar notificaciones automáticas en los diferentes estados del servicio técnico.

12. Almacenamiento en la Nube (pCloud)

12.1 Configuración de pCloud

El módulo integra pCloud como servicio de almacenamiento para documentos del cliente. Permite organizar documentos en carpetas por cliente o contrato y compartir enlaces seguros.

12.2 Gestión de Carpetas y Archivos

El modelo pcloud.folder.file mantiene un árbol de carpetas y archivos sincronizado con pCloud. Los archivos se pueden visualizar directamente en Odoo o compartir mediante un enlace público.

12.3 Descargas Públicas Controladas

El controlador PcloudPublico gestiona las descargas públicas, verificando que el partner tenga el campo allow_downloads activo antes de permitir cualquier descarga.

13. Manuales y Documentación PDF Segura

13.1 Visualización Segura de PDFs

Los manuales se visualizan en el navegador usando PDF.js sin posibilidad de descarga directa. El controlador de manuales sirve el archivo en fragmentos al visor, dificultando la captura del PDF completo.

13.2 Organización por Categorías

Los manuales (secure_pdf_viewer.manual) se organizan en categorías (secure_pdf_viewer.category) para facilitar su búsqueda. Cada acceso al manual incrementa el contador access_count.

13.3 Permisos de Acceso

Los manuales públicos son legibles por el grupo base.group_public (sin autenticación), pero solo editables por usuarios internos.

14. Cotizaciones y Facturación

14.1 Cotización de Alquiler

El formulario principal del módulo es la cotización de alquiler (copier.company). El proceso habitual es:

- Crear la cotización con todos los datos de la máquina y el cliente.

- Generar el QR de la máquina con generar_qr_code().

- Imprimir el reporte de cotización (PDF con toda la información del contrato).

- Enviar por email con la plantilla email_template_propuesta_alquiler o por WhatsApp.

- Al aprobar, cambiar el estado de la máquina a "Alquilada".

14.2 Cotizaciones Múltiples (copier.quotation)

El modelo de cotizaciones múltiples permite agrupar varias máquinas en una sola propuesta comercial con un único precio total.

14.3 Facturación desde Contadores

La generación de facturas se produce desde la vista de contadores confirmados. El sistema crea facturas en account.move con las líneas correspondientes a copias B/N y color, usando los productos configurados en la máquina (producto_facturable_bn_id, producto_facturable_color_id).

Las facturas se generan sin IGV en el precio unitario (ya que el módulo calcula el subtotal sin IGV), permitiendo que Odoo aplique el impuesto correspondiente al producto.

15. Reportes e Impresión

15.1 Reporte de Cotización de Alquiler

Acción: action_report_report_cotizacion_alquiler

Modelo reporte: report.copier_company.cotizacion_view

Contenido: Datos completos del cliente, máquina, plazos, costos unitarios (con indicación de IGV incluido o no), tabla de cálculo de renta mensual, código QR de la máquina.

15.2 Reporte de Lecturas de Contador

Acción: action_report_counter_readings

Modelo reporte: report.copier_company.report_counter_readings

Contenido: Tabla de lecturas por máquina (máquinas monocromas separadas de máquinas color), subtotales con y sin descuento, IGV, total general. Requiere que todos los registros seleccionados pertenezcan al mismo cliente.

15.3 Reporte de Servicio Técnico

Contenido: Datos del servicio, cliente, técnico asignado, trabajo realizado, contadores registrados, firma del cliente.

15.4 Etiquetas (Stickers)

El controlador sticker_controller.py genera etiquetas QR para las máquinas que incluyen código QR (que apunta al menú público del equipo), nombre del modelo, número de serie, marca, y datos de Copier Company.

El controlador sticker_print.py maneja la impresión masiva de etiquetas seleccionando múltiples registros desde la vista de lista.

16. Seguridad y Control de Accesos

16.1 Grupos de Acceso

El módulo utiliza los grupos estándar de Odoo:

GrupoNivel de Acceso

base.group_publicSolo lectura en catálogos públicos

base.group_portalLectura en equipos propios, creación de solicitudes

base.group_userAcceso completo a todas las funcionalidades del módulo

base.group_systemAcceso administrativo completo incluyendo configuración

16.2 Permisos por Modelo

La tabla completa de permisos se encuentra en security/ir.model.access.csv. A continuación se resumen los más relevantes:

ModeloPortalUsuarioAdmin

copier.companyCRUDCRUDCRUD

copier.counterRCRUD (manager)CRUD

copier.service.requestRC (sin delete)CRUDCRUD

copier.stockRCRUDCRUD

whatsapp.config—RCRUD

copier.printtracker.config—RCWCRUD

secure_pdf_viewer.manualRCRUDCRUD

Leyenda: R=Leer, C=Crear, W=Escribir, D=Eliminar

16.3 Control de Descargas

El modelo res.partner (contactos) tiene el campo allow_downloads que controla si ese contacto puede descargar archivos desde pCloud. Esto debe configurarse manualmente por el administrador.

17. Automatizaciones y Cron Jobs

17.1 Verificación de Contratos por Vencer

Método: CopierCompany._cron_check_contract_expiration()

Frecuencia: Diaria

Acción: Recorre todos los contratos con estado vigente o por_vencer y fecha de fin definida. Si 0 < días_restantes <= dias_notificacion y el estado no es por_vencer, cambia el estado, publica una nota en el chatter, y crea actividades para el responsable o el equipo de ventas. Si los días restantes llegan a 0, cambia el estado a finalizado.

17.2 Generación de Lecturas Mensuales

Método: CopierCounter.generate_monthly_readings()

Frecuencia: Diaria

Acción: Para cada máquina en estado "Alquilada" con dia_facturacion configurado, verifica si hoy es la fecha de facturación. Si es así y no existe ya una lectura para ese período, crea una lectura en borrador con los contadores anteriores pre-cargados.

17.3 Cron de Alertas WhatsApp

Definido en data/cron.xml, gestiona el envío periódico de alertas de contratos por vencer a través de WhatsApp.

18. Activos Frontend (JS/CSS)

Todos los activos de frontend se cargan en el bundle website.assets_frontend.

18.1 Estilos CSS

ArchivoPropósito

counter_charts.cssEstilos para los gráficos de contadores

cotizacion_styles.cssFormulario web de cotizaciones

PcloudDescargas.cssInterfaz de descarga de archivos pCloud

copier_list.cssLista de máquinas en el sitio web

18.2 Scripts JavaScript

ArchivoPropósito

counter_charts.jsGráficos interactivos con Chart.js para histórico de contadores

cotizacion.jsLógica del formulario de cotización web

PcloudDescargas.jsNavegador de archivos pCloud en el portal

copier_homepage_scripts.jsScripts de la página de inicio

copier_services_scripts.jsScripts de la página de servicios

manuals.jsVisor seguro de PDFs con PDF.js

pdf.js y pdf.worker.jsArchivos de soporte para PDF.js (versión local)

18.3 Plantillas QWeb de Frontend

El archivo static/src/xml/counter_charts_templates.xml contiene las plantillas OWL/QWeb para los widgets de gráficos de contadores, registrado en web.assets_qweb.

19. Guía de Instalación y Configuración

19.1 Requisitos Previos

Antes de instalar el módulo, asegúrese de tener instaladas las dependencias Python:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

pip install requests requests_toolbelt qrcode Pillow

Y el binario del sistema:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

# Debian/Ubuntu

sudo apt-get install wkhtmltopdf

19.2 Instalación del Módulo

- Copiar el directorio copier_company al directorio de addons de Odoo.

- Reiniciar el servidor de Odoo.

- Activar el modo desarrollador en Odoo.

- Ir a Aplicaciones → Actualizar lista de aplicaciones.

- Buscar "Gestión de Fotocopiadoras" e instalar.

19.3 Configuración Inicial

Paso 1: Datos Básicos del Catálogo

Ir a Gestión de Equipos → Configuración y crear:

- Marcas de máquinas (Canon, Konica Minolta, Ricoh, etc.)

- Modelos de máquinas con sus especificaciones

- Accesorios disponibles

- Tipos de problemas técnicos para el servicio

Paso 2: Productos de Facturación

Crear en Odoo dos productos del tipo "Servicio":

- "Alquiler de Máquina Fotocopiadora Blanco y Negro"

- "Alquiler de Máquina Fotocopiadora Color"

Asignar la cuenta de ingresos correspondiente a cada producto.

Paso 3: Configuración de WhatsApp (Opcional)

Ir a Configuración → WhatsApp API Config y crear una configuración con la URL de su instancia de Baileys API y la API key. Verificar la conexión y escanear el código QR de WhatsApp.

Paso 4: Configuración de PrintTracker (Opcional)

Ir a Configuración → PrintTracker Pro y crear una configuración con la URL de la API, el API key, y el ID de entidad principal. Probar la conexión.

Paso 5: Configuración de pCloud (Opcional)

Ir a Configuración → pCloud y configurar las credenciales de la API de pCloud.

19.4 Configuración por Máquina

Para cada máquina en alquiler:

- Asignar los productos de facturación (B/N y color) en el formulario.

- Configurar el día de facturación (1-31).

- Opcionalmente, mapear con PrintTracker usando el número de serie.

- Generar el código QR con el botón correspondiente.

- Imprimir la etiqueta (sticker) para pegar en la máquina.

20. Flujos de Trabajo Principales

20.1 Incorporar una Nueva Máquina en Alquiler

1. Crear Modelo (si no existe) → Gestión de Equipos > Modelos
2. Crear Cotización → Gestión de Equipos > Nueva Cotización
   - Seleccionar modelo y serie
   - Asignar cliente (buscar o crear por RUC/DNI)
   - Configurar tipo de impresora, formato, accesorios
   - Definir volúmenes mensuales y costos por copia
   - Establecer fecha de inicio y duración del contrato
   - Asignar productos de facturación B/N y color
3. Generar QR → botón "Generar QR"
4. Imprimir cotización → botón "Imprimir"
5. Enviar al cliente → email o WhatsApp
6. Al aceptar: cambiar estado de máquina a "Alquilada"
7. Imprimir sticker → botón "Stickers" e imprimir etiqueta para la máquina
8. Mapear con PrintTracker → botón "Mapear con PrintTracker" (opcional)

20.2 Facturación Mensual

1. Ir a Contadores > Lecturas
2. Las lecturas se crean automáticamente por el cron diario (en estado borrador)
   O crear manualmente: botón "Crear Lectura"
3. Ingresar los contadores actuales B/N y Color
   O actualizar desde PrintTracker: botón "Actualizar desde PrintTracker"
4. Verificar los cálculos de copias facturables y totales
5. Confirmar la lectura → botón "Confirmar"
6. Generar factura → botón "Crear Factura"
   O factura consolidada (varios equipos): seleccionar varios y "Factura Consolidada"
7. La factura se crea en Odoo en estado borrador para revisión
8. Validar la factura desde el módulo de Contabilidad

20.3 Gestión de un Servicio Técnico

Cliente (desde QR de la máquina):
1. Escanear QR de la máquina
2. Seleccionar "Solicitar Servicio Técnico"
3. Completar formulario de problema
4. Recibe email de confirmación con número de ticket

Administrador:
5. Ver solicitud en Servicio Técnico > Solicitudes
6. Asignar técnico: botón "Asignar Técnico"
7. Confirmar fecha: botón "Confirmar Visita"
8. Cliente recibe email con técnico y fecha asignados

Técnico:
9. Indicar en ruta: botón "En Ruta"
10. Llegar al sitio: botón "Iniciar Servicio"
11. Registrar diagnóstico, trabajo realizado, contadores, fotos
12. Completar: botón "Completar Servicio"

Post-Servicio:
13. Cliente recibe email con enlace de evaluación
14. Cliente evalúa de 1 a 5 estrellas (token de un solo uso)

20.4 Renovación de Contrato

1. El sistema alerta automáticamente (X días antes) mediante:
   - Nota en el chatter del contrato
   - Actividad asignada al responsable
   - Estado cambia a "Por Vencer"
2. Negociar términos de renovación con el cliente
3. Ejecutar renovación: botón "Renovar Contrato"
   - Se registra el período anterior en el historial
   - La nueva fecha de inicio es el día siguiente al fin anterior
   - Se calcula la nueva fecha de fin según la duración configurada
   - El estado vuelve a "Renovado"

21. Referencia de la API Interna

21.1 Rutas HTTP del Módulo

Portal Autenticado

RutaMétodoDescripción

/my/copier/equipmentsGETLista de equipos del cliente

/my/copier/equipment/<id>GETDetalle de un equipo

/my/copier/equipment/<id>/ticketGETCrear ticket para equipo

/my/copier/countersGETLecturas de contador del cliente

Público (Sin Autenticación)

RutaMétodoDescripción

/public/equipment_menuGETMenú de acceso rápido del equipo (desde QR)

/public/service_requestGET/POSTFormulario de solicitud de servicio

/service/track/<token>GETSeguimiento de solicitud

/service/evaluate/<token>GET/POSTEvaluación del servicio

/toner_requestGET/POSTSolicitud de tóner

/remote_assistanceGET/POSTSolicitud de asistencia remota

Sitio Web

RutaMétodoDescripción

/equipos-disponiblesGETCatálogo de máquinas en venta

/equipos-disponibles/<id>GETDetalle de máquina en venta

/stickers/printGETImpresión de etiquetas

/sticker/generate/<id>GETGenerar sticker individual

/manualesGETLista de manuales

pCloud

RutaMétodoDescripción

/cloud/filesGETLista de archivos del cliente

/cloud/download/<id>GETDescarga controlada de archivo

21.2 Métodos de Modelos Principales

CopierCompany

MétodoDescripción

generar_qr_code()Genera QR que apunta a /public/equipment_menu?copier_company_id=ID

generar_sticker_corporativo(layout)Abre URL de generación de sticker (horizontal/vertical)

action_crear_servicio_tecnico()Abre formulario de nuevo servicio pre-cargado

action_print_stickers()Impresión masiva de stickers

action_renovar_contrato()Renueva el contrato y registra en historial

action_print_report()Imprime cotización de alquiler

send_whatsapp_report()Abre wizard de envío por WhatsApp

action_send_whatsapp_multi()Envío múltiple por WhatsApp

enviar_correo_propuesta()Envía email de propuesta al cliente

get_label_costo_bn()Retorna texto formateado del costo B/N para el reporte

get_label_costo_color()Retorna texto formateado del costo color para el reporte

CopierCounter

MétodoDescripción

action_confirm()Confirma la lectura con validaciones

action_create_invoice()Crea factura individual

action_create_multiple_invoices()Crea facturas consolidadas por cliente

action_update_from_printtracker()Actualiza contadores desde PrintTracker

action_send_counter_email()Envía email con reporte de lecturas

cargar_usuarios_asociados()Carga usuarios internos del equipo

WhatsAppConfig

MétodoDescripción

check_connection(silent)Verifica conexión con Baileys API

send_message(phone, message)Envía mensaje de texto

send_media(phone, file_data, media_type, caption, filename)Envía archivo multimedia

verify_number(phone)Verifica si un número existe en WhatsApp

clean_phone_number(phone, country_code)Normaliza formato de número

get_active_config()Obtiene configuración activa de la compañía

22. Glosario

TérminoDefinición

B/NBlanco y Negro. Tipo de copia o impresión monocromática.

Baileys APIImplementación no oficial del protocolo de WhatsApp Web que permite enviar mensajes programáticamente.

ChatterSistema de mensajería y registro de cambios de Odoo adjunto a cada registro.

ContómetroOdómetro de copias de una fotocopiadora. Cuenta el número total de impresiones desde su fabricación.

Copias FacturablesEl máximo entre las copias reales del período y el volumen mínimo mensual contratado.

CT-XXXXXXFormato del número de cotización/contrato generado por el módulo.

IGVImpuesto General a las Ventas. Equivalente al IVA en Perú. Tasa estándar: 18%.

MonocromaMáquina que solo imprime en blanco y negro.

pCloudServicio de almacenamiento en la nube europeo utilizado para gestionar documentos de clientes.

PENCódigo ISO 4217 del Sol peruano (S/). Moneda base del módulo.

PrintTracker ProSoftware de gestión remota de impresoras que lee contadores automáticamente a través de un agente.

QR de MáquinaCódigo QR único por equipo que dirige al menú público de acciones rápidas.

RUCRegistro Único de Contribuyentes. Número de identificación fiscal en Perú (11 dígitos).

SerieNúmero de serie del equipo. Identificador único físico de cada máquina.

SLAService Level Agreement. Acuerdo de nivel de servicio que define los tiempos máximos de respuesta y resolución.

StickerEtiqueta adhesiva con código QR, modelo y serie de la máquina, diseñada para pegarse en el equipo.

Token de SeguimientoCadena aleatoria única que permite acceder a la página de seguimiento de un ticket sin autenticarse.

Volumen MensualNúmero de copias mensuales incluidas en el contrato sin costo adicional. El exceso se factura al mismo precio unitario.

WizardFormulario emergente (transient model) para ejecutar acciones que requieren confirmación o datos adicionales.

Notas Adicionales

Soporte Multi-Compañía

El módulo soporta instalaciones con múltiples compañías. La configuración de WhatsApp y los permisos están segmentados por compañía. Las facturas y los contratos siempre están asociados a env.company.

Idioma

El módulo está desarrollado completamente en español (Peru), incluyendo los textos de la interfaz, los mensajes del chatter y los reportes. No incluye archivos de traducción .po para otros idiomas.

Código QR y Acceso Público

El código QR generado para cada máquina apunta a la URL:

{web.base.url}/public/equipment_menu?copier_company_id={ID}

Esta URL es completamente pública (auth='public') y no requiere autenticación, lo que permite al cliente o al usuario de la máquina acceder rápidamente a las funciones de soporte.

Compatibilidad de Versión de Odoo

El módulo está desarrollado para Odoo 17 (se infiere por las sintaxis de código, uso de Domain.AND(), fields.Boolean() con parámetros modernos, y el sistema de assets website.assets_frontend).

Documentación generada automáticamente a partir del análisis del código fuente del repositorio copier_company.
