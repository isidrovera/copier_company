odoo.define('copier_company.pdf_viewer', function(require) {
    'use strict';

    const { Component, onWillStart, onMounted, useState } = owl;
    const { xml } = owl.tags;
    const { useRef } = owl.hooks;

    class PDFViewer extends Component {
        setup() {
            this.state = useState({
                currentPage: 1,
                totalPages: 0,
                isLoaded: false,
                error: null
            });
            
            this.pdfContainer = useRef('pdfContainer');
            this.canvasRef = useRef('pdfCanvas');
            this.pdfDoc = null;
            
            onWillStart(() => {
                // Cargamos PDF.js si no está cargado
                if (typeof window.pdfjsLib === 'undefined') {
                    return this._loadPDFJS();
                }
            });
            
            onMounted(() => {
                // Obtenemos la URL del PDF desde el atributo data
                const container = this.pdfContainer.el;
                if (container) {
                    this.pdfUrl = container.dataset.pdfUrl;
                    if (this.pdfUrl) {
                        this._initPDFViewer();
                        this._preventUnwantedActions();
                    }
                }
            });
        }
        
        /**
         * Carga PDF.js desde CDN
         */
        async _loadPDFJS() {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
                script.onload = () => {
                    // Configurar el worker
                    window.pdfjsLib.GlobalWorkerOptions.workerSrc = 
                        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                    resolve();
                };
                script.onerror = () => {
                    this.state.error = 'No se pudo cargar PDF.js';
                    reject(new Error('No se pudo cargar PDF.js'));
                };
                document.head.appendChild(script);
            });
        }
        
        /**
         * Inicializa el visor de PDF
         */
        async _initPDFViewer() {
            try {
                // Cargar el PDF
                this.pdfDoc = await window.pdfjsLib.getDocument(this.pdfUrl).promise;
                this.state.totalPages = this.pdfDoc.numPages;
                this.state.currentPage = 1;
                
                // Renderizar la primera página
                await this._renderPage(this.state.currentPage);
                this.state.isLoaded = true;
            } catch (error) {
                console.error('Error al cargar el PDF:', error);
                this.state.error = 'Error al cargar el documento PDF';
            }
        }
        
        /**
         * Renderiza una página específica del PDF
         */
        async _renderPage(pageNumber) {
            if (!this.pdfDoc) return;
            
            const canvas = this.canvasRef.el;
            const ctx = canvas.getContext('2d');
            
            // Obtener la página
            const page = await this.pdfDoc.getPage(pageNumber);
            
            // Determinar la escala para que se ajuste al ancho del contenedor
            const containerWidth = this.pdfContainer.el.clientWidth;
            const viewport = page.getViewport({ scale: 1 });
            const scale = containerWidth / viewport.width;
            const scaledViewport = page.getViewport({ scale: scale });
            
            // Establecer las dimensiones del canvas
            canvas.height = scaledViewport.height;
            canvas.width = scaledViewport.width;
            
            // Renderizar la página
            const renderContext = {
                canvasContext: ctx,
                viewport: scaledViewport
            };
            
            await page.render(renderContext).promise;
            this.state.currentPage = pageNumber;
        }
        
        /**
         * Previene acciones no deseadas como descarga, impresión, etc.
         */
        _preventUnwantedActions() {
            const container = this.pdfContainer.el;
            
            // Prevenir clic derecho
            document.addEventListener('contextmenu', (e) => {
                if (this._isEventInViewer(e, container)) {
                    e.preventDefault();
                    return false;
                }
            });
            
            // Prevenir teclas de acceso rápido (Ctrl+P, Ctrl+S, etc.)
            document.addEventListener('keydown', (e) => {
                if (this._isEventInViewer(e, container)) {
                    // Prevenir Ctrl+P (imprimir)
                    if (e.ctrlKey && (e.key === 'p' || e.keyCode === 80)) {
                        e.preventDefault();
                        return false;
                    }
                    
                    // Prevenir Ctrl+S (guardar)
                    if (e.ctrlKey && (e.key === 's' || e.keyCode === 83)) {
                        e.preventDefault();
                        return false;
                    }
                    
                    // Prevenir Ctrl+Shift+E (exportar)
                    if (e.ctrlKey && e.shiftKey && (e.key === 'e' || e.keyCode === 69)) {
                        e.preventDefault();
                        return false;
                    }
                }
            });
            
            // Deshabilitar la función de arrastrar y soltar
            container.addEventListener('dragstart', (e) => {
                e.preventDefault();
                return false;
            });
        }
        
        /**
         * Comprueba si un evento ocurrió dentro del visor de PDF
         */
        _isEventInViewer(event, container) {
            const rect = container.getBoundingClientRect();
            const x = event.clientX;
            const y = event.clientY;
            
            return (
                x >= rect.left &&
                x <= rect.right &&
                y >= rect.top &&
                y <= rect.bottom
            );
        }
        
        /**
         * Navega a la página anterior
         */
        previousPage() {
            if (this.state.currentPage > 1) {
                this._renderPage(this.state.currentPage - 1);
            }
        }
        
        /**
         * Navega a la página siguiente
         */
        nextPage() {
            if (this.state.currentPage < this.state.totalPages) {
                this._renderPage(this.state.currentPage + 1);
            }
        }
    }
    
    PDFViewer.template = xml`
        <div t-ref="pdfContainer" class="pdf-viewer-container w-100 h-100">
            <div t-if="state.error" class="alert alert-danger" t-esc="state.error"/>
            <div t-else="" class="pdf-content h-90 position-relative">
                <canvas t-ref="pdfCanvas" class="w-100"/>
                <div t-if="state.isLoaded" class="pdf-navbar d-flex justify-content-between align-items-center mt-2">
                    <button class="btn btn-sm btn-secondary" t-on-click="previousPage">
                        &laquo; Anterior
                    </button>
                    <div class="page-indicator">
                        Página <t t-esc="state.currentPage"/> de <t t-esc="state.totalPages"/>
                    </div>
                    <button class="btn btn-sm btn-secondary" t-on-click="nextPage">
                        Siguiente &raquo;
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Registrar el componente para que esté disponible en las plantillas QWeb
    owl.utils.whenReady(() => {
        owl.mount(PDFViewer, { target: document.getElementById('pdfViewerContainer') });
    });
    
    return PDFViewer;
});