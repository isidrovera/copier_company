/* 
 * Visor de PDF básico usando jQuery para Odoo 18 
 * Este enfoque evita depender de web.public.widget
 */
$(document).ready(function() {
    // Buscar el contenedor del visor de PDF
    var $container = $('#pdfViewerContainer');
    if ($container.length === 0) return;
    
    // Obtener URL del PDF
    var pdfUrl = $container.data('pdf-url');
    if (!pdfUrl) return;
    
    // Variables para el visor
    var pdfDoc = null;
    var currentPage = 1;
    var totalPages = 0;
    var canvas = null;
    var canvasContainer = null;
    var pageIndicator = null;
    
    // Inicializar el visor
    function initViewer() {
        // Crear estructura del visor
        $container.html('<div id="pdfViewer" class="w-100 h-100"></div>');
        var $viewer = $('#pdfViewer');
        
        // Crear contenedor del canvas
        canvasContainer = $('<div class="canvas-container"></div>')
            .css({
                width: '100%',
                height: '90%',
                overflow: 'auto',
                position: 'relative'
            });
        
        // Crear canvas
        var $canvas = $('<canvas id="pdf-canvas"></canvas>')
            .css('width', '100%');
        
        canvasContainer.append($canvas);
        $viewer.append(canvasContainer);
        
        // Guardar referencia al canvas
        canvas = $canvas[0];
        
        // Crear navegación
        var navbar = $('<div class="pdf-navbar d-flex justify-content-between align-items-center mt-2"></div>');
        
        // Botón anterior
        var prevBtn = $('<button class="btn btn-sm btn-secondary">&laquo; Anterior</button>')
            .on('click', function() {
                if (currentPage > 1) {
                    currentPage--;
                    renderPage(currentPage);
                }
            });
        
        // Indicador de página
        pageIndicator = $('<div class="page-indicator">Cargando PDF...</div>');
        
        // Botón siguiente
        var nextBtn = $('<button class="btn btn-sm btn-secondary">Siguiente &raquo;</button>')
            .on('click', function() {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderPage(currentPage);
                }
            });
        
        // Agregar elementos a la barra de navegación
        navbar.append(prevBtn).append(pageIndicator).append(nextBtn);
        $viewer.append(navbar);
        
        // Cargar PDF
        loadPdf();
    }
    
    // Cargar el PDF
    function loadPdf() {
        pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
            pdfDoc = pdf;
            totalPages = pdf.numPages;
            currentPage = 1;
            
            // Renderizar primera página
            renderPage(currentPage);
        }).catch(function(error) {
            console.error('Error al cargar el PDF:', error);
            $('#pdfViewer').html('<div class="alert alert-danger">Error al cargar el documento PDF</div>');
        });
    }
    
    // Renderizar una página
    function renderPage(pageNumber) {
        pdfDoc.getPage(pageNumber).then(function(page) {
            var ctx = canvas.getContext('2d');
            
            // Calcular escala
            var containerWidth = $(canvasContainer).width();
            var viewport = page.getViewport({ scale: 1 });
            var scale = containerWidth / viewport.width;
            var scaledViewport = page.getViewport({ scale: scale });
            
            // Ajustar canvas
            canvas.height = scaledViewport.height;
            canvas.width = scaledViewport.width;
            
            // Renderizar
            var renderContext = {
                canvasContext: ctx,
                viewport: scaledViewport
            };
            
            page.render(renderContext).promise.then(function() {
                // Actualizar indicador
                pageIndicator.text('Página ' + pageNumber + ' de ' + totalPages);
            });
        });
    }
    
    // Prevenir acciones no deseadas
    function preventUnwantedActions() {
        // Prevenir clic derecho en el visor
        $container.on('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
        
        // Prevenir teclas de acceso rápido
        $(document).on('keydown', function(e) {
            if (!isEventInViewer(e)) return;
            
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
        });
        
        // Deshabilitar arrastrar y soltar
        $container.on('dragstart', function(e) {
            e.preventDefault();
            return false;
        });
    }
    
    // Comprobar si un evento ocurrió dentro del visor
    function isEventInViewer(event) {
        var rect = $container[0].getBoundingClientRect();
        var x = event.clientX;
        var y = event.clientY;
        
        return (
            x >= rect.left &&
            x <= rect.right &&
            y >= rect.top &&
            y <= rect.bottom
        );
    }
    
    // Cargar PDF.js
    $.getScript('/copier_company/static/lib/pdfjs/pdf.min.js')
        .done(function() {
            // Configurar el worker
            pdfjsLib.GlobalWorkerOptions.workerSrc = '/copier_company/static/lib/pdfjs/pdf.worker.min.js';
            
            // Inicializar visor
            initViewer();
            
            // Prevenir acciones no deseadas
            preventUnwantedActions();
        })
        .fail(function() {
            console.error('No se pudo cargar PDF.js');
            $container.html('<div class="alert alert-danger">No se pudo cargar el visor de PDF</div>');
        });
});