/**
 * Copier Company - Homepage
 * JavaScript simplificado y seguro
 *
 * Funciones:
 * - Scroll suave para enlaces internos
 * - Elimina badges antiguos de "Performance" si aún aparecen por caché/assets
 * - Mantiene visible todo el contenido aunque el JS falle
 */

(function () {
    'use strict';

    /**
     * Inicializa scroll suave para enlaces internos tipo #seccion
     */
    function initSmoothScroll() {
        const links = document.querySelectorAll('a[href^="#"]');

        links.forEach(function (link) {
            link.addEventListener('click', function (event) {
                const href = link.getAttribute('href');

                if (!href || href === '#') {
                    return;
                }

                let target = null;

                try {
                    target = document.querySelector(href);
                } catch (error) {
                    return;
                }

                if (!target) {
                    return;
                }

                event.preventDefault();

                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            });
        });
    }

    /**
     * Elimina elementos antiguos relacionados con Performance.
     * Esto ayuda si Odoo todavía tiene algún asset viejo en caché.
     */
    function removeOldPerformanceElements() {
        const selectors = [
            '.performance-badge',
            '.performance-card',
            '.performance-widget',
            '#performance-badge',
            '#performance-card',
            '[data-performance]'
        ];

        selectors.forEach(function (selector) {
            document.querySelectorAll(selector).forEach(function (element) {
                element.remove();
            });
        });

        /**
         * También busca textos visibles que digan Performance
         * dentro de badges pequeños antiguos.
         */
        document.querySelectorAll('span, div, small').forEach(function (element) {
            const text = (element.textContent || '').trim().toLowerCase();

            if (text === 'performance') {
                const parent = element.closest(
                    '.badge, .card, .position-fixed, .position-absolute'
                );

                if (parent) {
                    parent.remove();
                }
            }
        });
    }

    /**
     * Asegura que las secciones de la página permanezcan visibles.
     * La página no depende de animaciones JS para mostrarse.
     */
    function ensureContentVisible() {
        document.querySelectorAll('.cc-reveal').forEach(function (element) {
            element.style.opacity = '1';
            element.style.transform = 'none';
            element.style.visibility = 'visible';
        });
    }

    /**
     * Inicialización general
     */
    function initHomepage() {
        initSmoothScroll();
        removeOldPerformanceElements();
        ensureContentVisible();

        /**
         * Segunda revisión por si Odoo inserta algún elemento
         * unos milisegundos después de cargar la página.
         */
        setTimeout(function () {
            removeOldPerformanceElements();
            ensureContentVisible();
        }, 500);

        setTimeout(function () {
            removeOldPerformanceElements();
        }, 1500);
    }

    /**
     * Ejecutar cuando el DOM esté disponible
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHomepage);
    } else {
        initHomepage();
    }
})();