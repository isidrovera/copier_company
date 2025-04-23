// copier_company/static/src/js/copier_list.js
// Script completamente independiente, sin heredar de Odoo
(function() {
    console.log('[DEBUG] script independiente copier_list.js cargado');

    document.addEventListener('DOMContentLoaded', function() {
        console.log('[DEBUG] DOMContentLoaded: inicializando CopierList');

        var container = document.querySelector('.copier-list-container');
        if (!container) {
            console.warn('[WARN] No se encontró el contenedor .copier-list-container, abortando inicialización');
            return;
        }
        console.log('[DEBUG] Contenedor principal encontrado');

        // Comprueba y carga Bootstrap si es necesario
        checkBootstrapAndInit();

        function checkBootstrapAndInit() {
            console.log('[DEBUG] Verificando existencia de Bootstrap');
            if (typeof bootstrap === 'undefined') {
                console.warn('[ERROR] Bootstrap no está cargado, cargando desde CDN...');
                var script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js';
                script.integrity = 'sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq';
                script.crossOrigin = 'anonymous';
                script.onload = function() {
                    console.log('[DEBUG] Bootstrap cargado desde CDN');
                    initComponents();
                };
                script.onerror = function() {
                    console.error('[ERROR] No se pudo cargar Bootstrap desde CDN');
                    alert('Error: No se pudo cargar Bootstrap. Algunas funcionalidades estarán limitadas.');
                };
                document.head.appendChild(script);
            } else {
                console.log('[DEBUG] Bootstrap ya está presente');
                initComponents();
            }
        }

        // Inicializa toggle de vistas y modal de reserva
        function initComponents() {
            console.log('[DEBUG] Inicializando componentes: toggle de vistas y modal de reserva');
            initViewToggle();
            initReserveModal();
        }

        // Configura cambio entre lista y Kanban
        function initViewToggle() {
            console.log('[DEBUG] Configurando toggle de vistas');
            var btnList   = container.querySelector('#btn-list-view');
            var btnKanban = container.querySelector('#btn-kanban-view');
            var listView  = container.querySelector('#list-view');
            var kanbanView= container.querySelector('#kanban-view');

            if (!btnList || !btnKanban) {
                console.error('[ERROR] Botones de vista no encontrados');
                return;
            }

            btnList.addEventListener('click', function() {
                console.log('[DEBUG] Cambiando a vista LISTA');
                listView.style.display   = 'block';
                kanbanView.style.display = 'none';
                btnList.classList.add('active');
                btnKanban.classList.remove('active');
                localStorage.setItem('copierViewPreference', 'list');
            });

            btnKanban.addEventListener('click', function() {
                console.log('[DEBUG] Cambiando a vista KANBAN');
                listView.style.display   = 'none';
                kanbanView.style.display = 'block';
                btnKanban.classList.add('active');
                btnList.classList.remove('active');
                localStorage.setItem('copierViewPreference', 'kanban');
            });

            var saved = localStorage.getItem('copierViewPreference');
            console.log('[DEBUG] Preferencia guardada:', saved);
            if (saved === 'kanban') {
                console.log('[DEBUG] Aplicando preferencia KANBAN');
                btnKanban.click();
            }
        }

        // Inicializa el modal de reserva con logs detallados
        function initReserveModal() {
            try {
                console.log('[DEBUG] Inicializando modal de reserva');
                var modalEl     = container.querySelector('#reserveModal');
                var reserveBtns = container.querySelectorAll('.reserve-btn');
                var reserveForm = container.querySelector('#reserveForm');

                if (!modalEl) {
                    console.error('[ERROR] Elemento #reserveModal no encontrado');
                    return;
                }
                if (!reserveBtns.length) {
                    console.warn('[WARN] No se hallaron botones .reserve-btn');
                }
                if (!reserveForm) {
                    console.error('[ERROR] Formulario #reserveForm no encontrado');
                    return;
                }

                var reserveModal = new bootstrap.Modal(modalEl);
                console.log('[DEBUG] Modal de reserva inicializado');

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
    });
})();
