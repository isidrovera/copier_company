/**
 * Copier Company
 * Homepage
 *
 * JavaScript mínimo.
 *
 * Este archivo:
 * - NO modifica estilos.
 * - NO crea botones flotantes.
 * - NO toca el chat de Odoo.
 * - NO contiene Performance.
 * - NO oculta secciones.
 * - NO utiliza animaciones que puedan dejar espacios en blanco.
 */

(function () {

    'use strict';


    /**
     * Scroll suave únicamente para enlaces internos.
     *
     * Ejemplo:
     * href="#servicios"
     */
    function initSmoothScroll() {

        const links =
            document.querySelectorAll(
                'a[href^="#"]'
            );


        links.forEach(function (link) {

            link.addEventListener(
                'click',
                function (event) {

                    const href =
                        this.getAttribute(
                            'href'
                        );


                    if (
                        !href ||
                        href === '#'
                    ) {
                        return;
                    }


                    let target = null;


                    try {

                        target =
                            document.querySelector(
                                href
                            );

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

                }
            );

        });

    }


    /**
     * Inicialización.
     */
    function initHomepage() {

        initSmoothScroll();

    }


    /**
     * Ejecutar cuando el DOM esté listo.
     */
    if (
        document.readyState ===
        'loading'
    ) {

        document.addEventListener(
            'DOMContentLoaded',
            initHomepage
        );

    } else {

        initHomepage();

    }


})();