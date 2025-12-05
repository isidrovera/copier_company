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

    # ---------- MÉTODOS PRIVADOS DE APOYO ----------

    def _get_portal_partner(self):
        return request.env.user.partner_id

    def _get_equipment_for_portal(self, equipment_id):
        """
        Recupera el equipo y verifica que pertenezca al partner del portal.
        Ajusta el modelo y el campo cliente_id/partner_id según tu implementación.
        """
        # SUPOSICIÓN: modelo 'copier.equipment' (ajusta si tu modelo se llama distinto)
        Equipment = request.env['copier.equipment'].sudo()
        equipment = Equipment.browse(equipment_id)
        partner = self._get_portal_partner()

        # AJUSTAR ESTE CAMPO: cliente_id / partner_id / company_id, etc.
        owner = equipment.cliente_id or equipment.partner_id

        if not equipment.exists() or not owner or owner.id != partner.id:
            return None
        return equipment

    def _get_counters_for_equipment(self, equipment):
        """
        Devuelve los copier.counter del equipo para este cliente.
        Ajusta el dominio a tu modelo real.
        """
        Counter = request.env['copier.counter'].sudo()
        partner = self._get_portal_partner()

        domain = [
            ('maquina_id', '=', equipment.id),   # AJUSTAR campo si es otro
            ('cliente_id', '=', partner.id),     # AJUSTAR si tu campo cliente se llama distinto
        ]
        counters = Counter.search(domain, order="fecha asc, id asc")
        return counters

    def _check_counter_access(self, counter):
        """
        Verifica que un solo copier.counter pertenece al partner portal.
        """
        partner = self._get_portal_partner()

        # AJUSTA campos 'cliente_id' y 'maquina_id.cliente_id' según tu modelo
        if counter.cliente_id and counter.cliente_id.id == partner.id:
            return True
        if counter.maquina_id and counter.maquina_id.cliente_id and counter.maquina_id.cliente_id.id == partner.id:
            return True
        return False

    # ---------- RUTAS PDF ----------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/pdf'],
        type='http', auth='user', website=True
    )
    def portal_counters_pdf_all(self, equipment_id, **kwargs):
        """
        PDF con TODAS las lecturas del equipo para el cliente del portal.
        """
        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            return request.not_found()

        report = request.env.ref('copier_company.action_report_counter_readings_portal')
        pdf_content, _ = report._render_qweb_pdf(counters.ids)

        filename = 'Lecturas_%s.pdf' % (equipment.display_name or equipment.id)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(pdf_content, headers=headers)

    @http.route(
        ['/my/copier/counter/<int:counter_id>/pdf'],
        type='http', auth='user', website=True
    )
    def portal_counter_pdf_single(self, counter_id, **kwargs):
        """
        PDF de UNA sola lectura (fila).
        """
        Counter = request.env['copier.counter'].sudo()
        counter = Counter.browse(counter_id)
        if not counter.exists() or not self._check_counter_access(counter):
            return request.not_found()

        report = request.env.ref('copier_company.action_report_counter_readings_portal')
        pdf_content, _ = report._render_qweb_pdf(counter.ids)

        filename = 'Lectura_%s.pdf' % (counter.name or counter.id)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(pdf_content, headers=headers)

    # ---------- RUTA EXCEL ----------

    @http.route(
        ['/my/copier/equipment/<int:equipment_id>/counters/xlsx'],
        type='http', auth='user', website=True
    )
    def portal_counters_xlsx(self, equipment_id, **kwargs):
        """
        Exporta todas las lecturas del equipo a Excel con las mismas columnas que la tabla.
        """
        if not xlsxwriter:
            return request.not_found()

        equipment = self._get_equipment_for_portal(equipment_id)
        if not equipment:
            return request.not_found()

        counters = self._get_counters_for_equipment(equipment)
        if not counters:
            return request.not_found()

        # Crear libro en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Lecturas')

        # Formatos
        head_fmt = workbook.add_format({'bold': True})
        num_fmt = workbook.add_format({'num_format': '#,##0'})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        # Encabezados (mismas columnas que la tabla)
        headers = [
            'Referencia',
            'Fecha',
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

        for col, name in enumerate(headers):
            sheet.write(0, col, name, head_fmt)

        # Filas
        row = 1
        for counter in counters:
            col = 0
            sheet.write(row, col, counter.name or '')
            col += 1

            # Fecha
            if counter.fecha:
                sheet.write_datetime(row, col, counter.fecha, date_fmt)
            else:
                sheet.write(row, col, '')
            col += 1

            sheet.write(row, col, counter.mes_facturacion or '')
            col += 1

            sheet.write_number(row, col, counter.contador_anterior_bn or 0, num_fmt)
            col += 1
            sheet.write_number(row, col, counter.contador_actual_bn or 0, num_fmt)
            col += 1
            sheet.write_number(row, col, counter.total_copias_bn or 0, num_fmt)
            col += 1

            if equipment.tipo == 'color':
                sheet.write_number(row, col, counter.contador_anterior_color or 0, num_fmt)
                col += 1
                sheet.write_number(row, col, counter.contador_actual_color or 0, num_fmt)
                col += 1
                sheet.write_number(row, col, counter.total_copias_color or 0, num_fmt)
                col += 1

            sheet.write(row, col, counter.state or '')
            row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        output.close()

        filename = 'Lecturas_%s.xlsx' % (equipment.display_name or equipment.id)
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Length', len(xlsx_data)),
            ('Content-Disposition', http.content_disposition(filename)),
        ]
        return request.make_response(xlsx_data, headers=headers)
