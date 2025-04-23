/** @odoo-module **/
import publicWidget from 'web.public.widget';

publicWidget.registry.CopierList = publicWidget.Widget.extend({
    selector: '.copier-list-container',

    events: {
        'click #btn-list-view': '_onClickList',
        'click #btn-kanban-view': '_onClickKanban',
    },

    start() {
        this._super(...arguments);
        console.log('[DEBUG] OWL widget CopierList arrancado');

        // Restaurar vista previa
        this._restoreViewPreference();

        // Inicializar modal de reserva (si Bootstrap está cargado)
        if (typeof bootstrap !== 'undefined') {
            this._initReserveModal();
        } else {
            console.warn('[WARN] bootstrap no presente → modal deshabilitado');
        }
    },

    // ————————————————————————————————————————————————————————————
    // Toggle de vistas
    // ————————————————————————————————————————————————————————————
    _onClickList()   { this._toggleView('list'); },
    _onClickKanban() { this._toggleView('kanban'); },

    _toggleView(mode) {
        console.log('[DEBUG] Cambiando a vista', mode);
        const btnList   = this.el.querySelector('#btn-list-view');
        const btnKanban = this.el.querySelector('#btn-kanban-view');
        const listView  = this.el.querySelector('#list-view');
        const kanbanView= this.el.querySelector('#kanban-view');

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
    },

    _restoreViewPreference() {
        const saved = localStorage.getItem('copierViewPreference') || 'list';
        console.log('[DEBUG] Preferencia previa:', saved);
        this._toggleView(saved);
    },

    // ————————————————————————————————————————————————————————————
    // Modal de reserva (depende de Bootstrap)
    // ————————————————————————————————————————————————————————————
    _initReserveModal() {
        console.log('[DEBUG] Inicializando modal de reserva');
        const modalEl     = this.el.querySelector('#reserveModal');
        const reserveBtns = this.el.querySelectorAll('.reserve-btn');
        const reserveForm = this.el.querySelector('#reserveForm');

        if (!modalEl || !reserveForm) {
            console.error('[ERROR] Falta #reserveModal o #reserveForm en el DOM');
            return;
        }

        this.reserveModal = new bootstrap.Modal(modalEl);
        reserveBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.machineId;
                console.log('[DEBUG] Reserva solicitada máquina ID:', id);
                reserveForm.action = `/stock-maquinas/${id}/reserve`;
                this.reserveModal.show();
            });
        });
        console.log(
            `[DEBUG] Listeners de reserva registrados en ${reserveBtns.length} botones`
        );
    },
});
