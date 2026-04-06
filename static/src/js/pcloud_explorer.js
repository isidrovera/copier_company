/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Bootstrap Icons (bi-*) + colores por extensión ──────────────────────────
// Requiere: bootstrap-icons CSS cargado (se inyecta automáticamente abajo)

const FILE_TYPES = {
    // ── Documentos Office ──
    pdf:  { icon: "bi-file-earmark-pdf-fill",   color: "#dc2626", bg: "#fef2f2", label: "PDF",  previewable: true  },
    doc:  { icon: "bi-file-earmark-word-fill",   color: "#1d4ed8", bg: "#eff6ff", label: "DOC",  previewable: false },
    docx: { icon: "bi-file-earmark-word-fill",   color: "#1d4ed8", bg: "#eff6ff", label: "DOCX", previewable: false },
    xls:  { icon: "bi-file-earmark-excel-fill",  color: "#16a34a", bg: "#f0fdf4", label: "XLS",  previewable: false },
    xlsx: { icon: "bi-file-earmark-excel-fill",  color: "#16a34a", bg: "#f0fdf4", label: "XLSX", previewable: false },
    xlsm: { icon: "bi-file-earmark-excel-fill",  color: "#16a34a", bg: "#f0fdf4", label: "XLSM", previewable: false },
    csv:  { icon: "bi-filetype-csv",             color: "#15803d", bg: "#f0fdf4", label: "CSV",  previewable: false },
    ppt:  { icon: "bi-file-earmark-ppt-fill",    color: "#ea580c", bg: "#fff7ed", label: "PPT",  previewable: false },
    pptx: { icon: "bi-file-earmark-ppt-fill",    color: "#ea580c", bg: "#fff7ed", label: "PPTX", previewable: false },
    txt:  { icon: "bi-file-earmark-text",        color: "#475569", bg: "#f8fafc", label: "TXT",  previewable: false },
    // ── Imágenes ──
    jpg:  { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "JPG",  previewable: true  },
    jpeg: { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "JPEG", previewable: true  },
    png:  { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "PNG",  previewable: true  },
    gif:  { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "GIF",  previewable: true  },
    webp: { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "WEBP", previewable: true  },
    svg:  { icon: "bi-filetype-svg",             color: "#7c3aed", bg: "#f5f3ff", label: "SVG",  previewable: true  },
    bmp:  { icon: "bi-file-earmark-image-fill",  color: "#7c3aed", bg: "#f5f3ff", label: "BMP",  previewable: true  },
    // ── Comprimidos ──
    zip:  { icon: "bi-file-earmark-zip-fill",    color: "#b45309", bg: "#fffbeb", label: "ZIP",  previewable: false },
    rar:  { icon: "bi-file-earmark-zip-fill",    color: "#b45309", bg: "#fffbeb", label: "RAR",  previewable: false },
    "7z": { icon: "bi-file-earmark-zip-fill",    color: "#b45309", bg: "#fffbeb", label: "7Z",   previewable: false },
    tar:  { icon: "bi-file-earmark-zip-fill",    color: "#b45309", bg: "#fffbeb", label: "TAR",  previewable: false },
    gz:   { icon: "bi-file-earmark-zip-fill",    color: "#b45309", bg: "#fffbeb", label: "GZ",   previewable: false },
    // ── Video ──
    mp4:  { icon: "bi-file-earmark-play-fill",   color: "#be123c", bg: "#fff1f2", label: "MP4",  previewable: true  },
    webm: { icon: "bi-file-earmark-play-fill",   color: "#be123c", bg: "#fff1f2", label: "WEBM", previewable: true  },
    avi:  { icon: "bi-file-earmark-play-fill",   color: "#be123c", bg: "#fff1f2", label: "AVI",  previewable: false },
    mov:  { icon: "bi-file-earmark-play-fill",   color: "#be123c", bg: "#fff1f2", label: "MOV",  previewable: false },
    mkv:  { icon: "bi-file-earmark-play-fill",   color: "#be123c", bg: "#fff1f2", label: "MKV",  previewable: false },
    // ── Audio ──
    mp3:  { icon: "bi-file-earmark-music-fill",  color: "#6d28d9", bg: "#f5f3ff", label: "MP3",  previewable: true  },
    wav:  { icon: "bi-file-earmark-music-fill",  color: "#6d28d9", bg: "#f5f3ff", label: "WAV",  previewable: true  },
    ogg:  { icon: "bi-file-earmark-music-fill",  color: "#6d28d9", bg: "#f5f3ff", label: "OGG",  previewable: true  },
    flac: { icon: "bi-file-earmark-music-fill",  color: "#6d28d9", bg: "#f5f3ff", label: "FLAC", previewable: false },
    // ── Código ──
    js:   { icon: "bi-filetype-js",              color: "#ca8a04", bg: "#fefce8", label: "JS",   previewable: false },
    ts:   { icon: "bi-filetype-tsx",             color: "#2563eb", bg: "#eff6ff", label: "TS",   previewable: false },
    py:   { icon: "bi-filetype-py",              color: "#2563eb", bg: "#eff6ff", label: "PY",   previewable: false },
    php:  { icon: "bi-filetype-php",             color: "#7e22ce", bg: "#faf5ff", label: "PHP",  previewable: false },
    html: { icon: "bi-filetype-html",            color: "#c2410c", bg: "#fff7ed", label: "HTML", previewable: false },
    css:  { icon: "bi-filetype-css",             color: "#0369a1", bg: "#f0f9ff", label: "CSS",  previewable: false },
    json: { icon: "bi-filetype-json",            color: "#374151", bg: "#f9fafb", label: "JSON", previewable: false },
    xml:  { icon: "bi-filetype-xml",             color: "#166534", bg: "#f0fdf4", label: "XML",  previewable: false },
    sql:  { icon: "bi-filetype-sql",             color: "#1e40af", bg: "#eff6ff", label: "SQL",  previewable: false },
    // ── Binarios / Firmware ──
    bin:  { icon: "bi-file-earmark-binary-fill", color: "#1f2937", bg: "#f3f4f6", label: "BIN",  previewable: false },
    hex:  { icon: "bi-file-earmark-binary-fill", color: "#1f2937", bg: "#f3f4f6", label: "HEX",  previewable: false },
    fw:   { icon: "bi-cpu-fill",                 color: "#374151", bg: "#f3f4f6", label: "FW",   previewable: false },
    iso:  { icon: "bi-disc-fill",                color: "#374151", bg: "#f3f4f6", label: "ISO",  previewable: false },
    img:  { icon: "bi-hdd-fill",                 color: "#374151", bg: "#f3f4f6", label: "IMG",  previewable: false },
    // ── Ejecutables ──
    exe:  { icon: "bi-gear-fill",                color: "#374151", bg: "#f3f4f6", label: "EXE",  previewable: false },
    msi:  { icon: "bi-gear-fill",                color: "#374151", bg: "#f3f4f6", label: "MSI",  previewable: false },
};

