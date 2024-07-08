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
    _description = 'Aqui se registran las maquinas que estan en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('modelos.maquinas', string='Maquina')
    secuencia = fields.Char('Formulario N°', default='New', copy=False, required=True, readonly=True)
    @api.model
    def create(self, vals):
        vals['secuencia'] = self.env['ir.sequence'].next_by_code('copier.company') or '/'
        return super(CopierCompany, self).create(vals)
        
    imagen_id = fields.Binary(related='name.imagen', string='Imagen')
    especificaciones_id = fields.Html(related='name.especificaciones', string=' ')
    serie_id = fields.Char(string='Serie')
    marca_id = fields.Many2one('marcas.maquinas', string='Marca', related='name.marca_id')
    cliente_id = fields.Many2one('res.partner', string='Cliente')
    tipo_identificacion = fields.Many2one(related='cliente_id.l10n_latam_identification_type_id', string="Tipo de identificación", readonly=False)
    identificacion = fields.Char(related='cliente_id.vat', string="Numero de identificación",readonly=False)
    @api.onchange('identificacion')
    def _onchange_identificacion(self):
        if self.identificacion:
            partner = self.env['res.partner'].search([('vat', '=', self.identificacion)], limit=1)
            if partner:
                self.cliente_id = partner.id
                self.tipo_identificacion = partner.l10n_latam_identification_type_id.id
            else:
                # Crear un nuevo partner con un nombre temporal
                new_partner = self.env['res.partner'].create({
                    'vat': self.identificacion,
                    'name': 'Cargando...',
                    'l10n_latam_identification_type_id': self.tipo_identificacion.id
                })
                
                # Llamar a la lógica de res.partner para obtener los datos de la SUNAT
                new_partner._doc_number_change()
                
                # Asegurarse de que el nombre se actualiza después de obtener los datos
                if new_partner.name == 'Cargando...':
                    new_partner.name = new_partner.vat
                
                self.cliente_id = new_partner.id
                self.tipo_identificacion = new_partner.l10n_latam_identification_type_id.id
    
    tipo = fields.Selection(string='Tipo de impresora', selection=[('monocroma', 'Blanco y negro'), ('color', 'Color')],
                            default='monocroma', help='Aqui elija que tipo de equipo multifuncional necesita si blanco y negro o color.')
       
    contacto = fields.Char(string='Contacto')
    celular = fields.Char(string='Telefono')
    correo = fields.Char(string='Correo')
    detalles = fields.Text(string='Detalle')
    formato = fields.Selection(string='Formato', selection=[('a4', 'A4'), ('a3', 'A3')], default='a3', help='Elija el formato de papel')
    ubicacion = fields.Char(string='Ubicación')
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado_maquina_id = fields.Many2one('copier.estados', string="Estado de la Máquina", default=lambda self: self.env.ref('copier_company.estado_disponible').id, tracking=True)
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler")
    duracion_alquiler_id = fields.Many2one('copier.duracion', string="Duración del Alquiler", default=lambda self: self.env.ref('copier_company.duracion_1_año').id)
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)
    qr_code = fields.Binary(string='Código QR', readonly=True)

    @api.model
    def _default_currency_id(self):
        value = self.env['res.currency'].search(
            [('name', '=', 'PEN')], limit=1)
        return value and value.id or False

    currency_id = fields.Many2one('res.currency', string='Tipo de moneda', default=_default_currency_id)
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", currency_field='currency_id')
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", currency_field='currency_id')
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")
    renta_mensual_color = fields.Monetary(string="Renta Mensual (Color)", compute='_compute_renta_mensual', currency_field='currency_id')
    renta_mensual_bn = fields.Monetary(string="Renta Mensual (B/N)", compute='_compute_renta_mensual', currency_field='currency_id')
    total_facturar_mensual = fields.Monetary(string="Total a Facturar Mensual", compute='_compute_renta_mensual', currency_field='currency_id')
    igv = fields.Float(string='IGV (%)', default=18.0)
    descuento = fields.Float(string='Descuento (%)', default=0.0)

    @api.depends('volumen_mensual_color', 'volumen_mensual_bn', 'costo_copia_color', 'costo_copia_bn', 'igv', 'descuento')
    def _compute_renta_mensual(self):
        for record in self:
            renta_mensual_color = record.volumen_mensual_color * record.costo_copia_color
            renta_mensual_bn = record.volumen_mensual_bn * record.costo_copia_bn
            subtotal = renta_mensual_color + renta_mensual_bn
            
            # Aplicar descuento
            descuento_total = subtotal * (record.descuento / 100.0)
            subtotal_descuento = subtotal - descuento_total
            
            # Aplicar IGV
            igv_total = subtotal_descuento * (record.igv / 100.0)
            total_con_igv = subtotal_descuento + igv_total
            
            record.renta_mensual_color = renta_mensual_color
            record.renta_mensual_bn = renta_mensual_bn
            record.total_facturar_mensual = total_con_igv

    @api.depends('fecha_inicio_alquiler', 'duracion_alquiler_id')
    def _calcular_fecha_fin(self):
        for record in self:
            if record.fecha_inicio_alquiler and record.duracion_alquiler_id:
                start_date = fields.Date.from_string(record.fecha_inicio_alquiler)
                duracion = record.duracion_alquiler_id.name
                if duracion == '6 Meses':
                    record.fecha_fin_alquiler = start_date + relativedelta(months=+6)
                elif duracion == '1 Año':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+1)
                elif duracion == '2 Años':
                    record.fecha_fin_alquiler = start_date + relativedelta(years=+2)

    def crear_ticket(self):
        ticket = self.env['helpdesk.ticket']
        ticket_id = ticket.create({
            'partner_id': self.cliente_id.id,
            'producto_id': self.id,
            'name': "Actualizar",
        })
        return {
            'name': 'Registro',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def generar_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_path = get_module_resource('copier_company', 'static', 'src', 'img', 'logo.png')

        # Verifica si el archivo existe
        if not logo_path or not os.path.isfile(logo_path):
            raise FileNotFoundError(f"Logo file not found: {logo_path}")

        logo = Image.open(logo_path)

        # Ajustamos el tamaño de la imagen del logo
        hsize = int((float(logo.size[1]) * float(100 / float(logo.size[0]))))
        logo = logo.resize((100, hsize), Image.ANTIALIAS)

        for record in self:
            data_to_encode = f"{base_url}/public/helpdesk_ticket?copier_company_id={record.id}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, logo)

            # Redimensionar la imagen del QR a la mitad de su tamaño original
            new_size = (qr_img.size[0] // 2, qr_img.size[1] // 2)
            qr_img = qr_img.resize(new_size, Image.ANTIALIAS)

            img_byte_array = io.BytesIO()
            qr_img.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

            record.qr_code = qr_image_base64
    def action_print_report(self):
        return self.env.ref('copier_company.action_report_report_cotizacion_alquiler').report_action(self)