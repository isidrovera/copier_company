# -*- coding: utf-8 -*-
import logging
import json
import werkzeug
from datetime import datetime, timedelta
from odoo import http, _, fields
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv import expression
import base64

_logger = logging.getLogger(__name__)


class CopierPortal(CustomerPortal):
    def _safe_get_text(self, value, maxlen=200):
        """
        Normaliza texto para mostrar en plantillas/valores.
        No cambia comportamiento: solo coalesce, strip y recorte opcional.
        """
        try:
            s = value or ''
            if not isinstance(s, str):
                s = str(s)
            s = s.strip()
            if maxlen and len(s) > maxlen:
                s = s[:maxlen]
            return s
        except Exception:
            return ''

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        try:
            partner = request.env.user.partner_id
            equipment_count = request.env['copier.company'].sudo().search_count([('cliente_id', '=', partner.id)])
        except Exception:
            equipment_count = 0
        values.update({
            'equipment_count': equipment_count,
        })
        return values

    @http.route(['/my/copier/equipments'], type='http', auth='user', website=True)
    def portal_my_equipment(self, **kwargs):
        _logger.info("=== INICIANDO portal_my_equipment ===")
        page = int(kwargs.get('page', 1))
        partner = request.env.user.partner_id

        # --- ORDENAMIENTOS (incluye 'date' para evitar KeyError) ---
        searchbar_sortings = {
            'name': {'label': _('Nombre'), 'order': 'name asc'},
            'date': {'label': _('Fecha'), 'order': 'create_date desc'},
            'status': {'label': _('Estado'), 'order': 'estado_renovacion asc, name asc'},
        }

        # --- FILTROS ---
        domain_base = [('cliente_id', '=', partner.id)]
        searchbar_filters = {
            'all': {'label': _('Todos'), 'domain': domain_base},
            'active': {'label': _('Contratos Activos'),
                    'domain': expression.AND([domain_base, [('estado_renovacion', 'in', ['vigente', 'por_vencer'])]])},
            'expired': {'label': _('Vencidos'),
                        'domain': expression.AND([domain_base, [('estado_renovacion', '=', 'finalizado')]])},
        }

        filterby = kwargs.get('filterby') or 'all'
        if filterby not in searchbar_filters:
            filterby = 'all'
        current_domain = searchbar_filters[filterby]['domain']

        sortby = kwargs.get('sortby') or 'name'
        if sortby not in searchbar_sortings:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # --- Paginación (no usar pager['step']) ---
        step = 20  # usa este valor para limit
        Equip = request.env['copier.company'].sudo()
        total = Equip.search_count(current_domain)
        pager = portal_pager(
            url="/my/copier/equipments",
            url_args={'filterby': filterby, 'sortby': sortby},
            total=total,
            page=page,
            step=step
        )
        offset = pager.get('offset', 0)

        equipments = Equip.search(current_domain, order=order, limit=step, offset=offset)

        values = {
            'page_name': 'equipment',
            'equipments': equipments,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'filters': searchbar_filters,
            'filterby': filterby,
        }
        return request.render('copier_company.portal_my_copier_equipments', values)

    @http.route(['/my/copier/equipment/<int:equipment_id>'], type='http', auth='user', website=True)
    def portal_equipment_detail(self, equipment_id, **kwargs):
        Equip = request.env['copier.company'].sudo()
        equipment = Equip.browse(equipment_id)
        if not equipment or equipment.cliente_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')

        values = {
            'page_name': 'equipment_detail',
            'equipment': equipment,
        }
        return request.render('copier_company.portal_my_copier_equipment', values)

    @http.route(['/my/copier/equipment/<int:equipment_id>/counters'], type='http', auth='user', website=True)
    def portal_equipment_counters(self, equipment_id, **kwargs):
        Equip = request.env['copier.company'].sudo()
        equipment = Equip.browse(equipment_id)
        if not equipment or equipment.cliente_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')

        Counter = request.env['copier.counter'].sudo()
        counters = Counter.search([('maquina_id', '=', equipment.id)], order='fecha desc, id desc')

        chart_data = {}

        values = {
            'page_name': 'equipment_counters',
            'equipment': equipment,
            'counters': counters,
            'chart_data': chart_data,
        }
        return request.render('copier_company.portal_my_copier_counters', values)
        
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
            redirect_url = f'/public/service_request?copier_company_id={equipment_id}'
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

                    # CAMBIO 1: Buscar TODOS los contadores (no solo confirmed/invoiced)
                    counters = request.env['copier.counter'].search([
                        ('maquina_id', '=', equipment_id)
                    ], order='fecha desc')

                    _logger.info("Contadores encontrados: %s", len(counters))

                    # CAMBIO 2: Filtrar contadores que tienen datos de usuario
                    counters_with_users = counters.filtered(lambda c: c.usuario_detalle_ids)
                    _logger.info("Contadores con datos de usuario: %s", len(counters_with_users))

                    # CAMBIO 3: Log detallado de cada contador con usuarios
                    for counter in counters_with_users:
                        _logger.info("Contador con usuarios: ID=%s, Nombre=%s, Mes=%s, Usuarios=%s, Estado=%s", 
                                counter.id, counter.name, counter.mes_facturacion, 
                                len(counter.usuario_detalle_ids), counter.state)
                        
                        # Log de cada usuario
                        for user_detail in counter.usuario_detalle_ids:
                            _logger.info("  - Usuario: %s, Copias: %s", 
                                    user_detail.usuario_id.name, user_detail.cantidad_copias)

                    # Preparar datos para el gráfico general (código existente...)
                    monthly_data = []
                    yearly_data = []
                    month_dict = {}
                    year_dict = {}

                    # CAMBIO 4: Procesar solo contadores confirmados para gráficos principales
                    confirmed_counters = counters.filtered(lambda c: c.state in ('confirmed', 'invoiced'))
                    
                    for counter in confirmed_counters:
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

                    # CAMBIO 5: Gráfico del último contador por usuario (solo si tiene datos)
                    chart_user_data = []
                    if counters_with_users:
                        first = counters_with_users[0]  # El más reciente
                        if first.usuario_detalle_ids:
                            for user_detail in first.usuario_detalle_ids:
                                chart_user_data.append({
                                    'name': user_detail.usuario_id.name,
                                    'copies': user_detail.cantidad_copias
                                })
                            _logger.info("Datos de usuario del contador más reciente: %s usuarios", len(chart_user_data))

                    # CAMBIO 6: Gráfico mensual por usuario - usar TODOS los contadores con usuarios
                    from collections import defaultdict
                    monthly_user_data = defaultdict(lambda: defaultdict(int))

                    for counter in counters_with_users:  # Usar todos los contadores con usuarios
                        mes = counter.mes_facturacion or counter.fecha.strftime('%B %Y') if counter.fecha else 'Sin fecha'
                        for detalle in counter.usuario_detalle_ids:
                            nombre = detalle.usuario_id.name or 'Sin nombre'
                            monthly_user_data[mes][nombre] += detalle.cantidad_copias

                    labels = sorted(monthly_user_data.keys())
                    usuarios_unicos = sorted({u for datos in monthly_user_data.values() for u in datos})

                    _logger.info("Datos de usuario mensual: %s meses, %s usuarios únicos", len(labels), len(usuarios_unicos))
                    _logger.info("Meses encontrados: %s", labels)
                    _logger.info("Usuarios únicos: %s", usuarios_unicos)

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

                    _logger.info("Datos para gráfico preparados: %s meses, %s años, %s usuarios", 
                            len(monthly_data), len(yearly_data), len(chart_user_data))

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
                'company_phone': '+51 975 399 303',  # Configurar según tus datos
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
        """Formulario de asistencia remota"""
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
                
            _logger.info("Cargando formulario de asistencia remota para equipo: %s", 
                        equipment.name.name if equipment.name else 'Sin nombre')
            
            # Preparar datos del equipo (SIN datos de contacto del equipo)
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'ip': self._safe_get_text(equipment.ip_id) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
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
                    
                    _logger.info("Datos del formulario capturados: %s", 
                            {k: v if k not in ['user_password', 'scanner_password'] else '***' for k, v in form_data.items()})
                    
                    # Validaciones básicas
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
                        _logger.info("Partner encontrado para email %s: ID=%s, Nombre=%s", 
                                form_data['contact_email'], partner.id, partner.name)
                        # Actualizar datos si es necesario
                        update_vals = {}
                        if partner.name != form_data['contact_name']:
                            update_vals['name'] = form_data['contact_name']
                        if form_data['contact_phone'] and not partner.mobile:
                            update_vals['mobile'] = form_data['contact_phone']
                        if update_vals:
                            partner.sudo().write(update_vals)
                            _logger.info("Partner actualizado: %s", update_vals)
                    else:
                        try:
                            partner = request.env['res.partner'].sudo().create({
                                'name': form_data['contact_name'],
                                'email': form_data['contact_email'],
                                'mobile': form_data['contact_phone'],
                                'is_company': False
                            })
                            _logger.info("Nuevo partner creado: ID=%s, Nombre=%s, Email=%s", 
                                    partner.id, partner.name, partner.email)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                            values['error_message'] = _("Error al procesar los datos del contacto. Por favor intente nuevamente.")
                            return request.render("copier_company.portal_remote_assistance", values)
                    
                    # Crear solicitud de asistencia remota
                    if 'remote.assistance.request' in request.env:
                        try:
                            _logger.info("Creando solicitud de asistencia remota")
                            
                            assistance_request = request.env['remote.assistance.request'].sudo().create_from_public_form(form_data)
                            _logger.info("Solicitud de asistencia remota creada exitosamente: ID=%s, Secuencia=%s", 
                                    assistance_request.id, assistance_request.secuencia)
                            
                            # Enviar notificación por email al equipo técnico
                            try:
                                self._send_technical_notification(assistance_request)
                            except Exception as e:
                                _logger.error("Error enviando notificación técnica: %s", str(e))
                            
                            # Mapeo de tipos de asistencia para el mensaje
                            assistance_types = {
                                'general': 'Asistencia General',
                                'scanner_email': 'Configuración Escáner por Email',
                                'network': 'Problemas de Red',
                                'drivers': 'Instalación de Drivers',
                                'printing': 'Problemas de Impresión',
                                'scanning': 'Problemas de Escaneo',
                                'maintenance': 'Mantenimiento Preventivo',
                                'other': 'Otro'
                            }
                            
                            # Mensaje de éxito con información detallada
                            success_message = _(
                                "¡Solicitud de asistencia remota creada exitosamente!<br/><br/>"
                                "<strong>Número de solicitud:</strong> {}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Tipo de asistencia:</strong> {}<br/>"
                                "<strong>Prioridad:</strong> {}<br/><br/>"
                                "Nuestro equipo técnico se pondrá en contacto contigo pronto.<br/>"
                                "Recibirás actualizaciones en: {}"
                            ).format(
                                assistance_request.secuencia,
                                equipment_data['name'],
                                equipment_data['serie'],
                                assistance_types.get(assistance_request.assistance_type, 'General'),
                                dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media'),
                                form_data['contact_email']
                            )
                            
                            values['success_message'] = success_message
                            values['assistance_request'] = assistance_request
                            
                            # Agregar datos de la solicitud para mostrar en la pantalla de éxito
                            values['request_data'] = {
                                'secuencia': assistance_request.secuencia,
                                'assistance_type': assistance_types.get(assistance_request.assistance_type, 'General'),
                                'priority': dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media'),
                                'anydesk_id': assistance_request.anydesk_id or 'No proporcionado',
                                'username': assistance_request.username or 'No proporcionado',
                                'scanner_email': assistance_request.scanner_email or 'No proporcionado',
                            }
                            
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
        """Envía notificación por email para nueva solicitud de asistencia remota"""
        _logger.info("=== INICIANDO _send_technical_notification para solicitud %s ===", assistance_request.secuencia)
        try:
            # 1) Destinatarios: primero por grupo, si no hay usar lista fija
            technical_emails = []
            try:
                tech_group = request.env.ref('copier_company.group_technical_support', False)
                if tech_group and tech_group.users:
                    technical_emails = [u.email for u in tech_group.users if u.email]
            except Exception:
                _logger.info("Grupo técnico no encontrado; usando fallback.")
            if not technical_emails:
                technical_emails = [
                    'soporte@copiercompanysac.com',
                    'tecnico@copiercompanysac.com',
                    'administracion@copiercompanysac.com',
                ]

            # 2) Servidor de correo: Outlook con fallback
            mail_server = request.env['ir.mail_server'].sudo().search([('name', '=', 'Outlook')], limit=1)
            if not mail_server:
                _logger.error("No se encontró el servidor de correo 'Outlook'. Intentando fallback…")
                mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
                if not mail_server:
                    _logger.error("No hay servidores de correo configurados")
                    return False
            _logger.info("Usando servidor de correo: %s (ID: %s)", mail_server.name, mail_server.id)

            # 3) Mapeos legibles
            assistance_types = {
                'general': 'Asistencia General',
                'scanner_email': 'Configuración Escáner por Email',
                'network': 'Problemas de Red',
                'drivers': 'Instalación de Drivers',
                'printing': 'Problemas de Impresión',
                'scanning': 'Problemas de Escaneo',
                'maintenance': 'Mantenimiento Preventivo',
                'other': 'Otro'
            }
            priority_names = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta', 'urgent': 'Urgente'}
            priority_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}

            equipment = assistance_request.equipment_id
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''

            # 4) Datos de acceso (passwords enmascaradas)
            def mask(val):
                return '●' * len(val) if val else ''
            access_rows = []
            if assistance_request.anydesk_id:
                access_rows.append(f"<tr><td>AnyDesk ID</td><td>{assistance_request.anydesk_id}</td></tr>")
            if assistance_request.username:
                access_rows.append(f"<tr><td>Usuario del Equipo</td><td>{assistance_request.username}</td></tr>")
            if assistance_request.user_password:
                access_rows.append(f"<tr><td>Contraseña</td><td>{mask(assistance_request.user_password)}</td></tr>")
            if assistance_request.scanner_email:
                access_rows.append(f"<tr><td>Email del Escáner</td><td>{assistance_request.scanner_email}</td></tr>")
            if assistance_request.scanner_password:
                access_rows.append(f"<tr><td>Clave Email Escáner</td><td>{mask(assistance_request.scanner_password)}</td></tr>")
            access_table = ("<table border='1' style='border-collapse:collapse;width:100%'>"
                            "<tr style='background:#f0f0f0'><th style='text-align:left;padding:8px'>Dato</th>"
                            "<th style='text-align:left;padding:8px'>Información</th></tr>"
                            + "".join([r.replace("<td>", "<td style='padding:8px;border:1px solid #ddd;'>")
                                        .replace("<tr>", "<tr style='border:1px solid #ddd;'>") for r in access_rows])
                            + "</table>") if access_rows else "<p>No se proporcionaron datos de acceso específicos.</p>"

            # 5) Cuerpo del correo (combina lo mejor de ambos)
            email_body = f"""
            <h2>🛠️ Nueva Solicitud de Asistencia Remota</h2>

            <h3>📋 Información de la Solicitud</h3>
            <p><strong>Número:</strong> {assistance_request.secuencia}</p>
            <p><strong>Fecha:</strong> {assistance_request.request_date.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Tipo:</strong> {assistance_types.get(assistance_request.assistance_type, 'General')}</p>
            <p><strong>Prioridad:</strong> {priority_icons.get(assistance_request.priority, '⚪')}
                {priority_names.get(assistance_request.priority, 'Media')}</p>

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

            <h3>🔍 Descripción del Problema</h3>
            <div style="background:#f9f9f9;padding:15px;border-left:4px solid #007bff;margin:10px 0;">
                <p style="margin:0;">{(assistance_request.problem_description or '').replace(chr(10), '<br/>')}</p>
            </div>

            <h3>🔑 Datos de Acceso Remoto</h3>
            {access_table}

            <h3>⚡ Acciones</h3>
            <ul>
                <li><a href="{base_url}/web#id={assistance_request.id}&model=remote.assistance.request&view_type=form">Ver Solicitud en el Sistema</a></li>
                <li>Contactar al cliente para coordinar la sesión</li>
                <li>Programar fecha y hora de la asistencia</li>
                <li>Actualizar el estado de la solicitud</li>
            </ul>

            <hr/>
            <p><small>Este email fue generado automáticamente desde el portal de equipos de Copier Company.</small></p>
            """

            # 6) Enviar
            subject = f"🛠️ Nueva Solicitud de Asistencia Remota - {assistance_request.secuencia} - " \
                    f"{equipment.name.name if equipment.name else 'Equipo'}"
            for email in technical_emails:
                if not email:
                    continue
                try:
                    mail_values = {
                        'subject': subject,
                        'email_to': email,
                        'email_from': 'info@copiercompanysac.com',
                        'body_html': email_body,
                        'auto_delete': False,
                        'mail_server_id': mail_server.id,
                    }
                    mail = request.env['mail.mail'].sudo().create(mail_values)
                    mail.send()
                    _logger.info("Notificación de asistencia remota enviada a: %s con servidor: %s", email, mail_server.name)
                except Exception as e:
                    _logger.error("Error enviando notificación a %s: %s", email, str(e))

            _logger.info("Proceso de notificación de asistencia remota completado")
            return True

        except Exception as e:
            _logger.exception("Error en _send_technical_notification: %s", str(e))
            return False

    
    @http.route(['/public/request_toner'], type='http', auth="public", website=True)
    def public_request_toner(self, copier_company_id=None, **kw):
        """Formulario para solicitar toner"""
        _logger.info("=== INICIANDO public_request_toner ===")
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
            
            _logger.info("Cargando formulario de solicitud de toner para equipo: %s", 
                        equipment.name.name if equipment.name else 'Sin nombre')
            
            # Preparar datos del equipo (SIN datos de contacto del equipo)
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }
            
            _logger.info("Datos del equipo pre-cargados: %s", equipment_data)
            
            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'page_title': _('Solicitar Toner'),
            }
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST de solicitud de toner")
                
                try:
                    # Capturar datos del formulario
                    form_data = {
                        'equipment_id': int(copier_company_id),
                        'client_name': kw.get('client_name', '').strip(),
                        'client_email': kw.get('client_email', '').strip(),
                        'client_phone': kw.get('client_phone', '').strip(),
                        'toner_type': kw.get('toner_type', ''),
                        'quantity': int(kw.get('quantity', 1)) if kw.get('quantity') else 1,
                        'urgency': kw.get('urgency', 'medium'),
                        'current_toner_level': kw.get('current_toner_level', ''),
                        'reason': kw.get('reason', '').strip(),
                    }
                    
                    _logger.info("Datos del formulario capturados: %s", form_data)
                    
                    # Validaciones básicas
                    if not form_data['client_name']:
                        _logger.warning("Nombre del solicitante requerido")
                        values['error_message'] = _("El nombre del solicitante es requerido.")
                        return request.render("copier_company.portal_request_toner", values)
                    
                    if not form_data['client_email']:
                        _logger.warning("Email del solicitante requerido")
                        values['error_message'] = _("El email del solicitante es requerido.")
                        return request.render("copier_company.portal_request_toner", values)
                    
                    if not form_data['toner_type']:
                        _logger.warning("Tipo de toner requerido")
                        values['error_message'] = _("Debe seleccionar el tipo de toner.")
                        return request.render("copier_company.portal_request_toner", values)
                    
                    # Validar email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, form_data['client_email']):
                        _logger.warning("Email inválido: %s", form_data['client_email'])
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_request_toner", values)
                    
                    # Validar cantidad
                    if form_data['quantity'] <= 0:
                        _logger.warning("Cantidad inválida: %s", form_data['quantity'])
                        values['error_message'] = _("La cantidad debe ser mayor a cero.")
                        return request.render("copier_company.portal_request_toner", values)
                    
                    # Buscar o crear partner basado en email
                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['client_email'])], limit=1)
                    if partner:
                        _logger.info("Partner encontrado para email %s: ID=%s, Nombre=%s", form_data['client_email'], partner.id, partner.name)
                        # Actualizar datos si es necesario
                        update_vals = {}
                        if partner.name != form_data['client_name']:
                            update_vals['name'] = form_data['client_name']
                        if form_data['client_phone'] and not partner.mobile:
                            update_vals['mobile'] = form_data['client_phone']
                        if update_vals:
                            partner.sudo().write(update_vals)
                            _logger.info("Partner actualizado: %s", update_vals)
                    else:
                        try:
                            partner = request.env['res.partner'].sudo().create({
                                'name': form_data['client_name'],
                                'email': form_data['client_email'],
                                'mobile': form_data['client_phone'],
                                'is_company': False
                            })
                            _logger.info("Nuevo partner creado: ID=%s, Nombre=%s, Email=%s", partner.id, partner.name, partner.email)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                            values['error_message'] = _("Error al procesar los datos del contacto. Por favor intente nuevamente.")
                            return request.render("copier_company.portal_request_toner", values)
                    
                    # Crear solicitud de toner
                    if 'toner.request' in request.env:
                        try:
                            _logger.info("Creando solicitud de toner")
                            
                            toner_request = request.env['toner.request'].sudo().create_from_public_form(form_data)
                            _logger.info("Solicitud de toner creada exitosamente: ID=%s, Secuencia=%s", 
                                    toner_request.id, toner_request.secuencia)
                            
                            # Enviar notificación por email al equipo de logística
                            try:
                                self._send_toner_notification(toner_request)
                            except Exception as e:
                                _logger.error("Error enviando notificación de toner: %s", str(e))
                            
                            # Mapeo de tipos de toner para el mensaje
                            toner_types = {
                                'black': 'Negro',
                                'cyan': 'Cian', 
                                'magenta': 'Magenta',
                                'yellow': 'Amarillo',
                                'complete_set': 'Juego Completo',
                                'maintenance_kit': 'Kit de Mantenimiento'
                            }
                            
                            # Mensaje de éxito con información detallada
                            success_message = _(
                                "¡Solicitud de toner creada exitosamente!<br/><br/>"
                                "<strong>Número de solicitud:</strong> {}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Tipo de toner:</strong> {}<br/>"
                                "<strong>Cantidad:</strong> {}<br/><br/>"
                                "Nuestro equipo se pondrá en contacto contigo para coordinar la entrega.<br/>"
                                "Recibirás actualizaciones en: {}"
                            ).format(
                                toner_request.secuencia,
                                equipment_data['name'],
                                equipment_data['serie'],
                                toner_types.get(toner_request.toner_type, 'Desconocido'),
                                toner_request.quantity,
                                form_data['client_email']
                            )
                            
                            values['success_message'] = success_message
                            values['toner_request'] = toner_request
                            
                            # Agregar datos de la solicitud para mostrar en la pantalla de éxito
                            values['request_data'] = {
                                'secuencia': toner_request.secuencia,
                                'toner_type': toner_types.get(toner_request.toner_type, 'Desconocido'),
                                'quantity': toner_request.quantity,
                                'urgency': dict(toner_request._fields['urgency'].selection).get(toner_request.urgency, 'Media'),
                                'current_level': dict(toner_request._fields['current_toner_level'].selection).get(toner_request.current_toner_level, 'No especificado') if toner_request.current_toner_level else 'No especificado',
                            }
                            
                        except Exception as e:
                            _logger.exception("Error al crear solicitud de toner: %s", str(e))
                            values['error_message'] = _("Ocurrió un error al procesar la solicitud. Por favor intente nuevamente o contacte directamente con soporte.")
                    else:
                        _logger.warning("Modelo toner.request no disponible")
                        values['error_message'] = _("El servicio de solicitud de toner no está disponible en este momento. Por favor contacte directamente con soporte.")
                    
                except Exception as e:
                    _logger.exception("Error procesando formulario de toner: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario. Por favor verifique los datos e intente nuevamente.")
            
            # Verificar existencia del template
            template = 'copier_company.portal_request_toner'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')
            
            _logger.info("Renderizando template de solicitud de toner: %s", template)
            _logger.info("=== FINALIZANDO public_request_toner ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_request_toner!: %s", str(e))
            return request.redirect('/')

    def _send_toner_notification(self, toner_request):
        """Envía notificación por email para nueva solicitud de toner"""
        _logger.info("=== INICIANDO _send_toner_notification para solicitud %s ===", toner_request.secuencia)
        
        try:
            # Emails del equipo de logística/ventas
            logistics_emails = [
                'logistica@copiercompanysac.com',
                'ventas@copiercompanysac.com',
                'administracion@copiercompanysac.com'
            ]
            
            # Buscar el servidor de correo Outlook configurado
            mail_server = request.env['ir.mail_server'].sudo().search([
                ('name', '=', 'Outlook')
            ], limit=1)
            
            if not mail_server:
                _logger.error("No se encontró el servidor de correo 'Outlook'")
                # Buscar cualquier servidor de correo disponible como fallback
                mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
                if mail_server:
                    _logger.info("Usando servidor de correo fallback: %s", mail_server.name)
                else:
                    _logger.error("No hay servidores de correo configurados")
                    return False
            else:
                _logger.info("Usando servidor de correo: %s (ID: %s)", mail_server.name, mail_server.id)
            
            # Mapeo de tipos de toner
            toner_types = {
                'black': 'Negro',
                'cyan': 'Cian', 
                'magenta': 'Magenta',
                'yellow': 'Amarillo',
                'complete_set': 'Juego Completo',
                'maintenance_kit': 'Kit de Mantenimiento'
            }
            
            urgency_names = {
                'low': 'Baja',
                'medium': 'Media',
                'high': 'Alta',
                'urgent': 'Urgente'
            }
            
            urgency_icons = {
                'low': '🟢',
                'medium': '🟡', 
                'high': '🟠',
                'urgent': '🔴'
            }
            
            toner_level_names = {
                'empty': 'Vacío (0%)',
                'low': 'Bajo (1-10%)',
                'medium_low': 'Medio-Bajo (11-25%)',
                'medium': 'Medio (26-50%)',
                'high': 'Alto (51-75%)',
                'full': 'Lleno (76-100%)'
            }
            
            # Preparar datos del equipo
            equipment = toner_request.equipment_id
            
            email_body = f"""
            <h2>🖨️ Nueva Solicitud de Toner</h2>
            
            <h3>📋 Información de la Solicitud</h3>
            <p><strong>Número:</strong> {toner_request.secuencia}</p>
            <p><strong>Fecha:</strong> {toner_request.request_date.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Urgencia:</strong> {urgency_icons.get(toner_request.urgency, '⚪')} {urgency_names.get(toner_request.urgency, 'Media')}</p>
            
            <h3>🖨️ Información del Equipo</h3>
            <p><strong>Equipo:</strong> {equipment.name.name if equipment.name else 'Sin nombre'}</p>
            <p><strong>Serie:</strong> {equipment.serie_id or 'Sin serie'}</p>
            <p><strong>Marca:</strong> {equipment.marca_id.name if equipment.marca_id else 'Sin marca'}</p>
            <p><strong>Tipo:</strong> {'Color' if equipment.tipo == 'color' else 'Blanco y Negro'}</p>
            <p><strong>Cliente:</strong> {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}</p>
            <p><strong>Ubicación:</strong> {equipment.ubicacion or 'Sin ubicación'}</p>
            <p><strong>Sede:</strong> {equipment.sede or 'Sin sede'}</p>
            <p><strong>IP:</strong> {equipment.ip_id or 'Sin IP'}</p>
            
            <h3>👤 Información del Solicitante</h3>
            <p><strong>Nombre:</strong> {toner_request.client_name}</p>
            <p><strong>Email:</strong> {toner_request.client_email}</p>
            <p><strong>Teléfono:</strong> {toner_request.client_phone or 'No proporcionado'}</p>
            
            <h3>🖨️ Detalles del Toner Solicitado</h3>
            <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Detalle</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Información</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Tipo de Toner</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{toner_types.get(toner_request.toner_type, 'Desconocido')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Cantidad</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{toner_request.quantity}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Nivel Actual</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{toner_level_names.get(toner_request.current_toner_level, 'No especificado') if toner_request.current_toner_level else 'No especificado'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Urgencia</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{urgency_icons.get(toner_request.urgency, '⚪')} {urgency_names.get(toner_request.urgency, 'Media')}</td>
                </tr>
            </table>
            
            {f'<h3>📝 Motivo de la Solicitud</h3><p>{toner_request.reason}</p>' if toner_request.reason else ''}
            
            <h3>⚡ Acciones Sugeridas</h3>
            <ul>
                <li><a href="{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={toner_request.id}&model=toner.request&view_type=form">Ver Solicitud en el Sistema</a></li>
                <li>Verificar disponibilidad de stock del toner solicitado</li>
                <li>Contactar al cliente para coordinar la entrega</li>
                <li>Programar la entrega e instalación del toner</li>
                <li>Actualizar el estado de la solicitud en el sistema</li>
            </ul>
            
            <hr/>
            <p><small>Esta solicitud fue generada automáticamente desde el portal de equipos de Copier Company.</small></p>
            """
            
            # Enviar email a cada persona del equipo de logística
            for email in logistics_emails:
                if email:
                    try:
                        mail_values = {
                            'subject': f'🖨️ Nueva Solicitud de Toner - {toner_request.secuencia} - {equipment.name.name if equipment.name else "Equipo"}',
                            'email_to': email,
                            'email_from': 'info@copiercompanysac.com',
                            'body_html': email_body,
                            'auto_delete': False,
                            'mail_server_id': mail_server.id,  # ✅ USAR SERVIDOR OUTLOOK
                        }
                        
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        mail.send()
                        _logger.info("Notificación de toner enviada a: %s usando servidor: %s", email, mail_server.name)
                        
                    except Exception as e:
                        _logger.error("Error enviando notificación de toner a %s: %s", email, str(e))
            
            _logger.info("Proceso de notificación de toner completado")
            return True
            
        except Exception as e:
            _logger.exception("Error en _send_toner_notification: %s", str(e))
            return False

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
    # Agregar al final de tu clase CopierPortal, ANTES del último método

    @http.route(['/public/service_request'], type='http', auth="public", website=True)
    def public_service_request(self, copier_company_id=None, **kw):
        """Formulario público para solicitar servicio técnico"""
        _logger.info("=== INICIANDO public_service_request ===")
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
            
            # Detectar si viene de QR/Scanner
            from_qr = kw.get('from_qr', '0') == '1'
            
            _logger.info("Cargando formulario de servicio técnico para equipo: %s (Origen: %s)", 
                        equipment.name.name if equipment.name else 'Sin nombre',
                        'QR Scanner' if from_qr else 'Web Normal')
            
            # Preparar datos del equipo
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'modelo': self._safe_get_text(equipment.name.name) if equipment.name else 'Sin modelo',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'ip': self._safe_get_text(equipment.ip_id) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }
            
            # SI VIENE DE WEB: Pre-cargar datos de contacto (si existen)
            # SI VIENE DE QR: Campos vacíos (usuario DEBE llenarlos)
            contact_data = {}
            if not from_qr and equipment.cliente_id:
                contact_data = {
                    'contacto': self._safe_get_text(equipment.contacto) or '',
                    'correo': self._safe_get_text(equipment.correo) or '',
                    'telefono_contacto': self._safe_get_text(equipment.celular) or '',
                }
                _logger.info("Pre-cargando datos de contacto desde equipo (acceso web normal)")
            else:
                contact_data = {
                    'contacto': '',
                    'correo': '',
                    'telefono_contacto': '',
                }
                _logger.info("Campos de contacto vacíos (acceso desde QR/Scanner)")
            
            # Cargar tipos de problemas disponibles
            problem_types = request.env['copier.service.problem.type'].sudo().search([
                ('active', '=', True)
            ], order='sequence, name')
            
            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'contact_data': contact_data,
                'problem_types': problem_types,
                'from_qr': from_qr,
                'page_title': _('Solicitar Servicio Técnico'),
            }
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST de servicio técnico")
                
                try:
                    # Capturar datos del formulario
                    form_data = {
                        'maquina_id': int(copier_company_id),
                        'contacto': kw.get('contacto', '').strip(),
                        'correo': kw.get('correo', '').strip(),
                        'telefono_contacto': kw.get('telefono_contacto', '').strip(),
                        'tipo_problema_id': int(kw.get('tipo_problema_id')) if kw.get('tipo_problema_id') else None,
                        'problema_reportado': kw.get('problema_reportado', '').strip(),
                        'prioridad': kw.get('prioridad', '1'),
                        'origen_solicitud': 'whatsapp' if from_qr else 'portal',
                        'foto_antes': kw.get('foto_antes'),
                    }
                    
                    _logger.info("Datos del formulario capturados: %s", 
                            {k: v for k, v in form_data.items() if k != 'foto_antes'})
                    
                    # VALIDACIONES
                    if not form_data['contacto']:
                        values['error_message'] = _("El nombre de la persona que reporta es OBLIGATORIO.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    if not form_data['correo']:
                        values['error_message'] = _("El email de contacto es OBLIGATORIO.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    if not form_data['telefono_contacto']:
                        values['error_message'] = _("El número de teléfono/celular es OBLIGATORIO para poder contactarte.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    if not form_data['tipo_problema_id']:
                        values['error_message'] = _("Debe seleccionar el tipo de problema.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    if not form_data['problema_reportado']:
                        values['error_message'] = _("La descripción del problema es OBLIGATORIA.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    # Validar email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, form_data['correo']):
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    # Validar teléfono (mínimo 9 dígitos)
                    phone_clean = re.sub(r'[^0-9]', '', form_data['telefono_contacto'])
                    if len(phone_clean) < 9:
                        values['error_message'] = _("El número de teléfono debe tener al menos 9 dígitos.")
                        return request.render("copier_company.portal_service_request", values)
                    
                    # Procesar imagen si se envió
                    if form_data['foto_antes'] and hasattr(form_data['foto_antes'], 'read'):
                        try:
                            photo_data = form_data['foto_antes'].read()
                            form_data['foto_antes'] = base64.b64encode(photo_data)
                            _logger.info("Imagen procesada exitosamente, tamaño: %s bytes", len(photo_data))
                        except Exception as e:
                            _logger.error("Error procesando imagen: %s", str(e))
                            form_data['foto_antes'] = False
                    else:
                        form_data['foto_antes'] = False
                    
                    # Crear solicitud de servicio
                    if 'copier.service.request' in request.env:
                        try:
                            _logger.info("Creando solicitud de servicio técnico (Origen: %s)", 
                                        'QR Scanner' if from_qr else 'Web Portal')
                            
                            # Preparar valores para creación
                            service_vals = {
                                'maquina_id': form_data['maquina_id'],
                                'tipo_problema_id': form_data['tipo_problema_id'],
                                'problema_reportado': form_data['problema_reportado'],
                                'prioridad': form_data['prioridad'],
                                'origen_solicitud': form_data['origen_solicitud'],
                                'estado': 'nuevo',
                            }
                            
                            # Agregar foto si existe
                            if form_data['foto_antes']:
                                service_vals['foto_antes'] = form_data['foto_antes']
                            
                            # Crear la solicitud
                            service_request = request.env['copier.service.request'].sudo().create(service_vals)
                            _logger.info("Solicitud de servicio creada: ID=%s, Número=%s", 
                                    service_request.id, service_request.name)
                            
                            # Registrar en el chatter quién reportó
                            service_request.message_post(
                                body=f'''
                                    📱 Información del Reportante
                                    
                                    • Nombre: {form_data['contacto']}
                                    • Email: {form_data['correo']}
                                    • Teléfono: {form_data['telefono_contacto']}
                                    • Origen: {'📱 Escáner QR' if from_qr else '🌐 Portal Web'}
                                ''',
                                message_type='notification'
                            )
                                                                                    
                            # Obtener tipo de problema para mensaje
                            tipo_problema = request.env['copier.service.problem.type'].sudo().browse(
                                form_data['tipo_problema_id']
                            )
                            
                            priority_names = {
                                '0': 'Baja',
                                '1': 'Normal',
                                '2': 'Alta',
                                '3': 'Crítica'
                            }
                            
                            # Mensaje de éxito
                            success_message = _(
                                "¡Solicitud de servicio creada exitosamente!<br/><br/>"
                                "<strong>Número de solicitud:</strong> {}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Tipo de problema:</strong> {}<br/>"
                                "<strong>Prioridad:</strong> {}<br/>"
                                "<strong>Reportado por:</strong> {}<br/><br/>"
                                "Nuestro equipo técnico se pondrá en contacto contigo pronto.<br/>"
                                "📧 Recibirás actualizaciones en: {}<br/>"
                                "📱 Te contactaremos al: {}"
                            ).format(
                                service_request.name,
                                equipment_data['name'],
                                equipment_data['serie'],
                                tipo_problema.name if tipo_problema else 'Desconocido',
                                priority_names.get(service_request.prioridad, 'Normal'),
                                form_data['contacto'],
                                form_data['correo'],
                                form_data['telefono_contacto']
                            )
                            
                            values['success_message'] = success_message
                            values['service_request'] = service_request
                            values['request_data'] = {
                                'number': service_request.name,
                                'tipo_problema': tipo_problema.name if tipo_problema else 'Desconocido',
                                'prioridad': priority_names.get(service_request.prioridad, 'Normal'),
                                'estado': 'Nuevo',
                                'reportado_por': form_data['contacto'],
                                'email': form_data['correo'],
                                'telefono': form_data['telefono_contacto'],
                            }
                            
                            # NOTIFICACIÓN (agregar después)
                            # try:
                            #     self._send_service_notification(service_request, form_data)
                            # except Exception as e:
                            #     _logger.error("Error enviando notificación: %s", str(e))
                            
                        except Exception as e:
                            _logger.exception("Error al crear solicitud de servicio: %s", str(e))
                            values['error_message'] = _(
                                "Ocurrió un error al procesar la solicitud. "
                                "Por favor intente nuevamente o contacte directamente con soporte."
                            )
                    else:
                        _logger.warning("Modelo copier.service.request no disponible")
                        values['error_message'] = _(
                            "El servicio de solicitudes técnicas no está disponible en este momento. "
                            "Por favor contacte directamente con soporte."
                        )
                    
                except Exception as e:
                    _logger.exception("Error procesando formulario de servicio: %s", str(e))
                    values['error_message'] = _(
                        "Error al procesar el formulario. "
                        "Por favor verifique los datos e intente nuevamente."
                    )
            
            # Verificar existencia del template
            template = 'copier_company.portal_service_request'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')
            
            _logger.info("Renderizando template de servicio técnico: %s", template)
            _logger.info("=== FINALIZANDO public_service_request ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_service_request!: %s", str(e))
            return request.redirect('/')


    @http.route(['/public/service_request/scan'], type='http', auth="public", website=True)
    def public_service_request_scan(self, copier_company_id=None, **kw):
        """Ruta para acceso directo mediante escaneo de QR"""
        _logger.info("=== INICIANDO public_service_request_scan (QR) ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s", copier_company_id)
        
        try:
            if not copier_company_id:
                _logger.error("No se proporcionó ID de equipo desde QR")
                return request.redirect('/')
            
            # Verificar que el equipo existe
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                _logger.error("Equipo ID %s no encontrado desde QR", copier_company_id)
                return request.redirect('/')
            
            _logger.info("✅ Acceso mediante QR para equipo: %s (Serie: %s)", 
                        equipment.name.name if equipment.name else 'Sin nombre',
                        equipment.serie_id or 'Sin serie')
            
            # Redirigir al formulario normal pero marcar que vino de QR
            return request.redirect(f'/public/service_request?copier_company_id={copier_company_id}&from_qr=1')
            
        except Exception as e:
            _logger.exception("Error en public_service_request_scan: %s", str(e))
            return request.redirect('/')
   
    @http.route(['/public/upload_counters'], type='http', auth="public", website=True)
    def public_upload_counters(self, copier_company_id=None, **kw):
        """Formulario para subir contadores"""
        _logger.info("=== INICIANDO public_upload_counters ===")
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
            
            _logger.info("Cargando formulario de contadores para equipo: %s", 
                        equipment.name.name if equipment.name else 'Sin nombre')
            
            # Obtener último contador oficial para mostrar como referencia
            last_counter = None
            last_counter_data = {}
            
            if 'copier.counter' in request.env:
                try:
                    last_counter = request.env['copier.counter'].sudo().search([
                        ('maquina_id', '=', equipment.id),
                        ('state', 'in', ['confirmed', 'invoiced'])
                    ], order='fecha desc', limit=1)
                    
                    if last_counter:
                        last_counter_data = {
                            'date': last_counter.fecha.strftime('%d/%m/%Y') if last_counter.fecha else 'Sin fecha',
                            'counter_bn': last_counter.contador_actual_bn or 0,
                            'counter_color': last_counter.contador_actual_color or 0,
                            'copies_bn': last_counter.total_copias_bn or 0,
                            'copies_color': last_counter.total_copias_color or 0,
                        }
                        _logger.info("Último contador encontrado: Fecha=%s, B/N=%s, Color=%s", 
                                last_counter_data['date'], last_counter_data['counter_bn'], last_counter_data['counter_color'])
                    else:
                        _logger.info("No se encontraron contadores anteriores para el equipo")
                except Exception as e:
                    _logger.error("Error buscando último contador: %s", str(e))
            else:
                _logger.warning("Modelo copier.counter no disponible")
            
            # Preparar datos del equipo
            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }
            
            _logger.info("Datos del equipo pre-cargados: %s", equipment_data)
            
            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'last_counter': last_counter,
                'last_counter_data': last_counter_data,
                'page_title': _('Reportar Contadores'),
            }
            
            # Si es una solicitud POST, procesar el formulario
            if request.httprequest.method == 'POST':
                _logger.info("Procesando formulario POST de contadores")
                
                try:
                    # Capturar datos del formulario
                    form_data = {
                        'equipment_id': int(copier_company_id),
                        'client_name': kw.get('client_name', '').strip(),
                        'client_email': kw.get('client_email', '').strip(),
                        'client_phone': kw.get('client_phone', '').strip(),
                        'counter_bn': int(kw.get('counter_bn', 0)) if kw.get('counter_bn') else 0,
                        'counter_color': int(kw.get('counter_color', 0)) if kw.get('counter_color') else 0,
                        'notes': kw.get('notes', '').strip(),
                        'counter_photo': kw.get('counter_photo'),
                    }
                    
                    _logger.info("Datos del formulario capturados: %s", 
                            {k: v for k, v in form_data.items() if k != 'counter_photo'})
                    
                    # Validaciones básicas
                    if not form_data['client_name']:
                        _logger.warning("Nombre del reportante requerido")
                        values['error_message'] = _("El nombre del reportante es requerido.")
                        return request.render("copier_company.portal_upload_counters", values)
                    
                    if not form_data['client_email']:
                        _logger.warning("Email del reportante requerido")
                        values['error_message'] = _("El email del reportante es requerido.")
                        return request.render("copier_company.portal_upload_counters", values)
                    
                    if form_data['counter_bn'] < 0:
                        _logger.warning("Contador B/N negativo: %s", form_data['counter_bn'])
                        values['error_message'] = _("El contador de blanco y negro no puede ser negativo.")
                        return request.render("copier_company.portal_upload_counters", values)
                    
                    if form_data['counter_color'] < 0:
                        _logger.warning("Contador Color negativo: %s", form_data['counter_color'])
                        values['error_message'] = _("El contador de color no puede ser negativo.")
                        return request.render("copier_company.portal_upload_counters", values)
                    
                    # Validar email
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, form_data['client_email']):
                        _logger.warning("Email inválido: %s", form_data['client_email'])
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_upload_counters", values)
                    
                    # Validar que los contadores no sean menores a los anteriores
                    if last_counter:
                        last_bn = last_counter.contador_actual_bn or 0
                        last_color = last_counter.contador_actual_color or 0
                        
                        if form_data['counter_bn'] < last_bn:
                            _logger.warning("Contador B/N menor al anterior: %s < %s", form_data['counter_bn'], last_bn)
                            values['error_message'] = _(
                                "El contador B/N ({:,}) no puede ser menor al contador anterior ({:,})."
                            ).format(form_data['counter_bn'], last_bn)
                            return request.render("copier_company.portal_upload_counters", values)
                        
                        if form_data['counter_color'] < last_color:
                            _logger.warning("Contador Color menor al anterior: %s < %s", form_data['counter_color'], last_color)
                            values['error_message'] = _(
                                "El contador Color ({:,}) no puede ser menor al contador anterior ({:,})."
                            ).format(form_data['counter_color'], last_color)
                            return request.render("copier_company.portal_upload_counters", values)
                    
                    # Procesar imagen si se envió
                    if form_data['counter_photo'] and hasattr(form_data['counter_photo'], 'read'):
                        try:
                            import base64
                            photo_data = form_data['counter_photo'].read()
                            form_data['counter_photo'] = base64.b64encode(photo_data)
                            form_data['counter_photo_filename'] = getattr(form_data['counter_photo'], 'filename', 'counter_photo.jpg')
                            _logger.info("Imagen procesada exitosamente, tamaño: %s bytes", len(photo_data))
                        except Exception as e:
                            _logger.error("Error procesando imagen: %s", str(e))
                            form_data['counter_photo'] = False
                            form_data['counter_photo_filename'] = False
                    else:
                        form_data['counter_photo'] = False
                        form_data['counter_photo_filename'] = False
                    
                    # Buscar o crear partner basado en email
                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['client_email'])], limit=1)
                    if partner:
                        _logger.info("Partner encontrado para email %s: ID=%s, Nombre=%s", form_data['client_email'], partner.id, partner.name)
                        # Actualizar datos si es necesario
                        update_vals = {}
                        if partner.name != form_data['client_name']:
                            update_vals['name'] = form_data['client_name']
                        if form_data['client_phone'] and not partner.mobile:
                            update_vals['mobile'] = form_data['client_phone']
                        if update_vals:
                            partner.sudo().write(update_vals)
                            _logger.info("Partner actualizado: %s", update_vals)
                    else:
                        try:
                            partner = request.env['res.partner'].sudo().create({
                                'name': form_data['client_name'],
                                'email': form_data['client_email'],
                                'mobile': form_data['client_phone'],
                                'is_company': False
                            })
                            _logger.info("Nuevo partner creado: ID=%s, Nombre=%s, Email=%s", partner.id, partner.name, partner.email)
                        except Exception as e:
                            _logger.exception("Error al crear partner: %s", str(e))
                            values['error_message'] = _("Error al procesar los datos del contacto. Por favor intente nuevamente.")
                            return request.render("copier_company.portal_upload_counters", values)
                    
                    # Crear reporte de contadores
                    if 'client.counter.submission' in request.env:
                        try:
                            _logger.info("Creando reporte de contadores")
                            
                            counter_submission = request.env['client.counter.submission'].sudo().create_from_public_form(form_data)
                            _logger.info("Reporte de contadores creado exitosamente: ID=%s, Secuencia=%s", 
                                    counter_submission.id, counter_submission.secuencia)
                            
                            # Calcular copias del período para el mensaje
                            copies_bn_period = counter_submission.copies_bn_period
                            copies_color_period = counter_submission.copies_color_period
                            total_copies_period = copies_bn_period + copies_color_period
                            
                            # Enviar notificación por email al equipo administrativo
                            try:
                                self._send_counter_notification(counter_submission)
                            except Exception as e:
                                _logger.error("Error enviando notificación de contadores: %s", str(e))
                            
                            # Mensaje de éxito con información detallada
                            success_message = _(
                                "¡Contadores reportados exitosamente!<br/><br/>"
                                "<strong>Número de reporte:</strong> {}<br/>"
                                "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                                "<strong>Contador B/N:</strong> {:,}<br/>"
                                "<strong>Contador Color:</strong> {:,}<br/>"
                                "<strong>Copias B/N del período:</strong> {:,}<br/>"
                                "<strong>Copias Color del período:</strong> {:,}<br/>"
                                "<strong>Total de copias del período:</strong> {:,}<br/><br/>"
                                "Los contadores serán revisados y procesados para la facturación.<br/>"
                                "Recibirás confirmación en: {}"
                            ).format(
                                counter_submission.secuencia,
                                equipment_data['name'],
                                equipment_data['serie'],
                                counter_submission.counter_bn,
                                counter_submission.counter_color,
                                copies_bn_period,
                                copies_color_period,
                                total_copies_period,
                                form_data['client_email']
                            )
                            
                            values['success_message'] = success_message
                            values['counter_submission'] = counter_submission
                            
                            # Agregar datos del reporte para mostrar en la pantalla de éxito
                            values['submission_data'] = {
                                'secuencia': counter_submission.secuencia,
                                'counter_bn': counter_submission.counter_bn,
                                'counter_color': counter_submission.counter_color,
                                'copies_bn_period': copies_bn_period,
                                'copies_color_period': copies_color_period,
                                'total_copies_period': total_copies_period,
                                'estimated_amount': counter_submission.estimated_total_amount,
                            }
                            
                        except Exception as e:
                            _logger.exception("Error al crear reporte de contadores: %s", str(e))
                            values['error_message'] = _("Ocurrió un error al procesar el reporte. Por favor intente nuevamente o contacte directamente con administración.")
                    else:
                        _logger.warning("Modelo client.counter.submission no disponible")
                        values['error_message'] = _("El servicio de reporte de contadores no está disponible en este momento. Por favor contacte directamente con administración.")
                    
                except ValueError as ve:
                    _logger.error("Error de valor en formulario de contadores: %s", str(ve))
                    values['error_message'] = _("Los valores de los contadores deben ser números válidos.")
                    return request.render("copier_company.portal_upload_counters", values)
                except Exception as e:
                    _logger.exception("Error procesando formulario de contadores: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario. Por favor verifique los datos e intente nuevamente.")
            
            # Verificar existencia del template
            template = 'copier_company.portal_upload_counters'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')
            
            _logger.info("Renderizando template de contadores: %s", template)
            _logger.info("=== FINALIZANDO public_upload_counters ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_upload_counters!: %s", str(e))
            return request.redirect('/')

    def _send_counter_notification(self, counter_submission):
        """Envía notificación por email para nuevo reporte de contadores"""
        _logger.info("=== INICIANDO _send_counter_notification para reporte %s ===", counter_submission.secuencia)
        
        try:
            # Emails del equipo administrativo/contable
            admin_emails = [
                'facturacion@copiercompanysac.com'
            ]
            
            # Buscar el servidor de correo Outlook configurado
            mail_server = request.env['ir.mail_server'].sudo().search([
                ('name', '=', 'Outlook')
            ], limit=1)
            
            if not mail_server:
                _logger.error("No se encontró el servidor de correo 'Outlook'")
                # Buscar cualquier servidor de correo disponible como fallback
                mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
                if mail_server:
                    _logger.info("Usando servidor de correo fallback: %s", mail_server.name)
                else:
                    _logger.error("No hay servidores de correo configurados")
                    return False
            else:
                _logger.info("Usando servidor de correo: %s (ID: %s)", mail_server.name, mail_server.id)
            
            # Preparar datos del equipo
            equipment = counter_submission.equipment_id
            
            # Calcular totales
            total_copies_period = counter_submission.copies_bn_period + counter_submission.copies_color_period
            
            email_body = f"""
            <h2>📊 Nuevo Reporte de Contadores</h2>
            
            <h3>📋 Información del Reporte</h3>
            <p><strong>Número:</strong> {counter_submission.secuencia}</p>
            <p><strong>Fecha:</strong> {counter_submission.submission_date.strftime('%d/%m/%Y %H:%M')}</p>
            
            <h3>🖨️ Información del Equipo</h3>
            <p><strong>Equipo:</strong> {equipment.name.name if equipment.name else 'Sin nombre'}</p>
            <p><strong>Serie:</strong> {equipment.serie_id or 'Sin serie'}</p>
            <p><strong>Marca:</strong> {equipment.marca_id.name if equipment.marca_id else 'Sin marca'}</p>
            <p><strong>Tipo:</strong> {'Color' if equipment.tipo == 'color' else 'Blanco y Negro'}</p>
            <p><strong>Cliente:</strong> {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}</p>
            <p><strong>Ubicación:</strong> {equipment.ubicacion or 'Sin ubicación'}</p>
            <p><strong>Sede:</strong> {equipment.sede or 'Sin sede'}</p>
            <p><strong>IP:</strong> {equipment.ip_id or 'Sin IP'}</p>
            
            <h3>👤 Información del Reportante</h3>
            <p><strong>Nombre:</strong> {counter_submission.client_name}</p>
            <p><strong>Email:</strong> {counter_submission.client_email}</p>
            <p><strong>Teléfono:</strong> {counter_submission.client_phone or 'No proporcionado'}</p>
            
            <h3>📊 Contadores Reportados</h3>
            <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Tipo</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Contador Anterior</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Contador Actual</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Copias del Período</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Blanco y Negro</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.previous_counter_bn:,}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.counter_bn:,}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.copies_bn_period:,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Color</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.previous_counter_color:,}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.counter_color:,}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{counter_submission.copies_color_period:,}</td>
                </tr>
                <tr style="background-color: #f9f9f9; font-weight: bold;">
                    <td style="padding: 8px; border: 1px solid #ddd;">TOTAL</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">-</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">-</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{total_copies_period:,}</td>
                </tr>
            </table>
            
            <h3>💰 Información Financiera Estimada</h3>
            <p><strong>Monto Estimado B/N:</strong> S/ {counter_submission.estimated_amount_bn:,.2f}</p>
            <p><strong>Monto Estimado Color:</strong> S/ {counter_submission.estimated_amount_color:,.2f}</p>
            <p><strong>Monto Total Estimado:</strong> S/ {counter_submission.estimated_total_amount:,.2f}</p>
            
            {f'<h3>📝 Observaciones del Cliente</h3><p>{counter_submission.notes}</p>' if counter_submission.notes else ''}
            
            <h3>⚡ Acciones Sugeridas</h3>
            <ul>
                <li><a href="{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={counter_submission.id}&model=client.counter.submission&view_type=form">Ver Reporte en el Sistema</a></li>
                <li>Revisar y validar los contadores reportados</li>
                <li>Comparar con lecturas anteriores para detectar anomalías</li>
                <li>Aprobar y generar contador oficial para facturación</li>
                <li>Contactar al cliente si hay discrepancias o consultas</li>
                <li>Actualizar el estado del reporte en el sistema</li>
            </ul>
            
            <hr/>
            <p><small>Este reporte fue generado automáticamente desde el portal de equipos de Copier Company.</small></p>
            """
            
            # Enviar email a cada persona del equipo administrativo
            for email in admin_emails:
                if email:
                    try:
                        mail_values = {
                            'subject': f'📊 Nuevo Reporte de Contadores - {counter_submission.secuencia} - {equipment.name.name if equipment.name else "Equipo"}',
                            'email_to': email,
                            'email_from': 'info@copiercompanysac.com',
                            'body_html': email_body,
                            'auto_delete': False,
                            'mail_server_id': mail_server.id,  # ✅ AGREGAR ESTA LÍNEA
                        }
                        
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        mail.send()
                        _logger.info("Notificación de contadores enviada a: %s usando servidor: %s", email, mail_server.name)
                        
                    except Exception as e:
                        _logger.error("Error enviando notificación de contadores a %s: %s", email, str(e))
            
            _logger.info("Proceso de notificación de contadores completado")
            return True
            
        except Exception as e:
            _logger.exception("Error en _send_counter_notification: %s", str(e))
            return False