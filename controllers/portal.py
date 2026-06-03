# -*- coding: utf-8 -*-
import logging
import json
import calendar
import werkzeug
import base64
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlencode

from odoo import http, _, fields
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class CopierPortal(CustomerPortal):
    # =========================================================================
    # FASE 01 - UTILIDADES GENERALES
    # =========================================================================
    def _safe_get_text(self, value, maxlen=200):
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

    # =========================================================================
    # FASE 02 - HELPERS DE EMPRESAS VISIBLES
    # =========================================================================

    def _get_allowed_partner_ids_for_portal(self):
        user = request.env.user
        partner = user.partner_id
        commercial_partner = partner.commercial_partner_id

        allowed_partner_ids = set()

        if commercial_partner:
            allowed_partner_ids.add(commercial_partner.id)

        if hasattr(partner, 'portal_empresa_ids'):
            allowed_partner_ids.update(partner.portal_empresa_ids.ids)

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] user_id=%s partner_id=%s commercial_partner_id=%s "
            "portal_empresa_ids=%s allowed_partner_ids=%s",
            user.id,
            partner.id,
            commercial_partner.id if commercial_partner else False,
            partner.portal_empresa_ids.ids if hasattr(partner, 'portal_empresa_ids') else [],
            list(allowed_partner_ids),
        )

        return list(allowed_partner_ids)

    def _get_equipment_domain_for_portal(self, only_rented=True):
        user = request.env.user
        domain = []

        if user.has_group('base.group_portal'):
            allowed_partner_ids = self._get_allowed_partner_ids_for_portal()
            domain.append(('cliente_id.commercial_partner_id', 'in', allowed_partner_ids))

        if only_rented:
            domain.append(('estado_maquina_id.name', '=', 'Alquilada'))

        return domain

    def _get_equipment_for_portal(self, equipment_id):
        equipment = request.env['copier.company'].sudo().browse(int(equipment_id))

        if not equipment.exists():
            return False

        user = request.env.user

        if not user.has_group('base.group_portal'):
            return equipment

        allowed_partner_ids = self._get_allowed_partner_ids_for_portal()

        equipment_partner = equipment.cliente_id.commercial_partner_id if equipment.cliente_id else False
        equipment_partner_id = equipment_partner.id if equipment_partner else False

        if not equipment_partner_id or equipment_partner_id not in allowed_partner_ids:
            _logger.warning(
                "[PORTAL EQUIPMENTS ACCESS] Acceso denegado a equipo. "
                "user_id=%s partner_id=%s equipment_id=%s cliente_id=%s allowed_partner_ids=%s",
                user.id,
                user.partner_id.id,
                equipment.id,
                equipment.cliente_id.id if equipment.cliente_id else False,
                allowed_partner_ids,
            )
            raise AccessError("No tiene permisos para acceder a este equipo.")

        return equipment

    # =========================================================================
    # FASE 03 - CONTADOR DEL HOME PORTAL
    # =========================================================================

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()

        try:
            equipment_count = request.env['copier.company'].sudo().search_count(
                self._get_equipment_domain_for_portal(only_rented=True)
            )
        except Exception as e:
            _logger.exception(
                "[PORTAL EQUIPMENTS ACCESS] Error calculando equipment_count: %s",
                str(e),
            )
            equipment_count = 0

        values.update({
            'equipment_count': equipment_count,
        })

        return values

    # =========================================================================
    # FASE 04 - LISTADO DE EQUIPOS CON PAGINACIÓN Y BÚSQUEDA
    # =========================================================================

    @http.route([
        '/my/copier/equipments',
        '/my/copier/equipments/page/<int:page>',
    ], type='http', auth='user', website=True)
    def portal_my_equipment(self, page=1, **kwargs):
        _logger.info("=== INICIANDO portal_my_equipment ===")

        page = int(page or 1)

        # Forzar strings puros para evitar TypeError con Markup de Odoo
        search = str(kwargs.get('search') or '').strip()
        sortby = str(kwargs.get('sortby') or 'name')
        filterby = str(kwargs.get('filterby') or 'all')

        # --- ORDENAMIENTOS ---
        searchbar_sortings = {
            'name': {
                'label': _('Nombre'),
                'order': 'name asc',
            },
            'date': {
                'label': _('Fecha'),
                'order': 'create_date desc',
            },
            'status': {
                'label': _('Estado'),
                'order': 'estado_renovacion asc, name asc',
            },
        }

        if sortby not in searchbar_sortings:
            sortby = 'name'

        # --- DOMINIO BASE ---
        domain_base = self._get_equipment_domain_for_portal(only_rented=True)

        _logger.info("[PORTAL EQUIPMENTS ACCESS] domain_base=%s", domain_base)

        # --- FILTROS ---
        searchbar_filters = {
            'all': {
                'label': _('Todos'),
                'domain': domain_base,
            },
            'active': {
                'label': _('Contratos Activos'),
                'domain': Domain.AND([
                    domain_base,
                    [('estado_renovacion', 'in', ['vigente', 'por_vencer'])]
                ]),
            },
            'expired': {
                'label': _('Vencidos'),
                'domain': Domain.AND([
                    domain_base,
                    [('estado_renovacion', '=', 'finalizado')]
                ]),
            },
        }

        if filterby not in searchbar_filters:
            filterby = 'all'

        current_domain = searchbar_filters[filterby]['domain']

        # --- BÚSQUEDA POR TEXTO LIBRE ---
        if search:
            search_domain = [
                '|', '|', '|',
                ('name.name', 'ilike', search),
                ('serie_id', 'ilike', search),
                ('ubicacion', 'ilike', search),
                ('sede', 'ilike', search),
            ]
            current_domain = Domain.AND([current_domain, search_domain])

        order = searchbar_sortings[sortby]['order']

        # --- PAGINACIÓN ---
        step = 20
        Equip = request.env['copier.company'].sudo()
        total = Equip.search_count(current_domain)

        pager = portal_pager(
            url="/my/copier/equipments",
            url_args={
                'filterby': filterby,
                'sortby': sortby,
                'search': search,
            },
            total=total,
            page=page,
            step=step,
        )

        equipments = Equip.search(
            current_domain,
            order=order,
            limit=step,
            offset=pager.get('offset', 0),
        )

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] Equipos encontrados=%s ids=%s",
            len(equipments),
            equipments.ids,
        )

        # --- CONTAR SERVICIOS POR EQUIPO ---
        service_counts = {}
        if equipments:
            try:
                service_data = request.env['copier.service.request'].sudo()._read_group(
                    [('maquina_id', 'in', equipments.ids)],
                    ['maquina_id'],
                    ['maquina_id:count'],
                )
                service_counts = {
                    rec[0].id: rec[1]
                    for rec in service_data
                    if rec[0]
                }
            except Exception as e:
                _logger.exception(
                    "[PORTAL EQUIPMENTS ACCESS] Error calculando service_counts: %s",
                    str(e),
                )
                service_counts = {}

        values = {
            'page_name': 'equipment',
            'equipments': equipments,
            'pager': pager,
            'equipment_count': total,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'service_counts': service_counts,
        }

        return request.render('copier_company.portal_my_copier_equipments', values)

    # =========================================================================
    # FASE 05 - DETALLE DE EQUIPO
    # =========================================================================

    @http.route(['/my/copier/equipment/<int:equipment_id>'], type='http', auth='user', website=True)
    def portal_equipment_detail(self, equipment_id, **kwargs):
        try:
            equipment = self._get_equipment_for_portal(equipment_id)
        except AccessError as e:
            _logger.warning(
                "[PORTAL EQUIPMENTS ACCESS] Acceso denegado al detalle equipment_id=%s error=%s",
                equipment_id,
                str(e),
            )
            return request.redirect('/my')

        if not equipment:
            return request.redirect('/my')

        values = {
            'page_name': 'equipment_detail',
            'equipment': equipment,
        }

        return request.render('copier_company.portal_my_copier_equipment', values)

    # =========================================================================
    # FASE 06 - HELPERS DE FILTRO PARA CONTADORES
    # =========================================================================

    def _parse_date(self, value):
        if not value:
            return False
        try:
            return fields.Date.from_string(value)
        except Exception:
            _logger.warning("[PORTAL EQUIPMENTS ACCESS] Fecha inválida recibida: %s", value)
            return False

    def _parse_int(self, value):
        if value in (None, False, ''):
            return False
        try:
            return int(value)
        except Exception:
            return False

    def _get_counter_filter_values(self, kwargs=None):
        kwargs = kwargs or {}
        return {
            'fecha_desde': kwargs.get('fecha_desde') or '',
            'fecha_hasta': kwargs.get('fecha_hasta') or '',
            'fecha_facturacion_desde': kwargs.get('fecha_facturacion_desde') or '',
            'fecha_facturacion_hasta': kwargs.get('fecha_facturacion_hasta') or '',
            'anio': kwargs.get('anio') or '',
            'mes': kwargs.get('mes') or '',
            'state': kwargs.get('state') or '',
            'usuario_id': kwargs.get('usuario_id') or '',
            'q': kwargs.get('q') or '',
        }

    def _build_counter_domain_for_portal(self, equipment, kwargs=None):
        kwargs = kwargs or {}

        domain = [('maquina_id', '=', equipment.id)]

        fecha_desde = self._parse_date(kwargs.get('fecha_desde'))
        fecha_hasta = self._parse_date(kwargs.get('fecha_hasta'))
        fecha_facturacion_desde = self._parse_date(kwargs.get('fecha_facturacion_desde'))
        fecha_facturacion_hasta = self._parse_date(kwargs.get('fecha_facturacion_hasta'))

        state = kwargs.get('state')
        q = kwargs.get('q')
        usuario_id = self._parse_int(kwargs.get('usuario_id'))
        anio = self._parse_int(kwargs.get('anio'))
        mes = self._parse_int(kwargs.get('mes'))

        if fecha_desde:
            domain.append(('fecha', '>=', fecha_desde))
        if fecha_hasta:
            domain.append(('fecha', '<=', fecha_hasta))
        if fecha_facturacion_desde:
            domain.append(('fecha_facturacion', '>=', fecha_facturacion_desde))
        if fecha_facturacion_hasta:
            domain.append(('fecha_facturacion', '<=', fecha_facturacion_hasta))

        if anio and not mes:
            domain.append(('fecha_facturacion', '>=', f'{anio}-01-01'))
            domain.append(('fecha_facturacion', '<=', f'{anio}-12-31'))

        if anio and mes and 1 <= mes <= 12:
            ultimo_dia = calendar.monthrange(anio, mes)[1]
            domain.append(('fecha_facturacion', '>=', f'{anio}-{mes:02d}-01'))
            domain.append(('fecha_facturacion', '<=', f'{anio}-{mes:02d}-{ultimo_dia:02d}'))

        if state:
            allowed_states = ['draft', 'confirmed', 'invoiced', 'cancelled']
            if state in allowed_states:
                domain.append(('state', '=', state))

        if usuario_id:
            domain.append(('usuario_detalle_ids.usuario_id', '=', usuario_id))

        if q:
            domain += [
                '|', '|', '|',
                ('name', 'ilike', q),
                ('mes_facturacion', 'ilike', q),
                ('serie', 'ilike', q),
                ('ubicacion', 'ilike', q),
            ]

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] Dominio counters equipment_id=%s domain=%s",
            equipment.id,
            domain,
        )

        return domain

    def _get_query_string(self, kwargs=None):
        kwargs = kwargs or {}
        filter_values = self._get_counter_filter_values(kwargs)
        clean = {k: v for k, v in filter_values.items() if v not in (None, False, '')}
        if not clean:
            return ''
        return urlencode(clean)

    def _get_url_with_filters(self, base_url, kwargs=None):
        query_string = self._get_query_string(kwargs)
        if query_string:
            return f'{base_url}?{query_string}'
        return base_url

    def _check_download_permission(self):
        user = request.env.user
        if not user.has_group('base.group_portal'):
            return True
        partner = user.partner_id
        if not hasattr(partner, 'allow_downloads'):
            return False
        return bool(partner.allow_downloads)

    def _get_user_options(self, equipment):
        if 'copier.machine.user' not in request.env:
            return request.env['res.partner'].sudo().browse([])
        return request.env['copier.machine.user'].sudo().search(
            [('maquina_id', '=', equipment.id)],
            order='name asc',
        )

    def _get_summary_values(self, counters):
        total_bn = sum(counters.mapped('total_copias_bn')) if counters else 0
        total_color = sum(counters.mapped('total_copias_color')) if counters else 0

        user_totals = {}
        for counter in counters:
            for detail in counter.usuario_detalle_ids:
                name = detail.usuario_id.name or 'Sin usuario'
                total = (detail.cantidad_bn or 0) + (detail.cantidad_color or 0)
                user_totals[name] = user_totals.get(name, 0) + total

        top_user = False
        if user_totals:
            top_name = max(user_totals, key=user_totals.get)
            top_user = {'name': top_name, 'total': user_totals[top_name]}

        return {
            'counter_count': len(counters),
            'total_bn': total_bn,
            'total_color': total_color,
            'total_general': total_bn + total_color,
            'top_user': top_user,
        }

    def _build_chart_data_for_counters(self, equipment, counters):
        monthly_data = []
        yearly_data = []
        month_dict = {}
        year_dict = {}

        counters_with_users = counters.filtered(lambda c: c.usuario_detalle_ids)
        confirmed_counters = counters.filtered(lambda c: c.state in ('confirmed', 'invoiced'))

        for counter in confirmed_counters:
            fecha = counter.fecha_facturacion or counter.fecha
            if not fecha:
                continue

            year = fecha.year
            month = fecha.month
            month_key = f"{year}-{month:02d}"
            month_name = counter.mes_facturacion or f"{month:02d}/{year}"

            if month_key not in month_dict:
                month_dict[month_key] = {'key': month_key, 'name': month_name, 'bn': 0, 'color': 0, 'total': 0}

            month_dict[month_key]['bn'] += counter.total_copias_bn or 0
            month_dict[month_key]['color'] += counter.total_copias_color or 0
            month_dict[month_key]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

            if year not in year_dict:
                year_dict[year] = {'name': str(year), 'bn': 0, 'color': 0, 'total': 0}

            year_dict[year]['bn'] += counter.total_copias_bn or 0
            year_dict[year]['color'] += counter.total_copias_color or 0
            year_dict[year]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

        for key in sorted(month_dict.keys()):
            monthly_data.append(month_dict[key])

        for key in sorted(year_dict.keys()):
            yearly_data.append(year_dict[key])

        chart_user_data = []
        if counters_with_users:
            first = counters_with_users[0]
            if first.usuario_detalle_ids:
                for user_detail in first.usuario_detalle_ids:
                    total = (user_detail.cantidad_bn or 0) + (user_detail.cantidad_color or 0)
                    chart_user_data.append({
                        'name': user_detail.usuario_id.name or 'Sin usuario',
                        'copies': total,
                        'total': total,
                        'bn': user_detail.cantidad_bn or 0,
                        'color': user_detail.cantidad_color or 0,
                    })

        monthly_user_data = defaultdict(lambda: defaultdict(int))
        all_user_data_map = {}

        for counter in counters_with_users:
            fecha = counter.fecha_facturacion or counter.fecha

            if counter.mes_facturacion:
                mes_label = counter.mes_facturacion
            elif fecha:
                mes_label = fecha.strftime('%m/%Y')
            else:
                mes_label = 'Sin fecha'

            mes_key = fecha.strftime('%Y-%m') if fecha else mes_label

            if mes_key not in all_user_data_map:
                all_user_data_map[mes_key] = {
                    'key': mes_key,
                    'month': mes_label,
                    'date': str(counter.fecha or ''),
                    'name': counter.name or '',
                    'users': [],
                }

            for detalle in counter.usuario_detalle_ids:
                nombre = detalle.usuario_id.name or 'Sin nombre'
                total = (detalle.cantidad_bn or 0) + (detalle.cantidad_color or 0)
                monthly_user_data[mes_label][nombre] += total
                all_user_data_map[mes_key]['users'].append({
                    'name': nombre,
                    'bn': detalle.cantidad_bn or 0,
                    'color': detalle.cantidad_color or 0,
                    'total': total,
                    'copies': total,
                })

        labels = sorted(monthly_user_data.keys())
        usuarios_unicos = sorted({u for datos in monthly_user_data.values() for u in datos})

        datasets = []
        for usuario in usuarios_unicos:
            datasets.append({
                'label': usuario,
                'data': [monthly_user_data[mes].get(usuario, 0) for mes in labels],
            })

        all_user_data = [all_user_data_map[key] for key in sorted(all_user_data_map.keys())]

        equipment_ranking = []
        try:
            Equip = request.env['copier.company'].sudo()
            accessible_equipments = Equip.search(self._get_equipment_domain_for_portal(only_rented=True))

            ranking_counters = request.env['copier.counter'].sudo().search([
                ('maquina_id', 'in', accessible_equipments.ids),
                ('state', 'in', ['confirmed', 'invoiced']),
            ])

            machine_totals = {}
            for counter in ranking_counters:
                machine = counter.maquina_id
                if not machine:
                    continue

                name_parts = []
                if machine.serie_id:
                    name_parts.append(machine.serie_id)
                if machine.name and machine.name.name:
                    name_parts.append(machine.name.name)

                machine_name = ' - '.join(name_parts) or machine.display_name or f'Equipo {machine.id}'

                if machine_name not in machine_totals:
                    machine_totals[machine_name] = {'name': machine_name, 'bn': 0, 'color': 0, 'total': 0}

                machine_totals[machine_name]['bn'] += counter.total_copias_bn or 0
                machine_totals[machine_name]['color'] += counter.total_copias_color or 0
                machine_totals[machine_name]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

            equipment_ranking = sorted(machine_totals.values(), key=lambda item: item['total'], reverse=True)[:20]

        except Exception as e:
            _logger.exception("[PORTAL EQUIPMENTS ACCESS] Error generando ranking de equipos: %s", str(e))
            equipment_ranking = []

        return {
            'monthly': monthly_data,
            'yearly': yearly_data,
            'by_user': chart_user_data,
            'by_user_monthly': {'labels': labels, 'datasets': datasets},
            'all_user_data': all_user_data,
            'by_equipment': equipment_ranking,
        }

    # =========================================================================
    # FASE 07 - HISTORIAL DE CONTADORES
    # =========================================================================

    @http.route(['/my/copier/equipment/<int:equipment_id>/counters'], type='http', auth="user", website=True)
    def portal_equipment_counters(self, equipment_id, **kw):
        _logger.info("=== INICIANDO portal_equipment_counters ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kw: %s", equipment_id, kw)

        try:
            try:
                equipment_sudo = self._get_equipment_for_portal(equipment_id)
                if not equipment_sudo:
                    return request.redirect('/my')
            except AccessError as e:
                _logger.error(
                    "[PORTAL EQUIPMENTS ACCESS] Error de acceso para equipo ID %s: %s",
                    equipment_id, str(e),
                )
                return request.redirect('/my')

            values = self._prepare_portal_layout_values()

            if 'copier.counter' not in request.env:
                _logger.error("Modelo copier.counter no encontrado")
                counters = request.env['ir.ui.view'].sudo().browse([])
                chart_data = {
                    'monthly': [], 'yearly': [], 'by_user': [],
                    'by_user_monthly': {'labels': [], 'datasets': []},
                    'all_user_data': [], 'by_equipment': [],
                }
            else:
                try:
                    counter_domain = self._build_counter_domain_for_portal(equipment_sudo, kw)
                    counters = request.env['copier.counter'].sudo().search(
                        counter_domain, order='fecha desc, id desc',
                    )

                    _logger.info(
                        "[PORTAL EQUIPMENTS ACCESS] Contadores encontrados=%s ids=%s",
                        len(counters), counters.ids,
                    )

                    chart_data = self._build_chart_data_for_counters(equipment_sudo, counters)

                except Exception as e:
                    _logger.exception(
                        "[PORTAL EQUIPMENTS ACCESS] Error al buscar contadores o preparar gráficos: %s",
                        str(e),
                    )
                    counters = request.env['copier.counter'].sudo().browse([])
                    chart_data = {
                        'monthly': [], 'yearly': [], 'by_user': [],
                        'by_user_monthly': {'labels': [], 'datasets': []},
                        'all_user_data': [], 'by_equipment': [],
                    }

            filter_values = self._get_counter_filter_values(kw)
            pdf_url = self._get_url_with_filters(
                f'/my/copier/equipment/{equipment_sudo.id}/counters/pdf', kw)
            xlsx_url = self._get_url_with_filters(
                f'/my/copier/equipment/{equipment_sudo.id}/counters/xlsx', kw)

            values.update({
                'equipment': equipment_sudo,
                'counters': counters,
                'page_name': 'equipment_counters',
                'today': fields.Date.today(),
                'chart_data': json.dumps(chart_data),
                'filter_values': filter_values,
                'user_options': self._get_user_options(equipment_sudo),
                'can_download': self._check_download_permission(),
                'pdf_url': pdf_url,
                'xlsx_url': xlsx_url,
                'summary': self._get_summary_values(counters),
            })

            template = 'copier_company.portal_my_copier_counters'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                _logger.error("¡ERROR! Template %s no encontrado", template)
                return request.redirect(f'/my/copier/equipment/{equipment_id}')

            return request.render(template, values)

        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en portal_equipment_counters!: %s", str(e))
            return request.redirect('/my')

    # =========================================================================
    # FASE 08 - RUTAS PÚBLICAS
    # =========================================================================

    @http.route(['/public/equipment_menu'], type='http', auth="public", website=True)
    def public_equipment_menu(self, copier_company_id=None, **kw):
        _logger.info("=== INICIANDO public_equipment_menu ===")
        try:
            if not copier_company_id:
                return request.redirect('/')

            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            values = {
                'equipment': equipment,
                'page_title': _('Servicios para su Equipo'),
                'company_name': 'Copier Company',
                'company_phone': '+51 975 399 303',
                'company_email': 'info@copiercompanysac.com',
                'company_website': 'https://copiercompanysac.com'
            }

            template = 'copier_company.portal_equipment_menu'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                return request.redirect('/')

            return request.render(template, values)

        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_equipment_menu!: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/remote_assistance'], type='http', auth="public", website=True)
    def public_remote_assistance(self, copier_company_id=None, **kw):
        _logger.info("=== INICIANDO public_remote_assistance ===")
        try:
            if not copier_company_id:
                return request.redirect('/')

            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'ip': self._safe_get_text(equipment.ip_id) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }

            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'page_title': _('Solicitar Asistencia Remota'),
            }

            if request.httprequest.method == 'POST':
                try:
                    form_data = {
                        'equipment_id': int(copier_company_id),
                        'contact_name': kw.get('contact_name', '').strip(),
                        'contact_email': kw.get('contact_email', '').strip(),
                        'contact_phone': kw.get('contact_phone', '').strip(),
                        'assistance_type': kw.get('assistance_type', 'general'),
                        'problem_description': kw.get('problem_description', '').strip(),
                        'priority': kw.get('priority', 'medium'),
                        'anydesk_id': kw.get('anydesk_id', '').strip(),
                        'username': kw.get('username', '').strip(),
                        'user_password': kw.get('user_password', '').strip(),
                        'scanner_email': kw.get('scanner_email', '').strip(),
                        'scanner_password': kw.get('scanner_password', '').strip(),
                    }

                    if not form_data['contact_name']:
                        values['error_message'] = _("El nombre de contacto es requerido.")
                        return request.render("copier_company.portal_remote_assistance", values)

                    if not form_data['contact_email']:
                        values['error_message'] = _("El email de contacto es requerido.")
                        return request.render("copier_company.portal_remote_assistance", values)

                    if not form_data['problem_description']:
                        values['error_message'] = _("La descripción del problema es requerida.")
                        return request.render("copier_company.portal_remote_assistance", values)

                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['contact_email']):
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_remote_assistance", values)

                    if form_data['assistance_type'] == 'scanner_email' and not form_data['scanner_email']:
                        values['error_message'] = _("Para configuración de escáner por email, debe proporcionar el email del escáner.")
                        return request.render("copier_company.portal_remote_assistance", values)

                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['contact_email'])], limit=1)
                    if partner:
                        update_vals = {}
                        if partner.name != form_data['contact_name']:
                            update_vals['name'] = form_data['contact_name']
                        if form_data['contact_phone'] and not partner.mobile:
                            update_vals['mobile'] = form_data['contact_phone']
                        if update_vals:
                            partner.sudo().write(update_vals)
                    else:
                        partner = request.env['res.partner'].sudo().create({
                            'name': form_data['contact_name'],
                            'email': form_data['contact_email'],
                            'mobile': form_data['contact_phone'],
                            'is_company': False,
                        })

                    if 'remote.assistance.request' in request.env:
                        assistance_request = request.env['remote.assistance.request'].sudo().create_from_public_form(form_data)
                        try:
                            self._send_technical_notification(assistance_request)
                        except Exception as e:
                            _logger.error("Error enviando notificación técnica: %s", str(e))

                        assistance_types = {
                            'general': 'Asistencia General', 'scanner_email': 'Configuración Escáner por Email',
                            'network': 'Problemas de Red', 'drivers': 'Instalación de Drivers',
                            'printing': 'Problemas de Impresión', 'scanning': 'Problemas de Escaneo',
                            'maintenance': 'Mantenimiento Preventivo', 'other': 'Otro',
                        }

                        values['success_message'] = _(
                            "¡Solicitud de asistencia remota creada exitosamente!<br/><br/>"
                            "<strong>Número de solicitud:</strong> {}<br/>"
                            "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                            "<strong>Tipo de asistencia:</strong> {}<br/>"
                            "<strong>Prioridad:</strong> {}<br/><br/>"
                            "Nuestro equipo técnico se pondrá en contacto contigo pronto.<br/>"
                            "Recibirás actualizaciones en: {}"
                        ).format(
                            assistance_request.secuencia,
                            equipment_data['name'], equipment_data['serie'],
                            assistance_types.get(assistance_request.assistance_type, 'General'),
                            dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media'),
                            form_data['contact_email'],
                        )
                        values['assistance_request'] = assistance_request
                        values['request_data'] = {
                            'secuencia': assistance_request.secuencia,
                            'assistance_type': assistance_types.get(assistance_request.assistance_type, 'General'),
                            'priority': dict(assistance_request._fields['priority'].selection).get(assistance_request.priority, 'Media'),
                            'anydesk_id': assistance_request.anydesk_id or 'No proporcionado',
                            'username': assistance_request.username or 'No proporcionado',
                            'scanner_email': assistance_request.scanner_email or 'No proporcionado',
                        }
                    else:
                        values['error_message'] = _("El servicio de asistencia remota no está disponible en este momento.")

                except Exception as e:
                    _logger.exception("Error procesando formulario de asistencia remota: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario. Por favor verifique los datos e intente nuevamente.")

            template = 'copier_company.portal_remote_assistance'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')

            return request.render(template, values)

        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_remote_assistance!: %s", str(e))
            return request.redirect('/')

    def _send_technical_notification(self, assistance_request):
        _logger.info("=== INICIANDO _send_technical_notification para solicitud %s ===", assistance_request.secuencia)
        try:
            technical_emails = []
            try:
                tech_group = request.env.ref('copier_company.group_technical_support', False)
                if tech_group and tech_group.users:
                    technical_emails = [u.email for u in tech_group.users if u.email]
            except Exception:
                pass
            if not technical_emails:
                technical_emails = [
                    'soporte@copiercompanysac.com',
                    'tecnico@copiercompanysac.com',
                    'administracion@copiercompanysac.com',
                ]

            mail_server = request.env['ir.mail_server'].sudo().search([('name', '=', 'Outlook')], limit=1)
            if not mail_server:
                mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                _logger.error("No hay servidores de correo configurados")
                return False

            assistance_types = {
                'general': 'Asistencia General', 'scanner_email': 'Configuración Escáner por Email',
                'network': 'Problemas de Red', 'drivers': 'Instalación de Drivers',
                'printing': 'Problemas de Impresión', 'scanning': 'Problemas de Escaneo',
                'maintenance': 'Mantenimiento Preventivo', 'other': 'Otro',
            }
            priority_names = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta', 'urgent': 'Urgente'}
            priority_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}

            equipment = assistance_request.equipment_id
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''

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

            access_table = (
                "<table border='1' style='border-collapse:collapse;width:100%'>"
                "<tr style='background:#f0f0f0'><th style='text-align:left;padding:8px'>Dato</th>"
                "<th style='text-align:left;padding:8px'>Información</th></tr>"
                + "".join([r.replace("<td>", "<td style='padding:8px;border:1px solid #ddd;'>")
                            .replace("<tr>", "<tr style='border:1px solid #ddd;'>") for r in access_rows])
                + "</table>"
            ) if access_rows else "<p>No se proporcionaron datos de acceso específicos.</p>"

            email_body = f"""
            <h2>🛠️ Nueva Solicitud de Asistencia Remota</h2>
            <h3>📋 Información de la Solicitud</h3>
            <p><strong>Número:</strong> {assistance_request.secuencia}</p>
            <p><strong>Fecha:</strong> {assistance_request.request_date.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Tipo:</strong> {assistance_types.get(assistance_request.assistance_type, 'General')}</p>
            <p><strong>Prioridad:</strong> {priority_icons.get(assistance_request.priority, '⚪')} {priority_names.get(assistance_request.priority, 'Media')}</p>
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
            </ul>
            <hr/>
            <p><small>Este email fue generado automáticamente desde el portal de equipos de Copier Company.</small></p>
            """

            subject = (f"🛠️ Nueva Solicitud de Asistencia Remota - {assistance_request.secuencia} - "
                       f"{equipment.name.name if equipment.name else 'Equipo'}")
            for email in technical_emails:
                if not email:
                    continue
                try:
                    mail = request.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'email_to': email,
                        'email_from': 'info@copiercompanysac.com',
                        'body_html': email_body,
                        'auto_delete': False,
                        'mail_server_id': mail_server.id,
                    })
                    mail.send()
                except Exception as e:
                    _logger.error("Error enviando notificación a %s: %s", email, str(e))

            return True

        except Exception as e:
            _logger.exception("Error en _send_technical_notification: %s", str(e))
            return False

    @http.route(['/public/request_toner'], type='http', auth="public", website=True)
    def public_request_toner(self, copier_company_id=None, **kw):
        _logger.info("=== INICIANDO public_request_toner ===")
        try:
            if not copier_company_id:
                return request.redirect('/')

            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }

            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'page_title': _('Solicitar Toner'),
            }

            if request.httprequest.method == 'POST':
                try:
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

                    if not form_data['client_name']:
                        values['error_message'] = _("El nombre del solicitante es requerido.")
                        return request.render("copier_company.portal_request_toner", values)
                    if not form_data['client_email']:
                        values['error_message'] = _("El email del solicitante es requerido.")
                        return request.render("copier_company.portal_request_toner", values)
                    if not form_data['toner_type']:
                        values['error_message'] = _("Debe seleccionar el tipo de toner.")
                        return request.render("copier_company.portal_request_toner", values)

                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['client_email']):
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_request_toner", values)

                    if form_data['quantity'] <= 0:
                        values['error_message'] = _("La cantidad debe ser mayor a cero.")
                        return request.render("copier_company.portal_request_toner", values)

                    partner = request.env['res.partner'].sudo().search([('email', '=', form_data['client_email'])], limit=1)
                    if partner:
                        update_vals = {}
                        if partner.name != form_data['client_name']:
                            update_vals['name'] = form_data['client_name']
                        if form_data['client_phone'] and not partner.mobile:
                            update_vals['mobile'] = form_data['client_phone']
                        if update_vals:
                            partner.sudo().write(update_vals)
                    else:
                        partner = request.env['res.partner'].sudo().create({
                            'name': form_data['client_name'],
                            'email': form_data['client_email'],
                            'mobile': form_data['client_phone'],
                            'is_company': False,
                        })

                    if 'toner.request' in request.env:
                        toner_request = request.env['toner.request'].sudo().create_from_public_form(form_data)
                        try:
                            self._send_toner_notification(toner_request)
                        except Exception as e:
                            _logger.error("Error enviando notificación de toner: %s", str(e))

                        toner_types = {
                            'black': 'Negro', 'cyan': 'Cian', 'magenta': 'Magenta',
                            'yellow': 'Amarillo', 'complete_set': 'Juego Completo',
                            'maintenance_kit': 'Kit de Mantenimiento',
                        }

                        values['success_message'] = _(
                            "¡Solicitud de toner creada exitosamente!<br/><br/>"
                            "<strong>Número de solicitud:</strong> {}<br/>"
                            "<strong>Equipo:</strong> {} (Serie: {})<br/>"
                            "<strong>Tipo de toner:</strong> {}<br/>"
                            "<strong>Cantidad:</strong> {}<br/><br/>"
                            "Nuestro equipo se pondrá en contacto contigo para coordinar la entrega.<br/>"
                            "Recibirás actualizaciones en: {}"
                        ).format(
                            toner_request.secuencia,
                            equipment_data['name'], equipment_data['serie'],
                            toner_types.get(toner_request.toner_type, 'Desconocido'),
                            toner_request.quantity,
                            form_data['client_email'],
                        )
                        values['toner_request'] = toner_request
                        values['request_data'] = {
                            'secuencia': toner_request.secuencia,
                            'toner_type': toner_types.get(toner_request.toner_type, 'Desconocido'),
                            'quantity': toner_request.quantity,
                            'urgency': dict(toner_request._fields['urgency'].selection).get(toner_request.urgency, 'Media'),
                            'current_level': dict(toner_request._fields['current_toner_level'].selection).get(
                                toner_request.current_toner_level, 'No especificado') if toner_request.current_toner_level else 'No especificado',
                        }
                    else:
                        values['error_message'] = _("El servicio de solicitud de toner no está disponible en este momento.")

                except Exception as e:
                    _logger.exception("Error procesando formulario de toner: %s", str(e))
                    values['error_message'] = _("Error al procesar el formulario. Por favor verifique los datos e intente nuevamente.")

            template = 'copier_company.portal_request_toner'
            if not request.env['ir.ui.view'].sudo().search([('key', '=', template)]):
                return request.redirect(f'/public/equipment_menu?copier_company_id={copier_company_id}')

            return request.render(template, values)

        except Exception as e:
            _logger.exception("¡EXCEPCIÓN GENERAL en public_request_toner!: %s", str(e))
            return request.redirect('/')

    def _send_toner_notification(self, toner_request):
        _logger.info("=== INICIANDO _send_toner_notification para solicitud %s ===", toner_request.secuencia)
        try:
            logistics_emails = [
                'logistica@copiercompanysac.com',
                'ventas@copiercompanysac.com',
                'administracion@copiercompanysac.com',
            ]

            mail_server = request.env['ir.mail_server'].sudo().search([('name', '=', 'Outlook')], limit=1)
            if not mail_server:
                mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                _logger.error("No hay servidores de correo configurados")
                return False

            toner_types = {
                'black': 'Negro', 'cyan': 'Cian', 'magenta': 'Magenta',
                'yellow': 'Amarillo', 'complete_set': 'Juego Completo',
                'maintenance_kit': 'Kit de Mantenimiento',
            }
            urgency_names = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta', 'urgent': 'Urgente'}
            urgency_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}
            toner_level_names = {
                'empty': 'Vacío (0%)', 'low': 'Bajo (1-10%)', 'medium_low': 'Medio-Bajo (11-25%)',
                'medium': 'Medio (26-50%)', 'high': 'Alto (51-75%)', 'full': 'Lleno (76-100%)',
            }

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
            <p><strong>Cliente:</strong> {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}</p>
            <p><strong>Ubicación:</strong> {equipment.ubicacion or 'Sin ubicación'}</p>
            <h3>👤 Información del Solicitante</h3>
            <p><strong>Nombre:</strong> {toner_request.client_name}</p>
            <p><strong>Email:</strong> {toner_request.client_email}</p>
            <p><strong>Teléfono:</strong> {toner_request.client_phone or 'No proporcionado'}</p>
            <h3>🖨️ Detalles del Toner</h3>
            <p><strong>Tipo:</strong> {toner_types.get(toner_request.toner_type, 'Desconocido')}</p>
            <p><strong>Cantidad:</strong> {toner_request.quantity}</p>
            <p><strong>Nivel Actual:</strong> {toner_level_names.get(toner_request.current_toner_level, 'No especificado') if toner_request.current_toner_level else 'No especificado'}</p>
            {f'<h3>📝 Motivo</h3><p>{toner_request.reason}</p>' if toner_request.reason else ''}
            <h3>⚡ Acciones</h3>
            <ul>
                <li><a href="{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={toner_request.id}&model=toner.request&view_type=form">Ver Solicitud en el Sistema</a></li>
            </ul>
            <hr/><p><small>Generado automáticamente desde el portal de Copier Company.</small></p>
            """

            subject = f'🖨️ Nueva Solicitud de Toner - {toner_request.secuencia} - {equipment.name.name if equipment.name else "Equipo"}'
            for email in logistics_emails:
                if email:
                    try:
                        mail = request.env['mail.mail'].sudo().create({
                            'subject': subject,
                            'email_to': email,
                            'email_from': 'info@copiercompanysac.com',
                            'body_html': email_body,
                            'auto_delete': False,
                            'mail_server_id': mail_server.id,
                        })
                        mail.send()
                    except Exception as e:
                        _logger.error("Error enviando notificación de toner a %s: %s", email, str(e))

            return True

        except Exception as e:
            _logger.exception("Error en _send_toner_notification: %s", str(e))
            return False

    @http.route(['/public/send_whatsapp'], type='http', auth="public", website=True)
    def public_send_whatsapp(self, copier_company_id=None, **kw):
        try:
            if not copier_company_id:
                return request.redirect('/')
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            whatsapp_number = "51999999999"
            message = (
                f"Hola! Necesito soporte para mi equipo:\n\n"
                f"📱 *Información del Equipo:*\n"
                f"• Equipo: {equipment.name.name if equipment.name else 'Sin nombre'}\n"
                f"• Serie: {equipment.serie_id or 'Sin serie'}\n"
                f"• Ubicación: {equipment.ubicacion or 'Sin ubicación'}\n\n"
                f"¿Podrían ayudarme?"
            )
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={werkzeug.urls.url_quote(message)}"
            return request.redirect(whatsapp_url)

        except Exception as e:
            _logger.exception("Error en public_send_whatsapp: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/send_email'], type='http', auth="public", website=True)
    def public_send_email(self, copier_company_id=None, **kw):
        try:
            if not copier_company_id:
                return request.redirect('/')
            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            support_email = "soporte@copiercompanysac.com"
            subject = f"Soporte para equipo {equipment.name.name if equipment.name else 'Sin nombre'} - Serie: {equipment.serie_id or 'Sin serie'}"
            body = (
                f"Estimado equipo de soporte,\n\nSolicito asistencia para mi equipo:\n\n"
                f"- Equipo: {equipment.name.name if equipment.name else 'Sin nombre'}\n"
                f"- Serie: {equipment.serie_id or 'Sin serie'}\n"
                f"- Ubicación: {equipment.ubicacion or 'Sin ubicación'}\n"
                f"- Cliente: {equipment.cliente_id.name if equipment.cliente_id else 'Sin cliente'}\n\n"
                f"DESCRIPCIÓN DEL PROBLEMA:\n[Describa aquí el problema]\n\nSaludos."
            )
            mailto_url = f"mailto:{support_email}?subject={werkzeug.urls.url_quote(subject)}&body={werkzeug.urls.url_quote(body)}"
            return request.redirect(mailto_url)

        except Exception as e:
            _logger.exception("Error en public_send_email: %s", str(e))
            return request.redirect('/')

    @http.route(['/public/upload_counters'], type='http', auth="public", website=True)
    def public_upload_counters(self, copier_company_id=None, **kw):
        _logger.info("=== INICIANDO public_upload_counters ===")
        try:
            if not copier_company_id:
                return request.redirect('/')

            equipment = request.env['copier.company'].sudo().browse(int(copier_company_id))
            if not equipment.exists():
                return request.redirect('/')

            last_counter = None
            last_counter_data = {}

            if 'copier.counter' in request.env:
                try:
                    last_counter = request.env['copier.counter'].sudo().search([
                        ('maquina_id', '=', equipment.id),
                        ('state', 'in', ['confirmed', 'invoiced']),
                    ], order='fecha desc', limit=1)

                    if last_counter:
                        last_counter_data = {
                            'date': last_counter.fecha.strftime('%d/%m/%Y') if last_counter.fecha else 'Sin fecha',
                            'counter_bn': last_counter.contador_actual_bn or 0,
                            'counter_color': last_counter.contador_actual_color or 0,
                            'copies_bn': last_counter.total_copias_bn or 0,
                            'copies_color': last_counter.total_copias_color or 0,
                        }
                except Exception as e:
                    _logger.error("Error buscando último contador: %s", str(e))

            equipment_data = {
                'id': equipment.id,
                'name': self._safe_get_text(equipment.name.name) if equipment.name else 'Equipo sin nombre',
                'serie': self._safe_get_text(equipment.serie_id) or 'Sin serie',
                'marca': self._safe_get_text(equipment.marca_id.name) if equipment.marca_id else 'Sin marca',
                'cliente_name': self._safe_get_text(equipment.cliente_id.name) if equipment.cliente_id else 'Sin cliente',
                'cliente_email': self._safe_get_text(equipment.cliente_id.email) if equipment.cliente_id else '',
                'cliente_phone': self._safe_get_text(equipment.cliente_id.phone) or '',
                'ubicacion': self._safe_get_text(equipment.ubicacion) or 'Sin ubicación',
                'sede': self._safe_get_text(equipment.sede) or '',
                'tipo': 'Color' if equipment.tipo == 'color' else 'Blanco y Negro',
            }

            values = {
                'equipment': equipment,
                'equipment_data': equipment_data,
                'last_counter': last_counter,
                'last_counter_data': last_counter_data,
                'page_title': _('Reportar Contadores'),
            }

            if request.httprequest.method == 'POST':
                try:
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

                    if not form_data['client_name']:
                        values['error_message'] = _("El nombre del reportante es requerido.")
                        return request.render("copier_company.portal_upload_counters", values)
                    if not form_data['client_email']:
                        values['error_message'] = _("El email del reportante es requerido.")
                        return request.render("copier_company.portal_upload_counters", values)
                    if form_data['counter_bn'] < 0:
                        values['error_message'] = _("El contador de blanco y negro no puede ser negativo.")
                        return request.render("copier_company.portal_upload_counters", values)
                    if form_data['counter_color'] < 0:
                        values['error_message'] = _("El contador de color no puede ser negativo.")
                        return request.render("copier_company.portal_upload_counters", values)

                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['client_email']):
                        values['error_message'] = _("El formato del email no es válido.")
                        return request.render("copier_company.portal_upload_counters", values)

                    if last_counter:
                        last_bn = last_counter.contador_actual_bn or 0
                        last_color = last_counter.contador_actual_color or 0
                        if form_data['counter_bn'] < last_bn:
                            values['error_message'] = _(
                                "El contador B/N ({:,}) no puede ser menor al contador anterior ({:,})."
                            ).format(form_data['counter_bn'], last_bn)
                            return request.render("copier_company.portal_upload_counters", values)
                        if form_data['counter_color'] < last_color:
                            values['error_message'] = _(
                                "El contador Color ({:,}) no puede ser menor al contador anterior ({:,})."
                            ).format(form_data['counter_color'], last_color)
                            return request.render("copier_company.portal_upload_counters", values)

                    if form_data['counter_photo'] and hasattr(form_data['counter_photo'], 'read'):
                        try:
                            photo_data = form_data['counter_photo'].read()
                            form_data['counter_photo'] = base64.b64encode(photo_data)
                            form_data['counter_photo_filename'] = 'counter_photo.jpg'
                        except Exception as e:
                            _logger.error("Error procesando imagen: %s", str(e))
                            form_data['counter_photo'] = False
                            form_data['counter_photo_filename'] = False
                    else:
                        form_data['counter_photo'] = False
                        form_data