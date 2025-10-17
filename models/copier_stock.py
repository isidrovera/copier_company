# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


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
    # Especifica si el ítem aplica a máquinas color, monocromas o ambas
    applies_to = fields.Selection([
        ('all', 'Todas las máquinas'),
        ('color', 'Solo máquinas color'),
        ('mono', 'Solo máquinas monocromas')
    ], string='Aplica a', default='all', required=True)
    active = fields.Boolean(default=True)


class CopierStock(models.Model):
    _name = 'copier.stock'
    _description = 'Stock de Máquinas (Fotocopiadoras de 2ª mano)'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Secuencia automática
    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )

    modelo_id = fields.Many2one('modelos.maquinas', string='Modelo', required=True, tracking=True)
    marca_id = fields.Many2one(related='modelo_id.marca_id', store=True, string='Marca', readonly=True)
    serie = fields.Char(string='N° de Serie', required=True, tracking=True)
    contometro = fields.Integer(string='Contómetro', default=0, tracking=True)

    tipo = fields.Selection([
        ('monocroma', 'Monocroma'),
        ('color', 'Color')
    ], string='Tipo de Máquina', required=True, default='monocroma', tracking=True)

    reparacion = fields.Selection([
        ('none', 'Sin reparación'),
        ('pending', 'Pendiente'),
        ('in_progress', 'En reparación'),
        ('done', 'Reparada')
    ], string='Estado Reparación', default='none', tracking=True)

    accesorios_ids = fields.Many2many('accesorios.maquinas', string='Accesorios Incluidos')

    checklist_ids = fields.One2many('copier.checklist.line', 'machine_id', string='Checklist de Unidad')

    checklist_status = fields.Selection([
        ('pending', 'Pendiente de revisión'),
        ('in_progress', 'En revisión'),
        ('completed', 'Revisado completo')
    ], string='Estado del Checklist', default='pending', tracking=True,
        compute='_compute_checklist_status', store=True)

    # Estado mejorado con nuevas etapas
    state = fields.Selection([
        ('importing', 'En Importación'),
        ('unloading', 'En Descarga'),
        ('available', 'Disponible'),
        ('reserved', 'Reservada'),
        ('pending_payment', 'Pendiente de Pago'),
        ('sold', 'Vendida')
    ], string='Estado', default='importing', tracking=True)

    reserved_by = fields.Many2one('res.partner', string='Reservada por', tracking=True)
    reserved_date = fields.Datetime(string='Fecha de Reserva', tracking=True)
    sold_date = fields.Datetime(string='Fecha de Venta', tracking=True)

    payment_proof = fields.Binary(string='Comprobante de Pago', attachment=True)
    payment_proof_filename = fields.Char(string='Nombre del archivo')
    payment_verified = fields.Boolean(string='Pago Verificado', default=False, tracking=True)

    sale_price = fields.Float(string='Precio de Venta', tracking=True)
    notes = fields.Text(string='Notas')
    active = fields.Boolean(string='Activo', default=True)

    # Temporizador de reserva
    reservation_initial_state = fields.Selection([
        ('importing', 'En Importación'),
        ('unloading', 'En Descarga'),
        ('available', 'Disponible')
    ], string='Estado Inicial de Reserva', tracking=True)

    reservation_expiry_date = fields.Datetime(string='Fecha de Expiración de Reserva', tracking=True)

    days_left = fields.Integer(string='Días Restantes', compute='_compute_days_left')

    # Imágenes
    image = fields.Binary(string="Imagen Principal", attachment=True)
    image_ids = fields.One2many('copier.stock.image', 'machine_id', string='Imágenes Adicionales')

    # Seguimiento de importación/descarga
    import_date = fields.Date(string='Fecha de Importación', tracking=True)
    unloading_date = fields.Date(string='Fecha de Descarga', tracking=True)
    import_reference = fields.Char(string='Referencia de Importación', tracking=True)
    shipping_company = fields.Char(string='Empresa de Transporte', tracking=True)

    # ---------------------------
    # CREATE
    # ---------------------------
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('copier.stock') or _('New')
            vals['name'] = seq

        # Por defecto, el estado es 'importing'
        if 'state' not in vals:
            vals['state'] = 'importing'

        # Registrar fecha de importación si aplica
        if vals.get('state') == 'importing' and 'import_date' not in vals:
            vals['import_date'] = fields.Date.today()

        record = super().create(vals)
        record._create_default_checklist()
        return record

    # ---------------------------
    # CHECKLIST
    # ---------------------------
    def _create_default_checklist(self):
        """Crea el checklist por defecto para la(s) máquina(s) basado en su tipo."""
        for rec in self:
            if rec.tipo == 'monocroma':
                checklist_items = self.env['copier.checklist.item'].search([
                    ('active', '=', True),
                    ('applies_to', 'in', ['all', 'mono'])
                ])
            else:
                checklist_items = self.env['copier.checklist.item'].search([
                    ('active', '=', True),
                    ('applies_to', 'in', ['all', 'color'])
                ])

            checklist_vals = [(0, 0, {
                'item_id': item.id,
                'name': item.name,
                'state': 'not_reviewed',
            }) for item in checklist_items]

            if checklist_vals:
                rec.write({'checklist_ids': checklist_vals})

    @api.depends('checklist_ids.state')
    def _compute_checklist_status(self):
        """Calcula el estado general del checklist basado en las líneas."""
        for record in self:
            if not record.checklist_ids:
                record.checklist_status = 'pending'
                continue

            not_reviewed = 0
            completed_items = 0

            for line in record.checklist_ids:
                if line.state == 'not_reviewed':
                    not_reviewed += 1
                elif line.state in ['good', 'regular', 'poor', 'replaced', 'not_applicable']:
                    completed_items += 1

            total_items = len(record.checklist_ids)

            if not_reviewed == total_items:
                record.checklist_status = 'pending'
            elif not_reviewed > 0:
                record.checklist_status = 'in_progress'
            else:
                record.checklist_status = 'completed'

    # ---------------------------
    # RESERVAS
    # ---------------------------
    @api.depends('reservation_expiry_date')
    def _compute_days_left(self):
        """Calcular los días restantes (enteros) antes de que expire la reserva."""
        now = fields.Datetime.now()
        for record in self:
            if record.reservation_expiry_date and record.state == 'reserved':
                delta = record.reservation_expiry_date - now
                record.days_left = max(0, int(delta.total_seconds() // 86400))
            else:
                record.days_left = 0

    def action_move_to_unloading(self):
        """Cambiar estado a 'En Descarga'."""
        for rec in self:
            rec.state = 'unloading'
            rec.unloading_date = fields.Date.today()

    def action_move_to_available(self):
        """Cambiar estado a 'Disponible' (ya no requiere checklist completo)."""
        for rec in self:
            if rec.reparacion == 'pending':
                raise UserError(_('La máquina tiene reparaciones pendientes.'))
            elif rec.reparacion == 'in_progress':
                raise UserError(_('La máquina está en proceso de reparación.'))
            rec.state = 'available'

    def action_reserve(self):
        """Reservar la máquina con temporizador según el estado inicial."""
        for rec in self:
            if rec.state not in ['available', 'importing', 'unloading']:
                raise UserError(_('Solo se pueden reservar máquinas disponibles, en importación o en descarga.'))

            rec.reservation_initial_state = rec.state
            rec.state = 'reserved'
            rec.reserved_by = self.env.user.partner_id
            rec.reserved_date = fields.Datetime.now()

            # Calcular fecha de expiración según el estado inicial
            expiry_days = 15 if rec.reservation_initial_state in ['importing', 'unloading'] else 5
            rec.reservation_expiry_date = rec.reserved_date + timedelta(days=expiry_days)

    def action_pending_payment(self):
        """Marcar como pendiente de pago."""
        for rec in self:
            if rec.state != 'reserved':
                raise UserError(_('Solo se pueden marcar como pendiente de pago máquinas reservadas.'))
            rec.state = 'pending_payment'
            # Al pasar a pendiente de pago, eliminamos la fecha de expiración
            rec.reservation_expiry_date = False

    def action_confirm_sale(self):
        """Confirmar la venta."""
        for rec in self:
            if rec.state not in ['pending_payment', 'reserved']:
                raise UserError(_('Solo se pueden confirmar ventas de máquinas reservadas o pendientes de pago.'))

            if not rec.payment_proof:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Advertencia'),
                        'message': _('No se puede confirmar la venta sin comprobante de pago.'),
                        'type': 'warning',
                    }
                }

            rec.state = 'sold'
            rec.sold_date = fields.Datetime.now()
            rec.payment_verified = True
            rec.reservation_expiry_date = False

    def action_cancel_reservation(self):
        """Cancelar reserva."""
        for rec in self:
            if rec.state not in ['reserved', 'pending_payment']:
                raise UserError(_('Solo se pueden cancelar reservas de máquinas reservadas o pendientes de pago.'))

            rec.state = 'available'
            rec.reserved_by = False
            rec.reserved_date = False
            rec.payment_proof = False
            rec.payment_proof_filename = False
            rec.payment_verified = False
            rec.reservation_expiry_date = False
            rec.reservation_initial_state = False

    @api.onchange('payment_proof')
    def _onchange_payment_proof(self):
        """Cambiar automáticamente el estado cuando se sube un comprobante de pago."""
        for rec in self:
            if rec.payment_proof and rec.state in ['reserved', 'pending_payment']:
                rec.state = 'pending_payment'
                rec.reservation_expiry_date = False

    # ---------------------------
    # CRONS
    # ---------------------------
    @api.model
    def _cron_check_expired_reservations(self):
        """Verificar y liberar reservas expiradas."""
        now = fields.Datetime.now()
        expired_machines = self.search([
            ('state', '=', 'reserved'),
            ('reservation_expiry_date', '!=', False),
            ('reservation_expiry_date', '<', now)
        ])

        for machine in expired_machines:
            machine.action_cancel_reservation()

            # Notificar al administrador (si existe)
            admin_user = self.env.ref('base.user_admin', raise_if_not_found=False)
            if admin_user:
                machine.message_post(
                    body=_("La reserva ha expirado y se ha liberado automáticamente."),
                    partner_ids=[admin_user.partner_id.id]
                )

    @api.model
    def _cron_check_payments(self):
        """Verificar automáticamente máquinas con comprobantes de pago subidos."""
        machines = self.search([
            ('state', '=', 'pending_payment'),
            ('payment_proof', '!=', False),
            ('payment_verified', '=', False)
        ])
        for machine in machines:
            # Lógica adicional de verificación podría ir aquí.
            # Por ahora, confirmamos la venta si hay comprobante.
            machine.action_confirm_sale()

    # ---------------------------
    # ACCIONES / WIZARDS
    # ---------------------------
    def action_mass_update_state(self):
        """Abrir asistente de actualización masiva de estados."""
        return {
            'name': _('Actualizar Estado'),
            'type': 'ir.actions.act_window',
            'res_model': 'copier.stock.state.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_copier_ids': self.ids},
        }

    # ---------------------------
    # CONSTRAINTS
    # ---------------------------
    @api.constrains('serie')
    def _check_unique_serie(self):
        """Evitar duplicidad de serie en máquinas activas."""
        for record in self:
            duplicates = self.search([
                ('serie', '=', record.serie),
                ('id', '!=', record.id),
                ('active', '=', True)
            ])
            if duplicates:
                raise ValidationError(_('Ya existe una máquina activa con el mismo número de serie.'))

    @api.onchange('tipo')
    def _onchange_tipo(self):
        """Al cambiar el tipo de máquina, recrear el checklist apropiado."""
        if self.checklist_ids and self._origin and self._origin.id:
            self.checklist_ids.unlink()
            self._create_default_checklist()


