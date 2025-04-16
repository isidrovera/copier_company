/* 
 * Visor de PDF mejorado y estable para Odoo 18
 * Incluye búsqueda optimizada dentro del PDF y controles adicionales
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
    var searchInProgress = false;
    
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
                if (currentPage !== 1) {
                    currentPage = 1;
                    renderPage(currentPage);
                }
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
                if (!isNaN(page) && page >= 1 && page <= totalPages) {
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
                if (currentPage !== totalPages) {
                    currentPage = totalPages;
                    renderPage(currentPage);
                }
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
        
        // Botón explícito de búsqueda para evitar reaccionar a cada tecla
        var $searchButton = $('<button id="pdfSearchButton" class="btn btn-primary ml-1">Buscar</button>');
        $searchButton.insertAfter($searchInput);
        
        // Botón para cancelar búsqueda
        var $cancelButton = $('<button id="pdfSearchCancel" class="btn btn-outline-secondary ml-1">Cancelar</button>')
            .css('display', 'none')
            .on('click', function() {
                if (searchInProgress) {
                    searchInProgress = false;
                    $(this).hide();
                    $searchButton.show();
                }
                clearSearch();
                $searchInput.val('');
            });
        $cancelButton.insertAfter($searchButton);
        
        // Buscar con Enter
        $searchInput.on('keypress', function(e) {
            if (e.which === 13) { // Enter key
                e.preventDefault();
                $searchButton.click();
            }
        });
        
        // Iniciar búsqueda con el botón
        $searchButton.on('click', function() {
            var text = $searchInput.val().trim();
            if (text.length >= 2) {
                searchText = text;
                $searchButton.hide();
                $cancelButton.show();
                performSearch();
            } else {
                $searchResults.text("Ingrese al menos 2 caracteres");
                setTimeout(function() { 
                    $searchResults.text("");
                }, 3000);
            }
        });
        
        // Navegación entre resultados
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
        
        // Función principal de búsqueda
        function performSearch() {
            searchActive = true;
            searchInProgress = true;
            searchMatches = [];
            searchMatchIndex = -1;
            
            $searchResults.text("Buscando...");
            $searchPrev.prop('disabled', true);
            $searchNext.prop('disabled', true);
            
            // Reiniciar página actual
            var currentPageBackup = currentPage;
            
            // Limitar el número de páginas a procesar por lote para evitar bloqueos
            var batchSize = 5;
            var currentBatch = 1;
            var maxBatches = Math.ceil(totalPages / batchSize);
            
            processBatch(1, batchSize);
            
            // Procesar lotes de páginas secuencialmente
            function processBatch(startPage, endPage) {
                if (!searchInProgress) {
                    $searchResults.text("Búsqueda cancelada");
                    return;
                }
                
                if (startPage > totalPages) {
                    finishSearch();
                    return;
                }
                
                // Ajustar el final del lote
                endPage = Math.min(endPage, totalPages);
                
                // Actualizar progreso
                $searchResults.text("Buscando... (" + Math.round((currentBatch / maxBatches) * 100) + "%)");
                
                // Buscar en este lote de páginas
                searchPagesInRange(startPage, endPage, function() {
                    // Avanzar al siguiente lote
                    currentBatch++;
                    processBatch(endPage + 1, endPage + batchSize);
                });
            }
            
            // Buscar en un rango específico de páginas
            function searchPagesInRange(start, end, callback) {
                var currentPageIndex = start;
                
                function processNextPage() {
                    if (currentPageIndex > end || !searchInProgress) {
                        callback();
                        return;
                    }
                    
                    try {
                        pdfDoc.getPage(currentPageIndex).then(function(page) {
                            return page.getTextContent().then(function(textContent) {
                                // Obtener texto de la página
                                var pageText = textContent.items.map(function(item) {
                                    return item.str;
                                }).join(' ');
                                
                                // Buscar coincidencias
                                var regex = new RegExp(escapeRegExp(searchText), 'gi');
                                var match;
                                while ((match = regex.exec(pageText)) !== null) {
                                    searchMatches.push({
                                        page: currentPageIndex,
                                        index: match.index,
                                        length: searchText.length
                                    });
                                }
                                
                                // Avanzar a la siguiente página
                                currentPageIndex++;
                                setTimeout(processNextPage, 0);
                            }).catch(function(error) {
                                console.error("Error al obtener texto de la página " + currentPageIndex + ":", error);
                                currentPageIndex++;
                                setTimeout(processNextPage, 0);
                            });
                        }).catch(function(error) {
                            console.error("Error al obtener la página " + currentPageIndex + ":", error);
                            currentPageIndex++;
                            setTimeout(processNextPage, 0);
                        });
                    } catch (error) {
                        console.error("Error inesperado al procesar la página " + currentPageIndex + ":", error);
                        currentPageIndex++;
                        setTimeout(processNextPage, 0);
                    }
                }
                
                // Iniciar procesamiento
                processNextPage();
            }
            
            // Finalizar búsqueda cuando todas las páginas hayan sido procesadas
            function finishSearch() {
                searchInProgress = false;
                
                if (searchMatches.length > 0) {
                    $searchResults.text(searchMatches.length + " coincidencia(s)");
                    $searchPrev.prop('disabled', false);
                    $searchNext.prop('disabled', false);
                    
                    // Ir a la primera coincidencia
                    searchMatchIndex = 0;
                    highlightCurrentMatch();
                } else {
                    $searchResults.text("No se encontraron coincidencias");
                    $cancelButton.hide();
                    $searchButton.show();
                    
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
            searchInProgress = false;
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
                
                // Actualizar la interfaz de usuario primero
                $searchResults.text((searchMatchIndex + 1) + " de " + searchMatches.length);
                
                // Validar número de página antes de cambiar
                if (match.page < 1 || match.page > totalPages) {
                    console.error("Número de página inválido:", match.page, "Total:", totalPages);
                    // Si la página no es válida, simplemente avanzar al siguiente resultado
                    if (searchMatches.length > 1) {
                        searchMatchIndex = (searchMatchIndex + 1) % searchMatches.length;
                        highlightCurrentMatch();
                    }
                    return;
                }
                
                // Cambiar a la página de la coincidencia actual
                if (currentPage !== match.page) {
                    currentPage = match.page;
                    // Primero renderizar la página, luego resaltar
                    renderPage(currentPage, function() {
                        // Dar tiempo al renderizado para completarse
                        setTimeout(function() {
                            highlightTextInPage(match);
                        }, 300);
                    });
                } else {
                    // Ya estamos en la página correcta, sólo resaltar
                    highlightTextInPage(match);
                }
            }
        }
        
        function highlightTextInPage(match) {
            // Primero limpiar cualquier resaltado anterior
            $('#textLayer').empty();
            
            try {
                // Verificar que la página sea válida
                if (match.page < 1 || match.page > totalPages) {
                    console.error("Página inválida para resaltado:", match.page);
                    return;
                }
                
                pdfDoc.getPage(match.page).then(function(page) {
                    return page.getTextContent().then(function(textContent) {
                        var $textLayer = $('#textLayer');
                        
                        // Crear elemento de resaltado
                        var highlight = $('<div class="search-highlight current"></div>')
                            .css({
                                position: 'absolute',
                                background: 'rgba(255, 255, 0, 0.4)',
                                border: '2px solid #ff8c00', // naranja más intenso
                                'border-radius': '3px',
                                'pointer-events': 'none',
                                'z-index': '100',
                                'box-shadow': '0 0 10px rgba(255, 140, 0, 0.7)' // Añadir un resplandor
                            });
                        
                        // Viewport actual
                        var viewport = page.getViewport({ scale: currentScale });
                        
                        // Encontrar el elemento de texto que contiene la coincidencia
                        var charIndex = 0;
                        var foundItem = null;
                        var matchStartIndex = -1;
                        
                        for (var i = 0; i < textContent.items.length; i++) {
                            var item = textContent.items[i];
                            var itemEndIndex = charIndex + item.str.length;
                            
                            // Comprobar si la coincidencia está dentro de este item
                            if (charIndex <= match.index && match.index < itemEndIndex) {
                                foundItem = item;
                                matchStartIndex = charIndex;
                                break;
                            }
                            
                            charIndex += item.str.length + 1; // +1 por el espacio
                        }
                        
                        // Si encontramos el elemento, resaltarlo
                        if (foundItem) {
                            // Transformar coordenadas del item
                            var tx = pdfjsLib.Util.transform(
                                viewport.transform,
                                foundItem.transform
                            );
                            
                            // Calcular offset relativo dentro del item
                            var relativeOffset = match.index - matchStartIndex;
                            
                            // Estimar ancho de caracter (usando una aproximación simple)
                            var charWidth = foundItem.width / foundItem.str.length;
                            
                            // Posicionar el resaltado
                            var left = tx[4] + (relativeOffset * charWidth);
                            var top = tx[5] - foundItem.height;
                            var width = searchText.length * charWidth;
                            var height = foundItem.height * 1.2;
                            
                            highlight.css({
                                left: left + 'px',
                                top: top + 'px',
                                width: width + 'px',
                                height: height + 'px'
                            });
                            
                            $textLayer.append(highlight);
                            
                            // Scroll hasta la coincidencia
                            setTimeout(function() {
                                var container = $(canvasContainer);
                                container.scrollTop(
                                    top - (container.height() / 3)
                                );
                            }, 100);
                        } else {
                            console.log("No se pudo encontrar la posición exacta del texto en la página");
                            
                            // Intentar scroll aproximado a un tercio de la página
                            setTimeout(function() {
                                $(canvasContainer).scrollTop(viewport.height / 3);
                            }, 100);
                        }
                    }).catch(function(error) {
                        console.error("Error al obtener el contenido de texto:", error);
                    });
                }).catch(function(error) {
                    console.error("Error al obtener la página para resaltado:", error);
                });
            } catch (error) {
                console.error("Error inesperado al resaltar texto:", error);
            }
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
        if (pageNumber < 1 || pageNumber > totalPages) {
            console.error("Intento de renderizar página inválida:", pageNumber, "Total:", totalPages);
            pageNumber = 1; // Valor predeterminado seguro
        }
        
        // Limpiar capa de texto en cada cambio de página
        $('#textLayer').empty();
        
        // Mostrar indicador de carga
        var loadingIndicator = $('<div class="loading-indicator text-center py-3"><div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando página...</span></div></div>');
        $(canvasContainer).prepend(loadingIndicator);
        
        // Intentar obtener y renderizar la página
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
                // Quitar indicador de carga
                loadingIndicator.remove();
                
                // Si hay una función de callback (para búsqueda), ejecutarla
                if (typeof callback === 'function') {
                    callback();
                }
            }).catch(function(error) {
                loadingIndicator.remove();
                console.error("Error al renderizar la página:", error);
                $(canvasContainer).prepend('<div class="alert alert-warning">Error al renderizar la página. Intente cambiar de página o recargar el visor.</div>');
            });
        }).catch(function(error) {
            loadingIndicator.remove();
            console.error("Error al obtener la página:", error);
            $(canvasContainer).prepend('<div class="alert alert-warning">Error al cargar la página. Intente cambiar de página o recargar el visor.</div>');
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
    
    // Cargar PDF.js desde CDN (usando la versión 3.11.174 que parece estar ya cargada en el sistema)
    $.getScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js')
        .done(function() {
            // Configurar el worker con la MISMA versión
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            // Inicializar visor
            initViewer();
            
            // Prevenir acciones no deseadas
            preventUnwantedActions();
            
            // Mejorar las funcionalidades del visor, iniciando con la búsqueda
            console.log("PDF.js cargado exitosamente, versión:", pdfjsLib.version);
        })
        .fail(function() {
            console.error('No se pudo cargar PDF.js');
            $container.html('<div class="alert alert-danger">No se pudo cargar el visor de PDF</div>');
        });
});