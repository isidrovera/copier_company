from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import calendar
import logging
_logger = logging.getLogger(__name__)


class CopierCounter(models.Model):
    _name = 'copier.counter'
    _description = 'Control de Contadores de Máquinas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
   

    name = fields.Char('Referencia', default='New', copy=False, readonly=True)
    
    # Campos de relación y fechas
    maquina_id = fields.Many2one(
        'copier.company', 
        string='Máquina',
        required=True,
        tracking=True,
        domain=[('estado_maquina_id.name', '=', 'Alquilada')]
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',related="maquina_id.payment_term_id", string='Términos de pago',
        help='Términos de pago para esta transacción'
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        store=True,
        tracking=True,
        readonly=True,
        index=True,
        copy=False,
        help="Cliente congelado al momento de crear el servicio. No cambia si la máquina cambia de cliente."
    )
    serie = fields.Char(
        related='maquina_id.serie_id',
        string='Serie',
        store=True
    )
    ubicacion = fields.Char(
        string='Ubicación',
        store=True,
        readonly=True,
        copy=False,
        help="Ubicación congelada al momento de crear el servicio."
    )
    fecha = fields.Date(
        'Fecha de Lectura',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    fecha_facturacion = fields.Date(
        'Fecha de Facturación',
        required=True,
        tracking=True
    )
    mes_facturacion = fields.Char(
        'Mes de Facturación',
        compute='_compute_mes_facturacion',
        store=True
    )

    fecha_emision_factura = fields.Date(
        'Fecha de Emisión',
        help="Fecha que aparecerá en la factura. Si está vacío, usa la fecha de hoy"
    )
    def action_send_counter_email(self):
        self.ensure_one()
        template = self.env.ref('copier_company.email_template_counter_readings', raise_if_not_found=False)
        if not template:
            raise UserError("No se encontró la plantilla de correo 'email_template_counter_readings'.")

        if not self.cliente_id or not self.cliente_id.email:
            raise UserError("El cliente no tiene un correo configurado. Verifique el campo Email en el contacto.")

        # Debug para ver a quién va
        _logger.info("📧 Enviando correo de lecturas para counter %s a %s", self.name, self.cliente_id.email)

        mail_id = template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Correo enviado',
                'message': f'Se ha enviado el reporte de lecturas a {self.cliente_id.email}.',
                'type': 'success',
                'sticky': False,
            }
        }

    # Contadores B/N
    contador_anterior_bn = fields.Integer(
        'Contador Anterior B/N',
        readonly=False,
        required=True,  # Agregado required
        copy=False,     # No copiar en duplicados
        tracking=True   # Seguimiento de cambios
    )
    contador_actual_bn = fields.Integer(
        'Contador Actual B/N',
        required=True,
        tracking=True
    )
    total_copias_bn = fields.Integer(
        'Total Copias B/N',
        compute='_compute_copias',
        store=True
    )
    exceso_bn = fields.Integer(
        'Exceso B/N',
        compute='_compute_excesos',
        store=True,
        help="Copias que exceden el volumen mensual contratado"
    )
    copias_facturables_bn = fields.Integer(
        'Copias Facturables B/N',
        compute='_compute_facturables',
        store=True,
        help="Total de copias a facturar (mínimo mensual o real)"
    )

    # Contadores Color
    contador_anterior_color = fields.Integer(
        'Contador Anterior Color',
        readonly=False,
        required=True,  # Agregado required
        copy=False,     # No copiar en duplicados
        tracking=True   # Seguimiento de cambios
    )
    contador_actual_color = fields.Integer(
        'Contador Actual Color',
        tracking=True
    )
    total_copias_color = fields.Integer(
        'Total Copias Color',
        compute='_compute_copias',
        store=True
    )
    exceso_color = fields.Integer(
        'Exceso Color',
        compute='_compute_excesos',
        store=True,
        help="Copias color que exceden el volumen mensual contratado"
    )
    copias_facturables_color = fields.Integer(
        'Copias Facturables Color',
        compute='_compute_facturables',
        store=True,
        help="Total de copias color a facturar (mínimo mensual o real)"
    )
    precio_bn_sin_igv = fields.Float(
        'Precio B/N sin IGV',
        compute='_compute_precios_sin_igv',
        store=True,
        digits=(16, 6)  # Aumentamos la precisión decimal
    )
    precio_color_sin_igv = fields.Float(
        'Precio Color sin IGV',
        compute='_compute_precios_sin_igv',
        store=True,
        digits=(16, 6)  # Aumentamos la precisión decimal
    )


    # Campos financieros
    currency_id = fields.Many2one(
        'res.currency',
        related='maquina_id.currency_id',
        string='Moneda'
    )

    tipo_maquina = fields.Selection(
        related='maquina_id.tipo',
        string='Tipo de Máquina',
        store=True,
        readonly=True,
        help='Tipo de máquina usado para organizar la vista y ocultar los campos de color cuando corresponde.'
    )
   
  
 
    subtotal = fields.Monetary(
        'Subtotal',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    igv = fields.Monetary(
        'IGV (18%)',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    total = fields.Monetary(
        'Total',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('invoiced', 'Facturado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    @api.depends('maquina_id', 
                'maquina_id.precio_bn_incluye_igv', 
                'maquina_id.precio_color_incluye_igv',
                'maquina_id.costo_copia_bn', 
                'maquina_id.costo_copia_color')
    def _compute_precios_sin_igv(self):
        """Convierte los precios a su valor sin IGV manteniendo precisión completa"""
        for record in self:
            if record.maquina_id:
                # Obtener precios de la máquina
                precio_bn = float(record.maquina_id.costo_copia_bn or 0.0)
                precio_color = float(record.maquina_id.costo_copia_color or 0.0)

                # Convertir a precio sin IGV si incluye IGV (manteniendo toda la precisión)
                record.precio_bn_sin_igv = precio_bn / 1.18 if record.maquina_id.precio_bn_incluye_igv else precio_bn
                record.precio_color_sin_igv = precio_color / 1.18 if record.maquina_id.precio_color_incluye_igv else precio_color
            else:
                record.precio_bn_sin_igv = 0.0
                record.precio_color_sin_igv = 0.0
    @api.model
    def create(self, vals_list):
        """
        Crea lecturas de contador manteniendo historial correcto.

        Importante:
        - cliente_id se guarda como snapshot del cliente actual de la máquina.
        - Si luego la máquina cambia de cliente, las lecturas antiguas no cambian.
        - También conserva la lógica de contadores anteriores y secuencia.
        """

        # Asegurar compatibilidad con dict individual y lista
        single_create = isinstance(vals_list, dict)
        if single_create:
            vals_list = [vals_list]

        for vals in vals_list:
            maquina = False

            if vals.get('maquina_id'):
                maquina = self.env['copier.company'].browse(vals.get('maquina_id')).exists()

            # ==========================================================
            # SNAPSHOT DEL CLIENTE
            # ==========================================================
            # Solo se asigna si viene máquina y no viene cliente manualmente.
            # Esto evita que el contador dependa del cliente actual de la máquina.
            if maquina and not vals.get('cliente_id'):
                vals['cliente_id'] = maquina.cliente_id.id or False

            # ==========================================================
            # CONTADORES ANTERIORES
            # ==========================================================
            # Se mantiene tu lógica original, pero mejorando:
            # - incluye confirmed e invoiced
            # - solo busca si hay máquina
            if maquina and not vals.get('contador_anterior_bn'):
                ultima_lectura = self.search([
                    ('maquina_id', '=', maquina.id),
                    ('state', 'in', ['confirmed', 'invoiced']),
                ], limit=1, order='fecha desc, id desc')

                vals['contador_anterior_bn'] = ultima_lectura.contador_actual_bn if ultima_lectura else 0
                vals['contador_anterior_color'] = ultima_lectura.contador_actual_color if ultima_lectura else 0

            # ==========================================================
            # SECUENCIA
            # ==========================================================
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('copier.counter') or 'New'

        records = super(CopierCounter, self).create(vals_list)

        return records[0] if single_create else records
    @api.depends('fecha_facturacion', 'fecha_emision_factura')
    def _compute_mes_facturacion(self):
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        for record in self:
            # Usar fecha_emision_factura si existe, sino fecha_facturacion
            fecha_ref = record.fecha_emision_factura or record.fecha_facturacion
            if fecha_ref:
                record.mes_facturacion = f"{meses[fecha_ref.month]} {fecha_ref.year}"
    @api.constrains('fecha_emision_factura', 'fecha')
    def _check_fecha_emision(self):
        for record in self:
            if record.fecha_emision_factura and record.fecha:
                if record.fecha_emision_factura < record.fecha:
                    raise ValidationError(
                        "La fecha de emisión no puede ser anterior a la fecha de lectura."
                    )

    def action_confirm(self):
        """
        Confirma la lectura después de validar contadores y,
        cuando corresponde, el detalle de copias por usuario.
        """
        self.ensure_one()

        if self.contador_actual_bn < self.contador_anterior_bn:
            raise UserError(
                'El contador actual B/N no puede ser menor al anterior.'
            )

        if (
            self.maquina_id.tipo == 'color'
            and self.contador_actual_color < self.contador_anterior_color
        ):
            raise UserError(
                'El contador actual Color no puede ser menor al anterior.'
            )

        if self.informe_por_usuario and self.usuario_detalle_ids:
            total_bn_usuarios = sum(
                self.usuario_detalle_ids.mapped('cantidad_bn')
            )
            total_color_usuarios = sum(
                self.usuario_detalle_ids.mapped('cantidad_color')
            )

            if total_bn_usuarios != self.total_copias_bn:
                raise UserError(
                    f'Las copias B/N por usuario ({total_bn_usuarios}) '
                    f'no coinciden con el total del contador '
                    f'({self.total_copias_bn}).'
                )

            if (
                self.maquina_id.tipo == 'color'
                and total_color_usuarios != self.total_copias_color
            ):
                raise UserError(
                    f'Las copias Color por usuario ({total_color_usuarios}) '
                    f'no coinciden con el total del contador '
                    f'({self.total_copias_color}).'
                )

        _logger.info(
            "Confirmando counter %s | serie=%s | total_bn=%s | "
            "exceso_bn=%s | total_color=%s | exceso_color=%s | total=%s",
            self.name,
            self.serie,
            self.total_copias_bn,
            self.exceso_bn,
            self.total_copias_color,
            self.exceso_color,
            self.total,
        )

        self.write({'state': 'confirmed'})

    def get_fecha_factura_efectiva(self):
        """Devuelve la fecha efectiva que se usará en la factura"""
        self.ensure_one()
        return self.fecha_emision_factura or fields.Date.today()
    @api.onchange('maquina_id')
    def _onchange_maquina(self):
        """
        Al seleccionar una máquina:
        - Copia el cliente actual como snapshot.
        - Carga últimos contadores.
        - Calcula fecha de facturación según día configurado.
        """

        if not self.maquina_id:
            self.cliente_id = False
            self.contador_anterior_bn = 0
            self.contador_anterior_color = 0
            return

        # ==========================================================
        # SNAPSHOT DEL CLIENTE
        # ==========================================================
        # Este valor queda guardado en la lectura.
        # No será related, por eso no cambiará si la máquina cambia de cliente.
        self.cliente_id = self.maquina_id.cliente_id.id or False

        # ==========================================================
        # ÚLTIMA LECTURA
        # ==========================================================
        ultima_lectura = self.search([
            ('maquina_id', '=', self.maquina_id.id),
            ('state', 'in', ['confirmed', 'invoiced'])
        ], limit=1, order='fecha desc, id desc')

        self.contador_anterior_bn = ultima_lectura.contador_actual_bn if ultima_lectura else 0
        self.contador_anterior_color = ultima_lectura.contador_actual_color if ultima_lectura else 0

        # ==========================================================
        # FECHA DE FACTURACIÓN
        # ==========================================================
        if self.maquina_id.dia_facturacion:
            fecha_base = fields.Date.today()

            # Último día del mes actual
            ultimo_dia_mes = calendar.monthrange(fecha_base.year, fecha_base.month)[1]

            # Día válido dentro del mes
            dia = min(self.maquina_id.dia_facturacion, ultimo_dia_mes)

            # Fecha tentativa en el mes actual
            fecha_facturacion = fecha_base.replace(day=dia)

            # Si ya pasó, mover al mes siguiente
            if fecha_base > fecha_facturacion:
                fecha_facturacion = fecha_facturacion + relativedelta(months=1)

                ultimo_dia_mes_sig = calendar.monthrange(
                    fecha_facturacion.year,
                    fecha_facturacion.month
                )[1]

                dia = min(self.maquina_id.dia_facturacion, ultimo_dia_mes_sig)
                fecha_facturacion = fecha_facturacion.replace(day=dia)

            # Si cae domingo, mover a sábado
            if fecha_facturacion.weekday() == 6:
                fecha_facturacion -= timedelta(days=1)

            self.fecha_facturacion = fecha_facturacion

    @api.depends('contador_actual_bn', 'contador_anterior_bn',
                'contador_actual_color', 'contador_anterior_color')
    def _compute_copias(self):
        for record in self:
            record.total_copias_bn = (record.contador_actual_bn or 0) - (record.contador_anterior_bn or 0)
            record.total_copias_color = (record.contador_actual_color or 0) - (record.contador_anterior_color or 0)

    @api.depends('total_copias_bn', 'total_copias_color',
                'maquina_id.volumen_mensual_bn', 'maquina_id.volumen_mensual_color')
    def _compute_excesos(self):
        for record in self:
            record.exceso_bn = max(0, record.total_copias_bn - (record.maquina_id.volumen_mensual_bn or 0))
            record.exceso_color = max(0, record.total_copias_color - (record.maquina_id.volumen_mensual_color or 0))

    @api.depends('total_copias_bn', 'total_copias_color',
                'maquina_id.volumen_mensual_bn', 'maquina_id.volumen_mensual_color')

    @api.depends(
        'total_copias_bn',
        'total_copias_color',
        'exceso_bn',
        'exceso_color',
        'maquina_id.tipo_calculo',
        'maquina_id.volumen_mensual_bn',
        'maquina_id.volumen_mensual_color'
    )
    def _compute_facturables(self):
        """
        Calcula las copias facturables sin cambiar los nombres técnicos existentes.

        Reglas:
        - auto:
          Se factura como mínimo el volumen contratado o el consumo real si es mayor.
        - renta fija manual B/N:
          La renta fija cubre el volumen contratado B/N y solo se factura el excedente.
        - renta fija manual Color:
          La renta fija cubre el volumen contratado Color y solo se factura el excedente.
        - renta fija manual Total:
          La renta fija cubre ambos volúmenes y se facturan los excedentes B/N y Color.
        """
        tipos_renta_fija_bn = {
            'manual_sin_igv_bn',
            'manual_con_igv_bn',
            'manual_sin_igv_total',
            'manual_con_igv_total',
        }
        tipos_renta_fija_color = {
            'manual_sin_igv_color',
            'manual_con_igv_color',
            'manual_sin_igv_total',
            'manual_con_igv_total',
        }

        _logger.info("=== INICIO _compute_facturables ===")

        for record in self:
            maquina = record.maquina_id

            if not maquina:
                record.copias_facturables_bn = 0
                record.copias_facturables_color = 0
                _logger.warning(
                    "Counter ID %s sin máquina: copias facturables en cero.",
                    record.id,
                )
                continue

            tipo_calculo = maquina.tipo_calculo or 'auto'
            volumen_bn = maquina.volumen_mensual_bn or 0
            volumen_color = maquina.volumen_mensual_color or 0

            if tipo_calculo in tipos_renta_fija_bn:
                record.copias_facturables_bn = max(record.exceso_bn or 0, 0)
            else:
                record.copias_facturables_bn = max(
                    record.total_copias_bn or 0,
                    volumen_bn,
                )

            if maquina.tipo == 'color':
                if tipo_calculo in tipos_renta_fija_color:
                    record.copias_facturables_color = max(
                        record.exceso_color or 0,
                        0,
                    )
                else:
                    record.copias_facturables_color = max(
                        record.total_copias_color or 0,
                        volumen_color,
                    )
            else:
                record.copias_facturables_color = 0

            _logger.info(
                "Counter %s | tipo=%s | total_bn=%s | incluido_bn=%s | "
                "exceso_bn=%s | facturable_bn=%s | total_color=%s | "
                "incluido_color=%s | exceso_color=%s | facturable_color=%s",
                record.name or record.id,
                tipo_calculo,
                record.total_copias_bn,
                volumen_bn,
                record.exceso_bn,
                record.copias_facturables_bn,
                record.total_copias_color,
                volumen_color,
                record.exceso_color,
                record.copias_facturables_color,
            )

        _logger.info("=== FIN _compute_facturables ===")

    descuento_porcentaje = fields.Float(
        'Descuento (%)',
        compute='_compute_descuento_desde_maquina',
        store=True,
        help="Porcentaje de descuento de la máquina"
    )
    
# PASO 3: AGREGAR este método compute en copier.counter:

    @api.depends('maquina_id', 'maquina_id.descuento')
    def _compute_descuento_desde_maquina(self):
        """Obtiene el descuento de la máquina con logs para debugging"""
        _logger.info("=== INICIANDO _compute_descuento_desde_maquina ===")
        
        for record in self:
            try:
                if record.maquina_id:
                    descuento_maquina = record.maquina_id.descuento or 0.0
                    record.descuento_porcentaje = descuento_maquina
                    
                    _logger.info("Counter ID: %s - Descuento de máquina: %s%%", 
                               record.id, descuento_maquina)
                    
                    if descuento_maquina == 0.0:
                        _logger.warning("⚠️ La máquina %s no tiene descuento configurado", 
                                      record.maquina_id.secuencia)
                else:
                    record.descuento_porcentaje = 0.0
                    _logger.warning("⚠️ Counter sin máquina asociada")
                    
            except Exception as e:
                _logger.exception("Error obteniendo descuento: %s", str(e))
                record.descuento_porcentaje = 0.0
    def debug_descuento_maquina(self):
        """Debug específico para verificar el descuento"""
        self.ensure_one()
        
        _logger.info("=== DEBUG DESCUENTO MÁQUINA ===")
        _logger.info("Counter ID: %s", self.id)
        _logger.info("Serie: %s", self.serie)
        
        if self.maquina_id:
            _logger.info("Máquina ID: %s", self.maquina_id.id)
            _logger.info("Secuencia máquina: %s", self.maquina_id.secuencia)
            _logger.info("Descuento en company: %s%%", self.maquina_id.descuento)
            _logger.info("Descuento en counter: %s%%", self.descuento_porcentaje)
            
            # Verificar otros campos relevantes
            _logger.info("IGV company: %s%%", self.maquina_id.igv)
            _logger.info("Subtotal company: %s", self.maquina_id.subtotal_sin_igv)
            _logger.info("Total company: %s", self.maquina_id.total_facturar_mensual)
            
            # Verificar tipo de cálculo
            _logger.info("Tipo de cálculo: %s", self.maquina_id.tipo_calculo)
            
        else:
            _logger.error("❌ No hay máquina asociada al counter")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug Descuento',
                'message': f'Descuento: {self.descuento_porcentaje}%. Ver logs para detalles.',
                'type': 'info',
                'sticky': True,
            }
        }

# PASO 5: TAMBIÉN AGREGAR este método en copier.company para debug:

    def debug_totales_company(self):
        """Método de debug para copier.company"""
        _logger.info("=== DEBUG TOTALES COMPANY para %s ===", self.secuencia)
        self.ensure_one()
        
        try:
            _logger.info("CONFIGURACIÓN BÁSICA:")
            _logger.info("- Company ID: %s", self.id)
            _logger.info("- Secuencia: %s", self.secuencia)
            _logger.info("- Tipo de cálculo: %s", self.tipo_calculo)
            
            _logger.info("VOLÚMENES Y COSTOS:")
            _logger.info("- Volumen B/N: %s", self.volumen_mensual_bn)
            _logger.info("- Volumen Color: %s", self.volumen_mensual_color)
            _logger.info("- Costo B/N: %s", self.costo_copia_bn)
            _logger.info("- Costo Color: %s", self.costo_copia_color)
            
            _logger.info("CONFIGURACIÓN FINANCIERA:")
            _logger.info("- Descuento: %s%%", self.descuento)
            _logger.info("- IGV: %s%%", self.igv)
            
            _logger.info("RENTAS CALCULADAS:")
            _logger.info("- Renta B/N: %s", self.renta_mensual_bn)
            _logger.info("- Renta Color: %s", self.renta_mensual_color)
            
            _logger.info("TOTALES FINALES:")
            _logger.info("- Subtotal sin IGV: %s", self.subtotal_sin_igv)
            _logger.info("- Monto IGV: %s", self.monto_igv)
            _logger.info("- Total a facturar: %s", self.total_facturar_mensual)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Debug Company',
                    'message': f'Total: {self.total_facturar_mensual}. Ver logs para detalles.',
                    'type': 'info',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            _logger.exception("Error en debug_totales_company: %s", str(e))

    

    renta_fija_bn = fields.Monetary(
        'Renta Fija B/N',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help='Renta fija B/N sin IGV antes de descuento.'
    )
    monto_exceso_bn = fields.Monetary(
        'Monto Excedente B/N',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help='Importe sin IGV de las copias B/N excedentes antes de descuento.'
    )
    renta_fija_color = fields.Monetary(
        'Renta Fija Color',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help='Renta fija Color sin IGV antes de descuento.'
    )
    monto_exceso_color = fields.Monetary(
        'Monto Excedente Color',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help='Importe sin IGV de las copias Color excedentes antes de descuento.'
    )

    subtotal_antes_descuento = fields.Monetary(
        'Subtotal Antes Descuento',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help="Subtotal antes de aplicar descuento"
    )
    
    monto_descuento = fields.Monetary(
        'Monto Descuento',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
        help="Monto del descuento aplicado"
    )
    @api.depends('copias_facturables_bn', 'copias_facturables_color',
                'precio_bn_sin_igv', 'precio_color_sin_igv', 'descuento_porcentaje',
                'maquina_id.tipo_calculo', 'maquina_id.monto_mensual_bn', 
                'maquina_id.monto_mensual_color', 'maquina_id.monto_mensual_total')

    @api.depends(
        'copias_facturables_bn',
        'copias_facturables_color',
        'exceso_bn',
        'exceso_color',
        'precio_bn_sin_igv',
        'precio_color_sin_igv',
        'descuento_porcentaje',
        'maquina_id.tipo',
        'maquina_id.tipo_calculo',
        'maquina_id.monto_mensual_bn',
        'maquina_id.monto_mensual_color',
        'maquina_id.monto_mensual_total',
        'maquina_id.volumen_mensual_bn',
        'maquina_id.volumen_mensual_color',
        'maquina_id.igv'
    )
    def _compute_totales(self):
        """
        Calcula renta fija + excedentes conservando todos los nombres técnicos.

        Los importes de renta fija configurados con IGV se convierten primero
        a valores sin IGV. Luego se suman los excedentes, se aplica el descuento
        y finalmente se calcula el IGV.
        """
        _logger.info("=== INICIO _compute_totales: renta fija + excedentes ===")

        for record in self:
            try:
                maquina = record.maquina_id

                if not maquina:
                    _logger.warning(
                        "Counter ID %s sin máquina. Totales asignados a cero.",
                        record.id,
                    )
                    record._set_zero_values()
                    continue

                tipo_calculo = maquina.tipo_calculo or 'auto'
                igv_rate = (maquina.igv or 18.0) / 100.0
                divisor_igv = 1.0 + igv_rate

                renta_fija_bn = 0.0
                renta_fija_color = 0.0
                monto_exceso_bn = 0.0
                monto_exceso_color = 0.0
                renta_bn = 0.0
                renta_color = 0.0

                _logger.info(
                    "Counter %s | serie=%s | tipo_maquina=%s | tipo_calculo=%s",
                    record.name or record.id,
                    record.serie,
                    maquina.tipo,
                    tipo_calculo,
                )

                # ======================================================
                # CÁLCULO AUTOMÁTICO
                # ======================================================
                if tipo_calculo == 'auto':
                    renta_bn = (
                        (record.copias_facturables_bn or 0)
                        * (record.precio_bn_sin_igv or 0.0)
                    )

                    if maquina.tipo == 'color':
                        renta_color = (
                            (record.copias_facturables_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )

                    _logger.info(
                        "AUTO | B/N: %s x %s = %s | Color: %s x %s = %s",
                        record.copias_facturables_bn,
                        record.precio_bn_sin_igv,
                        renta_bn,
                        record.copias_facturables_color,
                        record.precio_color_sin_igv,
                        renta_color,
                    )

                # ======================================================
                # RENTA FIJA SOLO B/N + EXCEDENTE B/N
                # Color continúa en automático si la máquina es color.
                # ======================================================
                elif tipo_calculo in {
                    'manual_sin_igv_bn',
                    'manual_con_igv_bn',
                }:
                    monto_configurado = maquina.monto_mensual_bn or 0.0

                    if tipo_calculo == 'manual_con_igv_bn':
                        renta_fija_bn = monto_configurado / divisor_igv
                    else:
                        renta_fija_bn = monto_configurado

                    monto_exceso_bn = (
                        (record.exceso_bn or 0)
                        * (record.precio_bn_sin_igv or 0.0)
                    )
                    renta_bn = renta_fija_bn + monto_exceso_bn

                    if maquina.tipo == 'color':
                        renta_color = (
                            (record.copias_facturables_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )

                    _logger.info(
                        "RENTA FIJA B/N | fija=%s | exceso=%s x %s=%s | "
                        "subtotal_bn=%s | color_auto=%s",
                        renta_fija_bn,
                        record.exceso_bn,
                        record.precio_bn_sin_igv,
                        monto_exceso_bn,
                        renta_bn,
                        renta_color,
                    )

                # ======================================================
                # RENTA FIJA SOLO COLOR + EXCEDENTE COLOR
                # B/N continúa en automático.
                # ======================================================
                elif tipo_calculo in {
                    'manual_sin_igv_color',
                    'manual_con_igv_color',
                }:
                    renta_bn = (
                        (record.copias_facturables_bn or 0)
                        * (record.precio_bn_sin_igv or 0.0)
                    )

                    monto_configurado = maquina.monto_mensual_color or 0.0

                    if tipo_calculo == 'manual_con_igv_color':
                        renta_fija_color = monto_configurado / divisor_igv
                    else:
                        renta_fija_color = monto_configurado

                    if maquina.tipo == 'color':
                        monto_exceso_color = (
                            (record.exceso_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )
                        renta_color = renta_fija_color + monto_exceso_color

                    _logger.info(
                        "RENTA FIJA COLOR | bn_auto=%s | fija=%s | "
                        "exceso=%s x %s=%s | subtotal_color=%s",
                        renta_bn,
                        renta_fija_color,
                        record.exceso_color,
                        record.precio_color_sin_igv,
                        monto_exceso_color,
                        renta_color,
                    )

                # ======================================================
                # RENTA FIJA TOTAL + EXCEDENTES B/N Y COLOR
                # ======================================================
                elif tipo_calculo in {
                    'manual_sin_igv_total',
                    'manual_con_igv_total',
                }:
                    monto_configurado = maquina.monto_mensual_total or 0.0

                    if tipo_calculo == 'manual_con_igv_total':
                        renta_fija_total = monto_configurado / divisor_igv
                    else:
                        renta_fija_total = monto_configurado

                    monto_exceso_bn = (
                        (record.exceso_bn or 0)
                        * (record.precio_bn_sin_igv or 0.0)
                    )

                    if maquina.tipo == 'color':
                        monto_exceso_color = (
                            (record.exceso_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )

                    # Distribuir únicamente la renta fija total.
                    # Los excedentes se mantienen en su modalidad real.
                    if maquina.tipo != 'color':
                        renta_fija_bn = renta_fija_total
                        renta_fija_color = 0.0
                    else:
                        base_bn = (
                            (maquina.volumen_mensual_bn or 0)
                            * (record.precio_bn_sin_igv or 0.0)
                        )
                        base_color = (
                            (maquina.volumen_mensual_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )
                        base_total = base_bn + base_color

                        if base_total > 0:
                            renta_fija_bn = renta_fija_total * (
                                base_bn / base_total
                            )
                            renta_fija_color = (
                                renta_fija_total - renta_fija_bn
                            )
                        else:
                            renta_fija_bn = renta_fija_total
                            renta_fija_color = 0.0

                    renta_bn = renta_fija_bn + monto_exceso_bn
                    renta_color = renta_fija_color + monto_exceso_color

                    _logger.info(
                        "RENTA FIJA TOTAL | total_fija=%s | fija_bn=%s | "
                        "fija_color=%s | exceso_bn=%s | exceso_color=%s",
                        renta_fija_total,
                        renta_fija_bn,
                        renta_fija_color,
                        monto_exceso_bn,
                        monto_exceso_color,
                    )

                else:
                    _logger.warning(
                        "Tipo de cálculo no reconocido: %s. Se usa automático.",
                        tipo_calculo,
                    )
                    renta_bn = (
                        (record.copias_facturables_bn or 0)
                        * (record.precio_bn_sin_igv or 0.0)
                    )
                    if maquina.tipo == 'color':
                        renta_color = (
                            (record.copias_facturables_color or 0)
                            * (record.precio_color_sin_igv or 0.0)
                        )

                # Guardar desglose antes del descuento.
                record.renta_fija_bn = round(renta_fija_bn, 2)
                record.monto_exceso_bn = round(monto_exceso_bn, 2)
                record.renta_fija_color = round(renta_fija_color, 2)
                record.monto_exceso_color = round(monto_exceso_color, 2)

                subtotal_antes_descuento = renta_bn + renta_color
                record.subtotal_antes_descuento = round(
                    subtotal_antes_descuento,
                    2,
                )

                descuento_porcentaje = record.descuento_porcentaje or 0.0
                descuento_valor = (
                    subtotal_antes_descuento
                    * descuento_porcentaje
                    / 100.0
                )
                record.monto_descuento = round(descuento_valor, 2)

                subtotal_con_descuento = (
                    subtotal_antes_descuento - descuento_valor
                )

                if subtotal_antes_descuento > 0:
                    factor_descuento = (
                        subtotal_con_descuento
                        / subtotal_antes_descuento
                    )
                else:
                    factor_descuento = 0.0

                subtotal_bn_final = renta_bn * factor_descuento
                subtotal_color_final = renta_color * factor_descuento

                igv_bn = subtotal_bn_final * igv_rate
                igv_color = subtotal_color_final * igv_rate

                total_bn = subtotal_bn_final + igv_bn
                total_color = subtotal_color_final + igv_color

                record.subtotal_bn = round(subtotal_bn_final, 2)
                record.subtotal_color = round(subtotal_color_final, 2)
                record.igv_bn = round(igv_bn, 2)
                record.igv_color = round(igv_color, 2)
                record.total_bn = round(total_bn, 2)
                record.total_color = round(total_color, 2)

                record.subtotal = round(subtotal_con_descuento, 2)
                record.igv = round(igv_bn + igv_color, 2)
                record.total = round(total_bn + total_color, 2)

                _logger.info(
                    "RESULTADO %s | fija_bn=%s | exceso_bn=%s | "
                    "fija_color=%s | exceso_color=%s | antes_desc=%s | "
                    "descuento=%s | subtotal=%s | igv=%s | total=%s",
                    record.name or record.id,
                    record.renta_fija_bn,
                    record.monto_exceso_bn,
                    record.renta_fija_color,
                    record.monto_exceso_color,
                    record.subtotal_antes_descuento,
                    record.monto_descuento,
                    record.subtotal,
                    record.igv,
                    record.total,
                )

            except Exception as error:
                _logger.exception(
                    "Error en _compute_totales para counter ID %s: %s",
                    record.id,
                    error,
                )
                record._set_zero_values()

        _logger.info("=== FIN _compute_totales: renta fija + excedentes ===")

    def _set_zero_values(self):
        """Helper para asignar valores cero en caso de error"""
        self.renta_fija_bn = 0.0
        self.monto_exceso_bn = 0.0
        self.renta_fija_color = 0.0
        self.monto_exceso_color = 0.0
        self.subtotal_antes_descuento = 0.0
        self.monto_descuento = 0.0
        self.subtotal_bn = 0.0
        self.subtotal_color = 0.0
        self.igv_bn = 0.0
        self.igv_color = 0.0
        self.total_bn = 0.0
        self.total_color = 0.0
        self.subtotal = 0.0
        self.igv = 0.0
        self.total = 0.0
    def action_open_add_copies_wizard(self):
        """Abre el wizard para sumar cantidad de copias al contador anterior"""
        self.ensure_one()

        if self.state != 'draft':
            raise UserError('Solo se puede usar este asistente en lecturas en borrador.')

        if not self.maquina_id:
            raise UserError('Primero seleccione una máquina.')

        return {
            'name': 'Sumar Copias al Contador',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.counter.add.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_counter_id': self.id,
            },
        }
    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancelled'})

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.cliente_id.name or ''} - {record.serie or ''} - {record.mes_facturacion or ''}"
            result.append((record.id, name))
        return result
    
    def action_print_report(self):
        """Método para la acción del servidor que genera el reporte"""
        return self.env.ref('copier_company.action_report_counter_readings').report_action(self)
   
    def action_generate_report(self):
        return self.env.ref('copier_company.action_report_counter_readings').report_action(self)


    @api.model
    def generate_monthly_readings(self):
        """
        Genera lecturas mensuales automáticamente.

        Ahora guarda cliente_id como snapshot para que las lecturas históricas
        no cambien si la máquina retorna y luego se asigna a otro cliente.
        """

        today = fields.Date.today()

        machines = self.env['copier.company'].search([
            ('estado_maquina_id.name', '=', 'Alquilada'),
            ('dia_facturacion', '!=', False)
        ])

        for machine in machines:
            try:
                # Calcular fecha de facturación segura
                ultimo_dia_mes = calendar.monthrange(today.year, today.month)[1]
                dia = min(machine.dia_facturacion, ultimo_dia_mes)
                fecha_facturacion = today.replace(day=dia)

                # Ajustar al mes siguiente si ya pasó
                if today > fecha_facturacion:
                    fecha_facturacion = fecha_facturacion + relativedelta(months=1)

                    ultimo_dia_mes_sig = calendar.monthrange(
                        fecha_facturacion.year,
                        fecha_facturacion.month
                    )[1]

                    dia = min(machine.dia_facturacion, ultimo_dia_mes_sig)
                    fecha_facturacion = fecha_facturacion.replace(day=dia)

                # Si cae domingo, mover al sábado
                if fecha_facturacion.weekday() == 6:
                    fecha_facturacion -= timedelta(days=1)

                crear_hoy = today == fecha_facturacion

                # Evitar duplicado por máquina y fecha de facturación
                existing_reading = self.env['copier.counter'].search([
                    ('maquina_id', '=', machine.id),
                    ('fecha_facturacion', '=', fecha_facturacion)
                ], limit=1)

                if existing_reading:
                    _logger.info(
                        "Ya existe lectura para la máquina %s en fecha %s",
                        machine.serie_id,
                        fecha_facturacion
                    )
                    continue

                if crear_hoy:
                    ultima_lectura = self.env['copier.counter'].search([
                        ('maquina_id', '=', machine.id),
                        ('state', 'in', ['confirmed', 'invoiced'])
                    ], limit=1, order='fecha desc, id desc')

                    contador_anterior_bn = ultima_lectura.contador_actual_bn if ultima_lectura else 0
                    contador_anterior_color = ultima_lectura.contador_actual_color if ultima_lectura else 0

                    vals = {
                        'maquina_id': machine.id,
                        'cliente_id': machine.cliente_id.id or False,
                        'fecha': today,
                        'fecha_facturacion': fecha_facturacion,
                        'fecha_emision_factura': False,
                        'contador_anterior_bn': contador_anterior_bn,
                        'contador_anterior_color': contador_anterior_color,
                        'contador_actual_bn': contador_anterior_bn,
                        'contador_actual_color': contador_anterior_color,
                        'state': 'draft',
                    }

                    with self.env.cr.savepoint():
                        self.env['copier.counter'].create(vals)

                    _logger.info(
                        "Creada nueva lectura para máquina %s, cliente %s, fecha de facturación %s",
                        machine.serie_id,
                        machine.cliente_id.display_name if machine.cliente_id else 'Sin cliente',
                        fecha_facturacion
                    )

            except Exception as e:
                _logger.exception(
                    "Error al procesar máquina %s: %s",
                    machine.serie_id,
                    str(e)
                )
                continue

        return True

    def _get_next_reading_date(self):
        """
        Calcula la próxima fecha de lectura/facturación para una máquina
        """
        self.ensure_one()
        today = fields.Date.today()
        
        if not self.maquina_id.dia_facturacion:
            return False
            
        # Calcular fecha de facturación
        dia = min(self.maquina_id.dia_facturacion, 
                 (today.replace(day=1) + relativedelta(months=1, days=-1)).day)
        fecha_facturacion = today.replace(day=dia)
        
        # Ajustar al mes siguiente si ya pasó la fecha
        if today > fecha_facturacion:
            if today.month == 12:
                fecha_facturacion = fecha_facturacion.replace(year=today.year + 1, month=1)
            else:
                fecha_facturacion = fecha_facturacion.replace(month=today.month + 1)
                
        # Si es domingo, mover al sábado
        if fecha_facturacion.weekday() == 6:
            fecha_facturacion -= timedelta(days=1)
            
        return fecha_facturacion

    informe_por_usuario = fields.Boolean('Informe detallado por usuarios', default=False)
    usuario_detalle_ids = fields.One2many(
        'copier.counter.user.detail',
        'contador_id',
        string='Detalle mensual por usuario'
    )

    def cargar_usuarios_asociados(self):
        self.ensure_one()
        if not self.maquina_id:
            raise UserError('Primero selecciona la máquina asociada.')

        self.usuario_detalle_ids.unlink()

        usuarios = self.env['copier.machine.user'].search([
            ('maquina_id', '=', self.maquina_id.id)
        ])

        detalles = []
        for usuario in usuarios:
            detalles.append((0, 0, {
                'usuario_id': usuario.id,
                'cantidad_bn': 0,
                'cantidad_color': 0,
            }))

        self.usuario_detalle_ids = detalles

    

    subtotal_bn = fields.Monetary(
        'Subtotal B/N',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    subtotal_color = fields.Monetary(
        'Subtotal Color',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    igv_bn = fields.Monetary(
        'IGV B/N',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    igv_color = fields.Monetary(
        'IGV Color',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    total_bn = fields.Monetary(
        'Total B/N',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    total_color = fields.Monetary(
        'Total Color',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    # Agregar después de los campos financieros existentes
    producto_facturable_bn_id = fields.Many2one(
    'product.product',
        related='maquina_id.producto_facturable_bn_id',
        string='Producto B/N',
        store=True,
        readonly=True
    )
    producto_facturable_color_id = fields.Many2one(
        'product.product',
        related='maquina_id.producto_facturable_color_id',
        string='Producto Color',
        store=True,
        readonly=True
    )

    # Mantener para compatibilidad (opcional)
    producto_facturable_id = fields.Many2one(
        'product.product',
        related='maquina_id.producto_facturable_id',
        string='Producto Principal',
        store=True,
        readonly=True
    )

    precio_producto = fields.Monetary(
        'Precio Producto',
        currency_field='currency_id',
        compute='_compute_precio_producto',
        store=True,
        help='Precio del producto configurado para facturación'
    )

    @api.depends('producto_facturable_id')
    def _compute_precio_producto(self):
        """Calcula el precio del producto desde la lista de precios"""
        for record in self:
            if record.producto_facturable_id:
                pricelist = record.cliente_id.property_product_pricelist or \
                        self.env['product.pricelist'].search([('currency_id', '=', record.currency_id.id)], limit=1)
                
                if pricelist:
                    precio = pricelist._get_product_price(
                        record.producto_facturable_id,
                        1.0,
                        partner=record.cliente_id,
                        date=record.fecha_facturacion
                    )
                    record.precio_producto = precio
                else:
                    record.precio_producto = record.producto_facturable_id.list_price
            else:
                record.precio_producto = 0.0


    def action_create_invoice(self):
        """
        Crea una factura basada en la lectura.

        Para rentas fijas genera líneas separadas:
        - renta fija;
        - copias excedentes.

        No cambia los nombres técnicos existentes ni los productos configurados.
        """
        self.ensure_one()

        if self.state != 'confirmed':
            raise UserError(
                'Solo se pueden facturar lecturas confirmadas.'
            )

        if not self.cliente_id:
            raise UserError(
                'No se encontró cliente asociado a la máquina.'
            )

        maquina = self.maquina_id
        tipo_calculo = maquina.tipo_calculo or 'auto'

        if maquina.tipo == 'monocroma':
            if not self.producto_facturable_bn_id:
                raise UserError(
                    f'Configure el Producto B/N en la máquina {self.serie}.'
                )
        else:
            if not self.producto_facturable_bn_id:
                raise UserError(
                    f'Configure el Producto B/N en la máquina {self.serie}.'
                )
            if not self.producto_facturable_color_id:
                raise UserError(
                    f'Configure el Producto Color en la máquina {self.serie}.'
                )

        modelo_maquina = (
            maquina.name.name if maquina.name else 'N/A'
        )
        info_maquina = (
            f'Modelo: {modelo_maquina} - Serie: {self.serie}'
        )

        if maquina.facturacion_automatica:
            fecha_para_factura = self.fecha_facturacion
        else:
            fecha_para_factura = (
                self.fecha_emision_factura or fields.Date.today()
            )

        invoice_vals = {
            'partner_id': self.cliente_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fecha_para_factura,
            'invoice_payment_term_id': (
                self.payment_term_id.id
                if self.payment_term_id
                else False
            ),
            'invoice_origin': self.name,
        }

        invoice = self.env['account.move'].create(invoice_vals)
        invoice_lines = []

        subtotal_antes_descuento = (
            self.subtotal_antes_descuento or 0.0
        )
        if subtotal_antes_descuento > 0:
            factor_descuento = (
                (self.subtotal or 0.0)
                / subtotal_antes_descuento
            )
        else:
            factor_descuento = 1.0

        def _income_account(product):
            return (
                product.property_account_income_id.id
                or product.categ_id.property_account_income_categ_id.id
            )

        def _tax_commands(product):
            taxes = product.taxes_id.filtered(
                lambda tax: not tax.company_id
                or tax.company_id == self.env.company
            )
            return [(6, 0, taxes.ids)]

        def _append_line(product, description, quantity, price_unit):
            if not product or quantity <= 0 or price_unit < 0:
                return

            invoice_lines.append((0, 0, {
                'move_id': invoice.id,
                'product_id': product.id,
                'name': description,
                'quantity': quantity,
                'price_unit': price_unit,
                'account_id': _income_account(product),
                'tax_ids': _tax_commands(product),
            }))

        tipos_renta_bn = {
            'manual_sin_igv_bn',
            'manual_con_igv_bn',
            'manual_sin_igv_total',
            'manual_con_igv_total',
        }
        tipos_renta_color = {
            'manual_sin_igv_color',
            'manual_con_igv_color',
            'manual_sin_igv_total',
            'manual_con_igv_total',
        }

        # ==========================================================
        # BLANCO Y NEGRO
        # ==========================================================
        if tipo_calculo in tipos_renta_bn:
            renta_bn_factura = (
                (self.renta_fija_bn or 0.0)
                * factor_descuento
            )
            exceso_bn_unitario = (
                (self.precio_bn_sin_igv or 0.0)
                * factor_descuento
            )

            _append_line(
                self.producto_facturable_bn_id,
                (
                    f'{self.producto_facturable_bn_id.name} - '
                    f'Renta fija B/N - {self.mes_facturacion}\n'
                    f'Incluye hasta '
                    f'{int(maquina.volumen_mensual_bn or 0)} copias\n'
                    f'{info_maquina}'
                ),
                1,
                renta_bn_factura,
            )

            if self.exceso_bn > 0:
                _append_line(
                    self.producto_facturable_bn_id,
                    (
                        f'{self.producto_facturable_bn_id.name} - '
                        f'Excedente B/N - {self.mes_facturacion}\n'
                        f'{int(self.exceso_bn)} copias excedentes x '
                        f'{self.precio_bn_sin_igv:.6f} sin IGV\n'
                        f'{info_maquina}'
                    ),
                    self.exceso_bn,
                    exceso_bn_unitario,
                )
        else:
            _append_line(
                self.producto_facturable_bn_id,
                (
                    f'{self.producto_facturable_bn_id.name} - '
                    f'Copias B/N: '
                    f'{int(self.copias_facturables_bn)} - '
                    f'{self.mes_facturacion}\n{info_maquina}'
                ),
                1,
                self.subtotal_bn,
            )

        # ==========================================================
        # COLOR
        # ==========================================================
        if maquina.tipo == 'color':
            if tipo_calculo in tipos_renta_color:
                renta_color_factura = (
                    (self.renta_fija_color or 0.0)
                    * factor_descuento
                )
                exceso_color_unitario = (
                    (self.precio_color_sin_igv or 0.0)
                    * factor_descuento
                )

                _append_line(
                    self.producto_facturable_color_id,
                    (
                        f'{self.producto_facturable_color_id.name} - '
                        f'Renta fija Color - {self.mes_facturacion}\n'
                        f'Incluye hasta '
                        f'{int(maquina.volumen_mensual_color or 0)} copias\n'
                        f'{info_maquina}'
                    ),
                    1,
                    renta_color_factura,
                )

                if self.exceso_color > 0:
                    _append_line(
                        self.producto_facturable_color_id,
                        (
                            f'{self.producto_facturable_color_id.name} - '
                            f'Excedente Color - {self.mes_facturacion}\n'
                            f'{int(self.exceso_color)} copias excedentes x '
                            f'{self.precio_color_sin_igv:.6f} sin IGV\n'
                            f'{info_maquina}'
                        ),
                        self.exceso_color,
                        exceso_color_unitario,
                    )
            else:
                _append_line(
                    self.producto_facturable_color_id,
                    (
                        f'{self.producto_facturable_color_id.name} - '
                        f'Copias Color: '
                        f'{int(self.copias_facturables_color)} - '
                        f'{self.mes_facturacion}\n{info_maquina}'
                    ),
                    1,
                    self.subtotal_color,
                )

        if not invoice_lines:
            invoice.unlink()
            raise UserError(
                'No se pudieron crear líneas de factura. '
                'Revise la renta fija, los excedentes y los productos.'
            )

        invoice.write({'invoice_line_ids': invoice_lines})
        self.write({'state': 'invoiced'})

        _logger.info(
            "Factura %s creada desde counter %s | cliente=%s | "
            "tipo_calculo=%s | líneas=%s | subtotal=%s | igv=%s | total=%s",
            invoice.name,
            self.name,
            self.cliente_id.display_name,
            tipo_calculo,
            len(invoice_lines),
            self.subtotal,
            self.igv,
            self.total,
        )

        self.message_post(
            body=(
                f'Factura creada: {invoice.name}<br/>'
                f'Renta fija B/N: S/ {self.renta_fija_bn:.2f}<br/>'
                f'Excedente B/N: {self.exceso_bn} copias = '
                f'S/ {self.monto_exceso_bn:.2f}<br/>'
                f'Renta fija Color: S/ {self.renta_fija_color:.2f}<br/>'
                f'Excedente Color: {self.exceso_color} copias = '
                f'S/ {self.monto_exceso_color:.2f}<br/>'
                f'Subtotal: S/ {self.subtotal:.2f}<br/>'
                f'IGV: S/ {self.igv:.2f}<br/>'
                f'Total: S/ {self.total:.2f}<br/>'
                f'Fecha factura: {fecha_para_factura}'
            ),
            message_type='notification',
        )

        return {
            'name': 'Factura Creada',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_multiple_invoices(self):
        """Crea una factura consolidada por cliente para múltiples lecturas seleccionadas"""
        
        # Validar que hay registros seleccionados
        if not self:
            raise UserError('No se han seleccionado registros para facturar.')
        
        # Validar estado de los registros
        registros_invalidos = self.filtered(lambda r: r.state != 'confirmed')
        if registros_invalidos:
            raise UserError(
                f'Algunos registros no están confirmados:\n' +
                '\n'.join([f"- {r.name} ({r.state})" for r in registros_invalidos])
            )
        
        # Agrupar por cliente
        lecturas_por_cliente = {}
        for record in self:
            cliente_id = record.cliente_id.id
            if cliente_id not in lecturas_por_cliente:
                lecturas_por_cliente[cliente_id] = self.env['copier.counter']
            lecturas_por_cliente[cliente_id] |= record
        
        facturas_creadas = []
        errores = []
        
        # Crear una factura por cada cliente
        for cliente_id, lecturas in lecturas_por_cliente.items():
            try:
                factura = self._crear_factura_consolidada(lecturas)
                if factura:
                    facturas_creadas.append({
                        'factura': factura,
                        'lecturas': lecturas,
                        'cliente': lecturas[0].cliente_id.name
                    })
            except Exception as e:
                cliente_name = lecturas[0].cliente_id.name
                errores.append(f"{cliente_name}: {str(e)}")
                _logger.exception(f"Error creando factura para cliente {cliente_name}")
        
        # Preparar mensaje de resultado
        if facturas_creadas:
            mensaje_detalle = '\n'.join([
                f"✓ {item['cliente']}: {item['factura'].name} ({len(item['lecturas'])} equipos)"
                for item in facturas_creadas
            ])
            mensaje = f"Facturas creadas: {len(facturas_creadas)}\n\n{mensaje_detalle}"
            tipo = 'success'
        else:
            mensaje = "No se crearon facturas"
            tipo = 'warning'
        
        if errores:
            mensaje += f"\n\n❌ Errores: {len(errores)}\n" + '\n'.join(errores)
            tipo = 'warning'
        
        # Mostrar notificación
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Facturación Masiva Completada',
                'message': mensaje,
                'type': tipo,
                'sticky': True,
            }
        }
        
        # Si solo hay una factura, abrir directamente
        if len(facturas_creadas) == 1:
            return {
                'name': 'Factura Creada',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': facturas_creadas[0]['factura'].id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Si hay múltiples, mostrar lista de facturas creadas
        if facturas_creadas:
            factura_ids = [item['factura'].id for item in facturas_creadas]
            return {
                'name': 'Facturas Creadas',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', factura_ids)],
                'target': 'current',
            }
        
        return notification


    def _crear_factura_consolidada(self, lecturas):
        """Crea una factura consolidada para múltiples lecturas del mismo cliente"""
        
        if not lecturas:
            return False
        
        # Usar la primera lectura como referencia
        primera_lectura = lecturas[0]
        cliente = primera_lectura.cliente_id
        
        # Validar que todas sean del mismo cliente
        if any(l.cliente_id.id != cliente.id for l in lecturas):
            raise UserError('Todas las lecturas deben ser del mismo cliente.')
        
        # Validar productos configurados
        for lectura in lecturas:
            productos_faltantes = []
            
            if lectura.maquina_id.tipo == 'monocroma':
                if not lectura.producto_facturable_bn_id and lectura.copias_facturables_bn > 0:
                    productos_faltantes.append(f"Producto B/N para {lectura.serie}")
            else:  # color
                if not lectura.producto_facturable_bn_id and lectura.copias_facturables_bn > 0:
                    productos_faltantes.append(f"Producto B/N para {lectura.serie}")
                if not lectura.producto_facturable_color_id and lectura.copias_facturables_color > 0:
                    productos_faltantes.append(f"Producto Color para {lectura.serie}")
            
            if productos_faltantes:
                raise UserError(
                    f"Faltan productos en la máquina {lectura.serie}:\n" +
                    "\n".join([f"- {p}" for p in productos_faltantes])
                )
        
        # Determinar fecha de factura (usar la más reciente de fecha_emision_factura o hoy)
        fechas_emision = [l.fecha_emision_factura for l in lecturas if l.fecha_emision_factura]
        if fechas_emision:
            fecha_para_factura = max(fechas_emision)
        else:
            fecha_para_factura = fields.Date.today()
        
        # Obtener término de pago (usar el de la primera lectura)
        payment_term = primera_lectura.payment_term_id
        
        # Crear factura
        invoice_vals = {
            'partner_id': cliente.id,
            'move_type': 'out_invoice',
            'invoice_date': fecha_para_factura,
            'invoice_payment_term_id': payment_term.id if payment_term else False,
            'invoice_origin': ', '.join(lecturas.mapped('name')),
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Crear líneas de factura para cada lectura
        invoice_lines = []
        total_copias_bn = 0
        total_copias_color = 0
        total_equipos = 0
        
        for lectura in lecturas.sorted(key=lambda l: l.serie):
            modelo_maquina = lectura.maquina_id.name.name if lectura.maquina_id.name else 'N/A'
            info_maquina = f"Modelo: {modelo_maquina} - Serie: {lectura.serie}"
            
            # Línea B/N
            if lectura.copias_facturables_bn > 0 and lectura.producto_facturable_bn_id:
                descripcion_bn = (
                    f'{lectura.producto_facturable_bn_id.name} - '
                    f'Copias B/N: {int(lectura.copias_facturables_bn)} - '
                    f'{lectura.mes_facturacion}\n{info_maquina}'
                )
                
                line_vals_bn = {
                    'move_id': invoice.id,
                    'product_id': lectura.producto_facturable_bn_id.id,
                    'name': descripcion_bn,
                    'quantity': 1,
                    'price_unit': lectura.subtotal_bn,
                    'account_id': (
                        lectura.producto_facturable_bn_id.property_account_income_id.id or 
                        lectura.producto_facturable_bn_id.categ_id.property_account_income_categ_id.id
                    ),
                }
                invoice_lines.append((0, 0, line_vals_bn))
                total_copias_bn += lectura.copias_facturables_bn
                total_equipos += 1
            
            # Línea Color
            if lectura.copias_facturables_color > 0 and lectura.producto_facturable_color_id:
                descripcion_color = (
                    f'{lectura.producto_facturable_color_id.name} - '
                    f'Copias Color: {int(lectura.copias_facturables_color)} - '
                    f'{lectura.mes_facturacion}\n{info_maquina}'
                )
                
                line_vals_color = {
                    'move_id': invoice.id,
                    'product_id': lectura.producto_facturable_color_id.id,
                    'name': descripcion_color,
                    'quantity': 1,
                    'price_unit': lectura.subtotal_color,
                    'account_id': (
                        lectura.producto_facturable_color_id.property_account_income_id.id or 
                        lectura.producto_facturable_color_id.categ_id.property_account_income_categ_id.id
                    ),
                }
                invoice_lines.append((0, 0, line_vals_color))
                total_copias_color += lectura.copias_facturables_color
        
        if not invoice_lines:
            invoice.unlink()
            raise UserError('No se pudieron crear líneas de factura para ninguna lectura.')
        
        # Asignar líneas a la factura
        invoice.write({'invoice_line_ids': invoice_lines})
        
        # Marcar lecturas como facturadas
        lecturas.write({'state': 'invoiced'})
        
        # Agregar nota en el chatter de cada lectura
        for lectura in lecturas:
            lectura.message_post(
                body=f'Incluido en factura consolidada: {invoice.name}\n'
                    f'- B/N: {lectura.copias_facturables_bn} copias = S/ {lectura.total_bn:.2f}\n'
                    f'- Color: {lectura.copias_facturables_color} copias = S/ {lectura.total_color:.2f}\n'
                    f'- Subtotal equipo: S/ {lectura.total:.2f}',
                message_type='notification'
            )
        
        # Nota en la factura
        resumen = f'''
    Factura consolidada con {total_equipos} equipos:
    - Total copias B/N: {int(total_copias_bn)}
    - Total copias Color: {int(total_copias_color)}

    Equipos incluidos:
    {chr(10).join([f'• {l.serie} ({l.mes_facturacion})' for l in lecturas])}
    '''
        
        invoice.message_post(
            body=resumen,
            message_type='notification'
        )
        
        _logger.info(f"Factura consolidada {invoice.name} creada para cliente {cliente.name} con {len(lecturas)} lecturas")
        
        return invoice

        

class ReportCounterReadings(models.AbstractModel):
    _name = 'report.copier_company.report_counter_readings'
    _description = 'Reporte de Lecturas'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['copier.counter'].browse(docids)

        # Validar que todos los registros pertenezcan al mismo cliente
        clientes = docs.mapped('cliente_id')
        if len(clientes) > 1:
            raise UserError("Debe seleccionar registros de un solo cliente para generar el reporte.")

        # Agrupar por tipo de máquina
        maquinas_mono = docs.filtered(lambda x: x.maquina_id.tipo == 'monocroma')
        maquinas_color = docs.filtered(lambda x: x.maquina_id.tipo == 'color')

        # Calcular el total general
        total_general = sum(docs.mapped('total'))

        return {
            'docs': docs,
            'company': self.env.company,
            'cliente': clientes[0] if clientes else None,  # Cliente único
            'maquinas_mono': maquinas_mono,
            'maquinas_color': maquinas_color,
            'total_general': total_general,
        }

class CopierMachineUser(models.Model):
    _name = 'copier.machine.user'
    _description = 'Usuarios Internos por Máquina'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre Empresa/Usuario', required=True)
    clave = fields.Char('Clave')
    correo = fields.Char('Correo Electrónico')

    maquina_id = fields.Many2one(
        'copier.company',
        string='Máquina Asociada',
        required=True,
        tracking=True
    )

    # 🔹 CAMPOS RELACIONADOS (SOLO LECTURA)

    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        store=True,
        tracking=True,
        readonly=True,
        index=True,
        copy=False,
        help="Cliente congelado al momento de crear el servicio. No cambia si la máquina cambia de cliente."
    )

    serie_maquina = fields.Char(
        string='Serie',
        related='maquina_id.serie_id',
        store=True,
        readonly=True
    )

    modelo_maquina = fields.Many2one(
        'modelos.maquinas',
        string='Modelo',
        related='maquina_id.name',
        store=True,
        readonly=True
    )

    ubicacion = fields.Char(
        string='Ubicación',
        store=True,
        readonly=True,
        copy=False,
        help="Ubicación congelada al momento de crear el servicio."
    )


class CopierCounterUserDetail(models.Model):
    _name = 'copier.counter.user.detail'
    _description = 'Detalle mensual de copias por usuario'

    contador_id = fields.Many2one(
        'copier.counter',
        string='Contador General',
        required=True,
        ondelete='cascade'
    )
    tipo_maquina = fields.Selection(
        related='contador_id.maquina_id.tipo',
        string='Tipo Máquina',
        store=True,
        readonly=True
    )

    usuario_id = fields.Many2one(
        'copier.machine.user',
        string='Empresa/Usuario',
        required=True
    )

    # NUEVOS CAMPOS
    cantidad_bn = fields.Integer(
        'Copias B/N',
        default=0,
        help="Total de copias en blanco y negro"
    )

    cantidad_color = fields.Integer(
        'Copias Color',
        default=0,
        help="Total de copias a color"
    )

    # Campo total (opcional pero recomendable)
    total_copias = fields.Integer(
        'Total Copias',
        compute='_compute_total_copias',
        store=True
    )

    @api.depends('cantidad_bn', 'cantidad_color')
    def _compute_total_copias(self):
        for record in self:
            record.total_copias = (record.cantidad_bn or 0) + (record.cantidad_color or 0)

