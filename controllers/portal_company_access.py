# -*- coding: utf-8 -*-
import logging
import json
import calendar
from collections import defaultdict
from urllib.parse import urlencode

from odoo import http, _, fields
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.fields import Domain

# Importa tu controlador original para no perder lógica existente.
# IMPORTANTE: este archivo debe cargarse después de controllers/portal.py
from .portal import CopierPortal as BaseCopierPortal


_logger = logging.getLogger(__name__)


class CopierPortalCompanyAccess(BaseCopierPortal):
    """
    Extensión segura del portal de equipos.

    Corrige:
    - /my/copier/equipments
    - /my/copier/equipment/<id>
    - /my/copier/equipment/<id>/counters

    Objetivo:
    Permitir que un contacto portal vea:
    1. Equipos de su empresa principal.
    2. Equipos de empresas adicionales configuradas en res.partner.portal_empresa_ids.

    No toca rutas públicas como:
    - /public/request_toner
    - /public/remote_assistance
    - /public/upload_counters
    - /public/service_request
    """

    # -------------------------------------------------------------------------
    # HELPERS DE EMPRESAS VISIBLES
    # -------------------------------------------------------------------------

    def _get_allowed_partner_ids_for_portal(self):
        """
        Devuelve las empresas que el contacto portal puede ver.

        Incluye:
        - partner.commercial_partner_id
        - partner.portal_empresa_ids
        """
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
        """
        Dominio de equipos visibles en portal.

        Usuario portal:
            cliente_id.commercial_partner_id in empresas permitidas

        Usuario interno:
            sin restricción de cliente
        """
        user = request.env.user
        domain = []

        if user.has_group('base.group_portal'):
            allowed_partner_ids = self._get_allowed_partner_ids_for_portal()
            domain.append(('cliente_id.commercial_partner_id', 'in', allowed_partner_ids))

        if only_rented:
            domain.append(('estado_maquina_id.name', '=', 'Alquilada'))

        return domain

    def _get_equipment_for_portal(self, equipment_id):
        """
        Obtiene equipo validando acceso portal con empresa principal + empresas visibles.
        """
        equipment = request.env['copier.company'].sudo().browse(int(equipment_id))

        if not equipment.exists():
            return False

        user = request.env.user

        # Usuario interno puede ver todo
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

    # -------------------------------------------------------------------------
    # HOME PORTAL COUNT
    # -------------------------------------------------------------------------

    def _prepare_portal_layout_values(self):
        """
        Corrige el contador de 'Mis Equipos' en /my/home.
        """
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

    # -------------------------------------------------------------------------
    # LISTADO DE EQUIPOS
    # -------------------------------------------------------------------------

    @http.route(['/my/copier/equipments'], type='http', auth='user', website=True)
    def portal_my_equipment(self, **kwargs):
        """
        Lista equipos visibles del contacto portal.

        Antes:
            cliente_id = commercial_partner.id

        Ahora:
            cliente_id.commercial_partner_id in empresas permitidas
        """
        _logger.info("=== INICIANDO portal_my_equipment EXTENDIDO ===")

        page = int(kwargs.get('page', 1))

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

        # --- DOMINIO BASE CON EMPRESAS VISIBLES ---
        domain_base = self._get_equipment_domain_for_portal(only_rented=True)

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] domain_base=%s",
            domain_base,
        )

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

        filterby = kwargs.get('filterby') or 'all'
        if filterby not in searchbar_filters:
            filterby = 'all'

        current_domain = searchbar_filters[filterby]['domain']

        sortby = kwargs.get('sortby') or 'name'
        if sortby not in searchbar_sortings:
            sortby = 'name'

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
            },
            total=total,
            page=page,
            step=step,
        )

        offset = pager.get('offset', 0)

        equipments = Equip.search(
            current_domain,
            order=order,
            limit=step,
            offset=offset,
        )

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] Equipos encontrados=%s ids=%s current_domain=%s",
            len(equipments),
            equipments.ids,
            current_domain,
        )

        # --- CONTAR SERVICIOS POR EQUIPO ---
        service_counts = {}

        if equipments:
            equipment_ids = equipments.ids

            try:
                service_data = request.env['copier.service.request'].sudo()._read_group(
                    [('maquina_id', 'in', equipment_ids)],
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
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'filters': searchbar_filters,
            'filterby': filterby,
            'service_counts': service_counts,
        }

        return request.render('copier_company.portal_my_copier_equipments', values)

    # -------------------------------------------------------------------------
    # DETALLE DE EQUIPO
    # -------------------------------------------------------------------------

    @http.route(['/my/copier/equipment/<int:equipment_id>'], type='http', auth='user', website=True)
    def portal_equipment_detail(self, equipment_id, **kwargs):
        """
        Detalle del equipo validando empresa principal + empresas visibles.
        """
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

    # -------------------------------------------------------------------------
    # HELPERS DE FILTRO PARA CONTADORES
    # -------------------------------------------------------------------------

    def _parse_date(self, value):
        if not value:
            return False

        try:
            return fields.Date.from_string(value)
        except Exception:
            _logger.warning(
                "[PORTAL EQUIPMENTS ACCESS] Fecha inválida recibida: %s",
                value,
            )
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
        """
        Dominio de lecturas para la vista del portal.
        """
        kwargs = kwargs or {}

        domain = [
            ('maquina_id', '=', equipment.id),
        ]

        fecha_desde = self._parse_date(kwargs.get('fecha_desde'))
        fecha_hasta = self._parse_date(kwargs.get('fecha_hasta'))
        fecha_facturacion_desde = self._parse_date(kwargs.get('fecha_facturacion_desde'))
        fecha_facturacion_hasta = self._parse_date(kwargs.get('fecha_facturacion_hasta'))

        state = kwargs.get('state')
        q = kwargs.get('q')
        usuario_id = self._parse_int(kwargs.get('usuario_id'))
        anio = self._parse_int(kwargs.get('anio'))
        mes = self._parse_int(kwargs.get('mes'))

        # Fecha de lectura
        if fecha_desde:
            domain.append(('fecha', '>=', fecha_desde))

        if fecha_hasta:
            domain.append(('fecha', '<=', fecha_hasta))

        # Fecha de facturación directa
        if fecha_facturacion_desde:
            domain.append(('fecha_facturacion', '>=', fecha_facturacion_desde))

        if fecha_facturacion_hasta:
            domain.append(('fecha_facturacion', '<=', fecha_facturacion_hasta))

        # Año / mes de facturación
        if anio and not mes:
            domain.append(('fecha_facturacion', '>=', f'{anio}-01-01'))
            domain.append(('fecha_facturacion', '<=', f'{anio}-12-31'))

        if anio and mes and 1 <= mes <= 12:
            ultimo_dia = calendar.monthrange(anio, mes)[1]
            domain.append(('fecha_facturacion', '>=', f'{anio}-{mes:02d}-01'))
            domain.append(('fecha_facturacion', '<=', f'{anio}-{mes:02d}-{ultimo_dia:02d}'))

        # Estado
        if state:
            allowed_states = ['draft', 'confirmed', 'invoiced', 'cancelled']
            if state in allowed_states:
                domain.append(('state', '=', state))

        # Usuario interno
        if usuario_id:
            domain.append(('usuario_detalle_ids.usuario_id', '=', usuario_id))

        # Búsqueda rápida
        if q:
            domain += [
                '|', '|', '|',
                ('name', 'ilike', q),
                ('mes_facturacion', 'ilike', q),
                ('serie', 'ilike', q),
                ('ubicacion', 'ilike', q),
            ]

        _logger.info(
            "[PORTAL EQUIPMENTS ACCESS] Dominio counters equipment_id=%s kwargs=%s domain=%s",
            equipment.id,
            kwargs,
            domain,
        )

        return domain

    def _get_query_string(self, kwargs=None):
        kwargs = kwargs or {}
        filter_values = self._get_counter_filter_values(kwargs)

        clean = {}
        for key, value in filter_values.items():
            if value not in (None, False, ''):
                clean[key] = value

        if not clean:
            return ''

        return urlencode(clean)

    def _get_url_with_filters(self, base_url, kwargs=None):
        query_string = self._get_query_string(kwargs)
        if query_string:
            return f'{base_url}?{query_string}'
        return base_url

    def _check_download_permission(self):
        """
        Permiso de descargas.

        Usuario interno:
            permitido

        Usuario portal:
            depende de partner.allow_downloads
        """
        user = request.env.user

        if not user.has_group('base.group_portal'):
            return True

        partner = user.partner_id

        if not hasattr(partner, 'allow_downloads'):
            return False

        return bool(partner.allow_downloads)

    def _get_user_options(self, equipment):
        """
        Usuarios internos asociados al equipo.
        """
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
            top_user = {
                'name': top_name,
                'total': user_totals[top_name],
            }

        return {
            'counter_count': len(counters),
            'total_bn': total_bn,
            'total_color': total_color,
            'total_general': total_bn + total_color,
            'top_user': top_user,
        }

    def _build_chart_data_for_counters(self, equipment, counters):
        """
        Mantiene la lógica existente de gráficos:
        - monthly
        - yearly
        - by_user
        - by_user_monthly

        Agrega:
        - by_equipment
        - all_user_data
        """
        monthly_data = []
        yearly_data = []
        month_dict = {}
        year_dict = {}

        counters_with_users = counters.filtered(lambda c: c.usuario_detalle_ids)
        confirmed_counters = counters.filtered(lambda c: c.state in ('confirmed', 'invoiced'))

        # ---------------------------------------------------------------------
        # Mensual / Anual
        # ---------------------------------------------------------------------
        for counter in confirmed_counters:
            fecha = counter.fecha_facturacion or counter.fecha
            if not fecha:
                continue

            year = fecha.year
            month = fecha.month
            month_key = f"{year}-{month:02d}"
            month_name = counter.mes_facturacion or f"{month:02d}/{year}"

            if month_key not in month_dict:
                month_dict[month_key] = {
                    'key': month_key,
                    'name': month_name,
                    'bn': 0,
                    'color': 0,
                    'total': 0,
                }

            month_dict[month_key]['bn'] += counter.total_copias_bn or 0
            month_dict[month_key]['color'] += counter.total_copias_color or 0
            month_dict[month_key]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

            if year not in year_dict:
                year_dict[year] = {
                    'name': str(year),
                    'bn': 0,
                    'color': 0,
                    'total': 0,
                }

            year_dict[year]['bn'] += counter.total_copias_bn or 0
            year_dict[year]['color'] += counter.total_copias_color or 0
            year_dict[year]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

        for key in sorted(month_dict.keys()):
            monthly_data.append(month_dict[key])

        for key in sorted(year_dict.keys()):
            yearly_data.append(year_dict[key])

        # ---------------------------------------------------------------------
        # Último contador con usuarios
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # Mensual por usuario
        # ---------------------------------------------------------------------
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

        all_user_data = [
            all_user_data_map[key]
            for key in sorted(all_user_data_map.keys())
        ]

        # ---------------------------------------------------------------------
        # Ranking por equipos visibles
        # ---------------------------------------------------------------------
        equipment_ranking = []

        try:
            Equip = request.env['copier.company'].sudo()
            accessible_equipment_domain = self._get_equipment_domain_for_portal(only_rented=True)
            accessible_equipments = Equip.search(accessible_equipment_domain)

            ranking_domain = [
                ('maquina_id', 'in', accessible_equipments.ids),
                ('state', 'in', ['confirmed', 'invoiced']),
            ]

            ranking_counters = request.env['copier.counter'].sudo().search(ranking_domain)

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
                    machine_totals[machine_name] = {
                        'name': machine_name,
                        'bn': 0,
                        'color': 0,
                        'total': 0,
                    }

                machine_totals[machine_name]['bn'] += counter.total_copias_bn or 0
                machine_totals[machine_name]['color'] += counter.total_copias_color or 0
                machine_totals[machine_name]['total'] += (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

            equipment_ranking = sorted(
                machine_totals.values(),
                key=lambda item: item['total'],
                reverse=True,
            )[:20]

        except Exception as e:
            _logger.exception(
                "[PORTAL EQUIPMENTS ACCESS] Error generando ranking de equipos: %s",
                str(e),
            )
            equipment_ranking = []

        chart_data = {
            'monthly': monthly_data,
            'yearly': yearly_data,
            'by_user': chart_user_data,
            'by_user_monthly': {
                'labels': labels,
                'datasets': datasets,
            },
            'all_user_data': all_user_data,
            'by_equipment': equipment_ranking,
        }

        return chart_data

    # -------------------------------------------------------------------------
    # HISTORIAL DE CONTADORES
    # -------------------------------------------------------------------------

    @http.route(['/my/copier/equipment/<int:equipment_id>/counters'], type='http', auth="user", website=True)
    def portal_equipment_counters(self, equipment_id, **kw):
        """
        Historial de contadores con acceso corregido para empresas visibles.
        """
        _logger.info("=== INICIANDO portal_equipment_counters EXTENDIDO ===")
        _logger.info("Parámetros recibidos - equipment_id: %s, kw: %s", equipment_id, kw)

        try:
            try:
                equipment_sudo = self._get_equipment_for_portal(equipment_id)
                if not equipment_sudo:
                    return request.redirect('/my')

                _logger.info(
                    "[PORTAL EQUIPMENTS ACCESS] Acceso verificado para equipo ID: %s",
                    equipment_id,
                )

            except AccessError as e:
                _logger.error(
                    "[PORTAL EQUIPMENTS ACCESS] Error de acceso para equipo ID %s: %s",
                    equipment_id,
                    str(e),
                )
                return request.redirect('/my')

            values = self._prepare_portal_layout_values()

            if 'copier.counter' not in request.env:
                _logger.error("Modelo copier.counter no encontrado")
                counters = request.env['ir.ui.view'].sudo().browse([])
                chart_data = {
                    'monthly': [],
                    'yearly': [],
                    'by_user': [],
                    'by_user_monthly': {
                        'labels': [],
                        'datasets': [],
                    },
                    'all_user_data': [],
                    'by_equipment': [],
                }
            else:
                try:
                    _logger.info("Buscando contadores para el equipo ID: %s", equipment_id)

                    counter_domain = self._build_counter_domain_for_portal(equipment_sudo, kw)

                    counters = request.env['copier.counter'].sudo().search(
                        counter_domain,
                        order='fecha desc, id desc',
                    )

                    _logger.info(
                        "[PORTAL EQUIPMENTS ACCESS] Contadores encontrados=%s ids=%s domain=%s",
                        len(counters),
                        counters.ids,
                        counter_domain,
                    )

                    counters_with_users = counters.filtered(lambda c: c.usuario_detalle_ids)

                    _logger.info(
                        "[PORTAL EQUIPMENTS ACCESS] Contadores con usuarios=%s",
                        len(counters_with_users),
                    )

                    for counter in counters_with_users:
                        _logger.info(
                            "[PORTAL EQUIPMENTS ACCESS] Contador con usuarios: ID=%s Nombre=%s Mes=%s Usuarios=%s Estado=%s",
                            counter.id,
                            counter.name,
                            counter.mes_facturacion,
                            len(counter.usuario_detalle_ids),
                            counter.state,
                        )

                        for user_detail in counter.usuario_detalle_ids:
                            _logger.info(
                                "[PORTAL EQUIPMENTS ACCESS]   Usuario=%s B/N=%s Color=%s",
                                user_detail.usuario_id.name,
                                user_detail.cantidad_bn,
                                user_detail.cantidad_color,
                            )

                    chart_data = self._build_chart_data_for_counters(equipment_sudo, counters)

                    _logger.info(
                        "[PORTAL EQUIPMENTS ACCESS] Datos gráficos: monthly=%s yearly=%s by_user=%s",
                        len(chart_data.get('monthly', [])),
                        len(chart_data.get('yearly', [])),
                        len(chart_data.get('by_user', [])),
                    )

                except Exception as e:
                    _logger.exception(
                        "[PORTAL EQUIPMENTS ACCESS] Error al buscar contadores o preparar gráficos: %s",
                        str(e),
                    )
                    counters = request.env['copier.counter'].sudo().browse([])
                    chart_data = {
                        'monthly': [],
                        'yearly': [],
                        'by_user': [],
                        'by_user_monthly': {
                            'labels': [],
                            'datasets': [],
                        },
                        'all_user_data': [],
                        'by_equipment': [],
                    }

            filter_values = self._get_counter_filter_values(kw)

            pdf_url = self._get_url_with_filters(
                f'/my/copier/equipment/{equipment_sudo.id}/counters/pdf',
                kw,
            )

            xlsx_url = self._get_url_with_filters(
                f'/my/copier/equipment/{equipment_sudo.id}/counters/xlsx',
                kw,
            )

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

            _logger.info("Renderizando template: %s", template)
            _logger.info("=== FINALIZANDO portal_equipment_counters EXTENDIDO ===")

            return request.render(template, values)

        except Exception as e:
            _logger.exception(
                "¡EXCEPCIÓN GENERAL en portal_equipment_counters EXTENDIDO!: %s",
                str(e),
            )
            return request.redirect('/my')