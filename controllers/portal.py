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
import base64
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
            _logger.info("Verificando acceso al equipo ID: %s", equipment_id)
            try:
                equipment_sudo = self._document_check_access('copier.company', equipment_id)
                _logger.info("Acceso verificado para equipo ID: %s", equipment_id)
            except (AccessError, MissingError) as e:
                _logger.error("Error de acceso para equipo ID %s: %s", equipment_id, str(e))
                return request.redirect('/my')

            values = self._prepare_portal_layout_values()

            if 'copier.counter' not in request.env:
                _logger.error("Modelo copier.counter no encontrado")
                counters = []
                chart_data = {}
            else:
                try:
                    _logger.info("Buscando contadores para el equipo ID: %s", equipment_id)

                    counters = request.env['copier.counter'].search([
                        ('maquina_id', '=', equipment_id)
                    ], order='fecha desc')

                    _logger.info("Contadores encontrados: %s", len(counters))

                    # Preparar datos para el gráfico general
                    monthly_data = []
                    yearly_data = []
                    month_dict = {}
                    year_dict = {}

                    for counter in counters:
                        if counter.state not in ('confirmed', 'invoiced'):
                            continue

                        fecha = counter.fecha
                        if not fecha:
                            continue

                        year = fecha.year
                        month = fecha.month
                        month_key = f"{year}-{month:02d}"
                        month_name = counter.mes_facturacion or f"{month:02d}/{year}"

                        if month_key not in month_dict:
                            month_dict[month_key] = {
                                'name': month_name,
                                'bn': 0,
                                'color': 0
                            }
                        month_dict[month_key]['bn'] += counter.total_copias_bn
                        month_dict[month_key]['color'] += counter.total_copias_color

                        if year not in year_dict:
                            year_dict[year] = {
                                'name': str(year),
                                'bn': 0,
                                'color': 0
                            }
                        year_dict[year]['bn'] += counter.total_copias_bn
                        year_dict[year]['color'] += counter.total_copias_color

                    for key in sorted(month_dict.keys()):
                        monthly_data.append(month_dict[key])
                    for key in sorted(year_dict.keys()):
                        yearly_data.append(year_dict[key])

                    # Gráfico del último contador por usuario
                    chart_user_data = []
                    if counters:
                        first = counters[0]
                        if first.informe_por_usuario and first.usuario_detalle_ids:
                            for user_detail in first.usuario_detalle_ids:
                                chart_user_data.append({
                                    'name': user_detail.usuario_id.name,
                                    'copies': user_detail.cantidad_copias
                                })

                    # Gráfico mensual por usuario acumulado
                    from collections import defaultdict
                    monthly_user_data = defaultdict(lambda: defaultdict(int))

                    for counter in counters:
                        if counter.state not in ('confirmed', 'invoiced'):
                            continue

                        mes = counter.mes_facturacion or counter.fecha.strftime('%B %Y')
                        for detalle in counter.usuario_detalle_ids:
                            nombre = detalle.usuario_id.name or 'Sin nombre'
                            monthly_user_data[mes][nombre] += detalle.cantidad_copias

                    labels = sorted(monthly_user_data.keys())
                    usuarios_unicos = sorted({u for datos in monthly_user_data.values() for u in datos})

                    datasets = []
                    for usuario in usuarios_unicos:
                        datasets.append({
                            'label': usuario,
                            'data': [monthly_user_data[mes].get(usuario, 0) for mes in labels]
                        })

                    # Consolidar todos los datos
                    chart_data = {
                        'monthly': monthly_data,
                        'yearly': yearly_data,
                        'by_user': chart_user_data,
                        'by_user_monthly': {
                            'labels': labels,
                            'datasets': datasets
                        }
                    }

                    _logger.info("Datos para gráfico preparados: %s meses, %s años", len(monthly_data), len(yearly_data))

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
        """Permite crear tickets desde el menú de equipos"""
        _logger.info("=== INICIANDO public_create_ticket ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s, kw: %s", copier_company_id, kw)
        
        try:
            if not copier_company_id:
                _logger.error("No se proporcionó ID de equipo")
                return request.redirect('/')
                    
            # Buscar el equipo
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                _logger.error("Equipo ID %s no encontrado", copier_company_id)
                return request.redirect('/')
                    
            _logger.info("Equipo encontrado: ID=%s, Nombre=%s, Cliente=%s", 
                        equipment.id, 
                        self._safe_get_text(equipment.name.name) if equipment.name else 'Sin nombre',
                        self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente')
            
            # ✅ PREPARAR DATOS COMPLETOS DEL EQUIPO Y CLIENTE
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.mobile) or self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or 'Sin sede',
                'ip': self._safe_get_text(equipment.ip_id) or 'Sin IP',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
                'contacto_equipo': self._safe_get_text(equipment.contacto) or '',
                'celular_equipo': self._safe_get_text(equipment.celular) or '',
                'correo_equipo': self._safe_get_text(equipment.correo) or ''
            }
            
            _logger.info("Equipment_data preparado: %s", equipment_data)
            
            # ✅ VALORES PARA EL TEMPLATE - INCLUIR DATOS DE CONTACTO
            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'page_title': _('Reportar Problema Técnico'),
                # ✅ DATOS DE CONTACTO PREDETERMINADOS PARA JAVASCRIPT
                'default_contact_name': equipment_data['cliente_name'],
                'default_contact_email': equipment_data['cliente_email'],
                'default_contact_phone': equipment_data['cliente_phone'],
            }
            
            _logger.info("Values preparados para template: %s", {k: v for k, v in values.items() if k not in ['equipment']})
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST de ticket")
                
                try:
                    # Capturar datos del formulario
                    form_data = {
                        'producto_id': int(copier_company_id),
                        'nombre_reporta': kw.get('nombre_reporta', '').strip(),
                        'partner_email': kw.get('email', '').strip(),
                        'celular_reporta': kw.get('celular_reporta', '').strip(),
                        'problem_type': kw.get('problem_type', ''),
                        'urgency': kw.get('urgency', 'medium'),
                        'additional_description': kw.get('additional_description', '').strip(),
                        'image': kw.get('image'),
                    }
                    
                    _logger.info("Datos del formulario capturados: %s", 
                            {k: v for k, v in form_data.items() if k != 'image'})
                    
                    # Validaciones básicas
                    if not form_data['nombre_reporta'] or not form_data['partner_email'] or not form_data['problem_type']:
                        _logger.warning("Datos incompletos en el formulario de ticket")
                        values['error_message'] = _("Por favor completa todos los campos obligatorios.")
                        return request.render("copier_company.public_helpdesk_ticket_form", values)
                    
                    # Validar email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
                    if not re.match(email_pattern, form_data['partner_email']):
                        _logger.warning("Email inválido en ticket: %s", form_data['partner_email'])
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.public_helpdesk_ticket_form", values)
                    
                    # Buscar o crear partner
                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['partner_email'])], limit=1)
                    if partner:
                        _logger.info("Partner encontrado: ID=%s, Nombre=%s", partner.id, partner.name)
                        # Actualizar datos si han cambiado
                        update_vals = {}
                        if partner.name != form_data['nombre_reporta']:
                            update_vals['name'] = form_data['nombre_reporta']
                        if form_data['celular_reporta'] and not partner.mobile:
                            update_vals['mobile'] = form_data['celular_reporta']
                        if update_vals:
                            partner.sudo().write(update_vals)
                            _logger.info("Partner actualizado con: %s", update_vals)
                    else:
                        try:
                            partner = request.env['res.partner'].sudo().create({
                                'name': form_data['nombre_reporta'],
                                'email': form_data['partner_email'],
                                'mobile': form_data['celular_reporta'],
                                'is_company': False
                            })
                            _logger.info("Partner creado: ID=%s", partner.id)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                            values['error_message'] = _("Error al procesar los datos del contacto.")
                            return request.render("copier_company.public_helpdesk_ticket_form", values)
                    
                    # Crear ticket
                    if 'helpdesk.ticket' in request.env and partner:
                        try:
                            _logger.info("Creando ticket para partner ID: %s", partner.id)
                            
                            # Mapeo de nombres de problemas
                            problem_names = {
                                'printing': 'Problemas de Impresión',
                                'scanning': 'Problemas de Escaneo',
                                'paper_jam': 'Atasco de Papel',
                                'toner': 'Problemas de Toner',
                                'network': 'Problemas de Red',
                                'maintenance': 'Mantenimiento',
                                'general': 'Otro Problema'
                            }
                            
                            problem_name = problem_names.get(form_data['problem_type'], 'Problema Técnico')
                            
                            # Preparar descripción del ticket
                            description_parts = []
                            
                            # Descripción automática según el tipo
                            auto_descriptions = {
                                'printing': 'El equipo presenta problemas de impresión. Se requiere revisión técnica para identificar y solucionar la falla en el sistema de impresión.',
                                'scanning': 'Se reportan problemas en la función de escaneo del equipo. Es necesaria una revisión técnica del módulo de escaneado.',
                                'paper_jam': 'El equipo presenta atascos de papel frecuentes. Se requiere revisión del sistema de alimentación de papel y limpieza de rodillos.',
                                'toner': 'Problemas relacionados con el toner o calidad de impresión. Puede requerir reemplazo de toner o revisión del sistema de impresión.',
                                'network': 'El equipo presenta problemas de conectividad de red. Se requiere revisión de la configuración de red y conectividad.',
                                'maintenance': 'Se solicita mantenimiento preventivo del equipo según el plan de mantenimiento programado.',
                                'general': 'Problema general que requiere evaluación técnica específica.'
                            }
                            
                            description_parts.append(auto_descriptions.get(form_data['problem_type'], 'Problema técnico reportado.'))
                            
                            # Agregar descripción adicional si existe
                            if form_data['additional_description']:
                                description_parts.append(f"\n\nDescripción adicional proporcionada por el usuario:\n{form_data['additional_description']}")
                            
                            # Información del equipo
                            description_parts.append(f"\n\nInformación del Equipo:")
                            description_parts.append(f"- Equipo: {equipment_data['name']}")
                            description_parts.append(f"- Serie: {equipment_data['serie']}")
                            description_parts.append(f"- Marca: {equipment_data['marca']}")
                            description_parts.append(f"- Ubicación: {equipment_data['ubicacion']}")
                            description_parts.append(f"- Sede: {equipment_data['sede']}")
                            description_parts.append(f"- IP: {equipment_data['ip']}")
                            description_parts.append(f"- Tipo: {equipment_data['tipo']}")
                            
                            # Información de contacto
                            description_parts.append(f"\n\nInformación de Contacto:")
                            description_parts.append(f"- Nombre: {form_data['nombre_reporta']}")
                            description_parts.append(f"- Email: {form_data['partner_email']}")
                            description_parts.append(f"- Teléfono: {form_data['celular_reporta']}")
                            
                            ticket_description = '\n'.join(description_parts)
                            
                            # Preparar valores para el ticket
                            ticket_vals = {
                                'partner_id': partner.id,
                                'name': f"{problem_name} - {equipment_data['name']} (Serie: {equipment_data['serie']})",
                                'description': ticket_description,
                                
                                # Campos personalizados si existen en el modelo
                                'urgency': form_data['urgency'],
                            }
                            
                            # Agregar campos personalizados si existen en el modelo
                            ticket_model = request.env['helpdesk.ticket']
                            if hasattr(ticket_model, '_fields'):
                                if 'producto_id' in ticket_model._fields:
                                    ticket_vals['producto_id'] = equipment.id
                                if 'nombre_reporta' in ticket_model._fields:
                                    ticket_vals['nombre_reporta'] = form_data['nombre_reporta']
                                if 'celular_reporta' in ticket_model._fields:
                                    ticket_vals['celular_reporta'] = form_data['celular_reporta']
                                if 'problem_type' in ticket_model._fields:
                                    ticket_vals['problem_type'] = form_data['problem_type']
                                if 'additional_description' in ticket_model._fields:
                                    ticket_vals['additional_description'] = form_data['additional_description']
                            
                            # Manejar imagen si se subió
                            if form_data['image']:
                                try:
                                    image_data = form_data['image'].read()
                                    if hasattr(ticket_model, '_fields') and 'image' in ticket_model._fields:
                                        ticket_vals['image'] = base64.b64encode(image_data)
                                    _logger.info("Imagen adjuntada al ticket")
                                except Exception as e:
                                    _logger.error("Error procesando imagen: %s", str(e))
                            
                            _logger.info("Valores del ticket: %s", {k: v for k, v in ticket_vals.items() if k not in ['image', 'description']})
                            ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)
                            _logger.info("Ticket creado exitosamente: ID=%s", ticket.id)
                            
                            # Mensaje de éxito
                            urgency_names = {
                                'low': 'Baja',
                                'medium': 'Media',
                                'high': 'Alta',
                                'urgent': 'Crítica'
                            }
                            
                            success_message = _(
                                "¡Ticket de soporte creado exitosamente!<br/><br/>"
                                "<strong>Número de ticket:</strong> #{}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Tipo de problema:</strong> {}<br/>"
                                "<strong>Urgencia:</strong> {}<br/><br/>"
                                "Nuestro equipo técnico se pondrá en contacto contigo pronto.<br/>"
                                "Recibirás actualizaciones en: {}"
                            ).format(
                                ticket.id,
                                equipment_data['name'],
                                equipment_data['serie'],
                                problem_name,
                                urgency_names.get(form_data['urgency'], 'Media'),
                                form_data['partner_email']
                            )
                            
                            values['success_message'] = success_message
                            values['ticket'] = ticket
                            
                            # Enviar notificación al equipo técnico
                            try:
                                self._send_ticket_notification(ticket, equipment_data, form_data['nombre_reporta'], form_data['partner_email'], problem_name)
                            except Exception as e:
                                _logger.error("Error enviando notificación: %s", str(e))
                            
                        except Exception as e:
                            _logger.exception("Error al crear ticket: %s", str(e))
                            values['error_message'] = _("Ocurrió un error al crear el ticket. Por favor intenta nuevamente.")
                    else:
                        _logger.warning("No se pudo crear ticket: módulo helpdesk no instalado o partner no encontrado")
                        values['error_message'] = _("El servicio de tickets no está disponible.")
                        
                except Exception as e:
                    _logger.exception("Error procesando formulario: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario.")
            
            # Verificar template
            template = 'copier_company.public_helpdesk_ticket_form'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("Template %s no encontrado", template)
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')
            
            _logger.info("Renderizando template de ticket: %s", template)
            _logger.info("=== FINALIZANDO public_create_ticket ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("Error general en public_create_ticket: %s", str(e))
            return request.redirect('/')

    def _send_ticket_notification(self, ticket, equipment_data, contact_name, contact_email, problem_description):
        """Envía notificación por email para nuevo ticket"""
        _logger.info("=== INICIANDO _send_ticket_notification para ticket %s ===", ticket.id)
        
        try:
            # Emails del equipo técnico
            technical_emails = [
                'soporte@copiercompanysac.com',
                'tecnico@copiercompanysac.com'
            ]
            
            email_body = f"""
            <h2>🎫 Nuevo Ticket de Soporte Técnico</h2>
            
            <h3>📋 Información del Ticket</h3>
            <p><strong>ID del Ticket:</strong> #{ticket.id}</p>
            <p><strong>Fecha:</strong> {ticket.create_date.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Tipo de Problema:</strong> {problem_description}</p>
            
            <h3>🖨️ Información del Equipo</h3>
            <p><strong>Equipo:</strong> {equipment_data['name']}</p>
            <p><strong>Serie:</strong> {equipment_data['serie']}</p>
            <p><strong>Marca:</strong> {equipment_data['marca']}</p>
            <p><strong>Tipo:</strong> {equipment_data['tipo']}</p>
            <p><strong>Cliente:</strong> {equipment_data['cliente_name']}</p>
            <p><strong>Ubicación:</strong> {equipment_data['ubicacion']}</p>
            <p><strong>Sede:</strong> {equipment_data['sede']}</p>
            <p><strong>IP:</strong> {equipment_data['ip']}</p>
            
            <h3>👤 Información del Contacto</h3>
            <p><strong>Nombre:</strong> {contact_name}</p>
            <p><strong>Email:</strong> {contact_email}</p>
            
            <h3>🔧 Descripción del Problema</h3>
            <p>{ticket.description.replace(chr(10), '<br/>')}</p>
            
            <h3>⚡ Acciones</h3>
            <ul>
                <li><a href="{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={ticket.id}&model=helpdesk.ticket&view_type=form">Ver Ticket en el Sistema</a></li>
                <li>Contactar al cliente para más información</li>
                <li>Asignar técnico responsable</li>
                <li>Programar visita técnica si es necesario</li>
            </ul>
            
            <hr/>
            <p><small>Ticket generado automáticamente desde el portal público de Copier Company.</small></p>
            """
            
            for email in technical_emails:
                try:
                    mail_values = {
                        'subject': f'🎫 Nuevo Ticket #{ticket.id} - {equipment_data["name"]} - {problem_description}',
                        'email_to': email,
                        'email_from': 'noreply@copiercompanysac.com',
                        'body_html': email_body,
                        'auto_delete': False,
                    }
                    
                    mail = request.env['mail.mail'].sudo().create(mail_values)
                    mail.send()
                    _logger.info("Notificación de ticket enviada a: %s", email)
                    
                except Exception as e:
                    _logger.error("Error enviando notificación de ticket a %s: %s", email, str(e))
            
        except Exception as e:
            _logger.exception("Error en _send_ticket_notification: %s", str(e))

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










# Agregar estas rutas al archivo controllers.py existente

    @http.route(['/public/equipment_menu'], type='http', auth="public", website=True)
    def public_equipment_menu(self, copier_company_id=None, **kw):
        """Página principal de menú para el equipo - carga datos automáticamente"""
        _logger.info("=== INICIANDO public_equipment_menu ===")
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
                
            _logger.info("Equipo encontrado: ID=%s, Nombre=%s, Cliente=%s, Serie=%s, Ubicación=%s", 
                        equipment.id, 
                        self._safe_get_text(equipment.name.name) if equipment.name else 'Sin nombre',
                        self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                        self._safe_get_text(equipment.serie_id) or 'Sin serie',
                        self._safe_get_text(equipment.ubicacion) or 'Sin ubicación')
                    
            values = {
                'equipment': equipment,
                'page_title': _('Servicios para su Equipo'),
                'company_name': 'Copier Company',
                'company_phone': '+51 999 999 999',  # Configurar según tus datos
                'company_email': 'info@copiercompanysac.com',
                'company_website': 'https://copiercompanysac.com'
            }
            
            # Verificar existencia del template
            template = 'copier_company.portal_equipment_menu'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect('/')
            
            _logger.info("Renderizando template de menú: %s", template)
            _logger.info("=== FINALIZANDO public_equipment_menu ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_equipment_menu!: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/remote_assistance'], type='http', auth="public", website=True)
    def public_remote_assistance(self, copier_company_id=None, **kw):
        """Formulario de asistencia remota con datos pre-cargados del equipo"""
        _logger.info("=== INICIANDO public_remote_assistance ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s, kw: %s", copier_company_id, kw)
        
        try:
            if not copier_company_id:
                _logger.error("No se proporcionó ID de equipo")
                return request.redirect('/')
                
            # Buscar el equipo
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                _logger.error("Equipo ID %s no encontrado", copier_company_id)
                return request.redirect('/')
                
            _logger.info("Cargando formulario de asistencia remota para equipo: %s", equipment.name.name if equipment.name else 'Sin nombre')
            
            # Preparar datos pre-cargados del equipo
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.mobile) or self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'ip': self._safe_get_text(equipment.ip_id) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
                'contacto_equipo': self._safe_get_text(equipment.contacto) or '',
                'celular_equipo': self._safe_get_text(equipment.celular) or '',
                'correo_equipo': self._safe_get_text(equipment.correo) or ''
            }
            
            _logger.info("Datos del equipo pre-cargados: %s", equipment_data)
            
            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'page_title': _('Solicitar Asistencia Remota'),
            }
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST de asistencia remota")
                
                try:
                    # Capturar datos del formulario
                    form_data = {
                        'equipment_id': int(copier_company_id),
                        'contact_name': kw.get('contact_name', '').strip(),
                        'contact_email': kw.get('contact_email', '').strip(),
                        'contact_phone': kw.get('contact_phone', '').strip(),
                        'assistance_type': kw.get('assistance_type', 'general'),
                        'problem_description': kw.get('problem_description', '').strip(),
                        'priority': kw.get('priority', 'medium'),
                        
                        # Datos de acceso remoto (opcionales)
                        'anydesk_id': kw.get('anydesk_id', '').strip(),
                        'username': kw.get('username', '').strip(),
                        'user_password': kw.get('user_password', '').strip(),
                        
                        # Para escáneres por correo (opcionales)
                        'scanner_email': kw.get('scanner_email', '').strip(),
                        'scanner_password': kw.get('scanner_password', '').strip(),
                    }
                    
                    _logger.info("Datos del formulario capturados: %s", {k: v if k not in ['user_password', 'scanner_password'] else '***' for k, v in form_data.items()})
                    
                    # Validaciones
                    if not form_data['contact_name']:
                        _logger.warning("Nombre de contacto requerido")
                        values['error_message'] = _("El nombre de contacto es requerido.")
                        return request.render("copier_company.portal_remote_assistance", values)
                    
                    if not form_data['contact_email']:
                        _logger.warning("Email de contacto requerido")
                        values['error_message'] = _("El email de contacto es requerido.")
                        return request.render("copier_company.portal_remote_assistance", values)
                    
                    if not form_data['problem_description']:
                        _logger.warning("Descripción del problema requerida")
                        values['error_message'] = _("La descripción del problema es requerida.")
                        return request.render("copier_company.portal_remote_assistance", values)
                    
                    # Validar email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, form_data['contact_email']):
                        _logger.warning("Email inválido: %s", form_data['contact_email'])
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_remote_assistance", values)
                    
                    # Validaciones específicas según tipo de asistencia
                    if form_data['assistance_type'] == 'scanner_email':
                        if not form_data['scanner_email']:
                            _logger.warning("Email del escáner requerido para configuración de escáner")
                            values['error_message'] = _("Para configuración de escáner por email, debe proporcionar el email del escáner.")
                            return request.render("copier_company.portal_remote_assistance", values)
                    
                    # Buscar o crear partner basado en email
                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['contact_email'])], limit=1)
                    if partner:
                        _logger.info("Partner encontrado para email %s: ID=%s, Nombre=%s", form_data['contact_email'], partner.id, partner.name)
                        # Actualizar datos si es necesario
                        if partner.name != form_data['contact_name']:
                            partner.sudo().write({'name': form_data['contact_name']})
                            _logger.info("Nombre del partner actualizado a: %s", form_data['contact_name'])
                        if form_data['contact_phone'] and not partner.mobile:
                            partner.sudo().write({'mobile': form_data['contact_phone']})
                            _logger.info("Teléfono del partner actualizado a: %s", form_data['contact_phone'])
                    else:
                        try:
                            partner = request.env['res.partner'].sudo().create({
                                'name': form_data['contact_name'],
                                'email': form_data['contact_email'],
                                'mobile': form_data['contact_phone'],
                                'is_company': False
                            })
                            _logger.info("Nuevo partner creado: ID=%s, Nombre=%s, Email=%s", partner.id, partner.name, partner.email)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                            values['error_message'] = _("Error al procesar los datos del contacto. Por favor intente nuevamente.")
                            return request.render("copier_company.portal_remote_assistance", values)
                    
                    # Crear solicitud de asistencia remota
                    if 'remote.assistance.request' in request.env:
                        try:
                            _logger.info("Creando solicitud de asistencia remota")
                            
                            assistance_request = request.env['remote.assistance.request'].sudo().create_from_public_form(form_data)
                            _logger.info("Solicitud de asistencia remota creada exitosamente: ID=%s, Secuencia=%s", assistance_request.id, assistance_request.secuencia)
                            
                            # Enviar notificación por email al equipo técnico
                            try:
                                self._send_technical_notification(assistance_request)
                            except Exception as e:
                                _logger.error("Error enviando notificación técnica: %s", str(e))
                            
                            # Mensaje de éxito con información detallada
                            success_message = _(
                                "¡Solicitud de asistencia remota creada exitosamente!<br/><br/>"
                                "<strong>Número de solicitud:</strong> {}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Tipo de asistencia:</strong> {}<br/><br/>"
                                "Nuestro equipo técnico se pondrá en contacto contigo pronto.<br/>"
                                "Recibirás un email de confirmación en: {}"
                            ).format(
                                assistance_request.secuencia,
                                equipment_data['name'],
                                equipment_data['serie'],
                                dict(assistance_request._fields['assistance_type'].selection).get(assistance_request.assistance_type, 'General'),
                                form_data['contact_email']
                            )
                            
                            values['success_message'] = success_message
                            values['assistance_request'] = assistance_request
                            
                        except Exception as e:
                            _logger.exception("Error al crear solicitud de asistencia remota: %s", str(e))
                            values['error_message'] = _("Ocurrió un error al procesar la solicitud. Por favor intente nuevamente o contacte directamente con soporte.")
                    else:
                        _logger.warning("Modelo remote.assistance.request no disponible")
                        values['error_message'] = _("El servicio de asistencia remota no está disponible en este momento. Por favor contacte directamente con soporte.")
                    
                except Exception as e:
                    _logger.exception("Error procesando formulario de asistencia remota: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario. Por favor verifique los datos e intente nuevamente.")
            
            # Verificar existencia del template
            template = 'copier_company.portal_remote_assistance'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')
            
            _logger.info("Renderizando template de asistencia remota: %s", template)
            _logger.info("=== FINALIZANDO public_remote_assistance ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_remote_assistance!: %s", str(e))
            return request.redirect('/')

    def _send_technical_notification(self, assistance_request):
        """Envía notificación por email al equipo técnico"""
        _logger.info("=== INICIANDO _send_technical_notification para solicitud %s ===", assistance_request.secuencia)
        
        try:
            # Buscar emails del equipo técnico (configurar según tu setup)
            technical_emails = []
            
            # Opción 1: Buscar grupo específico de técnicos
            try:
                tech_group = request.env.ref('copier_company.group_technical_support', False)
                if tech_group and tech_group.users:
                    technical_emails.extend([user.email for user in tech_group.users if user.email])
                    _logger.info("Emails encontrados del grupo técnico: %s", technical_emails)
            except Exception:
                _logger.info("Grupo técnico no encontrado, usando emails por defecto")
            
            # Opción 2: Emails por defecto si no hay grupo configurado
            if not technical_emails:
                technical_emails = [
                    'soporte@copiercompanysac.com',
                    'tecnico@copiercompanysac.com'
                ]
                _logger.info("Usando emails técnicos por defecto: %s", technical_emails)
            
            # Preparar datos para el email
            equipment = assistance_request.equipment_id
            assistance_type_name = dict(assistance_request._fields['assistance_type'].selection).get(
                assistance_request.assistance_type, 'General'
            )
            priority_name = dict(assistance_request._fields['priority'].selection).get(
                assistance_request.priority, 'Media'
            )
            
            # Preparar datos de acceso si están disponibles
            access_info = []
            if assistance_request.anydesk_id:
                access_info.append(f"• AnyDesk ID: {assistance_request.anydesk_id}")
            if assistance_request.username:
                access_info.append(f"• Usuario: {assistance_request.username}")
            if assistance_request.user_password:
                access_info.append(f"• Contraseña: {assistance_request.user_password}")
            if assistance_request.scanner_email:
                access_info.append(f"• Email Escáner: {assistance_request.scanner_email}")
            if assistance_request.scanner_password:
                access_info.append(f"• Clave Email Escáner: {assistance_request.scanner_password}")
            
            access_info_text = "<br/>".join(access_info) if access_info else "No se proporcionaron datos de acceso específicos."
            
            # Crear el cuerpo del email
            email_body = f"""
            <h2>🖥️ Nueva Solicitud de Asistencia Remota</h2>
            
            <h3>📋 Información de la Solicitud</h3>
            <p><strong>Número:</strong> {assistance_request.secuencia}</p>
            <p><strong>Fecha:</strong> {assistance_request.request_date.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Tipo:</strong> {assistance_type_name}</p>
            <p><strong>Prioridad:</strong> {priority_name}</p>
            
            <h3>🖨️ Información del Equipo</h3>
            <p><strong>Equipo:</strong> {equipment.name.name if equipment.name else 'Sin nombre'}</p>
            <p><strong>Serie:</strong> {equipment.serie_id or 'Sin serie'}</p>
            <p><strong>Marca:</strong> {equipment.marca_id.name if equipment.marca_id else 'Sin marca'}</p>
            <p><strong>Tipo:</strong> {'Color' if equipment.tipo == 'color' else 'Blanco y Negro'}</p>
            <p><strong>Cliente:</strong> {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}</p>
            <p><strong>Ubicación:</strong> {equipment.ubicacion or 'Sin ubicación'}</p>
            <p><strong>Sede:</strong> {equipment.sede or 'Sin sede'}</p>
            <p><strong>IP:</strong> {equipment.ip_id or 'Sin IP'}</p>
            
            <h3>👤 Información del Contacto</h3>
            <p><strong>Nombre:</strong> {assistance_request.contact_name}</p>
            <p><strong>Email:</strong> {assistance_request.contact_email}</p>
            <p><strong>Teléfono:</strong> {assistance_request.contact_phone or 'No proporcionado'}</p>
            
            <h3>🔧 Descripción del Problema</h3>
            <p>{assistance_request.problem_description.replace(chr(10), '<br/>')}</p>
            
            <h3>🔑 Datos de Acceso Remoto</h3>
            <p>{access_info_text}</p>
            
            <h3>⚡ Acciones Sugeridas</h3>
            <ul>
                <li>Revisar la solicitud en el sistema: <a href="{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={assistance_request.id}&model=remote.assistance.request&view_type=form">Ver Solicitud</a></li>
                <li>Contactar al cliente para coordinar la asistencia</li>
                <li>Programar la sesión de asistencia remota</li>
                <li>Actualizar el estado de la solicitud</li>
            </ul>
            
            <hr/>
            <p><small>Este email fue generado automáticamente desde el portal de equipos de Copier Company.</small></p>
            """
            
            # Enviar email a cada técnico
            for email in technical_emails:
                if email:
                    try:
                        mail_values = {
                            'subject': f'🖥️ Nueva Asistencia Remota - {assistance_request.secuencia} - {equipment.name.name if equipment.name else "Equipo"}',
                            'email_to': email,
                            'email_from': 'noreply@copiercompanysac.com',
                            'body_html': email_body,
                            'auto_delete': False,
                        }
                        
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        mail.send()
                        _logger.info("Email de notificación enviado a: %s", email)
                        
                    except Exception as e:
                        _logger.error("Error enviando email a %s: %s", email, str(e))
            
            _logger.info("Proceso de notificación técnica completado")
            
        except Exception as e:
            _logger.exception("Error en _send_technical_notification: %s", str(e))
            raise

    @http.route(['/public/request_toner'], type='http', auth="public", website=True)
    def public_request_toner(self, copier_company_id=None, **kw):
        """Formulario para solicitar toner con datos pre-cargados"""
        _logger.info("=== INICIANDO public_request_toner ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s, kw: %s", copier_company_id, kw)
        
        try:
            if not copier_company_id:
                return request.redirect('/')
                
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')
            
            values = {
                'equipment': equipment,
                'page_title': _('Solicitar Toner'),
            }
            
            # Si es POST, procesar solicitud
            if request.httprequest.method == 'POST':
                # Lógica para procesar solicitud de toner
                # Similar a asistencia remota pero más simple
                pass
            
            return request.render('copier_company.portal_request_toner', values)
            
        except Exception as e:
            _logger.exception("Error en public_request_toner: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/send_whatsapp'], type='http', auth="public", website=True)
    def public_send_whatsapp(self, copier_company_id=None, **kw):
        """Redirige a WhatsApp con mensaje pre-formateado"""
        _logger.info("=== INICIANDO public_send_whatsapp ===")
        
        try:
            if not copier_company_id:
                return request.redirect('/')
                
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')
            
            # Número de WhatsApp de la empresa (configurar según tus datos)
            whatsapp_number = "51999999999"  # Cambiar por tu número real
            
            # Mensaje pre-formateado
            message = f"""Hola! Necesito soporte para mi equipo:

    📱 *Información del Equipo:*
    • Equipo: {equipment.name.name if equipment.name else 'Sin nombre'}
    • Serie: {equipment.serie_id or 'Sin serie'}
    • Ubicación: {equipment.ubicacion or 'Sin ubicación'}

    ¿Podrían ayudarme?"""
            
            # URL de WhatsApp
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={werkzeug.urls.url_quote(message)}"
            
            _logger.info("Redirigiendo a WhatsApp: %s", whatsapp_url)
            return request.redirect(whatsapp_url)
            
        except Exception as e:
            _logger.exception("Error en public_send_whatsapp: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/send_email'], type='http', auth="public", website=True)
    def public_send_email(self, copier_company_id=None, **kw):
        """Abre cliente de email con datos pre-cargados"""
        _logger.info("=== INICIANDO public_send_email ===")
        
        try:
            if not copier_company_id:
                return request.redirect('/')
                
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')
            
            # Email de soporte
            support_email = "soporte@copiercompanysac.com"
            
            # Asunto y cuerpo pre-formateados
            subject = f"Soporte para equipo {equipment.name.name if equipment.name else 'Sin nombre'} - Serie: {equipment.serie_id or 'Sin serie'}"
            
            body = f"""Estimado equipo de soporte,

    Solicito asistencia para mi equipo con la siguiente información:

    INFORMACIÓN DEL EQUIPO:
    - Equipo: {equipment.name.name if equipment.name else 'Sin nombre'}
    - Serie: {equipment.serie_id or 'Sin serie'}
    - Marca: {equipment.marca_id.name if equipment.marca_id else 'Sin marca'}
    - Ubicación: {equipment.ubicacion or 'Sin ubicación'}
    - Sede: {equipment.sede or 'Sin sede'}
    - Cliente: {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}

    DESCRIPCIÓN DEL PROBLEMA:
    [Por favor, describa aquí el problema que está experimentando]

    INFORMACIÓN DE CONTACTO:
    - Nombre: [Su nombre completo]
    - Teléfono: [Su número de teléfono]
    - Email: [Su email]

    Quedo atento a su respuesta.

    Saludos cordiales."""
            
            # URL mailto
            mailto_url = f"mailto:{support_email}?subject={werkzeug.urls.url_quote(subject)}&body={werkzeug.urls.url_quote(body)}"
            
            _logger.info("Redirigiendo a cliente de email")
            return request.redirect(mailto_url)
            
        except Exception as e:
            _logger.exception("Error en public_send_email: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/upload_counters'], type='http', auth="public", website=True)
    def public_upload_counters(self, copier_company_id=None, **kw):
        """Formulario para subir contadores"""
        _logger.info("=== INICIANDO public_upload_counters ===")
        
        try:
            if not copier_company_id:
                return request.redirect('/')
                
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')
            
            values = {
                'equipment': equipment,
                'page_title': _('Reportar Contadores'),
            }
            
            # Si es POST, procesar contadores
            if request.httprequest.method == 'POST':
                # Lógica para procesar contadores
                # Crear registro en copier.counter
                pass
            
            return request.render('copier_company.portal_upload_counters', values)
            
        except Exception as e:
            _logger.exception("Error en public_upload_counters: %s", str(e))
            return request.redirect('/')