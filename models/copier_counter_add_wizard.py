from odoo import models, fields, api
from odoo.exceptions import UserError


class CopierCounterAddWizard(models.TransientModel):
    _name = 'copier.counter.add.wizard'
    _description = 'Wizard para sumar copias al contador anterior'

    counter_id = fields.Many2one(
        'copier.counter',
        string='Lectura',
        required=True,
        ondelete='cascade'
    )

    tipo_maquina = fields.Selection(
        related='counter_id.maquina_id.tipo',
        string='Tipo de Máquina',
        readonly=True
    )

    contador_anterior_bn = fields.Integer(
        related='counter_id.contador_anterior_bn',
        string='Contador Anterior B/N',
        readonly=True
    )

    contador_anterior_color = fields.Integer(
        related='counter_id.contador_anterior_color',
        string='Contador Anterior Color',
        readonly=True
    )

    cantidad_bn = fields.Integer(
        'Cantidad de Copias B/N',
        required=True,
        default=0,
        help="Cantidad de copias B/N realizadas en el periodo. Se sumará al contador anterior."
    )

    cantidad_color = fields.Integer(
        'Cantidad de Copias Color',
        default=0,
        help="Cantidad de copias Color realizadas en el periodo. Se sumará al contador anterior."
    )

    # Vista previa de los nuevos contadores
    nuevo_contador_bn = fields.Integer(
        'Nuevo Contador B/N',
        compute='_compute_nuevos_contadores'
    )

    nuevo_contador_color = fields.Integer(
        'Nuevo Contador Color',
        compute='_compute_nuevos_contadores'
    )

    @api.depends('cantidad_bn', 'cantidad_color',
                 'contador_anterior_bn', 'contador_anterior_color')
    def _compute_nuevos_contadores(self):
        for record in self:
            record.nuevo_contador_bn = (record.contador_anterior_bn or 0) + (record.cantidad_bn or 0)
            record.nuevo_contador_color = (record.contador_anterior_color or 0) + (record.cantidad_color or 0)

    def action_aplicar(self):
        self.ensure_one()

        if self.cantidad_bn < 0 or self.cantidad_color < 0:
            raise UserError('Las cantidades no pueden ser negativas.')

        if self.counter_id.state != 'draft':
            raise UserError('Solo se pueden modificar lecturas en estado borrador.')

        vals = {
            'contador_actual_bn': self.contador_anterior_bn + self.cantidad_bn,
        }

        # Solo actualizar color si la máquina es color
        if self.tipo_maquina == 'color':
            vals['contador_actual_color'] = self.contador_anterior_color + self.cantidad_color

        self.counter_id.write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Contadores actualizados',
                'message': f'Nuevo contador B/N: {vals["contador_actual_bn"]}' +
                           (f' | Nuevo contador Color: {vals.get("contador_actual_color")}'
                            if self.tipo_maquina == 'color' else ''),
                'type': 'success',
                'sticky': False,
            }
        }