class CopierChecklistLine(models.Model):
    _name = 'copier.checklist.line'
    _description = 'Línea de Checklist para cada Máquina'
    _order = 'sequence, id'

    machine_id = fields.Many2one('copier.stock', string='Máquina', ondelete='cascade', required=True)
    item_id = fields.Many2one('copier.checklist.item', string='Item')
    name = fields.Char(string='Item de Checklist', required=True)
    sequence = fields.Integer(related='item_id.sequence', store=True)

    state = fields.Selection([
        ('not_reviewed', 'Sin revisar'),
        ('good', 'Buen Estado'),
        ('regular', 'Regular'),
        ('poor', 'Mal Estado'),
        ('replaced', 'Reemplazado'),
        ('not_applicable', 'No Aplica')
    ], string='Estado', required=True, default='not_reviewed')

    notes = fields.Text(string='Observaciones')

    # Indica si se requiere acción
    requires_action = fields.Boolean(
        string='Requiere Acción',
        compute='_compute_requires_action',
        store=True
    )

    @api.depends('state')
    def _compute_requires_action(self):
        """Calcula si el ítem requiere alguna acción basado en su estado."""
        for record in self:
            record.requires_action = record.state in ['not_reviewed', 'poor']


class CopierStockImage(models.Model):
    _name = 'copier.stock.image'
    _description = 'Imágenes adicionales de la máquina'

    machine_id = fields.Many2one('copier.stock', string='Máquina', ondelete='cascade')
    image = fields.Binary(string='Imagen', attachment=True, required=True)
    name = fields.Char(string='Descripción')


