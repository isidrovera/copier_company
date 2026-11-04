
/** @odoo-module **/

/*
 * COPIER COMPANY — PORTAL DE DESCARGAS
 * Odoo 19 / pCloud
 *
 * Interfaz de clientes tipo Dropbox.
 *
 * La búsqueda profunda y la vista previa requieren
 * las rutas del controlador que se implementarán
 * en el siguiente archivo.
 */

(function () {
    "use strict";

    const ROOT_ID = "cc-dropbox";

    const SEARCH_DELAY = 450;
    const PREVIEW_ROUTE = "/soporte/vista-previa";
    const SEARCH_ROUTE = "/soporte/descargas/buscar";

    const VIEW_KEY = "cc_portal_download_view";
    const SORT_KEY = "cc_portal_download_sort";

    function init() {
        const root = document.getElementById(ROOT_ID);

        if (!root || root.dataset.initialized === "1") {
            return;
        }

        root.dataset.initialized = "1";

        const elements = {
            search: root.querySelector("#search-input"),
            searchForm: root.querySelector("#search-form"),
            clearSearch: root.querySelector("#cc-clear-search"),

            gridButton: root.querySelector("#kanban-view-btn"),
            listButton: root.querySelector("#list-view-btn"),

            gridView: root.querySelector("#kanban-view"),
            listView: root.querySelector("#list-view"),

            grid: root.querySelector("#cc-card-grid"),
            list: root.querySelector("#files-list"),

            empty: root.querySelector("#cc-filter-empty"),
            counts: root.querySelectorAll(
                "#cc-item-count, .cc-explorer-count"
            ),

            sortButton: root.querySelector("#modified-header"),
            sortIcon: root.querySelector("#sort-icon"),

            recentSection: root.querySelector("#cc-recent-section"),
            recentGrid: root.querySelector("#cc-recent-grid"),

            modal: root.querySelector("#cc-file-modal"),
            modalBackdrop: root.querySelector("#cc-modal-backdrop"),
            modalClose: root.querySelector("#cc-modal-close"),

            modalFilename: root.querySelector("#cc-modal-filename"),
            modalSize: root.querySelector("#cc-modal-size"),
            modalDate: root.querySelector("#cc-modal-date"),

            previewContainer: root.querySelector(
                "#cc-preview-container"
            ),

            previewButton: root.querySelector("#cc-preview-btn"),
            downloadButton: root.querySelector("#cc-modal-download"),
        };

        const required = [
            "search",
            "searchForm",
            "gridButton",
            "listButton",
            "gridView",
            "listView",
            "grid",
            "list",
            "modal",
        ];

        if (required.some((name) => !elements[name])) {
            console.error(
                "[Copier Descargas] Faltan elementos en el XML."
            );
            return;
        }

        const state = {
            folderId: root.dataset.folderId || "0",
            view: readStorage(VIEW_KEY, "grid"),
            sort: readStorage(SORT_KEY, "desc"),
            searchTimer: null,
            searchController: null,
            searchSequence: 0,
            selectedFile: null,
            initialGrid: Array.from(
                elements.grid.children
            ).map((node) => node.cloneNode(true)),
            initialRows: Array.from(
                elements.list.children
            ).map((node) => node.cloneNode(true)),
        };

        function readStorage(key, fallback) {
            try {
                return localStorage.getItem(key) || fallback;
            } catch (_) {
                return fallback;
            }
        }

        function writeStorage(key, value) {
            try {
                localStorage.setItem(key, value);
            } catch (_) {
                // El portal sigue funcionando sin almacenamiento.
            }
        }

        function setView(mode) {
            const isGrid = mode !== "list";

            state.view = isGrid ? "grid" : "list";

            elements.gridView.hidden = !isGrid;
            elements.listView.hidden = isGrid;

            elements.gridButton.classList.toggle(
                "active",
                isGrid
            );

            elements.listButton.classList.toggle(
                "active",
                !isGrid
            );

            elements.gridButton.setAttribute(
                "aria-pressed",
                String(isGrid)
            );

            elements.listButton.setAttribute(
                "aria-pressed",
                String(!isGrid)
            );

            writeStorage(VIEW_KEY, state.view);
        }

        elements.gridButton.addEventListener("click", () => {
            setView("grid");
        });

        elements.listButton.addEventListener("click", () => {
            setView("list");
        });

        setView(state.view);

        /*
         * UTILIDADES DE ARCHIVOS
         */

        function fileDownloadUrl(fileId) {
            return (
                "/soporte/descarga?file_id=" +
                encodeURIComponent(fileId)
            );
        }

        function filePreviewUrl(fileId) {
            return (
                PREVIEW_ROUTE +
                "?file_id=" +
                encodeURIComponent(fileId)
            );
        }

        function getExtension(filename) {
            const value = String(filename || "");

            if (!value.includes(".")) {
                return "";
            }

            return value.split(".").pop().toLowerCase();
        }

        function getPreviewType(filename) {
            const ext = getExtension(filename);

            if (["png", "jpg", "jpeg", "gif", "webp"].includes(ext)) {
                return "image";
            }

            if (ext === "pdf") {
                return "pdf";
            }

            if (["mp4", "webm", "ogg"].includes(ext)) {
                return "video";
            }

            if (["txt", "log", "csv"].includes(ext)) {
                return "text";
            }

            return "unsupported";
        }

        function showPreviewMessage(message, icon = "fa-file-o") {
            elements.previewContainer.replaceChildren();

            const placeholder = document.createElement("div");
            placeholder.className = "cc-preview-placeholder";

            const iconElement = document.createElement("i");
            iconElement.className = "fa " + icon;

            const paragraph = document.createElement("p");
            paragraph.textContent = message;

            placeholder.append(iconElement, paragraph);
            elements.previewContainer.appendChild(placeholder);
        }

        function openFile(file) {
            if (!file || !file.id) {
                return;
            }

            state.selectedFile = file;

            elements.modalFilename.textContent =
                file.name || "Archivo";

            elements.modalSize.textContent =
                file.size || "—";

            elements.modalDate.textContent =
                file.date || "—";

            elements.downloadButton.href = fileDownloadUrl(file.id);

            showPreviewMessage(
                "Selecciona Vista previa para visualizar el archivo."
            );

            const previewType = getPreviewType(file.name);

            elements.previewButton.hidden =
                previewType === "unsupported";

            if (previewType === "unsupported") {
                showPreviewMessage(
                    "Este formato no tiene vista previa disponible. " +
                    "Puedes descargar el archivo.",
                    "fa-file-o"
                );
            }

            elements.modal.hidden = false;
            document.body.style.overflow = "hidden";

            elements.modalClose?.focus();
        }

        function closeFile() {
            elements.modal.hidden = true;

            state.selectedFile = null;

            elements.previewContainer.replaceChildren();

            document.body.style.overflow = "";
        }

        function getFileFromElement(element) {
            return {
                id: element.dataset.fileId || "",
                name: element.dataset.name || "",
                size: element.dataset.size || "",
                date: element.dataset.date || "",
                icon: element.dataset.icon || "",
            };
        }

        /*
         * CLIC EN LOS ARCHIVOS
         *
         * Las carpetas son enlaces en el XML:
         * se abren directamente con un clic.
         */

        root.addEventListener("click", (event) => {
            const trigger = event.target.closest(
                ".cc-file-trigger"
            );

            if (!trigger || !root.contains(trigger)) {
                return;
            }

            event.preventDefault();

            openFile(getFileFromElement(trigger));
        });

        elements.modalClose?.addEventListener(
            "click",
            closeFile
        );

        elements.modalBackdrop?.addEventListener(
            "click",
            closeFile
        );

        document.addEventListener("keydown", (event) => {
            if (
                event.key === "Escape" &&
                !elements.modal.hidden
            ) {
                closeFile();
            }
        });

        /*
         * VISTA PREVIA
         *
         * No utiliza la ruta /soporte/descarga,
         * porque dicha ruta obliga a descargar.
         *
         * Requiere implementar PREVIEW_ROUTE
         * en el controlador Python.
         */

        async function previewFile() {
            const file = state.selectedFile;

            if (!file) {
                return;
            }

            const type = getPreviewType(file.name);

            if (type === "unsupported") {
                showPreviewMessage(
                    "No hay vista previa para este formato."
                );
                return;
            }

            const url = filePreviewUrl(file.id);

            showPreviewMessage(
                "Cargando vista previa...",
                "fa-spinner fa-spin"
            );

            try {
                const response = await fetch(url, {
                    method: "HEAD",
                    credentials: "same-origin",
                    cache: "no-store",
                });

                if (!response.ok) {
                    throw new Error(
                        "No se pudo cargar la vista previa."
                    );
                }

                const contentType = (
                    response.headers.get("Content-Type") || ""
                ).toLowerCase();

                if (
                    contentType.includes("text/html") &&
                    type !== "text"
                ) {
                    throw new Error(
                        "La ruta no devolvió el archivo esperado."
                    );
                }

                if (state.selectedFile !== file) {
                    return;
                }

                elements.previewContainer.replaceChildren();

                let viewer;

                if (type === "image") {
                    viewer = document.createElement("img");
                    viewer.alt = file.name;
                    viewer.src = url;

                } else if (type === "pdf") {
                    viewer = document.createElement("iframe");
                    viewer.title = "Vista previa: " + file.name;
                    viewer.src = url;

                } else if (type === "video") {
                    viewer = document.createElement("video");
                    viewer.controls = true;
                    viewer.preload = "metadata";
                    viewer.src = url;

                } else if (type === "text") {
                    const textResponse = await fetch(url, {
                        credentials: "same-origin",
                    });

                    if (!textResponse.ok) {
                        throw new Error("No se pudo leer el texto.");
                    }

                    const text = await textResponse.text();

                    if (state.selectedFile !== file) {
                        return;
                    }

                    viewer = document.createElement("pre");
                    viewer.textContent = text.slice(0, 200000);
                    viewer.style.cssText =
                        "padding:20px;white-space:pre-wrap;" +
                        "overflow:auto;width:100%;max-height:60vh;";
                }

                if (viewer) {
                    viewer.addEventListener?.("error", () => {
                        showPreviewMessage(
                            "No se pudo mostrar el archivo. " +
                            "Utiliza Descargar."
                        );
                    });

                    elements.previewContainer.appendChild(viewer);
                }

            } catch (error) {
                console.warn(
                    "[Copier Descargas] Vista previa:",
                    error
                );

                showPreviewMessage(
                    "Vista previa no disponible. " +
                    "Puedes descargar el archivo."
                );
            }
        }

        elements.previewButton?.addEventListener(
            "click",
            previewFile
        );

        /*
         * BÚSQUEDA
         *
         * 1. Filtra inmediatamente los elementos visibles.
         * 2. Solicita resultados al controlador con debounce.
         * 3. Evita mostrar respuestas antiguas.
         */

        function normalize(value) {
            return String(value || "")
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase()
                .trim();
        }

        function visibleCount() {
            const container =
                state.view === "list"
                    ? elements.list
                    : elements.grid;

            return Array.from(container.children).filter(
                (node) => !node.hidden
            ).length;
        }

        function updateCount(count) {
            elements.counts.forEach((element) => {
                element.textContent =
                    count + (count === 1 ? " elemento" : " elementos");
            });
        }

        function updateEmpty() {
            if (!elements.empty) {
                return;
            }

            const count = visibleCount();

            elements.empty.hidden = count !== 0;

            updateCount(count);
        }

        function filterLocally(searchTerm) {
            const term = normalize(searchTerm);

            elements.grid.querySelectorAll(
                ".cc-file-card"
            ).forEach((card) => {
                card.hidden = !normalize(
                    card.dataset.name
                ).includes(term);
            });

            elements.list.querySelectorAll(
                ".cc-file-row"
            ).forEach((row) => {
                row.hidden = !normalize(
                    row.dataset.name
                ).includes(term);
            });

            updateEmpty();
        }

        function clearNode(node) {
            node.replaceChildren();
        }

        function restoreInitialItems() {
            clearNode(elements.grid);
            clearNode(elements.list);

            state.initialGrid.forEach((node) => {
                elements.grid.appendChild(node.cloneNode(true));
            });

            state.initialRows.forEach((node) => {
                elements.list.appendChild(node.cloneNode(true));
            });

            applySort();
            updateEmpty();
        }

        /*
         * CONSTRUCCIÓN SEGURA DE RESULTADOS
         *
         * Los nombres se insertan como texto,
         * nunca como HTML procedente de pCloud.
         */

        function createIcon(item) {
            const wrapper = document.createElement("div");
            wrapper.className = "cc-row-icon";

            if (item.isfolder) {
                const icon = document.createElement("i");
                icon.className = "fa fa-folder";
                wrapper.appendChild(icon);
            } else {
                const image = document.createElement("img");

                image.src =
                    "/copier_company/static/src/img/" +
                    encodeURIComponent(item.icon || "icons8-file-48.png");

                image.alt = "";
                wrapper.appendChild(image);
            }

            return wrapper;
        }

        function createCard(item) {
            const folder = Boolean(item.isfolder);
            const card = document.createElement(
                folder ? "a" : "button"
            );

            card.className =
                "cc-file-card " +
                (folder
                    ? "cc-folder-card"
                    : "cc-document-card cc-file-trigger");

            card.dataset.name = item.name || "";
            card.dataset.type = folder ? "folder" : "file";

            if (folder) {
                card.href =
                    "/soporte/descargas?folder_id=" +
                    encodeURIComponent(item.id);

            } else {
                card.type = "button";
                card.dataset.fileId = String(item.id);
                card.dataset.size = item.size || "";
                card.dataset.date = item.modified || "";
                card.dataset.icon = item.icon || "";
            }

            const top = document.createElement("div");
            top.className = "cc-card-top";

            const typeLabel = document.createElement("span");
            typeLabel.className = "cc-file-type";
            typeLabel.textContent = folder ? "Carpeta" : "Archivo";

            top.appendChild(typeLabel);

            const visual = document.createElement("div");
            visual.className =
                "cc-card-visual " +
                (folder
                    ? "cc-folder-visual"
                    : "cc-document-visual");

            if (folder) {
                const icon = document.createElement("i");
                icon.className = "fa fa-folder";
                visual.appendChild(icon);
            } else {
                const image = document.createElement("img");

                image.src =
                    "/copier_company/static/src/img/" +
                    encodeURIComponent(item.icon || "icons8-file-48.png");

                image.alt = "";
                image.loading = "lazy";

                visual.appendChild(image);
            }

            const info = document.createElement("div");
            info.className = "cc-card-info";

            const name = document.createElement("strong");
            name.textContent = item.name || "";
            name.title = item.name || "";

            const details = document.createElement("span");
            details.className = "cc-card-details";
            details.textContent = folder
                ? "Abrir carpeta"
                : (item.size || "Archivo");

            info.append(name, details);

            card.append(top, visual, info);

            return card;
        }

        function createRow(item) {
            const folder = Boolean(item.isfolder);

            const row = document.createElement("tr");
            row.className = "cc-file-row";
            row.dataset.name = item.name || "";
            row.dataset.date = item.modified || "";

            const nameCell = document.createElement("td");
            const nameWrapper = document.createElement("div");
            nameWrapper.className = "cc-row-name";

            nameWrapper.appendChild(createIcon(item));

            const nameControl = document.createElement(
                folder ? "a" : "button"
            );

            nameControl.className =
                "cc-row-link" +
                (folder ? "" : " cc-file-trigger");

            nameControl.textContent = item.name || "";

            if (folder) {
                nameControl.href =
                    "/soporte/descargas?folder_id=" +
                    encodeURIComponent(item.id);
            } else {
                nameControl.type = "button";
                nameControl.dataset.fileId = String(item.id);
                nameControl.dataset.name = item.name || "";
                nameControl.dataset.size = item.size || "";
                nameControl.dataset.date = item.modified || "";
                nameControl.dataset.icon = item.icon || "";
            }

            nameWrapper.appendChild(nameControl);
            nameCell.appendChild(nameWrapper);

            const typeCell = document.createElement("td");
            typeCell.textContent = folder ? "Carpeta" : "Archivo";

            const sizeCell = document.createElement("td");
            sizeCell.textContent = item.size || "—";

            const dateCell = document.createElement("td");
            dateCell.textContent = item.modified || "—";

            const actionCell = document.createElement("td");
            const action = document.createElement("a");

            action.className = "cc-row-action";

            action.href = folder
                ? "/soporte/descargas?folder_id=" +
                  encodeURIComponent(item.id)
                : fileDownloadUrl(item.id);

            action.title = folder
                ? "Abrir carpeta"
                : "Descargar archivo";

            const icon = document.createElement("i");
            icon.className = folder
                ? "fa fa-arrow-right"
                : "fa fa-download";

            action.appendChild(icon);
            actionCell.appendChild(action);

            row.append(
                nameCell,
                typeCell,
                sizeCell,
                dateCell,
                actionCell
            );

            return row;
        }

        function renderResults(items) {
            clearNode(elements.grid);
            clearNode(elements.list);

            items.forEach((item) => {
                if (
                    item.id === undefined ||
                    item.id === null
                ) {
                    return;
                }

                elements.grid.appendChild(createCard(item));
                elements.list.appendChild(createRow(item));
            });

            applySort();
            updateEmpty();
        }

        /*
         * CONSULTA AL CONTROLADOR
         *
         * Respuesta esperada:
         * {
         *   "items": [
         *      {
         *        "id": 123,
         *        "name": "manual.pdf",
         *        "isfolder": false,
         *        "size": "2.50 MB",
         *        "modified": "04 Nov 2026, 14:00",
         *        "icon": "icons8-pdf-48.png"
         *      }
         *   ]
         * }
         */

        async function searchRemotely(term, sequence) {
            const params = new URLSearchParams({
                folder_id: state.folderId,
                search: term,
            });

            if (state.searchController) {
                state.searchController.abort();
            }

            const controller = new AbortController();
            state.searchController = controller;

            try {
                const response = await fetch(
                    SEARCH_ROUTE + "?" + params.toString(),
                    {
                        method: "GET",
                        credentials: "same-origin",
                        signal: controller.signal,
                        headers: {
                            Accept: "application/json",
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        "Error HTTP " + response.status
                    );
                }

                const data = await response.json();

                if (!Array.isArray(data.items)) {
                    throw new Error(
                        "La respuesta no contiene items."
                    );
                }

                if (
                    sequence !== state.searchSequence ||
                    normalize(elements.search.value) !== normalize(term)
                ) {
                    return;
                }

                renderResults(data.items);

            } catch (error) {
                if (error.name === "AbortError") {
                    return;
                }

                console.warn(
                    "[Copier Descargas] Búsqueda remota:",
                    error
                );

                /*
                 * Conserva el filtro local si el endpoint
                 * todavía no está disponible.
                 */
            }
        }

        function handleSearch() {
            const term = elements.search.value.trim();

            clearTimeout(state.searchTimer);

            const sequence = ++state.searchSequence;

            if (state.searchController) {
                state.searchController.abort();
                state.searchController = null;
            }

            if (!term) {
                restoreInitialItems();
                return;
            }

            filterLocally(term);

            state.searchTimer = setTimeout(() => {
                searchRemotely(term, sequence);
            }, SEARCH_DELAY);
        }

        elements.search.addEventListener(
            "input",
            handleSearch
        );

        elements.clearSearch?.addEventListener(
            "click",
            () => {
                elements.search.value = "";
                handleSearch();
                elements.search.focus();
            }
        );

        elements.searchForm.addEventListener(
            "submit",
            (event) => {
                event.preventDefault();
                handleSearch();
            }
        );

        /*
         * ORDENAMIENTO
         */

        function parseFileDate(value) {
            if (!value) {
                return 0;
            }

            const text = String(value).trim();

            const months = {
                jan: 0, ene: 0,
                feb: 1,
                mar: 2,
                apr: 3, abr: 3,
                may: 4,
                jun: 5,
                jul: 6,
                aug: 7, ago: 7,
                sep: 8, set: 8,
                oct: 9,
                nov: 10,
                dec: 11, dic: 11,
            };

            const match = text.match(
                /^(\d{1,2})\s+([a-záéíóú]{3})\s+(\d{4})(?:,\s*(\d{1,2}):(\d{2}))?/i
            );

            if (match) {
                const monthKey = normalize(match[2]).slice(0, 3);
                const month = months[monthKey];

                if (month !== undefined) {
                    return new Date(
                        Number(match[3]),
                        month,
                        Number(match[1]),
                        Number(match[4] || 0),
                        Number(match[5] || 0)
                    ).getTime();
                }
            }

            const numeric = text.match(
                /^(\d{1,2})\/(\d{1,2})\/(\d{4})/
            );

            if (numeric) {
                return new Date(
                    Number(numeric[3]),
                    Number(numeric[2]) - 1,
                    Number(numeric[1])
                ).getTime();
            }

            const parsed = Date.parse(text);

            return Number.isFinite(parsed) ? parsed : 0;
        }

        function sortContainer(container, selector) {
            const nodes = Array.from(
                container.querySelectorAll(selector)
            );

            nodes.sort((a, b) => {
                const dateA = parseFileDate(a.dataset.date);
                const dateB = parseFileDate(b.dataset.date);

                return state.sort === "desc"
                    ? dateB - dateA
                    : dateA - dateB;
            });

            nodes.forEach((node) => {
                container.appendChild(node);
            });
        }

        function applySort() {
            sortContainer(elements.grid, ".cc-file-card");
            sortContainer(elements.list, ".cc-file-row");

            if (elements.sortIcon) {
                elements.sortIcon.className =
                    state.sort === "desc"
                        ? "fa fa-sort-amount-desc"
                        : "fa fa-sort-amount-asc";
            }
        }

        elements.sortButton?.addEventListener(
            "click",
            () => {
                state.sort =
                    state.sort === "desc" ? "asc" : "desc";

                writeStorage(SORT_KEY, state.sort);
                applySort();
            }
        );

        applySort();

        /*
         * ARCHIVOS RECIENTES
         *
         * Se muestran archivos del listado actual
         * ordenados según su fecha de modificación.
         * No se inventan fechas ni estadísticas.
         */

        function buildRecentFiles() {
            if (
                !elements.recentSection ||
                !elements.recentGrid
            ) {
                return;
            }

            const files = Array.from(
                elements.grid.querySelectorAll(
                    ".cc-document-card"
                )
            ).map((card) => getFileFromElement(card));

            files.sort((a, b) => {
                return (
                    parseFileDate(b.date) -
                    parseFileDate(a.date)
                );
            });

            const recent = files.filter(
                (file) => parseFileDate(file.date) > 0
            ).slice(0, 4);

            elements.recentGrid.replaceChildren();

            if (!recent.length) {
                elements.recentSection.hidden = true;
                return;
            }

            recent.forEach((file) => {
                const button = document.createElement("button");
                button.type = "button";

                button.className =
                    "cc-recent-item cc-file-trigger";

                button.dataset.fileId = file.id;
                button.dataset.name = file.name;
                button.dataset.size = file.size;
                button.dataset.date = file.date;
                button.dataset.icon = file.icon;

                const icon = document.createElement("div");
                icon.className = "cc-recent-icon";

                const iconImage = document.createElement("i");
                iconImage.className = "fa fa-file-o";
                icon.appendChild(iconImage);

                const info = document.createElement("div");
                info.className = "cc-recent-info";

                const name = document.createElement("strong");
                name.textContent = file.name;
                name.title = file.name;

                const date = document.createElement("small");
                date.textContent = file.date || "Archivo";

                info.append(name, date);
                button.append(icon, info);

                elements.recentGrid.appendChild(button);
            });

            elements.recentSection.hidden = false;
        }

        buildRecentFiles();

        /*
         * RESTAURAR BÚSQUEDA INICIAL
         */

        if (elements.search.value.trim()) {
            handleSearch();
        } else {
            updateEmpty();
        }

        console.info(
            "[Copier Descargas] Portal inicializado."
        );
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            init,
            { once: true }
        );
    } else {
        init();
    }
})();
