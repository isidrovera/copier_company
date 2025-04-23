// copier_company/static/src/js/copier_list.js
document.addEventListener('DOMContentLoaded', function () {
    console.log('[DEBUG] DOM cargado completamente. Inicializando script de fotocopiadoras...');
    inicializarComponentes();
});

function inicializarComponentes() {
    console.log('[DEBUG] Inicializando componentes...');

    // Botones de cambio de vista
    const btnListView   = document.getElementById('btn-list-view');
    const btnKanbanView = document.getElementById('btn-kanban-view');
    const listView      = document.getElementById('list-view');
    const kanbanView    = document.getElementById('kanban-view');

    if (!btnListView || !btnKanbanView) {
        console.error('[ERROR] No se encontraron los botones de vista');
        return;
    }

    // Cambio a vista de lista
    btnListView.addEventListener('click', () => {
        console.log('[DEBUG] Cambiando a vista de lista');
        listView.style.display = 'block';
        kanbanView.style.display = 'none';
        btnListView.classList.add('active');
        btnKanbanView.classList.remove('active');
        localStorage.setItem('copierViewPreference', 'list');
    });

    // Cambio a vista kanban
    btnKanbanView.addEventListener('click', () => {
        console.log('[DEBUG] Cambiando a vista kanban');
        listView.style.display = 'none';
        kanbanView.style.display = 'block';
        btnKanbanView.classList.add('active');
        btnListView.classList.remove('active');
        localStorage.setItem('copierViewPreference', 'kanban');
    });

    // Aplicar preferencia guardada
    const savedView = localStorage.getItem('copierViewPreference');
    if (savedView === 'kanban') {
        console.log('[DEBUG] Aplicando preferencia: vista kanban');
        btnKanbanView.click();
    }

    // Inicializar modal de reserva (ya que Bootstrap está en el bundle)
    try {
        const modalEl = document.getElementById('reserveModal');
        if (!modalEl) {
            console.error('[ERROR] No se encontró el elemento del modal');
            return;
        }
        const reserveModal = new bootstrap.Modal(modalEl);
        const reserveBtns  = document.querySelectorAll('.reserve-btn');
        const reserveForm  = document.getElementById('reserveForm');
        if (!reserveForm) {
            console.error('[ERROR] No se encontró el formulario de reserva');
            return;
        }
        reserveBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const machineId = btn.dataset.machineId;
                console.log('[DEBUG] Reserva solicitada para máquina ID:', machineId);
                reserveForm.action = `/stock-maquinas/${machineId}/reserve`;
                reserveModal.show();
            });
        });
    } catch (err) {
        console.error('[ERROR] Error al inicializar modal:', err);
        alert('Error: No se pudo inicializar el modal de reserva. Por favor, recarga la página.');
    }
}
