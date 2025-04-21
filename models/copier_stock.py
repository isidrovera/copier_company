# models/copier_stock.py
from odoo import api, fields, models, _
from datetime import datetime

class CopierStock(models.Model):
    _name = 'copier.stock'
    _description = 'Stock de Máquinas (Fotocopiadoras de 2ª mano)'
    _order = 'name'

    # Secuencia automática
    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    modelo_id = fields.Many2one('modelos.maquinas', string='Modelo', required=True)
    marca_id = fields.Many2one(related='modelo_id.marca_id', store=True,
                               string='Marca', readonly=True)
    serie = fields.Char(string='N° de Serie', required=True)
    contometro_color = fields.Integer(string='Contómetro Color', default=0)
    contometro_bn = fields.Integer(string='Contómetro B/N', default=0)
    reparacion = fields.Selection([
            ('none', 'Sin reparación'),
            ('pending', 'Pendiente'),
            ('in_progress', 'En reparación'),
            ('done', 'Reparada')],
        string='Estado Reparación', default='none')
    accesorios_ids = fields.Many2many('accesorios.maquinas',
                                      string='Accesorios Incluidos')
    checklist_ids = fields.One2many('copier.checklist.line', 'machine_id',
                                    string='Checklist de Unidad')
    state = fields.Selection([
            ('available', 'Disponible'),
            ('reserved', 'Reservada'),
            ('sold', 'Vendida')],
        string='Estado', default='available', tracking=True)
    reserved_by = fields.Many2one('res.partner', string='Reservada por')
    reserved_date = fields.Datetime(string='Fecha de Reserva')
    sold_date = fields.Datetime(string='Fecha de Venta')
    payment_proof = fields.Binary(string='Comprobante de Pago', attachment=True)
    active = fields.Boolean(string='Activo', default=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('copier.stock') or _('New')
            vals['name'] = seq
        return super().create(vals)

    def action_reserve(self):
        for rec in self:
            rec.state = 'reserved'
            rec.reserved_by = self.env.user.partner_id.id
            rec.reserved_date = fields.Datetime.now()

    def action_confirm_sale(self):
        for rec in self:
            rec.state = 'sold'
            rec.sold_date = fields.Datetime.now()

    def action_cancel_reservation(self):
        for rec in self:
            rec.state = 'available'
            rec.reserved_by = False
            rec.reserved_date = False
            rec.payment_proof = False

class CopierChecklistLine(models.Model):
    _name = 'copier.checklist.line'
    _description = 'Línea de Checklist para cada Máquina'

    machine_id = fields.Many2one('copier.stock', string='Máquina',
                                 ondelete='cascade', required=True)
    name = fields.Char(string='Item de Checklist', required=True)
    done = fields.Boolean(string='Hecho', default=False)
