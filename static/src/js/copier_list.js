/** @odoo-module **/
odoo.define('copier_company.copier_list', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.CopierList = publicWidget.Widget.extend({
        selector: '.copier-list-container',

        /**
         * @override
         */
        start: function () {
            this._super.apply(this, arguments);
            console.log('[DEBUG] Iniciando CopierList OWL widget');

            // Restaura la vista previa (list o kanban)
            this._restoreViewPreference();

            // Inicializa el modal sólo si bootstrap está disponible
            if (window.bootstrap) {
                this._initReserveModal();
            }
        },

        // =========================================================================
        // Toggle de vistas
        // =========================================================================
        events: {
            'click #btn-list-view': '_onClickList',
            'click #btn-kanban-view': '_onClickKanban',
        },

        _onClickList: function () {
            this._toggleView('list');
        },
        _onClickKanban: function () {
            this._toggleView('kanban');
        },

        _toggleView: function (mode) {
            const btnList    = this.el.querySelector('#btn-list-view');
            const btnKanban  = this.el.querySelector('#btn-kanban-view');
            const listView   = this.el.querySelector('#list-view');
            const kanbanView = this.el.querySelector('#kanban-view');

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
        },

        _restoreViewPreference: function () {
            const saved = localStorage.getItem('copierViewPreference') || 'list';
            console.log('[DEBUG] Preferencia cargada:', saved);
            this._toggleView(saved);
        },

        // =========================================================================
        // Modal de reserva (depende de bootstrap)
        // =========================================================================
        _initReserveModal: function () {
            try {
                console.log('[DEBUG] Inicializando modal de reserva');

                const modalEl     = this.el.querySelector('#reserveModal');
                const reserveBtns = this.el.querySelectorAll('.reserve-btn');
                const reserveForm = this.el.querySelector('#reserveForm');

                if (!modalEl) {
                    console.warn('[WARN] #reserveModal no encontrado');
                    return;
                }

                this.reserveModal = new bootstrap.Modal(modalEl);
                console.log('[DEBUG] bootstrap.Modal inicializado');

                reserveBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = btn.dataset.machineId;
                        console.log('[DEBUG] Reserva solicitada máquina ID:', id);
                        reserveForm.action = `/stock-maquinas/${id}/reserve`;
                        this.reserveModal.show();
                    });
                });

                console.log(
                    `[DEBUG] Event listeners de reserva configurados en ${reserveBtns.length} botones`
                );
            } catch (err) {
                console.error('[ERROR] Excepción en _initReserveModal:', err);
            }
        },
    });
});
