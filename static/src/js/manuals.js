/* 
 * Visor de PDF mejorado usando jQuery para Odoo 18
 * Incluye búsqueda dentro del PDF y controles adicionales
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
    var currentScale = 1.0;
    var MIN_SCALE = 0.5;
    var MAX_SCALE = 3.0;
    
    // Variables para la búsqueda
    var searchText = '';
    var searchMatches = [];
    var searchMatchIndex = -1;
    var searchActive = false;
    
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
        
        // Crear elemento para mostrar resultados de búsqueda resaltados
        var textLayer = $('<div id="textLayer"></div>')
            .css({
                position: 'absolute',
                left: 0,
                top: 0,
                right: 0,
                bottom: 0,
                overflow: 'hidden',
                opacity: 0.2,
                'pointer-events': 'none'
            });
        
        // Crear canvas
        var $canvas = $('<canvas id="pdf-canvas"></canvas>')
            .css('width', '100%');
        
        canvasContainer.append($canvas);
        canvasContainer.append(textLayer);
        $viewer.append(canvasContainer);
        
        // Guardar referencia al canvas
        canvas = $canvas[0];
        
        // Crear navegación
        var navbar = $('<div class="pdf-navbar d-flex justify-content-between align-items-center mt-2"></div>');
        
        // Grupo de botones de navegación
        var navGroup = $('<div class="btn-group"></div>');
        
        // Botón primera página
        var firstBtn = $('<button class="btn btn-sm btn-secondary"><i class="fa fa-step-backward"></i></button>')
            .on('click', function() {
                currentPage = 1;
                renderPage(currentPage);
            });
        
        // Botón anterior
        var prevBtn = $('<button class="btn btn-sm btn-secondary"><i class="fa fa-chevron-left"></i></button>')
            .on('click', function() {
                if (currentPage > 1) {
                    currentPage--;
                    renderPage(currentPage);
                }
            });
        
        // Indicador de página con input para ir a una página específica
        var pageInputGroup = $('<div class="input-group mx-2" style="width: 150px;"></div>');
        var pageInput = $('<input type="number" min="1" class="form-control form-control-sm" style="text-align: center;"/>')
            .on('change', function() {
                var page = parseInt($(this).val());
                if (page >= 1 && page <= totalPages) {
                    currentPage = page;
                    renderPage(currentPage);
                } else {
                    $(this).val(currentPage);
                }
            });
        
        pageIndicator = $('<div class="input-group-append"><span class="input-group-text">/ <span id="totalPages">...</span></span></div>');
        pageInputGroup.append(pageInput).append(pageIndicator);
        
        // Botón siguiente
        var nextBtn = $('<button class="btn btn-sm btn-secondary"><i class="fa fa-chevron-right"></i></button>')
            .on('click', function() {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderPage(currentPage);
                }
            });
        
        // Botón última página
        var lastBtn = $('<button class="btn btn-sm btn-secondary"><i class="fa fa-step-forward"></i></button>')
            .on('click', function() {
                currentPage = totalPages;
                renderPage(currentPage);
            });
        
        // Agregar elementos a la barra de navegación
        navGroup.append(firstBtn).append(prevBtn);
        navbar.append(navGroup).append(pageInputGroup);
        navGroup = $('<div class="btn-group"></div>').append(nextBtn).append(lastBtn);
        navbar.append(navGroup);
        
        $viewer.append(navbar);
        
        // Cargar PDF
        loadPdf();
        
        // Configurar búsqueda
        setupSearch();
        
        // Configurar zoom
        setupZoom();
    }
    
    // Configurar búsqueda en el PDF
    function setupSearch() {
        var $searchInput = $('#pdfSearchInput');
        var $searchPrev = $('#pdfSearchPrev');
        var $searchNext = $('#pdfSearchNext');
        var $searchResults = $('#pdfSearchResults');
        
        $searchInput.on('input', function() {
            searchText = $(this).val().trim();
            if (searchText.length >= 3) {
                performSearch();
            } else {
                clearSearch();
            }
        });
        
        $searchPrev.on('click', function() {
            if (searchMatches.length > 0) {
                searchMatchIndex = (searchMatchIndex - 1 + searchMatches.length) % searchMatches.length;
                highlightCurrentMatch();
            }
        });
        
        $searchNext.on('click', function() {
            if (searchMatches.length > 0) {
                searchMatchIndex = (searchMatchIndex + 1) % searchMatches.length;
                highlightCurrentMatch();
            }
        });
        
        function performSearch() {
            searchActive = true;
            searchMatches = [];
            searchMatchIndex = -1;
            
            $searchResults.text("Buscando...");
            $searchPrev.prop('disabled', true);
            $searchNext.prop('disabled', true);
            
            // Reiniciar página actual
            var currentPageBackup = currentPage;
            
            // Buscar en todas las páginas
            var pendingSearches = totalPages;
            var pagePromises = [];
            
            for (var i = 1; i <= totalPages; i++) {
                var promise = pdfDoc.getPage(i).then(function(page) {
                    return page.getTextContent().then(function(textContent) {
                        var pageIndex = page.pageIndex + 1;
                        var pageText = textContent.items.map(function(item) {
                            return item.str;
                        }).join(' ');
                        
                        var regex = new RegExp(escapeRegExp(searchText), 'gi');
                        var match;
                        while ((match = regex.exec(pageText)) !== null) {
                            searchMatches.push({
                                page: pageIndex,
                                index: match.index,
                                length: searchText.length
                            });
                        }
                        
                        pendingSearches--;
                        if (pendingSearches === 0) {
                            finishSearch();
                        }
                    });
                });
                
                pagePromises.push(promise);
            }
            
            // Finalizar búsqueda cuando todas las páginas hayan sido procesadas
            function finishSearch() {
                if (searchMatches.length > 0) {
                    $searchResults.text(searchMatches.length + " coincidencia(s)");
                    $searchPrev.prop('disabled', false);
                    $searchNext.prop('disabled', false);
                    
                    // Ir a la primera coincidencia
                    searchMatchIndex = 0;
                    highlightCurrentMatch();
                } else {
                    $searchResults.text("No se encontraron coincidencias");
                    // Volver a la página original
                    if (currentPage !== currentPageBackup) {
                        currentPage = currentPageBackup;
                        renderPage(currentPage);
                    }
                }
            }
        }
        
        function clearSearch() {
            searchActive = false;
            searchMatches = [];
            searchMatchIndex = -1;
            $searchResults.text("");
            $searchPrev.prop('disabled', true);
            $searchNext.prop('disabled', true);
            $('#textLayer').empty();
        }
        
        function highlightCurrentMatch() {
            if (searchMatchIndex >= 0 && searchMatchIndex < searchMatches.length) {
                var match = searchMatches[searchMatchIndex];
                
                // Cambiar a la página de la coincidencia actual
                if (currentPage !== match.page) {
                    currentPage = match.page;
                    renderPage(currentPage, function() {
                        highlightTextInPage(match);
                    });
                } else {
                    highlightTextInPage(match);
                }
                
                $searchResults.text((searchMatchIndex + 1) + " de " + searchMatches.length);
            }
        }
        
        function highlightTextInPage(match) {
            pdfDoc.getPage(match.page).then(function(page) {
                page.getTextContent().then(function(textContent) {
                    var $textLayer = $('#textLayer');
                    $textLayer.empty();
                    
                    // Crear destacado para la coincidencia actual
                    var viewport = page.getViewport({ scale: currentScale });
                    var highlight = $('<div class="search-highlight current"></div>')
                        .css({
                            position: 'absolute',
                            background: 'rgba(255, 255, 0, 0.4)',
                            border: '2px solid orange',
                            'border-radius': '3px'
                        });
                    
                    // Encontrar la posición de la coincidencia en el viewport
                    var charIndex = 0;
                    var found = false;
                    
                    for (var i = 0; i < textContent.items.length && !found; i++) {
                        var item = textContent.items[i];
                        
                        if (charIndex <= match.index && match.index < charIndex + item.str.length) {
                            // Encontramos el elemento que contiene la coincidencia
                            var matchOffset = match.index - charIndex;
                            
                            // Convertir a coordenadas del viewport
                            var tx = pdfjsLib.Util.transform(
                                viewport.transform,
                                item.transform
                            );
                            
                            // Aproximar la posición y tamaño del texto
                            var fontHeight = Math.sqrt(tx[2] * tx[2] + tx[3] * tx[3]);
                            var fontSize = Math.abs(item.height);
                            
                            highlight.css({
                                left: (tx[4] + matchOffset * fontSize * 0.6) + 'px',
                                top: (tx[5] - fontHeight) + 'px',
                                width: (match.length * fontSize * 0.6) + 'px',
                                height: fontHeight + 'px'
                            });
                            
                            found = true;
                        }
                        
                        charIndex += item.str.length + 1; // +1 por el espacio que agregamos al juntar
                    }
                    
                    $textLayer.append(highlight);
                    
                    // Scroll hasta la coincidencia
                    var highlightPosition = highlight.position();
                    if (highlightPosition) {
                        $(canvasContainer).scrollTop(
                            highlightPosition.top - $(canvasContainer).height() / 2
                        );
                    }
                });
            });
        }
        
        // Función auxiliar para escapar caracteres especiales en RegExp
        function escapeRegExp(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }
    }
    
    // Configurar controles de zoom
    function setupZoom() {
        $('#zoomIn').on('click', function() {
            if (currentScale < MAX_SCALE) {
                currentScale += 0.25;
                renderPage(currentPage);
            }
        });
        
        $('#zoomOut').on('click', function() {
            if (currentScale > MIN_SCALE) {
                currentScale -= 0.25;
                renderPage(currentPage);
            }
        });
    }
    
    // Cargar el PDF
    function loadPdf() {
        pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
            pdfDoc = pdf;
            totalPages = pdf.numPages;
            
            // Actualizar elementos UI
            $('#totalPages').text(totalPages);
            $('input[type=number]').attr('max', totalPages).val(currentPage);
            
            // Renderizar primera página
            renderPage(currentPage);
        }).catch(function(error) {
            console.error('Error al cargar el PDF:', error);
            $('#pdfViewer').html('<div class="alert alert-danger">Error al cargar el documento PDF</div>');
        });
    }
    
    // Renderizar una página
    function renderPage(pageNumber, callback) {
        pdfDoc.getPage(pageNumber).then(function(page) {
            var ctx = canvas.getContext('2d');
            
            // Calcular escala
            var containerWidth = $(canvasContainer).width();
            var viewport = page.getViewport({ scale: 1 });
            var scale = (containerWidth / viewport.width) * currentScale;
            var scaledViewport = page.getViewport({ scale: scale });
            
            // Ajustar canvas
            canvas.height = scaledViewport.height;
            canvas.width = scaledViewport.width;
            
            // Actualizar input de página
            $('input[type=number]').val(pageNumber);
            
            // Renderizar
            var renderContext = {
                canvasContext: ctx,
                viewport: scaledViewport
            };
            
            page.render(renderContext).promise.then(function() {
                // Si hay una búsqueda activa, actualizar destacados
                if (searchActive && callback) {
                    callback();
                }
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
            
            // Navegar con teclas de flecha
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                if (currentPage > 1) {
                    currentPage--;
                    renderPage(currentPage);
                    e.preventDefault();
                }
                return false;
            }
            
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderPage(currentPage);
                    e.preventDefault();
                }
                return false;
            }
            
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
            
            // Búsqueda con Ctrl+F
            if (e.ctrlKey && (e.key === 'f' || e.keyCode === 70)) {
                $('#pdfSearchInput').focus();
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
    
    // Cargar PDF.js desde CDN
    $.getScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js')
        .done(function() {
            // Configurar el worker
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
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