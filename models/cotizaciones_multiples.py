from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class CopierQuotation(models.Model):
    """Modelo principal para cotizaciones con múltiples equipos y modalidades de pago"""
    _name = 'copier.quotation'
    _description = 'Cotización de Alquiler de Equipos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    

    # Información básica
    name = fields.Char('Número de Cotización', default='New', copy=False, required=True, readonly=True)
    fecha_cotizacion = fields.Date('Fecha de Cotización', default=fields.Date.today, required=True, tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('copier.quotation') or 'COT/0001'
        return super(CopierQuotation, self).create(vals)

    # Cliente
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    tipo_identificacion = fields.Many2one(related='cliente_id.l10n_latam_identification_type_id', 
                                        string="Tipo de identificación", readonly=False)
    identificacion = fields.Char(related='cliente_id.vat', string="Número de identificación", readonly=False)
    contacto = fields.Char('Persona de Contacto')
    telefono = fields.Char('Teléfono')
    email = fields.Char('Email')
    
    # Ubicación
    direccion = fields.Text('Dirección de Instalación')
    sede = fields.Char('Sede/Sucursal')
    
    # Estado de la cotización
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('convertido', 'Convertido a Contrato')
    ], string='Estado', default='borrador', tracking=True)
    
    # Líneas de equipos
    linea_equipos_ids = fields.One2many('copier.quotation.line', 'quotation_id', 
                                       string='Equipos Cotizados', copy=True)
    
    # Modalidad de pago y configuración
    modalidad_pago_id = fields.Many2one('copier.payment.mode', string='Modalidad de Pago', 
                                       required=True, tracking=True)
    
    # Fechas del contrato
    fecha_inicio_propuesta = fields.Date('Fecha Inicio Propuesta')
    duracion_contrato_id = fields.Many2one('copier.duracion', string="Duración del Contrato",
                                          default=lambda self: self.env.ref('copier_company.duracion_1_año').id)
    fecha_fin_propuesta = fields.Date('Fecha Fin Propuesta', compute='_compute_fecha_fin', store=True)
    
    @api.depends('fecha_inicio_propuesta', 'duracion_contrato_id')
    def _compute_fecha_fin(self):
        for record in self:
            if record.fecha_inicio_propuesta and record.duracion_contrato_id:
                start_date = record.fecha_inicio_propuesta
                duracion = record.duracion_contrato_id.name
                
                if duracion == '6 Meses':
                    record.fecha_fin_propuesta = start_date + relativedelta(months=+6)
                elif duracion == '1 Año':
                    record.fecha_fin_propuesta = start_date + relativedelta(years=+1)
                elif duracion == '2 Años':
                    record.fecha_fin_propuesta = start_date + relativedelta(years=+2)
                else:
                    record.fecha_fin_propuesta = False
            else:
                record.fecha_fin_propuesta = False
    
    # Configuración financiera
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                 default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1))
    descuento_general = fields.Float('Descuento General (%)', default=0.0)
    igv = fields.Float('IGV (%)', default=18.0)
    
    # Campos calculados - Totales mensuales
    subtotal_mensual = fields.Monetary('Subtotal Mensual', compute='_compute_totales', 
                                      store=True, currency_field='currency_id')
    descuento_mensual = fields.Monetary('Descuento Mensual', compute='_compute_totales', 
                                       store=True, currency_field='currency_id')
    subtotal_con_descuento_mensual = fields.Monetary('Subtotal Mensual c/Desc', compute='_compute_totales', 
                                                     store=True, currency_field='currency_id')
    igv_mensual = fields.Monetary('IGV Mensual', compute='_compute_totales', 
                                 store=True, currency_field='currency_id')
    total_mensual = fields.Monetary('Total Mensual', compute='_compute_totales', 
                                   store=True, currency_field='currency_id')
    
    # Campos calculados - Totales por modalidad de pago
    subtotal_modalidad = fields.Monetary('Subtotal por Modalidad', compute='_compute_totales', 
                                        store=True, currency_field='currency_id')
    descuento_modalidad = fields.Monetary('Descuento por Modalidad', compute='_compute_totales', 
                                         store=True, currency_field='currency_id')
    descuento_total = fields.Monetary('Descuento Total', compute='_compute_totales', 
                                     store=True, currency_field='currency_id')
    subtotal_final = fields.Monetary('Subtotal Final', compute='_compute_totales', 
                                    store=True, currency_field='currency_id')
    igv_final = fields.Monetary('IGV Final', compute='_compute_totales', 
                               store=True, currency_field='currency_id')
    total_por_modalidad = fields.Monetary('Total por Modalidad', compute='_compute_totales', 
                                         store=True, currency_field='currency_id')
    
    # Total anual para referencia
    total_anual = fields.Monetary('Total Anual', compute='_compute_totales', 
                                 store=True, currency_field='currency_id')
    
    @api.depends('linea_equipos_ids.subtotal_linea', 'descuento_general', 'igv', 'modalidad_pago_id')
    def _compute_totales(self):
        for record in self:
            # 1. Calcular totales mensuales base
            subtotal_mensual = sum(record.linea_equipos_ids.mapped('subtotal_linea'))
            
            # 2. Aplicar descuento general mensual
            descuento_mensual = subtotal_mensual * (record.descuento_general / 100.0)
            subtotal_con_descuento_mensual = subtotal_mensual - descuento_mensual
            
            # 3. Calcular IGV mensual
            igv_mensual = subtotal_con_descuento_mensual * (record.igv / 100.0)
            total_mensual = subtotal_con_descuento_mensual + igv_mensual
            
            # Asignar valores mensuales
            record.subtotal_mensual = subtotal_mensual
            record.descuento_mensual = descuento_mensual
            record.subtotal_con_descuento_mensual = subtotal_con_descuento_mensual
            record.igv_mensual = igv_mensual
            record.total_mensual = total_mensual
            
            # 4. Calcular según modalidad de pago
            if record.modalidad_pago_id:
                # Multiplicar por frecuencia de la modalidad
                frecuencia = record.modalidad_pago_id.frecuencia_meses
                subtotal_modalidad = subtotal_con_descuento_mensual * frecuencia
                
                # Aplicar descuento por modalidad de pago
                descuento_modalidad = subtotal_modalidad * (record.modalidad_pago_id.descuento_porcentaje / 100.0)
                subtotal_final = subtotal_modalidad - descuento_modalidad
                
                # Calcular IGV final
                igv_final = subtotal_final * (record.igv / 100.0)
                total_por_modalidad = subtotal_final + igv_final
                
                # Asignar valores por modalidad
                record.subtotal_modalidad = subtotal_modalidad
                record.descuento_modalidad = descuento_modalidad
                record.descuento_total = descuento_mensual * frecuencia + descuento_modalidad
                record.subtotal_final = subtotal_final
                record.igv_final = igv_final
                record.total_por_modalidad = total_por_modalidad
                
                # Total anual para referencia
                record.total_anual = total_mensual * 12
            else:
                # Si no hay modalidad, usar valores mensuales
                record.subtotal_modalidad = subtotal_con_descuento_mensual
                record.descuento_modalidad = 0
                record.descuento_total = descuento_mensual
                record.subtotal_final = subtotal_con_descuento_mensual
                record.igv_final = igv_mensual
                record.total_por_modalidad = total_mensual
                record.total_anual = total_mensual * 12
    
    # Campos de validez
    validez_dias = fields.Integer('Validez de la Cotización (días)', default=30)
    fecha_vencimiento = fields.Date('Fecha de Vencimiento', compute='_compute_fecha_vencimiento', store=True)
    
    @api.depends('fecha_cotizacion', 'validez_dias')
    def _compute_fecha_vencimiento(self):
        for record in self:
            if record.fecha_cotizacion and record.validez_dias:
                record.fecha_vencimiento = record.fecha_cotizacion + relativedelta(days=record.validez_dias)
            else:
                record.fecha_vencimiento = False
    
    # Observaciones
    observaciones = fields.Html('Observaciones y Condiciones')
    
    # Métodos de acción
    def action_enviar_cotizacion(self):
        """Envía la cotización por email/WhatsApp"""
        self.estado = 'enviado'
        # Aquí irían las integraciones de envío
        return True
    
    def action_aprobar_cotizacion(self):
        """Aprueba la cotización"""
        self.estado = 'aprobado'
        return True
    
    def action_convertir_contratos(self):
        """Convierte cada línea de equipo en un contrato individual"""
        contratos_creados = []
        
        for linea in self.linea_equipos_ids:
            # Crear un registro en copier.company por cada equipo
            contrato = self.env['copier.company'].create({
                'name': linea.equipo_id.id,
                'cliente_id': self.cliente_id.id,
                'contacto': self.contacto,
                'celular': self.telefono,
                'correo': self.email,
                'ubicacion': self.direccion,
                'sede': self.sede,
                'tipo': linea.tipo_equipo,
                'volumen_mensual_bn': linea.volumen_mensual_bn,
                'volumen_mensual_color': linea.volumen_mensual_color,
                'costo_copia_bn': linea.precio_bn,
                'costo_copia_color': linea.precio_color,
                'fecha_inicio_alquiler': self.fecha_inicio_propuesta,
                'duracion_alquiler_id': self.duracion_contrato_id.id,
                'descuento': self.descuento_general,
                'igv': self.igv,
                # Referencia a la cotización original
                'observaciones_contrato': f'Generado desde cotización {self.name} - Línea {linea.sequence}'
            })
            contratos_creados.append(contrato.id)
        
        self.estado = 'convertido'
        
        # Retornar vista de los contratos creados
        return {
            'name': 'Contratos Generados',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.company',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', contratos_creados)],
            'context': {'create': False}
        }