// Colores de carpeta por hash del nombre
const FOLDER_COLORS = [
    { color: "#f59e0b", bg: "#fffbeb" },
    { color: "#f97316", bg: "#fff7ed" },
    { color: "#ef4444", bg: "#fef2f2" },
    { color: "#ec4899", bg: "#fdf2f8" },
    { color: "#8b5cf6", bg: "#f5f3ff" },
    { color: "#3b82f6", bg: "#eff6ff" },
    { color: "#06b6d4", bg: "#ecfeff" },
    { color: "#10b981", bg: "#ecfdf5" },
];

function getFolderStyle(name) {
    let h = 0;
    for (let i = 0; i < name.length; i++) h += name.charCodeAt(i);
    return FOLDER_COLORS[h % FOLDER_COLORS.length];
}

function getFileType(name, isFolder) {
    if (isFolder) {
        const style = getFolderStyle(name);
        return {
            icon: "bi-folder-fill",
            color: style.color,
            bg: style.bg,
            label: "DIR",
            previewable: false,
        };
    }
    const ext = name.split(".").pop().toLowerCase();
    return FILE_TYPES[ext] || {
        icon: "bi-file-earmark-fill",
        color: "#64748b",
        bg: "#f8fafc",
        label: (ext.toUpperCase().slice(0, 5) || "FILE"),
        previewable: false,
    };
}

function formatSize(bytes) {
    if (!bytes) return "";
    const u = ["B", "KB", "MB", "GB", "TB"];
    let s = bytes, i = 0;
    while (s >= 1024 && i < u.length - 1) { s /= 1024; i++; }
    return `${s.toFixed(1)} ${u[i]}`;
}

