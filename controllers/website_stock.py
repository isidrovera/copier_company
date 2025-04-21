# controllers/website_stock.py
from odoo import http, _
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)

class WebsiteStock(http.Controller):

    @http.route(['/stock-maquinas'], type='http', auth='user', website=True)
    def list_stock(self, **kwargs):
        """Listar máquinas disponibles con filtros"""
        domain = [('state', '=', 'available')]
        
        # Aplicar filtros si se proporcionan
        if kwargs.get('marca'):
            domain.append(('marca_id.id', '=', int(kwargs.get('marca'))))
        if kwargs.get('tipo'):
            domain.append(('tipo', '=', kwargs.get('tipo')))
            
        # Obtener todas las marcas para el filtro
        marcas = request.env['marca.maquina'].sudo().search([])
        
        # Obtener máquinas según filtros
        machines = request.env['copier.stock'].sudo().search(domain)
        
        return request.render('copier_company.copier_list', {
            'machines': machines,
            'marcas': marcas,
            'selected_marca': int(kwargs.get('marca', 0)),
            'selected_tipo': kwargs.get('tipo', ''),
        })

    @http.route(['/stock-maquinas/<model("copier.stock"):machine>'], type='http', auth='user', website=True)
    def detail_stock(self, machine, **kwargs):
        """Ver detalle de una máquina específica"""
        return request.render('copier_company.copier_detail', {
            'machine': machine,
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
                'sold_date': fields.Datetime.now(),
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