class CopierStockStateUpdateWizard(models.TransientModel):
    _name = 'copier.stock.state.update.wizard'
    _description = 'Asistente para actualización masiva de estados'

    copier_ids = fields.Many2many('copier.stock', string='Máquinas seleccionadas')
    target_state = fields.Selection([
        ('importing', 'En Importación'),
        ('unloading', 'En Descarga'),
        ('available', 'Disponible'),
    ], string='Estado Destino', required=True)

    def action_update_state(self):
        """Actualizar el estado de todas las máquinas seleccionadas."""
        if not self.copier_ids:
            raise UserError(_('No hay máquinas seleccionadas.'))

        warnings = []
        for copier in self.copier_ids:
            if self.target_state == 'unloading':
                copier.state = 'unloading'
                copier.unloading_date = fields.Date.today()
            elif self.target_state == 'available':
                if copier.checklist_status != 'completed':
                    warnings.append(_('La máquina %s no tiene el checklist completo.') % copier.display_name)
                copier.state = 'available'
            else:
                copier.state = self.target_state

        message = _('%d máquinas actualizadas a estado "%s".') % (
            len(self.copier_ids),
            dict(self._fields['target_state'].selection).get(self.target_state)
        )
        if warnings:
            message += '\n- ' + '\n- '.join(warnings)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
