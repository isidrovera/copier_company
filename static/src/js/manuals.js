/* 
 * Visor de PDF mejorado con funcionalidad de búsqueda para Odoo
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
    var pageRendering = false;
    var pageNumPending = null;
    var canvas = null;
    var ctx = null;
    var scale = 1.0;
    var canvasContainer = null;
    var searchMatches = [];
    var currentMatchIndex = -1;
    
    // Inicializar controles
    var $prevButton = $('#pdfPrevPage');
    var $nextButton = $('#pdfNextPage');
    var $pageInfo = $('#pdfPageInfo');
    var $zoomIn = $('#pdfZoomIn');
    var $zoomOut = $('#pdfZoomOut');
    var $searchInput = $('#pdfSearchInput');
    var $searchButton = $('#pdfSearchButton');
    var $searchResults = $('#pdfSearchResults');
    var $searchResultsList = $('#pdfSearchResultsList');
    var $searchClose = $('#pdfSearchClose');
    var $loadingSpinner = $('#pdfLoadingSpinner');
    
    // Verificar si PDF.js está disponible
    if (typeof pdfjsLib === 'undefined') {
        console.error('PDF.js no está disponible');
        $container.html('<div class="alert alert-danger">No se pudo cargar el visor de PDF</div>');
        return;
    }
    
    // Configurar el worker de PDF.js
    if (pdfjsLib.GlobalWorkerOptions) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = '/copier_company/static/lib/pdfjs/pdf.worker.mjs';
    }
    
    // Inicializar el visor
    function initViewer() {
        // Crear estructura del visor
        var $viewer = $('#pdfViewer');
        
        // Crear contenedor del canvas
        canvasContainer = document.createElement('div');
        canvasContainer.className = 'canvas-container d-flex justify-content-center';
        canvasContainer.style.minHeight = '100%';
        
        // Crear canvas
        canvas = document.createElement('canvas');
        canvas.id = 'pdf-canvas';
        ctx = canvas.getContext('2d');
        
        // Agregar el canvas al contenedor
        canvasContainer.appendChild(canvas);
        $viewer.append(canvasContainer);
        
        // Cargar PDF
        loadPdf();
        
        // Configurar eventos
        setupEventHandlers();
    }
    
    // Configurar manejadores de eventos
    function setupEventHandlers() {
        // Botones de página
        $prevButton.on('click', function() {
            if (currentPage > 1) {
                currentPage--;
                queueRenderPage(currentPage);
            }
        });
        
        $nextButton.on('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                queueRenderPage(currentPage);
            }
        });
        
        // Botones de zoom
        $zoomIn.on('click', function() {
            scale *= 1.2;
            queueRenderPage(currentPage);
        });
        
        $zoomOut.on('click', function() {
            scale /= 1.2;
            if (scale < 0.5) scale = 0.5;
            queueRenderPage(currentPage);
        });
        
        // Búsqueda
        $searchButton.on('click', performSearch);
        $searchInput.on('keypress', function(e) {
            if (e.which === 13) {
                performSearch();
            }
        });
        
        // Cerrar resultados de búsqueda
        $searchClose.on('click', function() {
            $searchResults.addClass('d-none');
        });
        
        // Prevenir acciones no deseadas
        preventUnwantedActions();
    }
    
    // Cargar el PDF
    function loadPdf() {
        pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
            pdfDoc = pdf;
            totalPages = pdf.numPages;
            
            // Actualizar información de página
            updatePageInfo();
            
            // Renderizar primera página
            renderPage(currentPage);
            
            // Ocultar spinner de carga
            $loadingSpinner.fadeOut();
        }).catch(function(error) {
            console.error('Error al cargar el PDF:', error);
            $('#pdfViewer').html('<div class="alert alert-danger m-3">Error al cargar el documento PDF</div>');
            $loadingSpinner.fadeOut();
        });
    }
    
    // Poner en cola la renderización de la página (evita problemas con cambios rápidos)
    function queueRenderPage(num) {
        if (pageRendering) {
            pageNumPending = num;
        } else {
            renderPage(num);
        }
    }
    
    // Renderizar una página
    function renderPage(pageNumber) {
        pageRendering = true;
        
        // Actualizar información de página
        currentPage = pageNumber;
        updatePageInfo();
        
        // Obtener la página
        pdfDoc.getPage(pageNumber).then(function(page) {
            // Calcular dimensiones
            var viewport = page.getViewport({ scale: scale });
            
            // Ajustar canvas
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Renderizar
            var renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };
            
            var renderTask = page.render(renderContext);
            
            // Esperar a que se complete la renderización
            renderTask.promise.then(function() {
                pageRendering = false;
                
                if (pageNumPending !== null) {
                    // Se ha solicitado una nueva página mientras se renderizaba
                    renderPage(pageNumPending);
                    pageNumPending = null;
                }
                
                // Resaltar coincidencias de búsqueda si existen
                highlightSearchMatches();
            });
        });
    }
    
    // Actualizar información de la página
    function updatePageInfo() {
        $pageInfo.text('Página ' + currentPage + ' de ' + totalPages);
        
        // Actualizar estado de los botones
        $prevButton.prop('disabled', currentPage <= 1);
        $nextButton.prop('disabled', currentPage >= totalPages);
    }
    
    // Realizar búsqueda en el documento
    function performSearch() {
        var searchTerm = $searchInput.val().trim();
        if (!searchTerm || !pdfDoc) return;
        
        // Limpiar resultados previos
        searchMatches = [];
        currentMatchIndex = -1;
        $searchResultsList.empty();
        
        // Mostrar spinner en resultados
        $searchResultsList.html('<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div> Buscando...</div>');
        $searchResults.removeClass('d-none');
        
        // Buscar en todas las páginas
        var pendingPages = totalPages;
        var matchFound = false;
        
        for (var i = 1; i <= totalPages; i++) {
            pdfDoc.getPage(i).then(function(page) {
                var pageIndex = page._pageIndex + 1;
                
                page.getTextContent().then(function(textContent) {
                    // Buscar en el texto de la página
                    var text = textContent.items.map(function(item) {
                        return item.str;
                    }).join(' ');
                    
                    // Buscar todas las ocurrencias (insensible a mayúsculas/minúsculas)
                    var regex = new RegExp(escapeRegExp(searchTerm), 'gi');
                    var match;
                    while ((match = regex.exec(text)) !== null) {
                        matchFound = true;
                        searchMatches.push({
                            page: pageIndex,
                            position: match.index,
                            text: text.substr(Math.max(0, match.index - 40), 80)
                        });
                    }
                    
                    pendingPages--;
                    
                    // Cuando se hayan buscado todas las páginas
                    if (pendingPages === 0) {
                        if (matchFound) {
                            displaySearchResults();
                        } else {
                            $searchResultsList.html('<div class="alert alert-info">No se encontraron coincidencias para "' + searchTerm + '"</div>');
                        }
                    }
                });
            });
        }
    }
    
    // Mostrar resultados de búsqueda
    function displaySearchResults() {
        $searchResultsList.empty();
        
        if (searchMatches.length === 0) {
            $searchResultsList.html('<div class="alert alert-info">No se encontraron coincidencias</div>');
            return;
        }
        
        // Ordenar por número de página
        searchMatches.sort(function(a, b) {
            return a.page - b.page;
        });
        
        // Crear lista de resultados
        var resultHtml = '<div class="list-group">';
        
        searchMatches.forEach(function(match, index) {
            var matchText = match.text.replace(new RegExp('(' + escapeRegExp($searchInput.val().trim()) + ')', 'gi'), '<strong class="text-primary">$1</strong>');
            
            resultHtml += '<a href="#" class="list-group-item list-group-item-action search-result-item py-2" data-index="' + index + '">' +
                          '<div class="d-flex justify-content-between">' +
                          '<small class="text-muted">Página ' + match.page + '</small>' +
                          '</div>' +
                          '<div class="match-text small">' + matchText + '...</div>' +
                          '</a>';
        });
        
        resultHtml += '</div>';
        $searchResultsList.html(resultHtml);
        
        // Manejar clics en resultados
        $('.search-result-item').on('click', function(e) {
            e.preventDefault();
            var index = $(this).data('index');
            currentMatchIndex = index;
            
            // Marcar como activo
            $('.search-result-item').removeClass('active');
            $(this).addClass('active');
            
            // Ir a la página y resaltar
            var match = searchMatches[index];
            if (match.page !== currentPage) {
                currentPage = match.page;
                queueRenderPage(currentPage);
            } else {
                highlightSearchMatches();
            }
        });
    }
    
    // Resaltar coincidencias de búsqueda en la página actual
    function highlightSearchMatches() {
        // Esta función es un marcador de posición
        // Una implementación completa requeriría métodos adicionales de PDF.js
        // para obtener las coordenadas exactas de las coincidencias de texto
        
        // Para una implementación básica, simplemente resaltamos el resultado seleccionado
        if (currentMatchIndex >= 0 && searchMatches.length > 0) {
            var match = searchMatches[currentMatchIndex];
            if (match.page === currentPage) {
                // Aquí se implementaría el resaltado real
                console.log('Resaltando coincidencia en página ' + currentPage);
            }
        }
    }
    
    // Escapar caracteres especiales para RegExp
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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
            
            // Teclas de navegación
            if (e.key === 'ArrowLeft' || e.key === 'Left') {
                if (currentPage > 1) {
                    currentPage--;
                    queueRenderPage(currentPage);
                }
                e.preventDefault();
            } else if (e.key === 'ArrowRight' || e.key === 'Right') {
                if (currentPage < totalPages) {
                    currentPage++;
                    queueRenderPage(currentPage);
                }
                e.preventDefault();
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
    
    // Iniciar el visor
    initViewer();
});