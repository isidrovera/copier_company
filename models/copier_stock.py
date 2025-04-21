# models/copier_stock.py
from odoo import api, fields, models, _
from datetime import datetime

class CopierChecklistItem(models.Model):
    _name = 'copier.checklist.item'
    _description = 'Items de Checklist para Fotocopiadoras'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre del Item', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    item_type = fields.Selection([
        ('component', 'Componente'),
        ('function', 'Función'),
        ('appearance', 'Apariencia'),
    ], string='Tipo de Item', required=True)
    active = fields.Boolean(default=True)


class CopierStock(models.Model):
    _name = 'copier.stock'
    _description = 'Stock de Máquinas (Fotocopiadoras de 2ª mano)'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Secuencia automática
    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'), tracking=True)
    modelo_id = fields.Many2one('modelos.maquinas', string='Modelo', required=True, tracking=True)
    marca_id = fields.Many2one(related='modelo_id.marca_id', store=True,
                               string='Marca', readonly=True)
    serie = fields.Char(string='N° de Serie', required=True, tracking=True)
    contometro_color = fields.Integer(string='Contómetro Color', default=0, tracking=True)
    contometro_bn = fields.Integer(string='Contómetro B/N', default=0, tracking=True)
    tipo = fields.Selection([
        ('monocroma', 'Monocroma'),
        ('color', 'Color')
    ], string='Tipo de Máquina', required=True, default='monocroma', tracking=True)
    reparacion = fields.Selection([
            ('none', 'Sin reparación'),
            ('pending', 'Pendiente'),
            ('in_progress', 'En reparación'),
            ('done', 'Reparada')],
        string='Estado Reparación', default='none', tracking=True)
    accesorios_ids = fields.Many2many('accesorios.maquinas',
                                      string='Accesorios Incluidos')
    checklist_ids = fields.One2many('copier.checklist.line', 'machine_id',
                                    string='Checklist de Unidad')
    state = fields.Selection([
            ('available', 'Disponible'),
            ('reserved', 'Reservada'),
            ('pending_payment', 'Pendiente de Pago'),
            ('sold', 'Vendida')],
        string='Estado', default='available', tracking=True)
    reserved_by = fields.Many2one('res.partner', string='Reservada por', tracking=True)
    reserved_date = fields.Datetime(string='Fecha de Reserva', tracking=True)
    sold_date = fields.Datetime(string='Fecha de Venta', tracking=True)
    payment_proof = fields.Binary(string='Comprobante de Pago', attachment=True)
    payment_proof_filename = fields.Char(string='Nombre del archivo')
    payment_verified = fields.Boolean(string='Pago Verificado', default=False, tracking=True)
    sale_price = fields.Float(string='Precio de Venta', tracking=True)
    notes = fields.Text(string='Notas')
    active = fields.Boolean(string='Activo', default=True)
    
    # Campo para la imagen principal
    image = fields.Binary(string="Imagen Principal", attachment=True)
    # Campo para imágenes adicionales
    image_ids = fields.One2many('copier.stock.image', 'machine_id', string='Imágenes Adicionales')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('copier.stock') or _('New')
            vals['name'] = seq
        
        # Crear automáticamente líneas de checklist
        result = super().create(vals)
        result._create_default_checklist()
        return result

    def _create_default_checklist(self):
        """Crea el checklist por defecto para la máquina"""
        checklist_items = self.env['copier.checklist.item'].search([('active', '=', True)])
        checklist_vals = []
        
        for item in checklist_items:
            checklist_vals.append((0, 0, {
                'item_id': item.id,
                'name': item.name,
                'state': 'good',
            }))
        
        self.write({'checklist_ids': checklist_vals})

    def action_reserve(self):
        for rec in self:
            rec.state = 'reserved'
            rec.reserved_by = self.env.user.partner_id.id
            rec.reserved_date = fields.Datetime.now()

    def action_pending_payment(self):
        for rec in self:
            rec.state = 'pending_payment'

    @api.model
    def _cron_check_payments(self):
        """Verificar automáticamente máquinas con comprobantes de pago subidos"""
        machines = self.search([
            ('state', '=', 'pending_payment'),
            ('payment_proof', '!=', False),
            ('payment_verified', '=', False)
        ])
        for machine in machines:
            # Aquí podría incluirse lógica adicional para verificación automática
            # Por ahora, simplemente confirma la venta si hay comprobante
            machine.action_confirm_sale()

    def action_confirm_sale(self):
        for rec in self:
            if rec.payment_proof:
                rec.state = 'sold'
                rec.sold_date = fields.Datetime.now()
                rec.payment_verified = True
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Advertencia'),
                        'message': _('No se puede confirmar la venta sin comprobante de pago.'),
                        'type': 'warning',
                    }
                }

    def action_cancel_reservation(self):
        for rec in self:
            rec.state = 'available'
            rec.reserved_by = False
            rec.reserved_date = False
            rec.payment_proof = False
            rec.payment_proof_filename = False
            rec.payment_verified = False

    @api.onchange('payment_proof')
    def _onchange_payment_proof(self):
        """Cambiar automáticamente el estado cuando se sube un comprobante de pago"""
        for rec in self:
            if rec.payment_proof and rec.state in ['reserved', 'pending_payment']:
                rec.state = 'sold'
                rec.sold_date = fields.Datetime.now()
                rec.payment_verified = True


class CopierStockImage(models.Model):
    _name = 'copier.stock.image'
    _description = 'Imágenes adicionales de la máquina'

    machine_id = fields.Many2one('copier.stock', string='Máquina', ondelete='cascade')
    image = fields.Binary(string='Imagen', attachment=True, required=True)
    name = fields.Char(string='Descripción')


class CopierChecklistLine(models.Model):
    _name = 'copier.checklist.line'
    _description = 'Línea de Checklist para cada Máquina'
    _order = 'sequence, id'

    machine_id = fields.Many2one('copier.stock', string='Máquina',
                                 ondelete='cascade', required=True)
    item_id = fields.Many2one('copier.checklist.item', string='Item')
    name = fields.Char(string='Item de Checklist', required=True)
    sequence = fields.Integer(related='item_id.sequence', store=True)
    
    state = fields.Selection([
        ('good', 'Buen Estado'),
        ('regular', 'Regular'),
        ('poor', 'Mal Estado'),
        ('replaced', 'Reemplazado'),
        ('not_applicable', 'No Aplica')
    ], string='Estado', required=True, default='good')
    
    notes = fields.Text(string='Observaciones')