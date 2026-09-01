/**
 * Copier Company - Homepage
 * JavaScript seguro y simplificado.
 *
 * IMPORTANTE:
 * La visibilidad del contenido NO depende de este archivo.
 * Si este JS no carga, toda la página seguirá mostrándose normalmente.
 */

(function () {
    'use strict';

    function initSmoothInternalLinks() {
        var links = document.querySelectorAll('a[href^="#"]');

        links.forEach(function (link) {
            link.addEventListener('click', function (event) {
                var selector = link.getAttribute('href');

                if (!selector || selector === '#') {
                    return;
                }

                var target;

                try {
                    target = document.querySelector(selector);
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSmoothInternalLinks);
    } else {
        initSmoothInternalLinks();
    }
})();
