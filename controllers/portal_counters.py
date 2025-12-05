# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import io
import logging

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class CopierPortalCounters(http.Controller):

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_portal_partner(self):
        """Cliente logueado en el portal."""
        return request.env.user.partner_id

    def _get_equipment_for_portal(self, equipment_id):
        """
        Retorna la máquina siempre que pertenezca al cliente del portal.
        Modelo real: copier.company
        """
        Equipment = request.env['copier.company'].sudo()
        equipment = Equipment.browse(int(equipment_id))

        partner = self._get_portal_partner()

        if not equipment.exists():
            return None

        # Seguridad: validar que la máquina pertenece al cliente logueado
        if equipment.cliente_id.id != partner.id:
            return None

        return equipment

    def _get_counters_for_equipment(self, equipment):
        """
        Devuelve todos los copier.counter asociados a una máquina
        y al cliente del portal.
        """
        Counter = request.env['copier.counter'].sudo()
        partner = self._get_portal_partner()

        return Counter.search([
            ('maquina_id', '=', equipment.id),
            ('cliente_id', '=', partner.id),
        ], order="fecha asc, id asc")

    def _check_counter_access(self, counter):
        """Valida que la lectura pertenece al cliente portal."""
        partner = self._get_portal_partner()

        if not counter.exists():
            return False

        return counter.cliente_id.id == partner.id

    # -------------------------------------------------------------------------
    # PDF — TODAS LAS LECTURAS DE UNA MÁQUINA
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/pdf'],
        type='http', auth='user', website=True
    )
    def portal_counters_pdf_all(self, equipment_id, **kwargs):

        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            return request.not_found()

        report = request.env.ref('copier_company.action_report_counter_readings_portal')
        pdf_content, _ = report._render_qweb_pdf(res_ids=counters.ids)

        filename = f"Lecturas_{equipment.serie_id or equipment.id}.pdf"
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        return request.make_response(pdf_content, headers=headers)

    # -------------------------------------------------------------------------
    # PDF — UNA SOLA LECTURA
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/counter/<int:counter_id>/pdf'],
        type='http', auth='user', website=True
    )
    def portal_counter_pdf_single(self, counter_id, **kwargs):

        Counter = request.env['copier.counter'].sudo()
        counter = Counter.browse(int(counter_id))

        if not self._check_counter_access(counter):
            return request.not_found()

        report = request.env.ref('copier_company.action_report_counter_readings_portal')
        pdf_content, _ = report._render_qweb_pdf(res_ids=counter.ids)

        filename = f"Lectura_{counter.name}.pdf"
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]

        return request.make_response(pdf_content, headers=headers)

    # -------------------------------------------------------------------------
    # EXCEL — TODAS LAS LECTURAS
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/xlsx'],
        type='http', auth='user', website=True
    )
    def portal_counters_xlsx(self, equipment_id, **kwargs):

        if not xlsxwriter:
            return request.not_found()

        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            return request.not_found()

        # Crear archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Lecturas")

        # Estilos
        header_fmt = workbook.add_format({'bold': True})
        number_fmt = workbook.add_format({'num_format': '#,##0'})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        # Encabezados (mismas columnas del portal)
        headers = [
            'Referencia',
            'Fecha Lectura',
            'Mes Facturación',
            'Anterior B/N',
            'Actual B/N',
            'Total B/N',
        ]

        if equipment.tipo == 'color':
            headers += [
                'Anterior Color',
                'Actual Color',
                'Total Color',
            ]

        headers += ['Estado']

        # Escribir encabezados
        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_fmt)

        # Escribir datos
        row = 1
        for counter in counters:
            col = 0

            sheet.write(row, col, counter.name or '')
            col += 1

            if counter.fecha:
                sheet.write_datetime(row, col, counter.fecha, date_fmt)
            else:
                sheet.write(row, col, '')
            col += 1

            sheet.write(row, col, counter.mes_facturacion or '')
            col += 1

            sheet.write_number(row, col, counter.contador_anterior_bn or 0, number_fmt)
            col += 1
            sheet.write_number(row, col, counter.contador_actual_bn or 0, number_fmt)
            col += 1
            sheet.write_number(row, col, counter.total_copias_bn or 0, number_fmt)
            col += 1

            if equipment.tipo == 'color':
                sheet.write_number(row, col, counter.contador_anterior_color or 0, number_fmt)
                col += 1
                sheet.write_number(row, col, counter.contador_actual_color or 0, number_fmt)
                col += 1
                sheet.write_number(row, col, counter.total_copias_color or 0, number_fmt)
                col += 1

            sheet.write(row, col, counter.state or '')
            row += 1

        workbook.close()
        xlsx_data = output.getvalue()

        filename = f"Lecturas_{equipment.serie_id or equipment.id}.xlsx"
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(xlsx_data, headers=headers)
