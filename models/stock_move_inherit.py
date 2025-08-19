# models/stock_move_inherit.py
from odoo import api, fields, models, _, exceptions
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        """Override para auto-crear copier.stock al recibir fotocopiadoras"""
        # Llamar al método original primero
        result = super()._action_done(cancel_backorder=cancel_backorder)
        
        # Procesar auto-creación de copier.stock para fotocopiadoras
        self._create_copier_stock_for_copiers()
        
        return result

    def _create_copier_stock_for_copiers(self):
        """Crea registros en copier.stock para fotocopiadoras recibidas"""
        for move in self:
            try:
                # Solo procesar si es una recepción (picking de entrada)
                if not self._is_receipt_move(move):
                    continue
                
                # Verificar si el producto es una fotocopiadora
                if not self._is_copier_product(move.product_id):
                    continue
                
                # Verificar que tenga números de serie asignados
                move_lines_with_lots = move.move_line_ids.filtered(lambda ml: ml.lot_id and ml.quantity_done > 0)
                if not move_lines_with_lots:
                    _logger.warning(f"Fotocopiadora {move.product_id.name} recibida sin número de serie")
                    continue
                
                # Procesar cada línea de movimiento con número de serie
                for move_line in move_lines_with_lots:
                    self._create_copier_stock_record(move, move_line.lot_id)
                    
            except Exception as e:
                _logger.error(f"Error procesando move {move.id}: {str(e)}")
                # No lanzar excepción para no bloquear el flujo normal
                continue

    def _is_receipt_move(self, move):
        """Verifica si el movimiento es una recepción (entrada)"""
        return (
            move.picking_id and 
            move.picking_id.picking_type_id.code == 'incoming' and
            move.state == 'done'
        )

    def _is_copier_product(self, product):
        """Verifica si el producto es una fotocopiadora"""
        if not product or not product.categ_id:
            return False
        
        # Verificar por categoría "Fotocopiadora"
        return product.categ_id.name.lower() in ['fotocopiadora', 'fotocopiadoras']

    def _create_copier_stock_record(self, move, lot):
        """Crea un registro individual en copier.stock"""
        try:
            # Verificar si ya existe un registro con esta serie
            existing_stock = self.env['copier.stock'].search([
                ('serie', '=', lot.name)
            ], limit=1)
            
            if existing_stock:
                _logger.warning(f"Ya existe copier.stock con serie {lot.name}: {existing_stock.name}")
                return
            
            # Buscar el modelo de máquina correspondiente
            modelo = self._find_modelo_maquina(move.product_id)
            if not modelo:
                _logger.error(f"No se encontró modelo para producto {move.product_id.name}")
                return
            
            # Preparar valores para copier.stock
            stock_vals = {
                'modelo_id': modelo.id,
                'serie': lot.name,
                'tipo': self._detect_machine_type(modelo),
                'state': 'importing',  # Estado inicial
                'import_date': fields.Date.today(),
                'import_reference': move.picking_id.name,
                'shipping_company': move.picking_id.partner_id.name if move.picking_id.partner_id else '',
                'contometro': 0,  # Contador inicial en 0
                'reparacion': 'none',  # Sin reparación inicialmente
                'notes': f'Creado automáticamente desde recepción {move.picking_id.name}\nProducto: {move.product_id.name}',
            }
            
            # Crear el registro
            new_copier = self.env['copier.stock'].create(stock_vals)
            
            _logger.info(f"✅ Copier.stock creado: {new_copier.name} - Serie: {lot.name} - Modelo: {modelo.name}")
            
            # Agregar nota en el chatter del picking
            if move.picking_id:
                move.picking_id.message_post(
                    body=f"✅ <b>Máquina agregada al stock de distribuidores:</b><br/>"
                         f"• Referencia: {new_copier.name}<br/>"
                         f"• Modelo: {modelo.name}<br/>"
                         f"• Serie: {lot.name}<br/>"
                         f"• Estado inicial: Importando",
                    message_type='notification'
                )
            
        except Exception as e:
            _logger.error(f"Error creando copier.stock para serie {lot.name}: {str(e)}")
            raise

    def _find_modelo_maquina(self, product):
        """Busca el modelo de máquina correspondiente al producto"""
        try:
            # Buscar por relación directa (si el producto fue creado desde modelos.maquinas)
            modelo = self.env['modelos.maquinas'].search([
                ('product_id', '=', product.id)
            ], limit=1)
            
            if modelo:
                return modelo
            
            # Buscar por nombre del producto
            # Extraer nombre del modelo desde el producto
            # Ej: "Fotocopiadora Canon iR-ADV C3330" -> buscar "iR-ADV C3330"
            product_name = product.name
            
            # Remover prefijos comunes
            prefixes_to_remove = ['fotocopiadora', 'impresora', 'multifuncional']
            for prefix in prefixes_to_remove:
                if product_name.lower().startswith(prefix.lower()):
                    product_name = product_name[len(prefix):].strip()
                    break
            
            # Buscar modelo por similitud de nombre
            # Primero intentar coincidencia exacta
            for modelo in self.env['modelos.maquinas'].search([]):
                modelo_full_name = f"{modelo.marca_id.name} {modelo.name}".strip()
                if modelo_full_name.lower() == product_name.lower():
                    return modelo
            
            # Si no encuentra exacto, buscar por contenido
            for modelo in self.env['modelos.maquinas'].search([]):
                if modelo.name.lower() in product_name.lower():
                    return modelo
            
            _logger.warning(f"No se encontró modelo para producto: {product.name}")
            return False
            
        except Exception as e:
            _logger.error(f"Error buscando modelo para producto {product.name}: {str(e)}")
            return False

    def _detect_machine_type(self, modelo):
        """Detecta el tipo de máquina basado en el modelo"""
        if not modelo:
            return 'monocroma'  # Por defecto
        
        # Si el modelo tiene tipo_maquina definido
        if hasattr(modelo, 'tipo_maquina') and modelo.tipo_maquina:
            if modelo.tipo_maquina in ['fotocopiadora']:
                # Detectar si es color o monocroma por el nombre
                name_lower = modelo.name.lower()
                if any(word in name_lower for word in ['color', 'colour', 'c550', 'c650', 'c750']):
                    return 'color'
                else:
                    return 'monocroma'
        
        return 'monocroma'  # Por defecto


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Override para validar series en fotocopiadoras antes de confirmar"""
        # Validar series de fotocopiadoras antes de procesar
        self._validate_copier_serial_numbers()
        
        # Llamar al método original
        return super().button_validate()

    def _validate_copier_serial_numbers(self):
        """Valida que las fotocopiadoras tengan número de serie"""
        if self.picking_type_id.code != 'incoming':
            return  # Solo validar en recepciones
        
        for move in self.move_ids:
            # Verificar si es fotocopiadora
            if self._is_copier_product_picking(move.product_id):
                # Verificar las líneas de movimiento (move.line_ids)
                for move_line in move.move_line_ids:
                    if move_line.quantity_done > 0:
                        # Verificar que tenga número de serie
                        if not move_line.lot_id and move.product_id.tracking == 'serial':
                            raise exceptions.UserError(
                                f"La fotocopiadora '{move.product_id.name}' requiere número de serie.\n\n"
                                f"Por favor, asigne un número de serie único a cada unidad antes de validar la recepción."
                            )

    def _is_copier_product_picking(self, product):
        """Verifica si el producto es una fotocopiadora (desde picking)"""
        if not product or not product.categ_id:
            return False
        
        return product.categ_id.name.lower() in ['fotocopiadora', 'fotocopiadoras']