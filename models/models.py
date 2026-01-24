from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import qrcode
import base64
import io
from dateutil import tz
from datetime import datetime, timedelta
from PIL import Image
from PIL import ImageDraw, ImageFont
import textwrap
import os
import re
import requests

import logging
_logger = logging.getLogger(__name__)

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Registro y gestión de máquinas multifuncionales en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('modelos.maquinas', string='Máquina', tracking=True)
    secuencia = fields.Char('Cotización N°', default='New', copy=False, required=True, readonly=True)
    
    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('secuencia') or vals.get('secuencia') in ('New', '/'):
                vals['secuencia'] = self.env['ir.sequence'].next_by_code('copier.company') or '/'

        records = super(CopierCompany, self).create(vals_list)

        # recalcular después de crear
        for rec in records:
            extra_vals = rec._get_costos_unitarios_vals()
            if extra_vals:
                rec.with_context(skip_recalc_costos=True).write(extra_vals)

        return records


    def write(self, vals):
        # Si venimos de la escritura interna para actualizar costos, no recalcular otra vez
        if self.env.context.get('skip_recalc_costos'):
            return super(CopierCompany, self).write(vals)

        res = super(CopierCompany, self).write(vals)

        # Después de guardar, recalculamos y escribimos SOLO los costos
        for rec in self:
            extra_vals = rec._get_costos_unitarios_vals()
            if extra_vals:
                rec.with_context(skip_recalc_costos=True).write(extra_vals)

        return res

    

    imagen_id = fields.Binary(related='name.imagen',string="Imagen de la Máquina", attachment=True)


    fecha_formateada = fields.Char('Fecha', compute='_compute_fecha_formateada', store=True)

    @api.depends('create_date')
    def _compute_fecha_formateada(self):
        meses = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        lima_tz = tz.gettz('America/Lima')
        
        for record in self:
            if record.create_date:
                fecha_lima = record.create_date.astimezone(lima_tz)
                record.fecha_formateada = f"Lima {fecha_lima.day} de {meses[fecha_lima.month]} {fecha_lima.year}"

    def enviar_correo_propuesta(self):
        template = self.env.ref('copier_company.email_template_propuesta_alquiler')
        if template:
            template.send_mail(self.id, force_send=True)
            estado_enviado = self.env.ref('copier_company.estado_enviado')
            self.write({'estado_maquina_id': estado_enviado.id})
    
    especificaciones_id = fields.Html(related='name.especificaciones', string='Especificaciones')
    serie_id = fields.Char(string='Serie', tracking=True)
    marca_id = fields.Many2one('marcas.maquinas', string='Marca', related='name.marca_id')
    es_color = fields.Boolean(string='Es impresora color', default=False, tracking=True)
    tipo = fields.Selection([
        ('monocroma', 'Blanco y negro'),
        ('color', 'Color')
    ], string='Tipo de impresora', default='monocroma', tracking=True)
    
    # Campos del cliente
    cliente_id = fields.Many2one('res.partner', string='Cliente', tracking=True)
    tipo_identificacion = fields.Many2one(related='cliente_id.l10n_latam_identification_type_id', string="Tipo de identificación", readonly=False)
    identificacion = fields.Char(related='cliente_id.vat', string="Número de identificación", readonly=False)
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Teléfono')
    correo = fields.Char(string='Correo')
    
    # Campos de ubicación
    ubicacion = fields.Char(string='Ubicación', tracking=True)
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    
    # Configuración técnica
    formato = fields.Selection([
        ('a4', 'A4'),
        ('a3', 'A3')
    ], string='Formato', default='a4', tracking=True)
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado_maquina_id = fields.Many2one('copier.estados', string="Estado de la Máquina",
                                       default=lambda self: self.env.ref('copier_company.estado_disponible').id,
                                       tracking=True)
    tipo_calculo = fields.Selection([
        ('auto', 'Cálculo Automático'),
        ('manual_sin_igv_bn', 'Monto Mensual B/N sin IGV'),
        ('manual_con_igv_bn', 'Monto Mensual B/N con IGV'),
        ('manual_sin_igv_color', 'Monto Mensual Color sin IGV'),
        ('manual_con_igv_color', 'Monto Mensual Color con IGV'),
        ('manual_sin_igv_total', 'Monto Mensual Total sin IGV'),
        ('manual_con_igv_total', 'Monto Mensual Total con IGV'),
    ], string='Tipo de Cálculo', default='auto', tracking=True)
    monto_mensual_bn = fields.Monetary(
        string="Monto Mensual B/N",
        currency_field='currency_id'
    )
    
    monto_mensual_color = fields.Monetary(
        string="Monto Mensual Color",
        currency_field='currency_id'
    )
    monto_mensual_total = fields.Monetary(
        string="Monto Mensual Total",
        currency_field='currency_id'
    )

    subtotal_sin_igv = fields.Monetary(
        string="Subtotal (Sin IGV)",
        compute='_compute_renta_mensual',
        currency_field='currency_id',
        store=True
    )

    monto_igv = fields.Monetary(
        string="Monto IGV",
        compute='_compute_renta_mensual',
        currency_field='currency_id',
        store=True
    )

    monto_mensual_ingresado = fields.Monetary(
        string="Monto Mensual Ingresado",
        currency_field='currency_id'
    )
    

    def _get_costos_unitarios_vals(self):
        """Devuelve los valores calculados para costo_copia_bn y costo_copia_color."""
        self.ensure_one()
        vals = {}

        rec = self

        # No hacemos nada si es cálculo automático
        if rec.tipo_calculo == 'auto':
            return vals

        # Validaciones de volumen
        if rec.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn'] and rec.volumen_mensual_bn <= 0:
            return vals

        if rec.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color'] and rec.volumen_mensual_color <= 0:
            return vals

        if rec.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
            if (rec.volumen_mensual_bn + rec.volumen_mensual_color) <= 0:
                return vals

        # --- Cálculo para monto mensual B/N ---
        if rec.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn']:
            monto_sin_igv = rec.monto_mensual_bn
            if rec.tipo_calculo == 'manual_con_igv_bn':
                monto_sin_igv = rec.monto_mensual_bn / (1 + (rec.igv / 100.0))

            if rec.volumen_mensual_bn > 0:
                vals['costo_copia_bn'] = monto_sin_igv / rec.volumen_mensual_bn

        # --- Cálculo para monto mensual Color ---
        elif rec.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color']:
            monto_sin_igv = rec.monto_mensual_color
            if rec.tipo_calculo == 'manual_con_igv_color':
                monto_sin_igv = rec.monto_mensual_color / (1 + (rec.igv / 100.0))

            if rec.volumen_mensual_color > 0:
                vals['costo_copia_color'] = monto_sin_igv / rec.volumen_mensual_color

        # --- Cálculo para monto mensual Total (distribución proporcional) ---
        elif rec.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
            monto_sin_igv = rec.monto_mensual_total
            if rec.tipo_calculo == 'manual_con_igv_total':
                monto_sin_igv = rec.monto_mensual_total / (1 + (rec.igv / 100.0))

            # Solo hay volumen B/N
            if rec.volumen_mensual_bn > 0 and rec.volumen_mensual_color == 0:
                vals['costo_copia_bn'] = monto_sin_igv / rec.volumen_mensual_bn
                vals['costo_copia_color'] = 0.0

            # Solo hay volumen Color
            elif rec.volumen_mensual_color > 0 and rec.volumen_mensual_bn == 0:
                vals['costo_copia_color'] = monto_sin_igv / rec.volumen_mensual_color
                vals['costo_copia_bn'] = 0.0

            # Hay ambos tipos, distribuir proporcionalmente manteniendo relación
            elif rec.volumen_mensual_bn > 0 and rec.volumen_mensual_color > 0:
                ratio_precio = 4  # color ≈ 4 veces B/N
                denominator = rec.volumen_mensual_bn + (ratio_precio * rec.volumen_mensual_color)

                if denominator > 0:
                    precio_bn = monto_sin_igv / denominator
                    precio_color = precio_bn * ratio_precio
                    vals['costo_copia_bn'] = precio_bn
                    vals['costo_copia_color'] = precio_color

        return vals


    @api.onchange('tipo_calculo',
                'monto_mensual_bn',
                'monto_mensual_color',
                'monto_mensual_total',
                'volumen_mensual_bn',
                'volumen_mensual_color',
                'igv')
    def _onchange_montos_mensuales(self):
        """
        Actualiza los costos unitarios cuando se cambian los montos mensuales
        o los volúmenes. Solo actúa en memoria (no escribe en BD).
        """
        for rec in self:
            vals = rec._get_costos_unitarios_vals()
            for field_name, value in vals.items():
                setattr(rec, field_name, value)

        # ==========================
    # HELPERS PARA EL REPORTE
    # ==========================
    def action_crear_servicio_tecnico(self):
        """Abrir formulario de nuevo servicio con máquina precargada"""
        self.ensure_one()

        return {
            'name': 'Nueva Solicitud de Servicio Técnico',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.service.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                # precargar datos
                'default_maquina_id': self.id,
                'default_company_id': self.env.company.id,
                'default_origen_solicitud': 'interno',
                'default_prioridad': '1',

                # precargar contacto desde la máquina
                'default_contacto': self.contacto or self.cliente_id.name,
                'default_correo': self.correo or self.cliente_id.email,
                'default_telefono_contacto': self.celular or self.cliente_id.phone,
            }
        }
    def action_print_stickers(self):
        ids = ",".join(str(x.id) for x in self)

        return {
            'type': 'ir.actions.act_url',
            'url': '/stickers/print?ids=%s' % ids,
            'target': 'new',
        }

    def has_volumen_mensual_bn(self):
        """Indica si hay volumen mensual B/N configurado."""
        self.ensure_one()
        return (self.volumen_mensual_bn or 0) > 0

    def has_volumen_mensual_color(self):
        """Indica si hay volumen mensual Color configurado."""
        self.ensure_one()
        return (self.volumen_mensual_color or 0) > 0

    def get_label_costo_bn(self):
        """
        Devuelve el texto del costo B/N listo para el reporte,
        respetando si incluye IGV o no.
        Ejemplo:
            - 'S/ 0.040 + IGV'
            - 'S/ 0.040 (incluye IGV)'
        """
        self.ensure_one()
        simbolo = self.currency_id.symbol or 'S/'
        monto_str = f"{self.costo_copia_bn:.3f}"  # 3 decimales B/N

        if self.precio_bn_incluye_igv:
            return f"{simbolo} {monto_str} (incluye IGV)"
        else:
            return f"{simbolo} {monto_str} + IGV"

    def get_label_costo_color(self):
        """
        Devuelve el texto del costo Color listo para el reporte,
        respetando si incluye IGV o no.
        Ejemplo:
            - 'S/ 0.20 + IGV'
            - 'S/ 0.20 (incluye IGV)'
        """
        self.ensure_one()
        simbolo = self.currency_id.symbol or 'S/'
        monto_str = f"{self.costo_copia_color:.2f}"  # 2 decimales Color

        if self.precio_color_incluye_igv:
            return f"{simbolo} {monto_str} (incluye IGV)"
        else:
            return f"{simbolo} {monto_str} + IGV"

    def format_phone_number(self, phone):
        if not phone:
            return False
        # Eliminar espacios en blanco y el carácter '+'
        phone = phone.strip().replace(' ', '').replace('+', '')
        # Eliminar cualquier otro carácter que no sea número
        phone = re.sub(r'[^0-9]', '', phone)
        
        # Si el número no empieza con '51' y tiene 9 dígitos, agregar '51'
        if not phone.startswith('51') and len(phone) == 9:
            phone = f'51{phone}'
        
        return phone

    def get_formatted_phones(self):
        """Obtiene y formatea los números de teléfono del cliente"""
        if not self.cliente_id.mobile:
            return False
            
        # Dividir números por punto y coma y formatear cada uno
        phones = self.cliente_id.mobile.split(';')
        formatted_phones = []
        
        for phone in phones:
            formatted = self.format_phone_number(phone)
            if formatted:
                formatted_phones.append(formatted)
                
        return formatted_phones

    def send_whatsapp_report(self):
        """Abre wizard para enviar cotización por WhatsApp"""
        self.ensure_one()
        
        # Validar que tenga cliente
        if not self.cliente_id:
            raise UserError('Debe asignar un cliente antes de enviar por WhatsApp.')
        
        # Abrir wizard
        return {
            'name': 'Enviar Cotización por WhatsApp',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.send.quotation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_copier_company_ids': [(6, 0, self.ids)],
            }
        }
    def action_send_whatsapp_multi(self):
        """Acción para enviar múltiples cotizaciones por WhatsApp (desde tree view)"""
        if not self:
            raise UserError('Debe seleccionar al menos una cotización.')
        
        # Validar que todas tengan cliente
        sin_cliente = self.filtered(lambda c: not c.cliente_id)
        if sin_cliente:
            raise UserError(
                f'Las siguientes cotizaciones no tienen cliente asignado:\n' +
                '\n'.join(sin_cliente.mapped('secuencia'))
            )
        
        return {
            'name': 'Enviar Cotizaciones por WhatsApp',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.send.quotation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_copier_company_ids': [(6, 0, self.ids)],
            }
        }
    # Campos de alquiler
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler", tracking=True)
    duracion_alquiler_id = fields.Many2one('copier.duracion', string="Duración del Alquiler",
                                          default=lambda self: self.env.ref('copier_company.duracion_1_año').id,
                                          tracking=True)
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)
    
    # Campos financieros
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                 default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1))
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", 
                                      currency_field='currency_id', 
                                      default=0.20)
    costo_copia_bn = fields.Float(string="Costo por Copia (B/N)", 
                             digits=(16,3),  # 16 dígitos en total, 3 decimales
                             default=0.04)
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")
    renta_mensual_color = fields.Monetary(string="Renta Mensual (Color)", 
                                        compute='_compute_renta_mensual',
                                        currency_field='currency_id',
                                        store=True)
    renta_mensual_bn = fields.Monetary(string="Renta Mensual (B/N)", 
                                     compute='_compute_renta_mensual',
                                     currency_field='currency_id',
                                     store=True)
    total_facturar_mensual = fields.Monetary(string="Total a Facturar Mensual",
                                           compute='_compute_renta_mensual',
                                           currency_field='currency_id',
                                           store=True)
    igv = fields.Float(string='IGV (%)', default=18.0)

    precio_bn_incluye_igv = fields.Boolean(
        'Precio B/N Incluye IGV',
        default=False,
        tracking=True,
        help="Si está marcado, el precio B/N ingresado ya incluye IGV"
    )

    precio_color_incluye_igv = fields.Boolean(
        'Precio Color Incluye IGV',
        default=False,
        tracking=True,
        help="Si está marcado, el precio Color ingresado ya incluye IGV"
    )
    descuento = fields.Float(string='Descuento (%)', default=0.0)
    dia_facturacion = fields.Integer(string='Día de Facturación', default=30)
    # Para preparar automatización futura
    facturacion_automatica = fields.Boolean(
        'Facturación Automática',
        default=False,
        help="Si está marcado, las lecturas se facturarán automáticamente"
    )
    # Campos técnicos
    detalles = fields.Text(string='Detalles técnicos')
    qr_code = fields.Binary(string='Código QR', readonly=True, attachment=True)
    
    @api.onchange('tipo')
    def _onchange_tipo(self):
        if self.tipo == 'monocroma':
            self.es_color = False
            self.volumen_mensual_color = 0
        else:
            self.es_color = True

    @api.onchange('identificacion')
    def _onchange_identificacion(self):
        if not self.identificacion:
            return
            
        partner = self.env['res.partner'].search([('vat', '=', self.identificacion)], limit=1)
        if partner:
            self.cliente_id = partner.id
            self.tipo_identificacion = partner.l10n_latam_identification_type_id.id
            return
            
        new_partner = self.env['res.partner'].create({
            'vat': self.identificacion,
            'name': self.identificacion,
            'l10n_latam_identification_type_id': self.tipo_identificacion.id
        })
        new_partner._doc_number_change()
        self.cliente_id = new_partner.id
        self.tipo_identificacion = new_partner.l10n_latam_identification_type_id.id
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Términos de pago',
        help='Términos de pago para esta transacción'
    )
    @api.depends('volumen_mensual_color', 'volumen_mensual_bn', 'costo_copia_color', 
             'costo_copia_bn', 'igv', 'descuento', 'tipo_calculo', 
             'monto_mensual_bn', 'monto_mensual_color', 'monto_mensual_total',
             'precio_bn_incluye_igv', 'precio_color_incluye_igv')  # AGREGAR DEPENDENCIAS
    def _compute_renta_mensual(self):
        for record in self:
            # Caso 1: Cálculo automático por costo unitario
            if record.tipo_calculo == 'auto':
                # Calcular rentas según si el precio incluye o no IGV
                if record.precio_bn_incluye_igv:
                    # El precio YA incluye IGV, calcular subtotal sin IGV
                    renta_bn_con_igv = record.volumen_mensual_bn * record.costo_copia_bn
                    renta_bn = renta_bn_con_igv / (1 + (record.igv / 100))
                else:
                    # El precio NO incluye IGV
                    renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
                
                if record.precio_color_incluye_igv:
                    # El precio YA incluye IGV, calcular subtotal sin IGV
                    renta_color_con_igv = record.volumen_mensual_color * record.costo_copia_color
                    renta_color = renta_color_con_igv / (1 + (record.igv / 100))
                else:
                    # El precio NO incluye IGV
                    renta_color = record.volumen_mensual_color * record.costo_copia_color
                
            # Caso 2: Cálculo con montos fijos para B/N
            elif record.tipo_calculo in ['manual_sin_igv_bn', 'manual_con_igv_bn']:
                if record.tipo_calculo == 'manual_sin_igv_bn':
                    renta_bn = record.monto_mensual_bn
                else:  # manual_con_igv_bn
                    renta_bn = record.monto_mensual_bn / (1 + (record.igv / 100))
                
                # Color sigue la lógica del checkbox
                if record.precio_color_incluye_igv:
                    renta_color_con_igv = record.volumen_mensual_color * record.costo_copia_color
                    renta_color = renta_color_con_igv / (1 + (record.igv / 100))
                else:
                    renta_color = record.volumen_mensual_color * record.costo_copia_color
            
            # Caso 3: Cálculo con montos fijos para Color
            elif record.tipo_calculo in ['manual_sin_igv_color', 'manual_con_igv_color']:
                if record.tipo_calculo == 'manual_sin_igv_color':
                    renta_color = record.monto_mensual_color
                else:  # manual_con_igv_color
                    renta_color = record.monto_mensual_color / (1 + (record.igv / 100))
                
                # B/N sigue la lógica del checkbox
                if record.precio_bn_incluye_igv:
                    renta_bn_con_igv = record.volumen_mensual_bn * record.costo_copia_bn
                    renta_bn = renta_bn_con_igv / (1 + (record.igv / 100))
                else:
                    renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
            
            # Caso 4: Cálculo con montos fijos para el total
            elif record.tipo_calculo in ['manual_sin_igv_total', 'manual_con_igv_total']:
                if record.tipo_calculo == 'manual_sin_igv_total':
                    monto_total = record.monto_mensual_total
                else:  # manual_con_igv_total
                    monto_total = record.monto_mensual_total / (1 + (record.igv / 100))
                
                volumen_total = record.volumen_mensual_bn + record.volumen_mensual_color
                
                if volumen_total > 0:
                    # Calcular costos base según checkbox
                    if record.precio_bn_incluye_igv:
                        costo_bn_base = (record.volumen_mensual_bn * record.costo_copia_bn) / (1 + (record.igv / 100))
                    else:
                        costo_bn_base = record.volumen_mensual_bn * record.costo_copia_bn
                    
                    if record.precio_color_incluye_igv:
                        costo_color_base = (record.volumen_mensual_color * record.costo_copia_color) / (1 + (record.igv / 100))
                    else:
                        costo_color_base = record.volumen_mensual_color * record.costo_copia_color
                    
                    costo_total_base = costo_bn_base + costo_color_base
                    
                    if costo_total_base > 0:
                        factor = monto_total / costo_total_base
                        renta_bn = costo_bn_base * factor
                        renta_color = costo_color_base * factor
                    else:
                        renta_bn = monto_total
                        renta_color = 0
                else:
                    renta_bn = monto_total
                    renta_color = 0
            
            # Común para todos: cálculo de totales
            subtotal = renta_color + renta_bn
            
            # Aplicar descuento
            descuento_valor = subtotal * (record.descuento / 100.0)
            subtotal_con_descuento = subtotal - descuento_valor
            
            # Calcular IGV
            igv_valor = subtotal_con_descuento * (record.igv / 100.0)
            
            # Asignar valores
            record.renta_mensual_color = renta_color
            record.renta_mensual_bn = renta_bn
            record.subtotal_sin_igv = subtotal_con_descuento
            record.monto_igv = igv_valor
            record.total_facturar_mensual = subtotal_con_descuento + igv_valor

    
    @api.depends('fecha_inicio_alquiler', 'duracion_alquiler_id')
    def _calcular_fecha_fin(self):
        for record in self:
            if not (record.fecha_inicio_alquiler and record.duracion_alquiler_id):
                continue
                
            start_date = fields.Date.from_string(record.fecha_inicio_alquiler)
            duracion = record.duracion_alquiler_id.name
            
            if duracion == '6 Meses':
                record.fecha_fin_alquiler = start_date + relativedelta(months=+6)
            elif duracion == '1 Año':
                record.fecha_fin_alquiler = start_date + relativedelta(years=+1)
            elif duracion == '2 Años':
                record.fecha_fin_alquiler = start_date + relativedelta(years=+2)

   
    qr_code_filename = fields.Char(
            string="Nombre archivo QR",
            compute='_compute_qr_filename'
        )   

    

    

    
   

    def _get_company_logo_base64(self):
        """Obtiene el logo de la compañía en base64"""
        try:
            company = self.env.user.company_id
            if company.logo:
                return company.logo.decode('utf-8')
            return None
        except Exception as e:
            _logger.error(f"Error obteniendo logo: {str(e)}")
            return None


   

    def generar_sticker_corporativo(self, layout='horizontal'):
        """Abre el sticker en nueva ventana"""
        self.ensure_one()
        url = f'/sticker/generate/{self.id}?layout={layout}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
        

    def action_ver_usuarios_internos(self):
        """Abrir usuarios internos asociados a esta máquina"""
        self.ensure_one()

        return {
            'name': 'Usuarios Internos de la Máquina',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.machine.user',
            'view_mode': 'list,form',
            'domain': [('maquina_id', '=', self.id)],
            'context': {
                # Para que al crear un nuevo usuario interno,
                # ya venga cargada esta máquina automáticamente
                'default_maquina_id': self.id,
            },
            'target': 'current',
        }


    user_count = fields.Integer(
        string='Usuarios Internos',
        compute='_compute_user_count'
    )

    def _compute_user_count(self):
        for rec in self:
            rec.user_count = self.env['copier.machine.user'].search_count([
                ('maquina_id', '=', rec.id)
            ])



    @api.depends('secuencia')
    def _compute_qr_filename(self):
        for record in self:
            record.qr_code_filename = f'qr_code_{record.secuencia}.png'
            
            
    def generar_qr_code(self):
        """
        Genera y asigna un QR con el logo. Orden de búsqueda del logo:
        1) logo de la compañía (self.env.company.logo o image_1920)
        2) ir.attachment con 'logo' en el nombre (busca globalmente)
        3) archivo en disk: ../static/src/img/logo.png (ruta relativa al módulo)
        Si no se encuentra logo, lanza UserError.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''

        # ---------------------------------
        # 1) Intentar obtener logo desde la compañía
        # ---------------------------------
        logo = None
        try:
            company = self.env.company
            logo_b64 = company.logo or getattr(company, 'image_1920', None)
            if logo_b64:
                # logo_b64 puede ser str o bytes
                logo_bytes = base64.b64decode(logo_b64 if isinstance(logo_b64, str) else logo_b64.decode('utf-8'))
                logo = Image.open(io.BytesIO(logo_bytes))
        except Exception:
            logo = None

        # ---------------------------------
        # 2) Si no hay logo, intentar ir.attachment (opcional)
        # ---------------------------------
        if logo is None:
            try:
                att = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', False),
                    ('name', 'ilike', 'logo')
                ], limit=1)
                if att and att.datas:
                    att_bytes = base64.b64decode(att.datas if isinstance(att.datas, str) else att.datas.decode('utf-8'))
                    logo = Image.open(io.BytesIO(att_bytes))
            except Exception:
                logo = None

        # ---------------------------------
        # 3) Fallback a archivo en disco (ruta relativa sin get_module_resource)
        # ---------------------------------
        if logo is None:
            module_dir = os.path.dirname(__file__)              # .../copier_company/models
            module_root = os.path.normpath(os.path.join(module_dir, '..'))  # .../copier_company
            logo_path = os.path.join(module_root, 'static', 'src', 'img', 'logo.png')
            if os.path.isfile(logo_path):
                try:
                    logo = Image.open(logo_path)
                except Exception:
                    logo = None

        # Si aún no hay logo -> avisar en UI
        if logo is None:
            raise ValidationError("No se encontró el logo. Coloca el logo en la configuración de la compañía o como ir.attachment o en static/src/img/logo.png del módulo.")

        # ---------------------------------
        # Preparar logo (resample compatible con distintas versiones de Pillow)
        # ---------------------------------
        # Determinar filtro de remuestreo (compatibilidad Pillow)
        try:
            resampling_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resampling_filter = getattr(Image, 'LANCZOS', Image.ANTIALIAS)

        # Redimensionar logo a un ancho objetivo (ajusta si quieres otro tamaño)
        target_logo_width = 100
        # proteger contra logos inválidos
        if logo.size[0] == 0:
            raise ValidationError("El logo tiene ancho 0. Reemplázalo por una imagen válida.")
        logo_height = int((float(logo.size[1]) * float(target_logo_width / float(logo.size[0]))))
        logo_size = (target_logo_width, logo_height)
        logo = logo.resize(logo_size, resampling_filter)

        # Asegurar canal alfa para usar como máscara al pegar
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')

        # ---------------------------------
        # Generar QR para cada registro del recordset
        # ---------------------------------
        for record in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(f"{base_url}/public/equipment_menu?copier_company_id={record.id}")
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            qr_img = qr_img.convert('RGBA')

            # Centrar logo sobre el QR
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo)

            # Reducir tamaño final (opcional). Ajusta el //2 si quieres otro tamaño
            new_size = (qr_img.size[0] // 2, qr_img.size[1] // 2)
            qr_img = qr_img.resize(new_size, resampling_filter)

            # Guardar en buffer y asignar al campo Binary (base64 string)
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            img_bytes = buffer.getvalue()
            record.qr_code = base64.b64encode(img_bytes).decode('utf-8')

    def action_print_report(self):
        return self.env.ref('copier_company.action_report_report_cotizacion_alquiler').report_action(self)

    # Campo compute para el contador
    counter_count = fields.Integer(
        string='Lecturas',
        compute='_compute_counter_count'
    )
    
    def _compute_counter_count(self):
        for record in self:
            record.counter_count = self.env['copier.counter'].search_count([
                ('maquina_id', '=', record.id)
            ])
    
    # Acción para el botón
    def action_view_counters(self):
        self.ensure_one()
        return {
            'name': 'Lecturas',
            'type': 'ir.actions.act_window',
            'res_model': 'copier.counter',
            'view_mode': 'list,form',
            'domain': [('maquina_id', '=', self.id)],
            'context': {'default_maquina_id': self.id},
        }
    # Nuevos campos para manejar renovaciones
    estado_renovacion = fields.Selection([
        ('vigente', 'Contrato Vigente'),
        ('por_vencer', 'Por Vencer'),
        ('renovado', 'Renovado'),
        ('finalizado', 'Finalizado')
    ], string='Estado de Renovación', default='vigente', tracking=True)
    
    dias_notificacion = fields.Integer(
        string='Días para Notificación', 
        default=30,
        help='Días antes del vencimiento para comenzar las notificaciones'
    )
    
    responsable_id = fields.Many2one(
        'res.users', 
        string='Responsable de Renovación',
        tracking=True
    )
    historial_renovaciones = fields.One2many(
        'copier.renewal.history',
        'copier_id',
        string='Historial de Renovaciones'
    )

    @api.model
    def _cron_check_contract_expiration(self):
        """
        Cron job que se ejecuta diariamente para verificar contratos próximos a vencer
        y notificar al equipo interno
        """
        _logger.info("Iniciando verificación de contratos próximos a vencer")
        
        hoy = fields.Date.today()
        # Buscar contratos que no estén finalizados
        contratos = self.search([
            ('estado_renovacion', 'in', ['vigente', 'por_vencer']),
            ('fecha_fin_alquiler', '!=', False)
        ])
        
        _logger.info(f"Encontrados {len(contratos)} contratos para revisar")
        
        for contrato in contratos:
            try:
                dias_restantes = (contrato.fecha_fin_alquiler - hoy).days
                _logger.info(f"Contrato {contrato.name.name} - Días restantes: {dias_restantes}")
                
                # Si está dentro del período de notificación y aún no está marcado como por vencer
                if 0 < dias_restantes <= contrato.dias_notificacion and contrato.estado_renovacion != 'por_vencer':
                    _logger.info(f"Marcando contrato {contrato.name.name} como por vencer")
                    contrato.estado_renovacion = 'por_vencer'
                    
                    # Crear nota en el chatter
                    contrato.message_post(
                        body=f"""
                        🔔 ALERTA DE VENCIMIENTO DE CONTRATO
                        
                        El contrato está próximo a vencer:
                        • Cliente: {contrato.cliente_id.name}
                        • Máquina: {contrato.name.name}
                        • Serie: {contrato.serie_id}
                        • Días restantes: {dias_restantes}
                        • Fecha de vencimiento: {contrato.fecha_fin_alquiler}
                        
                        Por favor, gestionar la renovación del contrato.
                        """,
                        message_type='notification'
                    )
                    
                    # Crear actividad para el responsable o equipo de ventas
                    if contrato.responsable_id:
                        contrato._crear_actividad_renovacion(contrato.responsable_id)
                    else:
                        grupo_ventas = self.env.ref('sales_team.group_sale_salesman', False)
                        if grupo_ventas and grupo_ventas.users:
                            for usuario in grupo_ventas.users:
                                contrato._crear_actividad_renovacion(usuario)
                
                # Si el contrato ya venció
                elif dias_restantes <= 0 and contrato.estado_renovacion != 'finalizado':
                    _logger.info(f"Marcando contrato {contrato.name.name} como finalizado")
                    contrato.estado_renovacion = 'finalizado'
                    contrato.message_post(
                        body="⚠️ CONTRATO VENCIDO\nEl contrato ha llegado a su fecha de finalización.",
                        message_type='notification'
                    )
                    
            except Exception as e:
                _logger.error(f"Error procesando contrato {contrato.name.name}: {str(e)}")
                
        _logger.info("Finalizada la verificación de contratos")
    def _crear_actividad_renovacion(self, usuario):
        """Crea una actividad para la renovación del contrato"""
        try:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'Renovación de Contrato - {self.name.name}',
                'note': f'''
                    📅 Contrato próximo a vencer
                    
                    • Cliente: {self.cliente_id.name}
                    • Máquina: {self.name.name}
                    • Serie: {self.serie_id}
                    • Fecha de vencimiento: {self.fecha_fin_alquiler}
                    • Días restantes: {(self.fecha_fin_alquiler - fields.Date.today()).days}
                    
                    Por favor, gestionar la renovación del contrato.
                ''',
                'user_id': usuario.id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('copier.company').id,
                'date_deadline': fields.Date.today() + timedelta(days=5)
            })
            _logger.info(f"Actividad creada para el usuario {usuario.name}")
        except Exception as e:
            _logger.error(f"Error creando actividad: {str(e)}")
    def _crear_nota_vencimiento(self, dias_restantes):
        """Crea una nota en el chatter sobre el vencimiento próximo"""
        self.message_post(
            body=f'''
            🔔 ALERTA DE VENCIMIENTO DE CONTRATO
            
            El contrato está próximo a vencer:
            • Cliente: {self.cliente_id.name}
            • Máquina: {self.name.name}
            • Serie: {self.serie_id}
            • Días restantes: {dias_restantes}
            • Fecha de vencimiento: {self.fecha_fin_alquiler}
            
            Se ha creado una actividad para gestionar la renovación.
            ''',
            message_type='notification'
        )

    def action_renovar_contrato(self):
        """
        Acción para renovar el contrato y registrar en el historial
        """
        self.ensure_one()
        _logger.info(f"Iniciando renovación de contrato para {self.name.name}")
        
        try:
            # Crear registro en el historial de renovaciones
            self.env['copier.renewal.history'].create({
                'copier_id': self.id,
                'fecha_anterior': self.fecha_inicio_alquiler,
                'fecha_fin_anterior': self.fecha_fin_alquiler,
                'duracion_anterior_id': self.duracion_alquiler_id.id,
                'notas': f'Renovación desde {self.fecha_inicio_alquiler} hasta {self.fecha_fin_alquiler}'
            })
            _logger.info("Historial de renovación creado exitosamente")
            
            # Actualizar fechas del contrato
            antigua_fecha_fin = self.fecha_fin_alquiler
            self.fecha_inicio_alquiler = antigua_fecha_fin + relativedelta(days=1)
            self._calcular_fecha_fin()
            
            # Actualizar estado
            self.estado_renovacion = 'renovado'
            
            # Registrar en el chatter
            self.message_post(
                body=f"""
                ✅ CONTRATO RENOVADO
                
                Se ha renovado el contrato:
                • Período anterior: {antigua_fecha_fin}
                • Nuevo período: {self.fecha_inicio_alquiler} - {self.fecha_fin_alquiler}
                • Duración: {self.duracion_alquiler_id.name}
                """,
                message_type='notification'
            )
            
            _logger.info(f"Renovación completada exitosamente para {self.name.name}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': 'El contrato ha sido renovado exitosamente',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error durante la renovación del contrato: {str(e)}")
            raise UserError(f"Error al renovar el contrato: {str(e)}")


    def get_precio_bn_sin_igv(self, precio):
        self.ensure_one()
        if self.precio_bn_incluye_igv:
            return precio / 1.18
        return precio

    def get_precio_color_sin_igv(self, precio):
        self.ensure_one()
        if self.precio_color_incluye_igv:
            return precio / 1.18
        return precio
    # Agregar después de los campos financieros existentes
    producto_facturable_bn_id = fields.Many2one(
        'product.product',
        string='Producto a Facturar B/N',
        help='Producto que se facturará para las copias en blanco y negro'
    )

    producto_facturable_color_id = fields.Many2one(
        'product.product',
        string='Producto a Facturar Color',
        help='Producto que se facturará para las copias a color'
    )

    # Campo computed para mantener compatibilidad (opcional)
    producto_facturable_id = fields.Many2one(
        'product.product',
        string='Producto Principal',
        compute='_compute_producto_principal',
        help='Producto principal (B/N para monocromas, B/N para color)'
    )

    @api.depends('tipo', 'producto_facturable_bn_id', 'producto_facturable_color_id')
    def _compute_producto_principal(self):
        """Determina el producto principal según el tipo de máquina"""
        for record in self:
            if record.tipo == 'monocroma':
                record.producto_facturable_id = record.producto_facturable_bn_id
            else:  # color
                record.producto_facturable_id = record.producto_facturable_bn_id or record.producto_facturable_color_id

   
    @api.onchange('tipo', 'es_color')
    def _onchange_tipo_producto(self):
        """Sugiere productos basados en el tipo de máquina"""
        
        # Limpiar productos primero
        self.producto_facturable_bn_id = False
        self.producto_facturable_color_id = False
        
        if self.tipo == 'monocroma':
            # Para monocromas: solo producto B/N
            producto_mono = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Blanco y Negro'),
                ('name', 'ilike', 'Alquiler%Blanco%Negro')
            ], limit=1)
            if producto_mono:
                self.producto_facturable_bn_id = producto_mono.id
                
        elif self.tipo == 'color':
            # Para color: ambos productos
            
            # Producto B/N (mismo que monocromas)
            producto_bn = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Blanco y Negro'),
                ('name', 'ilike', 'Alquiler%Blanco%Negro')
            ], limit=1)
            if producto_bn:
                self.producto_facturable_bn_id = producto_bn.id
            
            # Producto Color
            producto_color = self.env['product.product'].search([
                '|',
                ('name', '=', 'Alquiler de Máquina Fotocopiadora Color'),
                ('name', 'ilike', 'Alquiler%Color')
            ], limit=1)
            if producto_color:
                self.producto_facturable_color_id = producto_color.id
                
        # Mensaje informativo al usuario
        if self.tipo == 'color' and (not self.producto_facturable_bn_id or not self.producto_facturable_color_id):
            return {
                'warning': {
                    'title': 'Productos no encontrados',
                    'message': 'No se encontraron todos los productos necesarios para máquinas color. '
                            'Asegúrate de tener creados:\n'
                            '- Alquiler de Máquina Fotocopiadora Blanco y Negro\n'
                            '- Alquiler de Máquina Fotocopiadora Color'
                }
            }


class CopierRenewalHistory(models.Model):
    _name = 'copier.renewal.history'
    _description = 'Historial de Renovaciones de Contratos'
 

    copier_id = fields.Many2one('copier.company', string='Máquina', required=True, ondelete='cascade')
    fecha_renovacion = fields.Date(string='Fecha de Renovación', default=fields.Date.today)
    fecha_anterior = fields.Date(string='Fecha Inicio Anterior', required=True)
    fecha_fin_anterior = fields.Date(string='Fecha Fin Anterior', required=True)
    duracion_anterior_id = fields.Many2one('copier.duracion', string='Duración Anterior', required=True)
    notas = fields.Text(string='Notas')

class CotizacionAlquilerReport(models.AbstractModel):
    _name = 'report.copier_company.cotizacion_view'
    _description = 'Reporte de Cotización de Alquiler'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara los valores para el reporte"""
        # Obtener los registros directamente
        docs = self.env['copier.company'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'copier.company',
            'docs': docs,
            'data': data,
            'company': self.env.company,
            # Helper functions
            'format_currency': lambda amount: '{:,.2f}'.format(amount or 0.0),
            'format_number': lambda number: '{:,}'.format(number or 0),
        }