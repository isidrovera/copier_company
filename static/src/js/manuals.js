odoo.define('secure_pdf_viewer.pdf_viewer', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.SecurePDFViewer = publicWidget.Widget.extend({
        selector: '#pdfViewerContainer',
        
        /**
         * Inicializar el visor de PDF
         */
        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            
            // Obtener URL del PDF desde el atributo data
            this.pdfUrl = this.$el.data('pdf-url');
            
            if (this.pdfUrl) {
                // Inicializar el visor de PDF
                this._initPDFViewer();
                
                // Prevenir acciones no deseadas
                this._preventUnwantedActions();
            }
            
            return def;
        },
        
        /**
         * Inicializa el visor de PDF usando PDF.js
         */
        _initPDFViewer: function () {
            var self = this;
            var container = this.$el.find('#pdfViewer')[0];
            
            // Cargar el PDF
            pdfjsLib.getDocument(this.pdfUrl).promise.then(function(pdf) {
                // Almacenar la referencia al documento PDF
                self.pdfDoc = pdf;
                self.totalPages = pdf.numPages;
                self.currentPage = 1;
                
                // Crear el visor básico con canvas
                self._createViewer(container);
                
                // Renderizar la primera página
                self._renderPage(self.currentPage);
                
                // Agregar controles de navegación
                self._addNavigation(container);
            }).catch(function(error) {
                console.error('Error al cargar el PDF:', error);
                container.innerHTML = '<div class="alert alert-danger">Error al cargar el documento PDF</div>';
            });
        },
        
        /**
         * Crea el visor básico con un elemento canvas
         */
        _createViewer: function (container) {
            // Limpiar el contenedor
            container.innerHTML = '';
            
            // Crear el contenedor del canvas
            var canvasContainer = document.createElement('div');
            canvasContainer.className = 'canvas-container';
            canvasContainer.style.width = '100%';
            canvasContainer.style.height = '90%';
            canvasContainer.style.overflow = 'auto';
            canvasContainer.style.position = 'relative';
            
            // Crear el canvas para renderizar el PDF
            var canvas = document.createElement('canvas');
            canvas.id = 'pdf-canvas';
            canvas.style.width = '100%';
            
            // Agregar el canvas al contenedor
            canvasContainer.appendChild(canvas);
            container.appendChild(canvasContainer);
            
            // Guardar referencias
            this.canvas = canvas;
            this.canvasContainer = canvasContainer;
        },
        
        /**
         * Renderiza una página específica del PDF
         */
        _renderPage: function (pageNumber) {
            var self = this;
            var canvas = this.canvas;
            var ctx = canvas.getContext('2d');
            
            // Obtener la página
            this.pdfDoc.getPage(pageNumber).then(function(page) {
                // Determinar la escala para que se ajuste al ancho del contenedor
                var containerWidth = self.canvasContainer.clientWidth;
                var viewport = page.getViewport({ scale: 1 });
                var scale = containerWidth / viewport.width;
                var scaledViewport = page.getViewport({ scale: scale });
                
                // Establecer las dimensiones del canvas
                canvas.height = scaledViewport.height;
                canvas.width = scaledViewport.width;
                
                // Renderizar la página
                var renderContext = {
                    canvasContext: ctx,
                    viewport: scaledViewport
                };
                
                page.render(renderContext).promise.then(function() {
                    // Actualizar indicador de página
                    if (self.pageIndicator) {
                        self.pageIndicator.textContent = 'Página ' + pageNumber + ' de ' + self.totalPages;
                    }
                });
            });
        },
        
        /**
         * Agrega controles de navegación básicos
         */
        _addNavigation: function (container) {
            var self = this;
            
            // Crear barra de navegación
            var navbar = document.createElement('div');
            navbar.className = 'pdf-navbar d-flex justify-content-between align-items-center mt-2';
            
            // Botón anterior
            var prevBtn = document.createElement('button');
            prevBtn.className = 'btn btn-sm btn-secondary';
            prevBtn.innerHTML = '&laquo; Anterior';
            prevBtn.onclick = function() {
                if (self.currentPage > 1) {
                    self.currentPage--;
                    self._renderPage(self.currentPage);
                }
            };
            
            // Indicador de página
            var pageIndicator = document.createElement('div');
            pageIndicator.className = 'page-indicator';
            pageIndicator.textContent = 'Página ' + this.currentPage + ' de ' + this.totalPages;
            this.pageIndicator = pageIndicator;
            
            // Botón siguiente
            var nextBtn = document.createElement('button');
            nextBtn.className = 'btn btn-sm btn-secondary';
            nextBtn.innerHTML = 'Siguiente &raquo;';
            nextBtn.onclick = function() {
                if (self.currentPage < self.totalPages) {
                    self.currentPage++;
                    self._renderPage(self.currentPage);
                }
            };
            
            // Agregar elementos a la barra de navegación
            navbar.appendChild(prevBtn);
            navbar.appendChild(pageIndicator);
            navbar.appendChild(nextBtn);
            
            // Agregar barra de navegación al contenedor
            container.appendChild(navbar);
        },
        
        /**
         * Previene acciones no deseadas como descarga, impresión, etc.
         */
        _preventUnwantedActions: function () {
            var self = this;
            
            // Prevenir clic derecho
            document.addEventListener('contextmenu', function(e) {
                if (self._isEventInViewer(e)) {
                    e.preventDefault();
                    return false;
                }
            });
            
            // Prevenir teclas de acceso rápido (Ctrl+P, Ctrl+S, etc.)
            document.addEventListener('keydown', function(e) {
                if (self._isEventInViewer(e)) {
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
            this.$el.on('dragstart', function(e) {
                e.preventDefault();
                return false;
            });
        },
        
        /**
         * Comprueba si un evento ocurrió dentro del visor de PDF
         */
        _isEventInViewer: function (event) {
            var rect = this.$el[0].getBoundingClientRect();
            var x = event.clientX;
            var y = event.clientY;
            
            return (
                x >= rect.left &&
                x <= rect.right &&
                y >= rect.top &&
                y <= rect.bottom
            );
        }
    });
    
    return publicWidget.registry.SecurePDFViewer;
});