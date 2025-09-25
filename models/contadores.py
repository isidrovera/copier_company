from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import calendar
import logging

_logger = logging.getLogger(__name__)

# Constantes para mejorar mantenibilidad
IGV_RATE_DEFAULT = 18.0
IGV_MULTIPLIER = 1.18
SEQUENCE_CODE = 'copier.counter'


class CopierCounter(models.Model):
    _name = 'copier.counter'
    _description = 'Control de Contadores de Máquinas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_facturacion desc, maquina_id'

    # ==========================================
    # CAMPOS BÁSICOS
    # ==========================================
    
    name = fields.Char(
        string='Referencia',
        default='New',
        copy=False,
        readonly=True,
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('invoiced', 'Facturado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    # ==========================================
    # CAMPOS DE RELACIÓN Y FECHAS
    # ==========================================
    
    maquina_id = fields.Many2one(
        'copier.company',
        string='Máquina',
        required=True,
        tracking=True,
        domain=[('estado_maquina_id.name', '=', 'Alquilada')]
    )
    
    cliente_id = fields.Many2one(
        'res.partner',
        related='maquina_id.cliente_id',
        string='Cliente',
        store=True,
        readonly=True
    )
    
    serie = fields.Char(
        related='maquina_id.serie_id',
        string='Serie',
        store=True,
        readonly=True
    )
    
    payment_term_id = fields.Many2one(
        'account.payment.term',
        related='maquina_id.payment_term_id',
        string='Términos de pago',
        readonly=True,
        help='Términos de pago para esta transacción'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='maquina_id.currency_id',
        string='Moneda',
        readonly=True
    )

    fecha = fields.Date(
        string='Fecha de Lectura',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
    fecha_facturacion = fields.Date(
        string='Fecha de Facturación',
        required=True,
        tracking=True
    )
    
    fecha_emision_factura = fields.Date(
        string='Fecha de Emisión',
        help="Fecha que aparecerá en la factura. Si está vacío, usa la fecha de hoy"
    )
    
    mes_facturacion = fields.Char(
        string='Mes de Facturación',
        compute='_compute_mes_facturacion',
        store=True
    )

    # ==========================================
    # CONTADORES B/N
    # ==========================================
    
    contador_anterior_bn = fields.Integer(
        string='Contador Anterior B/N',
        required=True,
        copy=False,
        tracking=True,
        help="Contador B/N de la lectura anterior"
    )
    
    contador_actual_bn = fields.Integer(
        string='Contador Actual B/N',
        required=True,
        tracking=True,
        help="Lectura actual del contador B/N"
    )
    
    total_copias_bn = fields.Integer(
        string='Total Copias B/N',
        compute='_compute_copias_totales',
        store=True,
        help="Diferencia entre contador actual y anterior B/N"
    )
    
    exceso_bn = fields.Integer(
        string='Exceso B/N',
        compute='_compute_excesos',
        store=True,
        help="Copias que exceden el volumen mensual contratado B/N"
    )
    
    copias_facturables_bn = fields.Integer(
        string='Copias Facturables B/N',
        compute='_compute_facturables',
        store=True,
        help="Total de copias B/N a facturar (mínimo mensual o real)"
    )

    # ==========================================
    # CONTADORES COLOR
    # ==========================================
    
    contador_anterior_color = fields.Integer(
        string='Contador Anterior Color',
        required=True,
        copy=False,
        tracking=True,
        help="Contador Color de la lectura anterior"
    )
    
    contador_actual_color = fields.Integer(
        string='Contador Actual Color',
        tracking=True,
        help="Lectura actual del contador Color"
    )
    
    total_copias_color = fields.Integer(
        string='Total Copias Color',
        compute='_compute_copias_totales',
        store=True,
        help="Diferencia entre contador actual y anterior Color"
    )
    
    exceso_color = fields.Integer(
        string='Exceso Color',
        compute='_compute_excesos',
        store=True,
        help="Copias Color que exceden el volumen mensual contratado"
    )
    
    copias_facturables_color = fields.Integer(
        string='Copias Facturables Color',
        compute='_compute_facturables',
        store=True,
        help="Total de copias Color a facturar (mínimo mensual o real)"
    )

    # ==========================================
    # PRECIOS Y DESCUENTOS
    # ==========================================
    
    precio_bn_sin_igv = fields.Float(
        string='Precio B/N sin IGV',
        compute='_compute_precios_sin_igv',
        store=True,
        digits='Product Price',
        help="Precio unitario B/N sin IGV aplicado"
    )
    
    precio_color_sin_igv = fields.Float(
        string='Precio Color sin IGV',
        compute='_compute_precios_sin_igv',
        store=True,
        digits='Product Price',
        help="Precio unitario Color sin IGV aplicado"
    )
    
    descuento_porcentaje = fields.Float(
        string='Descuento (%)',
        compute='_compute_descuento_desde_maquina',
        store=True,
        help="Porcentaje de descuento aplicado"
    )

    # ==========================================
    # CAMPOS FINANCIEROS PRINCIPALES
    # ==========================================
    
    subtotal_antes_descuento = fields.Monetary(
        string='Subtotal Antes Descuento',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id',
        help="Subtotal antes de aplicar descuento"
    )
    
    monto_descuento = fields.Monetary(
        string='Monto Descuento',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id',
        help="Monto del descuento aplicado"
    )
    
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id',
        help="Subtotal después del descuento, antes del IGV"
    )
    
    igv = fields.Monetary(
        string='IGV (18%)',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id',
        help="Monto del IGV aplicado"
    )
    
    total = fields.Monetary(
        string='Total',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id',
        help="Monto total a facturar"
    )

    # ==========================================
    # CAMPOS FINANCIEROS DETALLADOS
    # ==========================================
    
    subtotal_bn = fields.Monetary(
        string='Subtotal B/N',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )
    
    subtotal_color = fields.Monetary(
        string='Subtotal Color',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )
    
    igv_bn = fields.Monetary(
        string='IGV B/N',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )
    
    igv_color = fields.Monetary(
        string='IGV Color',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )
    
    total_bn = fields.Monetary(
        string='Total B/N',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )
    
    total_color = fields.Monetary(
        string='Total Color',
        compute='_compute_totales_financieros',
        store=True,
        currency_field='currency_id'
    )

    # ==========================================
    # PRODUCTOS PARA FACTURACIÓN
    # ==========================================
    
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
    
    # Compatibilidad con versión anterior
    producto_facturable_id = fields.Many2one(
        'product.product',
        related='maquina_id.producto_facturable_id',
        string='Producto Principal',
        store=True,
        readonly=True
    )
    
    precio_producto = fields.Monetary(
        string='Precio Producto',
        currency_field='currency_id',
        compute='_compute_precio_producto',
        store=True,
        help='Precio del producto configurado para facturación'
    )

    # ==========================================
    # CAMPOS PARA INFORMES POR USUARIO
    # ==========================================
    
    informe_por_usuario = fields.Boolean(
        string='Informe detallado por usuarios',
        default=False
    )
    
    usuario_detalle_ids = fields.One2many(
        'copier.counter.user.detail',
        'contador_id',
        string='Detalle mensual por usuario'
    )

    # ==========================================
    # MÉTODOS COMPUTE - FECHAS
    # ==========================================

    @api.depends('fecha_facturacion', 'fecha_emision_factura')
    def _compute_mes_facturacion(self):
        """Calcula el mes de facturación en formato legible"""
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        for record in self:
            fecha_ref = record.fecha_emision_factura or record.fecha_facturacion
            if fecha_ref:
                record.mes_facturacion = f"{meses[fecha_ref.month]} {fecha_ref.year}"
            else:
                record.mes_facturacion = False

    # ==========================================
    # MÉTODOS COMPUTE - CONTADORES
    # ==========================================

    @api.depends('contador_actual_bn', 'contador_anterior_bn',
                 'contador_actual_color', 'contador_anterior_color')
    def _compute_copias_totales(self):
        """Calcula el total de copias por tipo"""
        for record in self:
            record.total_copias_bn = max(0, (record.contador_actual_bn or 0) - (record.contador_anterior_bn or 0))
            record.total_copias_color = max(0, (record.contador_actual_color or 0) - (record.contador_anterior_color or 0))

    @api.depends('total_copias_bn', 'total_copias_color',
                 'maquina_id.volumen_mensual_bn', 'maquina_id.volumen_mensual_color')
    def _compute_excesos(self):
        """Calcula los excesos sobre el volumen mensual contratado"""
        for record in self:
            volumen_bn = record.maquina_id.volumen_mensual_bn or 0
            volumen_color = record.maquina_id.volumen_mensual_color or 0
            
            record.exceso_bn = max(0, record.total_copias_bn - volumen_bn)
            record.exceso_color = max(0, record.total_copias_color - volumen_color)

    @api.depends('total_copias_bn', 'total_copias_color',
                 'maquina_id.volumen_mensual_bn', 'maquina_id.volumen_mensual_color')
    def _compute_facturables(self):
        """Calcula las copias facturables (mínimo mensual garantizado)"""
        for record in self:
            volumen_bn = record.maquina_id.volumen_mensual_bn or 0
            volumen_color = record.maquina_id.volumen_mensual_color or 0
            
            # Siempre se factura al menos el volumen mensual contratado
            record.copias_facturables_bn = max(record.total_copias_bn, volumen_bn)
            record.copias_facturables_color = max(record.total_copias_color, volumen_color)

    # ==========================================
    # MÉTODOS COMPUTE - PRECIOS
    # ==========================================

    @api.depends('maquina_id.costo_copia_bn', 'maquina_id.costo_copia_color',
                 'maquina_id.precio_bn_incluye_igv', 'maquina_id.precio_color_incluye_igv')
    def _compute_precios_sin_igv(self):
        """Calcula los precios sin IGV manteniendo precisión"""
        for record in self:
            if not record.maquina_id:
                record.precio_bn_sin_igv = 0.0
                record.precio_color_sin_igv = 0.0
                continue
            
            precio_bn = record.maquina_id.costo_copia_bn or 0.0
            precio_color = record.maquina_id.costo_copia_color or 0.0
            
            # Convertir a precio sin IGV si incluye IGV
            if record.maquina_id.precio_bn_incluye_igv:
                record.precio_bn_sin_igv = precio_bn / IGV_MULTIPLIER
            else:
                record.precio_bn_sin_igv = precio_bn
                
            if record.maquina_id.precio_color_incluye_igv:
                record.precio_color_sin_igv = precio_color / IGV_MULTIPLIER
            else:
                record.precio_color_sin_igv = precio_color

    @api.depends('maquina_id.descuento')
    def _compute_descuento_desde_maquina(self):
        """Obtiene el descuento configurado en la máquina"""
        for record in self:
            if record.maquina_id:
                record.descuento_porcentaje = record.maquina_id.descuento or 0.0
            else:
                record.descuento_porcentaje = 0.0

    @api.depends('producto_facturable_id', 'cliente_id', 'fecha_facturacion', 'currency_id')
    def _compute_precio_producto(self):
        """Calcula el precio del producto desde la lista de precios"""
        for record in self:
            if not record.producto_facturable_id:
                record.precio_producto = 0.0
                continue
            
            # Buscar lista de precios del cliente
            pricelist = record.cliente_id.property_product_pricelist
            if not pricelist:
                # Buscar lista de precios por defecto para la moneda
                pricelist = self.env['product.pricelist'].search([
                    ('currency_id', '=', record.currency_id.id)
                ], limit=1)
            
            if pricelist:
                precio = pricelist._get_product_price(
                    record.producto_facturable_id,
                    1.0,
                    partner=record.cliente_id,
                    date=record.fecha_facturacion or fields.Date.today()
                )
                record.precio_producto = precio
            else:
                record.precio_producto = record.producto_facturable_id.list_price

    # ==========================================
    # MÉTODOS COMPUTE - TOTALES FINANCIEROS
    # ==========================================

    @api.depends('copias_facturables_bn', 'copias_facturables_color',
                 'precio_bn_sin_igv', 'precio_color_sin_igv', 'descuento_porcentaje',
                 'maquina_id.tipo_calculo', 'maquina_id.monto_mensual_bn',
                 'maquina_id.monto_mensual_color', 'maquina_id.monto_mensual_total',
                 'maquina_id.igv')
    def _compute_totales_financieros(self):
        """Calcula todos los totales financieros usando la misma lógica que copier.company"""
        _logger.debug("=== Iniciando cálculo de totales financieros ===")
        
        for record in self:
            try:
                if not record.maquina_id:
                    record._reset_financial_values()
                    continue
                
                # 1. Calcular rentas base según tipo de cálculo
                renta_bn, renta_color = record._calcular_rentas_base()
                
                # 2. Aplicar descuento
                subtotal_antes = renta_bn + renta_color
                descuento_monto = subtotal_antes * (record.descuento_porcentaje / 100.0)
                subtotal_con_descuento = subtotal_antes - descuento_monto
                
                # 3. Distribuir descuento proporcionalmente
                if subtotal_antes > 0:
                    factor_descuento = subtotal_con_descuento / subtotal_antes
                    subtotal_bn_final = renta_bn * factor_descuento
                    subtotal_color_final = renta_color * factor_descuento
                else:
                    subtotal_bn_final = subtotal_color_final = 0.0
                
                # 4. Calcular IGV
                igv_rate = (record.maquina_id.igv or IGV_RATE_DEFAULT) / 100.0
                igv_bn = subtotal_bn_final * igv_rate
                igv_color = subtotal_color_final * igv_rate
                
                # 5. Calcular totales finales
                total_bn = subtotal_bn_final + igv_bn
                total_color = subtotal_color_final + igv_color
                
                # 6. Asignar valores con redondeo apropiado
                record.subtotal_antes_descuento = self._round_currency(subtotal_antes)
                record.monto_descuento = self._round_currency(descuento_monto)
                record.subtotal_bn = self._round_currency(subtotal_bn_final)
                record.subtotal_color = self._round_currency(subtotal_color_final)
                record.igv_bn = self._round_currency(igv_bn)
                record.igv_color = self._round_currency(igv_color)
                record.total_bn = self._round_currency(total_bn)
                record.total_color = self._round_currency(total_color)
                record.subtotal = self._round_currency(subtotal_con_descuento)
                record.igv = self._round_currency(igv_bn + igv_color)
                record.total = self._round_currency(total_bn + total_color)
                
                _logger.debug(f"Counter {record.id}: Total calculado = {record.total}")
                
            except Exception as e:
                _logger.error(f"Error calculando totales para counter {record.id}: {str(e)}")
                record._reset_financial_values()

    def _calcular_rentas_base(self):
        """Calcula las rentas base según el tipo de cálculo configurado en la máquina"""
        self.ensure_one()
        
        tipo_calculo = self.maquina_id.tipo_calculo or 'auto'
        _logger.debug(f"Tipo de cálculo: {tipo_calculo}")
        
        if tipo_calculo == 'auto':
            return self._calcular_renta_automatica()
        elif tipo_calculo.startswith('manual_'):
            return self._calcular_renta_manual(tipo_calculo)
        else:
            _logger.warning(f"Tipo de cálculo no reconocido: {tipo_calculo}")
            return self._calcular_renta_automatica()

    def _calcular_renta_automatica(self):
        """Cálculo automático basado en volumen y precio unitario"""
        renta_bn = self.copias_facturables_bn * self.precio_bn_sin_igv
        renta_color = self.copias_facturables_color * self.precio_color_sin_igv
        
        _logger.debug(f"Renta automática - B/N: {renta_bn}, Color: {renta_color}")
        return renta_bn, renta_color

    def _calcular_renta_manual(self, tipo_calculo):
        """Cálculo manual según configuración específica"""
        igv_rate = (self.maquina_id.igv or IGV_RATE_DEFAULT) / 100.0
        
        # Inicializar con cálculo automático
        renta_bn = self.copias_facturables_bn * self.precio_bn_sin_igv
        renta_color = self.copias_facturables_color * self.precio_color_sin_igv
        
        if 'bn' in tipo_calculo:
            # Cálculo manual para B/N
            monto_bn = self.maquina_id.monto_mensual_bn or 0
            if 'con_igv' in tipo_calculo:
                renta_bn = monto_bn / (1 + igv_rate)
            else:
                renta_bn = monto_bn
                
        elif 'color' in tipo_calculo:
            # Cálculo manual para Color
            monto_color = self.maquina_id.monto_mensual_color or 0
            if 'con_igv' in tipo_calculo:
                renta_color = monto_color / (1 + igv_rate)
            else:
                renta_color = monto_color
                
        elif 'total' in tipo_calculo:
            # Cálculo manual para total
            return self._calcular_renta_manual_total(tipo_calculo, igv_rate)
        
        _logger.debug(f"Renta manual {tipo_calculo} - B/N: {renta_bn}, Color: {renta_color}")
        return renta_bn, renta_color

    def _calcular_renta_manual_total(self, tipo_calculo, igv_rate):
        """Cálculo manual total con distribución proporcional"""
        monto_total = self.maquina_id.monto_mensual_total or 0
        
        # Convertir a sin IGV si es necesario
        if 'con_igv' in tipo_calculo:
            monto_total_sin_igv = monto_total / (1 + igv_rate)
        else:
            monto_total_sin_igv = monto_total
        
        # Distribuir proporcionalmente basado en costos unitarios
        costo_bn_base = self.copias_facturables_bn * self.precio_bn_sin_igv
        costo_color_base = self.copias_facturables_color * self.precio_color_sin_igv
        costo_total_base = costo_bn_base + costo_color_base
        
        if costo_total_base > 0:
            factor = monto_total_sin_igv / costo_total_base
            renta_bn = costo_bn_base * factor
            renta_color = costo_color_base * factor
        else:
            # Si no hay base de costos, asignar todo a B/N
            renta_bn = monto_total_sin_igv
            renta_color = 0
        
        _logger.debug(f"Renta manual total - B/N: {renta_bn}, Color: {renta_color}")
        return renta_bn, renta_color

    def _round_currency(self, amount):
        """Redondea montos según la precisión de la moneda"""
        if not self.currency_id:
            return round(amount, 2)
        return self.currency_id.round(amount)

    def _reset_financial_values(self):
        """Resetea todos los valores financieros a cero"""
        financial_fields = [
            'subtotal_antes_descuento', 'monto_descuento', 'subtotal_bn', 'subtotal_color',
            'igv_bn', 'igv_color', 'total_bn', 'total_color', 'subtotal', 'igv', 'total'
        ]
        for field in financial_fields:
            setattr(self, field, 0.0)

    # ==========================================
    # MÉTODOS DE CICLO DE VIDA
    # ==========================================

    @api.model_create_multi
    def create(self, vals_list):
        """Método create optimizado para Odoo 19"""
        for vals in vals_list:
            # Generar secuencia si es necesario
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(SEQUENCE_CODE) or 'New'
            
            # Configurar contadores anteriores si no están definidos
            if not vals.get('contador_anterior_bn') and vals.get('maquina_id'):
                contadores_anteriores = self._get_contadores_anteriores(vals['maquina_id'])
                vals.update(contadores_anteriores)
        
        return super().create(vals_list)

    def _get_contadores_anteriores(self, maquina_id):
        """Obtiene los contadores de la última lectura confirmada"""
        ultima_lectura = self.search([
            ('maquina_id', '=', maquina_id),
            ('state', 'in', ['confirmed', 'invoiced'])
        ], limit=1, order='fecha desc, id desc')
        
        return {
            'contador_anterior_bn': ultima_lectura.contador_actual_bn if ultima_lectura else 0,
            'contador_anterior_color': ultima_lectura.contador_actual_color if ultima_lectura else 0
        }

    # ==========================================
    # ONCHANGE METHODS
    # ==========================================

    @api.onchange('maquina_id')
    def _onchange_maquina(self):
        """Configura valores por defecto al seleccionar máquina"""
        if not self.maquina_id:
            return
        
        # Configurar contadores anteriores
        contadores = self._get_contadores_anteriores(self.maquina_id.id)
        self.contador_anterior_bn = contadores['contador_anterior_bn']
        self.contador_anterior_color = contadores['contador_anterior_color']
        
        # Configurar fecha de facturación
        if self.maquina_id.dia_facturacion:
            self.fecha_facturacion = self._calcular_fecha_facturacion()

    def _calcular_fecha_facturacion(self):
        """Calcula la fecha de facturación basada en la configuración de la máquina"""
        if not self.maquina_id.dia_facturacion:
            return fields.Date.today()
        
        fecha_base = fields.Date.today()
        max_day = calendar.monthrange(fecha_base.year, fecha_base.month)[1]
        dia = min(self.maquina_id.dia_facturacion, max_day)
        fecha_facturacion = fecha_base.replace(day=dia)
        
        # Mover al siguiente mes si ya pasó la fecha
        if fecha_base > fecha_facturacion:
            if fecha_base.month == 12:
                fecha_facturacion = fecha_facturacion.replace(year=fecha_base.year + 1, month=1)
            else:
                fecha_facturacion = fecha_facturacion.replace(month=fecha_base.month + 1)
        
        # Ajustar si cae en domingo
        if fecha_facturacion.weekday() == 6:  # domingo
            fecha_facturacion -= timedelta(days=1)
        
        return fecha_facturacion

    # ==========================================
    # VALIDACIONES
    # ==========================================

    @api.constrains('contador_actual_bn', 'contador_anterior_bn')
    def _check_contador_bn(self):
        """Valida que el contador actual B/N no sea menor al anterior"""
        for record in self:
            if record.contador_actual_bn < record.contador_anterior_bn:
                raise ValidationError(
                    f'El contador actual B/N ({record.contador_actual_bn}) '
                    f'no puede ser menor al anterior ({record.contador_anterior_bn})'
                )

    @api.constrains('contador_actual_color', 'contador_anterior_color')
    def _check_contador_color(self):
        """Valida que el contador actual Color no sea menor al anterior"""
        for record in self:
            if record.contador_actual_color < record.contador_anterior_color:
                raise ValidationError(
                    f'El contador actual Color ({record.contador_actual_color}) '
                    f'no puede ser menor al anterior ({record.contador_anterior_color})'
                )

    @api.constrains('fecha_emision_factura', 'fecha')
    def _check_fecha_emision(self):
        """Valida que la fecha de emisión no sea anterior a la fecha de lectura"""
        for record in self:
            if record.fecha_emision_factura and record.fecha:
                if record.fecha_emision_factura < record.fecha:
                    raise ValidationError(
                        "La fecha de emisión no puede ser anterior a la fecha de lectura."
                    )

    # ==========================================
    # MÉTODOS DE ACCIÓN DE ESTADO
    # ==========================================

    def action_confirm(self):
        """Confirma la lectura del contador"""
        for record in self:
            if record.state != 'draft':
                raise UserError('Solo se pueden confirmar lecturas en estado borrador.')
        
        return self.write({'state': 'confirmed'})

    def action_draft(self):
        """Regresa la lectura a estado borrador"""
        for record in self:
            if record.state == 'invoiced':
                raise UserError('No se pueden regresar a borrador lecturas ya facturadas.')
        
        return self.write({'state': 'draft'})

    def action_cancel(self):
        """Cancela la lectura del contador"""
        for record in self:
            if record.state == 'invoiced':
                raise UserError('No se pueden cancelar lecturas ya facturadas.')
        
        return self.write({'state': 'cancelled'})

    # ==========================================
    # MÉTODOS DE FACTURACIÓN
    # ==========================================

    def action_create_invoice(self):
        """Crea una factura basada en la lectura del contador"""
        self.ensure_one()
        
        # Validaciones previas
        self._validate_invoice_creation()
        
        # Determinar productos necesarios y validar
        productos_requeridos = self._get_productos_requeridos()
        self._validate_productos_facturacion(productos_requeridos)
        
        # Crear la factura
        invoice = self._create_invoice_header()
        
        # Crear líneas de factura
        invoice_lines = self._create_invoice_lines(invoice, productos_requeridos)
        
        if not invoice_lines:
            raise UserError('No se pudieron crear líneas de factura válidas.')
        
        # Asignar líneas a la factura
        invoice.write({'invoice_line_ids': invoice_lines})
        
        # Actualizar estado
        self.write({'state': 'invoiced'})
        
        # Registrar en el chatter
        self._post_invoice_message(invoice)
        
        return self._return_invoice_action(invoice)

    def _validate_invoice_creation(self):
        """Valida que se pueda crear la factura"""
        if self.state != 'confirmed':
            raise UserError('Solo se pueden facturar lecturas confirmadas.')
        
        if not self.cliente_id:
            raise UserError('No se encontró cliente asociado a la máquina.')

    def _get_productos_requeridos(self):
        """Determina qué productos son necesarios según el tipo de máquina y copias"""
        productos = {}
        
        if self.maquina_id.tipo == 'monocroma':
            if self.copias_facturables_bn > 0:
                productos['bn'] = {
                    'producto': self.producto_facturable_bn_id,
                    'copias': self.copias_facturables_bn,
                    'subtotal': self.subtotal_bn
                }
        else:  # máquina color
            if self.copias_facturables_bn > 0:
                productos['bn'] = {
                    'producto': self.producto_facturable_bn_id,
                    'copias': self.copias_facturables_bn,
                    'subtotal': self.subtotal_bn
                }
            
            if self.copias_facturables_color > 0:
                productos['color'] = {
                    'producto': self.producto_facturable_color_id,
                    'copias': self.copias_facturables_color,
                    'subtotal': self.subtotal_color
                }
        
        return productos

    def _validate_productos_facturacion(self, productos_requeridos):
        """Valida que todos los productos necesarios estén configurados"""
        productos_faltantes = []
        
        for tipo, info in productos_requeridos.items():
            if not info['producto']:
                nombre_tipo = 'B/N' if tipo == 'bn' else 'Color'
                productos_faltantes.append(f"Producto {nombre_tipo}")
        
        if productos_faltantes:
            raise UserError(
                f"Faltan productos por configurar:\n" + 
                "\n".join([f"- {p}" for p in productos_faltantes]) +
                f"\n\nVe a la configuración de la máquina {self.serie} y configura los productos necesarios."
            )

    def _create_invoice_header(self):
        """Crea el encabezado de la factura"""
        # Determinar fecha de factura
        fecha_factura = self._get_fecha_factura_efectiva()
        
        # Información de la máquina
        modelo_maquina = self.maquina_id.name.name if self.maquina_id.name else 'N/A'
        info_maquina = f"Modelo: {modelo_maquina} - Serie: {self.serie}"
        
        invoice_vals = {
            'partner_id': self.cliente_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fecha_factura,
            'invoice_payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'invoice_origin': self.name,
            'narration': f'Facturación por uso de máquina {self.serie} - {self.mes_facturacion}\n{info_maquina}',
        }
        
        return self.env['account.move'].create(invoice_vals)

    def _create_invoice_lines(self, invoice, productos_requeridos):
        """Crea las líneas de la factura"""
        invoice_lines = []
        modelo_maquina = self.maquina_id.name.name if self.maquina_id.name else 'N/A'
        info_maquina = f"Modelo: {modelo_maquina} - Serie: {self.serie}"
        
        for tipo, info in productos_requeridos.items():
            if info['copias'] > 0 and info['producto']:
                nombre_tipo = 'B/N' if tipo == 'bn' else 'Color'
                descripcion = (
                    f"{info['producto'].name} - Copias {nombre_tipo}: {int(info['copias'])} - "
                    f"{self.mes_facturacion}\n{info_maquina}"
                )
                
                line_vals = {
                    'move_id': invoice.id,
                    'product_id': info['producto'].id,
                    'name': descripcion,
                    'quantity': 1,
                    'price_unit': info['subtotal'],
                    'account_id': self._get_product_account(info['producto']),
                }
                
                invoice_lines.append((0, 0, line_vals))
        
        return invoice_lines

    def _get_product_account(self, product):
        """Obtiene la cuenta contable del producto"""
        return (product.property_account_income_id.id or 
                product.categ_id.property_account_income_categ_id.id)

    def _get_fecha_factura_efectiva(self):
        """Determina la fecha efectiva para la factura"""
        if self.maquina_id.facturacion_automatica:
            return self.fecha_facturacion
        else:
            return self.fecha_emision_factura or fields.Date.today()

    def _post_invoice_message(self, invoice):
        """Registra mensaje en el chatter sobre la factura creada"""
        mensaje = (
            f'Factura creada: {invoice.name}\n'
            f'- B/N: {self.copias_facturables_bn} copias = {self.currency_id.symbol} {self.total_bn:.2f}\n'
            f'- Color: {self.copias_facturables_color} copias = {self.currency_id.symbol} {self.total_color:.2f}\n'
            f'- Total: {self.currency_id.symbol} {self.total:.2f}\n'
            f'- Fecha factura: {self._get_fecha_factura_efectiva()}'
        )
        
        self.message_post(
            body=mensaje,
            message_type='notification'
        )

    def _return_invoice_action(self, invoice):
        """Retorna la acción para mostrar la factura creada"""
        return {
            'name': 'Factura Creada',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_multiple_invoices(self):
        """Crea facturas para múltiples lecturas seleccionadas"""
        facturas_creadas = []
        errores = []
        
        for record in self:
            try:
                if record.state == 'confirmed' and record._can_create_invoice():
                    record.action_create_invoice()
                    facturas_creadas.append(record.name)
                else:
                    errores.append(f"{record.name}: Estado o configuración no válida")
            except Exception as e:
                errores.append(f"{record.name}: {str(e)}")
        
        return self._show_batch_result(facturas_creadas, errores)

    def _can_create_invoice(self):
        """Verifica si se puede crear factura para este registro"""
        try:
            productos_requeridos = self._get_productos_requeridos()
            self._validate_productos_facturacion(productos_requeridos)
            return True
        except:
            return False

    def _show_batch_result(self, facturas_creadas, errores):
        """Muestra el resultado del procesamiento en lote"""
        mensaje = f"Facturas creadas: {len(facturas_creadas)}"
        if errores:
            mensaje += f"\nErrores: {len(errores)}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Proceso de Facturación',
                'message': mensaje,
                'type': 'success' if facturas_creadas else 'warning',
                'sticky': True,
            }
        }

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def get_fecha_factura_efectiva(self):
        """Método público para obtener la fecha efectiva de facturación"""
        self.ensure_one()
        return self._get_fecha_factura_efectiva()

    def cargar_usuarios_asociados(self):
        """Carga los usuarios asociados a la máquina para detalle por usuario"""
        self.ensure_one()
        
        if not self.maquina_id:
            raise UserError('Primero selecciona la máquina asociada.')
        
        # Limpiar registros previos
        self.usuario_detalle_ids.unlink()
        
        # Buscar usuarios asociados
        usuarios = self.env['copier.machine.user'].search([
            ('maquina_id', '=', self.maquina_id.id)
        ])
        
        # Crear registros de detalle
        detalles_vals = []
        for usuario in usuarios:
            detalles_vals.append((0, 0, {
                'usuario_id': usuario.id,
                'cantidad_copias': 0  # Inicializar en 0 para ingreso manual
            }))
        
        self.usuario_detalle_ids = detalles_vals

    def name_get(self):
        """Personaliza la representación del nombre del registro"""
        result = []
        for record in self:
            name_parts = [
                record.cliente_id.name or '',
                record.serie or '',
                record.mes_facturacion or ''
            ]
            name = ' - '.join(filter(None, name_parts))
            result.append((record.id, name))
        return result

    # ==========================================
    # MÉTODOS DE REPORTE
    # ==========================================

    def action_print_report(self):
        """Genera el reporte de lectura de contadores"""
        return self.env.ref('copier_company.action_report_counter_readings').report_action(self)

    def action_generate_report(self):
        """Alias para generar reporte (compatibilidad)"""
        return self.action_print_report()

    # ==========================================
    # MÉTODOS DE DEBUG (DESARROLLO)
    # ==========================================

    def debug_counter_totales(self):
        """Método de debug para verificar cálculos de totales"""
        self.ensure_one()
        
        debug_info = {
            'counter_id': self.id,
            'serie': self.serie,
            'tipo_calculo': self.maquina_id.tipo_calculo,
            'volumen_bn': self.copias_facturables_bn,
            'volumen_color': self.copias_facturables_color,
            'precio_bn': self.precio_bn_sin_igv,
            'precio_color': self.precio_color_sin_igv,
            'descuento': self.descuento_porcentaje,
            'subtotal_antes': self.subtotal_antes_descuento,
            'monto_descuento': self.monto_descuento,
            'subtotal': self.subtotal,
            'igv': self.igv,
            'total': self.total,
        }
        
        _logger.info(f"DEBUG Counter {self.id}: {debug_info}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug Counter',
                'message': f'Total: {self.total}. Ver logs para detalles completos.',
                'type': 'info',
                'sticky': True,
            }
        }

    # ==========================================
    # MÉTODOS AUTOMATIZADOS (CRON)
    # ==========================================

    @api.model
    def generate_monthly_readings(self):
        """
        Genera lecturas mensuales automáticamente via cron job.
        Busca máquinas que necesiten lectura según su día de facturación.
        """
        _logger.info("=== Iniciando generación automática de lecturas mensuales ===")
        
        today = fields.Date.today()
        readings_created = 0
        
        # Buscar máquinas activas en alquiler con día de facturación configurado
        machines = self.env['copier.company'].search([
            ('estado_maquina_id.name', '=', 'Alquilada'),
            ('dia_facturacion', '!=', False)
        ])
        
        _logger.info(f"Encontradas {len(machines)} máquinas para evaluar")
        
        for machine in machines:
            try:
                if self._should_create_reading_today(machine, today):
                    if not self._reading_exists_for_period(machine, today):
                        self._create_automatic_reading(machine, today)
                        readings_created += 1
                        _logger.info(f"Lectura creada para máquina {machine.serie_id}")
                
            except Exception as e:
                _logger.error(f"Error procesando máquina {machine.serie_id}: {str(e)}")
                continue
        
        _logger.info(f"=== Proceso completado: {readings_created} lecturas creadas ===")
        return True

    def _should_create_reading_today(self, machine, today):
        """Determina si se debe crear lectura hoy para la máquina"""
        fecha_facturacion = self._calculate_billing_date(machine, today)
        
        # Ajustar si cae en domingo
        if fecha_facturacion.weekday() == 6:  # domingo
            fecha_facturacion -= timedelta(days=1)
        
        return today == fecha_facturacion

    def _calculate_billing_date(self, machine, reference_date):
        """Calcula la fecha de facturación para la máquina"""
        max_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
        dia = min(machine.dia_facturacion, max_day)
        fecha_facturacion = reference_date.replace(day=dia)
        
        # Mover al siguiente mes si ya pasó
        if reference_date > fecha_facturacion:
            if reference_date.month == 12:
                fecha_facturacion = fecha_facturacion.replace(year=reference_date.year + 1, month=1)
            else:
                fecha_facturacion = fecha_facturacion.replace(month=reference_date.month + 1)
        
        return fecha_facturacion

    def _reading_exists_for_period(self, machine, reference_date):
        """Verifica si ya existe lectura para el período"""
        fecha_facturacion = self._calculate_billing_date(machine, reference_date)
        
        existing_reading = self.search([
            ('maquina_id', '=', machine.id),
            ('fecha_facturacion', '=', fecha_facturacion)
        ], limit=1)
        
        return bool(existing_reading)

    def _create_automatic_reading(self, machine, today):
        """Crea una nueva lectura automática"""
        fecha_facturacion = self._calculate_billing_date(machine, today)
        
        # Obtener contadores anteriores
        contadores_anteriores = self._get_contadores_anteriores(machine.id)
        
        # Crear lectura con contadores iguales (pendiente de actualización manual)
        vals = {
            'maquina_id': machine.id,
            'fecha': today,
            'fecha_facturacion': fecha_facturacion,
            'fecha_emision_factura': False,  # Para configuración manual
            'contador_anterior_bn': contadores_anteriores['contador_anterior_bn'],
            'contador_anterior_color': contadores_anteriores['contador_anterior_color'],
            'contador_actual_bn': contadores_anteriores['contador_anterior_bn'],
            'contador_actual_color': contadores_anteriores['contador_anterior_color'],
            'state': 'draft'
        }
        
        self.create(vals)
        self.env.cr.commit()


