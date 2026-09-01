/**
 * Copier Company - Homepage
 * JavaScript simplificado para la página de inicio.
 *
 * La nueva portada no utiliza modales, datos inventados,
 * animaciones pesadas ni contenido dinámico de productos/marcas.
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initRevealAnimation();
        initSmoothInternalLinks();
    });

    /**
     * Animación discreta al mostrar bloques.
     * Si IntersectionObserver no está disponible, se muestran directamente.
     */
    function initRevealAnimation() {
        const elements = document.querySelectorAll('.cc-reveal');

        if (!elements.length) {
            return;
        }

        if (!('IntersectionObserver' in window)) {
            elements.forEach(function (element) {
                element.classList.add('cc-visible');
            });
            return;
        }

        const observer = new IntersectionObserver(
            function (entries, currentObserver) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    entry.target.classList.add('cc-visible');
                    currentObserver.unobserve(entry.target);
                });
            },
            {
                threshold: 0.12,
                rootMargin: '0px 0px -40px 0px'
            }
        );

        elements.forEach(function (element) {
            observer.observe(element);
        });
    }

    /**
     * Scroll suave únicamente para enlaces internos de la misma página (#...).
     */
    function initSmoothInternalLinks() {
        const internalLinks = document.querySelectorAll('a[href^="#"]');

        internalLinks.forEach(function (link) {
            link.addEventListener('click', function (event) {
                const selector = link.getAttribute('href');

                if (!selector || selector === '#') {
                    return;
                }

                const target = document.querySelector(selector);

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
})();
