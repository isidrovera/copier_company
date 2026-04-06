/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Utilidades ───────────────────────────────────────────────────────────────

function formatSize(bytes) {
    if (!bytes) return "";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes;
    let i = 0;
    while (size >= 1024 && i < units.length - 1) {
        size /= 1024;
        i++;
    }
    return `${size.toFixed(1)} ${units[i]}`;
}

function getFileIcon(name, isFolder) {
    if (isFolder) return "📁";
    const ext = name.split(".").pop().toLowerCase();
    const icons = {
        pdf: "📄", doc: "📝", docx: "📝",
        xls: "📊", xlsx: "📊", xlsm: "📊",
        ppt: "📋", pptx: "📋",
        jpg: "🖼️", jpeg: "🖼️", png: "🖼️", gif: "🖼️", webp: "🖼️",
        zip: "🗜️", rar: "🗜️", tar: "🗜️", gz: "🗜️",
        mp4: "🎬", avi: "🎬", mov: "🎬", mkv: "🎬",
        mp3: "🎵", wav: "🎵", flac: "🎵",
        exe: "⚙️", msi: "⚙️", dmg: "⚙️",
        txt: "📃", csv: "📃", json: "📃", xml: "📃",
        js: "💻", py: "💻", php: "💻", html: "💻", css: "💻",
    };
    return icons[ext] || "📎";
}

// ─── Componente principal ─────────────────────────────────────────────────────