# ==========================================
# MODELO PARA REPORTES
# ==========================================

class ReportCounterReadings(models.AbstractModel):
    _name = 'report.copier_company.report_counter_readings'
    _description = 'Reporte de Lecturas de Contadores'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara los datos para el reporte de lecturas"""
        docs = self.env['copier.counter'].browse(docids)
        
        # Validar que todos los registros sean del mismo cliente
        clientes = docs.mapped('cliente_id')
        if len(clientes) > 1:
            raise UserError(
                "Debe seleccionar registros de un solo cliente para generar el reporte."
            )
        
        # Agrupar por tipo de máquina
        maquinas_mono = docs.filtered(lambda x: x.maquina_id.tipo == 'monocroma')
        maquinas_color = docs.filtered(lambda x: x.maquina_id.tipo == 'color')
        
        # Calcular totales
        total_general = sum(docs.mapped('total'))
        total_bn = sum(docs.mapped('total_bn'))
        total_color = sum(docs.mapped('total_color'))
        total_copias_bn = sum(docs.mapped('copias_facturables_bn'))
        total_copias_color = sum(docs.mapped('copias_facturables_color'))
        
        return {
            'docs': docs,
            'doc_ids': docids,
            'doc_model': 'copier.counter',
            'company': self.env.company,
            'cliente': clientes[0] if clientes else None,
            'maquinas_mono': maquinas_mono,
            'maquinas_color': maquinas_color,
            'total_general': total_general,
            'total_bn': total_bn,
            'total_color': total_color,
            'total_copias_bn': total_copias_bn,
            'total_copias_color': total_copias_color,
            'fecha_reporte': fields.Date.today(),
        }


# ==========================================
# MODELOS RELACIONADOS
# ==========================================

class CopierMachineUser(models.Model):
    _name = 'copier.machine.user'
    _description = 'Usuarios Internos por Máquina'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre Empresa/Usuario',
        required=True,
        tracking=True
    )
    
    clave = fields.Char(
        string='Clave',
        help="Clave de acceso del usuario en la máquina"
    )
    
    correo = fields.Char(
        string='Correo Electrónico',
        help="Email de contacto del usuario"
    )
    
    maquina_id = fields.Many2one(
        'copier.company',
        string='Máquina Asociada',
        required=True,
        ondelete='cascade'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name}"
            if record.maquina_id:
                name += f" ({record.maquina_id.serie_id})"
            result.append((record.id, name))
        return result


class CopierCounterUserDetail(models.Model):
    _name = 'copier.counter.user.detail'
    _description = 'Detalle mensual de copias por usuario'

    contador_id = fields.Many2one(
        'copier.counter',
        string='Contador General',
        required=True,
        ondelete='cascade'
    )
    
    usuario_id = fields.Many2one(
        'copier.machine.user',
        string='Empresa/Usuario',
        required=True
    )
    
    cantidad_copias = fields.Integer(
        string='Total Copias',
        required=True,
        default=0
    )
    
    notas = fields.Text(
        string='Notas',
        help="Observaciones adicionales sobre el uso"
    )

    @api.constrains('cantidad_copias')
    def _check_cantidad_copias(self):
        for record in self:
            if record.cantidad_copias < 0:
                raise ValidationError('La cantidad de copias no puede ser negativa.')