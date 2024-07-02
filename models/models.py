    from odoo import models, fields, api
from dateutil.relativedelta import relativedelta  # Importa relativedelta
import qrcode
import base64
import io

class CopierCompany(models.Model):
    _name = 'copier.company'
    _description = 'Aqui se registran las maquinas que estan en alquiler'
    _inherit = ['mail.thread', 'mail.activity.mixin']
       
    name = fields.Many2one('modelos.maquinas', string='Maquina')
    serie_id = fields.Char(string='Serie', required=True)
    marca_id = fields.Many2one('marcas.maquinas', string='Marca', required=True, related='name.marca_id')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    ubicacion = fields.Char(string='Ubicación')
    sede = fields.Char(string='Sede')
    ip_id = fields.Char(string="IP")
    accesorios_ids = fields.Many2many('accesorios.maquinas', string="Accesorios")
    estado_maquina_id = fields.Many2one('copier.estados', string="Estado de la Máquina", default=lambda self: self.env.ref('copier_company.estado_disponible').id, tracking=True)
    fecha_inicio_alquiler = fields.Date(string="Fecha de Inicio del Alquiler")
    duracion_alquiler_id = fields.Many2one('copier.duracion', string="Duración del Alquiler", default=lambda self: self.env.ref('copier_company.duracion_1_año').id)
    fecha_fin_alquiler = fields.Date(string="Fecha de Fin del Alquiler", compute='_calcular_fecha_fin', store=True)

    @api.model
    def _default_currency_id(self):
        value = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        return value and value.id or False
    currency_id = fields.Many2one('res.currency', string='Tipo de moneda', default=_default_currency_id)
    costo_copia_color = fields.Monetary(string="Costo por Copia (Color)", currency_field='currency_id')
    costo_copia_bn = fields.Monetary(string="Costo por Copia (B/N)", currency_field='currency_id')
    volumen_mensual_color = fields.Integer(string="Volumen Mensual (Color)")
    volumen_mensual_bn = fields.Integer(string="Volumen Mensual (B/N)")
    renta_mensual_color = fields.Monetary(string="Renta Mensual (Color)", compute='_compute_renta_mensual', currency_field='currency_id')
    renta_mensual_bn = fields.Monetary(string="Renta Mensual (B/N)", compute='_compute_renta_mensual', currency_field='currency_id')
    total_facturar_mensual = fields.Monetary(string="Total a Facturar Mensual", compute='_compute_renta_mensual', currency_field='currency_id')

    @api.depends('volumen_mensual_color', 'volumen_mensual_bn', 'costo_copia_color', 'costo_copia_bn')
    def _compute_renta_mensual(self):
        for record in self:
            record.renta_mensual_color = record.volumen_mensual_color * record.costo_copia_color
            record.renta_mensual_bn = record.volumen_mensual_bn * record.costo_copia_bn
            record.total_facturar_mensual = record.renta_mensual_color + record.renta_mensual_bn

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

    qr_code = fields.Binary(string='Código QR', readonly=True)

    def generar_qr_code(self):
        base_url = "https://copiercompanysac.com//public/helpdesk_ticket"
        dpi = 300
        inches_for_qr = 1.5 / 4
        pixels_for_qr = int(dpi * inches_for_qr)
        version_size = 21
        box_size = max(1, pixels_for_qr // (version_size + (2 * 4)))

        for record in self:
            data_to_encode = f"{base_url}?copier_company_id={record.id}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=4,
            )
            qr.add_data(data_to_encode)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            qr_image_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

            record.qr_code = qr_image_base64
