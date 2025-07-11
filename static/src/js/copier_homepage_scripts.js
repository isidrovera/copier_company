/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 1/3: Inicialización y Animaciones
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // VARIABLES GLOBALES
    // ====================================
    let isScrolling = false;
    let scrollTimeout;
    
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
            if (isScrolling) return;
            
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.05;
            
            floatingCards.forEach((card, index) => {
                const speed = (index + 1) * 0.02;
                const yPos = parallax * speed;
                card.style.transform = `translateY(${yPos}px)`;
            });
        }

        // Throttle scroll events
        window.addEventListener('scroll', function() {
            if (!isScrolling) {
                window.requestAnimationFrame(updateParallax);
                isScrolling = true;
                
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    isScrolling = false;
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
        let scrollTimer;
        window.addEventListener('scroll', function() {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => {
                if (window.pageYOffset > 100) {
                    scrollIndicator.style.opacity = '0';
                } else {
                    scrollIndicator.style.opacity = '1';
                }
            }, 100);
        }, { passive: true });
    }

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

        // Mostrar/ocultar según scroll
        let lastScrollY = window.pageYOffset;
        window.addEventListener('scroll', function() {
            const currentScrollY = window.pageYOffset;
            
            if (currentScrollY > 300) {
                if (currentScrollY < lastScrollY) {
                    // Scrolling up
                    whatsappBtn.parentElement.style.transform = 'translateY(0)';
                } else {
                    // Scrolling down
                    whatsappBtn.parentElement.style.transform = 'translateY(100px)';
                }
            } else {
                whatsappBtn.parentElement.style.transform = 'translateY(0)';
            }
            
            lastScrollY = currentScrollY;
        }, { passive: true });
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

        // Efecto de pulsación periódica
        setInterval(() => {
            quoteBtn.style.animation = 'none';
            setTimeout(() => {
                quoteBtn.style.animation = 'pulse 0.5s ease-in-out';
            }, 10);
        }, 10000); // Cada 10 segundos
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
    // OPTIMIZACIONES DE PERFORMANCE
    // ====================================
    function initPerformanceOptimizations() {
        // Lazy loading para imágenes
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            img.classList.add('loaded');
                            observer.unobserve(img);
                        }
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }

        // Preload de recursos críticos
        const criticalResources = [
            '/cotizacion/form',
            '/contactus',
            '/our-services'
        ];

        criticalResources.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });

        // Optimización de eventos scroll
        let ticking = false;
        function updateScrollEffects() {
            // Aquí se pueden agregar más efectos de scroll
            ticking = false;
        }

        window.addEventListener('scroll', function() {
            if (!ticking) {
                requestAnimationFrame(updateScrollEffects);
                ticking = true;
            }
        }, { passive: true });
    }

    // ====================================
    // ACCESIBILIDAD
    // ====================================
    function initAccessibility() {
        // Navegación por teclado para cards
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
                this.style.outline = '3px solid #667eea';
                this.style.outlineOffset = '2px';
            });

            card.addEventListener('blur', function() {
                this.style.outline = 'none';
            });
        });

        // Skip links para navegación rápida
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
            padding: 8px;
            text-decoration: none;
            z-index: 1000;
            transition: top 0.3s;
            border-radius: 4px;
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

        // Anuncios para lectores de pantalla
        const announcements = document.createElement('div');
        announcements.setAttribute('aria-live', 'polite');
        announcements.setAttribute('aria-atomic', 'true');
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

    // Hacer funciones disponibles globalmente para las otras partes
    window.copierHomepagePart1 = {
        isMobileDevice,
        isTouchDevice,
        throttle,
        initializeHomepage
    };

    // Debug info
    console.log('📦 Copier Homepage - Parte 1 cargada (Animaciones e Inicialización)');

})();
/**
 * ====================================
 * COPIER COMPANY - HOMEPAGE SCRIPTS
 * Archivo: copier_homepage_scripts.js
 * Parte 2/3: Modales Interactivos
 * ====================================
 */