class CopierQuotationLine(models.Model):
    """Líneas de equipos en la cotización"""
    _name = 'copier.quotation.line'
    _description = 'Línea de Equipo en Cotización'


    quotation_id = fields.Many2one('copier.quotation', string='Cotización', required=True, ondelete='cascade')
    sequence = fields.Integer('Secuencia', default=10)
    
    # Información del equipo
    equipo_id = fields.Many2one('modelos.maquinas', string='Modelo de Equipo', required=True)
    marca_id = fields.Many2one(related='equipo_id.marca_id', string='Marca', readonly=True)
    imagen_equipo = fields.Binary(related='equipo_id.imagen', string='Imagen', readonly=True)
    especificaciones = fields.Html(related='equipo_id.especificaciones', string='Especificaciones', readonly=True)
    
    # Configuración del equipo
    tipo_equipo = fields.Selection([
        ('monocroma', 'Blanco y Negro'),
        ('color', 'Color')
    ], string='Tipo', required=True, default='monocroma')
    
    formato = fields.Selection([
        ('a4', 'A4'),
        ('a3', 'A3')
    ], string='Formato', default='a4')
    
    cantidad = fields.Integer('Cantidad de Equipos', default=1, required=True)
    
    # Volúmenes mensuales
    volumen_mensual_bn = fields.Integer('Volumen Mensual B/N')
    volumen_mensual_color = fields.Integer('Volumen Mensual Color')
    
    # Precios unitarios
    precio_bn = fields.Float('Precio por Copia B/N', digits=(16, 4), default=0.04)
    precio_color = fields.Float('Precio por Copia Color', digits=(16, 4), default=0.20)
    
    # Cálculos por línea
    subtotal_bn = fields.Monetary('Subtotal B/N', compute='_compute_subtotales', 
                                 store=True, currency_field='currency_id')
    subtotal_color = fields.Monetary('Subtotal Color', compute='_compute_subtotales', 
                                    store=True, currency_field='currency_id')
    subtotal_linea = fields.Monetary('Subtotal Línea', compute='_compute_subtotales', 
                                    store=True, currency_field='currency_id')
    
    currency_id = fields.Many2one(related='quotation_id.currency_id', string='Moneda', readonly=True)
    
    @api.depends('cantidad', 'volumen_mensual_bn', 'volumen_mensual_color', 'precio_bn', 'precio_color')
    def _compute_subtotales(self):
        for line in self:
            subtotal_bn = line.cantidad * line.volumen_mensual_bn * line.precio_bn
            subtotal_color = line.cantidad * line.volumen_mensual_color * line.precio_color
            
            line.subtotal_bn = subtotal_bn
            line.subtotal_color = subtotal_color
            line.subtotal_linea = subtotal_bn + subtotal_color
    
    # Observaciones específicas de la línea
    observaciones = fields.Text('Observaciones del Equipo')
    
    @api.onchange('tipo_equipo')
    def _onchange_tipo_equipo(self):
        if self.tipo_equipo == 'monocroma':
            self.volumen_mensual_color = 0
    
    @api.onchange('equipo_id')
    def _onchange_equipo_id(self):
        """Al cambiar el equipo, sugerir precios por defecto"""
        if self.equipo_id:
            # Aquí puedes agregar lógica para precios sugeridos basados en el modelo
            pass