function formatDate(str) {
    if (!str) return "";
    try {
        return new Date(str).toLocaleDateString("es-PE", {
            day: "2-digit", month: "short", year: "numeric",
        });
    } catch { return str; }
}

// Inyectar Bootstrap Icons CSS una sola vez
(function injectBootstrapIcons() {
    if (document.getElementById("pce-bi-css")) return;
    const link = document.createElement("link");
    link.id   = "pce-bi-css";
    link.rel  = "stylesheet";
    link.href = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css";
    document.head.appendChild(link);
})();

// ─── Componente Principal ─────────────────────────────────────────────────────

class PCloudExplorer extends Component {
    static template = "copier_company.PCloudExplorer";

    setup() {
        this.orm          = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            items:           [],
            breadcrumbs:     [{ id: "0", name: "Mi pCloud" }],
            currentFolderId: "0",
            loading:         false,
            error:           null,

            selectedIds: new Set(),
            viewMode:    "grid",
            searchQuery: "",

            modal:     null,
            modalData: {},

            dragItemId: null,
            dragOverId: null,

            contextMenu: null,

            showCreatePanel:  false,
            createPricePen:   100,
            createPriceUsd:   25,
            createResults:    [],
            creatingProducts: false,

            previewItem:    null,
            previewUrl:     null,
            previewLoading: false,

            // ── Modal de confirmación personalizado ──────────────────
            confirmModal: null,
            // confirmModal = {
            //   title:      string,
            //   message:    string,
            //   variant:    "danger" | "warning" | "info",
            //   icon:       string (clase bi-*),
            //   confirmLabel: string,
            //   cancelLabel:  string,
            //   resolve:    Function,   // interna
            // }
        });

        onWillStart(() => this._loadContents("0"));
    }

    // ─── Modal de confirmación genérico ──────────────────────────────────────
    /**
     * Muestra un modal de confirmación elegante.
     * @param {Object} opts
     * @param {string} opts.title          - Título del modal
     * @param {string} opts.message        - Cuerpo / descripción
     * @param {"danger"|"warning"|"info"}  [opts.variant="danger"]
     * @param {string} [opts.icon]         - Clase Bootstrap Icon (sin "bi ")
     * @param {string} [opts.confirmLabel] - Texto botón confirmar
     * @param {string} [opts.cancelLabel]  - Texto botón cancelar
     * @returns {Promise<boolean>}
     */
    _showConfirm({
        title         = "¿Estás seguro?",
        message       = "",
        variant       = "danger",
        icon          = null,
        confirmLabel  = "Confirmar",
        cancelLabel   = "Cancelar",
    } = {}) {
        // Icono por defecto según variante
        if (!icon) {
            icon = {
                danger:  "bi-trash3-fill",
                warning: "bi-exclamation-triangle-fill",
                info:    "bi-info-circle-fill",
            }[variant] || "bi-question-circle-fill";
        }
        return new Promise((resolve) => {
            this.state.confirmModal = {
                title, message, variant, icon,
                confirmLabel, cancelLabel,
                resolve,
            };
        });
    }

    _onConfirmModalAccept() {
        const resolve = this.state.confirmModal?.resolve;
        this.state.confirmModal = null;
        resolve?.(true);
    }

    _onConfirmModalCancel() {
        const resolve = this.state.confirmModal?.resolve;
        this.state.confirmModal = null;
        resolve?.(false);
    }

    // ─── Navegación ───────────────────────────────────────────────────────────

    async _loadContents(folderId) {
        this.state.loading         = true;
        this.state.error           = null;
        this.state.selectedIds     = new Set();
        this.state.showCreatePanel = false;
        this.state.createResults   = [];
        try {
            const items = await this.orm.call(
                "pcloud.config", "pcloud_list_contents", [parseInt(folderId)]
            );
            this.state.items           = items;
            this.state.currentFolderId = String(folderId);
        } catch (e) {
            const msg = e.data?.message || e.message || "Error al conectar con pCloud";
            this.state.error = msg;
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    // Click principal: navega carpeta o previsualiza archivo
    async onItemClick(item, ev) {
        if (ev.target.closest(".pce_item_checkbox")) return;
        if (item.is_folder) {
            this.state.breadcrumbs.push({ id: item.id, name: item.name });
            await this._loadContents(item.id);
        } else {
            await this.openFilePreview(item);
        }
    }

    onCheckboxClick(item, ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const ids = new Set(this.state.selectedIds);
        ids.has(item.id) ? ids.delete(item.id) : ids.add(item.id);
        this.state.selectedIds     = ids;
        this.state.showCreatePanel = this.selectedFolderItems.length > 0;
    }

    async onBreadcrumbClick(crumb, index) {
        this.state.breadcrumbs = this.state.breadcrumbs.slice(0, index + 1);
        await this._loadContents(crumb.id);
    }

    // ─── Previsualización ─────────────────────────────────────────────────────

    async openFilePreview(item) {
        if (item.is_folder) return;
        const type = this.getPreviewType(item);

        if (type === "pdf") {
            const proxyUrl = `/pcloud/stream/${item.id}/${encodeURIComponent(item.name)}`;
            window.open(proxyUrl, "_blank");
            return;
        }

        this.state.previewItem    = item;
        this.state.previewUrl     = null;
        this.state.previewLoading = true;
        this.state.modal          = "preview";
        try {
            const proxyUrl = await this._getProxyUrl(item);
            this.state.previewUrl = proxyUrl;
        } catch (e) {
            this.notification.add(e.data?.message || e.message || "Error al obtener archivo", { type: "danger" });
            this.closeModal();
        } finally {
            this.state.previewLoading = false;
        }
    }

    _getProxyUrl(item) {
        const safeName = encodeURIComponent(item.name);
        return Promise.resolve(`/pcloud/stream/${item.id}/${safeName}`);
    }

    getPreviewType(item) {
        if (!item) return "unknown";
        const ext = item.name.split(".").pop().toLowerCase();
        if (["jpg","jpeg","png","gif","webp","svg","bmp"].includes(ext)) return "image";
        if (ext === "pdf") return "pdf";
        if (["mp4","webm"].includes(ext)) return "video";
        if (["mp3","wav","ogg","flac"].includes(ext)) return "audio";
        return "download";
    }

    getPdfViewerUrl(rawUrl) { return rawUrl || ""; }
    onPdfIframeLoad() {}

    // ─── Selección ────────────────────────────────────────────────────────────

    toggleSelectAll() {
        if (this.state.selectedIds.size === this.filteredItems.length) {
            this.state.selectedIds     = new Set();
            this.state.showCreatePanel = false;
        } else {
            this.state.selectedIds     = new Set(this.filteredItems.map(i => i.id));
            this.state.showCreatePanel = this.selectedFolderItems.length > 0;
        }
    }

    isSelected(item) { return this.state.selectedIds.has(item.id); }

    get selectedItems()       { return this.state.items.filter(i => this.state.selectedIds.has(i.id)); }
    get selectedFolderItems() { return this.selectedItems.filter(i => i.is_folder); }

    // ─── Modales ──────────────────────────────────────────────────────────────

    openModal(type, data = {}) { this.state.modal = type; this.state.modalData = { ...data }; }

    closeModal() {
        this.state.modal        = null;
        this.state.modalData    = {};
        this.state.previewItem  = null;
        this.state.previewUrl   = null;
    }

    // ─── Crear carpeta ────────────────────────────────────────────────────────

    openNewFolderModal() { this.openModal("newFolder", { name: "" }); }

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

    openRenameModal(item) { this.openModal("rename", { item, newName: item.name }); }

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

        const label = items.length > 1
            ? `${items.length} elementos`
            : `"${items[0].name}"`;

        const ok = await this._showConfirm({
            title:        "Eliminar " + (items.length > 1 ? "elementos" : "archivo"),
            message:      `¿Eliminar ${label}? Esta acción no se puede deshacer.`,
            variant:      "danger",
            icon:         "bi-trash3-fill",
            confirmLabel: "Sí, eliminar",
            cancelLabel:  "Cancelar",
        });

        if (!ok) return;

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
        ev.stopPropagation();
        this.state.selectedIds = new Set([item.id]);
        await this.deleteSelected();
    }

    // ─── Subir archivo ────────────────────────────────────────────────────────

    openUploadModal() { this.openModal("upload", { files: [] }); }

    onFileInputChange(ev) { this.state.modalData.files = Array.from(ev.target.files); }

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
            const r = new FileReader();
            r.onload  = () => resolve(r.result.split(",")[1]);
            r.onerror = reject;
            r.readAsDataURL(file);
        });
    }

    // ─── Compartir ────────────────────────────────────────────────────────────

    async openShareModal(item) {
        if (!item.is_folder) return;
        this.openModal("share", { item, loading: true, link: null });
        try {
            const result = await this.orm.call(
                "pcloud.config", "pcloud_get_share_link", [item.id]
            );
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
        const ok = await this._showConfirm({
            title:        "Revocar link público",
            message:      "El link dejará de funcionar para quienes lo tengan. ¿Deseas continuar?",
            variant:      "warning",
            icon:         "bi-link-45deg",
            confirmLabel: "Sí, revocar",
            cancelLabel:  "Cancelar",
        });
        if (!ok) return;

        try {
            await this.orm.call(
                "pcloud.config", "pcloud_delete_share_link", [this.state.modalData.code]
            );
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
            const safeName = encodeURIComponent(item.name);
            const proxyUrl = `/pcloud/stream/${item.id}/${safeName}`;
            const a = document.createElement("a");
            a.href     = proxyUrl;
            a.download = item.name;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al descargar", { type: "danger" });
        }
    }

    // ─── Crear productos desde carpetas ───────────────────────────────────────

    toggleCreatePanel() {
        this.state.showCreatePanel = !this.state.showCreatePanel;
        this.state.createResults   = [];
    }

    async confirmCreateProducts() {
        const folders  = this.selectedFolderItems.map(i => ({ id: i.id, name: i.name }));
        if (!folders.length) {
            this.notification.add("Selecciona al menos una carpeta", { type: "warning" });
            return;
        }
        const pricePen = parseFloat(this.state.createPricePen) || 100;
        const priceUsd = parseFloat(this.state.createPriceUsd) || 25;
        this.state.creatingProducts = true;
        this.state.createResults    = [];
        try {
            const results = await this.orm.call(
                "pcloud.config", "pcloud_create_products_from_folders",
                [folders, pricePen, priceUsd],
            );
            this.state.createResults = results;
            const created  = results.filter(r => r.status === "created").length;
            const existing = results.filter(r => r.status === "already_exists").length;
            const errors   = results.filter(r => r.status === "error").length;
            if (created > 0)
                this.notification.add(
                    `${created} producto(s) creado(s)${existing ? `, ${existing} ya existía(n)` : ""}`,
                    { type: "success" }
                );
            else if (existing > 0 && errors === 0)
                this.notification.add("Todos los productos ya existen", { type: "info" });
            if (errors > 0)
                this.notification.add(`${errors} error(es) al crear productos`, { type: "danger" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al crear productos", { type: "danger" });
        } finally {
            this.state.creatingProducts = false;
        }
    }

    getCreateResultIcon(status) {
        return { created: "✅", already_exists: "⚠️", error: "❌" }[status] || "❓";
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

    onDragLeave() { this.state.dragOverId = null; }

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
            this.notification.add(
                `"${dragged.name}" movido a "${targetItem.name}"`, { type: "success" }
            );
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al mover", { type: "danger" });
        }
    }

    // ─── Context menu ─────────────────────────────────────────────────────────

    onContextMenu(item, ev) {
        ev.preventDefault();
        this.state.selectedIds  = new Set([item.id]);
        this.state.contextMenu  = { x: ev.clientX, y: ev.clientY, item };
    }

    closeContextMenu() { this.state.contextMenu = null; }

    // ─── Búsqueda ─────────────────────────────────────────────────────────────

    get filteredItems() {
        const q = this.state.searchQuery.toLowerCase().trim();
        if (!q) return this.state.items;
        return this.state.items.filter(i => i.name.toLowerCase().includes(q));
    }

    // ─── Helpers template ─────────────────────────────────────────────────────

    getFileType(item)         { return getFileType(item.name, item.is_folder); }
    getFormattedSize(item)    { return item.is_folder ? "" : formatSize(item.size); }
    getFormattedDate(item)    { return formatDate(item.modified); }

    get allSelected() {
        return this.filteredItems.length > 0 &&
               this.state.selectedIds.size === this.filteredItems.length;
    }
}

registry.category("actions").add("pcloud_explorer_action", PCloudExplorer);