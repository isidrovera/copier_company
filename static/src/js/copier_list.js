/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

/**
 * CopierList Component
 * Widget para gestionar vista de lista y kanban para copiadoras
 */
export class CopierList extends Component {
    static template = "copier_company.CopierList";

    setup() {
        // Estado interno: ‘list’ o ‘kanban’
        this.state = useState({ viewMode: "list" });

        // Servicios de Odoo
        this.notificationService = useService("notification");
        this.rpc                 = useService("rpc");

        // Referencia al contenedor raíz
        this.container = useRef("container");

        // Al montar, inicializamos tooltips y vista
        onMounted(() => this._initialize());
    }

    _initialize() {
        console.log("CopierList: Inicializando componente...");

        // Inicializar tooltips de Bootstrap
        const tooltipEls = Array.from(
            this.container.el.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipEls.forEach(el => new bootstrap.Tooltip(el));

        // Restaurar vista guardada en localStorage
        this._restorePreferredView();
    }

    _onClickListView() {
        console.log("CopierList: Cambiando a vista de lista");
        this.state.viewMode = "list";
        localStorage.setItem("preferredView", "list");

        const btnList   = this.container.el.querySelector("#btn-list-view");
        const btnKanban = this.container.el.querySelector("#btn-kanban-view");
        const listView  = this.container.el.querySelector("#list-view");
        const kanbanView= this.container.el.querySelector("#kanban-view");

        btnList?.classList.add("active");
        btnKanban?.classList.remove("active");
        if (listView)  listView.style.display = "block";
        if (kanbanView) kanbanView.style.display = "none";
    }

    _onClickKanbanView() {
        console.log("CopierList: Cambiando a vista de kanban");
        this.state.viewMode = "kanban";
        localStorage.setItem("preferredView", "kanban");

        const btnList   = this.container.el.querySelector("#btn-list-view");
        const btnKanban = this.container.el.querySelector("#btn-kanban-view");
        const listView  = this.container.el.querySelector("#list-view");
        const kanbanView= this.container.el.querySelector("#kanban-view");

        btnKanban?.classList.add("active");
        btnList?.classList.remove("active");
        if (kanbanView) kanbanView.style.display = "block";
        if (listView)  listView.style.display = "none";
    }

    _onClickReserve(ev) {
        ev.preventDefault();
        const machineId = ev.currentTarget.dataset.machineId;
        console.log(`CopierList: Reservando máquina ID ${machineId}`);

        const form = this.container.el.querySelector("#reserveForm");
        if (form) {
            form.setAttribute("action", `/stock-maquinas/${machineId}/reserve`);
        }

        const modalEl = this.container.el.querySelector("#reserveModal");
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    }

    _onInputSearch(ev) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            const value = ev.target.value;
            console.log(`CopierList: Buscando "${value}"`);
            if (value.length >= 3 || value.length === 0) {
                const form = ev.target.closest("form");
                form?.submit();
            }
        }, 500);
    }

    _restorePreferredView() {
        const preferred = localStorage.getItem("preferredView");
        console.log(`CopierList: Restaurando vista preferida: ${preferred || "ninguna"}`);
        if (preferred === "kanban") {
            this._onClickKanbanView();
        }
    }
}

// Registro del componente en el sistema de assets de Odoo 18
registry.category("public_components").add("stock_maquinas.CopierList", {
    Component: CopierList,
    selector: ".copier-list-container",
});
