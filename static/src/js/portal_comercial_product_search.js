/** @odoo-module **/

(function () {
    "use strict";

    const PREFIX = "[Portal Comercial]";
    const log = (...args) => console.info(PREFIX, ...args);
    const warn = (...args) => console.warn(PREFIX, ...args);
    const fail = (...args) => console.error(PREFIX, ...args);

    function initializePicker(picker) {
        const form = picker.closest("form");
        const input = picker.querySelector(".pc-product-search");
        const results = picker.querySelector(".pc-search-results");

        // IMPORTANTE: product_id está en el formulario, no en picker.
        const productId = form?.querySelector(
            'input[name="product_id"]'
        );
        const description = form?.querySelector(
            '[name="description"]'
        );
        const price = form?.querySelector(
            '[name="price_unit"]'
        );
        const taxes = form?.querySelectorAll(
            'input[name="tax_ids"]'
        ) || [];

        if (!form || !input || !results || !productId) {
            fail("Buscador sin campos necesarios", {
                form: Boolean(form),
                input: Boolean(input),
                results: Boolean(results),
                productId: Boolean(productId),
            });
            return;
        }

        const orderId = picker.dataset.orderId;
        const invoiceId = picker.dataset.invoiceId;

        if (!orderId && !invoiceId) {
            fail("Falta data-order-id o data-invoice-id");
            return;
        }

        log("Buscador iniciado", {
            document: orderId ? "pedido" : "factura",
            id: orderId || invoiceId,
        });

        let debounceTimer;
        let activeRequest;
        let requestNumber = 0;

        function hideResults() {
            results.replaceChildren();
            results.hidden = true;
            picker.classList.remove("pc-picker-open");
        }

        function showMessage(message) {
            results.replaceChildren();

            const element = document.createElement("div");
            element.className = "pc-search-message";
            element.textContent = message;

            results.appendChild(element);
            results.hidden = false;
            picker.classList.add("pc-picker-open");
        }

        function selectProduct(product) {
            productId.value = String(product.id);
            input.value = product.name;

            if (description) {
                description.value =
                    product.description || product.name;
            }
            if (price) {
                price.value = String(product.price ?? 0);
            }

            const productTaxes = new Set(
                (product.tax_ids || []).map(Number)
            );
            for (const checkbox of taxes) {
                checkbox.checked = productTaxes.has(
                    Number(checkbox.value)
                );
            }

            log("Producto seleccionado", {
                id: product.id,
                code: product.code || "",
            });

            hideResults();
        }

        function displayProducts(products) {
            results.replaceChildren();
            results.hidden = false;
            picker.classList.add("pc-picker-open");

            if (!products.length) {
                showMessage(
                    "No encontramos productos relacionados. " +
                    "Pruebe con otra parte del nombre, modelo o código."
                );
                return;
            }

            for (const product of products) {
                const option = document.createElement("button");
                option.type = "button";
                option.className = "pc-search-option";

                const heading = document.createElement("span");
                heading.className = "pc-search-option-title";
                heading.textContent = product.name;

                const info = document.createElement("span");
                info.className = "pc-search-option-info";
                info.textContent = [
                    product.code,
                    product.description,
                ].filter(Boolean).join(" · ");

                const amount = document.createElement("span");
                amount.className = "pc-search-option-price";
                amount.textContent = product.price != null
                    ? `Precio base: ${product.price}`
                    : "";

                option.append(heading, info, amount);
                option.addEventListener(
                    "click",
                    () => selectProduct(product)
                );
                results.appendChild(option);
            }
        }

        async function search(term) {
            activeRequest?.abort();
            activeRequest = new AbortController();
            const currentRequest = ++requestNumber;

            const url = new URL(
                "/my/commercial/products/search",
                window.location.origin
            );
            url.searchParams.set("q", term);

            if (orderId) {
                url.searchParams.set("order_id", orderId);
            } else {
                url.searchParams.set("invoice_id", invoiceId);
            }

            // Se registra la longitud, no el texto introducido.
            log("Solicitando productos", {
                characters: term.length,
                request: currentRequest,
            });
            showMessage("Buscando productos…");

            try {
                const response = await fetch(url, {
                    credentials: "same-origin",
                    signal: activeRequest.signal,
                    headers: {
                        Accept: "application/json",
                    },
                });

                log("Respuesta del servidor", {
                    status: response.status,
                    request: currentRequest,
                });

                if (!response.ok) {
                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }

                const data = await response.json();
                if (currentRequest !== requestNumber) {
                    return;
                }

                const products = Array.isArray(data.products)
                    ? data.products
                    : [];

                log("Resultados recibidos", {
                    count: products.length,
                    request: currentRequest,
                });
                displayProducts(products);
            } catch (error) {
                if (error.name === "AbortError") {
                    log("Búsqueda anterior cancelada");
                    return;
                }

                fail("Error buscando productos", error);
                showMessage(
                    "No se pudo consultar el catálogo. " +
                    "Revise la consola y la pestaña Red."
                );
            }
        }

        input.addEventListener("input", () => {
            productId.value = "";
            clearTimeout(debounceTimer);

            const term = input.value.trim();
            log("Campo modificado", {
                characters: term.length,
            });

            if (term.length < 2) {
                activeRequest?.abort();
                hideResults();
                return;
            }

            debounceTimer = window.setTimeout(
                () => search(term),
                250
            );
        });

        input.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                hideResults();
            }
        });

        document.addEventListener("click", (event) => {
            if (!picker.contains(event.target)) {
                hideResults();
            }
        });

        form.addEventListener("submit", (event) => {
            if (productId.value) {
                return;
            }

            event.preventDefault();
            warn(
                "Se impidió agregar una línea sin " +
                "seleccionar un resultado"
            );
            input.setCustomValidity(
                "Seleccione un producto de los resultados."
            );
            input.reportValidity();
            input.setCustomValidity("");
            input.focus();
        });
    }

    function initialize() {
        const pickers = document.querySelectorAll(
            ".pc-product-picker"
        );
        log("Archivo JS cargado", {
            pickers: pickers.length,
            page: window.location.pathname,
        });

        for (const picker of pickers) {
            initializePicker(picker);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            { once: true }
        );
    } else {
        initialize();
    }
})();