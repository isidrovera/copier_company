/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useRef } from "@odoo/owl";

/**
 * CopierList Component
 * 
 * Widget para gestionar vista de lista y kanban para copiadoras
 */
export class CopierList extends Component {
    setup() {
        this.state = useState({
            viewMode: 'list', // 'list' o 'kanban'
        });
        
        this.notificationService = useService("notification");
        this.rpc = useService("rpc");
        this.container = useRef("container");
        
        onMounted(() => {
            this._initialize();
        });
    }

    /**
     * Inicializa el componente
     */
    _initialize() {
        console.log('CopierList: Inicializando componente...');
        
        // Inicializar tooltips de Bootstrap
        const tooltipTriggerList = [].slice.call(this.container.el.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Restaurar vista preferida
        this._restorePreferredView();
    }

    /**
     * Cambia a vista de lista
     */
    _onClickListView() {
        console.log('CopierList: Cambiando a vista de lista');
        this.state.viewMode = 'list';
        localStorage.setItem('preferredView', 'list');
        
        // Actualizar UI directamente
        const btnListView = this.container.el.querySelector('#btn-list-view');
        const btnKanbanView = this.container.el.querySelector('#btn-kanban-view');
        const listView = this.container.el.querySelector('#list-view');
        const kanbanView = this.container.el.querySelector('#kanban-view');
        
        if (btnListView) btnListView.classList.add('active');
        if (btnKanbanView) btnKanbanView.classList.remove('active');
        if (listView) listView.style.display = 'block';
        if (kanbanView) kanbanView.style.display = 'none';
    }

    /**
     * Cambia a vista de kanban
     */
    _onClickKanbanView() {
        console.log('CopierList: Cambiando a vista de kanban');
        this.state.viewMode = 'kanban';
        localStorage.setItem('preferredView', 'kanban');
        
        // Actualizar UI directamente
        const btnListView = this.container.el.querySelector('#btn-list-view');
        const btnKanbanView = this.container.el.querySelector('#btn-kanban-view');
        const listView = this.container.el.querySelector('#list-view');
        const kanbanView = this.container.el.querySelector('#kanban-view');
        
        if (btnKanbanView) btnKanbanView.classList.add('active');
        if (btnListView) btnListView.classList.remove('active');
        if (kanbanView) kanbanView.style.display = 'block';
        if (listView) listView.style.display = 'none';
    }

    /**
     * Maneja el clic en el botón de reserva
     * @param {Event} ev Evento del click
     */
    _onClickReserve(ev) {
        ev.preventDefault();
        const machineId = ev.currentTarget.dataset.machineId;
        console.log(`CopierList: Reservando máquina ID ${machineId}`);
        
        const reserveForm = this.container.el.querySelector('#reserveForm');
        if (reserveForm) {
            reserveForm.setAttribute('action', `/stock-maquinas/${machineId}/reserve`);
        }
        
        // Mostrar modal usando Bootstrap
        const modal = this.container.el.querySelector('#reserveModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    /**
     * Maneja la entrada en el campo de búsqueda
     * @param {Event} ev Evento de input
     */
    _onInputSearch(ev) {
        clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(() => {
            const value = ev.target.value;
            console.log(`CopierList: Buscando "${value}"`);
            
            if (value.length >= 3 || value.length === 0) {
                const form = ev.target.closest('form');
                if (form) {
                    form.submit();
                }
            }
        }, 500);
    }

    /**
     * Restaura la vista preferida del usuario desde localStorage
     */
    _restorePreferredView() {
        const preferredView = localStorage.getItem('preferredView');
        console.log(`CopierList: Restaurando vista preferida: ${preferredView || 'ninguna'}`);
        
        if (preferredView === 'kanban') {
            this._onClickKanbanView();
        }
    }
}

CopierList.template = 'stock_maquinas.CopierList';
CopierList.props = {};

// Registrar el componente en el registro de componentes públicos
registry.category("public_components").add("CopierList", {
    Component: CopierList,
    selector: '.copier-list-container',
});

// Otro enfoque con publicWidget (para compatibilidad con código anterior)
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.CopierList = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click #btn-list-view': '_onClickListView',
        'click #btn-kanban-view': '_onClickKanbanView',
        'click .reserve-btn': '_onClickReserve',
        'input [name="search"]': '_onInputSearch',
    },

    start() {
        const def = this._super(...arguments);
        this._restorePreferredView();
        // inicializar tooltips de Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
        return def;
    },

    _onClickListView() {
        const btnListView = document.getElementById('btn-list-view');
        const btnKanbanView = document.getElementById('btn-kanban-view');
        const listView = document.getElementById('list-view');
        const kanbanView = document.getElementById('kanban-view');
        
        if (btnListView) btnListView.classList.add('active');
        if (btnKanbanView) btnKanbanView.classList.remove('active');
        if (listView) listView.style.display = 'block';
        if (kanbanView) kanbanView.style.display = 'none';
        
        localStorage.setItem('preferredView', 'list');
    },

    _onClickKanbanView() {
        const btnListView = document.getElementById('btn-list-view');
        const btnKanbanView = document.getElementById('btn-kanban-view');
        const listView = document.getElementById('list-view');
        const kanbanView = document.getElementById('kanban-view');
        
        if (btnKanbanView) btnKanbanView.classList.add('active');
        if (btnListView) btnListView.classList.remove('active');
        if (kanbanView) kanbanView.style.display = 'block';
        if (listView) listView.style.display = 'none';
        
        localStorage.setItem('preferredView', 'kanban');
    },

    _onClickReserve(ev) {
        ev.preventDefault();
        const machineId = ev.currentTarget.dataset.machineId;
        
        const reserveForm = document.getElementById('reserveForm');
        if (reserveForm) {
            reserveForm.setAttribute('action', `/stock-maquinas/${machineId}/reserve`);
        }
        
        const modal = document.getElementById('reserveModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    },

    _onInputSearch(ev) {
        clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(() => {
            const value = ev.target.value;
            
            if (value.length >= 3 || value.length === 0) {
                const form = ev.target.closest('form');
                if (form) {
                    form.submit();
                }
            }
        }, 500);
    },

    _restorePreferredView() {
        if (localStorage.getItem('preferredView') === 'kanban') {
            this._onClickKanbanView();
        }
    },
});

export default publicWidget.registry.CopierList;