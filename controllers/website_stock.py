# controllers/website_stock.py
from odoo import http, _
from odoo.http import request
from datetime import datetime
import base64
import logging

_logger = logging.getLogger(__name__)

class WebsiteStock(http.Controller):

    @http.route(['/stock-maquinas'], type='http', auth='user', website=True)
    def list_stock(self, **kwargs):
        _logger.debug("📥 [START] Ingreso a /stock-maquinas con kwargs: %s", kwargs)
        
        domain = []

        # Filtro por marca
        marca_param = kwargs.get('marca') or ''
        try:
            selected_marca = int(marca_param) if marca_param else 0
        except ValueError:
            selected_marca = 0
            _logger.warning("⚠️ [WARN] 'marca' no es un entero válido: %s", marca_param)

        _logger.debug("🔧 Marca seleccionada: %s", selected_marca)
        if selected_marca:
            domain.append(('marca_id', '=', selected_marca))

        # Filtro por tipo
        selected_tipo = kwargs.get('tipo') or ''
        _logger.debug("🔧 Tipo seleccionado: %s", selected_tipo)
        if selected_tipo:
            domain.append(('tipo', '=', selected_tipo))

        # Filtro por estado
        selected_estado = kwargs.get('estado') or ''
        _logger.debug("🔧 Estado seleccionado: %s", selected_estado)

        # Filtro por checkbox "Mostrar solo disponibles"
        available_only = kwargs.get('available_only')
        _logger.debug("🔘 Checkbox 'available_only' recibido: %s", available_only)

        if available_only not in ['on', 'off']:
            available_only = 'on'
            _logger.debug("🔘 'available_only' no presente o inválido → usando valor por defecto: 'on'")
        else:
            _logger.debug("✅ 'available_only' confirmado como: %s", available_only)

        if available_only == 'on' and not selected_estado:
            domain.append(('state', '=', 'available'))
            _logger.debug("✅ Aplicando filtro por estado: disponible (checkbox activo, sin estado manual)")
        elif selected_estado:
            domain.append(('state', '=', selected_estado))
            _logger.debug("✅ Aplicando filtro por estado específico: %s", selected_estado)

        # Filtro por búsqueda
        search = kwargs.get('search') or ''
        _logger.debug("🔎 Texto de búsqueda: '%s'", search)
        if search:
            domain.append(('name', 'ilike', search))

        _logger.debug("🧾 Dominio final generado para búsqueda: %s", domain)

        # Obtener marcas disponibles
        marcas = request.env['marcas.maquinas'].sudo().search([])
        _logger.debug("📦 Total marcas encontradas: %d", len(marcas))

        # Consultar las máquinas
        machines = request.env['copier.stock'].sudo().search(domain)
        _logger.debug("📦 Total máquinas encontradas: %d", len(machines))

        # Render de plantilla
        _logger.debug("📤 Renderizando plantilla 'copier_company.copier_list'")
        return request.render('copier_company.copier_list', {
            'machines': machines,
            'marcas': marcas,
            'selected_marca': selected_marca,
            'selected_tipo': selected_tipo,
            'selected_estado': selected_estado,
            'available_only': available_only,
            'search': search,
            'user': request.env.user,
        })



    @http.route(['/stock-maquinas/<model("copier.stock"):machine>'], type='http', auth='user', website=True)
    def detail_stock(self, machine, **kwargs):
        """Ver detalle de una máquina específica"""
        return request.render('copier_company.copier_detail', {
            'machine': machine,
            'user': request.env.user,
        })

    @http.route(['/stock-maquinas/<model("copier.stock"):machine>/reserve'], type='http', auth='user', methods=['POST'], website=True)
    def reserve_stock(self, machine, **post):
        """Reservar una máquina"""
        if machine.state != 'available':
            return request.render('copier_company.machine_not_available', {
                'machine': machine,
            })
            
        # Reservar la máquina
        machine.sudo().action_reserve()
        return request.redirect(f'/stock-maquinas/{machine.id}/payment')

    @http.route(['/stock-maquinas/image/<int:machine_id>'], type='http', auth='user', website=True)
    def get_machine_image(self, machine_id, **kwargs):
        """Servir imágenes de máquinas"""
        machine = request.env['copier.stock'].sudo().browse(machine_id)
        if not machine.exists() or not machine.image:
            return request.not_found()
        
        return http.request.make_response(
            base64.b64decode(machine.image),
            headers=[('Content-Type', 'image/png')]  # Ajusta el tipo de contenido según sea necesario
        )

    @http.route(['/stock-maquinas/payment-proof/<int:machine_id>'], type='http', auth='user', website=True)
    def get_payment_proof(self, machine_id, **kwargs):
        """Servir imágenes de comprobantes de pago"""
        machine = request.env['copier.stock'].sudo().browse(machine_id)
        # Verifica si el usuario está autorizado para ver este comprobante
        if not machine.exists() or not machine.payment_proof:
            return request.not_found()
        
        return http.request.make_response(
            base64.b64decode(machine.payment_proof),
            headers=[('Content-Type', 'application/octet-stream')]  # Tipo de contenido genérico para archivos
        )
    
    @http.route(['/stock-maquinas/<model("copier.stock"):machine>/payment'], type='http', auth='user', website=True)
    def payment_page(self, machine, **kwargs):
        """Página para subir comprobante de pago"""
        if machine.state not in ['reserved', 'pending_payment'] or machine.reserved_by.id != request.env.user.partner_id.id:
            return request.redirect('/stock-maquinas')
            
        return request.render('copier_company.payment_upload', {
            'machine': machine,
        })
    
    @http.route(['/stock-maquinas/<model("copier.stock"):machine>/upload_payment'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def upload_payment(self, machine, **post):
        """Procesar la subida del comprobante de pago"""
        if machine.state not in ['reserved', 'pending_payment'] or machine.reserved_by.id != request.env.user.partner_id.id:
            return request.redirect('/stock-maquinas')
            
        file = post.get('payment_proof')
        if not file:
            return request.render('copier_company.payment_upload', {
                'machine': machine,
                'error': _("Por favor suba un comprobante de pago."),
            })
            
        try:
            data = file.read()
            filename = file.filename
            
            # Actualizar la máquina con el comprobante
            machine.sudo().write({
                'payment_proof': base64.b64encode(data),
                'payment_proof_filename': filename,
                'state': 'sold',  # Cambiar automáticamente a vendida
                'sold_date': datetime.now(),  # ✅ Corregido
                'payment_verified': True,
            })
            
            return request.render('copier_company.payment_success', {
                'machine': machine,
            })
        except Exception as e:
            _logger.error("Error al procesar el pago: %s", str(e))
            return request.render('copier_company.payment_upload', {
                'machine': machine,
                'error': _("Ocurrió un error al procesar su comprobante. Por favor intente nuevamente."),
            })

    
    @http.route(['/mis-maquinas'], type='http', auth='user', website=True)
    def my_machines(self, **kwargs):
        """Ver máquinas reservadas o compradas por el usuario"""
        partner_id = request.env.user.partner_id.id
        
        reserved_machines = request.env['copier.stock'].sudo().search([
            ('reserved_by', '=', partner_id),
            ('state', 'in', ['reserved', 'pending_payment'])
        ])
        
        purchased_machines = request.env['copier.stock'].sudo().search([
            ('reserved_by', '=', partner_id),
            ('state', '=', 'sold')
        ])
        
        return request.render('copier_company.my_machines', {
            'reserved_machines': reserved_machines,
            'purchased_machines': purchased_machines,
        })