odoo.define('copier_company.copier_list', function(require) {
    'use strict';
    console.log('[DEBUG] cargando módulo copier_company.copier_list');

    const publicWidget = require('web.public.widget');

    publicWidget.registry.CopierList = publicWidget.Widget.extend({
        selector: '.copier-list-container',

        /**
         * Se ejecuta cuando OWL monta el contenedor
         */
        start: function () {
            this._super.apply(this, arguments);
            console.log('[DEBUG] OWL Widget CopiersList montado');
            this._checkBootstrapAndInit();
        },

        /**
         * Verifica si Bootstrap está disponible o realiza carga dinámica
         */
        _checkBootstrapAndInit: function () {
            console.log('[DEBUG] Verificando existencia de Bootstrap');
            if (typeof bootstrap === 'undefined') {
                console.warn('[ERROR] Bootstrap JS no está cargado. Cargando desde CDN...');
                const bootstrapScript = document.createElement('script');
                bootstrapScript.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js';
                bootstrapScript.integrity = 'sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq';
                bootstrapScript.crossOrigin = 'anonymous';
                bootstrapScript.onload = () => {
                    console.log('[DEBUG] Bootstrap cargado exitosamente desde CDN');
                    this._initComponents();
                };
                bootstrapScript.onerror = () => {
                    console.error('[ERROR] No se pudo cargar Bootstrap desde CDN.');
                    alert('Error: No se pudo cargar Bootstrap. Algunas funcionalidades estarán limitadas.');
                };
                document.head.appendChild(bootstrapScript);
            } else {
                console.log('[DEBUG] Bootstrap ya está cargado');
                this._initComponents();
            }
        },

        /**
         * Inicializa toda la lógica: toggle de vistas y modal de reserva
         */
        _initComponents: function () {
            console.log('[DEBUG] Inicializando componentes de la lista de copiadoras');
            this._initViewToggle();
            this._initReserveModal();
        },

        /**
         * Configuración de cambio entre vista Lista y Kanban
         */
        _initViewToggle: function () {
            console.log('[DEBUG] Configurando toggle de vistas');
            const btnList   = this.el.querySelector('#btn-list-view');
            const btnKanban = this.el.querySelector('#btn-kanban-view');
            const listView  = this.el.querySelector('#list-view');
            const kanbanView= this.el.querySelector('#kanban-view');

            if (!btnList || !btnKanban) {
                console.error('[ERROR] No se encontraron los botones de vista');
                return;
            }

            btnList.addEventListener('click', () => {
                console.log('[DEBUG] Cambiando a vista Lista');
                listView.style.display   = 'block';
                kanbanView.style.display = 'none';
                btnList.classList.add('active');
                btnKanban.classList.remove('active');
                localStorage.setItem('copierViewPreference', 'list');
            });

            btnKanban.addEventListener('click', () => {
                console.log('[DEBUG] Cambiando a vista Kanban');
                listView.style.display   = 'none';
                kanbanView.style.display = 'block';
                btnKanban.classList.add('active');
                btnList.classList.remove('active');
                localStorage.setItem('copierViewPreference', 'kanban');
            });

            const saved = localStorage.getItem('copierViewPreference');
            console.log('[DEBUG] Preferencia guardada:', saved);
            if (saved === 'kanban') {
                console.log('[DEBUG] Aplicando preferencia: Kanban');
                btnKanban.click();
            }
        },

        /**
         * Inicializa el modal de reserva con logs detallados
         */
        _initReserveModal: function () {
            try {
                console.log('[DEBUG] Inicializando modal de reserva');
                const modalEl     = this.el.querySelector('#reserveModal');
                const reserveBtns = this.el.querySelectorAll('.reserve-btn');
                const reserveForm = this.el.querySelector('#reserveForm');

                if (!modalEl) {
                    console.error('[ERROR] No se encontró el elemento modal');
                    return;
                }
                if (!reserveBtns.length) {
                    console.warn('[WARN] No se encontraron botones de reserva');
                }
                if (!reserveForm) {
                    console.error('[ERROR] No se encontró el formulario de reserva');
                    return;
                }

                const reserveModal = new bootstrap.Modal(modalEl);
                console.log('[DEBUG] Modal de reserva inicializado');

                reserveBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = btn.dataset.machineId;
                        console.log('[DEBUG] Reserva solicitada para máquina ID:', id);
                        reserveForm.action = `/stock-maquinas/${id}/reserve`;
                        reserveModal.show();
                    });
                });
                console.log('[DEBUG] Eventos de reserva configurados en', reserveBtns.length, 'botones');

            } catch (error) {
                console.error('[ERROR] Error al inicializar modal de reserva:', error);
                alert('Error: No se pudo inicializar el modal de reserva. Por favor, recarga la página.');
            }
        },
    });
});
