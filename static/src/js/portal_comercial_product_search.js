/** @odoo-module **/

(function () {
    "use strict";

    function initSearch(container) {
        const input = container.querySelector(".pc-product-search");
        const results = container.querySelector(".pc-search-results");
        const productId = container.querySelector(
            'input[name="product_id"]'
        );
        const description = container.querySelector(
            '[name="description"]'
        );
        const price = container.querySelector(
            '[name="price_unit"]'
        );
        const taxInputs = container.querySelectorAll(
            'input[name="tax_ids"]'
        );
        const form = container.closest("form");

        if (!input || !results || !productId || !form) {
            return;
        }

        let timer = null;
        let controller = null;
        let sequence = 0;

        function clearResults() {
            results.replaceChildren();
            results.hidden = true;
        }

        function invalidateSelection() {
            productId.value = "";
        }

        function selectProduct(product) {
            productId.value = String(product.id);
            input.value = product.name;
            if (description) {
                description.value = product.description || product.name;
            }
            if (price) {
                price.value = String(product.price ?? 0);
            }

            const defaultTaxes = new Set(
                (product.tax_ids || []).map(Number)
            );
            for (const checkbox of taxInputs) {
                checkbox.checked = defaultTaxes.has(
                    Number(checkbox.value)
                );
            }

            clearResults();
            input.focus();
        }

        function showProducts(products) {
            clearResults();
            results.hidden = false;

            if (!products.length) {
                const empty = document.createElement("div");
                empty.className = "pc-search-empty";
                empty.textContent =
                    "No se encontraron productos relacionados";
                results.appendChild(empty);
                return;
            }

            for (const product of products) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "pc-search-option";

                const title = document.createElement("strong");
                title.textContent = product.name;
                button.appendChild(title);

                const extra = document.createElement("small");
                extra.textContent = [
                    product.code || "",
                    product.description || "",
                ].filter(Boolean).join(" · ");
                button.appendChild(extra);

                button.addEventListener("click", () => {
                    selectProduct(product);
                });
                results.appendChild(button);
            }
        }

        async function search(term) {
            if (controller) {
                controller.abort();
            }
            controller = new AbortController();
            const current = ++sequence;

            const url = new URL(
                "/my/commercial/products/search",
                window.location.origin
            );
            url.searchParams.set("q", term);

            const orderId = container.dataset.orderId;
            const invoiceId = container.dataset.invoiceId;

            if (orderId) {
                url.searchParams.set("order_id", orderId);
            } else if (invoiceId) {
                url.searchParams.set("invoice_id", invoiceId);
            } else {
                return;
            }

            try {
                const response = await fetch(url, {
                    credentials: "same-origin",
                    signal: controller.signal,
                    headers: {
                        Accept: "application/json",
                    },
                });
                if (!response.ok) {
                    throw new Error("Search failed");
                }
                const data = await response.json();
                if (current === sequence) {
                    showProducts(data.products || []);
                }
            } catch (error) {
                if (error.name !== "AbortError") {
                    clearResults();
                }
            }
        }

        input.addEventListener("input", () => {
            invalidateSelection();
            clearTimeout(timer);

            const term = input.value.trim();
            if (term.length < 2) {
                if (controller) {
                    controller.abort();
                }
                clearResults();
                return;
            }

            timer = window.setTimeout(() => {
                search(term);
            }, 250);
        });

        input.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                clearResults();
            }
        });

        document.addEventListener("click", (event) => {
            if (!container.contains(event.target)) {
                clearResults();
            }
        });

        form.addEventListener("submit", (event) => {
            if (!productId.value) {
                event.preventDefault();
                input.setCustomValidity(
                    "Seleccione un producto de los resultados"
                );
                input.reportValidity();
                input.setCustomValidity("");
            }
        });
    }

    function init() {
        document.querySelectorAll(
            ".pc-product-picker"
        ).forEach(initSearch);
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