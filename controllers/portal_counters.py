# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError
from collections import defaultdict
from urllib.parse import urlencode
import calendar
import io
import json
import logging
import xlsxwriter

_logger = logging.getLogger(__name__)


class CopierCounterPortal(http.Controller):

    # -------------------------------------------------------------------------
    # HELPERS DE ACCESO PORTAL
    # -------------------------------------------------------------------------

    def _is_portal_user(self):
        return request.env.user.has_group('base.group_portal')

    def _get_portal_partner(self):
        return request.env.user.partner_id

    def _get_allowed_partner_ids_for_portal(self):
        """
        Empresas que el contacto portal puede ver:
        - Su commercial_partner_id.
        - Empresas adicionales configuradas en portal_empresa_ids.
        """
        partner = self._get_portal_partner()
        commercial_partner = partner.commercial_partner_id

        allowed_partner_ids = set()

        if commercial_partner:
            allowed_partner_ids.add(commercial_partner.id)

        if hasattr(partner, 'portal_empresa_ids'):
            allowed_partner_ids.update(partner.portal_empresa_ids.ids)

        return list(allowed_partner_ids)

    def _check_download_permission(self):
        """
        Permiso para descargar PDF/Excel.
        Usuarios internos siempre pueden descargar.
        Usuarios portal dependen de res.partner.allow_downloads.
        """
        user = request.env.user

        if not user.has_group('base.group_portal'):
            return True

        partner = user.partner_id

        if not hasattr(partner, 'allow_downloads'):
            _logger.warning(
                "[PORTAL COUNTERS] Campo allow_downloads no existe en res.partner. "
                "Descarga bloqueada. user_id=%s partner_id=%s",
                user.id,
                partner.id,
            )
            return False

        return bool(partner.allow_downloads)

    def _raise_if_no_download_permission(self):
        if not self._check_download_permission():
            raise AccessError("No tiene permisos para descargar archivos.")

    def _get_equipment_for_portal(self, equipment_id):
        """
        Valida acceso al equipo.
        Portal puede acceder si la máquina pertenece a:
        - Empresa principal del contacto.
        - Empresas visibles adicionales.
        """
        Equipment = request.env['copier.company'].sudo()
        equipment = Equipment.browse(int(equipment_id))

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
                "[PORTAL COUNTERS] Acceso denegado a equipo. "
                "user_id=%s partner_id=%s equipment_id=%s cliente_id=%s allowed_partner_ids=%s",
                user.id,
                user.partner_id.id,
                equipment.id,
                equipment.cliente_id.id if equipment.cliente_id else False,
                allowed_partner_ids,
            )
            raise AccessError("No tiene permisos para acceder a este equipo.")

        return equipment

    def _get_accessible_equipment_domain(self):
        """
        Dominio de máquinas visibles para el usuario actual.
        Se usa para ranking general de equipos.
        """
        user = request.env.user

        if not user.has_group('base.group_portal'):
            return []

        allowed_partner_ids = self._get_allowed_partner_ids_for_portal()

        return [
            ('cliente_id.commercial_partner_id', 'in', allowed_partner_ids),
        ]

    def _check_counter_access(self, counter):
        """
        Valida acceso a una lectura individual.
        """
        if not counter or not counter.exists():
            return False

        user = request.env.user

        if not user.has_group('base.group_portal'):
            return True

        allowed_partner_ids = self._get_allowed_partner_ids_for_portal()

        equipment = counter.maquina_id
        equipment_partner = equipment.cliente_id.commercial_partner_id if equipment and equipment.cliente_id else False
        equipment_partner_id = equipment_partner.id if equipment_partner else False

        if equipment_partner_id and equipment_partner_id in allowed_partner_ids:
            return True

        counter_partner = counter.cliente_id.commercial_partner_id if counter.cliente_id else False
        counter_partner_id = counter_partner.id if counter_partner else False

        if counter_partner_id and counter_partner_id in allowed_partner_ids:
            return True

        _logger.warning(
            "[PORTAL COUNTERS] Acceso denegado a lectura. "
            "user_id=%s partner_id=%s counter_id=%s cliente_id=%s maquina_id=%s allowed_partner_ids=%s",
            user.id,
            user.partner_id.id,
            counter.id,
            counter.cliente_id.id if counter.cliente_id else False,
            counter.maquina_id.id if counter.maquina_id else False,
            allowed_partner_ids,
        )

        return False

    # -------------------------------------------------------------------------
    # HELPERS DE FILTRO
    # -------------------------------------------------------------------------

    def _parse_date(self, value):
        if not value:
            return False

        try:
            return fields.Date.from_string(value)
        except Exception:
            _logger.warning("[PORTAL COUNTERS] Fecha inválida recibida: %s", value)
            return False

    def _parse_int(self, value):
        if value in (None, False, ''):
            return False

        try:
            return int(value)
        except Exception:
            return False

    def _get_filter_values(self, kwargs=None):
        """
        Normaliza filtros recibidos por querystring.

        Soporta:
        - fecha_desde / fecha_hasta: fecha de lectura.
        - fecha_facturacion_desde / fecha_facturacion_hasta: fecha de facturación.
        - anio: año de facturación.
        - mes: mes numérico de facturación.
        - state.
        - usuario_id.
        - q.
        """
        kwargs = kwargs or {}

        values = {
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

        return values

    def _build_counter_domain(self, equipment=None, kwargs=None):
        """
        Dominio central para vista, gráficos, PDF y Excel.

        Si equipment existe, filtra por esa máquina.
        Si equipment no existe, sirve para ranking general con dominio adicional externo.
        """
        kwargs = kwargs or {}

        domain = []

        if equipment:
            domain.append(('maquina_id', '=', equipment.id))

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
            "[PORTAL COUNTERS] Dominio generado. equipment_id=%s kwargs=%s domain=%s",
            equipment.id if equipment else False,
            kwargs,
            domain,
        )

        return domain

    def _get_counters_for_equipment(self, equipment, kwargs=None):
        Counter = request.env['copier.counter'].sudo()
        domain = self._build_counter_domain(equipment, kwargs)

        return Counter.search(
            domain,
            order='fecha_facturacion desc, fecha desc, id desc'
        )

    def _get_global_counters_for_ranking(self, kwargs=None):
        """
        Lecturas visibles para ranking general de equipos.
        No reemplaza la vista por equipo: solo alimenta el gráfico
        'qué máquina imprimió más' dentro del rango filtrado.
        """
        Counter = request.env['copier.counter'].sudo()
        Equipment = request.env['copier.company'].sudo()

        equipment_domain = self._get_accessible_equipment_domain()
        accessible_equipments = Equipment.search(equipment_domain)

        if not accessible_equipments:
            return Counter.browse([])

        domain = self._build_counter_domain(None, kwargs)
        domain.append(('maquina_id', 'in', accessible_equipments.ids))

        return Counter.search(domain)

    def _get_query_string(self, kwargs=None):
        """
        Mantiene los filtros actuales para exportar PDF/Excel.
        """
        kwargs = kwargs or {}
        filter_values = self._get_filter_values(kwargs)

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

    def _get_report_ref(self):
        return 'copier_company.action_report_counter_readings_portal'

    def _get_equipment_filename_value(self, equipment):
        return equipment.serie_id or equipment.id

    def _get_month_name(self, month):
        meses = {
            1: 'Enero',
            2: 'Febrero',
            3: 'Marzo',
            4: 'Abril',
            5: 'Mayo',
            6: 'Junio',
            7: 'Julio',
            8: 'Agosto',
            9: 'Septiembre',
            10: 'Octubre',
            11: 'Noviembre',
            12: 'Diciembre',
        }
        return meses.get(month, '')

    # -------------------------------------------------------------------------
    # HELPERS DE DATOS PARA GRÁFICOS
    # -------------------------------------------------------------------------

    def _get_counter_total(self, counter):
        return (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

    def _build_chart_data(self, equipment, counters, kwargs=None):
        """
        Construye datos para:
        - consumo mensual del equipo;
        - consumo anual del equipo;
        - ranking de usuarios del equipo;
        - usuario por mes;
        - ranking de máquinas visibles.
        """
        kwargs = kwargs or {}

        monthly_map = {}
        yearly_map = {}
        user_map = {}
        user_monthly_map = {}
        all_user_months = {}
        equipment_map = {}

        # ---------------------------------------------------------
        # Datos por lectura del equipo actual
        # ---------------------------------------------------------
        for counter in counters:
            fecha_ref = counter.fecha_facturacion or counter.fecha or counter.create_date
            if not fecha_ref:
                continue

            year = fecha_ref.year
            month = fecha_ref.month
            month_key = f'{year}-{month:02d}'
            month_label = counter.mes_facturacion or f'{self._get_month_name(month)} {year}'

            if month_key not in monthly_map:
                monthly_map[month_key] = {
                    'key': month_key,
                    'name': month_label,
                    'bn': 0,
                    'color': 0,
                    'total': 0,
                }

            monthly_map[month_key]['bn'] += counter.total_copias_bn or 0
            monthly_map[month_key]['color'] += counter.total_copias_color or 0
            monthly_map[month_key]['total'] += self._get_counter_total(counter)

            if year not in yearly_map:
                yearly_map[year] = {
                    'name': str(year),
                    'bn': 0,
                    'color': 0,
                    'total': 0,
                }

            yearly_map[year]['bn'] += counter.total_copias_bn or 0
            yearly_map[year]['color'] += counter.total_copias_color or 0
            yearly_map[year]['total'] += self._get_counter_total(counter)

            for detail in counter.usuario_detalle_ids:
                user_name = detail.usuario_id.display_name or 'Sin usuario'
                bn = detail.cantidad_bn or 0
                color = detail.cantidad_color or 0
                total = bn + color

                if user_name not in user_map:
                    user_map[user_name] = {
                        'name': user_name,
                        'bn': 0,
                        'color': 0,
                        'total': 0,
                    }

                user_map[user_name]['bn'] += bn
                user_map[user_name]['color'] += color
                user_map[user_name]['total'] += total

                if month_key not in all_user_months:
                    all_user_months[month_key] = {
                        'month': month_label,
                        'key': month_key,
                        'users': [],
                    }

                all_user_months[month_key]['users'].append({
                    'name': user_name,
                    'bn': bn,
                    'color': color,
                    'total': total,
                })

                user_monthly_map.setdefault(user_name, {})
                user_monthly_map[user_name].setdefault(month_key, 0)
                user_monthly_map[user_name][month_key] += total

        # ---------------------------------------------------------
        # Ranking de máquinas visibles en el mismo rango filtrado
        # ---------------------------------------------------------
        ranking_counters = self._get_global_counters_for_ranking(kwargs)

        for counter in ranking_counters:
            machine = counter.maquina_id
            if not machine:
                continue

            label_parts = []
            if machine.serie_id:
                label_parts.append(machine.serie_id)
            if machine.name and machine.name.name:
                label_parts.append(machine.name.name)

            machine_name = ' - '.join(label_parts) or machine.display_name or f'Equipo {machine.id}'

            if machine_name not in equipment_map:
                equipment_map[machine_name] = {
                    'name': machine_name,
                    'bn': 0,
                    'color': 0,
                    'total': 0,
                }

            equipment_map[machine_name]['bn'] += counter.total_copias_bn or 0
            equipment_map[machine_name]['color'] += counter.total_copias_color or 0
            equipment_map[machine_name]['total'] += self._get_counter_total(counter)

        monthly = sorted(monthly_map.values(), key=lambda item: item['key'])
        yearly = sorted(yearly_map.values(), key=lambda item: item['name'])

        by_user = sorted(
            user_map.values(),
            key=lambda item: item['total'],
            reverse=True
        )

        by_equipment = sorted(
            equipment_map.values(),
            key=lambda item: item['total'],
            reverse=True
        )[:20]

        all_user_data = [
            all_user_months[key]
            for key in sorted(all_user_months.keys())
        ]

        user_month_keys = [item['key'] for item in monthly]
        user_month_labels = [item['name'] for item in monthly]

        by_user_monthly = {
            'labels': user_month_labels,
            'datasets': [],
        }

        for user_name, month_values in sorted(user_monthly_map.items()):
            by_user_monthly['datasets'].append({
                'label': user_name,
                'data': [month_values.get(key, 0) for key in user_month_keys],
            })

        return {
            'monthly': monthly,
            'yearly': yearly,
            'by_user': by_user,
            'by_user_monthly': by_user_monthly,
            'all_user_data': all_user_data,
            'by_equipment': by_equipment,
        }

    def _get_summary_values(self, counters, chart_data):
        total_bn = sum(c.total_copias_bn or 0 for c in counters)
        total_color = sum(c.total_copias_color or 0 for c in counters)
        total_general = total_bn + total_color

        top_user = False
        if chart_data.get('by_user'):
            top_user = chart_data['by_user'][0]

        top_equipment = False
        if chart_data.get('by_equipment'):
            top_equipment = chart_data['by_equipment'][0]

        return {
            'counter_count': len(counters),
            'total_bn': total_bn,
            'total_color': total_color,
            'total_general': total_general,
            'top_user': top_user,
            'top_equipment': top_equipment,
        }

    def _get_user_options(self, equipment):
        """
        Opciones para filtro por usuario interno.
        """
        UserModel = request.env['copier.machine.user'].sudo()

        return UserModel.search(
            [('maquina_id', '=', equipment.id)],
            order='name asc'
        )

    # -------------------------------------------------------------------------
    # VISTA PORTAL – HISTORIAL / GRÁFICOS / FILTROS
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters'],
        type='http',
        auth='user',
        website=True
    )
    def portal_equipment_counters(self, equipment_id, **kwargs):
        """
        Vista principal de lecturas del equipo.
        Aplica los mismos filtros que PDF y Excel.
        """
        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment, kwargs)
        chart_data = self._build_chart_data(equipment, counters, kwargs)
        summary = self._get_summary_values(counters, chart_data)

        filter_values = self._get_filter_values(kwargs)
        query_string = self._get_query_string(kwargs)

        pdf_url = self._get_url_with_filters(
            f'/my/copier/equipment/{equipment.id}/counters/pdf',
            kwargs
        )
        xlsx_url = self._get_url_with_filters(
            f'/my/copier/equipment/{equipment.id}/counters/xlsx',
            kwargs
        )

        values = {
            'page_name': 'equipment_counters',
            'equipment': equipment,
            'counters': counters,
            'chart_data': json.dumps(chart_data),
            'filter_values': filter_values,
            'summary': summary,
            'user_options': self._get_user_options(equipment),
            'can_download': self._check_download_permission(),
            'pdf_url': pdf_url,
            'xlsx_url': xlsx_url,
            'query_string': query_string,
        }

        return request.render('copier_company.portal_my_copier_counters', values)

    # -------------------------------------------------------------------------
    # PDF – LECTURAS FILTRADAS DEL EQUIPO
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/pdf'],
        type='http',
        auth='user',
        website=True
    )
    def portal_counters_pdf_all(self, equipment_id, **kwargs):
        self._raise_if_no_download_permission()

        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment, kwargs)
        if not counters:
            return request.not_found()

        report_ref = self._get_report_ref()
        request.env.ref(report_ref)

        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref,
            res_ids=counters.ids,
        )

        filename = f"Lecturas_{self._get_equipment_filename_value(equipment)}.pdf"

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        return request.make_response(pdf_content, headers=headers)

    # -------------------------------------------------------------------------
    # PDF – UNA SOLA LECTURA
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/counter/<int:counter_id>/pdf'],
        type='http',
        auth='user',
        website=True
    )
    def portal_counter_pdf_single(self, counter_id, **kwargs):
        self._raise_if_no_download_permission()

        Counter = request.env['copier.counter'].sudo()
        counter = Counter.browse(int(counter_id))

        if not self._check_counter_access(counter):
            return request.not_found()

        report_ref = self._get_report_ref()
        request.env.ref(report_ref)

        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref,
            res_ids=counter.ids,
        )

        filename = f"Lectura_{counter.name or counter.id}.pdf"

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        return request.make_response(pdf_content, headers=headers)

    # -------------------------------------------------------------------------
    # EXCEL – LECTURAS FILTRADAS DEL EQUIPO
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/xlsx'],
        type='http',
        auth='user',
        website=True
    )
    def portal_counters_xlsx(self, equipment_id, **kwargs):
        self._raise_if_no_download_permission()

        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment, kwargs)
        if not counters:
            return request.not_found()

        filter_values = self._get_filter_values(kwargs)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Lecturas')

        title_fmt = workbook.add_format({
            'bold': True,
            'font_size': 15,
        })
        subtitle_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
        })
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#F3F4F6',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        text_center = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })
        text_left = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
        })
        num_fmt = workbook.add_format({
            'num_format': '#,##0',
            'align': 'right',
            'valign': 'vcenter',
        })

        sheet.write(0, 0, 'Reporte de Lecturas', title_fmt)
        sheet.write(1, 0, 'Cliente:', subtitle_fmt)
        sheet.write(1, 1, equipment.cliente_id.display_name or '', text_left)
        sheet.write(2, 0, 'Serie:', subtitle_fmt)
        sheet.write(2, 1, equipment.serie_id or '', text_left)
        sheet.write(3, 0, 'Ubicación:', subtitle_fmt)
        sheet.write(3, 1, equipment.ubicacion or '', text_left)

        sheet.write(4, 0, 'Filtros:', subtitle_fmt)
        filtros_texto = []
        for key, label in [
            ('fecha_desde', 'Lectura desde'),
            ('fecha_hasta', 'Lectura hasta'),
            ('fecha_facturacion_desde', 'Fact. desde'),
            ('fecha_facturacion_hasta', 'Fact. hasta'),
            ('anio', 'Año'),
            ('mes', 'Mes'),
            ('state', 'Estado'),
            ('usuario_id', 'Usuario'),
            ('q', 'Búsqueda'),
        ]:
            if filter_values.get(key):
                filtros_texto.append(f'{label}: {filter_values.get(key)}')

        sheet.write(4, 1, ' | '.join(filtros_texto) if filtros_texto else 'Sin filtros', text_left)

        row_header = 6

        headers = [
            'Referencia',
            'Fecha Lectura',
            'Fecha Facturación',
            'Mes Facturación',
            'Anterior B/N',
            'Actual B/N',
            'Total B/N',
        ]

        is_color = equipment.tipo == 'color'

        if is_color:
            headers += [
                'Anterior Color',
                'Actual Color',
                'Total Color',
            ]

        headers += [
            'Total General',
            'Estado',
        ]

        for col, title in enumerate(headers):
            sheet.write(row_header, col, title, header_fmt)

        row = row_header + 1

        for counter in counters:
            col = 0

            total_general = (counter.total_copias_bn or 0) + (counter.total_copias_color or 0)

            sheet.write(row, col, counter.name or '', text_left)
            col += 1

            sheet.write(row, col, str(counter.fecha) if counter.fecha else '', text_center)
            col += 1

            sheet.write(row, col, str(counter.fecha_facturacion) if counter.fecha_facturacion else '', text_center)
            col += 1

            sheet.write(row, col, counter.mes_facturacion or '', text_center)
            col += 1

            sheet.write_number(row, col, counter.contador_anterior_bn or 0, num_fmt)
            col += 1

            sheet.write_number(row, col, counter.contador_actual_bn or 0, num_fmt)
            col += 1

            sheet.write_number(row, col, counter.total_copias_bn or 0, num_fmt)
            col += 1

            if is_color:
                sheet.write_number(row, col, counter.contador_anterior_color or 0, num_fmt)
                col += 1

                sheet.write_number(row, col, counter.contador_actual_color or 0, num_fmt)
                col += 1

                sheet.write_number(row, col, counter.total_copias_color or 0, num_fmt)
                col += 1

            sheet.write_number(row, col, total_general, num_fmt)
            col += 1

            sheet.write(row, col, counter.state or '', text_center)

            row += 1

        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 3, 18)
        sheet.set_column(4, 12, 16)
        sheet.freeze_panes(row_header + 1, 0)
        sheet.autofilter(row_header, 0, row - 1, len(headers) - 1)

        workbook.close()

        xlsx_data = output.getvalue()
        output.close()

        filename = f"Lecturas_{self._get_equipment_filename_value(equipment)}.xlsx"

        headers_response = [
            (
                'Content-Type',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        return request.make_response(xlsx_data, headers=headers_response)