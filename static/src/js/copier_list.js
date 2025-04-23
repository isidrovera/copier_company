/**
 * Copier List - Script independiente para manejar vistas de lista y kanban
 * @author Claude
 * @version 1.0
 */

// Esperamos a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('CopierList: DOM cargado, inicializando script...');
    
    // Inicializar el controlador de la lista de copiadoras
    initCopierList();
    
    // Inicializar tooltips de Bootstrap
    initTooltips();
});

/**
 * Inicializa el controlador principal para la lista de copiadoras
 */
function initCopierList() {
    console.log('CopierList: Inicializando controlador...');
    
    // Referencias a elementos del DOM
    const btnListView = document.getElementById('btn-list-view');
    const btnKanbanView = document.getElementById('btn-kanban-view');
    const listView = document.getElementById('list-view');
    const kanbanView = document.getElementById('kanban-view');
    const searchInput = document.querySelector('[name="search"]');
    
    // Verificar que los elementos existen
    if (!btnListView || !btnKanbanView) {
        console.error('CopierList: No se encontraron los botones de cambio de vista');
        return;
    }
    
    // Configurar eventos para cambio de vista
    btnListView.addEventListener('click', function() {
        console.log('CopierList: Cambiando a vista de lista');
        btnListView.classList.add('active');
        btnKanbanView.classList.remove('active');
        
        if (listView) listView.style.display = 'block';
        if (kanbanView) kanbanView.style.display = 'none';
        
        localStorage.setItem('preferredView', 'list');
    });
    
    btnKanbanView.addEventListener('click', function() {
        console.log('CopierList: Cambiando a vista de kanban');
        btnKanbanView.classList.add('active');
        btnListView.classList.remove('active');
        
        if (kanbanView) kanbanView.style.display = 'block';
        if (listView) listView.style.display = 'none';
        
        localStorage.setItem('preferredView', 'kanban');
    });
    
    // Configurar botones de reserva
    setupReserveButtons();
    
    // Configurar campo de búsqueda
    if (searchInput) {
        console.log('CopierList: Configurando campo de búsqueda');
        let searchTimeout;
        
        searchInput.addEventListener('input', function(ev) {
            clearTimeout(searchTimeout);
            
            searchTimeout = setTimeout(() => {
                const value = ev.target.value;
                console.log(`CopierList: Buscando "${value}"`);
                
                if (value.length >= 3 || value.length === 0) {
                    const form = ev.target.closest('form');
                    if (form) {
                        console.log('CopierList: Enviando formulario de búsqueda');
                        form.submit();
                    }
                }
            }, 500);
        });
    }
    
    // Restaurar vista preferida
    restorePreferredView();
}

/**
 * Configura los botones de reserva
 */
function setupReserveButtons() {
    console.log('CopierList: Configurando botones de reserva');
    
    const reserveButtons = document.querySelectorAll('.reserve-btn');
    
    reserveButtons.forEach(button => {
        button.addEventListener('click', function(ev) {
            ev.preventDefault();
            
            const machineId = this.getAttribute('data-machine-id');
            console.log(`CopierList: Reservando máquina ID ${machineId}`);
            
            const reserveForm = document.getElementById('reserveForm');
            if (reserveForm) {
                reserveForm.setAttribute('action', `/stock-maquinas/${machineId}/reserve`);
            }
            
            // Mostrar modal usando Bootstrap
            const modal = document.getElementById('reserveModal');
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            } else {
                console.error('CopierList: No se encontró el modal de reserva');
            }
        });
    });
}

/**
 * Inicializa los tooltips de Bootstrap
 */
function initTooltips() {
    console.log('CopierList: Inicializando tooltips');
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Restaura la vista preferida del usuario desde localStorage
 */
function restorePreferredView() {
    const preferredView = localStorage.getItem('preferredView');
    console.log(`CopierList: Restaurando vista preferida: ${preferredView}`);
    
    if (preferredView === 'kanban') {
        const btnKanbanView = document.getElementById('btn-kanban-view');
        if (btnKanbanView) {
            btnKanbanView.click();
        }
    }
}