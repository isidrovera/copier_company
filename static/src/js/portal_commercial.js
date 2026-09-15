/* Script clásico: se carga directamente desde la plantilla QWeb. */
(function () {
    'use strict';
    if (window.__copierCommercialLoaded) return;
    window.__copierCommercialLoaded = true;
    let pickerNumber = 0;

    function initializePicker(picker) {
        if (picker.dataset.pcInitialized) return;
        const form = picker.closest('form');
        const input = picker.querySelector('.pc-product-search');
        const results = picker.querySelector('.pc-search-results');
        const hint = picker.querySelector('.pc-search-hint');
        const productId = form?.querySelector('[name="product_id"]');
        if (!input || !results || !productId) return;
        picker.dataset.pcInitialized = '1';
        const description = form.querySelector('[name="description"]');
        const price = form.querySelector('[name="price_unit"]');
        const taxes = form.querySelectorAll('[name="tax_ids"]');
        const orderId = picker.dataset.orderId;
        const invoiceId = picker.dataset.invoiceId;
        let timer, controller, generation = 0, activeIndex = -1, composing = false;
        let products = [];
        results.id = 'pc-results-' + (++pickerNumber);
        input.setAttribute('role', 'combobox');
        input.setAttribute('aria-autocomplete', 'list');
        input.setAttribute('aria-controls', results.id);
        input.setAttribute('aria-expanded', 'false');
        const announce = text => { if (hint) hint.textContent = text; };
        function invalidate() {
            clearTimeout(timer);
            controller?.abort();
            generation++;
            picker.classList.remove('pc-searching');
            input.setAttribute('aria-busy', 'false');
        }
        function close() {
            results.hidden = true;
            picker.classList.remove('pc-picker-open');
            input.setAttribute('aria-expanded', 'false');
            input.removeAttribute('aria-activedescendant');
            activeIndex = -1;
        }
        function open() {
            results.hidden = false;
            picker.classList.add('pc-picker-open');
            input.setAttribute('aria-expanded', 'true');
        }
        function message(text) {
            products = [];
            activeIndex = -1;
            input.removeAttribute('aria-activedescendant');
            results.replaceChildren();
            const item = document.createElement('div');
            item.className = 'pc-search-message';
            item.textContent = text;
            results.append(item);
            announce(text);
            open();
        }
        function select(product) {
            invalidate();
            productId.value = String(product.id);
            input.value = product.name;
            input.setCustomValidity('');
            picker.classList.add('pc-selected');
            if (description) description.value = product.description || product.name;
            if (price) price.value = String(product.price ?? 0);
            const ids = new Set((product.tax_ids || []).map(Number));
            taxes.forEach(tax => { tax.checked = ids.has(Number(tax.value)); });
            close();
            announce('Producto seleccionado. Revise cantidad, precio e impuestos y pulse Agregar producto.');
        }
        function render(items) {
            if (!items.length) {
                message('No se encontraron productos. Pruebe otro nombre o referencia.');
                return;
            }
            products = items;
            activeIndex = -1;
            input.removeAttribute('aria-activedescendant');
            results.replaceChildren();
            items.forEach((product, index) => {
                const option = document.createElement('button');
                option.type = 'button';
                option.tabIndex = -1;
                option.id = results.id + '-' + index;
                option.className = 'pc-search-option';
                option.setAttribute('role', 'option');
                option.setAttribute('aria-selected', 'false');
                const title = document.createElement('span');
                title.className = 'pc-search-option-title';
                title.textContent = product.name;
                const info = document.createElement('span');
                info.className = 'pc-search-option-info';
                info.textContent = [product.code, product.description].filter(Boolean).join(' · ');
                const amount = document.createElement('span');
                amount.className = 'pc-search-option-price';
                amount.textContent = 'Precio base: ' + Number(product.price ?? 0).toLocaleString('es-PE', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                option.append(title, info, amount);
                option.addEventListener('mousedown', event => event.preventDefault());
                option.addEventListener('click', () => select(product));
                results.append(option);
            });
            announce(items.length + ' resultados. Seleccione uno para agregarlo.');
            open();
        }
        async function search(term, token) {
            if (token !== generation) return;
            if (!orderId && !invoiceId) {
                message('No se pudo identificar el documento. Recargue la página.');
                return;
            }
            controller = new AbortController();
            const url = new URL('/my/commercial/products/search', window.location.origin);
            url.searchParams.set('q', term);
            url.searchParams.set(orderId ? 'order_id' : 'invoice_id', orderId || invoiceId);
            picker.classList.add('pc-searching');
            input.setAttribute('aria-busy', 'true');
            message('Buscando productos…');
            try {
                const response = await fetch(url, {
                    credentials: 'same-origin', cache: 'no-store',
                    signal: controller.signal, headers: {Accept: 'application/json'},
                });
                if (token !== generation) return;
                if (response.redirected || response.status === 401) {
                    throw new Error('La sesión ha cambiado. Recargue la página e inicie sesión nuevamente.');
                }
                if (response.status === 403) throw new Error('No tiene permiso para editar este documento.');
                if (!response.ok) throw new Error('No se pudo consultar el catálogo. Vuelva a intentarlo.');
                if (!(response.headers.get('content-type') || '').includes('application/json')) {
                    throw new Error('El servidor no devolvió el catálogo. Recargue la página.');
                }
                const data = await response.json();
                if (token !== generation) return;
                if (!Array.isArray(data.products)) throw new Error('Respuesta de catálogo inválida. Vuelva a intentarlo.');
                render(data.products);
            } catch (error) {
                if (error.name === 'AbortError' || token !== generation) return;
                message(error.message || 'No se pudo conectar. Vuelva a intentarlo.');
            } finally {
                if (token === generation) {
                    picker.classList.remove('pc-searching');
                    input.setAttribute('aria-busy', 'false');
                }
            }
        }
        function schedule() {
            invalidate();
            productId.value = '';
            input.setCustomValidity('');
            picker.classList.remove('pc-selected');
            close();
            products = [];
            results.replaceChildren();
            const term = input.value.trim();
            if (!term || composing) {
                announce('Busque por nombre, referencia, código de barras o descripción.');
                return;
            }
            announce('Buscando coincidencias…');
            const token = generation;
            timer = setTimeout(() => search(term, token), 250);
        }
        input.addEventListener('input', schedule);
        input.addEventListener('compositionstart', () => { composing = true; invalidate(); close(); });
        input.addEventListener('compositionend', () => { composing = false; schedule(); });
        input.addEventListener('focus', () => { if (input.value.trim() && !productId.value) schedule(); });
        input.addEventListener('keydown', event => {
            if (event.isComposing) return;
            if (event.key === 'Escape' || event.key === 'Tab') {
                invalidate(); close(); return;
            }
            if (event.key === 'Enter' && !productId.value) {
                event.preventDefault();
                if (!results.hidden && activeIndex >= 0) select(products[activeIndex]);
                else if (input.value.trim()) { invalidate(); search(input.value.trim(), generation); }
            }
            if (['ArrowDown', 'ArrowUp'].includes(event.key) && products.length && !results.hidden) {
                event.preventDefault();
                activeIndex = (activeIndex + (event.key === 'ArrowDown' ? 1 : -1) + products.length) % products.length;
                [...results.children].forEach((option, index) => {
                    option.setAttribute('aria-selected', String(index === activeIndex));
                });
                const option = results.children[activeIndex];
                input.setAttribute('aria-activedescendant', option.id);
                option.scrollIntoView({block: 'nearest'});
            }
        });
        document.addEventListener('click', event => {
            if (!picker.contains(event.target)) { invalidate(); close(); }
        });
        form.addEventListener('submit', event => {
            if (productId.value) return;
            event.preventDefault();
            input.setCustomValidity('Seleccione un producto de los resultados.');
            input.reportValidity();
            input.focus();
        });
    }
    function initialize() {
        document.querySelectorAll('.pc-product-picker').forEach(initializePicker);
        document.querySelectorAll('.pc-navigation a').forEach(link => {
            const path = new URL(link.href).pathname;
            const current = window.location.pathname;
            if (path === current || (path !== '/my/commercial' && current.startsWith(path + '/'))) {
                link.setAttribute('aria-current', 'page');
            }
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, {once: true});
    else initialize();
})();
