# -*- coding: utf-8 -*-
import logging
import base64
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

_logger = logging.getLogger(__name__)


class ServiceRequestPortal(CustomerPortal):
    """Controlador para servicios técnicos"""
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
        
    @http.route(['/public/service_request'], type='http', auth="public", website=True)
    def public_service_request(self, copier_company_id=None, **kw):
        _logger.info("=== INICIANDO public_service_request ===")
        _logger.info("Parámetros recibidos - copier_company_id: %s, kw: %s", copier_company_id, kw)

        try:
            if not copier_company_id:
                return request.redirect('/')

            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            from_qr = kw.get('from_qr', '0') == '1'

            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo',
                'serie': self._safe_get_text(equipment.serie_id),
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else '',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else '',
                'ubicacion': self._safe_get_text(equipment.ubicacion),
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }

            # Detectar usuario logueado real (no público)
            user = request.env.user
            is_logged = bool(user and user.id and not user.has_group('base.group_public'))
            partner = user.partner_id if is_logged else False

            # Obtener teléfono de forma segura
            def _partner_phone(p):
                if not p:
                    return ''
                # usa solo campos que realmente existan
                return getattr(p, 'phone', '') or getattr(p, 'mobile', '')

            # Datos de contacto
            if is_logged and partner:
                contact_data = {
                    'contacto': self._safe_get_text(partner.name),
                    'correo': self._safe_get_text(partner.email),
                    'telefono_contacto': self._safe_get_text(_partner_phone(partner)),
                }
                _logger.info("Contacto desde usuario logueado")

            elif not from_qr and equipment.cliente_id:
                contact_data = {
                    'contacto': self._safe_get_text(equipment.contacto),
                    'correo': self._safe_get_text(equipment.correo),
                    'telefono_contacto': self._safe_get_text(equipment.celular),
                }
                _logger.info("Contacto desde datos del equipo")

            else:
                contact_data = {
                    'contacto': '',
                    'correo': '',
                    'telefono_contacto': '',
                }
                _logger.info("Contacto vacío")

            problem_types = request.env['copier.service.problem.type'].sudo().search(
                [('active', '=', True)], order='sequence, name'
            )

            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'contact_data': contact_data,
                'problem_types': problem_types,
                'from_qr': from_qr,
                'is_logged': is_logged,
                'page_title': _('Solicitar Servicio Técnico'),
            }

            # ===== POST =====
            if request.httprequest.method == 'POST':
                contacto = kw.get('contacto', '').strip()
                correo = kw.get('correo', '').strip()
                telefono = kw.get('telefono_contacto', '').strip()
                tipo_problema_id = int(kw.get('tipo_problema_id')) if kw.get('tipo_problema_id') else None
                descripcion = kw.get('problema_reportado', '').strip()
                prioridad = kw.get('prioridad', '1')

                if not all([contacto, correo, telefono, tipo_problema_id, descripcion]):
                    values['error_message'] = _("Complete todos los campos obligatorios.")
                    return request.render('copier_company.portal_service_request', values)

                service_vals = {
                    'maquina_id': equipment.id,
                    'tipo_problema_id': tipo_problema_id,
                    'problema_reportado': descripcion,
                    'prioridad': prioridad,
                    'estado': 'nuevo',
                    'contacto': contacto,
                    'correo': correo,
                    'telefono_contacto': telefono,
                    'origen_solicitud': 'portal',
                }

                foto = kw.get('foto_antes')
                if foto and hasattr(foto, 'read'):
                    service_vals['foto_antes'] = base64.b64encode(foto.read())

                service = request.env['copier.service.request'].sudo().create(service_vals)

                values['success_message'] = _("Solicitud creada correctamente.")
                values['request_data'] = {
                    'number': service.name,
                    'tipo_problema': request.env['copier.service.problem.type'].sudo().browse(tipo_problema_id).name,
                    'prioridad': prioridad,
                    'estado': 'Nuevo',
                    'reportado_por': contacto,
                    'email': correo,
                    'telefono': telefono,
                }

            return request.render('copier_company.portal_service_request', values)

        except Exception as e:
            _logger.exception("Error general en public_service_request: %s", str(e))
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
    @http.route(['/my/copier/equipment/<int:equipment_id>/services'], type='http', auth='user', website=True)
    def portal_equipment_services(self, equipment_id, **kwargs):
        """Muestra el historial de servicios técnicos del equipo"""
        _logger.info("=== INICIANDO portal_equipment_services ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kwargs: %s", equipment_id, kwargs)
        
        try:
            # Verificar acceso al equipo
            _logger.info("Verificando acceso al equipo ID: %s", equipment_id)
            try:
                equipment_sudo = self._document_check_access('copier.company', equipment_id)
                _logger.info("Acceso verificado para equipo ID: %s", equipment_id)
            except (AccessError, MissingError) as e:
                _logger.error("Error de acceso para equipo ID %s: %s", equipment_id, str(e))
                return request.redirect('/my')
            
            # Buscar servicios del equipo
            page = int(kwargs.get('page', 1))
            step = 20
            
            domain = [('maquina_id', '=', equipment_id)]
            
            # Filtro por estado
            filterby = kwargs.get('filterby', 'all')
            if filterby == 'pending':
                domain.append(('estado', 'not in', ['completado', 'cancelado']))
            elif filterby == 'completed':
                domain.append(('estado', '=', 'completado'))
            elif filterby == 'cancelled':
                domain.append(('estado', '=', 'cancelado'))
            
            ServiceRequest = request.env['copier.service.request'].sudo()
            total = ServiceRequest.search_count(domain)
            
            pager = portal_pager(
                url=f"/my/copier/equipment/{equipment_id}/services",
                url_args={'filterby': filterby},
                total=total,
                page=page,
                step=step
            )
            
            services = ServiceRequest.search(
                domain,
                order='create_date desc',
                limit=step,
                offset=pager.get('offset', 0)
            )
            
            # Filtros
            searchbar_filters = {
                'all': {'label': _('Todos'), 'count': ServiceRequest.search_count([('maquina_id', '=', equipment_id)])},
                'pending': {'label': _('Pendientes'), 'count': ServiceRequest.search_count([('maquina_id', '=', equipment_id), ('estado', 'not in', ['completado', 'cancelado'])])},
                'completed': {'label': _('Completados'), 'count': ServiceRequest.search_count([('maquina_id', '=', equipment_id), ('estado', '=', 'completado')])},
                'cancelled': {'label': _('Cancelados'), 'count': ServiceRequest.search_count([('maquina_id', '=', equipment_id), ('estado', '=', 'cancelado')])},
            }
            
            values = {
                'equipment': equipment_sudo,
                'services': services,
                'page_name': 'equipment_services',
                'pager': pager,
                'filterby': filterby,
                'filters': searchbar_filters,
            }
            
            template = 'copier_company.portal_my_copier_equipment_services'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/my/copier/equipment/{equipment_id}')
            
            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO portal_equipment_services ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_equipment_services!: %s", str(e))
            return request.redirect('/my')

    
    @http.route(['/my/copier/service/<int:service_id>'], type='http', auth='user', website=True)
    def portal_service_detail(self, service_id, **kwargs):
        """Muestra el detalle de un servicio técnico"""
        _logger.info("=== INICIANDO portal_service_detail ===")
        
        try:
            service = request.env['copier.service.request'].sudo().browse(service_id)
            
            if not service.exists():
                _logger.error("Servicio ID %s no encontrado", service_id)
                return request.redirect('/my')
            
            # Verificar que el usuario tenga acceso (sea cliente del equipo)
            if service.cliente_id.id != request.env.user.partner_id.id:
                _logger.error("Usuario no autorizado para ver servicio %s", service_id)
                return request.redirect('/my')
            
            values = {
                'service': service,
                'page_name': 'service_detail',
            }
            
            template = 'copier_company.portal_my_copier_service_detail'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect('/my')
            
            _logger.info("=== FINALIZANDO portal_service_detail ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("Error en portal_service_detail: %s", str(e))
            return request.redirect('/my')



    @http.route(['/my/copier/services'], type='http', auth='user', website=True)
    def portal_my_services(self, **kwargs):
        """Lista TODOS los servicios técnicos del cliente (de todos sus equipos)"""
        _logger.info("=== INICIANDO portal_my_services ===")
        
        try:
            partner = request.env.user.partner_id
            page = int(kwargs.get('page', 1))
            step = 20
            
            # Filtro por estado
            filterby = kwargs.get('filterby', 'all')
            
            domain = [('cliente_id', '=', partner.id)]
            
            if filterby == 'pending':
                domain.append(('estado', 'not in', ['completado', 'cancelado']))
            elif filterby == 'completed':
                domain.append(('estado', '=', 'completado'))
            elif filterby == 'cancelled':
                domain.append(('estado', '=', 'cancelado'))
            
            ServiceRequest = request.env['copier.service.request'].sudo()
            total = ServiceRequest.search_count(domain)
            
            pager = portal_pager(
                url="/my/copier/services",
                url_args={'filterby': filterby},
                total=total,
                page=page,
                step=step
            )
            
            services = ServiceRequest.search(
                domain,
                order='create_date desc',
                limit=step,
                offset=pager.get('offset', 0)
            )
            
            # Preparar filtros con contadores
            searchbar_filters = {
                'all': {
                    'label': _('Todos'), 
                    'count': ServiceRequest.search_count([('cliente_id', '=', partner.id)])
                },
                'pending': {
                    'label': _('Pendientes'), 
                    'count': ServiceRequest.search_count([
                        ('cliente_id', '=', partner.id), 
                        ('estado', 'not in', ['completado', 'cancelado'])
                    ])
                },
                'completed': {
                    'label': _('Completados'), 
                    'count': ServiceRequest.search_count([
                        ('cliente_id', '=', partner.id), 
                        ('estado', '=', 'completado')
                    ])
                },
                'cancelled': {
                    'label': _('Cancelados'), 
                    'count': ServiceRequest.search_count([
                        ('cliente_id', '=', partner.id), 
                        ('estado', '=', 'cancelado')
                    ])
                },
            }
            
            values = {
                'services': services,
                'page_name': 'my_services',
                'pager': pager,
                'filterby': filterby,
                'filters': searchbar_filters,
            }
            
            # Verificar que el template exista
            template = 'copier_company.portal_my_services_all'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect('/my')
            
            _logger.info("Renderizando template: %s con %s servicios", template, len(services))
            _logger.info("=== FINALIZANDO portal_my_services ===")
            return request.render(template, values)
            
        except Exception as e:
            _logger.exception("Error en portal_my_services: %s", str(e))
            return request.redirect('/my')
    # ========================================
    # RUTAS PÚBLICAS CON TOKEN
    # ========================================
    
    @http.route(['/service/track/<string:token>'], type='http', auth='public', website=True)
    def public_track_service(self, token, **kw):
        """Página pública de seguimiento de servicio (sin login)"""
        _logger.info("=== INICIANDO public_track_service ===")
        _logger.info("Token recibido: %s", token[:8] + "..." if len(token) > 8 else token)
        
        try:
            # Buscar solicitud por token
            service = request.env['copier.service.request'].sudo().search([
                ('tracking_token', '=', token)
            ], limit=1)
            
            if not service:
                _logger.warning("Token de seguimiento no válido: %s", token[:8] + "...")
                return request.render('copier_company.public_service_track_error', {
                    'error_title': _('Enlace no válido'),
                    'error_message': _('El enlace de seguimiento no es válido o ha expirado.'),
                })
            
            _logger.info("Solicitud encontrada: %s (ID: %s)", service.name, service.id)
            
            # Obtener datos de seguimiento
            tracking_data = service.get_tracking_data()
            
            values = {
                'service': service,
                'tracking_data': tracking_data,
                'page_title': _('Seguimiento de Servicio'),
            }
            
            _logger.info("Renderizando página de seguimiento para solicitud %s", service.name)
            return request.render('copier_company.public_service_track', values)
            
        except Exception as e:
            _logger.exception("Error en public_track_service: %s", str(e))
            return request.render('copier_company.public_service_track_error', {
                'error_title': _('Error'),
                'error_message': _('Ocurrió un error al cargar el seguimiento. Por favor intenta más tarde.'),
            })
    
    @http.route(['/service/evaluate/<string:token>'], type='http', auth='public', website=True, methods=['GET', 'POST'])
    def public_evaluate_service(self, token, **kw):
        """Página pública de evaluación de servicio (sin login)"""
        _logger.info("=== INICIANDO public_evaluate_service ===")
        _logger.info("Token recibido: %s, Método: %s", token[:8] + "...", request.httprequest.method)
        
        try:
            # Buscar solicitud por token
            service = request.env['copier.service.request'].sudo().search([
                ('evaluation_token', '=', token)
            ], limit=1)
            
            if not service:
                _logger.warning("Token de evaluación no válido: %s", token[:8] + "...")
                return request.render('copier_company.public_service_evaluation_error', {
                    'error_title': _('Enlace no válido'),
                    'error_message': _('El enlace de evaluación no es válido o ha expirado.'),
                })
            
            # Verificar que esté completado
            if service.estado != 'completado':
                _logger.warning("Intento de evaluar servicio no completado: %s", service.name)
                return request.render('copier_company.public_service_evaluation_error', {
                    'error_title': _('Servicio no completado'),
                    'error_message': _('Este servicio aún no ha sido completado. Podrás evaluarlo una vez finalizado.'),
                    'service': service,
                })
            
            # Verificar que no esté ya evaluado
            if service.calificacion:
                _logger.info("Servicio %s ya fue evaluado", service.name)
                return request.render('copier_company.public_service_evaluation_already_done', {
                    'service': service,
                    'calificacion': service.calificacion,
                    'comentario': service.comentario_cliente,
                })
            
            # Verificar que el token no haya sido usado
            if service.evaluation_token_used:
                _logger.warning("Token de evaluación ya usado: %s", token[:8] + "...")
                return request.render('copier_company.public_service_evaluation_error', {
                    'error_title': _('Enlace ya utilizado'),
                    'error_message': _('Este enlace de evaluación ya fue utilizado. Solo se puede usar una vez.'),
                })
            
            # Si es POST, procesar la evaluación
            if request.httprequest.method == 'POST':
                _logger.info("Procesando evaluación POST para servicio %s", service.name)
                
                try:
                    calificacion = kw.get('calificacion', '').strip()
                    comentario = kw.get('comentario', '').strip()
                    
                    # Validar calificación
                    if not calificacion or calificacion not in ['1', '2', '3', '4', '5']:
                        return request.render('copier_company.public_service_evaluation_form', {
                            'service': service,
                            'token': token,
                            'error_message': _('Por favor selecciona una calificación.'),
                            'comentario': comentario,
                        })
                    
                    # Registrar evaluación
                    service.registrar_evaluacion_publica(calificacion, comentario)
                    
                    _logger.info("✅ Evaluación registrada: %s estrellas para servicio %s", 
                                calificacion, service.name)
                    
                    # Mostrar página de agradecimiento
                    return request.render('copier_company.public_service_evaluation_thanks', {
                        'service': service,
                        'calificacion': calificacion,
                        'comentario': comentario,
                    })
                    
                except Exception as e:
                    _logger.exception("Error procesando evaluación: %s", str(e))
                    return request.render('copier_company.public_service_evaluation_form', {
                        'service': service,
                        'token': token,
                        'error_message': _('Ocurrió un error al guardar tu evaluación. Por favor intenta nuevamente.'),
                    })
            
            # GET: Mostrar formulario de evaluación
            _logger.info("Mostrando formulario de evaluación para servicio %s", service.name)
            
            values = {
                'service': service,
                'token': token,
                'page_title': _('Evaluar Servicio'),
            }
            
            return request.render('copier_company.public_service_evaluation_form', values)
            
        except Exception as e:
            _logger.exception("Error en public_evaluate_service: %s", str(e))
            return request.render('copier_company.public_service_evaluation_error', {
                'error_title': _('Error'),
                'error_message': _('Ocurrió un error al cargar la evaluación. Por favor intenta más tarde.'),
            })
    
    # ========================================
    # MÉTODO AUXILIAR
    # ========================================
    
    def _safe_get_text(self, value):
        """Helper para obtener texto seguro"""
        if not value:
            return ''
        return str(value).strip() if value else ''