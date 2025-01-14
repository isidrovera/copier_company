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

    # Campos financieros
    currency_id = fields.Many2one(
        'res.currency',
        related='maquina_id.currency_id',
        string='Moneda'
    )
    precio_bn = fields.Monetary(
        'Precio B/N',
        related='maquina_id.costo_copia_bn',
        readonly=True,
        currency_field='currency_id'
    )
    precio_color = fields.Monetary(
        'Precio Color',
        related='maquina_id.costo_copia_color',
        readonly=True,
        currency_field='currency_id'
    )
    # Agregar campo para total sin IGV
    total_sin_igv = fields.Monetary(
        'Total sin IGV',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
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
                ('state', '=', 'confirmed')
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
                'maquina_id.volumen_compartido_id')
    def _compute_excesos(self):
        for record in self:
            if record.maquina_id.usar_volumen_compartido and record.maquina_id.volumen_compartido_id:
                plan = record.maquina_id.volumen_compartido_id
                
                # Obtener todas las lecturas del mismo mes para máquinas del plan
                fecha_inicio = record.fecha_facturacion.replace(day=1)
                fecha_fin = (fecha_inicio + relativedelta(months=1, days=-1))
                
                # Buscar todas las lecturas confirmadas del mes para el mismo plan
                lecturas_mes = self.search([
                    ('maquina_id.volumen_compartido_id', '=', plan.id),
                    ('fecha_facturacion', '>=', fecha_inicio),
                    ('fecha_facturacion', '<=', fecha_fin),
                    ('state', '=', 'confirmed')
                ])
                
                # Calcular totales del mes para todas las máquinas
                total_mes_bn = sum(lecturas_mes.mapped('total_copias_bn'))
                total_mes_color = sum(lecturas_mes.mapped('total_copias_color'))
                
                # Calcular excesos totales
                exceso_total_bn = max(0, total_mes_bn - plan.volumen_mensual_bn)
                exceso_total_color = max(0, total_mes_color - plan.volumen_mensual_color)
                
                # Calcular la proporción de uso de esta máquina
                if exceso_total_bn > 0:
                    proporcion_bn = record.total_copias_bn / total_mes_bn if total_mes_bn else 0
                    record.exceso_bn = int(exceso_total_bn * proporcion_bn)
                else:
                    record.exceso_bn = 0
                    
                if exceso_total_color > 0:
                    proporcion_color = record.total_copias_color / total_mes_color if total_mes_color else 0
                    record.exceso_color = int(exceso_total_color * proporcion_color)
                else:
                    record.exceso_color = 0
            else:
                # Cálculo normal para máquinas individuales
                record.exceso_bn = max(0, record.total_copias_bn - record.maquina_id.volumen_mensual_bn)
                record.exceso_color = max(0, record.total_copias_color - record.maquina_id.volumen_mensual_color)

    @api.depends('total_copias_bn', 'total_copias_color', 
                'maquina_id.volumen_compartido_id')
    def _compute_facturables(self):
        for record in self:
            if record.maquina_id.usar_volumen_compartido and record.maquina_id.volumen_compartido_id:
                plan = record.maquina_id.volumen_compartido_id
                
                # Obtener todas las lecturas del mismo mes para máquinas del plan
                fecha_inicio = record.fecha_facturacion.replace(day=1)
                fecha_fin = (fecha_inicio + relativedelta(months=1, days=-1))
                
                lecturas_mes = self.search([
                    ('maquina_id.volumen_compartido_id', '=', plan.id),
                    ('fecha_facturacion', '>=', fecha_inicio),
                    ('fecha_facturacion', '<=', fecha_fin),
                    ('state', '=', 'confirmed')
                ])
                
                # Distribuir el volumen compartido proporcionalmente
                total_bn_grupo = sum(lecturas_mes.mapped('total_copias_bn'))
                total_color_grupo = sum(lecturas_mes.mapped('total_copias_color'))
                
                if total_bn_grupo > 0:
                    proporcion_bn = record.total_copias_bn / total_bn_grupo
                    record.copias_facturables_bn = int(plan.volumen_mensual_bn * proporcion_bn)
                else:
                    record.copias_facturables_bn = record.total_copias_bn
                
                if total_color_grupo > 0:
                    proporcion_color = record.total_copias_color / total_color_grupo
                    record.copias_facturables_color = int(plan.volumen_mensual_color * proporcion_color)
                else:
                    record.copias_facturables_color = record.total_copias_color
            else:
                # Cálculo normal para máquinas individuales
                record.copias_facturables_bn = max(
                    record.total_copias_bn,
                    record.maquina_id.volumen_mensual_bn or 0
                )
                record.copias_facturables_color = max(
                    record.total_copias_color,
                    record.maquina_id.volumen_mensual_color or 0
                )
    precios_incluyen_igv = fields.Boolean(
        'Precios Incluyen IGV',
        default=True,
        help="Si está marcado, los precios ya incluyen IGV y se calculará el monto base dividiendo entre 1.18"
    )
    precio_bn_incluye_igv = fields.Boolean(
        string='Precio B/N incluye IGV',
        default=True,
        help='Marcar si el precio B/N ya incluye IGV'
    )
    precio_color_incluye_igv = fields.Boolean(
        string='Precio Color incluye IGV',
        default=False,
        help='Marcar si el precio Color ya incluye IGV'
    )

    @api.depends('copias_facturables_bn', 'copias_facturables_color',
                'precio_bn', 'precio_color')
    def _compute_totales(self):
        for record in self:
            # Cálculo B/N (sin IGV)
            subtotal_bn = record.copias_facturables_bn * record.precio_bn
            total_bn = subtotal_bn * 1.18
            
            # Cálculo Color (con IGV incluido)
            total_color = record.copias_facturables_color * record.precio_color
            subtotal_color = total_color

            # Asignar valores
            record.subtotal = subtotal_bn + subtotal_color
            record.total_sin_igv = subtotal_bn + subtotal_color
            record.igv = total_bn - subtotal_bn
            record.total = total_bn + total_color

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
                    # Obtener última lectura confirmada
                    ultima_lectura = self.env['copier.counter'].search([
                        ('maquina_id', '=', machine.id),
                        ('state', '=', 'confirmed')
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
                        'contador_actual_bn': contador_anterior_bn,  # Inicializar con el mismo valor
                        'contador_actual_color': contador_anterior_color,  # Inicializar con el mismo valor
                        'state': 'draft'  # Asegurarnos que se crea en estado borrador
                    }
                    
                    self.env['copier.counter'].create(vals)
                    self.env.cr.commit()  # Commit después de cada creación exitosa
                    
                    _logger.info(
                        f"Creada nueva lectura para máquina {machine.serie_id} "
                        f"con fecha de facturación {fecha_facturacion}"
                    )

            except Exception as e:
                _logger.error(f"Error al procesar máquina {machine.serie_id}: {str(e)}")
                self.env.cr.rollback()  # Rollback en caso de error
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


class CopierVolumenCompartido(models.Model):
    _name = 'copier.volumen.compartido'
    _description = 'Volumen Compartido entre Máquinas'
    _inherit = ['mail.thread']
    _rec_name = 'nombre'

    nombre = fields.Char('Nombre del Plan', required=True, tracking=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    volumen_mensual_bn = fields.Integer(
        string='Volumen Mensual B/N Compartido',
        help='Cantidad total de copias B/N a compartir entre las máquinas',
        tracking=True
    )
    volumen_mensual_color = fields.Integer(
        string='Volumen Mensual Color Compartido',
        help='Cantidad total de copias color a compartir entre las máquinas',
        tracking=True
    )

    maquinas_ids = fields.One2many(
        'copier.company',
        'volumen_compartido_id',
        string='Máquinas en el Plan'
    )

    maquinas_count = fields.Integer(
        string='Cantidad de Máquinas',
        compute='_compute_maquinas_count',
        store=True
    )

    @api.depends('maquinas_ids')
    def _compute_maquinas_count(self):
        for record in self:
            record.maquinas_count = len(record.maquinas_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f'{record.nombre} - {record.cliente_id.name}'
            result.append((record.id, name))
        return result

    @api.model
    def _get_thread_with_access(self, res_id, access_token=False, **kwargs):
        """ Implementación del método requerido por el sistema de mensajería """
        if not res_id:
            return False
        try:
            record = self.browse(int(res_id)).exists()
            if not record:
                return False
            record.check_access_rights('read')
            record.check_access_rule('read')
            return record
        except AccessError:
            return False