// stock_maquinas/static/src/js/copier_list.js

odoo.define('stock_maquinas.copier_list', function (require) {
    'use strict';
    
    // Importaciones necesarias para Odoo 18
    const publicWidget = require('web.public.widget');
    
    publicWidget.registry.CopierList = publicWidget.Widget.extend({
        selector: '.container',
        events: {
            'click #btn-list-view': '_onClickListView',
            'click #btn-kanban-view': '_onClickKanbanView',
            'click .reserve-btn': '_onClickReserve',
            'input [name="search"]': '_onInputSearch',
        },
        
        /**
         * @override
         */
        start: function () {
            const def = this._super.apply(this, arguments);
            
            // Restaurar la vista preferida del usuario
            this._restorePreferredView();
            
            // Inicializar tooltips para botones pequeños
            $('[data-bs-toggle="tooltip"]').tooltip();
            
            return def;
        },
        
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
        
        /**
         * Cambia a vista lista
         * @private
         * @param {Event} ev
         */
        _onClickListView: function (ev) {
            $('#btn-list-view').addClass('active');
            $('#btn-kanban-view').removeClass('active');
            $('#list-view').show();
            $('#kanban-view').hide();
            localStorage.setItem('preferredView', 'list');
        },
        
        /**
         * Cambia a vista kanban
         * @private
         * @param {Event} ev
         */
        _onClickKanbanView: function (ev) {
            $('#btn-kanban-view').addClass('active');
            $('#btn-list-view').removeClass('active');
            $('#kanban-view').show();
            $('#list-view').hide();
            localStorage.setItem('preferredView', 'kanban');
        },
        
        /**
         * Maneja el clic en el botón reservar
         * @private
         * @param {Event} ev
         */
        _onClickReserve: function (ev) {
            ev.preventDefault();
            const machineId = $(ev.currentTarget).data('machine-id');
            $('#reserveForm').attr('action', `/stock-maquinas/${machineId}/reserve`);
            
            // Usar el modal de Bootstrap para confirmar
            var reserveModal = new bootstrap.Modal(document.getElementById('reserveModal'));
            reserveModal.show();
        },
        
        /**
         * Implementa búsqueda automática al escribir
         * @private
         * @param {Event} ev
         */
        _onInputSearch: function (ev) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                // Solo enviar si hay al menos 3 caracteres o está vacío
                if (ev.target.value.length >= 3 || ev.target.value.length === 0) {
                    $(ev.target).closest('form').submit();
                }
            }, 500);
        },
        
        /**
         * Restaura la vista preferida del usuario
         * @private
         */
        _restorePreferredView: function () {
            const preferredView = localStorage.getItem('preferredView');
            if (preferredView === 'kanban') {
                $('#btn-kanban-view').click();
            }
        },
    });
    
    return publicWidget.registry.CopierList;
});