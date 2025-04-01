# -*- coding: utf-8 -*-
import logging
import json
import werkzeug
from datetime import datetime, timedelta
from odoo import http, _, fields
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR, AND

_logger = logging.getLogger(__name__)


class CopierCompanyPortal(CustomerPortal):
    @staticmethod
    def _safe_get_text(field):
        """Método para obtener texto de manera segura"""
        try:
            return str(field) if field else ''
        except Exception as e:
            _logger.warning(f"Error al obtener texto: {e}")
            return ''

    def _prepare_home_portal_values(self, counters):
        """Prepara los valores para la página de inicio del portal, incluyendo el conteo de equipos en alquiler"""
        _logger.info("=== INICIANDO _prepare_home_portal_values ===")
        
        values = super()._prepare_home_portal_values(counters)
        
        # Solo calcular 'equipment_count' si está en counters o si counters está vacío (significa todos)
        if not counters or 'equipment_count' in counters:
            partner = request.env.user.partner_id
            _logger.info("Contando equipos para el partner_id: %s", partner.id)
            
            equipment_count = 0
            
            try:
                if 'copier.company' not in request.env:
                    _logger.error("Modelo 'copier.company' no encontrado en la base de datos")
                else:
                    equipment_count = request.env['copier.company'].sudo().search_count([
                        ('cliente_id', '=', partner.id)
                    ])
                    _logger.info("Equipos encontrados para el partner: %s", equipment_count)
            except Exception as e:
                _logger.exception("¡EXCEPCIÓN en _prepare_home_portal_values!: %s", str(e))
            
            values['equipment_count'] = equipment_count
            
        _logger.info("=== FINALIZANDO _prepare_home_portal_values ===")
        return values
        
    @http.route(['/my/copier/equipments', '/my/copier/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='name', groupby=None, **kw):
        """Muestra la lista de equipos en alquiler del cliente"""
        _logger.info("=== INICIANDO portal_my_equipment ===")
        _logger.info("Parámetros recibidos: page=%s, date_begin=%s, date_end=%s, sortby=%s, filterby=%s, search=%s, search_in=%s", 
                    page, date_begin, date_end, sortby, filterby, search, search_in)
        
        try:
            # Verificaciones iniciales
            if 'copier.company' not in request.env:
                _logger.error("Modelo 'copier.company' no encontrado - Redirigiendo a /my")
                return request.redirect('/my')
            
            # Obtener valores base del portal
            values = self._prepare_portal_layout_values()
            partner = request.env.user.partner_id
            CopierCompany = request.env['copier.company']
            
            _logger.info("Usuario: ID=%s, Nombre=%s, Partner ID=%s", 
                        request.env.user.id, request.env.user.name, partner.id)
            
            # Construir dominio
            domain = [('cliente_id', '=', partner.id)]
            _logger.info("Dominio base de búsqueda: %s", domain)
            
            # Configurar opciones de búsqueda
            searchbar_inputs = {
                'name': {'input': 'name', 'label': _('Máquina')},
                'serie': {'input': 'serie_id', 'label': _('Serie')},
            }
            
            # Configurar filtros
            searchbar_filters = {
                'all': {'label': _('Todos'), 'domain': domain},
                'active': {'label': _('Contratos Activos'), 'domain': AND([domain, [('estado_renovacion', 'in', ['vigente', 'por_vencer'])]])},
                'color': {'label': _('Impresoras Color'), 'domain': AND([domain, [('tipo', '=', 'color')]])},
                'bw': {'label': _('Impresoras B/N'), 'domain': AND([domain, [('tipo', '=', 'monocroma')]])},
            }
            
            # Configurar ordenamiento
            searchbar_sortings = {
                'date': {'label': _('Fecha'), 'order': 'create_date desc'},
                'name': {'label': _('Máquina'), 'order': 'name'},
                'estado': {'label': _('Estado'), 'order': 'estado_renovacion'},
            }
            
            # Aplicar valores por defecto
            if not sortby:
                sortby = 'date'
            sort_order = searchbar_sortings[sortby]['order']
            _logger.info("Ordenamiento aplicado: %s", sort_order)
            
            if not filterby:
                filterby = 'all'
            domain = searchbar_filters[filterby]['domain']
            _logger.info("Filtro aplicado: %s, dominio resultante: %s", filterby, domain)
            
            # Aplicar búsqueda de texto
            if search and search_in:
                _logger.info("Aplicando búsqueda de texto: '%s' en campo '%s'", search, search_in)
                search_domain = []
                if search_in == 'name':
                    search_domain = [('name.name', 'ilike', search)]
                elif search_in == 'serie':
                    search_domain = [('serie_id', 'ilike', search)]
                domain = AND([domain, search_domain])
                _logger.info("Dominio final con búsqueda: %s", domain)
            
            # Contar total de registros
            try:
                equipment_count = CopierCompany.search_count(domain)
                _logger.info("Total de equipos encontrados: %s", equipment_count)
            except Exception as e:
                _logger.exception("Error al contar equipos: %s", str(e))
                equipment_count = 0
            
            # Configurar paginación
            pager = portal_pager(
                url="/my/copier/equipments",
                url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 
                         'filterby': filterby, 'search_in': search_in, 'search': search},
                total=equipment_count,
                page=page,
                step=self._items_per_page
            )
            _logger.info("Paginación configurada: página=%s, offset=%s, límite=%s", 
                        page, pager['offset'], self._items_per_page)
            
            # Obtener registros para esta página
            try:
                equipments = CopierCompany.search(domain, order=sort_order, 
                                                limit=self._items_per_page, offset=pager['offset'])
                _logger.info("Equipos recuperados para esta página: %s", len(equipments))
                
                # Log detallado de equipos encontrados
                for equipment in equipments:
                    _logger.info("Equipo encontrado: ID=%s, Nombre=%s, Cliente=%s, Serie=%s", 
                                equipment.id, 
                                self._safe_get_text(equipment.name.name) if equipment.name else 'Sin nombre',
                                self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                                self._safe_get_text(equipment.serie_id) or 'Sin serie')
            except Exception as e:
                _logger.exception("Error al buscar equipos: %s", str(e))
                equipments = CopierCompany.browse([])
            
            # Preparar valores para renderizar la plantilla
            values.update({
                'equipments': equipments,
                'page_name': 'equipment',
                'pager': pager,
                'default_url': '/my/copier/equipments',
                'searchbar_sortings': searchbar_sortings,
                'searchbar_filters': searchbar_filters,
                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in,
                'sortby': sortby,
                'filterby': filterby,
            })
            
            # Verificar existencia del template
            template = 'copier_company.portal_my_copier_equipments'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect('/my')
            
            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO portal_my_equipment ===")
            return request.render(template, values)
        
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_my_equipment!: %s", str(e))
            return request.redirect('/my')
        
    @http.route(['/my/copier/equipment/<int:equipment_id>'], type='http', auth="user", website=True)
    def portal_my_equipment_detail(self, equipment_id, **kw):
        """Muestra el detalle de un equipo específico"""
        _logger.info("=== INICIANDO portal_my_equipment_detail ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kw: %s", equipment_id, kw)
        
        try:
            # Verificar acceso al documento
            _logger.info("Verificando acceso al equipo ID: %s", equipment_id)
            try:
                equipment_sudo = self._document_check_access('copier.company', equipment_id)
                _logger.info("Acceso verificado para equipo ID: %s", equipment_id)
                _logger.info("Equipo: Nombre=%s, Cliente=%s, Serie=%s", 
                            self._safe_get_text(equipment_sudo.name.name) if equipment_sudo.name else 'Sin nombre',
                            self._safe_get_text(equipment_sudo.cliente_id.name) if equipment_sudo.cliente_id else 'Sin cliente',
                            self._safe_get_text(equipment_sudo.serie_id) or 'Sin serie')
            except (AccessError, MissingError) as e:
                _logger.error("Error de acceso para equipo ID %s: %s", equipment_id, str(e))
                return request.redirect('/my')
                
            values = self._prepare_portal_layout_values()
            values.update({
                'equipment': equipment_sudo,
                'page_name': 'equipment_detail',
            })
            
            # Verificar existencia del template
            template = 'copier_company.portal_my_copier_equipment'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect('/my')
            
            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO portal_my_equipment_detail ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_my_equipment_detail!: %s", str(e))
            return request.redirect('/my')
        
    @http.route(['/my/copier/equipment/<int:equipment_id>/ticket'], type='http', auth="user", website=True)
    def portal_create_equipment_ticket(self, equipment_id, **kw):
        """Redirecciona a la creación de tickets para un equipo específico"""
        _logger.info("=== INICIANDO portal_create_equipment_ticket ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kw: %s", equipment_id, kw)
        
        try:
            # Verificar acceso al documento
            _logger.info("Verificando acceso al equipo ID: %s", equipment_id)
            try:
                equipment_sudo = self._document_check_access('copier.company', equipment_id)
                _logger.info("Acceso verificado para equipo ID: %s", equipment_id)
            except (AccessError, MissingError) as e:
                _logger.error("Error de acceso para equipo ID %s: %s", equipment_id, str(e))
                return request.redirect('/my')
            
            # Redirigir al formulario público de tickets con el ID del equipo
            redirect_url = f'/public/helpdesk_ticket?copier_company_id={equipment_id}'
            _logger.info("Redirigiendo a: %s", redirect_url)
            _logger.info("=== FINALIZANDO portal_create_equipment_ticket ===")
            return request.redirect(redirect_url)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_create_equipment_ticket!: %s", str(e))
            return request.redirect('/my')
        
    @http.route(['/my/copier/equipment/<int:equipment_id>/counters'], type='http', auth="user", website=True)
    def portal_equipment_counters(self, equipment_id, **kw):
        """Muestra el historial de contadores para un equipo específico con gráficos"""
        _logger.info("=== INICIANDO portal_equipment_counters ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kw: %s", equipment_id, kw)
        
        try:
            # Verificar acceso al documento
            _logger.info("Verificando acceso al equipo ID: %s", equipment_id)
            try:
                equipment_sudo = self._document_check_access('copier.company', equipment_id)
                _logger.info("Acceso verificado para equipo ID: %s", equipment_id)
            except (AccessError, MissingError) as e:
                _logger.error("Error de acceso para equipo ID %s: %s", equipment_id, str(e))
                return request.redirect('/my')
                
            values = self._prepare_portal_layout_values()
            
            # Verificar si existe el modelo de contadores
            if 'copier.counter' not in request.env:
                _logger.error("Modelo copier.counter no encontrado")
                counters = []
                chart_data = {}
            else:
                try:
                    _logger.info("Buscando contadores para el equipo ID: %s", equipment_id)
                    
                    # Buscar contadores usando el campo correcto
                    counters = request.env['copier.counter'].search([
                        ('maquina_id', '=', equipment_id)
                    ], order='fecha desc')
                    
                    _logger.info("Contadores encontrados: %s", len(counters))
                    
                    # Preparar datos para el gráfico
                    monthly_data = []
                    yearly_data = []
                    
                    # Diccionarios para agrupar datos
                    month_dict = {}
                    year_dict = {}
                    
                    # Procesar contadores para agrupar por mes y año
                    for counter in counters:
                        # Solo procesar contadores confirmados
                        if counter.state != 'confirmed' and counter.state != 'invoiced':
                            continue
                            
                        # Obtener fecha y extraer año y mes
                        fecha = counter.fecha
                        if not fecha:
                            continue
                            
                        year = fecha.year
                        month = fecha.month
                        month_key = f"{year}-{month:02d}"
                        month_name = counter.mes_facturacion or f"{month:02d}/{year}"
                        
                        # Datos para gráfico mensual
                        if month_key not in month_dict:
                            month_dict[month_key] = {
                                'name': month_name,
                                'bn': 0,
                                'color': 0
                            }
                        
                        month_dict[month_key]['bn'] += counter.total_copias_bn
                        month_dict[month_key]['color'] += counter.total_copias_color
                        
                        # Datos para gráfico anual
                        if year not in year_dict:
                            year_dict[year] = {
                                'name': str(year),
                                'bn': 0,
                                'color': 0
                            }
                        
                        year_dict[year]['bn'] += counter.total_copias_bn
                        year_dict[year]['color'] += counter.total_copias_color
                    
                    # Convertir diccionarios a listas para el gráfico
                    for key in sorted(month_dict.keys()):
                        monthly_data.append(month_dict[key])
                    
                    for key in sorted(year_dict.keys()):
                        yearly_data.append(year_dict[key])
                    
                    # Crear datos para el gráfico
                    chart_data = {
                        'monthly': monthly_data,
                        'yearly': yearly_data
                    }
                    
                    _logger.info("Datos para gráfico preparados: %s meses, %s años", 
                                len(monthly_data), len(yearly_data))
                    
                except Exception as e:
                    _logger.exception("Error al buscar contadores o preparar gráficos: %s", str(e))
                    counters = request.env['copier.counter'].browse([])
                    chart_data = {'monthly': [], 'yearly': []}
            
            values.update({
                'equipment': equipment_sudo,
                'counters': counters,
                'page_name': 'equipment_counters',
                'today': fields.Date.today(),
                'chart_data': json.dumps(chart_data)
            })
            
            # Verificar existencia del template
            template = 'copier_company.portal_my_copier_counters'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/my/copier/equipment/{equipment_id}')
            
            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO portal_equipment_counters ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_equipment_counters!: %s", str(e))
            return request.redirect('/my')
    
    # Ruta para el acceso público desde QR
    @http.route(['/public/helpdesk_ticket'], type='http', auth="public", website=True)
    def public_create_ticket(self, copier_company_id=None, **kw):
        """Permite crear tickets desde un código QR sin necesidad de inicio de sesión"""
        _logger.info("=== INICIANDO public_create_ticket ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s, kw: %s", copier_company_id, kw)
        
        try:
            if not copier_company_id:
                _logger.error("No se proporcionó ID de equipo - Redirigiendo a home")
                return request.redirect('/')
                
            # Buscar el equipo (modo sudo porque es acceso público)
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                _logger.error("Equipo ID %s no encontrado - Redirigiendo a home", copier_company_id)
                return request.redirect('/')
                
            _logger.info("Equipo encontrado: ID=%s, Nombre=%s, Cliente=%s", 
                        equipment.id, 
                        self._safe_get_text(equipment.name.name) if equipment.name else 'Sin nombre',
                        self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente')
                
            values = {
                'equipment': equipment,
                'page_title': _('Crear ticket de soporte'),
            }
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST")
                
                # Capturar datos del formulario
                description = kw.get('description', '')
                name = kw.get('name', '')
                email = kw.get('email', '')
                phone = kw.get('phone', '')
                
                _logger.info("Datos del formulario - Nombre: %s, Email: %s, Teléfono: %s", 
                            name, email, phone)
                
                if not name or not email or not description:
                    _logger.warning("Datos incompletos en el formulario")
                    values['error_message'] = _("Por favor completa todos los campos obligatorios.")
                    return request.render("copier_company.portal_public_create_ticket", values)
                
                # Buscar o crear partner
                partner = False
                if email:
                    partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
                    
                    if partner:
                        _logger.info("Partner encontrado con email %s: ID=%s, Nombre=%s", 
                                    email, partner.id, partner.name)
                    elif name:
                        try:
                            _logger.info("Creando nuevo partner para: %s <%s>", name, email)
                            partner = request.env['res.partner'].sudo().create({
                                'name': name,
                                'email': email,
                                'phone': phone,
                            })
                            _logger.info("Partner creado: ID=%s", partner.id)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                
                # Crear ticket
                if 'helpdesk.ticket' in request.env and partner:
                    try:
                        _logger.info("Creando ticket para partner ID: %s", partner.id)
                        
                        # Preparar valores para el ticket
                        ticket_vals = {
                            'partner_id': partner.id,
                            'name': f"Soporte para {self._safe_get_text(equipment.name.name) if equipment.name else 'equipo'} - {self._safe_get_text(equipment.serie_id) or 'Sin serie'}",
                            'description': description,
                        }
                        
                        # Agregar campos personalizados si existen
                        fields_info = request.env['helpdesk.ticket'].fields_get()
                        _logger.info("Campos disponibles en helpdesk.ticket: %s", list(fields_info.keys()))
                        
                        if 'producto_id' in fields_info:
                            ticket_vals['producto_id'] = equipment.id
                            _logger.info("Agregando campo producto_id=%s", equipment.id)
                            
                        if 'serie_id' in fields_info and equipment.serie_id:
                            ticket_vals['serie_id'] = equipment.serie_id
                            _logger.info("Agregando campo serie_id=%s", equipment.serie_id)
                        
                        _logger.info("Valores finales del ticket: %s", ticket_vals)
                        ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)
                        _logger.info("Ticket creado exitosamente: ID=%s", ticket.id)
                        
                        values['success_message'] = _("¡Ticket creado exitosamente! Te contactaremos pronto.")
                    except Exception as e:
                        _logger.exception("Error al crear ticket: %s", str(e))
                        values['error_message'] = _("Ocurrió un error al crear el ticket. Por favor intenta nuevamente.")
                else:
                    _logger.warning("No se pudo crear ticket: módulo helpdesk no instalado o partner no creado")
                    values['error_message'] = _("No se pudo procesar la solicitud. Por favor contacta directamente con soporte.")
            
            # Verificar existencia del template
            template = 'copier_company.portal_public_create_ticket'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return werkzeug.exceptions.NotFound()
            
            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO public_create_ticket ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_create_ticket!: %s", str(e))
            return request.redirect('/')

    # Método de diagnóstico para verificar la estructura del portal
    @http.route(['/my/copier/diagnostico'], type='http', auth="user", website=True)
    def portal_diagnostic(self, **kw):
        """Página de diagnóstico para verificar la estructura del portal y los modelos"""
        _logger.info("=== INICIANDO portal_diagnostic ===")
        
        try:
            partner = request.env.user.partner_id
            result = {
                'usuario': {
                    'id': request.env.user.id,
                    'nombre': request.env.user.name,
                    'partner_id': partner.id,
                    'partner_name': partner.name,
                    'email': partner.email,
                },
                'modelos': {},
                'templates': {},
                'equipos': [],
                'errores': [],
            }
            
            # Verificar modelos
            for model_name in ['copier.company', 'copier.counter', 'helpdesk.ticket']:
                if model_name in request.env:
                    result['modelos'][model_name] = {
                        'status': 'OK',
                        'campos': list(request.env[model_name].fields_get().keys())[:20]  # Limitar a 20 campos
                    }
                else:
                    result['modelos'][model_name] = {
                        'status': 'ERROR - No encontrado'
                    }
                    result['errores'].append(f"Modelo {model_name} no encontrado")
            
            # Verificar templates
            for template_key in [
                'copier_company.portal_my_copier_equipments',
                'copier_company.portal_my_copier_equipment',
                'copier_company.portal_my_copier_counters',
                'copier_company.portal_public_create_ticket'
            ]:
                template = request.env['ir.ui.view'].sudo().search([('key', '=', template_key)], limit=1)
                if template:
                    result['templates'][template_key] = {
                        'status': 'OK',
                        'id': template.id,
                        'name': template.name,
                    }
                else:
                    result['templates'][template_key] = {
                        'status': 'ERROR - No encontrado'
                    }
                    result['errores'].append(f"Template {template_key} no encontrado")
            
            # Verificar acceso a equipos
            if 'copier.company' in request.env:
                equipments = request.env['copier.company'].sudo().search([('cliente_id', '=', partner.id)], limit=10)
                for equip in equipments:
                    result['equipos'].append({
                        'id': equip.id,
                        'nombre': self._safe_get_text(equip.name.name) if equip.name else 'Sin nombre',
                        'serie': self._safe_get_text(equip.serie_id) or 'Sin serie',
                        'cliente_id': equip.cliente_id.id if equip.cliente_id else False,
                        'cliente_nombre': self._safe_get_text(equip.cliente_id.name) if equip.cliente_id else 'Sin cliente',
                    })
                
                if not equipments:
                    result['errores'].append(f"No se encontraron equipos para el partner_id {partner.id}")
            
            # Generar respuesta HTML
            html = """
            <html>
                <head>
                    <title>Diagnóstico de Portal Copier</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1, h2 { color: #1a73e8; }
                        .section { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                        .success { color: green; }
                        .error { color: red; font-weight: bold; }
                        table { border-collapse: collapse; width: 100%; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    <h1>Diagnóstico de Portal Copier</h1>
                    <div class="section">
                        <h2>Información de Usuario</h2>
                        <table>
                            <tr><th>Usuario ID</th><td>{}</td></tr>
                            <tr><th>Nombre</th><td>{}</td></tr>
                            <tr><th>Partner ID</th><td>{}</td></tr>
                            <tr><th>Partner Nombre</th><td>{}</td></tr>
                            <tr><th>Email</th><td>{}</td></tr>
                        </table>
                    </div>
            """.format(
                result['usuario']['id'],
                result['usuario']['nombre'],
                result['usuario']['partner_id'],
                result['usuario']['partner_name'],
                result['usuario']['email']
            )
            
            # Sección de modelos
            html += """
                    <div class="section">
                        <h2>Verificación de Modelos</h2>
                        <table>
                            <tr><th>Modelo</th><th>Estado</th><th>Campos (muestra)</th></tr>
            """
            
            for model_name, model_info in result['modelos'].items():
                status_class = 'success' if model_info['status'] == 'OK' else 'error'
                campos_str = ', '.join(model_info.get('campos', []))
                html += f"""
                            <tr>
                                <td>{model_name}</td>
                                <td class="{status_class}">{model_info['status']}</td>
                                <td>{campos_str}</td>
                            </tr>
                """
            
            html += """
                        </table>
                    </div>
            """
            
            # Sección de templates
            html += """
                    <div class="section">
                        <h2>Verificación de Templates</h2>
                        <table>
                            <tr><th>Template</th><th>Estado</th><th>ID</th><th>Nombre</th></tr>
            """
            
            for template_key, template_info in result['templates'].items():
                status_class = 'success' if template_info['status'] == 'OK' else 'error'
                template_id = template_info.get('id', 'N/A')
                template_name = template_info.get('name', 'N/A')
                html += f"""
                            <tr>
                                <td>{template_key}</td>
                                <td class="{status_class}">{template_info['status']}</td>
                                <td>{template_id}</td>
                                <td>{template_name}</td>
                            </tr>
                """
            
            html += """
                        </table>
                    </div>
            """
            
            # Sección de equipos
            html += """
                    <div class="section">
                        <h2>Equipos del Usuario</h2>
                        <table>
                            <tr><th>ID</th><th>Nombre</th><th>Serie</th><th>Cliente ID</th><th>Cliente Nombre</th></tr>
            """
            
            if result['equipos']:
                for equip in result['equipos']:
                    html += f"""
                                <tr>
                                    <td>{equip['id']}</td>
                                    <td>{equip['nombre']}</td>
                                    <td>{equip['serie']}</td>
                                    <td>{equip['cliente_id']}</td>
                                    <td>{equip['cliente_nombre']}</td>
                                </tr>
                    """
            else:
                html += """
                            <tr>
                                <td colspan="5" class="error">No se encontraron equipos para este usuario</td>
                            </tr>
                """
            
            html += """
                        </table>
                    </div>
            """
            
            # Sección de errores
            html += """
                    <div class="section">
                        <h2>Errores Detectados</h2>
            """
            
            if result['errores']:
                html += "<ul>"
                for error in result['errores']:
                    html += f"<li class='error'>{error}</li>"
                html += "</ul>"
            else:
                html += "<p class='success'>No se detectaron errores</p>"
            
            html += """
                    </div>
                    <div class="section">
                        <h2>Acciones</h2>
                        <p><a href="/my">Volver al Portal</a></p>
                        <p><a href="/my/copier/equipments">Ver mis equipos</a></p>
                    </div>
                </body>
            </html>
            """
            
            _logger.info("Diagnóstico completado con %s errores", len(result['errores']))
            _logger.info("=== FINALIZANDO portal_diagnostic ===")
            return request.make_response(html)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_diagnostic!: %s", str(e))
            error_html = f"""
            <html>
                <head>
                    <title>Error en Diagnóstico</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ color: red; }}
                        .error {{ color: red; font-weight: bold; }}
                        .section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>Error al generar diagnóstico</h1>
                    <div class="section">
                        <p class="error">{str(e)}</p>
                        <p><a href="/my">Volver al Portal</a></p>
                    </div>
                </body>
            </html>
            """
            return request.make_response(error_html)

    # Método adicional para verificar la estructura del portal via JSON
    @http.route(['/my/copier/api/verify'], type='http', auth="user", website=True)
    def portal_api_verify(self, **kw):
        """API para verificar el estado del portal (devuelve JSON)"""
        _logger.info("=== INICIANDO portal_api_verify ===")
        
        try:
            partner = request.env.user.partner_id
            result = {
                'timestamp': fields.Datetime.now().isoformat(),
                'user': {
                    'id': request.env.user.id,
                    'name': request.env.user.name,
                    'partner_id': partner.id,
                },
                'models': {},
                'templates': {},
                'equipment_count': 0,
                'errors': [],
                'status': 'success'
            }
            
            # Verificar modelos
            for model_name in ['copier.company', 'copier.counter', 'helpdesk.ticket']:
                if model_name in request.env:
                    model_fields = list(request.env[model_name].fields_get().keys())
                    result['models'][model_name] = {
                        'status': 'ok',
                        'fields_count': len(model_fields),
                        'sample_fields': model_fields[:5]
                    }
                else:
                    result['models'][model_name] = {
                        'status': 'error',
                        'message': f"Model {model_name} not found"
                    }
                    result['errors'].append(f"Model {model_name} not found")
            
            # Verificar templates
            for template_key in [
                'copier_company.portal_my_copier_equipments',
                'copier_company.portal_my_copier_equipment',
                'copier_company.portal_my_copier_counters'
            ]:
                template = request.env['ir.ui.view'].sudo().search([('key', '=', template_key)], limit=1)
                if template:
                    result['templates'][template_key] = {
                        'status': 'ok',
                        'id': template.id,
                        'name': template.name,
                    }
                else:
                    result['templates'][template_key] = {
                        'status': 'error',
                        'message': f"Template {template_key} not found"
                    }
                    result['errors'].append(f"Template {template_key} not found")
            
            # Contar equipos
            if 'copier.company' in request.env:
                equipment_count = request.env['copier.company'].sudo().search_count([
                    ('cliente_id', '=', partner.id)
                ])
                result['equipment_count'] = equipment_count
                
                if equipment_count == 0:
                    result['errors'].append(f"No equipment found for partner_id {partner.id}")
            else:
                result['errors'].append("Cannot count equipment: model copier.company not found")
            
            if result['errors']:
                result['status'] = 'warning'
            
            _logger.info("Verificación API completada con %s errores", len(result['errors']))
            _logger.info("=== FINALIZANDO portal_api_verify ===")
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_api_verify!: %s", str(e))
            error_result = {
                'timestamp': fields.Datetime.now().isoformat(),
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_result),
                headers=[('Content-Type', 'application/json')]
            )