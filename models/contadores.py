from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import calendar
import logging
_logger = logging.getLogger(__name__)


class CopierCounter(models.Model):
    _name = 'copier.counter'
    _description = 'Control de Contadores de Máquinas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_facturacion desc, maquina_id'

    name = fields.Char('Referencia', default='New', copy=False, readonly=True)
    
    # Campos de relación y fechas
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
        store=True
    )
    serie = fields.Char(
        related='maquina_id.serie_id',
        string='Serie',
        store=True
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
    def create(self, vals):
        if not vals.get('contador_anterior_bn'):
            # Buscar última lectura confirmada
            ultima_lectura = self.search([
                ('maquina_id', '=', vals.get('maquina_id')),
                ('state', '=', 'confirmed')
            ], limit=1, order='fecha desc, id desc')
            
            vals['contador_anterior_bn'] = ultima_lectura.contador_actual_bn if ultima_lectura else 0
            vals['contador_anterior_color'] = ultima_lectura.contador_actual_color if ultima_lectura else 0

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('copier.counter') or 'New'
            
        return super(CopierCounter, self).create(vals)
    @api.depends('fecha_facturacion')
    def _compute_mes_facturacion(self):
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        for record in self:
            if record.fecha_facturacion:
                record.mes_facturacion = f"{meses[record.fecha_facturacion.month]} {record.fecha_facturacion.year}"

    @api.onchange('maquina_id')
    def _onchange_maquina(self):
        if self.maquina_id:
            ultima_lectura = self.search([
                ('maquina_id', '=', self.maquina_id.id),
                ('state', 'in', ['confirmed', 'invoiced'])
            ], limit=1, order='fecha desc, id desc')
            
            # Asignar contadores anteriores
            self.contador_anterior_bn = ultima_lectura.contador_actual_bn if ultima_lectura else 0
            self.contador_anterior_color = ultima_lectura.contador_actual_color if ultima_lectura else 0
            
            # Configurar fecha de facturación
            if self.maquina_id.dia_facturacion:
                fecha_base = fields.Date.today()
                dia = min(self.maquina_id.dia_facturacion, calendar.monthrange(fecha_base.year, fecha_base.month)[1])
                fecha_facturacion = fecha_base.replace(day=dia)
                
                if fecha_base > fecha_facturacion:
                    if fecha_base.month == 12:
                        fecha_facturacion = fecha_facturacion.replace(year=fecha_base.year + 1, month=1)
                    else:
                        fecha_facturacion = fecha_facturacion.replace(month=fecha_base.month + 1)
                
                if fecha_facturacion.weekday() == 6:  # domingo
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
    def _compute_facturables(self):
        for record in self:
            # Para B/N - siempre se factura al menos el volumen mensual
            record.copias_facturables_bn = max(
                record.total_copias_bn,
                record.maquina_id.volumen_mensual_bn or 0
            )
            
            # Para Color - igual que B/N, facturar al menos el volumen mensual
            record.copias_facturables_color = max(
                record.total_copias_color,
                record.maquina_id.volumen_mensual_color or 0
            )
   
    @api.depends('copias_facturables_bn', 'copias_facturables_color',
                'precio_bn_sin_igv', 'precio_color_sin_igv')
    def _compute_totales(self):
        """Calcula totales usando los precios sin IGV con precisión completa"""
        for record in self:
            # Calcular subtotal usando precios sin IGV con toda la precisión
            subtotal_bn = record.copias_facturables_bn * record.precio_bn_sin_igv
            subtotal_color = record.copias_facturables_color * record.precio_color_sin_igv
            
            # Asignar valores redondeando solo al final para los campos monetarios
            record.subtotal = round(subtotal_bn + subtotal_color, 2)
            record.igv = round(record.subtotal * 0.18, 2)
            record.total = round(record.subtotal * 1.18, 2)
  

    def action_confirm(self):
        self.ensure_one()
        if self.contador_actual_bn < self.contador_anterior_bn:
            raise UserError('El contador actual B/N no puede ser menor al anterior')
        if self.contador_actual_color < self.contador_anterior_color:
            raise UserError('El contador actual Color no puede ser menor al anterior')
        self.write({'state': 'confirmed'})

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
        Método para generar lecturas mensuales automáticamente.
        Se ejecuta mediante el cron job.
        """
        today = fields.Date.today()
        
        # Buscar máquinas activas en alquiler
        machines = self.env['copier.company'].search([
            ('estado_maquina_id.name', '=', 'Alquilada'),
            ('dia_facturacion', '!=', False)
        ])

        for machine in machines:
            try:
                # Calcular fecha de facturación
                dia = min(machine.dia_facturacion, 
                        (today.replace(day=1) + relativedelta(months=1, days=-1)).day)
                fecha_facturacion = today.replace(day=dia)

                # Ajustar al mes siguiente si ya pasó la fecha
                if today > fecha_facturacion:
                    if today.month == 12:
                        fecha_facturacion = fecha_facturacion.replace(year=today.year + 1, month=1)
                    else:
                        fecha_facturacion = fecha_facturacion.replace(month=today.month + 1)

                # Determinar si crear hoy basado en la lógica actualizada
                crear_hoy = False
                if fecha_facturacion.weekday() == 6:  # Si es domingo
                    fecha_facturacion -= timedelta(days=1)  # Mover al sábado
                    crear_hoy = today == fecha_facturacion
                else:
                    crear_hoy = today == fecha_facturacion

                # Verificar si ya existe lectura para este período
                existing_reading = self.env['copier.counter'].search([
                    ('maquina_id', '=', machine.id),
                    ('fecha_facturacion', '=', fecha_facturacion)
                ], limit=1)

                if existing_reading:
                    _logger.info(f"Ya existe lectura para la máquina {machine.serie_id} "
                            f"en fecha {fecha_facturacion}")
                    continue

                # Crear nueva lectura si corresponde
                if crear_hoy:
                    # Obtener última lectura confirmada O facturada ← CAMBIO AQUÍ
                    ultima_lectura = self.env['copier.counter'].search([
                        ('maquina_id', '=', machine.id),
                        ('state', 'in', ['confirmed', 'invoiced'])  # ← CAMBIO PRINCIPAL
                    ], limit=1, order='fecha desc, id desc')

                    # Valores por defecto para los contadores
                    contador_anterior_bn = ultima_lectura.contador_actual_bn if ultima_lectura else 0
                    contador_anterior_color = ultima_lectura.contador_actual_color if ultima_lectura else 0
                    
                    # Crear registro con valores por defecto para contadores actuales
                    vals = {
                        'maquina_id': machine.id,
                        'fecha': today,
                        'fecha_facturacion': fecha_facturacion,
                        'contador_anterior_bn': contador_anterior_bn,
                        'contador_anterior_color': contador_anterior_color,
                        'contador_actual_bn': contador_anterior_bn,
                        'contador_actual_color': contador_anterior_color,
                        'state': 'draft'
                    }
                    
                    self.env['copier.counter'].create(vals)
                    self.env.cr.commit()
                    
                    _logger.info(
                        f"Creada nueva lectura para máquina {machine.serie_id} "
                        f"con fecha de facturación {fecha_facturacion}"
                    )

            except Exception as e:
                _logger.error(f"Error al procesar máquina {machine.serie_id}: {str(e)}")
                self.env.cr.rollback()
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
        
        self.usuario_detalle_ids.unlink()  # Limpia registros previos
        usuarios = self.env['copier.machine.user'].search([
            ('maquina_id', '=', self.maquina_id.id)
        ])
        detalles = [(0, 0, {
            'usuario_id': usuario.id,
            'cantidad_copias': 0  # Inicializa en 0 para ingresar manualmente
        }) for usuario in usuarios]

        self.usuario_detalle_ids = detalles
    


    # Agregar después de los campos financieros existentes
    producto_facturable_id = fields.Many2one(
        'product.product',
        related='maquina_id.producto_facturable_id',
        string='Producto a Facturar',
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
        """Crea una factura basada en la lectura del contador"""
        self.ensure_one()
        
        if self.state != 'confirmed':
            raise UserError('Solo se pueden facturar lecturas confirmadas.')
        
        if not self.cliente_id:
            raise UserError('No se encontró cliente asociado a la máquina.')
        
        # Validar productos según tipo de máquina
        if self.maquina_id.tipo == 'monocroma':
            if not self.producto_facturable_bn_id:
                raise UserError('La máquina monocroma debe tener configurado un producto B/N.')
        else:  # color
            if not self.producto_facturable_bn_id or not self.producto_facturable_color_id:
                raise UserError('La máquina color debe tener configurados ambos productos (B/N y Color).')
        
        # Preparar información del modelo y serie
        modelo_maquina = self.maquina_id.name.name if self.maquina_id.name else 'N/A'
        info_maquina = f"Modelo: {modelo_maquina} - Serie: {self.serie}"
        
        # Crear factura
        invoice_vals = {
            'partner_id': self.cliente_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.fecha_facturacion,
            'invoice_origin': self.name,
            'narration': f'Facturación por uso de máquina {self.serie} - {self.mes_facturacion}\n{info_maquina}',
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Crear líneas de factura
        invoice_lines = []
        
        # Línea para copias B/N (si hay y hay producto configurado)
        if self.copias_facturables_bn > 0 and self.producto_facturable_bn_id:
            descripcion_bn = f'{self.producto_facturable_bn_id.name} - Copias B/N: {int(self.copias_facturables_bn)} - {self.mes_facturacion}\n{info_maquina}'
            monto_bn = self.copias_facturables_bn * self.precio_bn_sin_igv
            
            line_vals_bn = {
                'move_id': invoice.id,
                'product_id': self.producto_facturable_bn_id.id,
                'name': descripcion_bn,
                'quantity': 1,  # 1 máquina
                'price_unit': monto_bn,  # Monto total por las copias B/N
                'account_id': self.producto_facturable_bn_id.property_account_income_id.id or 
                            self.producto_facturable_bn_id.categ_id.property_account_income_categ_id.id,
            }
            invoice_lines.append((0, 0, line_vals_bn))
        
        # Línea para copias Color (si hay y hay producto configurado)
        if self.copias_facturables_color > 0 and self.producto_facturable_color_id:
            descripcion_color = f'{self.producto_facturable_color_id.name} - Copias Color: {int(self.copias_facturables_color)} - {self.mes_facturacion}\n{info_maquina}'
            monto_color = self.copias_facturables_color * self.precio_color_sin_igv
            
            line_vals_color = {
                'move_id': invoice.id,
                'product_id': self.producto_facturable_color_id.id,
                'name': descripcion_color,
                'quantity': 1,  # 1 máquina
                'price_unit': monto_color,  # Monto total por las copias Color
                'account_id': self.producto_facturable_color_id.property_account_income_id.id or 
                            self.producto_facturable_color_id.categ_id.property_account_income_categ_id.id,
            }
            invoice_lines.append((0, 0, line_vals_color))
        
        # Si no hay líneas específicas, crear línea general con el subtotal
        if not invoice_lines:
            producto_generico = self.producto_facturable_bn_id or self.producto_facturable_color_id
            if producto_generico:
                descripcion_general = f'{producto_generico.name} - {self.mes_facturacion}\n{info_maquina}'
                
                line_vals_general = {
                    'move_id': invoice.id,
                    'product_id': producto_generico.id,
                    'name': descripcion_general,
                    'quantity': 1,  # 1 máquina
                    'price_unit': self.subtotal,  # Monto total del periodo
                    'account_id': producto_generico.property_account_income_id.id or 
                                producto_generico.categ_id.property_account_income_categ_id.id,
                }
                invoice_lines.append((0, 0, line_vals_general))
        
        if not invoice_lines:
            raise UserError('No se pudieron crear líneas de factura. Verifique la configuración de productos.')
        
        # Asignar líneas a la factura
        invoice.write({'invoice_line_ids': invoice_lines})
        
        # Marcar como facturado
        self.write({'state': 'invoiced'})
        
        # Agregar nota en el chatter
        self.message_post(
            body=f'Factura creada: {invoice.name}',
            message_type='notification'
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
        """Crea facturas para múltiples lecturas seleccionadas"""
        facturas_creadas = []
        errores = []
        
        for record in self:
            try:
                if record.state == 'confirmed' and record.producto_facturable_id:
                    result = record.action_create_invoice()
                    facturas_creadas.append(record.name)
                else:
                    errores.append(f"{record.name}: Estado o producto no válido")
            except Exception as e:
                errores.append(f"{record.name}: {str(e)}")
        
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
    maquina_id = fields.Many2one('copier.company', string='Máquina Asociada', required=True)

class CopierCounterUserDetail(models.Model):
    _name = 'copier.counter.user.detail'
    _description = 'Detalle mensual de copias por usuario'

    contador_id = fields.Many2one('copier.counter', string='Contador General', required=True, ondelete='cascade')
    usuario_id = fields.Many2one('copier.machine.user', string='Empresa/Usuario', required=True)
    cantidad_copias = fields.Integer('Total Copias', required=True)