class PCloudExplorer extends Component {
    static template = "copier_company.PCloudExplorer";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            items: [],
            breadcrumbs: [{ id: "0", name: "Mi pCloud" }],
            currentFolderId: "0",
            loading: false,
            error: null,
            selectedIds: new Set(),
            viewMode: "grid",
            modal: null,
            modalData: {},
            dragItemId: null,
            dragOverId: null,
            searchQuery: "",
            contextMenu: null,
        });

        onWillStart(() => this._loadContents("0"));
    }

    // ─── Navegación ───────────────────────────────────────────────────────────

    async _loadContents(folderId) {
        console.log("[pCloud] Loading folder:", folderId);
        this.state.loading = true;
        this.state.error = null;
        this.state.selectedIds = new Set();
        try {
            const items = await this.orm.call(
                "pcloud.config",
                "pcloud_list_contents",
                [parseInt(folderId)],
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
            console.log("[pCloud] Navigating to folder:", item.id, item.name);
            this.state.breadcrumbs.push({ id: item.id, name: item.name });
            await this._loadContents(item.id);
        }
    }

    async onBreadcrumbClick(crumb, index) {
        console.log("[pCloud] Breadcrumb click:", crumb.name);
        this.state.breadcrumbs = this.state.breadcrumbs.slice(0, index + 1);
        await this._loadContents(crumb.id);
    }

    // ─── Selección ────────────────────────────────────────────────────────────

    onItemClick(item, ev) {
        if (ev.ctrlKey || ev.metaKey) {
            const ids = new Set(this.state.selectedIds);
            if (ids.has(item.id)) {
                ids.delete(item.id);
            } else {
                ids.add(item.id);
            }
            this.state.selectedIds = ids;
        } else {
            this.state.selectedIds = new Set([item.id]);
        }
    }

    isSelected(item) {
        return this.state.selectedIds.has(item.id);
    }

    get selectedItems() {
        return this.state.items.filter((i) => this.state.selectedIds.has(i.id));
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
        console.log("[pCloud] Creating folder:", name);
        try {
            await this.orm.call("pcloud.config", "pcloud_create_folder", [
                name,
                parseInt(this.state.currentFolderId),
            ]);
            this.notification.add(`Carpeta "${name}" creada`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al crear carpeta";
            console.error("[pCloud] Create folder error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Renombrar ────────────────────────────────────────────────────────────

    openRenameModal(item) {
        this.openModal("rename", { item, newName: item.name });
    }

    async confirmRename() {
        const { item, newName } = this.state.modalData;
        if (!newName?.trim() || newName === item.name) {
            this.closeModal();
            return;
        }
        console.log("[pCloud] Renaming:", item.id, "->", newName);
        try {
            await this.orm.call("pcloud.config", "pcloud_rename", [
                item.id,
                newName.trim(),
                item.is_folder,
            ]);
            this.notification.add(`Renombrado a "${newName}"`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al renombrar";
            console.error("[pCloud] Rename error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Eliminar ─────────────────────────────────────────────────────────────

    async deleteSelected() {
        const items = this.selectedItems;
        if (!items.length) return;
        const label = items.length > 1
            ? `${items.length} elementos`
            : `"${items[0].name}"`;
        if (!confirm(`¿Eliminar ${label}? Esta acción no se puede deshacer.`)) return;
        console.log("[pCloud] Deleting:", items.map((i) => i.id));
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_delete", [
                    item.id,
                    item.is_folder,
                ]);
            }
            this.notification.add("Eliminado correctamente", { type: "success" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al eliminar";
            console.error("[pCloud] Delete error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // FIX: OWL no soporta async/await inline en t-on-click del template
    // Este método reemplaza el handler inline de la fila eliminar en vista lista
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
        console.log("[pCloud] Files selected:", this.state.modalData.files.length);
    }

    async confirmUpload() {
        const files = this.state.modalData.files;
        if (!files?.length) return;
        this.state.modalData.uploading = true;
        let uploaded = 0;
        console.log("[pCloud] Uploading", files.length, "files");
        try {
            for (const file of files) {
                console.log("[pCloud] Uploading:", file.name, file.size, "bytes");
                const b64 = await this._fileToBase64(file);
                await this.orm.call("pcloud.config", "pcloud_upload", [
                    file.name,
                    b64,
                    parseInt(this.state.currentFolderId),
                ]);
                uploaded++;
                console.log("[pCloud] Uploaded:", file.name);
            }
            this.notification.add(`${uploaded} archivo(s) subido(s)`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al subir";
            console.error("[pCloud] Upload error:", msg);
            this.notification.add(msg, { type: "danger" });
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
        console.log("[pCloud] Getting share link for:", item.id);
        this.openModal("share", { item, loading: true, link: null });
        try {
            const result = await this.orm.call(
                "pcloud.config",
                "pcloud_get_share_link",
                [item.id],
            );
            console.log("[pCloud] Share link:", result.link);
            this.state.modalData.link = result.link;
            this.state.modalData.code = result.code;
        } catch (e) {
            const msg = e.data?.message || "Error al obtener link";
            console.error("[pCloud] Share error:", msg);
            this.state.modalData.error = msg;
        } finally {
            this.state.modalData.loading = false;
        }
    }

    copyShareLink() {
        const link = this.state.modalData.link;
        if (!link) return;
        navigator.clipboard.writeText(link).then(() => {
            this.notification.add("Link copiado al portapapeles", { type: "success" });
        });
    }

    async deleteShareLink() {
        const code = this.state.modalData.code;
        if (!code) return;
        console.log("[pCloud] Revoking share link:", code);
        try {
            await this.orm.call("pcloud.config", "pcloud_delete_share_link", [code]);
            this.notification.add("Link público eliminado", { type: "success" });
            this.closeModal();
        } catch (e) {
            const msg = e.data?.message || "Error al eliminar link";
            console.error("[pCloud] Revoke share error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Mover ────────────────────────────────────────────────────────────────

    openMoveModal() {
        const items = this.selectedItems;
        if (!items.length) return;
        this.openModal("move", { items, targetFolderId: "" });
    }

    async confirmMove() {
        const { items, targetFolderId } = this.state.modalData;
        if (!targetFolderId) return;
        console.log("[pCloud] Moving", items.length, "items to:", targetFolderId);
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_move", [
                    item.id,
                    targetFolderId,
                    item.is_folder,
                ]);
            }
            this.notification.add("Movido correctamente", { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al mover";
            console.error("[pCloud] Move error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Descargar ────────────────────────────────────────────────────────────

    async downloadFile(item) {
        if (item.is_folder) return;
        console.log("[pCloud] Getting download URL for:", item.id);
        try {
            const url = await this.orm.call(
                "pcloud.config",
                "pcloud_get_file_download_url",
                [item.id],
            );
            console.log("[pCloud] Download URL obtained");
            window.open(url, "_blank");
        } catch (e) {
            const msg = e.data?.message || "Error al descargar";
            console.error("[pCloud] Download error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Drag & drop ──────────────────────────────────────────────────────────

    onDragStart(item, ev) {
        this.state.dragItemId = item.id;
        ev.dataTransfer.effectAllowed = "move";
        console.log("[pCloud] Drag start:", item.name);
    }

    onDragOver(item, ev) {
        if (!item.is_folder || item.id === this.state.dragItemId) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
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
        const draggedItem = this.state.items.find((i) => i.id === dragId);
        if (!draggedItem) return;
        console.log("[pCloud] Drop:", draggedItem.name, "->", targetItem.name);
        try {
            await this.orm.call("pcloud.config", "pcloud_move", [
                dragId,
                targetItem.id,
                draggedItem.is_folder,
            ]);
            this.notification.add(
                `"${draggedItem.name}" movido a "${targetItem.name}"`,
                { type: "success" },
            );
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            const msg = e.data?.message || "Error al mover";
            console.error("[pCloud] Drop error:", msg);
            this.notification.add(msg, { type: "danger" });
        }
    }

    // ─── Búsqueda ─────────────────────────────────────────────────────────────

    get filteredItems() {
        const q = this.state.searchQuery.toLowerCase().trim();
        if (!q) return this.state.items;
        return this.state.items.filter((i) => i.name.toLowerCase().includes(q));
    }

    // ─── Helpers ──────────────────────────────────────────────────────────────

    getIcon(item) {
        return getFileIcon(item.name, item.is_folder);
    }

    getFormattedSize(item) {
        return item.is_folder ? "" : formatSize(item.size);
    }

    toggleViewMode() {
        this.state.viewMode = this.state.viewMode === "grid" ? "list" : "grid";
        console.log("[pCloud] View mode:", this.state.viewMode);
    }

    onContextMenu(item, ev) {
        ev.preventDefault();
        this.state.selectedIds = new Set([item.id]);
        this.state.contextMenu = { x: ev.clientX, y: ev.clientY, item };
    }

    closeContextMenu() {
        this.state.contextMenu = null;
    }
}

registry.category("actions").add("pcloud_explorer_action", PCloudExplorer);