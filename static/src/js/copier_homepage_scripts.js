/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 1/10: Inicialización y Variables Globales
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // VARIABLES GLOBALES
    // ====================================
    let isScrolling = false;
    let scrollTimeout;
    let lastScrollY = 0;
    let ticking = false;

    // Configuration
    const config = {
        animationDuration: 300,
        scrollThreshold: 100,
        parallaxSpeed: 0.05,
        debounceDelay: 250,
        throttleDelay: 100
    };

    // ====================================
    // INICIALIZACIÓN PRINCIPAL
    // ====================================
    document.addEventListener('DOMContentLoaded', function() {
        initializeHomepage();
    });

    /**
     * Inicializa todas las funcionalidades de la homepage
     */
    function initializeHomepage() {
        // Solo ejecutar si estamos en la página con la clase correcta
        if (!document.querySelector('.copier-modern-homepage')) {
            return;
        }

        console.log('🚀 Inicializando Copier Company Homepage...');

        // Inicializar funcionalidades básicas
        initScrollAnimations();
        initScrollIndicator();
        initSmoothScrolling();
        initFloatingButtons();
        initPerformanceOptimizations();
        initAccessibility();

        console.log('✅ Homepage inicializada correctamente - Parte 1');
    }

    // ====================================
    // UTILIDADES BÁSICAS
    // ====================================

    /**
     * Detectar dispositivo móvil
     */
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * Detectar soporte para touch
     */
    function isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    /**
     * Throttle function
     */
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Debounce function
     */
    function debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    /**
     * Obtener información del dispositivo
     */
    function getDeviceInfo() {
        return {
            isMobile: isMobileDevice(),
            isTablet: /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent),
            isTouch: isTouchDevice(),
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight,
            pixelRatio: window.devicePixelRatio || 1
        };
    }

    // Hacer funciones disponibles globalmente para las otras partes
    window.copierHomepagePart1 = {
        isMobileDevice,
        isTouchDevice,
        throttle,
        debounce,
        getDeviceInfo,
        initializeHomepage,
        config
    };

    // Debug info
    console.log('📦 Copier Homepage - Parte 1 cargada (Inicialización y Variables)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 2/10: Animaciones y Efectos de Scroll
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // ANIMACIONES ON SCROLL
    // ====================================
    function initScrollAnimations() {
        // Configuración del Intersection Observer
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        // Observer para animaciones de entrada
        const animationObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Agregar delay escalonado para elementos en grid
                    if (entry.target.parentElement.classList.contains('benefits-grid') ||
                        entry.target.parentElement.classList.contains('brands-grid') ||
                        entry.target.parentElement.classList.contains('products-grid')) {
                        
                        const siblings = Array.from(entry.target.parentElement.children);
                        const index = siblings.indexOf(entry.target);
                        entry.target.style.animationDelay = `${index * 0.1}s`;
                    }
                    
                    // Anunciar cambio para lectores de pantalla
                    if (window.announceToScreenReader) {
                        const title = entry.target.querySelector('h3, h2, h4')?.textContent;
                        if (title) {
                            window.announceToScreenReader(`Sección ${title} visible`);
                        }
                    }
                }
            });
        }, observerOptions);

        // Observar elementos para animación
        const animatedElements = document.querySelectorAll(`
            .copier-modern-homepage .benefit-card,
            .copier-modern-homepage .brand-card,
            .copier-modern-homepage .product-card,
            .copier-modern-homepage .process-step,
            .copier-modern-homepage .testimonial-card,
            .copier-modern-homepage .section-header
        `);

        animatedElements.forEach(el => {
            el.classList.add('animate-fade-in');
            animationObserver.observe(el);
        });

        // Parallax ligero para elementos flotantes
        initParallaxEffect();
    }

    /**
     * Efecto parallax suave para elementos flotantes
     */
    function initParallaxEffect() {
        const floatingCards = document.querySelectorAll('.copier-modern-homepage .floating-card');
        
        if (floatingCards.length === 0) return;

        function updateParallax() {
            if (window.copierHomepagePart1.config.isScrolling) return;
            
            const scrolled = window.pageYOffset;
            const parallax = scrolled * window.copierHomepagePart1.config.parallaxSpeed;
            
            floatingCards.forEach((card, index) => {
                const speed = (index + 1) * 0.02;
                const yPos = parallax * speed;
                card.style.transform = `translateY(${yPos}px)`;
            });
        }

        // Throttle scroll events
        const throttledParallax = window.copierHomepagePart1.throttle(updateParallax, 16);
        
        window.addEventListener('scroll', function() {
            if (!window.copierHomepagePart1.config.isScrolling) {
                window.requestAnimationFrame(throttledParallax);
                window.copierHomepagePart1.config.isScrolling = true;
                
                clearTimeout(window.copierHomepagePart1.config.scrollTimeout);
                window.copierHomepagePart1.config.scrollTimeout = setTimeout(() => {
                    window.copierHomepagePart1.config.isScrolling = false;
                }, 100);
            }
        }, { passive: true });
    }

    // ====================================
    // SCROLL INDICATOR
    // ====================================
    function initScrollIndicator() {
        const scrollIndicator = document.querySelector('.copier-modern-homepage .scroll-indicator');
        
        if (!scrollIndicator) return;

        scrollIndicator.addEventListener('click', function() {
            const targetSection = document.querySelector('.copier-modern-homepage .benefits-section');
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Analytics tracking
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'scroll_indicator_click', {
                        event_category: 'navigation',
                        event_label: 'hero_to_benefits'
                    });
                }
            }
        });

        // Ocultar indicador después del scroll
        const throttledScrollHide = window.copierHomepagePart1.throttle(function() {
            if (window.pageYOffset > window.copierHomepagePart1.config.scrollThreshold) {
                scrollIndicator.style.opacity = '0';
            } else {
                scrollIndicator.style.opacity = '1';
            }
        }, window.copierHomepagePart1.config.throttleDelay);

        window.addEventListener('scroll', throttledScrollHide, { passive: true });
    }

    // ====================================
    // SMOOTH SCROLLING
    // ====================================
    function initSmoothScrolling() {
        // Smooth scrolling para todos los enlaces ancla
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                
                // Skip si es solo #
                if (targetId === '#') {
                    e.preventDefault();
                    return;
                }
                
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'anchor_click', {
                            event_category: 'navigation',
                            event_label: targetId
                        });
                    }
                }
            });
        });
    }

    // ====================================
    // CSS PARA ANIMACIONES
    // ====================================
    const animationStyles = `
        /* Animaciones de entrada */
        .animate-fade-in {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .animate-fade-in.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* Optimizaciones para dispositivos con movimiento reducido */
        @media (prefers-reduced-motion: reduce) {
            .animate-fade-in {
                animation: none;
                transform: none;
                transition: opacity 0.3s ease;
            }
        }

        /* Optimizaciones para móviles */
        .mobile-device .floating-card {
            transform: none !important;
        }

        /* Scroll indicator */
        .scroll-indicator {
            transition: opacity 0.3s ease;
            cursor: pointer;
        }

        .scroll-indicator:hover {
            opacity: 0.8;
        }

        /* Floating cards */
        .floating-card {
            will-change: transform;
        }

        /* Performance optimizations */
        .copier-modern-homepage {
            contain: layout style paint;
        }
    `;

    // Inyectar estilos de animaciones
    const animationStyleSheet = document.createElement('style');
    animationStyleSheet.textContent = animationStyles;
    document.head.appendChild(animationStyleSheet);

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart2 = {
        initScrollAnimations,
        initParallaxEffect,
        initScrollIndicator,
        initSmoothScrolling
    };

    // Debug info
    console.log('📦 Copier Homepage - Parte 2 cargada (Animaciones y Scroll)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 3/10: Botones Flotantes y Navegación
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // BOTONES FLOTANTES
    // ====================================
    function initFloatingButtons() {
        initWhatsAppButton();
        initQuoteButton();
    }

    /**
     * Botón flotante de WhatsApp
     */
    function initWhatsAppButton() {
        const whatsappBtn = document.querySelector('.copier-modern-homepage .whatsapp-btn');
        
        if (!whatsappBtn) return;

        // Agregar funcionalidad de tracking
        whatsappBtn.addEventListener('click', function(e) {
            // Analytics tracking
            if (typeof gtag !== 'undefined') {
                gtag('event', 'whatsapp_click', {
                    event_category: 'contact',
                    event_label: 'floating_button'
                });
            }
            
            console.log('WhatsApp button clicked');
        });

        // Mostrar/ocultar según scroll con mejor performance
        const throttledWhatsAppScroll = window.copierHomepagePart1.throttle(function() {
            const currentScrollY = window.pageYOffset;
            const btnContainer = whatsappBtn.parentElement;
            
            if (currentScrollY > 300) {
                if (currentScrollY < window.copierHomepagePart1.config.lastScrollY) {
                    // Scrolling up
                    btnContainer.style.transform = 'translateY(0)';
                    btnContainer.style.opacity = '1';
                } else {
                    // Scrolling down
                    btnContainer.style.transform = 'translateY(100px)';
                    btnContainer.style.opacity = '0.7';
                }
            } else {
                btnContainer.style.transform = 'translateY(0)';
                btnContainer.style.opacity = '1';
            }
            
            window.copierHomepagePart1.config.lastScrollY = currentScrollY;
        }, 16);

        window.addEventListener('scroll', throttledWhatsAppScroll, { passive: true });
    }

    /**
     * Botón flotante de cotización
     */
    function initQuoteButton() {
        const quoteBtn = document.querySelector('.copier-modern-homepage .quote-btn');
        
        if (!quoteBtn) return;

        // Agregar funcionalidad de tracking
        quoteBtn.addEventListener('click', function(e) {
            // Analytics tracking
            if (typeof gtag !== 'undefined') {
                gtag('event', 'quote_button_click', {
                    event_category: 'conversion',
                    event_label: 'floating_button'
                });
            }
            
            console.log('Quote button clicked');
        });

        // Efecto de pulsación periódica más suave
        let pulseInterval;
        
        function startPulseAnimation() {
            pulseInterval = setInterval(() => {
                if (document.visibilityState === 'visible') {
                    quoteBtn.style.animation = 'none';
                    requestAnimationFrame(() => {
                        quoteBtn.style.animation = 'pulse 0.5s ease-in-out';
                    });
                }
            }, 10000); // Cada 10 segundos
        }

        function stopPulseAnimation() {
            if (pulseInterval) {
                clearInterval(pulseInterval);
            }
        }

        // Iniciar animación
        startPulseAnimation();

        // Pausar animación cuando la página no está visible
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopPulseAnimation();
            } else {
                startPulseAnimation();
            }
        });

        // Limpiar interval al salir de la página
        window.addEventListener('beforeunload', stopPulseAnimation);
    }

    // ====================================
    // NAVEGACIÓN MEJORADA
    // ====================================
    function initEnhancedNavigation() {
        // Back to top button
        initBackToTopButton();
        
        // Section navigation
        initSectionNavigation();
        
        // Keyboard navigation
        initKeyboardNavigation();
    }

    /**
     * Botón back to top
     */
    function initBackToTopButton() {
        // Crear botón si no existe
        let backToTopBtn = document.querySelector('.back-to-top');
        
        if (!backToTopBtn) {
            backToTopBtn = document.createElement('button');
            backToTopBtn.className = 'back-to-top';
            backToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
            backToTopBtn.setAttribute('aria-label', 'Volver arriba');
            backToTopBtn.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            `;
            document.body.appendChild(backToTopBtn);
        }

        // Mostrar/ocultar según scroll
        const throttledBackToTop = window.copierHomepagePart1.throttle(function() {
            if (window.pageYOffset > 500) {
                backToTopBtn.style.opacity = '1';
                backToTopBtn.style.visibility = 'visible';
            } else {
                backToTopBtn.style.opacity = '0';
                backToTopBtn.style.visibility = 'hidden';
            }
        }, 100);

        window.addEventListener('scroll', throttledBackToTop, { passive: true });

        // Funcionalidad del botón
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });

            if (typeof gtag !== 'undefined') {
                gtag('event', 'back_to_top_click', {
                    event_category: 'navigation',
                    event_label: 'floating_button'
                });
            }
        });
    }

    /**
     * Navegación entre secciones
     */
    function initSectionNavigation() {
        const sections = document.querySelectorAll('.copier-modern-homepage section[id]');
        
        if (sections.length === 0) return;

        // Crear navegación lateral si no existe
        let sectionNav = document.querySelector('.section-navigation');
        
        if (!sectionNav && sections.length > 3) {
            sectionNav = document.createElement('nav');
            sectionNav.className = 'section-navigation';
            sectionNav.setAttribute('aria-label', 'Navegación de secciones');
            sectionNav.style.cssText = `
                position: fixed;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            `;

            const navList = document.createElement('ul');
            navList.style.cssText = `
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;

            sections.forEach((section, index) => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = `#${section.id}`;
                link.className = 'section-nav-link';
                link.setAttribute('aria-label', `Ir a sección ${index + 1}`);
                link.style.cssText = `
                    display: block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.5);
                    border: 2px solid #667eea;
                    transition: all 0.3s ease;
                    text-decoration: none;
                `;
                
                li.appendChild(link);
                navList.appendChild(li);
            });

            sectionNav.appendChild(navList);
            document.body.appendChild(sectionNav);

            // Mostrar navegación después del primer scroll
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 200) {
                    sectionNav.style.opacity = '1';
                    sectionNav.style.visibility = 'visible';
                }
            }, { passive: true, once: true });
        }

        // Observer para resaltar sección actual
        const navObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Remover active de todos los links
                    document.querySelectorAll('.section-nav-link').forEach(link => {
                        link.style.background = 'rgba(255,255,255,0.5)';
                    });
                    
                    // Agregar active al link correspondiente
                    const activeLink = document.querySelector(`.section-nav-link[href="#${entry.target.id}"]`);
                    if (activeLink) {
                        activeLink.style.background = '#667eea';
                    }
                }
            });
        }, { threshold: 0.6 });

        sections.forEach(section => navObserver.observe(section));
    }

    /**
     * Navegación por teclado
     */
    function initKeyboardNavigation() {
        document.addEventListener('keydown', function(e) {
            // ESC para cerrar modales
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const bsModal = bootstrap.Modal.getInstance(openModal);
                    if (bsModal) {
                        bsModal.hide();
                    }
                }
            }
            
            // Navegación con flechas (Alt + Arrow)
            if (e.altKey) {
                const sections = document.querySelectorAll('.copier-modern-homepage section[id]');
                const currentSection = getCurrentSection(sections);
                
                if (e.key === 'ArrowDown' && currentSection < sections.length - 1) {
                    e.preventDefault();
                    sections[currentSection + 1].scrollIntoView({ behavior: 'smooth' });
                } else if (e.key === 'ArrowUp' && currentSection > 0) {
                    e.preventDefault();
                    sections[currentSection - 1].scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }

    /**
     * Obtener sección actual
     */
    function getCurrentSection(sections) {
        const scrollPosition = window.pageYOffset + window.innerHeight / 2;
        
        for (let i = 0; i < sections.length; i++) {
            const section = sections[i];
            const sectionTop = section.offsetTop;
            const sectionBottom = sectionTop + section.offsetHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition <= sectionBottom) {
                return i;
            }
        }
        
        return 0;
    }

    // ====================================
    // CSS PARA BOTONES FLOTANTES
    // ====================================
    const floatingStyles = `
        /* Botones flotantes */
        .whatsapp-btn, .quote-btn {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            will-change: transform, opacity;
        }

        .whatsapp-btn:hover, .quote-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        /* Animación de pulso para quote button */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        /* Back to top button */
        .back-to-top:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }

        /* Section navigation */
        .section-nav-link:hover {
            background: #667eea !important;
            transform: scale(1.3);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .section-navigation {
                display: none;
            }
            
            .back-to-top {
                bottom: 80px;
                right: 20px;
                left: auto;
            }
        }

        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {
            .whatsapp-btn, .quote-btn, .back-to-top, .section-nav-link {
                transition: none;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
            }
        }
    `;

    // Inyectar estilos
    const floatingStyleSheet = document.createElement('style');
    floatingStyleSheet.textContent = floatingStyles;
    document.head.appendChild(floatingStyleSheet);

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart3 = {
        initFloatingButtons,
        initWhatsAppButton,
        initQuoteButton,
        initEnhancedNavigation,
        initBackToTopButton,
        initSectionNavigation,
        initKeyboardNavigation
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initFloatingButtons();
            initEnhancedNavigation();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 3 cargada (Botones Flotantes y Navegación)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 4/10: Optimizaciones de Performance y Accesibilidad
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // OPTIMIZACIONES DE PERFORMANCE
    // ====================================
    function initPerformanceOptimizations() {
        initLazyLoading();
        initResourcePreloading();
        initScrollOptimizations();
        initImageOptimizations();
        initNetworkOptimizations();
    }

    /**
     * Lazy loading para imágenes y contenido
     */
    function initLazyLoading() {
        if ('IntersectionObserver' in window) {
            // Lazy loading para imágenes
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        
                        // Cargar imagen
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        
                        // Cargar srcset si existe
                        if (img.dataset.srcset) {
                            img.srcset = img.dataset.srcset;
                            img.removeAttribute('data-srcset');
                        }
                        
                        img.classList.add('loaded');
                        observer.unobserve(img);
                        
                        // Analytics para lazy loading
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'image_lazy_loaded', {
                                event_category: 'performance',
                                event_label: img.alt || 'unnamed_image'
                            });
                        }
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            // Observar imágenes con data-src
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });

            // Lazy loading para contenido pesado
            const contentObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        
                        if (element.dataset.lazyContent) {
                            loadLazyContent(element);
                        }
                        
                        observer.unobserve(element);
                    }
                });
            }, {
                rootMargin: '100px 0px',
                threshold: 0.1
            });

            document.querySelectorAll('[data-lazy-content]').forEach(el => {
                contentObserver.observe(el);
            });
        }
    }

    /**
     * Cargar contenido lazy
     */
    function loadLazyContent(element) {
        const contentUrl = element.dataset.lazyContent;
        
        if (contentUrl) {
            fetch(contentUrl)
                .then(response => response.text())
                .then(html => {
                    element.innerHTML = html;
                    element.removeAttribute('data-lazy-content');
                    element.classList.add('lazy-loaded');
                    
                    // Reinicializar scripts si es necesario
                    const scripts = element.querySelectorAll('script');
                    scripts.forEach(script => {
                        const newScript = document.createElement('script');
                        newScript.textContent = script.textContent;
                        script.parentNode.replaceChild(newScript, script);
                    });
                    
                    console.log(`📦 Loaded lazy content for: ${element.className}`);
                })
                .catch(error => {
                    console.error('❌ Error loading lazy content:', error);
                    element.innerHTML = '<p>Error cargando contenido</p>';
                });
        }
    }

    /**
     * Preload de recursos críticos
     */
    function initResourcePreloading() {
        const criticalResources = [
            '/cotizacion/form',
            '/contactus',
            '/our-services'
        ];

        // Preload pages
        criticalResources.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });

        // Preload fonts críticas
        const criticalFonts = [
            '/fonts/inter-var.woff2',
            '/fonts/poppins-600.woff2'
        ];

        criticalFonts.forEach(fontUrl => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'font';
            link.type = 'font/woff2';
            link.href = fontUrl;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });

        // Preload next likely page based on user behavior
        initIntelligentPreloading();
    }

    /**
     * Preloading inteligente basado en comportamiento
     */
    function initIntelligentPreloading() {
        let hoveredLinks = new Set();
        let mouseIdleTimer;

        document.addEventListener('mouseover', function(e) {
            const link = e.target.closest('a[href]');
            if (link && link.hostname === window.location.hostname) {
                clearTimeout(mouseIdleTimer);
                
                mouseIdleTimer = setTimeout(() => {
                    if (!hoveredLinks.has(link.href)) {
                        hoveredLinks.add(link.href);
                        
                        const prefetchLink = document.createElement('link');
                        prefetchLink.rel = 'prefetch';
                        prefetchLink.href = link.href;
                        document.head.appendChild(prefetchLink);
                        
                        console.log(`🎯 Intelligent prefetch: ${link.href}`);
                    }
                }, 300);
            }
        });
    }

    /**
     * Optimizaciones de scroll
     */
    function initScrollOptimizations() {
        let ticking = false;

        function updateScrollEffects() {
            // Batch DOM reads and writes
            const scrollY = window.pageYOffset;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            // Update scroll-dependent elements efficiently
            requestAnimationFrame(() => {
                // Update progress bar if exists
                const progressBar = document.querySelector('.scroll-progress');
                if (progressBar) {
                    const progress = (scrollY / (documentHeight - windowHeight)) * 100;
                    progressBar.style.width = `${Math.min(progress, 100)}%`;
                }
                
                ticking = false;
            });
        }

        window.addEventListener('scroll', function() {
            if (!ticking) {
                requestAnimationFrame(updateScrollEffects);
                ticking = true;
            }
        }, { passive: true });
    }

    /**
     * Optimizaciones de imágenes
     */
    function initImageOptimizations() {
        // WebP detection y fallback
        function supportsWebP() {
            const canvas = document.createElement('canvas');
            canvas.width = 1;
            canvas.height = 1;
            return canvas.toDataURL('image/webp').indexOf('webp') > -1;
        }

        if (supportsWebP()) {
            document.documentElement.classList.add('webp-support');
        }

        // Optimize images based on connection speed
        if ('connection' in navigator) {
            const connection = navigator.connection;
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                document.documentElement.classList.add('slow-connection');
            }
        }
    }

    /**
     * Optimizaciones de red
     */
    function initNetworkOptimizations() {
        // Service Worker registration for caching
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('🔧 Service Worker registered:', registration);
                    })
                    .catch(error => {
                        console.log('❌ Service Worker registration failed:', error);
                    });
            });
        }

        // Network status monitoring
        function updateOnlineStatus() {
            const isOnline = navigator.onLine;
            document.documentElement.classList.toggle('offline', !isOnline);
            
            if (!isOnline) {
                showOfflineMessage();
            } else {
                hideOfflineMessage();
            }
        }

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
    }

    /**
     * Mostrar mensaje offline
     */
    function showOfflineMessage() {
        let offlineMessage = document.querySelector('.offline-message');
        
        if (!offlineMessage) {
            offlineMessage = document.createElement('div');
            offlineMessage.className = 'offline-message';
            offlineMessage.innerHTML = `
                <div class="offline-content">
                    <i class="fas fa-wifi-slash"></i>
                    <span>Sin conexión a internet</span>
                </div>
            `;
            offlineMessage.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #dc3545;
                color: white;
                padding: 10px;
                text-align: center;
                z-index: 10000;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
            `;
            document.body.appendChild(offlineMessage);
        }
        
        setTimeout(() => {
            offlineMessage.style.transform = 'translateY(0)';
        }, 100);
    }

    /**
     * Ocultar mensaje offline
     */
    function hideOfflineMessage() {
        const offlineMessage = document.querySelector('.offline-message');
        if (offlineMessage) {
            offlineMessage.style.transform = 'translateY(-100%)';
            setTimeout(() => {
                offlineMessage.remove();
            }, 300);
        }
    }

    // ====================================
    // ACCESIBILIDAD
    // ====================================
    function initAccessibility() {
        initKeyboardNavigation();
        initScreenReaderSupport();
        initFocusManagement();
        initARIALabels();
        initSkipLinks();
        initColorContrastEnhancements();
    }

    /**
     * Navegación por teclado para cards
     */
    function initKeyboardNavigation() {
        const clickableCards = document.querySelectorAll(`
            .copier-modern-homepage .benefit-card,
            .copier-modern-homepage .brand-card,
            .copier-modern-homepage .product-card,
            .copier-modern-homepage .service-card
        `);

        clickableCards.forEach(card => {
            // Hacer focuseable
            if (!card.hasAttribute('tabindex')) {
                card.setAttribute('tabindex', '0');
            }

            // Agregar atributos ARIA
            card.setAttribute('role', 'button');
            const titleElement = card.querySelector('h3, h4, h5');
            const title = titleElement ? titleElement.textContent : 'elemento';
            card.setAttribute('aria-label', `Ver detalles de ${title}`);

            // Manejar eventos de teclado
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });

            // Indicadores visuales de focus
            card.addEventListener('focus', function() {
                this.classList.add('keyboard-focused');
            });

            card.addEventListener('blur', function() {
                this.classList.remove('keyboard-focused');
            });
        });
    }

    /**
     * Soporte para lectores de pantalla
     */
    function initScreenReaderSupport() {
        // Crear contenedor para anuncios
        const announcements = document.createElement('div');
        announcements.setAttribute('aria-live', 'polite');
        announcements.setAttribute('aria-atomic', 'true');
        announcements.className = 'sr-only';
        announcements.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(announcements);

        // Función global para anunciar cambios
        window.announceToScreenReader = function(message) {
            announcements.textContent = message;
            setTimeout(() => {
                announcements.textContent = '';
            }, 1000);
        };

        // Anunciar carga de página
        window.addEventListener('load', function() {
            window.announceToScreenReader('Página de Copier Company cargada completamente');
        });
    }

    /**
     * Gestión de focus
     */
    function initFocusManagement() {
        // Focus trap para modales
        document.addEventListener('shown.bs.modal', function(e) {
            const modal = e.target;
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            }
        });

        // Restore focus cuando se cierra modal
        let lastFocusedElement;
        
        document.addEventListener('show.bs.modal', function(e) {
            lastFocusedElement = document.activeElement;
        });

        document.addEventListener('hidden.bs.modal', function(e) {
            if (lastFocusedElement) {
                lastFocusedElement.focus();
            }
        });
    }

    /**
     * Etiquetas ARIA mejoradas
     */
    function initARIALabels() {
        // Agregar descripciones ARIA a elementos interactivos
        const interactiveElements = document.querySelectorAll('button, a, [role="button"]');
        
        interactiveElements.forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                const text = element.textContent.trim();
                const icon = element.querySelector('i');
                
                if (icon && !text) {
                    // Elementos solo con iconos
                    if (icon.classList.contains('fa-whatsapp')) {
                        element.setAttribute('aria-label', 'Contactar por WhatsApp');
                    } else if (icon.classList.contains('fa-quote')) {
                        element.setAttribute('aria-label', 'Solicitar cotización');
                    }
                }
            }
        });

        // Marcar decoraciones como aria-hidden
        const decorativeElements = document.querySelectorAll('.decoration, .bg-pattern, .shape');
        decorativeElements.forEach(el => {
            el.setAttribute('aria-hidden', 'true');
        });
    }

    /**
     * Skip links para navegación rápida
     */
    function initSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Saltar al contenido principal';
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px 12px;
            text-decoration: none;
            z-index: 10000;
            transition: top 0.3s;
            border-radius: 4px;
            font-weight: 600;
        `;

        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });

        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);

        // Agregar ID al contenido principal si no existe
        const heroSection = document.querySelector('.copier-modern-homepage .hero-section');
        if (heroSection && !heroSection.id) {
            heroSection.id = 'main-content';
        }
    }

    /**
     * Mejoras de contraste de color
     */
    function initColorContrastEnhancements() {
        // Detectar preferencia de alto contraste
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.documentElement.classList.add('high-contrast');
        }

        // Detectar preferencia de colores invertidos
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark-mode-preferred');
        }
    }

    // ====================================
    // CSS PARA PERFORMANCE Y ACCESIBILIDAD
    // ====================================
    const performanceStyles = `
        /* Performance optimizations */
        .loaded {
            transition: opacity 0.3s ease;
        }

        img[data-src] {
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        img.loaded {
            opacity: 1;
        }

        .lazy-loaded {
            animation: fadeInUp 0.6s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Accessibility improvements */
        .keyboard-focused {
            outline: 3px solid #667eea !important;
            outline-offset: 2px !important;
        }

        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        /* High contrast mode */
        .high-contrast {
            filter: contrast(1.5);
        }

        .high-contrast .btn {
            border: 2px solid currentColor !important;
        }

        /* Slow connection optimizations */
        .slow-connection img {
            background: #f0f0f0;
        }

        .slow-connection .floating-card {
            transform: none !important;
        }

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* Offline styles */
        .offline-content {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        /* Focus management */
        .modal:focus {
            outline: none;
        }

        /* Skip link */
        .skip-link:focus {
            outline: 2px solid #fff;
            outline-offset: 2px;
        }
    `;

    // Inyectar estilos
    const performanceStyleSheet = document.createElement('style');
    performanceStyleSheet.textContent = performanceStyles;
    document.head.appendChild(performanceStyleSheet);

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart4 = {
        initPerformanceOptimizations,
        initAccessibility,
        initLazyLoading,
        loadLazyContent,
        showOfflineMessage,
        hideOfflineMessage
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initPerformanceOptimizations();
            initAccessibility();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 4 cargada (Performance y Accesibilidad)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 5/10: Modales - Estructura y Datos de Beneficios
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // INICIALIZACIÓN DE MODALES
    // ====================================
    function initModals() {
        initBenefitModal();
        console.log('📦 Modales de beneficios inicializados');
    }

    // ====================================
    // DATOS DE BENEFICIOS
    // ====================================
    const benefitData = {
        'sin-inversion': {
            title: 'Sin Inversión Inicial',
            icon: 'fas fa-hand-holding-usd',
            content: `
                <div class="row">
                    <div class="col-md-6">
                        <h4><i class="fas fa-chart-line text-primary me-2"></i>Ventajas Financieras</h4>
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Preserva tu capital de trabajo</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Mejora tu flujo de caja</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Reduce riesgos de inversión</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Planificación presupuestaria predecible</li>
                        </ul>
                        
                        <div class="financial-comparison mt-4">
                            <h5>Comparación de Costos</h5>
                            <div class="comparison-table">
                                <div class="comparison-row">
                                    <span class="comparison-label">Compra directa:</span>
                                    <span class="comparison-value cost">$15,000 - $50,000</span>
                                </div>
                                <div class="comparison-row">
                                    <span class="comparison-label">Alquiler mensual:</span>
                                    <span class="comparison-value benefit">$300 - $800</span>
                                </div>
                                <div class="comparison-row">
                                    <span class="comparison-label">Capital liberado:</span>
                                    <span class="comparison-value highlight">$14,700 - $49,200</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h4><i class="fas fa-business-time text-primary me-2"></i>Beneficios Operativos</h4>
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Equipos disponibles inmediatamente</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Actualización tecnológica constante</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Mantenimiento incluido</li>
                            <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Soporte técnico especializado</li>
                        </ul>
                        
                        <div class="roi-calculator mt-4">
                            <h5>Calculadora de ROI</h5>
                            <div class="calculator-box">
                                <p><strong>Con el capital liberado podrías:</strong></p>
                                <div class="roi-options">
                                    <div class="roi-option">
                                        <i class="fas fa-chart-line text-success"></i>
                                        <span>Invertir en marketing (+15% ventas)</span>
                                    </div>
                                    <div class="roi-option">
                                        <i class="fas fa-users text-info"></i>
                                        <span>Contratar personal especializado</span>
                                    </div>
                                    <div class="roi-option">
                                        <i class="fas fa-expand text-warning"></i>
                                        <span>Expandir tu línea de productos</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="alert alert-info mt-3">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>¿Sabías que?</strong> Las empresas que optan por alquiler pueden destinar hasta un 40% más de capital a actividades core de su negocio.
                </div>
            `
        },
        
        'soporte-24-7': {
            title: 'Soporte Técnico 24/7',
            icon: 'fas fa-headset',
            content: `
                <div class="row">
                    <div class="col-md-4">
                        <div class="text-center mb-4">
                            <div class="support-icon mb-3">
                                <i class="fas fa-phone" style="font-size: 3rem; color: #667eea;"></i>
                            </div>
                            <h5>Línea Directa</h5>
                            <p class="text-muted">Atención inmediata para emergencias</p>
                            <span class="badge bg-success">Disponible 24/7</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center mb-4">
                            <div class="support-icon mb-3">
                                <i class="fas fa-laptop" style="font-size: 3rem; color: #667eea;"></i>
                            </div>
                            <h5>Soporte Remoto</h5>
                            <p class="text-muted">Conexión remota para diagnóstico rápido</p>
                            <span class="badge bg-primary">Respuesta en 15 min</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center mb-4">
                            <div class="support-icon mb-3">
                                <i class="fas fa-user-tie" style="font-size: 3rem; color: #667eea;"></i>
                            </div>
                            <h5>Visita Técnica</h5>
                            <p class="text-muted">Técnico especializado en sitio</p>
                            <span class="badge bg-warning">Máximo 4 horas</span>
                        </div>
                    </div>
                </div>
                
                <div class="support-process mt-4">
                    <h4><i class="fas fa-cogs text-primary me-2"></i>Proceso de Soporte</h4>
                    <div class="process-timeline">
                        <div class="timeline-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <h6>Contacto Inicial</h6>
                                <p>Llamas o escribes reportando el problema</p>
                                <small>Tiempo: Inmediato</small>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <h6>Diagnóstico</h6>
                                <p>Nuestro técnico realiza diagnóstico remoto</p>
                                <small>Tiempo: 5-15 minutos</small>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <h6>Solución</h6>
                                <p>Resolución remota o envío de técnico</p>
                                <small>Tiempo: 15 min - 4 horas</small>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <h6>Seguimiento</h6>
                                <p>Verificamos que todo funcione correctamente</p>
                                <small>Tiempo: 24 horas después</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h4><i class="fas fa-tools text-primary me-2"></i>Servicios Incluidos</h4>
                <div class="row">
                    <div class="col-md-6">
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Diagnóstico remoto</li>
                            <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Resolución de problemas</li>
                            <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Configuración de funciones</li>
                            <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Optimización de rendimiento</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Capacitación de usuarios</li>
                            <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Optimización de workflows</li>
                            <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Consultoría especializada</li>
                            <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Actualizaciones de software</li>
                        </ul>
                    </div>
                </div>
                
                <div class="support-stats mt-4">
                    <h5>Estadísticas de Nuestro Soporte</h5>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">98.5%</span>
                            <span class="stat-label">Problemas resueltos remotamente</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">12 min</span>
                            <span class="stat-label">Tiempo promedio de respuesta</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">99.2%</span>
                            <span class="stat-label">Satisfacción del cliente</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">2.3 hrs</span>
                            <span class="stat-label">Tiempo promedio de resolución</span>
                        </div>
                    </div>
                </div>
            `
        },
        
        'instalacion-rapida': {
            title: 'Instalación en 24 Horas',
            icon: 'fas fa-rocket',
            content: `
                <div class="installation-timeline">
                    <h4><i class="fas fa-clock text-primary me-2"></i>Cronograma de Instalación</h4>
                    <div class="timeline">
                        <div class="timeline-item">
                            <div class="timeline-icon bg-primary">
                                <i class="fas fa-calendar-check"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Día 0 - Programación</h5>
                                <p>Coordinamos la fecha y hora más conveniente para tu empresa</p>
                                <small class="text-muted">Misma semana de confirmación del contrato</small>
                                <div class="timeline-details">
                                    <span class="detail-badge">Llamada de coordinación</span>
                                    <span class="detail-badge">Evaluación de espacio</span>
                                    <span class="detail-badge">Preparación de equipos</span>
                                </div>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-icon bg-info">
                                <i class="fas fa-truck"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Entrega e Instalación Física</h5>
                                <p>Nuestro equipo técnico lleva e instala el equipo en tu oficina</p>
                                <small class="text-muted">2-4 horas promedio</small>
                                <div class="timeline-details">
                                    <span class="detail-badge">Transporte especializado</span>
                                    <span class="detail-badge">Instalación eléctrica</span>
                                    <span class="detail-badge">Ubicación óptima</span>
                                </div>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-icon bg-success">
                                <i class="fas fa-cogs"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Configuración Completa</h5>
                                <p>Configuramos red, usuarios, funciones especiales y preferencias</p>
                                <small class="text-muted">Incluye integración con sistemas existentes</small>
                                <div class="timeline-details">
                                    <span class="detail-badge">Configuración de red</span>
                                    <span class="detail-badge">Creación de usuarios</span>
                                    <span class="detail-badge">Integración con software</span>
                                </div>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-icon bg-warning">
                                <i class="fas fa-graduation-cap"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Capacitación del Personal</h5>
                                <p>Entrenamos a tu equipo en todas las funciones del equipo</p>
                                <small class="text-muted">Manual de usuario y video tutoriales incluidos</small>
                                <div class="timeline-details">
                                    <span class="detail-badge">Sesión práctica</span>
                                    <span class="detail-badge">Manual impreso</span>
                                    <span class="detail-badge">Acceso a tutoriales</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="installation-checklist mt-4">
                    <h4><i class="fas fa-list-check text-primary me-2"></i>Checklist de Instalación</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Preparativos Previos</h6>
                            <ul class="checklist">
                                <li>Espacio físico adecuado</li>
                                <li>Toma eléctrica estabilizada</li>
                                <li>Acceso a red de datos</li>
                                <li>Personal disponible para capacitación</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Lo que Incluimos</h6>
                            <ul class="checklist">
                                <li>Transporte e instalación</li>
                                <li>Configuración completa</li>
                                <li>Capacitación integral</li>
                                <li>Pruebas de funcionamiento</li>
                                <li>Documentación técnica</li>
                                <li>Soporte post-instalación</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-success mt-4">
                    <i class="fas fa-thumbs-up me-2"></i>
                    <strong>Garantía de funcionamiento:</strong> Tu equipo estará 100% operativo desde el primer día, o extendemos el período de prueba sin costo.
                </div>
                
                <div class="installation-benefits mt-4">
                    <h5>Beneficios de Nuestra Instalación Express</h5>
                    <div class="benefits-grid">
                        <div class="benefit-item">
                            <i class="fas fa-bolt text-warning"></i>
                            <div>
                                <h6>Rapidez</h6>
                                <p>Instalación completa en menos de 24 horas</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-user-tie text-primary"></i>
                            <div>
                                <h6>Profesionalismo</h6>
                                <p>Técnicos certificados y especializados</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-shield-alt text-success"></i>
                            <div>
                                <h6>Sin Interrupciones</h6>
                                <p>Instalación sin afectar tu operación diaria</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-graduation-cap text-info"></i>
                            <div>
                                <h6>Capacitación Incluida</h6>
                                <p>Tu equipo listo para usar todas las funciones</p>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        
        'mantenimiento-incluido': {
            title: 'Mantenimiento Incluido',
            icon: 'fas fa-cog',
            content: `
                <div class="row">
                    <div class="col-md-6">
                        <h4><i class="fas fa-calendar-alt text-primary me-2"></i>Mantenimiento Preventivo</h4>
                        <div class="maintenance-schedule">
                            <div class="schedule-item">
                                <span class="frequency monthly">Mensual</span>
                                <span class="task">Limpieza profunda y calibración</span>
                            </div>
                            <div class="schedule-item">
                                <span class="frequency quarterly">Trimestral</span>
                                <span class="task">Revisión completa de componentes</span>
                            </div>
                            <div class="schedule-item">
                                <span class="frequency biannual">Semestral</span>
                                <span class="task">Actualización de firmware</span>
                            </div>
                            <div class="schedule-item">
                                <span class="frequency annual">Anual</span>
                                <span class="task">Overhaul completo del sistema</span>
                            </div>
                        </div>
                        
                        <div class="maintenance-details mt-4">
                            <h6>Detalles del Mantenimiento Preventivo</h6>
                            <div class="detail-list">
                                <div class="detail-item">
                                    <i class="fas fa-broom text-info"></i>
                                    <span>Limpieza de rodillos y sensores</span>
                                </div>
                                <div class="detail-item">
                                    <i class="fas fa-tools text-warning"></i>
                                    <span>Lubricación de partes móviles</span>
                                </div>
                                <div class="detail-item">
                                    <i class="fas fa-search text-primary"></i>
                                    <span>Inspección de desgaste</span>
                                </div>
                                <div class="detail-item">
                                    <i class="fas fa-chart-line text-success"></i>
                                    <span>Optimización de rendimiento</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h4><i class="fas fa-tools text-primary me-2"></i>Mantenimiento Correctivo</h4>
                        <ul class="list-unstyled">
                            <li class="mb-3">
                                <i class="fas fa-wrench text-success me-2"></i>
                                <strong>Reparaciones</strong><br>
                                <small class="text-muted">Sin costo adicional, repuestos originales incluidos</small>
                            </li>
                            <li class="mb-3">
                                <i class="fas fa-exchange-alt text-success me-2"></i>
                                <strong>Reemplazo Temporal</strong><br>
                                <small class="text-muted">Equipo de respaldo mientras reparamos el tuyo</small>
                            </li>
                            <li class="mb-3">
                                <i class="fas fa-tint text-success me-2"></i>
                                <strong>Consumibles</strong><br>
                                <small class="text-muted">Toners y repuestos originales al mejor precio</small>
                            </li>
                            <li class="mb-3">
                                <i class="fas fa-clock text-success me-2"></i>
                                <strong>Urgencias 24/7</strong><br>
                                <small class="text-muted">Atención inmediata para problemas críticos</small>
                            </li>
                        </ul>
                        
                        <div class="maintenance-guarantee mt-4">
                            <h6>Garantía de Mantenimiento</h6>
                            <div class="guarantee-box">
                                <i class="fas fa-medal text-warning mb-2"></i>
                                <p><strong>Garantizamos que tu equipo funcionará al menos el 99% del tiempo.</strong></p>
                                <p class="small">Si no cumplimos este estándar, extendemos tu contrato sin costo o te devolvemos la diferencia proporcional.</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="service-stats row text-center mt-4">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <h3 class="text-primary">99.5%</h3>
                            <p>Tiempo de funcionamiento</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <h3 class="text-success">< 4h</h3>
                            <p>Tiempo de respuesta</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <h3 class="text-info">24/7</h3>
                            <p>Disponibilidad</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <h3 class="text-warning">0%</h3>
                            <p>Costos ocultos</p>
                        </div>
                    </div>
                </div>
                
                <div class="cost-comparison mt-4">
                    <h5>Comparación de Costos de Mantenimiento</h5>
                    <div class="comparison-table">
                        <div class="comparison-header">
                            <span>Servicio</span>
                            <span>Sin Contrato</span>
                            <span>Con Nuestro Plan</span>
                            <span>Ahorro</span>
                        </div>
                        <div class="comparison-row">
                            <span>Visita técnica</span>
                            <span class="cost">$150</span>
                            <span class="included">Incluido</span>
                            <span class="savings">$150</span>
                        </div>
                        <div class="comparison-row">
                            <span>Mantenimiento mensual</span>
                            <span class="cost">$200</span>
                            <span class="included">Incluido</span>
                            <span class="savings">$200</span>
                        </div>
                        <div class="comparison-row">
                            <span>Repuestos</span>
                            <span class="cost">$300-800</span>
                            <span class="included">Incluido</span>
                            <span class="savings">$300-800</span>
                        </div>
                        <div class="comparison-total">
                            <span><strong>Ahorro anual estimado:</strong></span>
                            <span></span>
                            <span></span>
                            <span class="total-savings"><strong>$2,400 - $4,800</strong></span>
                        </div>
                    </div>
                </div>
            `
        }
    };

    // ====================================
    // MODAL DE BENEFICIOS
    // ====================================
    function initBenefitModal() {
        const benefitCards = document.querySelectorAll('.copier-modern-homepage .benefit-card[data-benefit]');
        const modal = document.getElementById('benefitModal');
        const modalBody = document.getElementById('benefitModalBody');
        const modalTitle = document.querySelector('#benefitModal .modal-title');

        if (!modal || !modalBody || !modalTitle) {
            console.warn('⚠️ Modal elements not found');
            return;
        }

        benefitCards.forEach(card => {
            card.addEventListener('click', function() {
                const benefitKey = this.getAttribute('data-benefit');
                const data = benefitData[benefitKey];
                
                if (data) {
                    modalTitle.innerHTML = `<i class="${data.icon} me-2"></i>${data.title}`;
                    modalBody.innerHTML = data.content;
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'benefit_modal_open', {
                            event_category: 'engagement',
                            event_label: benefitKey
                        });
                    }
                    
                    // Agregar animación de entrada
                    setTimeout(() => {
                        modalBody.classList.add('animate-fade-in', 'visible');
                    }, 100);
                    
                    console.log(`📊 Benefit modal opened: ${benefitKey}`);
                } else {
                    console.warn(`⚠️ Benefit data not found for key: ${benefitKey}`);
                }
            });
        });

        // Limpiar animaciones al cerrar modal
        modal.addEventListener('hidden.bs.modal', function() {
            modalBody.classList.remove('animate-fade-in', 'visible');
        });

        // Mejorar accesibilidad del modal
        modal.addEventListener('shown.bs.modal', function() {
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
    }

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart5 = {
        initModals,
        initBenefitModal,
        benefitData
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initModals();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 5 cargada (Modales de Beneficios)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 6/10: Modales - Datos de Marcas y Productos
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // DATOS DE MARCAS
    // ====================================
    const brandData = {
        'konica': {
            title: 'Konica Minolta',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Konica_Minolta_logo.svg/320px-Konica_Minolta_logo.svg.png',
            content: `
                <div class="brand-showcase">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Konica_Minolta_logo.svg/320px-Konica_Minolta_logo.svg.png" alt="Konica Minolta" class="brand-logo-large mb-4"/>
                            <div class="brand-stats">
                                <div class="stat-item">
                                    <span class="stat-number">150+</span>
                                    <span class="stat-label">Años de experiencia</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">#1</span>
                                    <span class="stat-label">En innovación</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">49</span>
                                    <span class="stat-label">Países de presencia</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h4>Tecnología Japonesa de Vanguardia</h4>
                            <p class="lead">Konica Minolta combina más de 150 años de experiencia en imagen con tecnología de punta para ofrecer soluciones que transforman los espacios de trabajo.</p>
                            
                            <div class="feature-grid">
                                <div class="feature-item">
                                    <i class="fas fa-tachometer-alt text-primary"></i>
                                    <div>
                                        <h6>Alta Velocidad</h6>
                                        <p>Hasta 75 páginas por minuto en modelos profesionales</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-palette text-primary"></i>
                                    <div>
                                        <h6>Calidad Superior</h6>
                                        <p>Impresión a color con calidad fotográfica y precisión excepcional</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-shield-alt text-primary"></i>
                                    <div>
                                        <h6>Seguridad Avanzada</h6>
                                        <p>Encriptación y autenticación biométrica de última generación</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-leaf text-primary"></i>
                                    <div>
                                        <h6>Eco-Friendly</h6>
                                        <p>Bajo consumo energético y materiales 100% reciclables</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="technology-showcase mt-4">
                        <h4>Tecnologías Exclusivas</h4>
                        <div class="tech-tabs">
                            <div class="tech-tab active" data-tech="simitri">
                                <span>Simitri HD+</span>
                            </div>
                            <div class="tech-tab" data-tech="emperon">
                                <span>Emperon</span>
                            </div>
                            <div class="tech-tab" data-tech="biometric">
                                <span>Biometric Auth</span>
                            </div>
                        </div>
                        <div class="tech-content">
                            <div class="tech-pane active" id="simitri">
                                <h6><i class="fas fa-atom text-primary me-2"></i>Tecnología Simitri HD+</h6>
                                <p>Toner polimerizado que ofrece colores más vivos, texto más nítido y menor consumo energético. Partículas esféricas perfectas que se adhieren uniformemente al papel.</p>
                                <ul>
                                    <li>50% menos consumo de energía</li>
                                    <li>Mayor densidad de color</li>
                                    <li>Menor temperatura de fijación</li>
                                    <li>Impresión en papeles especiales</li>
                                </ul>
                            </div>
                            <div class="tech-pane" id="emperon">
                                <h6><i class="fas fa-microchip text-primary me-2"></i>Controlador Emperon</h6>
                                <p>Procesamiento ultra-rápido de documentos complejos con RIP integrado para manejo superior de PDFs, PostScript y trabajos de impresión variables.</p>
                                <ul>
                                    <li>Procesamiento 3x más rápido</li>
                                    <li>RIP nativo integrado</li>
                                    <li>Soporte PDF/VT completo</li>
                                    <li>Gestión avanzada de color</li>
                                </ul>
                            </div>
                            <div class="tech-pane" id="biometric">
                                <h6><i class="fas fa-fingerprint text-primary me-2"></i>Autenticación Biométrica</h6>
                                <p>Seguridad de nivel bancario con reconocimiento de huella dactilar, tarjetas IC y autenticación multifactor para proteger información confidencial.</p>
                                <ul>
                                    <li>Reconocimiento de huella en 0.5s</li>
                                    <li>Encriptación AES-256</li>
                                    <li>Auditoría completa de accesos</li>
                                    <li>Integración con Active Directory</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="models-section mt-4">
                        <h4>Modelos Disponibles</h4>
                        <div class="models-grid">
                            <div class="model-card premium">
                                <div class="model-badge">Más Popular</div>
                                <h6>bizhub C458</h6>
                                <div class="model-specs">
                                    <span>45 ppm</span>
                                    <span>A3 Color</span>
                                    <span>Scanner</span>
                                    <span>WiFi</span>
                                </div>
                                <p>Ideal para oficinas medianas que requieren impresión a color de alta calidad con funciones avanzadas de escaneo.</p>
                                <div class="model-price">
                                    <span class="price">Desde $650/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>bizhub 754e</h6>
                                <div class="model-specs">
                                    <span>75 ppm</span>
                                    <span>A3 B/N</span>
                                    <span>Finisher</span>
                                    <span>OCR</span>
                                </div>
                                <p>Perfecto para empresas con alto volumen de impresión en blanco y negro. Incluye acabados profesionales.</p>
                                <div class="model-price">
                                    <span class="price">Desde $580/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>bizhub C287</h6>
                                <div class="model-specs">
                                    <span>28 ppm</span>
                                    <span>A3 Color</span>
                                    <span>WiFi</span>
                                    <span>Mobile</span>
                                </div>
                                <p>Compacto y versátil, ideal para pequeñas oficinas y grupos de trabajo que necesitan color ocasional.</p>
                                <div class="model-price">
                                    <span class="price">Desde $420/mes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="awards-section mt-4">
                        <h5>Reconocimientos y Certificaciones</h5>
                        <div class="awards-grid">
                            <div class="award-item">
                                <i class="fas fa-award text-warning"></i>
                                <span>BLI Pick Award 2024</span>
                            </div>
                            <div class="award-item">
                                <i class="fas fa-certificate text-success"></i>
                                <span>ISO 27001 Certified</span>
                            </div>
                            <div class="award-item">
                                <i class="fas fa-leaf text-success"></i>
                                <span>Energy Star Qualified</span>
                            </div>
                            <div class="award-item">
                                <i class="fas fa-medal text-primary"></i>
                                <span>Keypoint Intelligence</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        
        'canon': {
            title: 'Canon',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Canon_wordmark.svg/320px-Canon_wordmark.svg.png',
            content: `
                <div class="brand-showcase">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Canon_wordmark.svg/320px-Canon_wordmark.svg.png" alt="Canon" class="brand-logo-large mb-4"/>
                            <div class="brand-stats">
                                <div class="stat-item">
                                    <span class="stat-number">85+</span>
                                    <span class="stat-label">Años innovando</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">#1</span>
                                    <span class="stat-label">En calidad de imagen</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">180</span>
                                    <span class="stat-label">Países de presencia</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h4>Excelencia en Calidad de Imagen</h4>
                            <p class="lead">Canon es sinónimo de calidad fotográfica y precisión. Sus equipos multifuncionales combinan la tecnología de impresión más avanzada con diseños compactos y eficientes.</p>
                            
                            <div class="feature-grid">
                                <div class="feature-item">
                                    <i class="fas fa-camera text-primary"></i>
                                    <div>
                                        <h6>Calidad Fotográfica</h6>
                                        <p>Impresión con calidad de laboratorio fotográfico profesional</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-compress-alt text-primary"></i>
                                    <div>
                                        <h6>Diseño Compacto</h6>
                                        <p>Máximo rendimiento en espacios reducidos sin comprometer funciones</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-mobile-alt text-primary"></i>
                                    <div>
                                        <h6>Conectividad Avanzada</h6>
                                        <p>Impresión móvil y conectividad cloud con aplicaciones nativas</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-dollar-sign text-primary"></i>
                                    <div>
                                        <h6>Eficiencia de Costos</h6>
                                        <p>Menor costo por página y alta durabilidad de componentes</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="innovation-timeline mt-4">
                        <h4>Historia de Innovación</h4>
                        <div class="timeline-horizontal">
                            <div class="timeline-point">
                                <span class="year">1976</span>
                                <span class="innovation">Primera fotocopiadora láser</span>
                            </div>
                            <div class="timeline-point">
                                <span class="year">1988</span>
                                <span class="innovation">Tecnología Bubble Jet</span>
                            </div>
                            <div class="timeline-point">
                                <span class="year">2010</span>
                                <span class="innovation">imageRUNNER ADVANCE</span>
                            </div>
                            <div class="timeline-point">
                                <span class="year">2020</span>
                                <span class="innovation">AI-Enhanced Scanning</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="models-section mt-4">
                        <h4>Modelos Destacados</h4>
                        <div class="models-grid">
                            <div class="model-card featured">
                                <div class="model-badge">Recomendado</div>
                                <h6>imageRUNNER C3226</h6>
                                <div class="model-specs">
                                    <span>26 ppm</span>
                                    <span>A3 Color</span>
                                    <span>Touch Screen</span>
                                    <span>Cloud</span>
                                </div>
                                <p>Multifuncional compacto con pantalla táctil intuitiva para oficinas dinámicas que requieren versatilidad.</p>
                                <div class="model-highlights">
                                    <span class="highlight">Pantalla táctil 10.1"</span>
                                    <span class="highlight">Escaneo a 160 ipm</span>
                                    <span class="highlight">Canon SEND</span>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $590/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>imageRUNNER 2630</h6>
                                <div class="model-specs">
                                    <span>30 ppm</span>
                                    <span>A3 B/N</span>
                                    <span>Duplex</span>
                                    <span>DADF</span>
                                </div>
                                <p>Ideal para oficinas que requieren impresión rápida y económica con funciones de productividad avanzadas.</p>
                                <div class="model-highlights">
                                    <span class="highlight">DADF de 100 hojas</span>
                                    <span class="highlight">Ciclo 150K páginas</span>
                                    <span class="highlight">Arranque rápido</span>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $380/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>imageRUNNER C5560i</h6>
                                <div class="model-specs">
                                    <span>60 ppm</span>
                                    <span>A3 Color</span>
                                    <span>Finisher</span>
                                    <span>OCR</span>
                                </div>
                                <p>Potencia y versatilidad para entornos de alta producción que demandan calidad profesional constante.</p>
                                <div class="model-highlights">
                                    <span class="highlight">Finisher integrado</span>
                                    <span class="highlight">Ciclo 300K páginas</span>
                                    <span class="highlight">V2 Color Technology</span>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $890/mes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="software-integration mt-4">
                        <h4>Integración de Software</h4>
                        <div class="software-grid">
                            <div class="software-item">
                                <i class="fab fa-microsoft text-primary"></i>
                                <div>
                                    <h6>Microsoft 365</h6>
                                    <p>Integración nativa con SharePoint, OneDrive y Teams</p>
                                </div>
                            </div>
                            <div class="software-item">
                                <i class="fab fa-google text-success"></i>
                                <div>
                                    <h6>Google Workspace</h6>
                                    <p>Conectividad directa con Drive, Gmail y aplicaciones G Suite</p>
                                </div>
                            </div>
                            <div class="software-item">
                                <i class="fas fa-cloud text-info"></i>
                                <div>
                                    <h6>Canon SEND</h6>
                                    <p>Plataforma cloud propietaria para gestión avanzada de documentos</p>
                                </div>
                            </div>
                            <div class="software-item">
                                <i class="fas fa-mobile-alt text-warning"></i>
                                <div>
                                    <h6>Canon PRINT</h6>
                                    <p>Aplicación móvil para impresión y escaneo desde dispositivos móviles</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        
        'ricoh': {
            title: 'Ricoh',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Ricoh_logo.svg/320px-Ricoh_logo.svg.png',
            content: `
                <div class="brand-showcase">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Ricoh_logo.svg/320px-Ricoh_logo.svg.png" alt="Ricoh" class="brand-logo-large mb-4"/>
                            <div class="brand-stats">
                                <div class="stat-item">
                                    <span class="stat-number">85+</span>
                                    <span class="stat-label">Años de experiencia</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">#1</span>
                                    <span class="stat-label">En durabilidad</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-number">200+</span>
                                    <span class="stat-label">Países servidos</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h4>Rendimiento y Durabilidad Excepcional</h4>
                            <p class="lead">Ricoh se destaca por crear equipos robustos y confiables que mantienen un rendimiento óptimo durante años. Su enfoque en la facilidad de uso los convierte en la elección preferida para empresas exigentes.</p>
                            
                            <div class="feature-grid">
                                <div class="feature-item">
                                    <i class="fas fa-industry text-primary"></i>
                                    <div>
                                        <h6>Construcción Robusta</h6>
                                        <p>Diseñados para resistir uso intensivo diario en entornos exigentes</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-user-friends text-primary"></i>
                                    <div>
                                        <h6>Facilidad de Uso</h6>
                                        <p>Interfaz intuitiva que cualquiera puede manejar sin capacitación extensa</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-cloud text-primary"></i>
                                    <div>
                                        <h6>Conectividad Cloud</h6>
                                        <p>Integración perfecta con servicios en la nube y workflows digitales</p>
                                    </div>
                                </div>
                                <div class="feature-item">
                                    <i class="fas fa-chart-line text-primary"></i>
                                    <div>
                                        <h6>Productividad Máxima</h6>
                                        <p>Workflows optimizados para eficiencia total y reducción de pasos</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="smart-operation-center mt-4">
                        <h4>Smart Operation Panel</h4>
                        <div class="panel-showcase">
                            <div class="panel-features">
                                <div class="panel-feature">
                                    <i class="fas fa-hand-point-up text-primary"></i>
                                    <h6>Interfaz Táctil Intuitiva</h6>
                                    <p>Panel de 10.1" personalizable con accesos directos a funciones frecuentes</p>
                                </div>
                                <div class="panel-feature">
                                    <i class="fas fa-robot text-info"></i>
                                    <h6>IA Integrada</h6>
                                    <p>Aprende patrones de uso y sugiere optimizaciones automáticas</p>
                                </div>
                                <div class="panel-feature">
                                    <i class="fas fa-cog text-warning"></i>
                                    <h6>Configuración Automática</h6>
                                    <p>Detecta tipos de documento y ajusta configuraciones óptimas</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="models-section mt-4">
                        <h4>Serie IM - Intelligent Machines</h4>
                        <div class="models-grid">
                            <div class="model-card bestseller">
                                <div class="model-badge">Best Seller</div>
                                <h6>IM C3000</h6>
                                <div class="model-specs">
                                    <span>30 ppm</span>
                                    <span>A3 Color</span>
                                    <span>Smart Panel</span>
                                    <span>AI Ready</span>
                                </div>
                                <p>Multifuncional inteligente con panel personalizable y workflows automáticos para oficinas modernas.</p>
                                <div class="model-features">
                                    <div class="feature-badge">Smart Panel 10.1"</div>
                                    <div class="feature-badge">Reconocimiento facial</div>
                                    <div class="feature-badge">Workflows IA</div>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $620/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>IM 6000</h6>
                                <div class="model-specs">
                                    <span>60 ppm</span>
                                    <span>A3 B/N</span>
                                    <span>Security+</span>
                                    <span>HDD</span>
                                </div>
                                <p>Alto volumen con características de seguridad empresarial avanzadas y encriptación de datos.</p>
                                <div class="model-features">
                                    <div class="feature-badge">DataLock Security</div>
                                    <div class="feature-badge">Ciclo 275K páginas</div>
                                    <div class="feature-badge">Finisher opcional</div>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $720/mes</span>
                                </div>
                            </div>
                            <div class="model-card">
                                <h6>IM C2500</h6>
                                <div class="model-specs">
                                    <span>25 ppm</span>
                                    <span>A3 Color</span>
                                    <span>Eco Mode</span>
                                    <span>WiFi 6</span>
                                </div>
                                <p>Perfecto balance entre funcionalidad y eficiencia energética para pequeñas y medianas oficinas.</p>
                                <div class="model-features">
                                    <div class="feature-badge">WiFi 6 Ready</div>
                                    <div class="feature-badge">Eco Modo automático</div>
                                    <div class="feature-badge">Arranque 9s</div>
                                </div>
                                <div class="model-price">
                                    <span class="price">Desde $480/mes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="sustainability-section mt-4">
                        <h4>Compromiso Ambiental</h4>
                        <div class="sustainability-grid">
                            <div class="sustainability-item">
                                <i class="fas fa-recycle text-success"></i>
                                <div>
                                    <h6>Programa de Reciclaje</h6>
                                    <p>100% de los cartuchos son reciclados en nuestro programa circular</p>
                                </div>
                            </div>
                            <div class="sustainability-item">
                                <i class="fas fa-leaf text-green"></i>
                                <div>
                                    <h6>Reducción CO2</h6>
                                    <p>30% menos emisiones comparado con generación anterior</p>
                                </div>
                            </div>
                            <div class="sustainability-item">
                                <i class="fas fa-battery-half text-warning"></i>
                                <div>
                                    <h6>Ahorro Energético</h6>
                                    <p>Modo Sleep con consumo menor a 1W en todos los modelos</p>
                                </div>
                            </div>
                            <div class="sustainability-item">
                                <i class="fas fa-award text-info"></i>
                                <div>
                                    <h6>Certificaciones</h6>
                                    <p>ENERGY STAR, EPEAT Gold y Blue Angel certified</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        }
    };

    // ====================================
    // DATOS DE PRODUCTOS
    // ====================================
    const productData = {
        'multifuncional-a3': {
            title: 'Multifuncionales A3',
            icon: 'fas fa-print',
            content: `
                <div class="product-showcase">
                    <div class="row">
                        <div class="col-md-6">
                            <img src="https://images.unsplash.com/photo-1586473219010-2ffc57b0d282?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80" alt="Multifuncional A3" class="img-fluid rounded mb-4"/>
                            <div class="product-highlights">
                                <h5>Características Principales</h5>
                                <div class="highlight-grid">
                                    <div class="highlight-item">
                                        <i class="fas fa-file-alt"></i>
                                        <span>Formato A3/A4/A5</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-palette"></i>
                                        <span>Color/Monocromático</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-copy"></i>
                                        <span>4 en 1: Imprime/Copia/Escanea/Fax</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-wifi"></i>
                                        <span>Conectividad Total</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h4>Especificaciones Técnicas</h4>
                            <div class="specs-table">
                                <div class="spec-row">
                                    <span class="spec-label">Velocidad de impresión:</span>
                                    <span class="spec-value">20-75 ppm</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Resolución máxima:</span>
                                    <span class="spec-value">1200 x 1200 dpi</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Capacidad de papel:</span>
                                    <span class="spec-value">550-4,000 hojas</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Memoria RAM:</span>
                                    <span class="spec-value">2-8 GB</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Conectividad:</span>
                                    <span class="spec-value">Ethernet, WiFi, USB 3.0</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Funciones:</span>
                                    <span class="spec-value">Impresión, Copia, Escaneo, Fax</span>
                                </div>
                            </div>
                            
                            <h5 class="mt-4">Ideal Para:</h5>
                            <ul class="ideal-for-list">
                                <li><i class="fas fa-building text-success me-2"></i>Oficinas grandes (50+ empleados)</li>
                                <li><i class="fas fa-chart-bar text-success me-2"></i>Alto volumen de impresión (5,000+ pág/mes)</li>
                                <li><i class="fas fa-users text-success me-2"></i>Múltiples departamentos</li>
                                <li><i class="fas fa-file-pdf text-success me-2"></i>Documentos gran formato</li>
                                <li><i class="fas fa-presentation text-success me-2"></i>Presentaciones profesionales</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="applications-section mt-4">
                        <h4>Aplicaciones Empresariales</h4>
                        <div class="application-cards">
                            <div class="app-card">
                                <i class="fas fa-briefcase"></i>
                                <h6>Oficinas Corporativas</h6>
                                <p>Gestión de documentos empresariales, reportes y presentaciones de gran formato</p>
                                <div class="app-features">
                                    <span>Reportes financieros</span>
                                    <span>Presentaciones A3</span>
                                    <span>Documentos legales</span>
                                </div>
                            </div>
                            <div class="app-card">
                                <i class="fas fa-graduation-cap"></i>
                                <h6>Centros Educativos</h6>
                                <p>Material didáctico, exámenes y documentación académica en volumen</p>
                                <div class="app-features">
                                    <span>Material educativo</span>
                                    <span>Exámenes masivos</span>
                                    <span>Pósters académicos</span>
                                </div>
                            </div>
                            <div class="app-card">
                                <i class="fas fa-hospital"></i>
                                <h6>Centros Médicos</h6>
                                <p>Historias clínicas, imágenes médicas y documentación regulatoria</p>
                                <div class="app-features">
                                    <span>Historias clínicas</span>
                                    <span>Imágenes médicas</span>
                                    <span>Reportes regulatorios</span>
                                </div>
                            </div>
                            <div class="app-card">
                                <i class="fas fa-balance-scale"></i>
                                <h6>Estudios Legales</h6>
                                <p>Contratos, demandas y documentación legal de gran volumen</p>
                                <div class="app-features">
                                    <span>Contratos complejos</span>
                                    <span>Expedientes voluminosos</span>
                                    <span>Documentos certificados</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="comparison-benefits mt-4">
                        <h4>Ventajas vs Impresoras A4</h4>
                        <div class="comparison-grid">
                            <div class="comparison-item advantage">
                                <i class="fas fa-expand text-success"></i>
                                <h6>Formato Flexible</h6>
                                <p>Imprime desde A5 hasta A3 sin limitaciones</p>
                            </div>
                            <div class="comparison-item advantage">
                                <i class="fas fa-chart-line text-success"></i>
                                <div>
                                    <h6>Mayor Productividad</h6>
                                    <p>Elimina necesidad de reducir o fragmentar documentos</p>
                                </div>
                            </div>
                            <div class="comparison-item advantage">
                                <i class="fas fa-presentation text-success"></i>
                                <div>
                                    <h6>Presentaciones Impactantes</h6>
                                    <p>Gráficos y planos en tamaño real</p>
                                </div>
                            </div>
                            <div class="comparison-item advantage">
                                <i class="fas fa-dollar-sign text-success"></i>
                                <div>
                                    <h6>Mejor ROI</h6>
                                    <p>Un solo equipo para todos los formatos</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        
        'multifuncional-a4': {
            title: 'Multifuncionales A4',
            icon: 'fas fa-print',
            content: `
                <div class="product-showcase">
                    <div class="row">
                        <div class="col-md-6">
                            <img src="https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80" alt="Multifuncional A4" class="img-fluid rounded mb-4"/>
                            <div class="product-highlights">
                                <h5>Características Principales</h5>
                                <div class="highlight-grid">
                                    <div class="highlight-item">
                                        <i class="fas fa-file-alt"></i>
                                        <span>Formato A4/Letter</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-wifi"></i>
                                        <span>WiFi 6 Integrado</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-mobile-alt"></i>
                                        <span>Impresión Móvil</span>
                                    </div>
                                    <div class="highlight-item">
                                        <i class="fas fa-cloud"></i>
                                        <span>Cloud Ready</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h4>Especificaciones Técnicas</h4>
                            <div class="specs-table">
                                <div class="spec-row">
                                    <span class="spec-label">Velocidad de impresión:</span>
                                    <span class="spec-value">15-55 ppm</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Resolución máxima:</span>
                                    <span class="spec-value">4800 x 1200 dpi</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Capacidad de papel:</span>
                                    <span class="spec-value">250-1,200 hojas</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Memoria RAM:</span>
                                    <span class="spec-value">512 MB - 4 GB</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Conectividad:</span>
                                    <span class="spec-value">WiFi 6, Ethernet, USB 3.0, NFC</span>
                                </div>
                                <div class="spec-row">
                                    <span class="spec-label">Pantalla:</span>
                                    <span class="spec-value">Táctil 4.3" - 10.1"</span>
                                </div>
                            </div>
                            
                            <h5 class="mt-4">Ideal Para:</h5>
                            <ul class="ideal-for-list">
                                <li><i class="fas fa-building text-success me-2"></i>Oficinas medianas (10-50 empleados)</li>
                                <li><i class="fas fa-chart-bar text-success me-2"></i>Volumen moderado (1,000-5,000 pág/mes)</li>
                                <li><i class="fas fa-users text-success me-2"></i>Grupos de trabajo</li>
                                <li><i class="fas fa-mobile-alt text-success me-2"></i>Trabajo remoto e híbrido</li>
                                <li><i class="fas fa-home text-success me-2"></i>Oficinas satélite</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="features-section mt-4">
                        <h4>Funciones Avanzadas</h4>
                        <div class="feature-tabs">
                            <div class="feature-tab active" data-tab="connectivity">
                                <h6><i class="fas fa-wifi me-2"></i>Conectividad</h6>
                            </div>
                            <div class="feature-tab" data-tab="security">
                                <h6><i class="fas fa-shield-alt me-2"></i>Seguridad</h6>
                            </div>
                            <div class="feature-tab" data-tab="productivity">
                                <h6><i class="fas fa-chart-line me-2"></i>Productividad</h6>
                            </div>
                            <div class="feature-tab" data-tab="mobile">
                                <h6><i class="fas fa-mobile-alt me-2"></i>Móvil</h6>
                            </div>
                        </div>
                        <div class="tab-content">
                            <div class="tab-pane active" id="connectivity">
                                <div class="feature-details">
                                    <div class="feature-item">
                                        <i class="fas fa-wifi text-primary"></i>
                                        <div>
                                            <h6>WiFi 6 de Alta Velocidad</h6>
                                            <p>Conexión inalámbrica ultra-rápida con múltiples dispositivos simultáneos</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-ethernet text-info"></i>
                                        <div>
                                            <h6>Ethernet Gigabit</h6>
                                            <p>Conectividad cableada de alta velocidad para entornos de red exigentes</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-usb text-warning"></i>
                                        <div>
                                            <h6>USB 3.0 Host</h6>
                                            <p>Impresión directa desde unidades USB con soporte para múltiples formatos</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="tab-pane" id="security">
                                <div class="feature-details">
                                    <div class="feature-item">
                                        <i class="fas fa-id-card text-primary"></i>
                                        <div>
                                            <h6>Autenticación de Usuario</h6>
                                            <p>Control de acceso con tarjetas, códigos PIN o autenticación biométrica</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-lock text-success"></i>
                                        <div>
                                            <h6>Encriptación de Datos</h6>
                                            <p>Protección AES-256 para todos los datos almacenados y transmitidos</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-print text-info"></i>
                                        <div>
                                            <h6>Secure Print</h6>
                                            <p>Impresión segura con liberación por PIN para documentos confidenciales</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="tab-pane" id="productivity">
                                <div class="feature-details">
                                    <div class="feature-item">
                                        <i class="fas fa-copy text-primary"></i>
                                        <div>
                                            <h6>Escaneo Duplex Automático</h6>
                                            <p>Digitalización de ambas caras en una sola pasada hasta 160 ipm</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-search text-warning"></i>
                                        <div>
                                            <h6>OCR Integrado</h6>
                                            <p>Reconocimiento óptico de caracteres para PDFs completamente buscables</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-workflow text-success"></i>
                                        <div>
                                            <h6>Workflows Personalizables</h6>
                                            <p>Automatización de procesos repetitivos con un solo toque</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="tab-pane" id="mobile">
                                <div class="feature-details">
                                    <div class="feature-item">
                                        <i class="fab fa-apple text-primary"></i>
                                        <div>
                                            <h6>AirPrint Nativo</h6>
                                            <p>Impresión directa desde iPhone y iPad sin configuración adicional</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fab fa-android text-success"></i>
                                        <div>
                                            <h6>Mopria Certified</h6>
                                            <p>Compatibilidad universal con dispositivos Android</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-qr-code text-info"></i>
                                        <div>
                                            <h6>Códigos QR</h6>
                                            <p>Conexión instantánea mediante escaneo de código QR</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="integration-showcase mt-4">
                        <h4>Integración Cloud</h4>
                        <div class="cloud-services">
                            <div class="service-item">
                                <i class="fab fa-microsoft text-primary"></i>
                                <span>OneDrive</span>
                            </div>
                            <div class="service-item">
                                <i class="fab fa-google text-success"></i>
                                <span>Google Drive</span>
                            </div>
                            <div class="service-item">
                                <i class="fab fa-dropbox text-info"></i>
                                <span>Dropbox</span>
                            </div>
                            <div class="service-item">
                                <i class="fas fa-briefcase text-warning"></i>
                                <span>SharePoint</span>
                            </div>
                            <div class="service-item">
                                <i class="fas fa-envelope text-danger"></i>
                                <span>Email Direct</span>
                            </div>
                            <div class="service-item">
                                <i class="fas fa-folder text-secondary"></i>
                                <span>FTP/SMB</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        }
    };

    // ====================================
    // MODAL DE MARCAS
    // ====================================
    function initBrandModal() {
        const brandCards = document.querySelectorAll('.copier-modern-homepage .brand-card[data-brand]');
        const modal = document.getElementById('brandModal');
        const modalBody = document.getElementById('brandModalBody');
        const modalTitle = document.querySelector('#brandModal .modal-title');

        if (!modal || !modalBody || !modalTitle) {
            console.warn('⚠️ Brand modal elements not found');
            return;
        }

        brandCards.forEach(card => {
            card.addEventListener('click', function() {
                const brandKey = this.getAttribute('data-brand');
                const data = brandData[brandKey];
                
                if (data) {
                    modalTitle.innerHTML = `<i class="fas fa-award me-2"></i>${data.title}`;
                    modalBody.innerHTML = data.content;
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'brand_modal_open', {
                            event_category: 'engagement',
                            event_label: brandKey
                        });
                    }
                    
                    // Inicializar tabs después de cargar contenido
                    setTimeout(() => {
                        initBrandModalTabs();
                        modalBody.classList.add('animate-fade-in', 'visible');
                    }, 100);
                    
                    console.log(`🏢 Brand modal opened: ${brandKey}`);
                } else {
                    console.warn(`⚠️ Brand data not found for key: ${brandKey}`);
                }
            });
        });

        // Limpiar animaciones al cerrar modal
        modal.addEventListener('hidden.bs.modal', function() {
            modalBody.classList.remove('animate-fade-in', 'visible');
        });
    }

    // ====================================
    // MODAL DE PRODUCTOS
    // ====================================
    function initProductModal() {
        const productCards = document.querySelectorAll('.copier-modern-homepage .product-card[data-product]');
        const modal = document.getElementById('productModal');
        const modalBody = document.getElementById('productModalBody');
        const modalTitle = document.querySelector('#productModal .modal-title');

        if (!modal || !modalBody || !modalTitle) {
            console.warn('⚠️ Product modal elements not found');
            return;
        }

        productCards.forEach(card => {
            card.addEventListener('click', function() {
                const productKey = this.getAttribute('data-product');
                const data = productData[productKey];
                
                if (data) {
                    modalTitle.innerHTML = `<i class="${data.icon} me-2"></i>${data.title}`;
                    modalBody.innerHTML = data.content;
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'product_modal_open', {
                            event_category: 'engagement',
                            event_label: productKey
                        });
                    }
                    
                    // Inicializar tabs después de cargar contenido
                    setTimeout(() => {
                        initProductModalTabs();
                        modalBody.classList.add('animate-fade-in', 'visible');
                    }, 100);
                    
                    console.log(`📦 Product modal opened: ${productKey}`);
                } else {
                    console.warn(`⚠️ Product data not found for key: ${productKey}`);
                }
            });
        });

        // Limpiar animaciones al cerrar modal
        modal.addEventListener('hidden.bs.modal', function() {
            modalBody.classList.remove('animate-fade-in', 'visible');
        });
    }

    // ====================================
    // TABS DE MODALES DE MARCAS
    // ====================================
    function initBrandModalTabs() {
        // Technology tabs
        const techTabs = document.querySelectorAll('.tech-tab');
        techTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTech = this.getAttribute('data-tech');
                
                // Remover active de todos los tabs
                techTabs.forEach(t => t.classList.remove('active'));
                // Agregar active al tab clickeado
                this.classList.add('active');
                
                // Mostrar contenido correspondiente
                const techPanes = document.querySelectorAll('.tech-pane');
                techPanes.forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.id === targetTech) {
                        pane.classList.add('active');
                    }
                });
                
                // Analytics tracking
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'brand_tech_tab_click', {
                        event_category: 'engagement',
                        event_label: targetTech
                    });
                }
            });
        });
    }

    // ====================================
    // TABS DE MODALES DE PRODUCTOS
    // ====================================
    function initProductModalTabs() {
        // Feature tabs
        const featureTabs = document.querySelectorAll('.feature-tab');
        featureTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTab = this.getAttribute('data-tab');
                
                // Remover active de todos los tabs
                featureTabs.forEach(t => t.classList.remove('active'));
                // Agregar active al tab clickeado
                this.classList.add('active');
                
                // Mostrar contenido correspondiente
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.id === targetTab) {
                        pane.classList.add('active');
                    }
                });
                
                // Analytics tracking
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'product_feature_tab_click', {
                        event_category: 'engagement',
                        event_label: targetTab
                    });
                }
            });
        });
    }

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart6 = {
        brandData,
        productData,
        initBrandModal,
        initProductModal,
        initBrandModalTabs,
        initProductModalTabs
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initBrandModal();
            initProductModal();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 6 cargada (Modales de Marcas y Productos)');
    })();
    /**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 7/10: Estilos CSS para Modales
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // ESTILOS CSS PARA MODALES
    // ====================================
    const modalStyles = `
        /* ===== ESTILOS BASE DE MODALES ===== */
        .modal-content {
            border: none;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            overflow: hidden;
        }

        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom: none;
            padding: 20px 30px;
        }

        .modal-title {
            font-weight: 600;
            font-size: 1.25rem;
        }

        .modal-body {
            padding: 30px;
            max-height: 70vh;
            overflow-y: auto;
        }

        .modal-footer {
            border-top: 1px solid #e9ecef;
            padding: 20px 30px;
        }

        /* Scrollbar personalizada para modal */
        .modal-body::-webkit-scrollbar {
            width: 6px;
        }

        .modal-body::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }

        .modal-body::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 3px;
        }

        .modal-body::-webkit-scrollbar-thumb:hover {
            background: #5a67d8;
        }

        /* ===== TIMELINE STYLES ===== */
        .timeline {
            position: relative;
            padding: 20px 0;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 25px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #667eea, #764ba2);
        }

        .timeline-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 30px;
            position: relative;
        }

        .timeline-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2rem;
            margin-right: 20px;
            flex-shrink: 0;
            z-index: 2;
            position: relative;
        }

        .timeline-content {
            flex: 1;
            padding-top: 5px;
        }

        .timeline-content h5 {
            margin-bottom: 10px;
            color: #2c3e50;
            font-weight: 600;
        }

        .timeline-content p {
            color: #6c757d;
            margin-bottom: 8px;
            line-height: 1.5;
        }

        .timeline-content small {
            color: #adb5bd;
            font-style: italic;
        }

        .timeline-details {
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .detail-badge {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        /* ===== PROCESS TIMELINE ===== */
        .process-timeline {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }

        .process-timeline .timeline::before {
            left: 15px;
            background: #28a745;
        }

        .process-timeline .timeline-icon {
            width: 30px;
            height: 30px;
            font-size: 0.875rem;
        }

        /* ===== TIMELINE HORIZONTAL ===== */
        .timeline-horizontal {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            position: relative;
            overflow-x: auto;
        }

        .timeline-horizontal::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(to right, #667eea, #764ba2);
            z-index: 1;
        }

        .timeline-point {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            min-width: 120px;
            position: relative;
            z-index: 2;
        }

        .timeline-point::before {
            content: '';
            width: 12px;
            height: 12px;
            background: #667eea;
            border-radius: 50%;
            margin-bottom: 8px;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .timeline-point .year {
            font-weight: 700;
            color: #2c3e50;
            font-size: 0.875rem;
            margin-bottom: 4px;
        }

        .timeline-point .innovation {
            font-size: 0.75rem;
            color: #6c757d;
            max-width: 100px;
            line-height: 1.3;
        }

        /* ===== MAINTENANCE SCHEDULE ===== */
        .maintenance-schedule {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #dee2e6;
        }

        .schedule-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #dee2e6;
        }

        .schedule-item:last-child {
            border-bottom: none;
        }

        .frequency {
            font-weight: 600;
            color: #667eea;
            min-width: 100px;
            font-size: 0.875rem;
            padding: 4px 12px;
            border-radius: 20px;
            text-align: center;
        }

        .frequency.monthly {
            background: #e3f2fd;
            color: #1976d2;
        }

        .frequency.quarterly {
            background: #f3e5f5;
            color: #7b1fa2;
        }

        .frequency.biannual {
            background: #fff3e0;
            color: #f57c00;
        }

        .frequency.annual {
            background: #e8f5e8;
            color: #388e3c;
        }

        .task {
            color: #6c757d;
            flex-grow: 1;
            text-align: right;
            font-size: 0.875rem;
        }

        /* ===== MAINTENANCE DETAILS ===== */
        .maintenance-details {
            background: white;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #e9ecef;
        }

        .detail-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .detail-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 6px;
            font-size: 0.875rem;
        }

        .detail-item i {
            font-size: 1rem;
            width: 16px;
            text-align: center;
        }

        /* ===== SERVICE STATS ===== */
        .service-stats {
            margin: 20px 0;
        }

        .service-stats .stat-card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .service-stats .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }

        .service-stats .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .stat-card h3 {
            margin-bottom: 8px;
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1;
        }

        .stat-card p {
            margin: 0;
            font-size: 0.875rem;
            color: #6c757d;
            font-weight: 500;
        }

        /* ===== COMPARISON TABLE ===== */
        .comparison-table {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e9ecef;
            margin: 20px 0;
        }

        .comparison-header {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: 600;
            padding: 16px;
            font-size: 0.875rem;
            gap: 16px;
        }

        .comparison-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            padding: 12px 16px;
            border-bottom: 1px solid #f1f3f4;
            align-items: center;
            gap: 16px;
            font-size: 0.875rem;
        }

        .comparison-row:last-child {
            border-bottom: none;
        }

        .comparison-row:nth-child(even) {
            background: #fafbfc;
        }

        .comparison-total {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            padding: 16px;
            background: #f8f9fa;
            font-weight: 600;
            border-top: 2px solid #667eea;
            gap: 16px;
        }

        .cost {
            color: #dc3545;
            font-weight: 600;
        }

        .included {
            color: #28a745;
            font-weight: 600;
        }

        .savings, .total-savings {
            color: #667eea;
            font-weight: 700;
        }

        /* ===== BRAND STATS ===== */
        .brand-logo-large {
            max-height: 80px;
            width: auto;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
        }

        .brand-stats {
            text-align: center;
        }

        .stat-item {
            margin: 16px 0;
            padding: 12px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease;
        }

        .stat-item:hover {
            transform: scale(1.05);
        }

        .stat-number {
            display: block;
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            line-height: 1;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 0.875rem;
            color: #6c757d;
            font-weight: 500;
        }

        /* ===== FEATURE GRID ===== */
        .feature-grid {
            display: grid;
            gap: 20px;
            margin: 20px 0;
        }

        .feature-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .feature-item:hover {
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }

        .feature-item i {
            font-size: 1.5rem;
            margin-top: 4px;
            flex-shrink: 0;
        }

        .feature-item h6 {
            margin-bottom: 6px;
            font-weight: 600;
            color: #2c3e50;
        }

        .feature-item p {
            color: #6c757d;
            margin: 0;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* ===== MODELS GRID ===== */
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin: 24px 0;
        }

        .model-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .model-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }

        .model-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            border-color: #667eea;
        }

        .model-badge {
            position: absolute;
            top: 16px;
            right: 16px;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .model-badge.premium {
            background: #f59e0b;
        }

        .model-badge.featured {
            background: #10b981;
        }

        .model-badge.bestseller {
            background: #ef4444;
        }

        .model-card h6 {
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 12px;
            font-size: 1.25rem;
        }

        .model-specs {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        .model-specs span {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            color: #2c3e50;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid #e9ecef;
        }

        .model-highlights, .model-features {
            margin: 12px 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .highlight, .feature-badge {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            display: inline-block;
            width: fit-content;
        }

        .model-card p {
            color: #6c757d;
            font-size: 0.875rem;
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .model-price {
            margin-top: auto;
            padding-top: 16px;
            border-top: 1px solid #e9ecef;
        }

        .price {
            font-size: 1.25rem;
            font-weight: 700;
            color: #667eea;
        }

        /* ===== TABS ===== */
        .feature-tabs, .tech-tabs {
            display: flex;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 24px;
            gap: 4px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        .feature-tab, .tech-tab {
            padding: 12px 20px;
            border: 1px solid transparent;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            background: #f8f9fa;
            color: #6c757d;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
            font-weight: 500;
            text-decoration: none;
        }

        .feature-tab.active, .tech-tab.active {
            background: white;
            color: #667eea;
            border-color: #e9ecef;
            border-bottom-color: white;
            margin-bottom: -2px;
            z-index: 1;
            position: relative;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
        }

        .feature-tab:hover, .tech-tab:hover {
            background: #e9ecef;
            color: #495057;
        }

        .feature-tab.active:hover, .tech-tab.active:hover {
            background: white;
            color: #667eea;
        }

        .tab-content {
            margin-top: 24px;
        }

        .tab-pane, .tech-pane {
            display: none;
            animation: fadeInUp 0.3s ease-out;
        }

        .tab-pane.active, .tech-pane.active {
            display: block;
        }

        .tech-content {
            background: #f8f9fa;
            border-radius: 0 0 12px 12px;
            padding: 24px;
            border: 1px solid #e9ecef;
            border-top: none;
        }

        .tech-pane h6 {
            color: #2c3e50;
            margin-bottom: 12px;
            font-weight: 600;
        }

        .tech-pane p {
            color: #6c757d;
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .tech-pane ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .tech-pane li {
            padding: 6px 0;
            color: #495057;
            font-size: 0.875rem;
            position: relative;
            padding-left: 20px;
        }

        .tech-pane li::before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }

        /* ===== FEATURE DETAILS ===== */
        .feature-details {
            display: grid;
            gap: 16px;
        }

        .feature-details .feature-item {
            margin: 0;
        }

        /* ===== CHECKLIST ===== */
        .installation-checklist {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
        }

        .checklist {
            list-style: none;
            padding: 0;
            margin: 16px 0;
        }

        .checklist li {
            padding: 8px 0;
            color: #495057;
            font-size: 0.875rem;
            position: relative;
            padding-left: 24px;
        }

        .checklist li::before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
            font-size: 1rem;
        }

        /* ===== GUARANTEE BOX ===== */
        .maintenance-guarantee, .guarantee-box {
            background: linear-gradient(135deg, #fff7ed, #fef3c7);
            border: 1px solid #f59e0b;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .guarantee-box i {
            font-size: 2rem;
            margin-bottom: 8px;
        }

        .guarantee-box p {
            margin: 8px 0;
            color: #92400e;
        }

        .guarantee-box .small {
            color: #a16207;
        }

        /* ===== BENEFITS GRID ===== */
        .benefits-grid, .installation-benefits .benefits-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .benefit-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: white;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .benefit-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .benefit-item i {
            font-size: 1.5rem;
            margin-top: 4px;
            flex-shrink: 0;
        }

        .benefit-item h6 {
            margin-bottom: 6px;
            font-weight: 600;
            color: #2c3e50;
        }

        .benefit-item p {
            color: #6c757d;
            margin: 0;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* ===== FINANCIAL COMPARISON ===== */
        .financial-comparison {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
        }

        .financial-comparison h5 {
            color: #2c3e50;
            margin-bottom: 16px;
            font-weight: 600;
        }

        .comparison-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }

        .comparison-row:last-child {
            border-bottom: none;
            font-weight: 600;
        }

        .comparison-label {
            color: #495057;
            font-size: 0.875rem;
        }

        .comparison-value.cost {
            color: #dc3545;
            font-weight: 600;
        }

        .comparison-value.benefit {
            color: #28a745;
            font-weight: 600;
        }

        .comparison-value.highlight {
            color: #667eea;
            font-weight: 700;
            font-size: 1.1rem;
        }

        /* ===== ROI CALCULATOR ===== */
        .roi-calculator {
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 20px;
        }

        .calculator-box p {
            margin-bottom: 16px;
            color: #0c4a6e;
        }

        .roi-options {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .roi-option {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px;
            background: white;
            border-radius: 8px;
            font-size: 0.875rem;
            color: #0c4a6e;
        }

        .roi-option i {
            font-size: 1rem;
        }

        /* ===== SUPPORT PROCESS ===== */
        .support-process {
            margin: 24px 0;
        }

        .process-timeline {
            display: grid;
            gap: 16px;
        }

        .timeline-step {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .timeline-step:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .step-number {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }

        .step-content h6 {
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: 600;
        }

        .step-content p {
            margin-bottom: 4px;
            color: #6c757d;
            font-size: 0.875rem;
        }

        .step-content small {
            color: #adb5bd;
            font-style: italic;
        }

        /* ===== SUPPORT STATS ===== */
        .support-stats {
            margin: 24px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }

        .stats-grid .stat-item {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stats-grid .stat-number {
            font-size: 2rem;
            color: #667eea;
        }

        .stats-grid .stat-label {
            font-size: 0.875rem;
            color: #6c757d;
        }

        /* ===== AWARDS SECTION ===== */
        .awards-section {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
        }

        .awards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }

        .award-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            font-size: 0.875rem;
            font-weight: 500;
            color: #495057;
        }

        .award-item i {
            font-size: 1.25rem;
        }

        /* ===== CLOUD SERVICES ===== */
        .integration-showcase {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
        }

        .cloud-services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }

        .service-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 16px;
            background: white;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
        }

        .service-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .service-item i {
            font-size: 2rem;
        }

        .service-item span {
            font-size: 0.875rem;
            font-weight: 500;
            color: #495057;
        }

        /* ===== SOFTWARE INTEGRATION ===== */
        .software-integration {
            margin: 24px 0;
        }

        .software-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 16px;
        }

        .software-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .software-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .software-item i {
            font-size: 1.5rem;
            margin-top: 4px;
            flex-shrink: 0;
        }

        .software-item h6 {
            margin-bottom: 6px;
            font-weight: 600;
            color: #2c3e50;
        }

        .software-item p {
            color: #6c757d;
            margin: 0;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* ===== SUSTAINABILITY SECTION ===== */
        .sustainability-section {
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            border: 1px solid #16a34a;
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
        }

        .sustainability-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 16px;
        }

        .sustainability-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: white;
            border-radius: 12px;
            border: 1px solid #bbf7d0;
        }

        .sustainability-item i {
            font-size: 1.5rem;
            margin-top: 4px;
            flex-shrink: 0;
        }

        .sustainability-item h6 {
            margin-bottom: 6px;
            font-weight: 600;
            color: #166534;
        }

        .sustainability-item p {
            color: #15803d;
            margin: 0;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* ===== SMART OPERATION CENTER ===== */
        .smart-operation-center {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            border: 1px solid #f59e0b;
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
        }

        .panel-showcase {
            margin-top: 16px;
        }

        .panel-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .panel-feature {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #f59e0b;
            text-align: center;
        }

        .panel-feature i {
            font-size: 2rem;
            margin-bottom: 12px;
        }

        .panel-feature h6 {
            margin-bottom: 8px;
            color: #92400e;
            font-weight: 600;
        }

        .panel-feature p {
            color: #a16207;
            font-size: 0.875rem;
            margin: 0;
            line-height: 1.4;
        }

        /* ===== APPLICATION CARDS ===== */
        .applications-section {
            margin: 24px 0;
        }

        .application-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin: 24px 0;
        }

        .app-card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e9ecef;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .app-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }

        .app-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }

        .app-card i {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 16px;
        }

        .app-card h6 {
            color: #2c3e50;
            margin-bottom: 12px;
            font-weight: 600;
            font-size: 1.1rem;
        }

        .app-card p {
            color: #6c757d;
            font-size: 0.875rem;
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .app-features {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 16px;
        }

        .app-features span {
            background: #f8f9fa;
            color: #495057;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        /* ===== COMPARISON BENEFITS ===== */
        .comparison-benefits {
            margin: 24px 0;
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 16px;
        }

        .comparison-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .comparison-item.advantage {
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            border-color: #16a34a;
        }

        .comparison-item:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .comparison-item i {
            font-size: 1.5rem;
            margin-top: 4px;
            flex-shrink: 0;
        }

        .comparison-item h6 {
            margin-bottom: 6px;
            font-weight: 600;
            color: #2c3e50;
        }

        .comparison-item p {
            color: #6c757d;
            margin: 0;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* ===== PRODUCT HIGHLIGHTS ===== */
        .product-highlights {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }

        .highlight-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 16px;
        }

        .highlight-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .highlight-item:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .highlight-item i {
            color: #667eea;
            font-size: 1.25rem;
            flex-shrink: 0;
        }

        .highlight-item span {
            font-size: 0.875rem;
            font-weight: 500;
            color: #495057;
        }

        /* ===== SPECS TABLE ===== */
        .specs-table {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            border: 1px solid #e9ecef;
        }

        .spec-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }

        .spec-row:last-child {
            border-bottom: none;
        }

        .spec-label {
            font-weight: 500;
            color: #495057;
            font-size: 0.875rem;
        }

        .spec-value {
            color: #667eea;
            font-weight: 600;
            font-size: 0.875rem;
        }

        /* ===== IDEAL FOR LIST ===== */
        .ideal-for-list {
            list-style: none;
            padding: 0;
            margin: 16px 0;
        }

        .ideal-for-list li {
            padding: 6px 0;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
        }

        /* ===== RESPONSIVE DESIGN ===== */
        @media (max-width: 768px) {
            .modal-body {
                padding: 20px;
                max-height: 60vh;
            }

            .modal-header {
                padding: 16px 20px;
            }

            .modal-footer {
                padding: 16px 20px;
            }

            .models-grid,
            .application-cards,
            .benefits-grid,
            .comparison-grid,
            .software-grid,
            .sustainability-grid,
            .panel-features {
                grid-template-columns: 1fr;
            }

            .feature-grid {
                grid-template-columns: 1fr;
            }

            .highlight-grid {
                grid-template-columns: 1fr;
            }

            .feature-tabs,
            .tech-tabs {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }

            .timeline-horizontal {
                flex-direction: column;
                gap: 20px;
            }

            .timeline-horizontal::before {
                display: none;
            }

            .comparison-header,
            .comparison-row,
            .comparison-total {
                grid-template-columns: 1fr;
                text-align: center;
                gap: 8px;
            }

            .spec-row {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;
            }

            .timeline-item {
                flex-direction: column;
                text-align: center;
            }

            .timeline-icon {
                margin: 0 auto 16px auto;
            }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .cloud-services {
                grid-template-columns: repeat(3, 1fr);
            }

            .awards-grid {
                grid-template-columns: 1fr;
            }

            .model-badge {
                position: static;
                display: block;
                width: fit-content;
                margin-bottom: 12px;
            }
        }

        @media (max-width: 576px) {
            .modal-dialog {
                margin: 0;
                max-width: 100%;
                height: 100vh;
            }

            .modal-content {
                height: 100vh;
                border-radius: 0;
            }

            .modal-body {
                max-height: calc(100vh - 140px);
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .cloud-services {
                grid-template-columns: repeat(2, 1fr);
            }

            .model-specs {
                justify-content: center;
            }
        }

        /* ===== ACCESSIBILITY IMPROVEMENTS ===== */
        @media (prefers-reduced-motion: reduce) {
            .model-card,
            .app-card,
            .feature-item,
            .benefit-item,
            .comparison-item,
            .software-item,
            .service-item,
            .timeline-step,
            .stat-item {
                transition: none;
            }

            .tab-pane,
            .tech-pane {
                animation: none;
            }
        }

        /* ===== FOCUS STYLES ===== */
        .feature-tab:focus,
        .tech-tab:focus {
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }

        .model-card:focus,
        .app-card:focus {
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }

        /* ===== PRINT STYLES ===== */
        @media print {
            .modal-header {
                background: #fff !important;
                color: #000 !important;
            }

            .model-card,
            .app-card,
            .feature-item,
            .benefit-item {
                break-inside: avoid;
                box-shadow: none !important;
                border: 1px solid #000 !important;
            }

            .tab-content {
                display: block !important;
            }

            .tab-pane,
            .tech-pane {
                display: block !important;
                page-break-inside: avoid;
            }
        }

        /* ===== HIGH CONTRAST MODE ===== */
        @media (prefers-contrast: high) {
            .modal-content {
                border: 2px solid #000;
            }

            .model-card,
            .app-card,
            .feature-item {
                border: 2px solid #000 !important;
            }

            .feature-tab.active,
            .tech-tab.active {
                background: #000 !important;
                color: #fff !important;
            }
        }

        /* ===== ANIMATIONS ===== */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .modal-body.animate-fade-in.visible {
            animation: fadeInUp 0.5s ease-out;
        }

        .timeline-item {
            animation: slideIn 0.6s ease-out;
        }

        .timeline-item:nth-child(1) { animation-delay: 0.1s; }
        .timeline-item:nth-child(2) { animation-delay: 0.2s; }
        .timeline-item:nth-child(3) { animation-delay: 0.3s; }
        .timeline-item:nth-child(4) { animation-delay: 0.4s; }
    `;

    // ====================================
    // INYECCIÓN DE ESTILOS
    // ====================================
    function injectModalStyles() {
        // Verificar si los estilos ya fueron inyectados
        if (document.querySelector('#copier-modal-styles')) {
            return;
        }

        const modalStyleSheet = document.createElement('style');
        modalStyleSheet.id = 'copier-modal-styles';
        modalStyleSheet.textContent = modalStyles;
        document.head.appendChild(modalStyleSheet);

        console.log('🎨 Modal styles injected successfully');
    }

    // ====================================
    // OPTIMIZACIONES ESPECÍFICAS PARA MODALES
    // ====================================
    function optimizeModalPerformance() {
        // Lazy load de imágenes en modales
        const modalObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        modalObserver.unobserve(img);
                    }
                }
            });
        });

        // Observar cuando se abren modales
        document.addEventListener('shown.bs.modal', function(e) {
            const modal = e.target;
            const images = modal.querySelectorAll('img[data-src]');
            images.forEach(img => modalObserver.observe(img));

            // Scroll to top of modal
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.scrollTop = 0;
            }

            // Analytics para tiempo en modal
            modal._modalOpenTime = Date.now();
        });

        // Track tiempo en modal
        document.addEventListener('hidden.bs.modal', function(e) {
            const modal = e.target;
            if (modal._modalOpenTime && typeof gtag !== 'undefined') {
                const timeSpent = Date.now() - modal._modalOpenTime;
                gtag('event', 'modal_time_spent', {
                    event_category: 'engagement',
                    value: Math.floor(timeSpent / 1000) // en segundos
                });
            }
        });
    }

    // ====================================
    // MEJORAS DE ACCESIBILIDAD PARA MODALES
    // ====================================
    function enhanceModalAccessibility() {
        // Gestión de focus en modales
        document.addEventListener('shown.bs.modal', function(e) {
            const modal = e.target;
            
            // Focus en el primer elemento focuseable
            const firstFocusable = modal.querySelector(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (firstFocusable) {
                firstFocusable.focus();
            }

            // Trap focus dentro del modal
            trapFocus(modal);
        });

        // Anunciar contenido del modal para lectores de pantalla
        document.addEventListener('shown.bs.modal', function(e) {
            const modal = e.target;
            const title = modal.querySelector('.modal-title')?.textContent;
            
            if (title && window.announceToScreenReader) {
                window.announceToScreenReader(`Modal abierto: ${title}`);
            }
        });
    }

    /**
     * Trap focus dentro del modal
     */
    function trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        function handleTabKey(e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        }

        modal.addEventListener('keydown', handleTabKey);

        // Limpiar event listener cuando se cierra el modal
        modal.addEventListener('hidden.bs.modal', function() {
            modal.removeEventListener('keydown', handleTabKey);
        }, { once: true });
    }

    // ====================================
    // FUNCIONES PÚBLICAS
    // ====================================
    function initModalStyles() {
        injectModalStyles();
        optimizeModalPerformance();
        enhanceModalAccessibility();
    }

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart7 = {
        initModalStyles,
        injectModalStyles,
        optimizeModalPerformance,
        enhanceModalAccessibility,
        trapFocus
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initModalStyles();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 7 cargada (Estilos CSS para Modales)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 8/10: Analytics Avanzado y Tracking de Eventos
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // VARIABLES DE ANALYTICS
    // ====================================
    let analyticsInitialized = false;
    let userEngagementData = {
        mouseMovements: 0,
        clicks: 0,
        keyPresses: 0,
        scrollDepth: 0,
        timeOnPage: 0,
        interactionsCount: 0,
        isEngaged: false
    };

    let scrollDepthMarks = [25, 50, 75, 90, 100];
    let scrollDepthReached = [];
    let maxScrollReached = 0;
    let timeMarks = [30, 60, 120, 300, 600]; // 30s, 1m, 2m, 5m, 10m
    let timeMarksReached = [];
    let pageStartTime = Date.now();

    // ====================================
    // INICIALIZACIÓN DE ANALYTICS
    // ====================================
    function initAdvancedAnalytics() {
        if (analyticsInitialized) return;
        
        console.log('📊 Initializing advanced analytics...');
        
        // Verificar disponibilidad de gtag
        if (typeof gtag === 'undefined') {
            console.warn('⚠️ Google Analytics not available');
            return;
        }

        analyticsInitialized = true;
        
        // Inicializar todos los trackers
        initEventTracking();
        initScrollDepthTracking();
        initTimeTracking();
        initEngagementTracking();
        initPerformanceTracking();
        initErrorTracking();
        initConversionTracking();
        initUserBehaviorTracking();

        // Track page view con datos adicionales
        trackPageView();
        
        console.log('✅ Advanced analytics initialized');
    }

    // ====================================
    // TRACKING DE EVENTOS GENERALES
    // ====================================
    function initEventTracking() {
        document.addEventListener('click', function(e) {
            const target = e.target.closest('a, button, [data-bs-toggle], [role="button"]');
            if (!target) return;

            const trackingData = getElementTrackingData(target);
            if (trackingData) {
                trackEvent(trackingData);
                userEngagementData.clicks++;
                userEngagementData.interactionsCount++;
            }
        });

        // Track form submissions
        document.addEventListener('submit', function(e) {
            const form = e.target;
            const formName = form.name || form.id || 'unnamed_form';
            
            trackEvent({
                event: 'form_submit',
                category: 'conversion',
                label: formName,
                element: formName
            });
        });

        // Track input focus (engagement indicator)
        document.addEventListener('focus', function(e) {
            if (e.target.matches('input, textarea, select')) {
                trackEvent({
                    event: 'form_field_focus',
                    category: 'engagement',
                    label: e.target.name || e.target.id || 'unnamed_field'
                });
            }
        }, true);
    }

    /**
     * Obtener datos de tracking para un elemento
     */
    function getElementTrackingData(element) {
        let trackingData = null;
        const context = getElementContext(element);
        const elementText = element.textContent.trim();

        // CTA buttons
        if (element.matches('a[href="/cotizacion/form"], a[href*="cotizacion"]')) {
            trackingData = {
                event: 'cta_click',
                category: 'conversion',
                label: 'cotizacion_form',
                element: elementText,
                context: context,
                value: 1
            };
        }
        // Contact buttons
        else if (element.matches('a[href="/contactus"], a[href*="contact"]')) {
            trackingData = {
                event: 'contact_click',
                category: 'contact',
                label: 'contact_page',
                element: elementText,
                context: context
            };
        }
        // Service links
        else if (element.matches('a[href="/our-services"], a[href*="services"]')) {
            trackingData = {
                event: 'services_click',
                category: 'navigation',
                label: 'services_page',
                element: elementText,
                context: context
            };
        }
        // WhatsApp button
        else if (element.closest('.whatsapp-btn')) {
            trackingData = {
                event: 'whatsapp_click',
                category: 'contact',
                label: 'floating_button',
                element: 'whatsapp',
                context: 'floating'
            };
        }
        // Quote button
        else if (element.closest('.quote-btn')) {
            trackingData = {
                event: 'quote_button_click',
                category: 'conversion',
                label: 'floating_button',
                element: 'quote',
                context: 'floating',
                value: 1
            };
        }
        // Service cards
        else if (element.closest('.service-card')) {
            const serviceCard = element.closest('.service-card');
            const serviceName = serviceCard.querySelector('h3, h4, h5')?.textContent || 'unknown';
            trackingData = {
                event: 'service_interaction',
                category: 'engagement',
                label: serviceName.toLowerCase().replace(/\s+/g, '_'),
                element: serviceName,
                context: context
            };
        }
        // Benefit cards
        else if (element.closest('.benefit-card')) {
            const benefitCard = element.closest('.benefit-card');
            const benefitName = benefitCard.querySelector('h3, h4, h5')?.textContent || 'unknown';
            const benefitKey = benefitCard.getAttribute('data-benefit');
            trackingData = {
                event: 'benefit_interaction',
                category: 'engagement',
                label: benefitKey || benefitName.toLowerCase().replace(/\s+/g, '_'),
                element: benefitName,
                context: context
            };
        }
        // Brand cards
        else if (element.closest('.brand-card')) {
            const brandCard = element.closest('.brand-card');
            const brandName = brandCard.querySelector('h3, h4, h5')?.textContent || 'unknown';
            const brandKey = brandCard.getAttribute('data-brand');
            trackingData = {
                event: 'brand_interaction',
                category: 'engagement',
                label: brandKey || brandName.toLowerCase().replace(/\s+/g, '_'),
                element: brandName,
                context: context
            };
        }
        // Product cards
        else if (element.closest('.product-card')) {
            const productCard = element.closest('.product-card');
            const productName = productCard.querySelector('h3, h4, h5')?.textContent || 'unknown';
            const productKey = productCard.getAttribute('data-product');
            trackingData = {
                event: 'product_interaction',
                category: 'engagement',
                label: productKey || productName.toLowerCase().replace(/\s+/g, '_'),
                element: productName,
                context: context
            };
        }
        // Modal toggles
        else if (element.closest('[data-bs-toggle="modal"]')) {
            const modalTarget = element.closest('[data-bs-toggle="modal"]').getAttribute('data-bs-target');
            const modalType = modalTarget?.replace('#', '').replace('Modal', '') || 'unknown';
            trackingData = {
                event: 'modal_open',
                category: 'engagement',
                label: modalType,
                element: elementText,
                context: context
            };
        }
        // Testimonial interactions
        else if (element.closest('.testimonial-card')) {
            const testimonialCard = element.closest('.testimonial-card');
            const authorName = testimonialCard.querySelector('h4, h5')?.textContent || 'unknown';
            trackingData = {
                event: 'testimonial_interaction',
                category: 'engagement',
                label: authorName.toLowerCase().replace(/\s+/g, '_'),
                element: authorName,
                context: context
            };
        }
        // Navigation links
        else if (element.matches('nav a, .navbar a')) {
            trackingData = {
                event: 'navigation_click',
                category: 'navigation',
                label: element.getAttribute('href') || elementText.toLowerCase().replace(/\s+/g, '_'),
                element: elementText,
                context: 'navigation'
            };
        }

        return trackingData;
    }

    /**
     * Obtener contexto del elemento
     */
    function getElementContext(element) {
        if (element.closest('.hero-section')) return 'hero';
        if (element.closest('.benefits-section')) return 'benefits';
        if (element.closest('.brands-section')) return 'brands';
        if (element.closest('.products-section')) return 'products';
        if (element.closest('.process-section')) return 'process';
        if (element.closest('.testimonials-section')) return 'testimonials';
        if (element.closest('.faq-section')) return 'faq';
        if (element.closest('.final-cta-section')) return 'final_cta';
        if (element.closest('.whatsapp-float')) return 'whatsapp_float';
        if (element.closest('.quote-float')) return 'quote_float';
        if (element.closest('.modal')) return 'modal';
        if (element.closest('nav, .navbar')) return 'navigation';
        return 'unknown';
    }

    // ====================================
    // TRACKING DE PROFUNDIDAD DE SCROLL
    // ====================================
    function initScrollDepthTracking() {
        const throttledScrollTracker = window.copierHomepagePart1.throttle(function() {
            const scrollPercent = Math.round((window.pageYOffset / (document.body.scrollHeight - window.innerHeight)) * 100);
            
            // Track maximum scroll reached
            if (scrollPercent > maxScrollReached) {
                maxScrollReached = scrollPercent;
                userEngagementData.scrollDepth = scrollPercent;
            }
            
            // Track scroll milestones
            scrollDepthMarks.forEach(mark => {
                if (scrollPercent >= mark && !scrollDepthReached.includes(mark)) {
                    scrollDepthReached.push(mark);
                    
                    trackEvent({
                        event: 'scroll_depth',
                        category: 'engagement',
                        label: `${mark}%`,
                        value: mark
                    });
                    
                    console.log(`📜 Scroll Depth: ${mark}%`);
                }
            });

            // Check for engagement based on scroll
            if (scrollPercent > 25 && !userEngagementData.isEngaged) {
                markUserAsEngaged('scroll_depth');
            }
        }, 500);

        window.addEventListener('scroll', throttledScrollTracker, { passive: true });

        // Track max scroll on page unload
        window.addEventListener('beforeunload', function() {
            if (maxScrollReached > 0) {
                trackEvent({
                    event: 'max_scroll_depth',
                    category: 'engagement',
                    label: `${maxScrollReached}%`,
                    value: maxScrollReached
                }, true); // Send immediately
            }
        });
    }

    // ====================================
    // TRACKING DE TIEMPO EN PÁGINA
    // ====================================
    function initTimeTracking() {
        const timeTracker = setInterval(() => {
            if (document.hidden) return; // No contar tiempo cuando la tab no está visible
            
            const timeSpent = Math.floor((Date.now() - pageStartTime) / 1000);
            userEngagementData.timeOnPage = timeSpent;
            
            timeMarks.forEach(mark => {
                if (timeSpent >= mark && !timeMarksReached.includes(mark)) {
                    timeMarksReached.push(mark);
                    
                    trackEvent({
                        event: 'time_on_page',
                        category: 'engagement',
                        label: `${mark}s`,
                        value: mark
                    });
                    
                    console.log(`⏱️ Time on Page: ${mark}s`);

                    // Mark as engaged after 60 seconds
                    if (mark >= 60 && !userEngagementData.isEngaged) {
                        markUserAsEngaged('time_spent');
                    }
                }
            });
        }, 5000);

        // Clear interval and send final time on page unload
        window.addEventListener('beforeunload', function() {
            clearInterval(timeTracker);
            
            const totalTime = Math.floor((Date.now() - pageStartTime) / 1000);
            if (totalTime > 10) {
                trackEvent({
                    event: 'total_time_on_page',
                    category: 'engagement',
                    label: `${totalTime}s`,
                    value: totalTime
                }, true);
            }
        });
    }

    // ====================================
    // TRACKING DE ENGAGEMENT
    // ====================================
    function initEngagementTracking() {
        // Mouse movement tracking
        const throttledMouseTracker = window.copierHomepagePart1.throttle(function() {
            userEngagementData.mouseMovements++;
            if (userEngagementData.mouseMovements > 10 && !userEngagementData.isEngaged) {
                markUserAsEngaged('mouse_movement');
            }
        }, 1000);

        document.addEventListener('mousemove', throttledMouseTracker, { passive: true });

        // Keyboard tracking
        document.addEventListener('keydown', function() {
            userEngagementData.keyPresses++;
            if (userEngagementData.keyPresses >= 5 && !userEngagementData.isEngaged) {
                markUserAsEngaged('keyboard_usage');
            }
        });

        // Tab visibility tracking
        let tabSwitches = 0;
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                tabSwitches++;
                trackEvent({
                    event: 'tab_hidden',
                    category: 'engagement',
                    label: 'user_left_tab'
                });
            } else {
                if (tabSwitches > 0) {
                    trackEvent({
                        event: 'tab_return',
                        category: 'engagement',
                        label: 'returned_to_tab',
                        value: tabSwitches
                    });
                }
            }
        });

        // Copy/paste tracking (potential lead qualification)
        document.addEventListener('copy', function() {
            trackEvent({
                event: 'content_copy',
                category: 'engagement',
                label: 'user_copied_content'
            });
        });

        // Right-click tracking
        document.addEventListener('contextmenu', function() {
            trackEvent({
                event: 'right_click',
                category: 'engagement',
                label: 'context_menu_opened'
            });
        });
    }

    /**
     * Marcar usuario como engaged
     */
    function markUserAsEngaged(reason) {
        if (userEngagementData.isEngaged) return;
        
        userEngagementData.isEngaged = true;
        
        trackEvent({
            event: 'user_engaged',
            category: 'engagement',
            label: reason,
            value: 1
        });
        
        console.log(`🎯 User Engaged: ${reason}`);
    }

    // ====================================
    // TRACKING DE PERFORMANCE
    // ====================================
    function initPerformanceTracking() {
        if (!('performance' in window)) return;

        window.addEventListener('load', function() {
            setTimeout(() => {
                const perfData = performance.timing;
                const navigation = performance.getEntriesByType('navigation')[0];
                
                if (navigation) {
                    const metrics = {
                        loadTime: Math.round(navigation.loadEventEnd - navigation.fetchStart),
                        domReadyTime: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart),
                        firstByteTime: Math.round(navigation.responseStart - navigation.fetchStart),
                        connectTime: Math.round(navigation.connectEnd - navigation.connectStart),
                        dnsTime: Math.round(navigation.domainLookupEnd - navigation.domainLookupStart)
                    };

                    // Track performance metrics
                    Object.entries(metrics).forEach(([metric, value]) => {
                        if (value > 0) {
                            trackEvent({
                                event: 'performance_metric',
                                category: 'performance',
                                label: metric,
                                value: value
                            });
                        }
                    });

                    console.log(`⚡ Performance metrics:`, metrics);

                    // Track slow loading
                    if (metrics.loadTime > 3000) {
                        trackEvent({
                            event: 'slow_page_load',
                            category: 'performance',
                            label: 'load_time_over_3s',
                            value: metrics.loadTime
                        });
                    }
                }

                // Core Web Vitals (if available)
                if ('PerformanceObserver' in window) {
                    trackCoreWebVitals();
                }
            }, 100);
        });
    }

    /**
     * Track Core Web Vitals
     */
    function trackCoreWebVitals() {
        try {
            // Largest Contentful Paint (LCP)
            new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                trackEvent({
                    event: 'web_vital_lcp',
                    category: 'performance',
                    label: 'largest_contentful_paint',
                    value: Math.round(lastEntry.startTime)
                });
            }).observe({ entryTypes: ['largest-contentful-paint'] });

            // First Input Delay (FID)
            new PerformanceObserver((entryList) => {
                const firstInput = entryList.getEntries()[0];
                trackEvent({
                    event: 'web_vital_fid',
                    category: 'performance',
                    label: 'first_input_delay',
                    value: Math.round(firstInput.processingStart - firstInput.startTime)
                });
            }).observe({ entryTypes: ['first-input'] });

            // Cumulative Layout Shift (CLS)
            let clsValue = 0;
            new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                trackEvent({
                    event: 'web_vital_cls',
                    category: 'performance',
                    label: 'cumulative_layout_shift',
                    value: Math.round(clsValue * 1000) / 1000
                });
            }).observe({ entryTypes: ['layout-shift'] });
        } catch (error) {
            console.warn('⚠️ Core Web Vitals tracking not supported:', error);
        }
    }

    // ====================================
    // TRACKING DE ERRORES
    // ====================================
    function initErrorTracking() {
        // JavaScript errors
        window.addEventListener('error', function(e) {
            trackEvent({
                event: 'javascript_error',
                category: 'error',
                label: e.message,
                element: `${e.filename}:${e.lineno}`
            });
        });

        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', function(e) {
            trackEvent({
                event: 'promise_rejection',
                category: 'error',
                label: e.reason?.toString() || 'unknown_rejection'
            });
        });

        // Image load errors
        document.addEventListener('error', function(e) {
            if (e.target.tagName === 'IMG') {
                trackEvent({
                    event: 'image_load_error',
                    category: 'error',
                    label: e.target.src || 'unknown_image'
                });
            }
        }, true);
    }

    // ====================================
    // TRACKING DE CONVERSIONES
    // ====================================
    function initConversionTracking() {
        // Track when users are close to converting
        document.addEventListener('mouseleave', function(e) {
            if (e.clientY <= 0) { // Mouse left through top of page
                if (userEngagementData.timeOnPage > 30 && !sessionStorage.getItem('exit_intent_tracked')) {
                    trackEvent({
                        event: 'exit_intent',
                        category: 'conversion',
                        label: 'potential_conversion_loss'
                    });
                    sessionStorage.setItem('exit_intent_tracked', 'true');
                }
            }
        });

        // Track form engagement
        document.addEventListener('input', function(e) {
            if (e.target.matches('input[type="email"], input[type="tel"], input[name*="name"]')) {
                if (!sessionStorage.getItem('form_engagement_tracked')) {
                    trackEvent({
                        event: 'form_engagement',
                        category: 'conversion',
                        label: 'user_started_form'
                    });
                    sessionStorage.setItem('form_engagement_tracked', 'true');
                }
            }
        });

        // Track high-intent actions
        const highIntentSelectors = [
            'a[href*="cotizacion"]',
            'a[href*="contact"]',
            '.quote-btn',
            '.whatsapp-btn'
        ];

        highIntentSelectors.forEach(selector => {
            document.addEventListener('click', function(e) {
                if (e.target.matches(selector) || e.target.closest(selector)) {
                    trackEvent({
                        event: 'high_intent_action',
                        category: 'conversion',
                        label: selector.replace(/[^\w]/g, '_'),
                        value: 1
                    });
                }
            });
        });
    }

    // ====================================
    // TRACKING DE COMPORTAMIENTO
    // ====================================
    function initUserBehaviorTracking() {
        // Track reading behavior
        let readingTime = 0;
        const readingTracker = setInterval(() => {
            if (!document.hidden && window.pageYOffset > 100) {
                readingTime += 5;
                if (readingTime % 60 === 0) { // Every minute
                    trackEvent({
                        event: 'reading_time',
                        category: 'engagement',
                        label: 'active_reading',
                        value: readingTime
                    });
                }
            }
        }, 5000);

        window.addEventListener('beforeunload', () => clearInterval(readingTracker));

        // Track search behavior (if search functionality exists)
        document.addEventListener('submit', function(e) {
            if (e.target.matches('form[role="search"], .search-form')) {
                const query = e.target.querySelector('input[type="search"], input[name*="search"]')?.value;
                if (query) {
                    trackEvent({
                        event: 'site_search',
                        category: 'engagement',
                        label: query.toLowerCase().trim()
                    });
                }
            }
        });

        // Track device orientation changes (mobile)
        window.addEventListener('orientationchange', function() {
            trackEvent({
                event: 'orientation_change',
                category: 'device',
                label: screen.orientation?.type || 'unknown'
            });
        });
    }

    // ====================================
    // FUNCIONES DE TRACKING
    // ====================================
    
    /**
     * Track event principal
     */
    function trackEvent(data, immediate = false) {
        if (!analyticsInitialized || typeof gtag === 'undefined') return;

        const eventData = {
            event_category: data.category,
            event_label: data.label,
            value: data.value || undefined,
            custom_parameter_1: data.element || undefined,
            custom_parameter_2: data.context || undefined,
            page_title: document.title,
            page_location: window.location.href
        };

        // Remove undefined values
        Object.keys(eventData).forEach(key => {
            if (eventData[key] === undefined) {
                delete eventData[key];
            }
        });

        if (immediate) {
            // Send immediately (for page unload events)
            gtag('event', data.event, {
                ...eventData,
                transport_type: 'beacon'
            });
        } else {
            gtag('event', data.event, eventData);
        }

        console.log(`📊 Analytics Event:`, data.event, eventData);
    }

    /**
     * Track page view con datos adicionales
     */
    function trackPageView() {
        const deviceInfo = window.copierHomepagePart1?.getDeviceInfo() || {};
        
        gtag('event', 'page_view', {
            page_title: document.title,
            page_location: window.location.href,
            device_type: deviceInfo.isMobile ? 'mobile' : (deviceInfo.isTablet ? 'tablet' : 'desktop'),
            screen_resolution: `${deviceInfo.screenWidth}x${deviceInfo.screenHeight}`,
            viewport_size: `${deviceInfo.viewportWidth}x${deviceInfo.viewportHeight}`,
            connection_type: navigator.connection?.effectiveType || 'unknown',
            referrer: document.referrer || 'direct'
        });
    }

    /**
     * Enviar datos de engagement al final de la sesión
     */
    function sendEngagementSummary() {
        if (!userEngagementData.isEngaged) return;

        trackEvent({
            event: 'engagement_summary',
            category: 'engagement',
            label: 'session_summary',
            value: userEngagementData.interactionsCount
        }, true);

        // Send detailed engagement data
        gtag('event', 'user_engagement_data', {
            event_category: 'engagement',
            mouse_movements: userEngagementData.mouseMovements,
            clicks: userEngagementData.clicks,
            key_presses: userEngagementData.keyPresses,
            max_scroll_depth: userEngagementData.scrollDepth,
            time_on_page: userEngagementData.timeOnPage,
            total_interactions: userEngagementData.interactionsCount,
            transport_type: 'beacon'
        });
    }

    // ====================================
    // EVENT LISTENERS DE CICLO DE VIDA
    // ====================================
    
    // Send engagement summary on page unload
    window.addEventListener('beforeunload', sendEngagementSummary);

    // Send engagement summary on visibility change (mobile)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            sendEngagementSummary();
        }
    });

    // ====================================
    // FUNCIONES PÚBLICAS
    // ====================================
    
    function getEngagementData() {
        return { ...userEngagementData };
    }

    function trackCustomEvent(eventName, category, label, value) {
        trackEvent({
            event: eventName,
            category: category,
            label: label,
            value: value
        });
    }

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart8 = {
        initAdvancedAnalytics,
        trackEvent,
        trackCustomEvent,
        getEngagementData,
        markUserAsEngaged,
        sendEngagementSummary
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            // Esperar un poco para asegurar que gtag esté disponible
            setTimeout(() => {
                initAdvancedAnalytics();
            }, 1000);
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 8 cargada (Analytics Avanzado)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 9/10: Error Handling y Optimizaciones de Dispositivo
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // VARIABLES DE ERROR HANDLING
    // ====================================
    let errorCount = 0;
    let errorLogQueue = [];
    let isOnline = navigator.onLine;
    let connectionQuality = 'unknown';
    let deviceCapabilities = {};

    // ====================================
    // INICIALIZACIÓN DE ERROR HANDLING
    // ====================================
    function initErrorHandling() {
        initGlobalErrorHandlers();
        initNetworkMonitoring();
        initResourceErrorHandling();
        initFallbackMechanisms();
        initErrorReporting();
        
        console.log('🛡️ Error handling initialized');
    }

    // ====================================
    // MANEJADORES GLOBALES DE ERRORES
    // ====================================
    function initGlobalErrorHandlers() {
        // Global JavaScript error handler
        window.addEventListener('error', function(event) {
            const errorInfo = {
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error ? event.error.stack : null,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href,
                errorCount: ++errorCount
            };

            handleError(errorInfo);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', function(event) {
            const errorInfo = {
                type: 'promise_rejection',
                reason: event.reason?.toString() || 'Unknown promise rejection',
                stack: event.reason?.stack || null,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                errorCount: ++errorCount
            };

            handleError(errorInfo);
            
            // Prevent the default browser behavior
            event.preventDefault();
        });

        // Console error override for debugging
        const originalConsoleError = console.error;
        console.error = function(...args) {
            const errorInfo = {
                type: 'console_error',
                message: args.join(' '),
                timestamp: new Date().toISOString(),
                url: window.location.href
            };
            
            handleError(errorInfo);
            originalConsoleError.apply(console, args);
        };
    }

    // ====================================
    // MANEJO DE ERRORES ESPECÍFICOS
    // ====================================
    function handleError(errorInfo) {
        // Log error locally
        console.error(`🚨 ${errorInfo.type}:`, errorInfo);
        
        // Add to error queue
        errorLogQueue.push(errorInfo);
        
        // Keep only last 50 errors
        if (errorLogQueue.length > 50) {
            errorLogQueue = errorLogQueue.slice(-50);
        }

        // Send to analytics if available
        if (typeof gtag !== 'undefined') {
            gtag('event', 'javascript_error', {
                event_category: 'error',
                event_label: errorInfo.type,
                error_message: errorInfo.message?.substring(0, 100) || 'Unknown error',
                error_filename: errorInfo.filename || 'unknown',
                error_line: errorInfo.lineno || 0
            });
        }

        // Send to error tracking service if available
        if (window.errorTrackingService) {
            window.errorTrackingService.logError(errorInfo);
        }

        // Implement fallback mechanisms for critical errors
        implementErrorFallbacks(errorInfo);

        // Show user-friendly error message for critical errors
        if (errorCount > 5) {
            showErrorRecoveryUI();
        }
    }

    // ====================================
    // MONITOREO DE RECURSOS
    // ====================================
    function initResourceErrorHandling() {
        // Image load error handling
        document.addEventListener('error', function(event) {
            if (event.target.tagName === 'IMG') {
                handleImageError(event.target);
            } else if (event.target.tagName === 'SCRIPT') {
                handleScriptError(event.target);
            } else if (event.target.tagName === 'LINK') {
                handleStylesheetError(event.target);
            }
        }, true);

        // Font load error handling
        if ('fonts' in document) {
            document.fonts.addEventListener('loadingerror', function(event) {
                console.warn('⚠️ Font loading error:', event.fontface.family);
                
                // Fallback to system fonts
                document.documentElement.style.setProperty('--font-family-fallback', 'system-ui, -apple-system, sans-serif');
            });
        }
    }

    /**
     * Manejar errores de imágenes
     */
    function handleImageError(img) {
        console.warn('⚠️ Image loading error:', img.src);
        
        // Try to load from alternative source
        if (img.dataset.fallback && !img.dataset.errorHandled) {
            img.dataset.errorHandled = 'true';
            img.src = img.dataset.fallback;
            return;
        }
        
        // Show placeholder
        if (!img.dataset.errorHandled) {
            img.dataset.errorHandled = 'true';
            img.style.display = 'none';
            
            // Create placeholder
            const placeholder = document.createElement('div');
            placeholder.className = 'image-error-placeholder';
            placeholder.innerHTML = '<i class="fas fa-image"></i><span>Imagen no disponible</span>';
            placeholder.style.cssText = `
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8f9fa;
                border: 1px dashed #dee2e6;
                color: #6c757d;
                font-size: 0.875rem;
                min-height: 100px;
                gap: 8px;
            `;
            
            img.parentNode.insertBefore(placeholder, img);
        }
    }

    /**
     * Manejar errores de scripts
     */
    function handleScriptError(script) {
        console.error('🚨 Script loading error:', script.src);
        
        const errorInfo = {
            type: 'script_load_error',
            src: script.src,
            timestamp: new Date().toISOString()
        };
        
        handleError(errorInfo);
        
        // Try to load from CDN fallback
        if (script.dataset.fallback && !script.dataset.errorHandled) {
            script.dataset.errorHandled = 'true';
            const fallbackScript = document.createElement('script');
            fallbackScript.src = script.dataset.fallback;
            fallbackScript.async = script.async;
            fallbackScript.defer = script.defer;
            document.head.appendChild(fallbackScript);
        }
    }

    /**
     * Manejar errores de CSS
     */
    function handleStylesheetError(link) {
        console.warn('⚠️ Stylesheet loading error:', link.href);
        
        // Apply minimal fallback styles
        if (!document.querySelector('#fallback-styles')) {
            const fallbackCSS = document.createElement('style');
            fallbackCSS.id = 'fallback-styles';
            fallbackCSS.textContent = `
                body { font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; }
                .btn { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 0.25rem; }
                .card { border: 1px solid #dee2e6; border-radius: 0.25rem; padding: 1rem; margin-bottom: 1rem; }
            `;
            document.head.appendChild(fallbackCSS);
        }
    }

    // ====================================
    // MONITOREO DE RED
    // ====================================
    function initNetworkMonitoring() {
        // Network status monitoring
        function updateOnlineStatus() {
            const wasOnline = isOnline;
            isOnline = navigator.onLine;
            
            if (wasOnline !== isOnline) {
                if (isOnline) {
                    handleNetworkRestored();
                } else {
                    handleNetworkLoss();
                }
            }
        }

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);

        // Connection quality monitoring
        if ('connection' in navigator) {
            const connection = navigator.connection;
            connectionQuality = connection.effectiveType || 'unknown';
            
            connection.addEventListener('change', function() {
                const newQuality = connection.effectiveType;
                if (newQuality !== connectionQuality) {
                    handleConnectionQualityChange(connectionQuality, newQuality);
                    connectionQuality = newQuality;
                }
            });

            // Apply optimizations based on connection
            applyConnectionOptimizations(connection);
        }
    }

    /**
     * Manejar pérdida de conexión
     */
    function handleNetworkLoss() {
        console.warn('📡 Network connection lost');
        
        showOfflineMessage();
        
        // Disable non-essential features
        disableNonEssentialFeatures();
        
        // Cache critical data
        cacheCriticalData();
        
        if (typeof gtag !== 'undefined') {
            gtag('event', 'network_offline', {
                event_category: 'connectivity',
                event_label: 'connection_lost'
            });
        }
    }

    /**
     * Manejar restauración de conexión
     */
    function handleNetworkRestored() {
        console.log('📡 Network connection restored');
        
        hideOfflineMessage();
        
        // Re-enable features
        enableAllFeatures();
        
        // Sync pending data
        syncPendingData();
        
        if (typeof gtag !== 'undefined') {
            gtag('event', 'network_online', {
                event_category: 'connectivity',
                event_label: 'connection_restored'
            });
        }
    }

    /**
     * Manejar cambios en calidad de conexión
     */
    function handleConnectionQualityChange(oldQuality, newQuality) {
        console.log(`📡 Connection quality changed: ${oldQuality} → ${newQuality}`);
        
        // Apply appropriate optimizations
        if (newQuality === 'slow-2g' || newQuality === '2g') {
            enableSlowConnectionMode();
        } else if (newQuality === '3g') {
            enableMediumConnectionMode();
        } else {
            enableHighSpeedMode();
        }
        
        if (typeof gtag !== 'undefined') {
            gtag('event', 'connection_quality_change', {
                event_category: 'connectivity',
                event_label: `${oldQuality}_to_${newQuality}`
            });
        }
    }

    // ====================================
    // OPTIMIZACIONES DE DISPOSITIVO
    // ====================================
    function initDeviceOptimizations() {
        deviceCapabilities = analyzeDeviceCapabilities();
        applyDeviceOptimizations(deviceCapabilities);
        
        console.log('📱 Device optimizations applied:', deviceCapabilities);
    }

    /**
     * Analizar capacidades del dispositivo
     */
    function analyzeDeviceCapabilities() {
        const deviceInfo = window.copierHomepagePart1?.getDeviceInfo() || {};
        
        return {
            // Hardware capabilities
            isMobile: deviceInfo.isMobile,
            isTablet: deviceInfo.isTablet,
            isTouch: deviceInfo.isTouch,
            screenSize: deviceInfo.screenWidth * deviceInfo.screenHeight,
            pixelRatio: deviceInfo.pixelRatio,
            
            // Memory (if available)
            deviceMemory: navigator.deviceMemory || 'unknown',
            
            // CPU cores (if available)
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            
            // Connection
            connectionType: navigator.connection?.type || 'unknown',
            effectiveType: navigator.connection?.effectiveType || 'unknown',
            saveData: navigator.connection?.saveData || false,
            
            // Battery (if available)
            batteryLevel: 'unknown',
            
            // Performance
            supportsIntersectionObserver: 'IntersectionObserver' in window,
            supportsServiceWorker: 'serviceWorker' in navigator,
            supportsWebP: false, // Will be detected separately
            
            // Preferences
            prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            prefersHighContrast: window.matchMedia('(prefers-contrast: high)').matches,
            prefersDarkMode: window.matchMedia('(prefers-color-scheme: dark)').matches
        };
    }

    /**
     * Aplicar optimizaciones basadas en dispositivo
     */
    function applyDeviceOptimizations(capabilities) {
        // Low-end device optimizations
        if (isLowEndDevice(capabilities)) {
            enableLowEndMode();
        }
        
        // Mobile-specific optimizations
        if (capabilities.isMobile) {
            enableMobileOptimizations();
        }
        
        // Touch device optimizations
        if (capabilities.isTouch) {
            enableTouchOptimizations();
        }
        
        // High DPI optimizations
        if (capabilities.pixelRatio > 2) {
            enableHighDPIOptimizations();
        }
        
        // Accessibility preferences
        if (capabilities.prefersReducedMotion) {
            enableReducedMotionMode();
        }
        
        if (capabilities.prefersHighContrast) {
            enableHighContrastMode();
        }
        
        // Data saver mode
        if (capabilities.saveData) {
            enableDataSaverMode();
        }
    }

    /**
     * Detectar dispositivos de baja gama
     */
    function isLowEndDevice(capabilities) {
        const indicators = [
            capabilities.deviceMemory <= 2,
            capabilities.hardwareConcurrency <= 2,
            capabilities.screenSize < 500000, // Very small screen
            capabilities.effectiveType === 'slow-2g' || capabilities.effectiveType === '2g'
        ];
        
        return indicators.filter(Boolean).length >= 2;
    }

    // ====================================
    // MODOS DE OPTIMIZACIÓN
    // ====================================
    
    /**
     * Modo de dispositivo de baja gama
     */
    function enableLowEndMode() {
        document.documentElement.classList.add('low-end-device');
        
        // Reduce animations
        document.documentElement.classList.add('reduce-motion');
        
        // Disable parallax
        document.documentElement.classList.add('disable-parallax');
        
        // Reduce image quality
        document.documentElement.classList.add('low-quality-images');
        
        console.log('📱 Low-end device mode enabled');
    }

    /**
     * Optimizaciones móviles
     */
    function enableMobileOptimizations() {
        document.documentElement.classList.add('mobile-device');
        
        // Optimize touch targets
        document.body.style.touchAction = 'manipulation';
        
        // Prevent zoom on inputs
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport && !viewport.content.includes('user-scalable=no')) {
            viewport.content += ', user-scalable=no';
        }
        
        // Optimize scrolling
        document.body.style.webkitOverflowScrolling = 'touch';
        
        console.log('📱 Mobile optimizations enabled');
    }

    /**
     * Optimizaciones para dispositivos táctiles
     */
    function enableTouchOptimizations() {
        document.documentElement.classList.add('touch-device');
        
        // Increase touch target sizes
        const style = document.createElement('style');
        style.textContent = `
            .touch-device button,
            .touch-device a,
            .touch-device .btn {
                min-height: 44px;
                min-width: 44px;
            }
            .touch-device .card {
                margin-bottom: 16px;
            }
        `;
        document.head.appendChild(style);
        
        console.log('👆 Touch optimizations enabled');
    }

    /**
     * Modo de conexión lenta
     */
    function enableSlowConnectionMode() {
        document.documentElement.classList.add('slow-connection');
        
        // Disable autoplay videos
        const videos = document.querySelectorAll('video[autoplay]');
        videos.forEach(video => video.removeAttribute('autoplay'));
        
        // Reduce image quality
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.dataset.lowQuality) {
                img.src = img.dataset.lowQuality;
            }
        });
        
        console.log('🐌 Slow connection mode enabled');
    }

    /**
     * Modo de ahorro de datos
     */
    function enableDataSaverMode() {
        document.documentElement.classList.add('data-saver');
        
        // Disable non-essential images
        const decorativeImages = document.querySelectorAll('img[alt=""], img[role="presentation"]');
        decorativeImages.forEach(img => img.style.display = 'none');
        
        // Disable background images
        const style = document.createElement('style');
        style.textContent = `
            .data-saver * {
                background-image: none !important;
            }
        `;
        document.head.appendChild(style);
        
        console.log('💾 Data saver mode enabled');
    }

    /**
     * Modo de movimiento reducido
     */
    function enableReducedMotionMode() {
        document.documentElement.classList.add('reduce-motion');
        
        const style = document.createElement('style');
        style.textContent = `
            .reduce-motion *,
            .reduce-motion *::before,
            .reduce-motion *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
        
        console.log('🎭 Reduced motion mode enabled');
    }

    // ====================================
    // MECANISMOS DE FALLBACK
    // ====================================
    function initFallbackMechanisms() {
        // Service Worker fallback
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw-fallback.js')
                .catch(error => {
                    console.warn('⚠️ Service Worker registration failed:', error);
                });
        }
        
        // Local storage fallback
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
        } catch (e) {
            // Implement localStorage fallback using memory
            window.localStorageFallback = {};
            window.localStorage = {
                setItem: (key, value) => window.localStorageFallback[key] = value,
                getItem: (key) => window.localStorageFallback[key] || null,
                removeItem: (key) => delete window.localStorageFallback[key],
                clear: () => window.localStorageFallback = {}
            };
        }
    }

    function implementErrorFallbacks(errorInfo) {
        // Critical JavaScript error fallbacks
        if (errorInfo.type === 'javascript_error' && errorInfo.message.includes('Bootstrap')) {
            loadBootstrapFallback();
        }
        
        // Analytics fallback
        if (errorInfo.message.includes('gtag')) {
            implementAnalyticsFallback();
        }
    }

    function loadBootstrapFallback() {
        if (!document.querySelector('#bootstrap-fallback')) {
            const fallbackCSS = document.createElement('link');
            fallbackCSS.id = 'bootstrap-fallback';
            fallbackCSS.rel = 'stylesheet';
            fallbackCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css';
            document.head.appendChild(fallbackCSS);
        }
    }

    function implementAnalyticsFallback() {
        // Simple analytics fallback
        window.gtag = window.gtag || function() {
            console.log('Analytics fallback:', arguments);
        };
    }

    // ====================================
    // UI DE RECUPERACIÓN DE ERRORES
    // ====================================
    function showErrorRecoveryUI() {
        if (document.querySelector('.error-recovery-ui')) return;
        
        const errorUI = document.createElement('div');
        errorUI.className = 'error-recovery-ui';
        errorUI.innerHTML = `
            <div class="error-recovery-content">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>Algo salió mal</h4>
                <p>Hemos detectado algunos problemas técnicos. Puedes intentar:</p>
                <div class="error-recovery-actions">
                    <button onclick="window.location.reload()" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Recargar página
                    </button>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" class="btn btn-secondary">
                        <i class="fas fa-times"></i> Continuar
                    </button>
                </div>
                <details class="error-details">
                    <summary>Detalles técnicos</summary>
                    <pre id="error-log"></pre>
                </details>
            </div>
        `;
        
        errorUI.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        `;
        
        const errorContent = errorUI.querySelector('.error-recovery-content');
        errorContent.style.cssText = `
            background: white;
            color: #333;
            padding: 2rem;
            border-radius: 8px;
            max-width: 500px;
            text-align: center;
        `;
        
        // Add error log
        const errorLog = errorUI.querySelector('#error-log');
        errorLog.textContent = JSON.stringify(errorLogQueue.slice(-5), null, 2);
        
        document.body.appendChild(errorUI);
    }

    // ====================================
    // UTILIDADES DE RED
    // ====================================
    function showOfflineMessage() {
        if (document.querySelector('.offline-message')) return;
        
        const offlineMessage = document.createElement('div');
        offlineMessage.className = 'offline-message';
        offlineMessage.innerHTML = `
            <div class="offline-content">
                <i class="fas fa-wifi-slash"></i>
                <span>Sin conexión a internet</span>
                <button onclick="window.location.reload()" class="btn btn-sm btn-light">
                    <i class="fas fa-redo"></i> Reintentar
                </button>
            </div>
        `;
        offlineMessage.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #dc3545;
            color: white;
            padding: 12px;
            text-align: center;
            z-index: 9999;
            transform: translateY(-100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(offlineMessage);
        
        setTimeout(() => {
            offlineMessage.style.transform = 'translateY(0)';
        }, 100);
    }

    function hideOfflineMessage() {
        const offlineMessage = document.querySelector('.offline-message');
        if (offlineMessage) {
            offlineMessage.style.transform = 'translateY(-100%)';
            setTimeout(() => {
                offlineMessage.remove();
            }, 300);
        }
    }

    function disableNonEssentialFeatures() {
        // Disable animations
        document.documentElement.classList.add('offline-mode');
        
        // Disable auto-refresh features
        const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
        autoRefreshElements.forEach(el => el.dataset.autoRefreshDisabled = 'true');
    }

    function enableAllFeatures() {
        document.documentElement.classList.remove('offline-mode');
        
        // Re-enable auto-refresh
        const disabledElements = document.querySelectorAll('[data-auto-refresh-disabled]');
        disabledElements.forEach(el => el.removeAttribute('data-auto-refresh-disabled'));
    }

    function cacheCriticalData() {
        // Cache current page state
        try {
            const pageState = {
                url: window.location.href,
                timestamp: Date.now(),
                scrollPosition: window.pageYOffset,
                formData: gatherFormData()
            };
            localStorage.setItem('copier_page_state', JSON.stringify(pageState));
        } catch (e) {
            console.warn('⚠️ Could not cache page state:', e);
        }
    }

    function gatherFormData() {
        const formData = {};
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.name && input.value) {
                formData[input.name] = input.value;
            }
        });
        return formData;
    }

    function syncPendingData() {
        // Sync any pending analytics data
        if (window.copierHomepagePart8) {
            window.copierHomepagePart8.sendEngagementSummary();
        }
        
        // Sync form data if available
        try {
            const pageState = JSON.parse(localStorage.getItem('copier_page_state') || '{}');
            if (pageState.formData) {
                restoreFormData(pageState.formData);
                localStorage.removeItem('copier_page_state');
            }
        } catch (e) {
            console.warn('⚠️ Could not sync pending data:', e);
        }
    }

    function restoreFormData(formData) {
        Object.entries(formData).forEach(([name, value]) => {
            const input = document.querySelector(`[name="${name}"]`);
            if (input) {
                input.value = value;
            }
        });
    }

    // ====================================
    // CONEXIÓN CON APIS
    // ====================================
    function applyConnectionOptimizations(connection) {
        if (connection.saveData) {
            enableDataSaverMode();
        }
        
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            enableSlowConnectionMode();
        }
        
        // Adjust image loading strategy
        if (connection.downlink < 1) {
            document.documentElement.classList.add('low-bandwidth');
        }
    }

    function enableMediumConnectionMode() {
        document.documentElement.classList.remove('slow-connection');
        document.documentElement.classList.add('medium-connection');
        console.log('📶 Medium connection mode enabled');
    }

    function enableHighSpeedMode() {
        document.documentElement.classList.remove('slow-connection', 'medium-connection');
        document.documentElement.classList.add('high-speed-connection');
        console.log('🚀 High speed mode enabled');
    }

    function enableHighDPIOptimizations() {
        document.documentElement.classList.add('high-dpi');
        console.log('🖥️ High DPI optimizations enabled');
    }

    function enableHighContrastMode() {
        document.documentElement.classList.add('high-contrast');
        console.log('🔆 High contrast mode enabled');
    }

    // ====================================
    // REPORTING DE ERRORES
    // ====================================
    function initErrorReporting() {
        // Send error summary periodically
        setInterval(() => {
            if (errorLogQueue.length > 0) {
                sendErrorReport();
            }
        }, 60000); // Every minute
        
        // Send on page unload
        window.addEventListener('beforeunload', sendErrorReport);
    }

    function sendErrorReport() {
        if (errorLogQueue.length === 0) return;
        
        const report = {
            errors: errorLogQueue.slice(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            deviceCapabilities: deviceCapabilities,
            connectionQuality: connectionQuality,
            isOnline: isOnline
        };
        
        // Send to analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'error_report', {
                event_category: 'error',
                event_label: 'batch_report',
                error_count: errorLogQueue.length,
                transport_type: 'beacon'
            });
        }
        
        // Clear processed errors
        errorLogQueue = [];
        
        console.log('📋 Error report sent:', report);
    }

    // ====================================
    // FUNCIONES PÚBLICAS
    // ====================================
    function getErrorLog() {
        return [...errorLogQueue];
    }

    function clearErrorLog() {
        errorLogQueue = [];
        errorCount = 0;
    }

    function getDeviceCapabilities() {
        return { ...deviceCapabilities };
    }

    function forceErrorRecovery() {
        showErrorRecoveryUI();
    }

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart9 = {
        initErrorHandling,
        initDeviceOptimizations,
        handleError,
        getErrorLog,
        clearErrorLog,
        getDeviceCapabilities,
        forceErrorRecovery,
        showOfflineMessage,
        hideOfflineMessage
    };

    // Auto-inicialización
    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('.copier-modern-homepage')) {
            initErrorHandling();
            initDeviceOptimizations();
        }
    });

    // Debug info
    console.log('📦 Copier Homepage - Parte 9 cargada (Error Handling y Optimizaciones)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 10/10: Inicialización Final y Debug Mode
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // VARIABLES DE INICIALIZACIÓN
    // ====================================
    let initializationStartTime = performance.now();
    let initializationSteps = [];
    let isDebugMode = false;
    let debugPanel = null;
    let performanceMetrics = {};

    // ====================================
    // CONFIGURACIÓN Y CONSTANTES
    // ====================================
    const SCRIPT_VERSION = '1.0.0';
    const DEBUG_STORAGE_KEY = 'copier_debug_mode';
    const PERFORMANCE_STORAGE_KEY = 'copier_performance_data';
    
    const INITIALIZATION_STEPS = [
        'DOM Content Loaded',
        'Basic Utilities',
        'Animations and Scroll',
        'Floating Buttons',
        'Performance Optimizations',
        'Modals System',
        'CSS Styles',
        'Analytics',
        'Error Handling',
        'Final Setup'
    ];

    // ====================================
    // INICIALIZACIÓN PRINCIPAL
    // ====================================
    function initializeFinalSetup() {
        console.log('🚀 Starting final Copier Homepage initialization...');
        
        // Detectar modo debug
        detectDebugMode();
        
        // Verificar prerequisitos
        checkPrerequisites();
        
        // Inicializar sistemas finales
        initializeFinalSystems();
        
        // Configurar monitoreo de rendimiento
        setupPerformanceMonitoring();
        
        // Configurar modo debug si está activo
        if (isDebugMode) {
            setupDebugMode();
        }
        
        // Marcar como completamente cargado
        markAsFullyLoaded();
        
        console.log('✅ Copier Homepage initialization completed');
    }

    // ====================================
    // DETECCIÓN DE MODO DEBUG
    // ====================================
    function detectDebugMode() {
        const urlParams = new URLSearchParams(window.location.search);
        const debugFromURL = urlParams.get('debug') === 'true';
        const debugFromStorage = localStorage.getItem(DEBUG_STORAGE_KEY) === 'true';
        const debugFromHost = window.location.hostname === 'localhost' || 
                             window.location.hostname.includes('dev') ||
                             window.location.hostname.includes('staging');

        isDebugMode = debugFromURL || debugFromStorage || debugFromHost;
        
        if (isDebugMode) {
            console.log('🐛 Debug mode activated');
            document.documentElement.classList.add('debug-mode');
            localStorage.setItem(DEBUG_STORAGE_KEY, 'true');
        }
    }

    // ====================================
    // VERIFICACIÓN DE PREREQUISITOS
    // ====================================
    function checkPrerequisites() {
        const requiredParts = [
            'copierHomepagePart1',
            'copierHomepagePart2', 
            'copierHomepagePart3',
            'copierHomepagePart4',
            'copierHomepagePart5',
            'copierHomepagePart6',
            'copierHomepagePart7',
            'copierHomepagePart8',
            'copierHomepagePart9'
        ];

        const missingParts = requiredParts.filter(part => !window[part]);
        
        if (missingParts.length > 0) {
            console.error('🚨 Missing required script parts:', missingParts);
            showFallbackUI(missingParts);
            return false;
        }

        console.log('✅ All script parts loaded successfully');
        return true;
    }

    // ====================================
    // INICIALIZACIÓN DE SISTEMAS FINALES
    // ====================================
    function initializeFinalSystems() {
        try {
            // Inicializar lazy loading avanzado
            initAdvancedLazyLoading();
            
            // Configurar service worker
            setupServiceWorker();
            
            // Inicializar PWA features
            initPWAFeatures();
            
            // Configurar shortcuts de teclado
            setupKeyboardShortcuts();
            
            // Inicializar tooltips globales
            initGlobalTooltips();
            
            // Configurar auto-save de estado
            setupAutoSave();
            
            console.log('🔧 Final systems initialized');
        } catch (error) {
            console.error('🚨 Error initializing final systems:', error);
            if (window.copierHomepagePart9) {
                window.copierHomepagePart9.handleError({
                    type: 'initialization_error',
                    message: error.message,
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                });
            }
        }
    }

    // ====================================
    // LAZY LOADING AVANZADO
    // ====================================
    function initAdvancedLazyLoading() {
        if (!('IntersectionObserver' in window)) return;

        // Lazy loading para secciones pesadas
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const section = entry.target;
                    
                    // Cargar contenido diferido
                    if (section.dataset.lazyContent) {
                        loadSectionContent(section);
                    }
                    
                    // Inicializar componentes específicos
                    if (section.classList.contains('testimonials-section')) {
                        initTestimonialsCarousel(section);
                    }
                    
                    if (section.classList.contains('charts-section')) {
                        initChartsSection(section);
                    }
                    
                    sectionObserver.unobserve(section);
                }
            });
        }, { threshold: 0.1 });

        // Observar secciones que requieren lazy loading
        document.querySelectorAll('[data-lazy-content], .testimonials-section, .charts-section').forEach(section => {
            sectionObserver.observe(section);
        });
    }

    /**
     * Cargar contenido de sección de forma diferida
     */
    function loadSectionContent(section) {
        const contentUrl = section.dataset.lazyContent;
        if (!contentUrl) return;

        fetch(contentUrl)
            .then(response => response.text())
            .then(html => {
                section.innerHTML = html;
                section.removeAttribute('data-lazy-content');
                section.classList.add('lazy-loaded');
                
                // Reinicializar scripts si es necesario
                const scripts = section.querySelectorAll('script');
                scripts.forEach(script => {
                    const newScript = document.createElement('script');
                    newScript.textContent = script.textContent;
                    script.parentNode.replaceChild(newScript, script);
                });
                
                console.log(`📦 Loaded lazy content for: ${section.className}`);
            })
            .catch(error => {
                console.error('❌ Error loading lazy content:', error);
                section.innerHTML = '<div class="alert alert-warning">Error cargando contenido</div>';
            });
    }

    /**
     * Inicializar carousel de testimonios
     */
    function initTestimonialsCarousel(section) {
        const testimonialCards = section.querySelectorAll('.testimonial-card');
        if (testimonialCards.length <= 3) return;

        // Crear carousel container
        const carousel = document.createElement('div');
        carousel.className = 'testimonials-carousel';
        carousel.innerHTML = `
            <div class="carousel-container">
                <div class="carousel-track"></div>
                <button class="carousel-btn prev" aria-label="Anterior">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <button class="carousel-btn next" aria-label="Siguiente">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
            <div class="carousel-indicators"></div>
        `;

        // Mover cards al carousel
        const track = carousel.querySelector('.carousel-track');
        testimonialCards.forEach(card => track.appendChild(card));

        // Reemplazar contenido original
        section.innerHTML = '';
        section.appendChild(carousel);

        // Inicializar funcionalidad del carousel
        setupCarouselControls(carousel);
        
        console.log('🎠 Testimonials carousel initialized');
    }

    /**
     * Configurar controles del carousel
     */
    function setupCarouselControls(carousel) {
        const track = carousel.querySelector('.carousel-track');
        const cards = track.querySelectorAll('.testimonial-card');
        const prevBtn = carousel.querySelector('.prev');
        const nextBtn = carousel.querySelector('.next');
        const indicators = carousel.querySelector('.carousel-indicators');
        
        let currentIndex = 0;
        const cardWidth = 320; // Width including margin
        
        // Crear indicadores
        cards.forEach((_, index) => {
            const indicator = document.createElement('button');
            indicator.className = `indicator ${index === 0 ? 'active' : ''}`;
            indicator.addEventListener('click', () => goToSlide(index));
            indicators.appendChild(indicator);
        });

        function goToSlide(index) {
            currentIndex = index;
            track.style.transform = `translateX(-${index * cardWidth}px)`;
            
            // Update indicators
            indicators.querySelectorAll('.indicator').forEach((indicator, i) => {
                indicator.classList.toggle('active', i === index);
            });
        }

        prevBtn.addEventListener('click', () => {
            currentIndex = currentIndex > 0 ? currentIndex - 1 : cards.length - 1;
            goToSlide(currentIndex);
        });

        nextBtn.addEventListener('click', () => {
            currentIndex = currentIndex < cards.length - 1 ? currentIndex + 1 : 0;
            goToSlide(currentIndex);
        });

        // Auto-play
        setInterval(() => {
            if (!carousel.matches(':hover')) {
                nextBtn.click();
            }
        }, 5000);
    }

    // ====================================
    // SERVICE WORKER
    // ====================================
    function setupServiceWorker() {
        if (!('serviceWorker' in navigator)) return;

        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('🔧 Service Worker registered:', registration);
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch(error => {
                console.warn('⚠️ Service Worker registration failed:', error);
            });

        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', event => {
            if (event.data.type === 'CACHE_UPDATED') {
                console.log('📦 Cache updated by service worker');
            }
        });
    }

    /**
     * Mostrar notificación de actualización
     */
    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="update-content">
                <i class="fas fa-download"></i>
                <span>Nueva versión disponible</span>
                <button onclick="window.location.reload()" class="btn btn-sm btn-primary">
                    Actualizar
                </button>
                <button onclick="this.parentElement.parentElement.remove()" class="btn btn-sm btn-secondary">
                    Después
                </button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 300px;
        `;
        
        document.body.appendChild(notification);
    }

    // ====================================
    // PWA FEATURES
    // ====================================
    function initPWAFeatures() {
        // Install prompt
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            showInstallButton();
        });

        // Track installation
        window.addEventListener('appinstalled', () => {
            console.log('📱 PWA installed');
            if (typeof gtag !== 'undefined') {
                gtag('event', 'pwa_installed', {
                    event_category: 'engagement',
                    event_label: 'app_installed'
                });
            }
        });

        function showInstallButton() {
            const installBtn = document.createElement('button');
            installBtn.textContent = '📱 Instalar App';
            installBtn.className = 'btn btn-outline-primary btn-sm';
            installBtn.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 1000;
            `;
            
            installBtn.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'pwa_install_prompt', {
                            event_category: 'engagement',
                            event_label: outcome
                        });
                    }
                    
                    deferredPrompt = null;
                    installBtn.remove();
                }
            });
            
            document.body.appendChild(installBtn);
        }
    }

    // ====================================
    // SHORTCUTS DE TECLADO
    // ====================================
    function setupKeyboardShortcuts() {
        const shortcuts = {
            'ctrl+k': () => focusSearch(),
            'ctrl+/': () => showKeyboardHelp(),
            'alt+c': () => openContactModal(),
            'alt+q': () => openQuoteModal(),
            'esc': () => closeActiveModal(),
            'ctrl+shift+d': () => toggleDebugMode()
        };

        document.addEventListener('keydown', (e) => {
            const key = `${e.ctrlKey ? 'ctrl+' : ''}${e.altKey ? 'alt+' : ''}${e.shiftKey ? 'shift+' : ''}${e.key.toLowerCase()}`;
            
            if (shortcuts[key]) {
                e.preventDefault();
                shortcuts[key]();
            }
        });

        function focusSearch() {
            const searchInput = document.querySelector('input[type="search"], .search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        function showKeyboardHelp() {
            const helpModal = document.createElement('div');
            helpModal.className = 'keyboard-help-modal';
            helpModal.innerHTML = `
                <div class="modal-overlay" onclick="this.parentElement.remove()">
                    <div class="modal-content" onclick="event.stopPropagation()">
                        <h4>Atajos de Teclado</h4>
                        <div class="shortcuts-list">
                            <div class="shortcut-item">
                                <kbd>Ctrl</kbd> + <kbd>K</kbd>
                                <span>Buscar</span>
                            </div>
                            <div class="shortcut-item">
                                <kbd>Alt</kbd> + <kbd>C</kbd>
                                <span>Contacto</span>
                            </div>
                            <div class="shortcut-item">
                                <kbd>Alt</kbd> + <kbd>Q</kbd>
                                <span>Cotización</span>
                            </div>
                            <div class="shortcut-item">
                                <kbd>Esc</kbd>
                                <span>Cerrar modal</span>
                            </div>
                        </div>
                        <button onclick="this.closest('.keyboard-help-modal').remove()" class="btn btn-primary">
                            Cerrar
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(helpModal);
        }

        function openContactModal() {
            const contactBtn = document.querySelector('a[href="/contactus"], a[href*="contact"]');
            if (contactBtn) contactBtn.click();
        }

        function openQuoteModal() {
            const quoteBtn = document.querySelector('a[href="/cotizacion"], .quote-btn');
            if (quoteBtn) quoteBtn.click();
        }

        function closeActiveModal() {
            const activeModal = document.querySelector('.modal.show');
            if (activeModal) {
                const bsModal = bootstrap.Modal.getInstance(activeModal);
                if (bsModal) bsModal.hide();
            }
        }

        function toggleDebugMode() {
            isDebugMode = !isDebugMode;
            localStorage.setItem(DEBUG_STORAGE_KEY, isDebugMode.toString());
            
            if (isDebugMode) {
                setupDebugMode();
            } else {
                teardownDebugMode();
            }
        }
    }

    // ====================================
    // TOOLTIPS GLOBALES
    // ====================================
    function initGlobalTooltips() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }

        // Custom tooltips for specific elements
        const customTooltips = document.querySelectorAll('[data-tooltip]');
        customTooltips.forEach(element => {
            setupCustomTooltip(element);
        });
    }

    function setupCustomTooltip(element) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = element.dataset.tooltip;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.875rem;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        `;

        document.body.appendChild(tooltip);

        element.addEventListener('mouseenter', (e) => {
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
            tooltip.style.opacity = '1';
        });

        element.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
        });
    }

    // ====================================
    // AUTO-SAVE DE ESTADO
    // ====================================
    function setupAutoSave() {
        const forms = document.querySelectorAll('form[data-auto-save]');
        
        forms.forEach(form => {
            const saveKey = `copier_form_${form.id || 'default'}`;
            
            // Restore saved data
            try {
                const savedData = JSON.parse(localStorage.getItem(saveKey) || '{}');
                Object.entries(savedData).forEach(([name, value]) => {
                    const input = form.querySelector(`[name="${name}"]`);
                    if (input && input.type !== 'password') {
                        input.value = value;
                    }
                });
            } catch (e) {
                console.warn('⚠️ Could not restore form data:', e);
            }
            
            // Save on input
            form.addEventListener('input', window.copierHomepagePart1.debounce(() => {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());
                
                // Remove sensitive data
                delete data.password;
                delete data.credit_card;
                
                localStorage.setItem(saveKey, JSON.stringify(data));
            }, 1000));
            
            // Clear on submit
            form.addEventListener('submit', () => {
                localStorage.removeItem(saveKey);
            });
        });
    }

    // ====================================
    // MONITOREO DE RENDIMIENTO
    // ====================================
    function setupPerformanceMonitoring() {
        if (!('performance' in window)) return;

        // Measure initialization time
        const initializationTime = performance.now() - initializationStartTime;
        performanceMetrics.initializationTime = initializationTime;

        // Memory usage (if available)
        if ('memory' in performance) {
            performanceMetrics.memoryUsage = {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit
            };
        }

        // Resource timing
        const navigationEntry = performance.getEntriesByType('navigation')[0];
        if (navigationEntry) {
            performanceMetrics.navigation = {
                domContentLoaded: navigationEntry.domContentLoadedEventEnd - navigationEntry.navigationStart,
                loadComplete: navigationEntry.loadEventEnd - navigationEntry.navigationStart,
                firstByte: navigationEntry.responseStart - navigationEntry.requestStart
            };
        }

        // Long tasks monitoring (if available)
        if ('PerformanceObserver' in window) {
            try {
                const longTaskObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        console.warn(`🐌 Long task detected: ${entry.duration}ms`);
                        
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'long_task', {
                                event_category: 'performance',
                                event_label: 'long_task_detected',
                                value: Math.round(entry.duration)
                            });
                        }
                    }
                });
                
                longTaskObserver.observe({ entryTypes: ['longtask'] });
            } catch (e) {
                console.warn('⚠️ Long task observer not supported');
            }
        }

        // Store performance data
        localStorage.setItem(PERFORMANCE_STORAGE_KEY, JSON.stringify(performanceMetrics));
        
        console.log(`⚡ Initialization completed in ${initializationTime.toFixed(2)}ms`);
        console.log('📊 Performance metrics:', performanceMetrics);
    }

    // ====================================
    // MODO DEBUG
    // ====================================
    function setupDebugMode() {
        if (debugPanel) return; // Already set up

        console.log('🐛 Setting up debug mode...');
        
        createDebugPanel();
        setupDebugControls();
        enableDebugFeatures();
        
        document.documentElement.classList.add('debug-mode');
    }

    function createDebugPanel() {
        debugPanel = document.createElement('div');
        debugPanel.id = 'copier-debug-panel';
        debugPanel.innerHTML = `
            <div class="debug-header">
                <h4>🐛 Debug Panel</h4>
                <button class="debug-close" onclick="window.copierHomepagePart10.teardownDebugMode()">×</button>
            </div>
            <div class="debug-content">
                <div class="debug-section">
                    <h5>Performance</h5>
                    <div id="debug-performance"></div>
                </div>
                <div class="debug-section">
                    <h5>Analytics</h5>
                    <div id="debug-analytics"></div>
                </div>
                <div class="debug-section">
                    <h5>Errors</h5>
                    <div id="debug-errors"></div>
                </div>
                <div class="debug-section">
                    <h5>Actions</h5>
                    <div class="debug-actions">
                        <button onclick="window.copierHomepagePart10.exportDebugData()" class="btn btn-sm btn-primary">
                            Export Data
                        </button>
                        <button onclick="window.copierHomepagePart10.clearDebugData()" class="btn btn-sm btn-warning">
                            Clear Data
                        </button>
                        <button onclick="window.copierHomepagePart10.runDiagnostics()" class="btn btn-sm btn-info">
                            Run Diagnostics
                        </button>
                    </div>
                </div>
            </div>
        `;

        debugPanel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 350px;
            background: #fff;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-family: monospace;
            font-size: 12px;
            max-height: 500px;
            overflow-y: auto;
        `;

        document.body.appendChild(debugPanel);
        updateDebugPanel();
    }

    function updateDebugPanel() {
        if (!debugPanel) return;

        // Performance data
        const perfSection = debugPanel.querySelector('#debug-performance');
        if (perfSection) {
            perfSection.innerHTML = `
                <div>Init: ${performanceMetrics.initializationTime?.toFixed(2)}ms</div>
                <div>Memory: ${formatBytes(performanceMetrics.memoryUsage?.used || 0)}</div>
                <div>Scripts: ${Object.keys(window).filter(key => key.startsWith('copierHomepage')).length}/10</div>
            `;
        }

        // Analytics data
        const analyticsSection = debugPanel.querySelector('#debug-analytics');
        if (analyticsSection && window.copierHomepagePart8) {
            const engagementData = window.copierHomepagePart8.getEngagementData();
            analyticsSection.innerHTML = `
                <div>Clicks: ${engagementData.clicks}</div>
                <div>Scroll: ${engagementData.scrollDepth}%</div>
                <div>Time: ${engagementData.timeOnPage}s</div>
                <div>Engaged: ${engagementData.isEngaged ? 'Yes' : 'No'}</div>
            `;
        }

        // Error data
        const errorsSection = debugPanel.querySelector('#debug-errors');
        if (errorsSection && window.copierHomepagePart9) {
            const errorLog = window.copierHomepagePart9.getErrorLog();
            errorsSection.innerHTML = `
                <div>Total Errors: ${errorLog.length}</div>
                ${errorLog.slice(-3).map(error => 
                    `<div class="error-item">${error.type}: ${error.message?.substring(0, 30)}...</div>`
                ).join('')}
            `;
        }
    }

    function setupDebugControls() {
        // Update debug panel every 5 seconds
        setInterval(updateDebugPanel, 5000);

        // Add debug styles
        const debugStyles = document.createElement('style');
        debugStyles.textContent = `
            .debug-mode * {
                outline: 1px dotted rgba(255, 0, 0, 0.3) !important;
            }
            .debug-mode .modal {
                outline: 2px solid red !important;
            }
            #copier-debug-panel .debug-header {
                background: #f8f9fa;
                padding: 8px 12px;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            #copier-debug-panel .debug-content {
                padding: 12px;
            }
            #copier-debug-panel .debug-section {
                margin-bottom: 16px;
            }
            #copier-debug-panel .debug-section h5 {
                margin: 0 0 8px 0;
                color: #333;
                font-size: 14px;
            }
            #copier-debug-panel .debug-actions {
                display: flex;
                gap: 4px;
                flex-wrap: wrap;
            }
            #copier-debug-panel .btn {
                padding: 2px 6px;
                font-size: 10px;
            }
            #copier-debug-panel .error-item {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 2px;
                font-size: 10px;
            }
        `;
        document.head.appendChild(debugStyles);
    }

    function enableDebugFeatures() {
        // Add data attributes for debugging
        document.querySelectorAll('.benefit-card, .brand-card, .product-card').forEach((card, index) => {
            card.dataset.debugIndex = index;
            card.title = `Debug: ${card.className} #${index}`;
        });

        // Log all analytics events to console
        const originalGtag = window.gtag;
        if (originalGtag) {
            window.gtag = function(...args) {
                console.log('📊 Debug Analytics:', args);
                return originalGtag.apply(this, args);
            };
        }

        // Add performance marks
        performance.mark('debug-mode-enabled');
    }

    function teardownDebugMode() {
        isDebugMode = false;
        localStorage.setItem(DEBUG_STORAGE_KEY, 'false');
        document.documentElement.classList.remove('debug-mode');
        
        if (debugPanel) {
            debugPanel.remove();
            debugPanel = null;
        }
        
        console.log('🐛 Debug mode disabled');
    }

    // ====================================
    // FUNCIONES DE DEBUG PÚBLICAS
    // ====================================
    function exportDebugData() {
        console.log('📁 Preparing debug data export...');

        const debugData = {
            // Información básica
            version: window.copierHomepagePart10?.version || '1.0.0',
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            
            // Información de la página
            pageInfo: {
                title: document.title,
                lang: document.documentElement.lang,
                charset: document.characterSet,
                referrer: document.referrer,
                readyState: document.readyState,
                visibilityState: document.visibilityState
            },

            // Datos de rendimiento
            performance: {
                ...window.copierHomepagePart10?.getPerformanceMetrics?.() || {},
                navigationTiming: getNavigationTiming(),
                resourceTiming: getResourceTiming(),
                memoryInfo: getMemoryInfo(),
                connectionInfo: getConnectionInfo()
            },

            // Datos de analytics y engagement
            analytics: {
                ...window.copierHomepagePart8?.getEngagementData?.() || {},
                gtagAvailable: typeof gtag !== 'undefined',
                analyticsInitialized: window.copierHomepagePart8 ? true : false
            },

            // Log de errores
            errors: {
                errorLog: window.copierHomepagePart9?.getErrorLog?.() || [],
                consoleErrors: getConsoleErrors(),
                resourceErrors: getResourceErrors()
            },

            // Capacidades del dispositivo
            device: {
                ...window.copierHomepagePart9?.getDeviceCapabilities?.() || {},
                screen: {
                    width: screen.width,
                    height: screen.height,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight,
                    pixelDepth: screen.pixelDepth,
                    colorDepth: screen.colorDepth,
                    orientation: screen.orientation?.type || 'unknown'
                },
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    devicePixelRatio: window.devicePixelRatio
                },
                features: getDeviceFeatures()
            },

            // Estado de los scripts
            scripts: {
                loadedParts: Object.keys(window).filter(key => key.startsWith('copierHomepage')),
                totalParts: 10,
                missingParts: getMissingParts(),
                bootstrapAvailable: typeof bootstrap !== 'undefined',
                jqueryAvailable: typeof jQuery !== 'undefined',
                gtagAvailable: typeof gtag !== 'undefined'
            },

            // Estado del DOM
            domState: {
                hasHomepageClass: document.querySelector('.copier-modern-homepage') !== null,
                totalElements: document.querySelectorAll('*').length,
                modals: getModalInfo(),
                forms: getFormInfo(),
                images: getImageInfo(),
                links: getLinkInfo()
            },

            // Datos de localStorage
            localStorage: {
                debugMode: localStorage.getItem('copier_debug_mode'),
                performanceData: localStorage.getItem('copier_performance_data'),
                formData: getStoredFormData(),
                totalItems: localStorage.length,
                storageQuota: getStorageQuota()
            },

            // Configuración y preferencias
            preferences: {
                language: navigator.language,
                languages: navigator.languages,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine,
                platform: navigator.platform,
                vendor: navigator.vendor
            },

            // Información de red
            network: {
                onlineStatus: navigator.onLine,
                connection: getDetailedConnectionInfo(),
                serviceWorker: getServiceWorkerInfo()
            },

            // Métricas adicionales
            metrics: {
                initializationSteps: getInitializationSteps(),
                loadingMetrics: getLoadingMetrics(),
                interactionMetrics: getInteractionMetrics(),
                accessibilityMetrics: getAccessibilityMetrics()
            }
        };

        // Crear y descargar el archivo
        const dataStr = JSON.stringify(debugData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `copier-debug-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
        
        console.log('📁 Debug data exported successfully');
        console.log('📊 Export summary:', {
            totalSize: formatBytes(dataBlob.size),
            sections: Object.keys(debugData).length,
            timestamp: debugData.timestamp
        });

        // También mostrar un resumen en la consola
        console.table({
            'Scripts Loaded': `${debugData.scripts.loadedParts.length}/${debugData.scripts.totalParts}`,
            'Total Errors': debugData.errors.errorLog.length,
            'Page Load Time': `${debugData.performance.navigationTiming?.loadTime || 'N/A'}ms`,
            'Memory Usage': formatBytes(debugData.performance.memoryInfo?.used || 0),
            'User Engaged': debugData.analytics.isEngaged ? 'Yes' : 'No',
            'Debug Mode': debugData.localStorage.debugMode === 'true' ? 'On' : 'Off'
        });

        return debugData;
    }

    // ====================================
    // FUNCIONES AUXILIARES PARA DEBUG
    // ====================================

    function getNavigationTiming() {
        if (!('performance' in window) || !performance.timing) return null;
        
        const timing = performance.timing;
        return {
            navigationStart: timing.navigationStart,
            loadTime: timing.loadEventEnd - timing.navigationStart,
            domReadyTime: timing.domContentLoadedEventEnd - timing.navigationStart,
            firstByteTime: timing.responseStart - timing.requestStart,
            domParsingTime: timing.domComplete - timing.domLoading,
            resourceLoadTime: timing.loadEventEnd - timing.domContentLoadedEventEnd
        };
    }

    function getResourceTiming() {
        if (!('performance' in window)) return null;
        
        const resources = performance.getEntriesByType('resource');
        return {
            totalResources: resources.length,
            slowResources: resources.filter(r => r.duration > 1000).map(r => ({
                name: r.name,
                duration: Math.round(r.duration),
                size: r.transferSize || 0
            })),
            resourceTypes: resources.reduce((acc, r) => {
                const type = r.initiatorType || 'other';
                acc[type] = (acc[type] || 0) + 1;
                return acc;
            }, {}),
            totalTransferSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0)
        };
    }

    function getMemoryInfo() {
        if (!('performance' in window) || !performance.memory) return null;
        
        return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit,
            usagePercentage: Math.round((performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100)
        };
    }

    function getConnectionInfo() {
        if (!navigator.connection) return null;
        
        return {
            effectiveType: navigator.connection.effectiveType,
            downlink: navigator.connection.downlink,
            rtt: navigator.connection.rtt,
            saveData: navigator.connection.saveData,
            type: navigator.connection.type || 'unknown'
        };
    }

    function getDetailedConnectionInfo() {
        const connection = navigator.connection;
        if (!connection) return { available: false };

        return {
            available: true,
            effectiveType: connection.effectiveType,
            downlink: connection.downlink,
            downlinkMax: connection.downlinkMax,
            rtt: connection.rtt,
            saveData: connection.saveData,
            type: connection.type,
            quality: getConnectionQuality(connection)
        };
    }

    function getConnectionQuality(connection) {
        if (!connection) return 'unknown';
        
        const effectiveType = connection.effectiveType;
        if (effectiveType === '4g' && connection.downlink > 10) return 'excellent';
        if (effectiveType === '4g') return 'good';
        if (effectiveType === '3g') return 'fair';
        return 'poor';
    }

    function getServiceWorkerInfo() {
        if (!('serviceWorker' in navigator)) {
            return { available: false };
        }

        return {
            available: true,
            controller: navigator.serviceWorker.controller ? true : false,
            ready: navigator.serviceWorker.ready ? true : false,
            registrations: navigator.serviceWorker.getRegistrations ? 'supported' : 'not_supported'
        };
    }

    function getDeviceFeatures() {
        return {
            touchSupport: 'ontouchstart' in window,
            orientationSupport: 'orientation' in window,
            geolocationSupport: 'geolocation' in navigator,
            notificationSupport: 'Notification' in window,
            serviceWorkerSupport: 'serviceWorker' in navigator,
            intersectionObserverSupport: 'IntersectionObserver' in window,
            resizeObserverSupport: 'ResizeObserver' in window,
            mutationObserverSupport: 'MutationObserver' in window,
            webglSupport: getWebGLSupport(),
            localStorageSupport: testLocalStorage(),
            sessionStorageSupport: testSessionStorage(),
            indexedDBSupport: 'indexedDB' in window,
            webWorkerSupport: 'Worker' in window,
            offlineSupport: 'applicationCache' in window,
            fullscreenSupport: document.fullscreenEnabled || false
        };
    }

    function getWebGLSupport() {
        try {
            const canvas = document.createElement('canvas');
            return !!(window.WebGLRenderingContext && canvas.getContext('webgl'));
        } catch (e) {
            return false;
        }
    }

    function testLocalStorage() {
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            return true;
        } catch (e) {
            return false;
        }
    }

    function testSessionStorage() {
        try {
            sessionStorage.setItem('test', 'test');
            sessionStorage.removeItem('test');
            return true;
        } catch (e) {
            return false;
        }
    }

    function getMissingParts() {
        const expectedParts = [];
        for (let i = 1; i <= 10; i++) {
            expectedParts.push(`copierHomepagePart${i}`);
        }
        
        return expectedParts.filter(part => !window[part]);
    }

    function getModalInfo() {
        const modals = document.querySelectorAll('.modal');
        return {
            total: modals.length,
            visible: document.querySelectorAll('.modal.show').length,
            ids: Array.from(modals).map(modal => modal.id).filter(Boolean)
        };
    }

    function getFormInfo() {
        const forms = document.querySelectorAll('form');
        return {
            total: forms.length,
            withValidation: document.querySelectorAll('form[novalidate]').length,
            withAutoSave: document.querySelectorAll('form[data-auto-save]').length,
            inputs: {
                total: document.querySelectorAll('input').length,
                required: document.querySelectorAll('input[required]').length,
                email: document.querySelectorAll('input[type="email"]').length,
                tel: document.querySelectorAll('input[type="tel"]').length
            }
        };
    }

    function getImageInfo() {
        const images = document.querySelectorAll('img');
        return {
            total: images.length,
            withAlt: document.querySelectorAll('img[alt]').length,
            withoutAlt: document.querySelectorAll('img:not([alt])').length,
            lazyLoaded: document.querySelectorAll('img[data-src]').length,
            loaded: document.querySelectorAll('img.loaded').length
        };
    }

    function getLinkInfo() {
        const links = document.querySelectorAll('a');
        return {
            total: links.length,
            external: document.querySelectorAll('a[href^="http"]:not([href*="' + window.location.hostname + '"])').length,
            internal: document.querySelectorAll('a[href^="/"], a[href^="#"]').length,
            withTarget: document.querySelectorAll('a[target]').length
        };
    }

    function getStoredFormData() {
        const formData = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('copier_form_')) {
                try {
                    formData[key] = JSON.parse(localStorage.getItem(key));
                } catch (e) {
                    formData[key] = localStorage.getItem(key);
                }
            }
        }
        return formData;
    }

    function getStorageQuota() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            navigator.storage.estimate().then(estimate => {
                return {
                    quota: estimate.quota,
                    usage: estimate.usage,
                    available: estimate.quota - estimate.usage,
                    usagePercentage: Math.round((estimate.usage / estimate.quota) * 100)
                };
            });
        }
        return { available: false };
    }

    function getConsoleErrors() {
        // Esta función requeriría override del console.error para capturar errores
        // Por ahora retornamos un placeholder
        return {
            captured: false,
            note: 'Console error capture requires setup in Part 9'
        };
    }

    function getResourceErrors() {
        const resourceErrors = [];
        
        // Buscar imágenes con error
        document.querySelectorAll('img[data-error-handled]').forEach(img => {
            resourceErrors.push({
                type: 'image',
                src: img.src,
                error: 'Failed to load'
            });
        });

        return resourceErrors;
    }

    function getInitializationSteps() {
        return window.copierHomepagePart10?.initializationSteps || [];
    }

    function getLoadingMetrics() {
        return {
            domContentLoaded: performance.getEntriesByName('domContentLoaded')[0]?.startTime || null,
            loadComplete: performance.getEntriesByName('load')[0]?.startTime || null,
            firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || null,
            firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null
        };
    }

    function getInteractionMetrics() {
        const engagementData = window.copierHomepagePart8?.getEngagementData?.() || {};
        return {
            ...engagementData,
            clickableElements: document.querySelectorAll('button, a, [role="button"]').length,
            interactiveElements: document.querySelectorAll('input, select, textarea, button, a').length
        };
    }

    function getAccessibilityMetrics() {
        return {
            imagesWithoutAlt: document.querySelectorAll('img:not([alt])').length,
            buttonsWithoutLabel: document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').length,
            linksWithoutText: document.querySelectorAll('a:empty').length,
            focusableElements: document.querySelectorAll('[tabindex], button, a, input, select, textarea').length,
            skipLinks: document.querySelectorAll('.skip-link, [href^="#main"]').length,
            landmarks: document.querySelectorAll('main, nav, aside, footer, header, [role="main"], [role="navigation"]').length
        };
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // ====================================
    // FUNCIONES ADICIONALES DE DEBUG
    // ====================================

    function generateDebugReport() {
        const debugData = exportDebugData();
        
        const report = `
# Copier Homepage Debug Report
Generated: ${new Date().toLocaleString()}

## System Status
- Scripts Loaded: ${debugData.scripts.loadedParts.length}/${debugData.scripts.totalParts}
- Page Load Time: ${debugData.performance.navigationTiming?.loadTime || 'N/A'}ms
- Memory Usage: ${formatBytes(debugData.performance.memoryInfo?.used || 0)}
- Total Errors: ${debugData.errors.errorLog.length}

## Performance Metrics
- DOM Ready: ${debugData.performance.navigationTiming?.domReadyTime || 'N/A'}ms
- First Byte: ${debugData.performance.navigationTiming?.firstByteTime || 'N/A'}ms
- Total Resources: ${debugData.performance.resourceTiming?.totalResources || 'N/A'}
- Transfer Size: ${formatBytes(debugData.performance.resourceTiming?.totalTransferSize || 0)}

## User Engagement
- Mouse Movements: ${debugData.analytics.mouseMovements || 0}
- Clicks: ${debugData.analytics.clicks || 0}
- Scroll Depth: ${debugData.analytics.scrollDepth || 0}%
- Time on Page: ${debugData.analytics.timeOnPage || 0}s
- User Engaged: ${debugData.analytics.isEngaged ? 'Yes' : 'No'}

## Device Information
- User Agent: ${debugData.userAgent}
- Screen: ${debugData.device.screen.width}x${debugData.device.screen.height}
- Viewport: ${debugData.device.viewport.width}x${debugData.device.viewport.height}
- Connection: ${debugData.network.connection.effectiveType || 'Unknown'}
- Online: ${debugData.network.onlineStatus ? 'Yes' : 'No'}

## Accessibility
- Images without Alt: ${debugData.metrics.accessibilityMetrics.imagesWithoutAlt}
- Buttons without Label: ${debugData.metrics.accessibilityMetrics.buttonsWithoutLabel}
- Focusable Elements: ${debugData.metrics.accessibilityMetrics.focusableElements}

---
Report generated by Copier Homepage Debug System v${debugData.version}
        `;

        // Copiar al clipboard si está disponible
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(report).then(() => {
                console.log('📋 Debug report copied to clipboard');
            });
        }

        return report;
    }

    function runPerformanceAudit() {
        console.log('🔍 Running performance audit...');
        
        const audit = {
            score: 0,
            issues: [],
            recommendations: [],
            passed: []
        };

        // Check initialization time
        const initTime = window.copierHomepagePart10?.getInitializationTime?.() || 0;
        if (initTime > 3000) {
            audit.issues.push(`Slow initialization: ${initTime.toFixed(2)}ms`);
            audit.recommendations.push('Consider lazy loading non-critical components');
        } else {
            audit.passed.push(`Fast initialization: ${initTime.toFixed(2)}ms`);
        }

        // Check memory usage
        const memoryInfo = getMemoryInfo();
        if (memoryInfo && memoryInfo.usagePercentage > 70) {
            audit.issues.push(`High memory usage: ${memoryInfo.usagePercentage}%`);
            audit.recommendations.push('Review memory-intensive operations');
        } else if (memoryInfo) {
            audit.passed.push(`Good memory usage: ${memoryInfo.usagePercentage}%`);
        }

        // Check for missing scripts
        const missingParts = getMissingParts();
        if (missingParts.length > 0) {
            audit.issues.push(`Missing script parts: ${missingParts.join(', ')}`);
            audit.recommendations.push('Ensure all script parts are loaded');
        } else {
            audit.passed.push('All script parts loaded successfully');
        }

        // Check accessibility
        const a11yMetrics = getAccessibilityMetrics();
        if (a11yMetrics.imagesWithoutAlt > 0) {
            audit.issues.push(`${a11yMetrics.imagesWithoutAlt} images without alt text`);
            audit.recommendations.push('Add alt attributes to all images');
        }

        if (a11yMetrics.buttonsWithoutLabel > 0) {
            audit.issues.push(`${a11yMetrics.buttonsWithoutLabel} buttons without labels`);
            audit.recommendations.push('Add aria-label or aria-labelledby to all buttons');
        }

        // Calculate score
        const totalChecks = audit.issues.length + audit.passed.length;
        audit.score = totalChecks > 0 ? Math.round((audit.passed.length / totalChecks) * 100) : 0;

        console.log('🎯 Performance Audit Results:', audit);
        return audit;
    }

    // ====================================
    // EXPORTAR FUNCIONES PÚBLICAS
    // ====================================
    
    // Agregar a la API existente de Part 10
    if (window.copierHomepagePart10) {
        window.copierHomepagePart10.exportDebugData = exportDebugData;
        window.copierHomepagePart10.generateDebugReport = generateDebugReport;
        window.copierHomepagePart10.runPerformanceAudit = runPerformanceAudit;
        window.copierHomepagePart10.formatBytes = formatBytes;
    } else {
        // Crear objeto si no existe
        window.copierHomepagePart10 = {
            exportDebugData,
            generateDebugReport,
            runPerformanceAudit,
            formatBytes,
            version: '1.0.0'
        };
    }

    // ====================================
    // COMANDOS DE CONSOLA PARA DEBUG
    // ====================================
    
    // Hacer funciones disponibles globalmente para debug fácil
    window.copierDebug = {
        export: exportDebugData,
        report: generateDebugReport,
        audit: runPerformanceAudit,
        clear: () => window.copierHomepagePart10?.clearDebugData?.(),
        diagnostics: () => window.copierHomepagePart10?.runDiagnostics?.(),
        toggle: () => {
            const isDebug = window.copierHomepagePart10?.isDebugMode?.() || false;
            if (isDebug) {
                window.copierHomepagePart10?.teardownDebugMode?.();
            } else {
                window.copierHomepagePart10?.setupDebugMode?.();
            }
        }
    };

    console.log('📦 Copier Homepage - Part 10 COMPLETE loaded');
    console.log('🛠️ Debug commands available: copierDebug.export(), copierDebug.report(), copierDebug.audit()');

})();