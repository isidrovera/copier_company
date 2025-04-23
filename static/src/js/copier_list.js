/** @odoo-module **/

// Standalone implementation without Odoo widget dependencies
odoo.define('copier_company.copier_list', function (require) {
    'use strict';
    
    console.log('[DEBUG] Cargando módulo copier_company.copier_list');
    
    // Esperar a que el DOM esté completamente cargado
    document.addEventListener('DOMContentLoaded', function() {
        // Buscar el contenedor principal
        const container = document.querySelector('.copier-list-container');
        if (!container) {
            console.warn('[WARN] No se encontró el contenedor .copier-list-container');
            return;
        }
        
        console.log('[DEBUG] Contenedor encontrado, inicializando CopierList');
        initCopierList(container);
    });
    
    /**
     * Inicializa todas las funcionalidades del componente CopierList
     * @param {HTMLElement} container - El elemento contenedor principal
     */
    function initCopierList(container) {
        console.log('[DEBUG] OWL Widget CopierList montado');
        checkBootstrapAndInit(container);
    }
    
    /**
     * Comprueba si Bootstrap existe, si no lo carga y luego inicializa.
     * @param {HTMLElement} container - El elemento contenedor principal
     */
    function checkBootstrapAndInit(container) {
        console.log('[DEBUG] Verificando Bootstrap');
        if (typeof bootstrap === 'undefined') {
            console.warn('[ERROR] Bootstrap no está cargado, inyectando CDN...');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js';
            script.integrity = 'sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq';
            script.crossOrigin = 'anonymous';
            script.onload = () => {
                console.log('[DEBUG] Bootstrap cargado desde CDN');
                initComponents(container);
            };
            script.onerror = () => {
                console.error('[ERROR] Falló la carga de Bootstrap desde CDN');
                alert('Error: no se pudo cargar Bootstrap. Algunas funcionalidades estarán limitadas.');
            };
            document.head.appendChild(script);
        } else {
            console.log('[DEBUG] Bootstrap ya estaba disponible');
            initComponents(container);
        }
    }
    
    /**
     * Inicializa toggle de vistas y modal de reserva.
     * @param {HTMLElement} container - El elemento contenedor principal
     */
    function initComponents(container) {
        console.log('[DEBUG] Inicializando componentes de CopierList');
        initViewToggle(container);
        initReserveModal(container);
    }
    
    /**
     * Toggle entre vista Lista y Kanban.
     * @param {HTMLElement} container - El elemento contenedor principal
     */
    function initViewToggle(container) {
        console.log('[DEBUG] Configurando toggle de vistas');
        const btnList = container.querySelector('#btn-list-view');
        const btnKanban = container.querySelector('#btn-kanban-view');
        const listView = container.querySelector('#list-view');
        const kanbanView = container.querySelector('#kanban-view');
        
        if (!btnList || !btnKanban) {
            console.error('[ERROR] Botones de vista no encontrados');
            return;
        }
        
        btnList.addEventListener('click', () => {
            console.log('[DEBUG] Cambiando a vista LISTA');
            listView.style.display = 'block';
            kanbanView.style.display = 'none';
            btnList.classList.add('active');
            btnKanban.classList.remove('active');
            localStorage.setItem('copierViewPreference', 'list');
        });
        
        btnKanban.addEventListener('click', () => {
            console.log('[DEBUG] Cambiando a vista KANBAN');
            listView.style.display = 'none';
            kanbanView.style.display = 'block';
            btnKanban.classList.add('active');
            btnList.classList.remove('active');
            localStorage.setItem('copierViewPreference', 'kanban');
        });
        
        const saved = localStorage.getItem('copierViewPreference');
        console.log('[DEBUG] Preferencia guardada:', saved);
        if (saved === 'kanban') {
            console.log('[DEBUG] Aplicando preferencia KANBAN');
            btnKanban.click();
        }
    }
    
    /**
     * Inicializa el modal de reserva, con logs en cada paso.
     * @param {HTMLElement} container - El elemento contenedor principal
     */
    function initReserveModal(container) {
        try {
            console.log('[DEBUG] Inicializando modal de reserva');
            const modalEl = container.querySelector('#reserveModal');
            const reserveBtns = container.querySelectorAll('.reserve-btn');
            const reserveForm = container.querySelector('#reserveForm');
            
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
            
            const reserveModal = new bootstrap.Modal(modalEl);
            console.log('[DEBUG] Modal de reserva inicializado');
            
            reserveBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.dataset.machineId;
                    console.log('[DEBUG] Reserva solicitada para ID:', id);
                    reserveForm.action = `/stock-maquinas/${id}/reserve`;
                    reserveModal.show();
                });
            });
            console.log('[DEBUG] Event listeners de reserva configurados en', reserveBtns.length, 'botones');
        } catch (err) {
            console.error('[ERROR] Excepción en initReserveModal:', err);
            alert('Error: no se pudo inicializar el modal de reserva. Recarga la página, por favor.');
        }
    }
    
    return {
        initCopierList: initCopierList
    };
});