(function() {
    'use strict';

    // ====================================
    // INICIALIZACIÓN DE MODALES
    // ====================================
    document.addEventListener('DOMContentLoaded', function() {
        // Solo ejecutar si estamos en la página correcta
        if (!document.querySelector('.copier-modern-homepage')) {
            return;
        }

        initModals();
        console.log('📦 Copier Homepage - Parte 2 cargada (Modales Interactivos)');
    });

    function initModals() {
        initBenefitModal();
        initBrandModal();
        initProductModal();
    }

    // ====================================
    // MODAL DE BENEFICIOS
    // ====================================
    function initBenefitModal() {
        const benefitCards = document.querySelectorAll('.copier-modern-homepage .benefit-card[data-benefit]');
        const modal = document.getElementById('benefitModal');
        const modalBody = document.getElementById('benefitModalBody');
        const modalTitle = document.querySelector('#benefitModal .modal-title');

        if (!modal || !modalBody || !modalTitle) return;

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
                        </div>
                        <div class="col-md-6">
                            <h4><i class="fas fa-business-time text-primary me-2"></i>Beneficios Operativos</h4>
                            <ul class="list-unstyled">
                                <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Equipos disponibles inmediatamente</li>
                                <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Actualización tecnológica constante</li>
                                <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Mantenimiento incluido</li>
                                <li class="mb-2"><i class="fas fa-check text-success me-2"></i>Soporte técnico especializado</li>
                            </ul>
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
                    <h4><i class="fas fa-tools text-primary me-2"></i>Servicios Incluidos</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Diagnóstico remoto</li>
                                <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Resolución de problemas</li>
                                <li class="mb-2"><i class="fas fa-cog text-success me-2"></i>Configuración de funciones</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Capacitación de usuarios</li>
                                <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Optimización de workflows</li>
                                <li class="mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Consultoría especializada</li>
                            </ul>
                        </div>
                    </div>
                `
            },
            'instalacion-rapida': {
                title: 'Instalación en 24 Horas',
                icon: 'fas fa-rocket',
                content: `
                    <div class="timeline">
                        <div class="timeline-item">
                            <div class="timeline-icon bg-primary">
                                <i class="fas fa-calendar-check"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Día 0 - Programación</h5>
                                <p>Coordinamos la fecha y hora más conveniente para tu empresa</p>
                                <small class="text-muted">Misma semana de confirmación</small>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-icon bg-info">
                                <i class="fas fa-truck"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Entrega e Instalación</h5>
                                <p>Nuestro equipo técnico lleva e instala el equipo en tu oficina</p>
                                <small class="text-muted">2-4 horas promedio</small>
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
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-icon bg-warning">
                                <i class="fas fa-graduation-cap"></i>
                            </div>
                            <div class="timeline-content">
                                <h5>Capacitación del Personal</h5>
                                <p>Entrenamos a tu equipo en todas las funciones del equipo</p>
                                <small class="text-muted">Manual de usuario incluido</small>
                            </div>
                        </div>
                    </div>
                    <div class="alert alert-success mt-4">
                        <i class="fas fa-thumbs-up me-2"></i>
                        <strong>Garantía de funcionamiento:</strong> Tu equipo estará 100% operativo desde el primer día
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
                                    <span class="frequency">Mensual</span>
                                    <span class="task">Limpieza profunda y calibración</span>
                                </div>
                                <div class="schedule-item">
                                    <span class="frequency">Trimestral</span>
                                    <span class="task">Revisión completa de componentes</span>
                                </div>
                                <div class="schedule-item">
                                    <span class="frequency">Semestral</span>
                                    <span class="task">Actualización de firmware</span>
                                </div>
                                <div class="schedule-item">
                                    <span class="frequency">Anual</span>
                                    <span class="task">Overhaul completo del sistema</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h4><i class="fas fa-tools text-primary me-2"></i>Mantenimiento Correctivo</h4>
                            <ul class="list-unstyled">
                                <li class="mb-3">
                                    <i class="fas fa-wrench text-success me-2"></i>
                                    <strong>Reparaciones</strong><br>
                                    <small class="text-muted">Sin costo adicional, repuestos incluidos</small>
                                </li>
                                <li class="mb-3">
                                    <i class="fas fa-exchange-alt text-success me-2"></i>
                                    <strong>Reemplazo Temporal</strong><br>
                                    <small class="text-muted">Equipo de respaldo mientras reparamos</small>
                                </li>
                                <li class="mb-3">
                                    <i class="fas fa-tint text-success me-2"></i>
                                    <strong>Consumibles</strong><br>
                                    <small class="text-muted">Toners y repuestos originales</small>
                                </li>
                            </ul>
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
                `
            },
            'garantia-total': {
                title: 'Garantía Total',
                icon: 'fas fa-shield-alt',
                content: `
                    <div class="guarantee-grid">
                        <div class="guarantee-card">
                            <div class="guarantee-icon">
                                <i class="fas fa-shield-check"></i>
                            </div>
                            <h5>Cobertura Completa</h5>
                            <p>Todos los componentes del equipo están cubiertos por nuestra garantía total</p>
                            <ul class="coverage-list">
                                <li>Motor y mecanismos internos</li>
                                <li>Componentes electrónicos</li>
                                <li>Pantalla y controles</li>
                                <li>Sistema de alimentación de papel</li>
                            </ul>
                        </div>
                        <div class="guarantee-card">
                            <div class="guarantee-icon">
                                <i class="fas fa-clock"></i>
                            </div>
                            <h5>Respuesta Inmediata</h5>
                            <p>Garantizamos tiempos de respuesta específicos según el tipo de problema</p>
                            <div class="response-times">
                                <div class="time-badge critical">Crítico: 2 horas</div>
                                <div class="time-badge high">Alto: 4 horas</div>
                                <div class="time-badge medium">Medio: 8 horas</div>
                                <div class="time-badge low">Bajo: 24 horas</div>
                            </div>
                        </div>
                        <div class="guarantee-card">
                            <div class="guarantee-icon">
                                <i class="fas fa-exchange-alt"></i>
                            </div>
                            <h5>Reemplazo Garantizado</h5>
                            <p>Si no podemos reparar tu equipo en 48 horas, lo reemplazamos</p>
                            <div class="replacement-process">
                                <span class="process-step">Diagnóstico</span>
                                <span class="process-arrow">→</span>
                                <span class="process-step">Reparación</span>
                                <span class="process-arrow">→</span>
                                <span class="process-step">Reemplazo</span>
                            </div>
                        </div>
                    </div>
                    <div class="guarantee-footer">
                        <div class="alert alert-primary">
                            <i class="fas fa-handshake me-2"></i>
                            <strong>Compromiso total:</strong> Tu satisfacción es nuestra prioridad. Si no estás conforme, trabajamos hasta que lo estés.
                        </div>
                    </div>
                `
            },
            'escalabilidad': {
                title: 'Escalabilidad Total',
                icon: 'fas fa-chart-line',
                content: `
                    <div class="scalability-scenarios">
                        <h4><i class="fas fa-chart-trend-up text-primary me-2"></i>Crece Con Tu Negocio</h4>
                        <div class="scenario-cards">
                            <div class="scenario-card">
                                <div class="scenario-icon green">
                                    <i class="fas fa-arrow-up"></i>
                                </div>
                                <h5>Expansión</h5>
                                <p>¿Tu empresa está creciendo? Agregamos más equipos o upgradeamos a modelos más potentes</p>
                                <ul class="scenario-features">
                                    <li>Equipos adicionales en nuevas oficinas</li>
                                    <li>Upgrade a equipos de mayor capacidad</li>
                                    <li>Funciones especializadas según necesidades</li>
                                </ul>
                            </div>
                            <div class="scenario-card">
                                <div class="scenario-icon blue">
                                    <i class="fas fa-sync-alt"></i>
                                </div>
                                <h5>Adaptación</h5>
                                <p>¿Cambió tu modelo de negocio? Ajustamos el tipo de equipo a tus nuevas necesidades</p>
                                <ul class="scenario-features">
                                    <li>Cambio de multifuncional a impresora</li>
                                    <li>Migración de B/N a color</li>
                                    <li>Equipos especializados por industria</li>
                                </ul>
                            </div>
                            <div class="scenario-card">
                                <div class="scenario-icon orange">
                                    <i class="fas fa-arrow-down"></i>
                                </div>
                                <h5>Optimización</h5>
                                <p>¿Necesitas reducir costos? Ajustamos a equipos más eficientes o menor capacidad</p>
                                <ul class="scenario-features">
                                    <li>Equipos más eficientes en consumo</li>
                                    <li>Modelos compactos para espacios reducidos</li>
                                    <li>Optimización de contratos existentes</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="scalability-benefits">
                        <h4><i class="fas fa-star text-warning me-2"></i>Beneficios de la Escalabilidad</h4>
                        <div class="row">
                            <div class="col-md-6">
                                <ul class="benefits-list">
                                    <li><i class="fas fa-check text-success me-2"></i>Sin penalizaciones por cambios</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Evaluación periódica de necesidades</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Asesoría para optimización</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <ul class="benefits-list">
                                    <li><i class="fas fa-check text-success me-2"></i>Flexibilidad contractual</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Migración de datos incluida</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Capacitación en nuevos equipos</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                `
            }
        };

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
                }
            });
        });

        // Limpiar animaciones al cerrar modal
        modal.addEventListener('hidden.bs.modal', function() {
            modalBody.classList.remove('animate-fade-in', 'visible');
        });
    }

    // ====================================
    // MODAL DE MARCAS
    // ====================================
    function initBrandModal() {
        const brandCards = document.querySelectorAll('.copier-modern-homepage .brand-card[data-brand]');
        const modal = document.getElementById('brandModal');
        const modalBody = document.getElementById('brandModalBody');
        const modalTitle = document.querySelector('#brandModal .modal-title');

        if (!modal || !modalBody || !modalTitle) return;

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
                                            <p>Impresión a color con calidad fotográfica</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-shield-alt text-primary"></i>
                                        <div>
                                            <h6>Seguridad Avanzada</h6>
                                            <p>Encriptación y autenticación biométrica</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-leaf text-primary"></i>
                                        <div>
                                            <h6>Eco-Friendly</h6>
                                            <p>Bajo consumo energético y materiales reciclables</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="models-section mt-4">
                            <h4>Modelos Disponibles</h4>
                            <div class="models-grid">
                                <div class="model-card">
                                    <h6>bizhub C458</h6>
                                    <div class="model-specs">
                                        <span>45 ppm</span>
                                        <span>A3 Color</span>
                                        <span>Scanner</span>
                                    </div>
                                    <p>Ideal para oficinas medianas que requieren impresión a color de alta calidad</p>
                                </div>
                                <div class="model-card">
                                    <h6>bizhub 754e</h6>
                                    <div class="model-specs">
                                        <span>75 ppm</span>
                                        <span>A3 B/N</span>
                                        <span>Finisher</span>
                                    </div>
                                    <p>Perfecto para empresas con alto volumen de impresión en blanco y negro</p>
                                </div>
                                <div class="model-card">
                                    <h6>bizhub C287</h6>
                                    <div class="model-specs">
                                        <span>28 ppm</span>
                                        <span>A3 Color</span>
                                        <span>WiFi</span>
                                    </div>
                                    <p>Compacto y versátil, ideal para pequeñas oficinas y grupos de trabajo</p>
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
                                        <span class="stat-number">80+</span>
                                        <span class="stat-label">Años innovando</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-number">#1</span>
                                        <span class="stat-label">En calidad de imagen</span>
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
                                            <p>Impresión con calidad de laboratorio fotográfico</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-compress-alt text-primary"></i>
                                        <div>
                                            <h6>Diseño Compacto</h6>
                                            <p>Máximo rendimiento en espacios reducidos</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-mobile-alt text-primary"></i>
                                        <div>
                                            <h6>Conectividad Avanzada</h6>
                                            <p>Impresión móvil y conectividad cloud</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-dollar-sign text-primary"></i>
                                        <div>
                                            <h6>Eficiencia de Costos</h6>
                                            <p>Menor costo por página y alta durabilidad</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="models-section mt-4">
                            <h4>Modelos Destacados</h4>
                            <div class="models-grid">
                                <div class="model-card">
                                    <h6>imageRUNNER C3226</h6>
                                    <div class="model-specs">
                                        <span>26 ppm</span>
                                        <span>A3 Color</span>
                                        <span>Touch Screen</span>
                                    </div>
                                    <p>Multifuncional compacto con pantalla táctil intuitiva para oficinas dinámicas</p>
                                </div>
                                <div class="model-card">
                                    <h6>imageRUNNER 2630</h6>
                                    <div class="model-specs">
                                        <span>30 ppm</span>
                                        <span>A3 B/N</span>
                                        <span>Duplex</span>
                                    </div>
                                    <p>Ideal para oficinas que requieren impresión rápida y económica</p>
                                </div>
                                <div class="model-card">
                                    <h6>imageRUNNER C5560i</h6>
                                    <div class="model-specs">
                                        <span>60 ppm</span>
                                        <span>A3 Color</span>
                                        <span>Finisher</span>
                                    </div>
                                    <p>Potencia y versatilidad para entornos de alta producción</p>
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
                                            <p>Diseñados para resistir uso intensivo diario</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-user-friends text-primary"></i>
                                        <div>
                                            <h6>Facilidad de Uso</h6>
                                            <p>Interfaz intuitiva que cualquiera puede manejar</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-cloud text-primary"></i>
                                        <div>
                                            <h6>Conectividad Cloud</h6>
                                            <p>Integración perfecta con servicios en la nube</p>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <i class="fas fa-chart-line text-primary"></i>
                                        <div>
                                            <h6>Productividad Máxima</h6>
                                            <p>Workflows optimizados para eficiencia total</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="models-section mt-4">
                            <h4>Serie Destacada</h4>
                            <div class="models-grid">
                                <div class="model-card">
                                    <h6>IM C3000</h6>
                                    <div class="model-specs">
                                        <span>30 ppm</span>
                                        <span>A3 Color</span>
                                        <span>Smart Panel</span>
                                    </div>
                                    <p>Multifuncional inteligente con panel personalizable y workflows automáticos</p>
                                </div>
                                <div class="model-card">
                                    <h6>IM 6000</h6>
                                    <div class="model-specs">
                                        <span>60 ppm</span>
                                        <span>A3 B/N</span>
                                        <span>Security</span>
                                    </div>
                                    <p>Alto volumen con características de seguridad empresarial avanzadas</p>
                                </div>
                                <div class="model-card">
                                    <h6>IM C2500</h6>
                                    <div class="model-specs">
                                        <span>25 ppm</span>
                                        <span>A3 Color</span>
                                        <span>Eco Mode</span>
                                    </div>
                                    <p>Perfecto balance entre funcionalidad y eficiencia energética</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            }
        };

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
                    
                    // Agregar animación de entrada
                    setTimeout(() => {
                        modalBody.classList.add('animate-fade-in', 'visible');
                    }, 100);
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

        if (!modal || !modalBody || !modalTitle) return;

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
                                            <span>Formato A3/A4</span>
                                        </div>
                                        <div class="highlight-item">
                                            <i class="fas fa-palette"></i>
                                            <span>Color/B&N</span>
                                        </div>
                                        <div class="highlight-item">
                                            <i class="fas fa-copy"></i>
                                            <span>Copia/Impresión</span>
                                        </div>
                                        <div class="highlight-item">
                                            <i class="fas fa-scan"></i>
                                            <span>Escaneo</span>
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
                                        <span class="spec-value">Ethernet, WiFi, USB</span>
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
                                </div>
                                <div class="app-card">
                                    <i class="fas fa-graduation-cap"></i>
                                    <h6>Centros Educativos</h6>
                                    <p>Material didáctico, exámenes y documentación académica en volumen</p>
                                </div>
                                <div class="app-card">
                                    <i class="fas fa-hospital"></i>
                                    <h6>Centros Médicos</h6>
                                    <p>Historias clínicas, imágenes médicas y documentación regulatoria</p>
                                </div>
                                <div class="app-card">
                                    <i class="fas fa-balance-scale"></i>
                                    <h6>Estudios Legales</h6>
                                    <p>Contratos, demandas y documentación legal de gran volumen</p>
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
                                            <span>Formato A4</span>
                                        </div>
                                        <div class="highlight-item">
                                            <i class="fas fa-wifi"></i>
                                            <span>WiFi Integrado</span>
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
                                        <span class="spec-value">WiFi, Ethernet, USB, NFC</span>
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
                            </div>
                            <div class="tab-content">
                                <div class="tab-pane active" id="connectivity">
                                    <ul>
                                        <li>Impresión desde smartphones y tablets</li>
                                        <li>Integración con Google Workspace y Office 365</li>
                                        <li>Escaneo directo a email y cloud</li>
                                        <li>Aplicaciones móviles nativas</li>
                                    </ul>
                                </div>
                                <div class="tab-pane" id="security">
                                    <ul>
                                        <li>Autenticación de usuario con tarjeta</li>
                                        <li>Encriptación de datos</li>
                                        <li>Secure Print con PIN</li>
                                        <li>Borrado seguro de disco duro</li>
                                    </ul>
                                </div>
                                <div class="tab-pane" id="productivity">
                                    <ul>
                                        <li>Escaneo automático duplex</li>
                                        <li>Detección de documentos múltiples</li>
                                        <li>OCR integrado para PDFs buscables</li>
                                        <li>Workflows personalizables</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            'impresoras-laser': {
                title: 'Impresoras Láser',
                icon: 'fas fa-print',
                content: `
                    <div class="product-showcase">
                        <div class="row">
                            <div class="col-md-6">
                                <img src="https://images.unsplash.com/photo-1562577309-2592ab84b1bc?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80" alt="Impresoras Láser" class="img-fluid rounded mb-4"/>
                                <div class="advantages-grid">
                                    <h5>Ventajas del Láser</h5>
                                    <div class="advantage-item">
                                        <i class="fas fa-bolt text-warning"></i>
                                        <div>
                                            <h6>Velocidad Superior</h6>
                                            <p>Hasta 75 ppm en modelos profesionales</p>
                                        </div>
                                    </div>
                                    <div class="advantage-item">
                                        <i class="fas fa-dollar-sign text-success"></i>
                                        <div>
                                            <h6>Costo por Página</h6>
                                            <p>El más bajo del mercado para alto volumen</p>
                                        </div>
                                    </div>
                                    <div class="advantage-item">
                                        <i class="fas fa-shield-alt text-primary"></i>
                                        <div>
                                            <h6>Durabilidad</h6>
                                            <p>Diseñadas para millones de impresiones</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h4>Especificaciones por Categoría</h4>
                                <div class="category-tabs">
                                    <div class="category-tab active" data-category="office">
                                        <h6>Oficina</h6>
                                    </div>
                                    <div class="category-tab" data-category="production">
                                        <h6>Producción</h6>
                                    </div>
                                </div>
                                <div class="tab-content">
                                    <div class="tab-pane active" id="office">
                                        <div class="specs-table">
                                            <div class="spec-row">
                                                <span class="spec-label">Velocidad:</span>
                                                <span class="spec-value">20-40 ppm</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Ciclo mensual:</span>
                                                <span class="spec-value">2,000-15,000 páginas</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Conectividad:</span>
                                                <span class="spec-value">WiFi, Ethernet, USB</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Duplex:</span>
                                                <span class="spec-value">Automático estándar</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="tab-pane" id="production">
                                        <div class="specs-table">
                                            <div class="spec-row">
                                                <span class="spec-label">Velocidad:</span>
                                                <span class="spec-value">45-75 ppm</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Ciclo mensual:</span>
                                                <span class="spec-value">50,000-300,000 páginas</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Acabados:</span>
                                                <span class="spec-value">Finisher, grapadoras</span>
                                            </div>
                                            <div class="spec-row">
                                                <span class="spec-label">Papel:</span>
                                                <span class="spec-value">60-300 gsm</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4">Tecnologías Incluidas</h5>
                                <div class="tech-badges">
                                    <span class="tech-badge">PCL6</span>
                                    <span class="tech-badge">PostScript</span>
                                    <span class="tech-badge">PDF Directo</span>
                                    <span class="tech-badge">Mobile Print</span>
                                    <span class="tech-badge">Secure Print</span>
                                    <span class="tech-badge">Energy Star</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="comparison-section mt-4">
                            <h4>Comparación Tecnológica</h4>
                            <div class="comparison-table">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Aspecto</th>
                                            <th>Láser</th>
                                            <th>Inkjet</th>
                                            <th>Ventaja</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Velocidad</td>
                                            <td>Muy alta</td>
                                            <td>Moderada</td>
                                            <td><i class="fas fa-check text-success"></i> Láser</td>
                                        </tr>
                                        <tr>
                                            <td>Costo por página</td>
                                            <td>Muy bajo</td>
                                            <td>Alto</td>
                                            <td><i class="fas fa-check text-success"></i> Láser</td>
                                        </tr>
                                        <tr>
                                            <td>Durabilidad</td>
                                            <td>Excelente</td>
                                            <td>Buena</td>
                                            <td><i class="fas fa-check text-success"></i> Láser</td>
                                        </tr>
                                        <tr>
                                            <td>Calidad texto</td>
                                            <td>Perfecta</td>
                                            <td>Muy buena</td>
                                            <td><i class="fas fa-check text-success"></i> Láser</td>
                                        </tr>
                                        <tr>
                                            <td>Calidad foto</td>
                                            <td>Buena</td>
                                            <td>Excelente</td>
                                            <td><i class="fas fa-check text-warning"></i> Inkjet</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `
            },
            'equipos-especializados': {
                title: 'Equipos Especializados',
                icon: 'fas fa-industry',
                content: `
                    <div class="product-showcase">
                        <div class="specialized-categories">
                            <h4>Categorías Especializadas</h4>
                            <div class="category-grid">
                                <div class="specialty-card">
                                    <div class="specialty-icon">
                                        <i class="fas fa-ruler-combined"></i>
                                    </div>
                                    <h5>Gran Formato</h5>
                                    <p>Impresoras A0, A1 y A2 para planos, pósters y cartelería profesional</p>
                                    <ul class="specialty-features">
                                        <li>Hasta 44 pulgadas de ancho</li>
                                        <li>Tintas pigmentadas resistentes</li>
                                        <li>Software de RIP incluido</li>
                                        <li>Soporte para CAD y GIS</li>
                                    </ul>
                                </div>
                                
                                <div class="specialty-card">
                                    <div class="specialty-icon">
                                        <i class="fas fa-industry"></i>
                                    </div>
                                    <h5>Producción Industrial</h5>
                                    <p>Equipos de alto volumen para centros de impresión y servicios gráficos</p>
                                    <ul class="specialty-features">
                                        <li>100+ páginas por minuto</li>
                                        <li>Ciclo de trabajo 500K+ páginas</li>
                                        <li>Acabados profesionales</li>
                                        <li>Control de calidad automático</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="consultation-cta mt-4">
                            <div class="cta-box">
                                <h5><i class="fas fa-user-tie me-2"></i>Consultoría Especializada</h5>
                                <p>Cada industria tiene necesidades únicas. Nuestros especialistas analizan tu caso específico para recomendar la solución más eficiente.</p>
                                <div class="cta-features">
                                    <span><i class="fas fa-check text-success me-1"></i>Análisis sin costo</span>
                                    <span><i class="fas fa-check text-success me-1"></i>Propuesta personalizada</span>
                                    <span><i class="fas fa-check text-success me-1"></i>ROI proyectado</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            }
        };

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
                        initModalTabs();
                        modalBody.classList.add('animate-fade-in', 'visible');
                    }, 100);
                }
            });
        });

        // Limpiar animaciones al cerrar modal
        modal.addEventListener('hidden.bs.modal', function() {
            modalBody.classList.remove('animate-fade-in', 'visible');
        });
    }

    // ====================================
    // TABS DENTRO DE MODALES
    // ====================================
    function initModalTabs() {
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
                    if (pane.id === targetCategory) {
                        pane.classList.add('active');
                    }
                });
            });
        });

        // Industry tabs
        const industryTabs = document.querySelectorAll('.industry-tab');
        industryTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetIndustry = this.getAttribute('data-industry');
                
                industryTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Mostrar contenido correspondiente
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.id === targetIndustry) {
                        pane.classList.add('active');
                    }
                });
            });
        });
    }

    // ====================================
    // ESTILOS CSS DINÁMICOS PARA MODALES
    // ====================================
    const modalStyles = `
        /* Timeline Styles */
        .timeline {
            position: relative;
            padding: 20px 0;
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
        }
        
        .timeline-content h5 {
            margin-bottom: 10px;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .timeline-content p {
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        .timeline-content small {
            color: #adb5bd;
        }
        
        /* Maintenance Schedule */
        .maintenance-schedule {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #e9ecef;
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
        }
        
        .task {
            color: #6c757d;
            flex-grow: 1;
            text-align: right;
        }
        
        /* Service Stats */
        .service-stats .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .service-stats .stat-card:hover {
            transform: translateY(-3px);
        }
        
        .stat-card h3 {
            margin-bottom: 8px;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .stat-card p {
            margin: 0;
            font-size: 0.875rem;
            color: #6c757d;
        }
        
        /* Guarantee Grid */
        .guarantee-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin: 24px 0;
        }
        
        .guarantee-card {
            background: #f8f9fa;
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }
        
        .guarantee-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .guarantee-icon {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 16px;
        }
        
        .guarantee-card h5 {
            color: #2c3e50;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .guarantee-card p {
            color: #6c757d;
            margin-bottom: 16px;
            line-height: 1.5;
        }
        
        .coverage-list {
            list-style: none;
            padding: 0;
            margin: 16px 0;
            text-align: left;
        }
        
        .coverage-list li {
            padding: 6px 0;
            color: #6c757d;
            font-size: 0.875rem;
        }
        
        .coverage-list li:before {
            content: "✓";
            color: #28a745;
            font-weight: bold;
            margin-right: 8px;
        }
        
        /* Response Times */
        .response-times {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin: 16px 0;
        }
        
        .time-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-align: center;
        }
        
        .time-badge.critical { 
            background: #dc3545; 
            color: white; 
        }
        
        .time-badge.high { 
            background: #fd7e14; 
            color: white; 
        }
        
        .time-badge.medium { 
            background: #ffc107; 
            color: #212529; 
        }
        
        .time-badge.low { 
            background: #198754; 
            color: white; 
        }
        
        /* Replacement Process */
        .replacement-process {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin: 16px 0;
            flex-wrap: wrap;
        }
        
        .process-step {
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .process-arrow {
            color: #667eea;
            font-weight: bold;
            font-size: 1.2rem;
        }
        
        /* Brand Stats */
        .brand-logo-large {
            max-height: 80px;
            width: auto;
            margin-bottom: 20px;
        }
        
        .brand-stats {
            text-align: center;
        }
        
        .stat-item {
            margin: 12px 0;
        }
        
        .stat-number {
            display: block;
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
            line-height: 1;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #6c757d;
            margin-top: 4px;
        }
        
        /* Feature Grid */
        .feature-grid {
            display: grid;
            gap: 20px;
            margin: 20px 0;
        }
        
        .feature-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
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
        
        /* Models Grid */
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .model-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .model-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .model-card h6 {
            color: #667eea;
            font-weight: 600;
            margin-bottom: 12px;
            font-size: 1.1rem;
        }
        
        .model-specs {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        
        .model-specs span {
            background: #e9ecef;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            color: #495057;
            font-weight: 500;
        }
        
        .model-card p {
            color: #6c757d;
            font-size: 0.875rem;
            margin: 0;
            line-height: 1.4;
        }
        
        /* Tabs */
        .feature-tabs,
        .category-tabs,
        .industry-tabs {
            display: flex;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 20px;
            gap: 4px;
            overflow-x: auto;
        }
        
        .feature-tab,
        .category-tab,
        .industry-tab {
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
        }
        
        .feature-tab.active,
        .category-tab.active,
        .industry-tab.active {
            background: white;
            color: #667eea;
            border-color: #e9ecef;
            border-bottom-color: white;
            margin-bottom: -2px;
            z-index: 1;
            position: relative;
        }
        
        .feature-tab:hover,
        .category-tab:hover,
        .industry-tab:hover {
            background: #e9ecef;
        }
        
        .feature-tab.active:hover,
        .category-tab.active:hover,
        .industry-tab.active:hover {
            background: white;
        }
        
        .tab-content {
            margin-top: 20px;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        /* Specs Table */
        .specs-table {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
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
        
        /* Tech Badges */
        .tech-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 16px 0;
        }
        
        .tech-badge {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .guarantee-grid,
            .feature-grid,
            .models-grid {
                grid-template-columns: 1fr;
            }
            
            .replacement-process {
                flex-direction: column;
                gap: 8px;
            }
            
            .process-arrow {
                transform: rotate(90deg);
            }
            
            .feature-tabs,
            .category-tabs,
            .industry-tabs {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
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
        }
    `;

    // Inyectar estilos de modales
    const modalStyleSheet = document.createElement('style');
    modalStyleSheet.textContent = modalStyles;
    document.head.appendChild(modalStyleSheet);

    // Hacer funciones disponibles globalmente
    window.copierHomepagePart2 = {
        initModals,
        initModalTabs
    };

})();querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.id === targetTab) {
                        pane.classList.add('active');
                    }
                });
            });
        });

        // Category tabs
        const categoryTabs = document.querySelectorAll('.category-tab');
        categoryTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetCategory = this.getAttribute('data-category');
                
                categoryTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Mostrar contenido correspondiente
                const tabPanes = document.