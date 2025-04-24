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
        """Listar máquinas disponibles con filtros"""
        domain = [('state', '=', 'available')]

        # --- Marca ---
        marca_param = kwargs.get('marca') or ''
        try:
            selected_marca = int(marca_param) if marca_param else 0
        except ValueError:
            selected_marca = 0
        if selected_marca:
            # Filtramos por el campo many2one "marca_id"
            domain.append(('marca_id', '=', selected_marca))

        # --- Tipo ---
        selected_tipo = kwargs.get('tipo') or ''
        if selected_tipo:
            domain.append(('tipo', '=', selected_tipo))

        # Obtener todas las marcas para el selector
        marcas = request.env['marcas.maquinas'].sudo().search([])

        # Obtener máquinas según filtros
        machines = request.env['copier.stock'].sudo().search(domain)

        return request.render('copier_company.copier_list', {
            'machines': machines,
            'marcas': marcas,
            'selected_marca': selected_marca,
            'selected_tipo': selected_tipo,
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