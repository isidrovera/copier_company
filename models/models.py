from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource
import qrcode
import base64
import io
from PIL import Image
import os

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Registro y gestión de máquinas multifuncionales en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('modelos.maquinas', string='Máquina', tracking=True)
    secuencia = fields.Char('Cotización N°', default='New', copy=False, required=True, readonly=True)
    
    @api.model
    def create(self, vals):
        vals['secuencia'] = self.env['ir.sequence'].next_by_code('copier.company') or '/'
        return super(CopierCompany, self).create(vals)
    
    imagen_id = fields.Binary(
    string='Imagen',
    compute='_compute_imagen',
    store=True,
    attachment=True
)

    @api.depends('name', 'name.imagen')
    def _compute_imagen(self):
        for record in self:
            record.imagen_id = record.name.imagen if record.name else False
    def action_clear_image(self):
        self.ensure_one()
        self.imagen_id = False
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
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", 
                                   currency_field='currency_id',
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
    descuento = fields.Float(string='Descuento (%)', default=0.0)
    
    # Campos técnicos
    detalles = fields.Text(string='Detalles técnicos')
    qr_code = fields.Binary(string='Código QR', readonly=True)
    
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

    @api.depends('volumen_mensual_color', 'volumen_mensual_bn', 'costo_copia_color', 
                'costo_copia_bn', 'igv', 'descuento')
    def _compute_renta_mensual(self):
        for record in self:
            renta_color = record.volumen_mensual_color * record.costo_copia_color
            renta_bn = record.volumen_mensual_bn * record.costo_copia_bn
            subtotal = renta_color + renta_bn
            
            descuento = subtotal * (record.descuento / 100.0)
            subtotal_con_descuento = subtotal - descuento
            igv = subtotal_con_descuento * (record.igv / 100.0)
            
            record.renta_mensual_color = renta_color
            record.renta_mensual_bn = renta_bn
            record.total_facturar_mensual = subtotal_con_descuento + igv

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

    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket'].create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            'name': f"Servicio técnico - {self.name.name}",
            'description': f"Máquina: {self.name.name}\nSerie: {self.serie_id}\nUbicación: {self.ubicacion}"
        })
        
        return {
            'name': 'Ticket de Servicio',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def generar_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_path = get_module_resource('copier_company', 'static', 'src', 'img', 'logo.png')
        
        if not os.path.isfile(logo_path):
            raise FileNotFoundError(f"Logo no encontrado: {logo_path}")
            
        logo = Image.open(logo_path)
        logo_size = (100, int((float(logo.size[1]) * float(100/float(logo.size[0])))))
        logo = logo.resize(logo_size, Image.ANTIALIAS)
        
        for record in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr.add_data(f"{base_url}/public/helpdesk_ticket?copier_company_id={record.id}")
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo)
            
            # Reducir tamaño del QR
            qr_img = qr_img.resize((qr_img.size[0] // 2, qr_img.size[1] // 2), Image.ANTIALIAS)
            
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            record.qr_code = base64.b64encode(buffer.getvalue())

    def action_print_report(self):
        return self.env.ref('copier_company.action_report_report_cotizacion_alquiler').report_action(self)