/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

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
        $('[data-bs-toggle="tooltip"]').tooltip();
        return def;
    },

    _onClickListView() {
        $('#btn-list-view').addClass('active');
        $('#btn-kanban-view').removeClass('active');
        $('#list-view').show();
        $('#kanban-view').hide();
        localStorage.setItem('preferredView', 'list');
    },

    _onClickKanbanView() {
        $('#btn-kanban-view').addClass('active');
        $('#btn-list-view').removeClass('active');
        $('#kanban-view').show();
        $('#list-view').hide();
        localStorage.setItem('preferredView', 'kanban');
    },

    _onClickReserve(ev) {
        ev.preventDefault();
        const machineId = $(ev.currentTarget).data('machine-id');
        $('#reserveForm').attr('action', `/stock-maquinas/${machineId}/reserve`);
        new bootstrap.Modal(document.getElementById('reserveModal')).show();
    },

    _onInputSearch(ev) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            const v = ev.target.value;
            if (v.length >= 3 || v.length === 0) {
                $(ev.target).closest('form').submit();
            }
        }, 500);
    },

    _restorePreferredView() {
        if (localStorage.getItem('preferredView') === 'kanban') {
            $('#btn-kanban-view').click();
        }
    },
});

export default publicWidget.registry.CopierList;
