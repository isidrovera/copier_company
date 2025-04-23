// copier_company/static/src/js/copier_list.js
// Script completamente independiente, sin heredar de Odoo
(function() {
    console.log('[DEBUG] script independiente copier_list.js cargado');

    // Punto de entrada: se llama tan pronto como el DOM esté listo
    function init() {
        console.log('[DEBUG] inicializando CopierList');

        var container = document.querySelector('.copier-list-container');
        if (!container) {
            console.warn('[WARN] No se encontró el contenedor .copier-list-container');
            return;
        }

        // 1️⃣ Configuramos siempre el toggle de vistas
        initViewToggle(container);

        // 2️⃣ Arrancamos la parte de modal (que depende de Bootstrap)
        initReserveFlow(container);
    }

    // Registra init() al DOMContentLoaded, o lo ejecuta inmediatamente si ya pasó
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ————————————————————————————————————————————————————————————————
    // Inicializa el toggle Lista ↔ Kanban
    // ————————————————————————————————————————————————————————————————
    function initViewToggle(container) {
        console.log('[DEBUG] Configurando toggle de vistas');

        var btnList    = container.querySelector('#btn-list-view');
        var btnKanban  = container.querySelector('#btn-kanban-view');

        if (!btnList || !btnKanban) {
            console.error('[ERROR] Botones de vista no encontrados');
            return;
        }

        btnList.addEventListener('click',  function() { toggleView('list', container); });
        btnKanban.addEventListener('click', function() { toggleView('kanban', container); });

        // Aplicar preferencia previa, o 'list' si no existe
        var saved = localStorage.getItem('copierViewPreference') || 'list';
        console.log('[DEBUG] Aplicando preferencia previa:', saved);
        toggleView(saved, container);
    }

    function toggleView(mode, container) {
        var btnList    = container.querySelector('#btn-list-view');
        var btnKanban  = container.querySelector('#btn-kanban-view');
        var listView   = container.querySelector('#list-view');
        var kanbanView = container.querySelector('#kanban-view');

        console.log('[DEBUG] Cambiando a vista', mode.toUpperCase());

        if (mode === 'list') {
            listView.style.display   = 'block';
            kanbanView.style.display = 'none';
            btnList.classList.add('active');
            btnKanban.classList.remove('active');
        } else {
            listView.style.display   = 'none';
            kanbanView.style.display = 'block';
            btnKanban.classList.add('active');
            btnList.classList.remove('active');
        }

        localStorage.setItem('copierViewPreference', mode);
    }

    // ————————————————————————————————————————————————————————————————
    // Inicializa el flujo de reserva (carga Bootstrap si hace falta)
    // ————————————————————————————————————————————————————————————————
    function initReserveFlow(container) {
        console.log('[DEBUG] Verificando existencia de Bootstrap para el modal');

        if (typeof bootstrap === 'undefined') {
            console.warn('[WARN] Bootstrap no está cargado, cargando desde CDN...');
            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js';
            script.integrity = 'sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq';
            script.crossOrigin = 'anonymous';
            script.onload = function() {
                console.log('[DEBUG] Bootstrap cargado desde CDN');
                initReserveModal(container);
            };
            script.onerror = function() {
                console.error('[ERROR] No se pudo cargar Bootstrap. El modal de reserva no funcionará.');
            };
            document.head.appendChild(script);
        } else {
            console.log('[DEBUG] Bootstrap ya presente');
            initReserveModal(container);
        }
    }

    function initReserveModal(container) {
        try {
            console.log('[DEBUG] Inicializando modal de reserva');

            var modalEl     = container.querySelector('#reserveModal');
            var reserveBtns = container.querySelectorAll('.reserve-btn');
            var reserveForm = container.querySelector('#reserveForm');

            if (!modalEl) {
                console.error('[ERROR] Elemento #reserveModal no encontrado');
                return;
            }
            if (!reserveForm) {
                console.error('[ERROR] Formulario #reserveForm no encontrado');
                return;
            }
            if (!reserveBtns.length) {
                console.warn('[WARN] No se hallaron botones .reserve-btn');
            }

            var reserveModal = new bootstrap.Modal(modalEl);
            console.log('[DEBUG] Modal de reserva inicializado con bootstrap.Modal');

            reserveBtns.forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var id = btn.dataset.machineId;
                    console.log('[DEBUG] Reserva solicitada para máquina ID:', id);
                    reserveForm.action = '/stock-maquinas/' + id + '/reserve';
                    reserveModal.show();
                });
            });

            console.log('[DEBUG] Event listeners de reserva configurados en ' + reserveBtns.length + ' botones');
        } catch (error) {
            console.error('[ERROR] Excepción en initReserveModal:', error);
            alert('Error: No se pudo inicializar el modal de reserva. Por favor, recarga la página.');
        }
    }

})();
