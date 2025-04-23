// copier_list.js - Versión independiente sin dependencias de Odoo
// Esta versión elimina todas las referencias a odoo.define y otros métodos de Odoo

// Esperar a que el DOM esté completamente cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando Copier List...');
    
    // Referencias a elementos del DOM
    const btnListView = document.getElementById('btn-list-view');
    const btnKanbanView = document.getElementById('btn-kanban-view');
    const listView = document.getElementById('list-view');
    const kanbanView = document.getElementById('kanban-view');
    const searchInput = document.querySelector('[name="search"]');
    const reserveButtons = document.querySelectorAll('.reserve-btn');
    
    // Configurar eventos para los botones de vista
    if (btnListView) {
        btnListView.addEventListener('click', function() {
            console.log('Cambiando a vista de lista');
            btnListView.classList.add('active');
            btnKanbanView.classList.remove('active');
            
            if (listView) listView.style.display = 'block';
            if (kanbanView) kanbanView.style.display = 'none';
            
            localStorage.setItem('preferredView', 'list');
        });
    }
    
    if (btnKanbanView) {
        btnKanbanView.addEventListener('click', function() {
            console.log('Cambiando a vista de kanban');
            btnKanbanView.classList.add('active');
            if (btnListView) btnListView.classList.remove('active');
            
            if (kanbanView) kanbanView.style.display = 'block';
            if (listView) listView.style.display = 'none';
            
            localStorage.setItem('preferredView', 'kanban');
        });
    }
    
    // Configurar botones de reserva
    reserveButtons.forEach(button => {
        button.addEventListener('click', function(ev) {
            ev.preventDefault();
            
            const machineId = this.getAttribute('data-machine-id');
            console.log(`Intentando reservar máquina ID: ${machineId}`);
            
            const reserveForm = document.getElementById('reserveForm');
            if (reserveForm) {
                reserveForm.setAttribute('action', `/stock-maquinas/${machineId}/reserve`);
                console.log(`Formulario actualizado con acción: /stock-maquinas/${machineId}/reserve`);
            }
            
            // Mostrar modal usando Bootstrap
            const modal = document.getElementById('reserveModal');
            if (modal && typeof bootstrap !== 'undefined') {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            } else {
                console.error('No se pudo encontrar el modal o Bootstrap no está disponible');
            }
        });
    });
    
    // Configurar campo de búsqueda con debounce
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function(ev) {
            clearTimeout(searchTimeout);
            
            searchTimeout = setTimeout(() => {
                const value = ev.target.value;
                console.log(`Búsqueda: "${value}"`);
                
                if (value.length >= 3 || value.length === 0) {
                    const form = ev.target.closest('form');
                    if (form) {
                        console.log('Enviando formulario de búsqueda');
                        form.submit();
                    }
                }
            }, 500);
        });
    }
    
    // Inicializar tooltips de Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        console.log('Tooltips de Bootstrap inicializados');
    }
    
    // Restaurar vista preferida
    restorePreferredView();
    
    function restorePreferredView() {
        const preferredView = localStorage.getItem('preferredView');
        console.log(`Restaurando vista preferida: ${preferredView || 'ninguna guardada'}`);
        
        if (preferredView === 'kanban' && btnKanbanView) {
            btnKanbanView.click();
        }
    }
});