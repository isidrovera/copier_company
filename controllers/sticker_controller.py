from odoo import http
from odoo.http import request
import base64
import qrcode
import io

class StickerController(http.Controller):
    
    @http.route('/sticker/generate/<int:record_id>', type='http', auth='user', methods=['GET'])
    def generate_sticker(self, record_id, layout='vertical', **kwargs):
        """Genera y muestra el sticker corporativo 6cm x 8cm vertical"""
        try:
            # Obtener el registro
            record = request.env['copier.company'].browse(record_id)
            if not record.exists():
                return request.not_found()
            
            # Generar QR usando la función existente del modelo
            if not record.qr_code:
                record.generar_qr_code()
            qr_base64 = record.qr_code.decode('utf-8') if record.qr_code else None
            
            # Obtener logo usando la función existente del modelo
            logo_base64 = record._get_company_logo_base64()
            
            # Preparar datos para el template
            # Corregir acceso a serie
            if hasattr(record, 'serie_id') and record.serie_id:
                serie = record.serie_id.name if hasattr(record.serie_id, 'name') else str(record.serie_id)
            elif hasattr(record, 'serie'):
                serie = record.serie
            else:
                serie = "Serie no especificada"
            
            # Corregir acceso a modelo
            if hasattr(record, 'modelo_id') and record.modelo_id:
                modelo = record.modelo_id.name if hasattr(record.modelo_id, 'name') else str(record.modelo_id)
            elif hasattr(record, 'modelo'):
                modelo = record.modelo
            elif hasattr(record, 'name'):
                modelo = record.name
            else:
                modelo = "Modelo no especificado"
            
            values = {
                'record': record,
                'qr_base64': qr_base64,
                'logo_base64': logo_base64,
                'layout': 'vertical',  # Siempre vertical
                'serie': serie,
                'modelo': modelo,
                # Dimensiones para sticker 8cm x 8cm (80mm x 80mm a 300 DPI)
                'width': "945px",   # 80mm a 300 DPI
                'height': "945px",  # 80mm a 300 DPI
            }
            
            # Renderizar template
            response = request.render('copier_company.sticker_template', values)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
            
        except Exception as e:
            # En caso de error, mostrar página de error
            return request.render('copier_company.sticker_error', {'error': str(e)})
    
    @http.route('/sticker/download/<int:record_id>', type='http', auth='user', methods=['GET'])
    def download_sticker(self, record_id, **kwargs):
        """Descarga el sticker como imagen"""
        try:
            record = request.env['copier.company'].browse(record_id)
            if not record.exists():
                return request.not_found()
            
            # Redirigir a la URL de generación para mostrar en navegador
            # El usuario puede hacer Ctrl+P para imprimir o guardar como PDF
            return request.redirect(f'/sticker/generate/{record_id}')
            
        except Exception as e:
            return request.not_found()
    
    @http.route('/sticker/preview/<int:record_id>', type='http', auth='user', methods=['GET'])
    def preview_sticker(self, record_id, **kwargs):
        """Vista previa del sticker con información adicional"""
        try:
            record = request.env['copier.company'].browse(record_id)
            if not record.exists():
                return request.not_found()
            
            # Preparar datos básicos para mostrar información
            values = {
                'record': record,
                'sticker_url': f'/sticker/generate/{record_id}',
                'download_url': f'/sticker/download/{record_id}',
            }
            
            # Retornar una página simple con el sticker embebido
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Vista Previa - Sticker {record.name if hasattr(record, 'name') else record.id}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', sans-serif;
                        background: #f8fafc;
                        margin: 0;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        min-height: 100vh;
                    }}
                    .preview-container {{
                        background: white;
                        padding: 30px;
                        border-radius: 12px;
                        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                        text-align: center;
                        max-width: 800px;
                    }}
                    .sticker-frame {{
                        border: 2px dashed #cbd5e1;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                        background: white;
                        display: inline-block;
                    }}
                    .buttons {{
                        margin-top: 20px;
                        display: flex;
                        gap: 15px;
                        justify-content: center;
                    }}
                    .btn {{
                        padding: 12px 24px;
                        border: none;
                        border-radius: 6px;
                        font-weight: 600;
                        text-decoration: none;
                        display: inline-block;
                        transition: all 0.2s ease;
                    }}
                    .btn-primary {{
                        background: #3b82f6;
                        color: white;
                    }}
                    .btn-secondary {{
                        background: #64748b;
                        color: white;
                    }}
                    .btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    }}
                    iframe {{
                        border: none;
                        width: 320px;  /* 8cm aprox en pantalla */
                        height: 320px; /* 8cm aprox en pantalla */
                        background: white;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }}
                </style>
            </head>
            <body>
                <div class="preview-container">
                    <h1>Vista Previa del Sticker</h1>
                    <p>Sticker para: <strong>{record.name if hasattr(record, 'name') else f'Registro {record.id}'}</strong></p>
                    <p>Tamaño: <strong>8cm x 8cm (Cuadrado)</strong></p>
                    
                    <div class="sticker-frame">
                        <iframe src="/sticker/generate/{record_id}" 
                                title="Sticker Preview"></iframe>
                    </div>
                    
                    <div class="buttons">
                        <a href="/sticker/generate/{record_id}" target="_blank" class="btn btn-primary">
                            🖨️ Abrir para Imprimir
                        </a>
                        <a href="/sticker/download/{record_id}" class="btn btn-secondary">
                            💾 Descargar
                        </a>
                    </div>
                    
                    <p style="margin-top: 20px; color: #64748b; font-size: 14px;">
                        💡 <strong>Tip:</strong> Para imprimir, abre el sticker en una nueva ventana y usa Ctrl+P
                    </p>
                </div>
            </body>
            </html>
            """
            
            return request.make_response(
                html_content,
                headers={'Content-Type': 'text/html; charset=utf-8'}
            )
            
        except Exception as e:
            return request.render('copier_company.sticker_error', {'error': str(e)})