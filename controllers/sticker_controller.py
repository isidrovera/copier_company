from odoo import http
from odoo.http import request
import base64
import qrcode
import io

class StickerController(http.Controller):
    
    @http.route('/sticker/generate/<int:record_id>', type='http', auth='user', methods=['GET'])
    def generate_sticker(self, record_id, layout='horizontal', **kwargs):
        """Genera y muestra el sticker corporativo"""
        try:
            # Obtener el registro
            record = request.env['copier.company'].browse(record_id)
            if not record.exists():
                return request.not_found()
            
            # Generar QR usando la función existente del modelo
            # Primero actualizar el QR del registro si no existe
            if not record.qr_code:
                record.generar_qr_code()
            qr_base64 = record.qr_code.decode('utf-8') if record.qr_code else None
            
            # Obtener logo usando la función existente del modelo
            logo_base64 = record._get_company_logo_base64()
            
            # Preparar datos para el template
            serie = getattr(record, 'serie_id', None) or "____________________"
            modelo = getattr(record.name, 'name', None) if hasattr(record, 'name') else "Modelo no especificado"
            
            values = {
                'record': record,
                'qr_base64': qr_base64,
                'logo_base64': logo_base64,
                'layout': layout,
                'serie': serie,
                'modelo': modelo,
                'width': "567px" if layout == 'vertical' else "944px",  # 8cm a 300 DPI
                'height': "944px" if layout == 'vertical' else "567px",  # 6cm a 300 DPI
            }
            
            # Renderizar template
            response = request.render('copier_company.sticker_template', values)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
            
        except Exception as e:
            # En caso de error, mostrar página de error
            return request.render('copier_company.sticker_error', {'error': str(e)})
    
    @http.route('/sticker/download/<int:record_id>', type='http', auth='user', methods=['GET'])
    def download_sticker(self, record_id, layout='horizontal', **kwargs):
        """Descarga el sticker como imagen PNG"""
        try:
            record = request.env['copier.company'].browse(record_id)
            if not record.exists():
                return request.not_found()
            
            # Redirigir a la URL de generación para mostrar en navegador
            # El usuario puede hacer click derecho > "Guardar imagen como"
            return request.redirect(f'/sticker/generate/{record_id}?layout={layout}')
            
        except Exception as e:
            return request.not_found()