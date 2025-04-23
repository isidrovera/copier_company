/** @odoo-module **/

// Import the correct public widget module
import { publicWidget } from 'web.public.widget';

console.log('[DEBUG] Cargando módulo copier_company.copier_list');

publicWidget.registry.CopierList = publicWidget.Widget.extend({
    selector: '.copier-list-container',

    /**
     * Se ejecuta una vez OWL monta el contenedor.
     */
    start() {
        this._super(...arguments);
        console.log('[DEBUG] OWL Widget CopierList montado');
        this._checkBootstrapAndInit();
    },

    /**
     * Comprueba si Bootstrap existe, si no lo carga y luego inicializa.
     */
    _checkBootstrapAndInit() {
        console.log('[DEBUG] Verificando Bootstrap');
        if (typeof bootstrap === 'undefined') {
            console.warn('[ERROR] Bootstrap no está cargado, inyectando CDN...');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js';
            script.integrity = 'sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq';
            script.crossOrigin = 'anonymous';
            script.onload = () => {
                console.log('[DEBUG] Bootstrap cargado desde CDN');
                this._initComponents();
            };
            script.onerror = () => {
                console.error('[ERROR] Falló la carga de Bootstrap desde CDN');
                alert('Error: no se pudo cargar Bootstrap. Algunas funcionalidades estarán limitadas.');
            };
            document.head.appendChild(script);
        } else {
            console.log('[DEBUG] Bootstrap ya estaba disponible');
            this._initComponents();
        }
    },

    /**
     * Inicializa toggle de vistas y modal de reserva.
     */
    _initComponents() {
        console.log('[DEBUG] Inicializando componentes de CopierList');
        this._initViewToggle();
        this._initReserveModal();
    },

    /**
     * Toggle entre vista Lista y Kanban.
     */
    _initViewToggle() {
        console.log('[DEBUG] Configurando toggle de vistas');
        const btnList   = this.el.querySelector('#btn-list-view');
        const btnKanban = this.el.querySelector('#btn-kanban-view');
        const listView  = this.el.querySelector('#list-view');
        const kanbanView= this.el.querySelector('#kanban-view');

        if (!btnList || !btnKanban) {
            console.error('[ERROR] Botones de vista no encontrados');
            return;
        }

        btnList.addEventListener('click', () => {
            console.log('[DEBUG] Cambiando a vista LISTA');
            listView.style.display   = 'block';
            kanbanView.style.display = 'none';
            btnList.classList.add('active');
            btnKanban.classList.remove('active');
            localStorage.setItem('copierViewPreference', 'list');
        });

        btnKanban.addEventListener('click', () => {
            console.log('[DEBUG] Cambiando a vista KANBAN');
            listView.style.display   = 'none';
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
    },

    /**
     * Inicializa el modal de reserva, con logs en cada paso.
     */
    _initReserveModal() {
        try {
            console.log('[DEBUG] Inicializando modal de reserva');
            const modalEl     = this.el.querySelector('#reserveModal');
            const reserveBtns = this.el.querySelectorAll('.reserve-btn');
            const reserveForm = this.el.querySelector('#reserveForm');

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
            console.error('[ERROR] Excepción en _initReserveModal:', err);
            alert('Error: no se pudo inicializar el modal de reserva. Recarga la página, por favor.');
        }
    },
});