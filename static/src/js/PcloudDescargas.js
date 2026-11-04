/* Portal de descargas (website, Odoo 19). Sin dependencias adicionales. */
(function () {
    'use strict';

    function initDownloads() {
        const root = document.getElementById('cc-downloads');
        if (!root || root.dataset.initialized === '1') return;
        root.dataset.initialized = '1';

        const list = root.querySelector('#list-view');
        const grid = root.querySelector('#kanban-view');
        const listBtn = root.querySelector('#list-view-btn');
        const gridBtn = root.querySelector('#kanban-view-btn');
        const searchInput = root.querySelector('#search-input');
        const form = root.querySelector('#search-form');
        const viewInput = root.querySelector('#cc-search-view-mode');
        const count = root.querySelector('#cc-visible-count');
        const empty = root.querySelector('#cc-filter-empty');
        const sortBtn = root.querySelector('#modified-header');
        const sortIcon = root.querySelector('#sort-icon');
        const rows = Array.from(root.querySelectorAll('.cc-file-row'));
        const cards = Array.from(root.querySelectorAll('.cc-file-card'));
        const initialTotal = rows.length;

        let url = new URL(window.location.href);
        let mode = url.searchParams.get('view_mode');
        if (mode !== 'list' && mode !== 'kanban') {
            try { mode = localStorage.getItem('cc_downloads_view') || 'list'; }
            catch (_e) { mode = 'list'; }
        }
        if (mode !== 'list' && mode !== 'kanban') mode = 'list';

        function setViewMode(nextMode, updateUrl) {
            mode = nextMode === 'kanban' ? 'kanban' : 'list';
            if (list) list.hidden = mode !== 'list';
            if (grid) grid.hidden = mode !== 'kanban';
            if (listBtn) {
                listBtn.classList.toggle('active', mode === 'list');
                listBtn.setAttribute('aria-pressed', mode === 'list' ? 'true' : 'false');
            }
            if (gridBtn) {
                gridBtn.classList.toggle('active', mode === 'kanban');
                gridBtn.setAttribute('aria-pressed', mode === 'kanban' ? 'true' : 'false');
            }
            if (viewInput) viewInput.value = mode;
            root.dataset.view = mode;
            try { localStorage.setItem('cc_downloads_view', mode); } catch (_e) { /* almacenamiento no disponible */ }
            if (updateUrl) {
                url = new URL(window.location.href);
                url.searchParams.set('view_mode', mode);
                window.history.replaceState({}, '', url.toString());
            }
        }

        if (listBtn) listBtn.addEventListener('click', () => setViewMode('list', true));
        if (gridBtn) gridBtn.addEventListener('click', () => setViewMode('kanban', true));
        setViewMode(mode, false);

        // Filtro visual inmediato sobre los elementos que el servidor ya mostró.
        // La búsqueda en todas las subcarpetas sigue siendo la del controlador Python.
        function filterCurrentItems() {
            const term = searchInput ? searchInput.value.trim().toLocaleLowerCase() : '';
            let visible = 0;
            rows.forEach((row) => {
                const ok = (row.dataset.name || '').toLocaleLowerCase().includes(term);
                row.hidden = !ok;
                if (ok) visible += 1;
            });
            cards.forEach((card) => {
                const ok = (card.dataset.name || '').toLocaleLowerCase().includes(term);
                card.hidden = !ok;
            });
            if (count) count.textContent = String(term ? visible : initialTotal);
            if (empty) empty.hidden = visible > 0;
        }

        // Filtra únicamente los elementos que el controlador devolvió.
        if (searchInput) {
            searchInput.addEventListener('input', filterCurrentItems);
        }
        if (form) {
            form.addEventListener('submit', () => {
                if (viewInput) viewInput.value = mode;
            });
        }

        // Ordenamiento local por fecha, sin alterar enlaces ni rutas.
        let ascending = false;
        try { ascending = localStorage.getItem('cc_downloads_ascending') === 'true'; }
        catch (_e) { ascending = false; }
        function parseDate(value) {
            if (!value) return 0;
            const text = String(value).trim();
            // El controlador devuelve habitualmente DD Mon YYYY, HH:mm.
            const match = text.match(/^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4}),?\s+(\d{1,2}):(\d{2})$/);
            if (match) {
                const months = { jan:0, feb:1, mar:2, apr:3, may:4, jun:5, jul:6, aug:7, sep:8, oct:9, nov:10, dec:11 };
                const month = months[match[2].toLowerCase()];
                if (month !== undefined) return new Date(Number(match[3]), month, Number(match[1]), Number(match[4]), Number(match[5])).getTime();
            }
            const esMatch = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?$/);
            if (esMatch) return new Date(Number(esMatch[3]), Number(esMatch[2]) - 1, Number(esMatch[1]), Number(esMatch[4] || 0), Number(esMatch[5] || 0)).getTime();
            const parsed = Date.parse(text);
            return Number.isFinite(parsed) ? parsed : 0;
        }
        if (sortBtn && rows.length) {
            sortBtn.addEventListener('click', () => {
                ascending = !ascending;
                const parent = rows[0].parentElement;
                rows.sort((a, b) => {
                    const x = parseDate(a.dataset.date), y = parseDate(b.dataset.date);
                    return ascending ? x - y : y - x;
                });
                if (parent) rows.forEach(row => parent.appendChild(row));
                if (sortIcon) sortIcon.className = ascending ? 'fa fa-sort-asc' : 'fa fa-sort-desc';
                try { localStorage.setItem('cc_downloads_ascending', String(ascending)); }
                catch (_e) { /* almacenamiento no disponible */ }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDownloads, { once: true });
    } else {
        initDownloads();
    }
})();
