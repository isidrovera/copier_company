# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import io
import xlsxwriter
import logging

_logger = logging.getLogger(__name__)


class CopierCounterPortal(http.Controller):

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_equipment_for_portal(self, equipment_id):
        """
        Obtiene la máquina (copier.company) verificando acceso del usuario portal.
        """
        Equipment = request.env['copier.company'].sudo()
        equipment = Equipment.browse(int(equipment_id))

        if not equipment.exists():
            return False

        user = request.env.user

        # Si es usuario portal, solo puede ver sus propias máquinas
        if user.has_group('base.group_portal'):
            partner = user.partner_id
            if equipment.cliente_id.id != partner.id:
                _logger.warning(
                    "Acceso denegado: partner %s intenta ver equipo %s de cliente %s",
                    partner.id, equipment.id, equipment.cliente_id.id
                )
                raise AccessError("No tiene permisos para acceder a este equipo.")

        # Usuarios internos pueden ver todo
        return equipment

    def _get_counters_for_equipment(self, equipment):
        """
        Devuelve los counters (copier.counter) de una máquina dada.
        """
        Counter = request.env['copier.counter'].sudo()
        counters = Counter.search(
            [('maquina_id', '=', equipment.id)],
            order='fecha_facturacion desc, fecha desc, id desc'
        )
        return counters

    def _check_counter_access(self, counter):
        """
        Verifica que el usuario actual tenga acceso a ese counter.
        """
        if not counter or not counter.exists():
            return False

        user = request.env.user

        # Portal solo puede ver lo que pertenece a su partner
        if user.has_group('base.group_portal'):
            partner = user.partner_id
            if counter.cliente_id.id != partner.id:
                _logger.warning(
                    "Acceso denegado: partner %s intenta ver lectura %s de cliente %s",
                    partner.id, counter.id, counter.cliente_id.id
                )
                return False

        return True

    # -------------------------------------------------------------------------
    # PDF – TODAS LAS LECTURAS DEL EQUIPO
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/pdf'],
        type='http', auth='user', website=True
    )
    def portal_counters_pdf_all(self, equipment_id, **kwargs):
        """
        Genera un PDF con TODAS las lecturas del equipo (para portal).
        """
        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            # Sin lecturas: puedes devolver 404 o un PDF vacío; aquí 404 simple
            return request.not_found()

        # xmlid del reporte definido en tu XML
        report_ref = 'copier_company.action_report_counter_readings_portal'

        # Asegurarse de que el reporte existe (si no, lanza error Odoo estándar)
        request.env.ref(report_ref)

        # IMPORTANTE: en tu versión de Odoo la firma es
        # _render_qweb_pdf(report_ref, res_ids=None, data=None)
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref,
            res_ids=counters.ids,
        )

        filename = f"Lecturas_{equipment.serie_id or equipment.id}.pdf"
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
        type='http', auth='user', website=True
    )
    def portal_counter_pdf_single(self, counter_id, **kwargs):
        """
        Genera un PDF SOLO con la lectura seleccionada (una fila).
        """
        Counter = request.env['copier.counter'].sudo()
        counter = Counter.browse(int(counter_id))

        if not self._check_counter_access(counter):
            return request.not_found()

        report_ref = 'copier_company.action_report_counter_readings_portal'
        request.env.ref(report_ref)

        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref,
            res_ids=counter.ids,
        )

        filename = f"Lectura_{counter.name}.pdf"
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(pdf_content, headers=headers)

    # -------------------------------------------------------------------------
    # EXCEL – TODAS LAS LECTURAS DEL EQUIPO
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/xlsx'],
        type='http', auth='user', website=True
    )
    def portal_counters_xlsx(self, equipment_id, **kwargs):
        """
        Exporta a Excel todas las lecturas del equipo.
        """
        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            return request.not_found()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Lecturas')

        # Formatos
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#F3F4F6',
            'border': 1
        })
        text_center = workbook.add_format({'align': 'center'})
        num_fmt = workbook.add_format({'num_format': '#,##0', 'align': 'right'})

        # Encabezados (mismas columnas que el PDF / tabla del portal)
        headers = [
            'Referencia',
            'Fecha',
            'Mes Facturación',
            'Anterior B/N',
            'Actual B/N',
            'Total B/N',
        ]

        is_color = (equipment.tipo == 'color')
        if is_color:
            headers += [
                'Anterior Color',
                'Actual Color',
                'Total Color',
            ]
        headers.append('Estado')

        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_fmt)

        # Datos
        row = 1
        for counter in counters.sorted(key=lambda r: (r.fecha or r.create_date)):
            col = 0
            sheet.write(row, col, counter.name or '')
            col += 1
            # Fecha
            if counter.fecha:
                sheet.write(row, col, str(counter.fecha), text_center)
            else:
                sheet.write(row, col, '', text_center)
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

            sheet.write(row, col, counter.state or '', text_center)
            row += 1

        # Ajustar ancho de columnas básico
        sheet.set_column(0, 0, 18)  # Referencia
        sheet.set_column(1, 1, 12)  # Fecha
        sheet.set_column(2, 2, 18)  # Mes
        sheet.set_column(3, 10, 14)

        workbook.close()
        xlsx_data = output.getvalue()
        output.close()

        filename = f"Lecturas_{equipment.serie_id or equipment.id}.xlsx"
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(xlsx_data, headers=headers)
