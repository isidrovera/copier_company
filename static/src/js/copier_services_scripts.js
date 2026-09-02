/**
 * Copier Company
 * Servicios
 *
 * Animaciones suaves y seguras
 * - scroll suave
 * - reveal al entrar en pantalla
 * - sin modales
 * - sin tocar el chat de Odoo
 */

(function () {
    'use strict';

    function initSmoothScroll() {
        const links = document.querySelectorAll('a[href^="#"]');

        links.forEach(function (link) {
            link.addEventListener('click', function (event) {
                const href = this.getAttribute('href');

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

    function initRevealAnimations() {
        const items = document.querySelectorAll('.cc-reveal');

        if (!items.length) {
            return;
        }

        if (!('IntersectionObserver' in window)) {
            items.forEach(function (item) {
                item.classList.add('cc-visible');
            });
            return;
        }

        const observer = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('cc-visible');
                    obs.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -40px 0px'
        });

        items.forEach(function (item) {
            observer.observe(item);
        });
    }

    function initServicesPage() {
        initSmoothScroll();
        initRevealAnimations();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initServicesPage);
    } else {
        initServicesPage();
    }
})();