class CopierPaymentMode(models.Model):
    """Modalidades de pago disponibles"""
    _name = 'copier.payment.mode'
    _description = 'Modalidades de Pago para Alquiler'
    

    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    
    # Configuración de frecuencia
    frecuencia_meses = fields.Integer('Frecuencia en Meses', required=True, 
                                     help='Cada cuántos meses se realizará el pago')
    
    # Descuento por modalidad
    descuento_porcentaje = fields.Float('Descuento (%)', default=0.0,
                                       help='Descuento adicional por elegir esta modalidad')
    
    # Estado
    activo = fields.Boolean('Activo', default=True)
    
    _sql_constraints = [
        ('frecuencia_positiva', 'CHECK(frecuencia_meses > 0)', 
         'La frecuencia debe ser mayor a 0'),
        ('descuento_valido', 'CHECK(descuento_porcentaje >= 0 AND descuento_porcentaje <= 100)', 
         'El descuento debe estar entre 0% y 100%')
    ]


# Extensión del modelo original para mantener compatibilidad
class CopierCompany(models.Model):
    _inherit = 'copier.company'
    
    # Referencia a la cotización original (opcional)
    cotizacion_origen_id = fields.Many2one('copier.quotation', string='Cotización Origen', 
                                          readonly=True, help='Cotización desde la cual se generó este contrato')
    observaciones_contrato = fields.Text('Observaciones del Contrato')


# Datos maestros por defecto
class CopierPaymentModeData(models.Model):
    """Datos por defecto para modalidades de pago"""
    _name = 'copier.payment.mode'
    _inherit = 'copier.payment.mode'
    
    @api.model
    def _create_default_payment_modes(self):
        """Crear modalidades de pago por defecto si no existen"""
        modes = [
            {
                'name': 'Pago Mensual',
                'descripcion': 'Pago mensual estándar',
                'frecuencia_meses': 1,
                'descuento_porcentaje': 0.0
            },
            {
                'name': 'Pago Trimestral',
                'descripcion': 'Pago cada 3 meses con descuento',
                'frecuencia_meses': 3,
                'descuento_porcentaje': 5.0
            },
            {
                'name': 'Pago Semestral',
                'descripcion': 'Pago cada 6 meses con descuento',
                'frecuencia_meses': 6,
                'descuento_porcentaje': 8.0
            },
            {
                'name': 'Pago Anual',
                'descripcion': 'Pago anual anticipado con máximo descuento',
                'frecuencia_meses': 12,
                'descuento_porcentaje': 15.0
            }
        ]
        
        for mode_data in modes:
            if not self.search([('name', '=', mode_data['name'])]):
                self.create(mode_data)