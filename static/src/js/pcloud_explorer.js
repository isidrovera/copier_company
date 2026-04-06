/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Iconos SVG por tipo de archivo ──────────────────────────────────────────

const FILE_ICONS = {
    // Documentos
    pdf:  { icon: "📄", color: "#e53935", bg: "#ffebee" },
    doc:  { icon: "📝", color: "#1565c0", bg: "#e3f2fd" },
    docx: { icon: "📝", color: "#1565c0", bg: "#e3f2fd" },
    xls:  { icon: "📊", color: "#2e7d32", bg: "#e8f5e9" },
    xlsx: { icon: "📊", color: "#2e7d32", bg: "#e8f5e9" },
    xlsm: { icon: "📊", color: "#2e7d32", bg: "#e8f5e9" },
    csv:  { icon: "📊", color: "#388e3c", bg: "#e8f5e9" },
    ppt:  { icon: "📋", color: "#e65100", bg: "#fff3e0" },
    pptx: { icon: "📋", color: "#e65100", bg: "#fff3e0" },
    txt:  { icon: "📃", color: "#546e7a", bg: "#eceff1" },
    // Imágenes
    jpg:  { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    jpeg: { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    png:  { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    gif:  { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    webp: { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    svg:  { icon: "🖼️", color: "#6a1b9a", bg: "#f3e5f5" },
    // Comprimidos
    zip:  { icon: "🗜️", color: "#f57f17", bg: "#fffde7" },
    rar:  { icon: "🗜️", color: "#f57f17", bg: "#fffde7" },
    tar:  { icon: "🗜️", color: "#f57f17", bg: "#fffde7" },
    gz:   { icon: "🗜️", color: "#f57f17", bg: "#fffde7" },
    "7z": { icon: "🗜️", color: "#f57f17", bg: "#fffde7" },
    // Video
    mp4:  { icon: "🎬", color: "#c62828", bg: "#ffebee" },
    avi:  { icon: "🎬", color: "#c62828", bg: "#ffebee" },
    mov:  { icon: "🎬", color: "#c62828", bg: "#ffebee" },
    mkv:  { icon: "🎬", color: "#c62828", bg: "#ffebee" },
    // Audio
    mp3:  { icon: "🎵", color: "#4527a0", bg: "#ede7f6" },
    wav:  { icon: "🎵", color: "#4527a0", bg: "#ede7f6" },
    flac: { icon: "🎵", color: "#4527a0", bg: "#ede7f6" },
    // Ejecutables
    exe:  { icon: "⚙️", color: "#37474f", bg: "#eceff1" },
    msi:  { icon: "⚙️", color: "#37474f", bg: "#eceff1" },
    dmg:  { icon: "⚙️", color: "#37474f", bg: "#eceff1" },
    // Código
    js:   { icon: "💻", color: "#f9a825", bg: "#fffde7" },
    py:   { icon: "💻", color: "#1565c0", bg: "#e3f2fd" },
    php:  { icon: "💻", color: "#6a1b9a", bg: "#f3e5f5" },
    html: { icon: "💻", color: "#e65100", bg: "#fff3e0" },
    css:  { icon: "💻", color: "#0277bd", bg: "#e1f5fe" },
    json: { icon: "💻", color: "#37474f", bg: "#eceff1" },
    xml:  { icon: "💻", color: "#558b2f", bg: "#f1f8e9" },
    // Firmware / binarios
    bin:  { icon: "💾", color: "#263238", bg: "#eceff1" },
    rom:  { icon: "💾", color: "#263238", bg: "#eceff1" },
    img:  { icon: "💾", color: "#263238", bg: "#eceff1" },
    iso:  { icon: "💾", color: "#263238", bg: "#eceff1" },
    hex:  { icon: "💾", color: "#263238", bg: "#eceff1" },
    fw:   { icon: "💾", color: "#263238", bg: "#eceff1" },
};

const FOLDER_COLORS = [
    "#f9a825", "#fb8c00", "#e65100", "#e53935",
    "#8e24aa", "#1565c0", "#00838f", "#2e7d32",
];

function getFolderColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash += name.charCodeAt(i);
    return FOLDER_COLORS[hash % FOLDER_COLORS.length];
}

function getFileInfo(name, isFolder) {
    if (isFolder) return { icon: "📁", color: getFolderColor(name), bg: "#fff8e1" };
    const ext = name.split(".").pop().toLowerCase();
    return FILE_ICONS[ext] || { icon: "📎", color: "#546e7a", bg: "#eceff1" };
}

function formatSize(bytes) {
    if (!bytes) return "";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes, i = 0;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return `${size.toFixed(1)} ${units[i]}`;
}

function formatDate(str) {
    if (!str) return "";
    try {
        // pCloud devuelve formato "Mon, 06 Apr 2026 15:30:56 +0000"
        return new Date(str).toLocaleDateString("es-PE", {
            day: "2-digit", month: "short", year: "numeric",
        });
    } catch { return str; }
}

// ─── Componente Principal ─────────────────────────────────────────────────────

class PCloudExplorer extends Component {
    static template = "copier_company.PCloudExplorer";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            // Navegación
            items: [],
            breadcrumbs: [{ id: "0", name: "Mi pCloud" }],
            currentFolderId: "0",
            loading: false,
            error: null,

            // Selección
            selectedIds: new Set(),

            // Vista
            viewMode: "grid",

            // Búsqueda
            searchQuery: "",

            // Modales
            modal: null,
            modalData: {},

            // Drag & drop
            dragItemId: null,
            dragOverId: null,

            // Context menu
            contextMenu: null,

            // Panel crear productos
            showCreatePanel: false,
            createPricePen: 100,
            createPriceUsd: 25,
            createResults: [],
            creatingProducts: false,
        });

        onWillStart(() => this._loadContents("0"));
    }

    // ─── Navegación ───────────────────────────────────────────────────────────

    async _loadContents(folderId) {
        console.log("[pCloud] Loading folder:", folderId);
        this.state.loading = true;
        this.state.error = null;
        this.state.selectedIds = new Set();
        this.state.showCreatePanel = false;
        this.state.createResults = [];
        try {
            const items = await this.orm.call(
                "pcloud.config", "pcloud_list_contents", [parseInt(folderId)]
            );
            console.log("[pCloud] Loaded", items.length, "items");
            this.state.items = items;
            this.state.currentFolderId = String(folderId);
        } catch (e) {
            const msg = e.data?.message || e.message || "Error al conectar con pCloud";
            console.error("[pCloud] Load error:", msg);
            this.state.error = msg;
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async onItemDblClick(item) {
        if (item.is_folder) {
            console.log("[pCloud] Navigate to:", item.name);
            this.state.breadcrumbs.push({ id: item.id, name: item.name });
            await this._loadContents(item.id);
        }
    }

    async onBreadcrumbClick(crumb, index) {
        this.state.breadcrumbs = this.state.breadcrumbs.slice(0, index + 1);
        await this._loadContents(crumb.id);
    }

    // ─── Selección ────────────────────────────────────────────────────────────

    onItemClick(item, ev) {
        if (ev.ctrlKey || ev.metaKey) {
            const ids = new Set(this.state.selectedIds);
            ids.has(item.id) ? ids.delete(item.id) : ids.add(item.id);
            this.state.selectedIds = ids;
        } else if (ev.shiftKey) {
            // Shift: seleccionar rango
            const all = this.filteredItems;
            const lastIdx = all.findIndex(i => i.id === [...this.state.selectedIds].pop());
            const currIdx = all.findIndex(i => i.id === item.id);
            if (lastIdx >= 0) {
                const [from, to] = [Math.min(lastIdx, currIdx), Math.max(lastIdx, currIdx)];
                const ids = new Set(this.state.selectedIds);
                all.slice(from, to + 1).forEach(i => ids.add(i.id));
                this.state.selectedIds = ids;
            } else {
                this.state.selectedIds = new Set([item.id]);
            }
        } else {
            this.state.selectedIds = new Set([item.id]);
        }

        // Mostrar/ocultar panel de crear productos si hay carpetas seleccionadas
        const selectedFolders = this.selectedFolderItems;
        this.state.showCreatePanel = selectedFolders.length > 0;
    }

    toggleSelectAll() {
        if (this.state.selectedIds.size === this.filteredItems.length) {
            this.state.selectedIds = new Set();
            this.state.showCreatePanel = false;
        } else {
            this.state.selectedIds = new Set(this.filteredItems.map(i => i.id));
            this.state.showCreatePanel = this.selectedFolderItems.length > 0;
        }
    }

    isSelected(item) {
        return this.state.selectedIds.has(item.id);
    }

    get selectedItems() {
        return this.state.items.filter(i => this.state.selectedIds.has(i.id));
    }

    get selectedFolderItems() {
        return this.selectedItems.filter(i => i.is_folder);
    }

    // ─── Modales ──────────────────────────────────────────────────────────────

    openModal(type, data = {}) {
        this.state.modal = type;
        this.state.modalData = { ...data };
    }

    closeModal() {
        this.state.modal = null;
        this.state.modalData = {};
    }

    // ─── Crear carpeta ────────────────────────────────────────────────────────

    openNewFolderModal() {
        this.openModal("newFolder", { name: "" });
    }

    async confirmNewFolder() {
        const name = this.state.modalData.name?.trim();
        if (!name) return;
        try {
            await this.orm.call("pcloud.config", "pcloud_create_folder", [
                name, parseInt(this.state.currentFolderId),
            ]);
            this.notification.add(`Carpeta "${name}" creada`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al crear carpeta", { type: "danger" });
        }
    }

    // ─── Renombrar ────────────────────────────────────────────────────────────

    openRenameModal(item) {
        this.openModal("rename", { item, newName: item.name });
    }

    async confirmRename() {
        const { item, newName } = this.state.modalData;
        if (!newName?.trim() || newName === item.name) { this.closeModal(); return; }
        try {
            await this.orm.call("pcloud.config", "pcloud_rename", [
                item.id, newName.trim(), item.is_folder,
            ]);
            this.notification.add(`Renombrado a "${newName}"`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al renombrar", { type: "danger" });
        }
    }

    // ─── Eliminar ─────────────────────────────────────────────────────────────

    async deleteSelected() {
        const items = this.selectedItems;
        if (!items.length) return;
        const label = items.length > 1 ? `${items.length} elementos` : `"${items[0].name}"`;
        if (!confirm(`¿Eliminar ${label}? Esta acción no se puede deshacer.`)) return;
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_delete", [item.id, item.is_folder]);
            }
            this.notification.add("Eliminado correctamente", { type: "success" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al eliminar", { type: "danger" });
        }
    }

    async onDeleteRowClick(item, ev) {
        this.onItemClick(item, ev);
        await this.deleteSelected();
    }

    // ─── Subir archivo ────────────────────────────────────────────────────────

    openUploadModal() {
        this.openModal("upload", { files: [] });
    }

    onFileInputChange(ev) {
        this.state.modalData.files = Array.from(ev.target.files);
    }

    async confirmUpload() {
        const files = this.state.modalData.files;
        if (!files?.length) return;
        this.state.modalData.uploading = true;
        let uploaded = 0;
        try {
            for (const file of files) {
                const b64 = await this._fileToBase64(file);
                await this.orm.call("pcloud.config", "pcloud_upload", [
                    file.name, b64, parseInt(this.state.currentFolderId),
                ]);
                uploaded++;
            }
            this.notification.add(`${uploaded} archivo(s) subido(s)`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al subir", { type: "danger" });
        } finally {
            this.state.modalData.uploading = false;
        }
    }

    _fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(",")[1]);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    // ─── Compartir ────────────────────────────────────────────────────────────

    async openShareModal(item) {
        if (!item.is_folder) return;
        this.openModal("share", { item, loading: true, link: null });
        try {
            const result = await this.orm.call("pcloud.config", "pcloud_get_share_link", [item.id]);
            this.state.modalData.link = result.link;
            this.state.modalData.code = result.code;
        } catch (e) {
            this.state.modalData.error = e.data?.message || "Error al obtener link";
        } finally {
            this.state.modalData.loading = false;
        }
    }

    copyShareLink() {
        const link = this.state.modalData.link;
        if (!link) return;
        navigator.clipboard.writeText(link).then(() => {
            this.notification.add("Link copiado", { type: "success" });
        });
    }

    async deleteShareLink() {
        try {
            await this.orm.call("pcloud.config", "pcloud_delete_share_link", [this.state.modalData.code]);
            this.notification.add("Link revocado", { type: "success" });
            this.closeModal();
        } catch (e) {
            this.notification.add(e.data?.message || "Error al revocar", { type: "danger" });
        }
    }

    // ─── Mover ────────────────────────────────────────────────────────────────

    openMoveModal() {
        if (!this.selectedItems.length) return;
        this.openModal("move", { items: this.selectedItems, targetFolderId: "" });
    }

    async confirmMove() {
        const { items, targetFolderId } = this.state.modalData;
        if (!targetFolderId) return;
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_move", [
                    item.id, targetFolderId, item.is_folder,
                ]);
            }
            this.notification.add("Movido correctamente", { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al mover", { type: "danger" });
        }
    }

    // ─── Descargar ────────────────────────────────────────────────────────────

    async downloadFile(item) {
        if (item.is_folder) return;
        try {
            const url = await this.orm.call("pcloud.config", "pcloud_get_file_download_url", [item.id]);
            window.open(url, "_blank");
        } catch (e) {
            this.notification.add(e.data?.message || "Error al descargar", { type: "danger" });
        }
    }

    // ─── Crear productos desde carpetas ───────────────────────────────────────

    toggleCreatePanel() {
        this.state.showCreatePanel = !this.state.showCreatePanel;
        this.state.createResults = [];
    }

    async confirmCreateProducts() {
        const folders = this.selectedFolderItems.map(i => ({ id: i.id, name: i.name }));
        if (!folders.length) {
            this.notification.add("Selecciona al menos una carpeta", { type: "warning" });
            return;
        }

        const pricePen = parseFloat(this.state.createPricePen) || 100;
        const priceUsd = parseFloat(this.state.createPriceUsd) || 25;

        console.log("[pCloud] Creating products for folders:", folders.length,
                    "PEN:", pricePen, "USD:", priceUsd);

        this.state.creatingProducts = true;
        this.state.createResults = [];

        try {
            const results = await this.orm.call(
                "pcloud.config",
                "pcloud_create_products_from_folders",
                [folders, pricePen, priceUsd],
            );

            console.log("[pCloud] Create products results:", results);
            this.state.createResults = results;

            const created = results.filter(r => r.status === "created").length;
            const existing = results.filter(r => r.status === "already_exists").length;
            const errors = results.filter(r => r.status === "error").length;

            if (created > 0) {
                this.notification.add(
                    `${created} producto(s) creado(s)${existing ? `, ${existing} ya existía(n)` : ""}`,
                    { type: "success" }
                );
            } else if (existing > 0 && errors === 0) {
                this.notification.add("Todos los productos ya existen", { type: "info" });
            }
            if (errors > 0) {
                this.notification.add(`${errors} error(es) al crear productos`, { type: "danger" });
            }

            // Recargar para actualizar indicadores "ya creado"
            await this._loadContents(this.state.currentFolderId);

        } catch (e) {
            const msg = e.data?.message || "Error al crear productos";
            console.error("[pCloud] Create products error:", msg);
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.creatingProducts = false;
        }
    }

    getCreateResultIcon(status) {
        const icons = {
            created: "✅",
            already_exists: "⚠️",
            error: "❌",
        };
        return icons[status] || "❓";
    }

    // ─── Drag & drop ──────────────────────────────────────────────────────────

    onDragStart(item, ev) {
        this.state.dragItemId = item.id;
        ev.dataTransfer.effectAllowed = "move";
    }

    onDragOver(item, ev) {
        if (!item.is_folder || item.id === this.state.dragItemId) return;
        ev.preventDefault();
        this.state.dragOverId = item.id;
    }

    onDragLeave() {
        this.state.dragOverId = null;
    }

    async onDrop(targetItem, ev) {
        ev.preventDefault();
        const dragId = this.state.dragItemId;
        this.state.dragItemId = null;
        this.state.dragOverId = null;
        if (!dragId || !targetItem.is_folder || dragId === targetItem.id) return;
        const dragged = this.state.items.find(i => i.id === dragId);
        if (!dragged) return;
        try {
            await this.orm.call("pcloud.config", "pcloud_move", [
                dragId, targetItem.id, dragged.is_folder,
            ]);
            this.notification.add(`"${dragged.name}" movido a "${targetItem.name}"`, { type: "success" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al mover", { type: "danger" });
        }
    }

    // ─── Context menu ─────────────────────────────────────────────────────────

    onContextMenu(item, ev) {
        ev.preventDefault();
        this.state.selectedIds = new Set([item.id]);
        this.state.contextMenu = { x: ev.clientX, y: ev.clientY, item };
    }

    closeContextMenu() {
        this.state.contextMenu = null;
    }

    // ─── Búsqueda ─────────────────────────────────────────────────────────────

    get filteredItems() {
        const q = this.state.searchQuery.toLowerCase().trim();
        if (!q) return this.state.items;
        return this.state.items.filter(i => i.name.toLowerCase().includes(q));
    }

    // ─── Helpers template ─────────────────────────────────────────────────────

    getFileInfo(item) {
        return getFileInfo(item.name, item.is_folder);
    }

    getFormattedSize(item) {
        return item.is_folder ? "" : formatSize(item.size);
    }

    getFormattedDate(item) {
        return formatDate(item.modified);
    }

    toggleViewMode() {
        this.state.viewMode = this.state.viewMode === "grid" ? "list" : "grid";
    }

    get allSelected() {
        return this.filteredItems.length > 0 &&
               this.state.selectedIds.size === this.filteredItems.length;
    }
}

registry.category("actions").add("pcloud_explorer_action", PCloudExplorer);