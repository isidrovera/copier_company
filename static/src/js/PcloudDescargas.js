document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var filesList = document.getElementById('files-list');
    var listViewBtn = document.getElementById('list-view-btn');
    var kanbanViewBtn = document.getElementById('kanban-view-btn');
    var listView = document.getElementById('list-view');
    var kanbanView = document.getElementById('kanban-view');
    var viewMode = localStorage.getItem('viewMode') || 'list';
    var modifiedHeader = document.getElementById('modified-header');
    var sortIcon = document.getElementById('sort-icon');
    var ascending = localStorage.getItem('sortDirection') === 'true' || true;

    // Función mejorada para establecer el modo de vista con transiciones suaves
    function setViewMode(mode) {
        if (mode === 'list') {
            listView.classList.remove('d-none');
            kanbanView.classList.add('d-none');
            listViewBtn.classList.add('active');
            kanbanViewBtn.classList.remove('active');
        } else {
            listView.classList.add('d-none');
            kanbanView.classList.remove('d-none');
            listViewBtn.classList.remove('active');
            kanbanViewBtn.classList.add('active');
        }
        localStorage.setItem('viewMode', mode);
        
        // Actualizar URL con el modo de vista sin recargar la página
        const url = new URL(window.location.href);
        url.searchParams.set('view_mode', mode);
        window.history.replaceState({}, '', url);
    }

    // Event listeners para botones de vista con feedback visual mejorado
    listViewBtn.addEventListener('click', function() {
        setViewMode('list');
        this.classList.add('pulse-animation');
        setTimeout(() => this.classList.remove('pulse-animation'), 300);
    });

    kanbanViewBtn.addEventListener('click', function() {
        setViewMode('kanban');
        this.classList.add('pulse-animation');
        setTimeout(() => this.classList.remove('pulse-animation'), 300);
    });

    // Búsqueda mejorada con resaltado de coincidencias y debounce
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            var searchTerm = searchInput.value.toLowerCase().trim();
            
            // Búsqueda en vista de lista
            var rows = filesList.getElementsByTagName('tr');
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var fileNameElement = row.querySelector('.file-name');
                if (!fileNameElement) continue;
                
                var fileName = fileNameElement.innerText.toLowerCase();
                if (searchTerm === '' || fileName.includes(searchTerm)) {
                    row.style.display = '';
                    // Resaltar coincidencias si hay término de búsqueda
                    if (searchTerm !== '') {
                        highlightMatches(fileNameElement, fileName, searchTerm);
                    } else {
                        // Restaurar texto original sin resaltado
                        fileNameElement.innerHTML = fileNameElement.textContent;
                    }
                } else {
                    row.style.display = 'none';
                }
            }

            // Búsqueda en vista Kanban
            var cards = kanbanView.querySelectorAll('.card');
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i];
                var cardTitle = card.querySelector('.card-title');
                if (!cardTitle) continue;
                
                var fileName = cardTitle.innerText.toLowerCase();
                var cardContainer = card.closest('[class*="col-"]'); // Obtener el contenedor de la tarjeta
                
                if (searchTerm === '' || fileName.includes(searchTerm)) {
                    cardContainer.style.display = '';
                    // Resaltar coincidencias
                    if (searchTerm !== '') {
                        highlightMatches(cardTitle, fileName, searchTerm);
                    } else {
                        cardTitle.innerHTML = cardTitle.textContent;
                    }
                } else {
                    cardContainer.style.display = 'none';
                }
            }
            
            // Mostrar mensaje cuando no hay resultados
            checkNoResults(rows, cards, searchTerm);
            
        }, 300); // Debounce de 300ms
    });

    // Función para resaltar coincidencias
    function highlightMatches(element, text, searchTerm) {
        var originalText = element.textContent;
        var lowerText = originalText.toLowerCase();
        var html = '';
        var lastIndex = 0;
        var index = lowerText.indexOf(searchTerm);
        
        while (index !== -1) {
            html += originalText.substring(lastIndex, index);
            html += '<span class="highlight">' + originalText.substring(index, index + searchTerm.length) + '</span>';
            lastIndex = index + searchTerm.length;
            index = lowerText.indexOf(searchTerm, lastIndex);
        }
        
        html += originalText.substring(lastIndex);
        element.innerHTML = html;
    }
    
    // Función para verificar si no hay resultados y mostrar mensaje
    function checkNoResults(rows, cards, searchTerm) {
        if (searchTerm === '') return;
        
        // Verificar si hay algún resultado visible
        let visibleInList = Array.from(rows).some(row => row.style.display !== 'none');
        let visibleInKanban = Array.from(cards).some(card => card.closest('[class*="col-"]').style.display !== 'none');
        
        // Mostrar mensaje de "no hay resultados" si es necesario
        let noResultsMsgList = document.getElementById('no-results-list');
        let noResultsMsgKanban = document.getElementById('no-results-kanban');
        
        if (!noResultsMsgList) {
            noResultsMsgList = document.createElement('div');
            noResultsMsgList.id = 'no-results-list';
            noResultsMsgList.className = 'text-center py-5 text-muted';
            noResultsMsgList.innerHTML = '<i class="fa fa-search fa-2x mb-3"></i><h5>No se encontraron resultados</h5>';
            listView.appendChild(noResultsMsgList);
        }
        
        if (!noResultsMsgKanban) {
            noResultsMsgKanban = document.createElement('div');
            noResultsMsgKanban.id = 'no-results-kanban';
            noResultsMsgKanban.className = 'text-center py-5 text-muted col-12';
            noResultsMsgKanban.innerHTML = '<i class="fa fa-search fa-2x mb-3"></i><h5>No se encontraron resultados</h5>';
            kanbanView.querySelector('.row').appendChild(noResultsMsgKanban);
        }
        
        noResultsMsgList.style.display = !visibleInList ? 'block' : 'none';
        noResultsMsgKanban.style.display = !visibleInKanban ? 'block' : 'none';
    }

    // Ordenamiento mejorado de fechas con animación y persistencia
    modifiedHeader.addEventListener('click', function() {
        // Actualizar icon de ordenamiento primero para feedback visual inmediato
        sortIcon.className = ascending ? 'fa fa-sort-desc ms-1' : 'fa fa-sort-asc ms-1';
        
        // Añadir indicador visual de carga
        modifiedHeader.classList.add('sorting');
        
        // Usar setTimeout para permitir que se muestre el feedback visual
        setTimeout(function() {
            var rows = Array.from(filesList.getElementsByTagName('tr'));
            
            // Mejorar el parsing de fecha para mayor compatibilidad
            rows.sort(function(a, b) {
                var dateA = parseDate(a.getElementsByTagName('td')[2].innerText);
                var dateB = parseDate(b.getElementsByTagName('td')[2].innerText);
                return ascending ? dateB - dateA : dateA - dateB; // Invertido para ser más intuitivo
            });

            // Animación suave para reordenar filas
            rows.forEach(function(row, index) {
                // Añadir delay incremental para efecto cascada
                setTimeout(() => {
                    filesList.appendChild(row);
                    row.classList.add('row-highlight');
                    setTimeout(() => row.classList.remove('row-highlight'), 300);
                }, index * 20);
            });
            
            // Invertir la dirección y guardar en localStorage
            ascending = !ascending;
            localStorage.setItem('sortDirection', ascending);
            
            // Quitar indicador de carga
            modifiedHeader.classList.remove('sorting');
        }, 10);
    });

    // Función mejorada para parsing de fechas en diferentes formatos
    function parseDate(dateStr) {
        if (!dateStr) return new Date(0);
        
        // Intentar formato estándar primero
        let date = new Date(dateStr);
        
        // Si la fecha es inválida, intentar otros formatos comunes
        if (isNaN(date.getTime())) {
            // Formato español DD/MM/YYYY
            let parts = dateStr.split('/');
            if (parts.length === 3) {
                date = new Date(parts[2], parts[1] - 1, parts[0]);
            }
            
            // Si sigue siendo inválida, último intento con regex
            if (isNaN(date.getTime())) {
                let match = dateStr.match(/(\d{1,2})[-\/](\d{1,2})[-\/](\d{2,4})/);
                if (match) {
                    date = new Date(
                        match[3].length === 2 ? '20' + match[3] : match[3],
                        parseInt(match[2]) - 1,
                        match[1]
                    );
                }
            }
        }
        
        return isNaN(date.getTime()) ? new Date(0) : date;
    }

    // Inicializar vista basada en localStorage o parámetro URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlViewMode = urlParams.get('view_mode');
    if (urlViewMode === 'list' || urlViewMode === 'kanban') {
        viewMode = urlViewMode;
    }
    setViewMode(viewMode);
    
    // Inicializar ícono de ordenamiento
    sortIcon.className = ascending ? 'fa fa-sort-asc ms-1' : 'fa fa-sort-desc ms-1';
    
    // Añadir efectos hover para tarjetas en vista Kanban
    const cards = document.querySelectorAll('.hover-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });
    
    // Añadir comportamiento para la barra de búsqueda
    searchInput.addEventListener('focus', function() {
        this.parentElement.classList.add('search-focused');
    });
    
    searchInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('search-focused');
    });
    
    // Si hay un parámetro de búsqueda en la URL, activar la búsqueda automáticamente
    const urlSearchTerm = urlParams.get('search');
    if (urlSearchTerm) {
        searchInput.value = urlSearchTerm;
        // Disparar el evento input manualmente
        searchInput.dispatchEvent(new Event('input'));
    }
});