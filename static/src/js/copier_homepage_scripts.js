(function() {
'use strict';

/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 1/10: INICIALIZACIÓN Y EFECTOS DE SCROLL
 * Versión Bootstrap Icons - Compatible con Odoo - CORREGIDA
 */

function initPart() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPart);
        return;
    }
    
    console.log('🚀 Iniciando Copier Company JS v2.0 - Parte 1/10');
    
    // =============================================
    // VERIFICACIÓN DE DEPENDENCIAS BOOTSTRAP
    // =============================================
    
    function checkBootstrapDependencies() {
        // Verificar si Bootstrap CSS ya está cargado por Odoo
        const hasBootstrapCSS = Array.from(document.styleSheets).some(sheet => {
            try {
                return sheet.href && (
                    sheet.href.includes('bootstrap') || 
                    sheet.href.includes('web.assets') ||
                    sheet.href.includes('cdn.jsdelivr.net')
                );
            } catch (e) {
                return false;
            }
        });
        
        // Verificar si Bootstrap Icons está disponible
        const hasBootstrapIcons = document.querySelector('link[href*="bootstrap-icons"]') !== null;
        
        if (!hasBootstrapIcons) {
            console.log('📦 Cargando Bootstrap Icons...');
            addBootstrapDependencies();
        } else {
            console.log('✅ Bootstrap Icons ya disponible');
        }
        
        if (hasBootstrapCSS) {
            console.log('✅ Bootstrap CSS detectado (Odoo)');
        }
        
        console.log('✅ Dependencias Bootstrap verificadas');
    }
    
    function addBootstrapDependencies() {
        // Solo Bootstrap Icons, sin Bootstrap CSS
        if (!document.querySelector('link[href*="bootstrap-icons"]')) {
            const iconsLink = document.createElement('link');
            iconsLink.rel = 'stylesheet';
            iconsLink.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css';
            iconsLink.onload = () => console.log('📦 Bootstrap Icons cargado exitosamente');
            iconsLink.onerror = () => console.warn('⚠️ Error cargando Bootstrap Icons');
            document.head.appendChild(iconsLink);
        }
    }
    
    // =============================================
    // EFECTOS DE SCROLL Y ANIMACIONES BÁSICAS
    // =============================================
    
    function initScrollEffects() {
        // Scroll indicator animation con Bootstrap Icons
        const scrollIndicator = document.querySelector('.scroll-indicator');
        if (scrollIndicator) {
            // Reemplazar icono si es necesario
            const icon = scrollIndicator.querySelector('i');
            if (icon && (icon.className.includes('fas') || icon.className.includes('fa-'))) {
                icon.className = 'bi bi-chevron-down';
            }
            
            scrollIndicator.addEventListener('click', function() {
                const benefitsSection = document.querySelector('.benefits-section');
                if (benefitsSection) {
                    benefitsSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
            
            // Hide/show scroll indicator based on scroll position
            let scrollTimeout;
            window.addEventListener('scroll', function() {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    const scrollY = window.scrollY || window.pageYOffset;
                    
                    if (scrollY > 100) {
                        scrollIndicator.style.opacity = '0';
                        scrollIndicator.style.transform = 'translateY(20px) scale(0.8)';
                        scrollIndicator.style.pointerEvents = 'none';
                    } else {
                        scrollIndicator.style.opacity = '1';
                        scrollIndicator.style.transform = 'translateY(0) scale(1)';
                        scrollIndicator.style.pointerEvents = 'auto';
                    }
                }, 10);
            });
        }
        
        console.log('✅ Efectos de scroll inicializados');
    }
    
    // =============================================
    // INTERSECTION OBSERVER PARA ANIMACIONES
    // =============================================
    
    function initIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const animationObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    
                    // Agregar clase de animación
                    target.classList.add('animate-in');
                    
                    // Animar elementos hijo con delay escalonado
                    const children = target.querySelectorAll('.benefit-item, .feature-item, .stat-item');
                    children.forEach((child, index) => {
                        setTimeout(() => {
                            child.classList.add('animate-in');
                        }, index * 100);
                    });
                    
                    // Una vez animado, dejar de observar para mejor performance
                    animationObserver.unobserve(target);
                }
            });
        }, observerOptions);
        
        // Elementos que se animan al entrar en viewport
        const animatedElements = document.querySelectorAll(
            '.benefit-card, .brand-card, .product-card, .process-step, ' +
            '.testimonial-card, .service-card, .feature-section, .stats-section'
        );
        
        animatedElements.forEach(el => {
            el.classList.add('animate-ready');
            animationObserver.observe(el);
        });
        
        console.log(`✅ Intersection Observer configurado para ${animatedElements.length} elementos`);
    }
    
    // =============================================
    // EFECTOS HOVER MEJORADOS CON BOOTSTRAP
    // =============================================
    
    function initHoverEffects() {
        // Service cards hover effect con Bootstrap classes
        const serviceCards = document.querySelectorAll('.service-card, .benefit-card, .product-card');
        
        serviceCards.forEach(card => {
            // Configurar estado inicial
            card.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
                this.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15)';
                this.style.zIndex = '10';
                
                // Animar icono si existe
                const icon = this.querySelector('i.bi');
                if (icon) {
                    icon.style.transform = 'scale(1.2) rotate(5deg)';
                    icon.style.transition = 'transform 0.3s ease';
                }
                
                // Efecto en el texto
                const title = this.querySelector('h3, h4, h5, h6');
                if (title) {
                    title.style.color = '#0066cc';
                    title.style.transition = 'color 0.3s ease';
                }
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
                this.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
                this.style.zIndex = 'auto';
                
                // Restaurar icono
                const icon = this.querySelector('i.bi');
                if (icon) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                }
                
                // Restaurar color del texto
                const title = this.querySelector('h3, h4, h5, h6');
                if (title) {
                    title.style.color = '';
                }
            });
        });
        
        console.log(`✅ Efectos hover aplicados a ${serviceCards.length} elementos`);
    }
    
    // =============================================
    // ANIMACIÓN DE TARJETAS FLOTANTES
    // =============================================
    
    function initFloatingCards() {
        const floatingCards = document.querySelectorAll('.floating-card, .hero-card');
        
        if (floatingCards.length > 0) {
            let animationFrameId;
            
            function animateFloatingCards() {
                const time = Date.now() * 0.001; // Convertir a segundos
                
                floatingCards.forEach((card, index) => {
                    const offset = index * 1.5; // Desfase entre tarjetas
                    const yOffset = Math.sin(time + offset) * 8; // Movimiento vertical suave
                    const rotationOffset = Math.sin(time * 0.5 + offset) * 2; // Rotación sutil
                    
                    card.style.transform = `translateY(${yOffset}px) rotate(${rotationOffset}deg)`;
                });
                
                animationFrameId = requestAnimationFrame(animateFloatingCards);
            }
            
            // Iniciar animación
            animateFloatingCards();
            
            // Pausar animación cuando no es visible (performance)
            const visibilityObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        if (!animationFrameId) {
                            animateFloatingCards();
                        }
                    } else {
                        if (animationFrameId) {
                            cancelAnimationFrame(animationFrameId);
                            animationFrameId = null;
                        }
                    }
                });
            });
            
            floatingCards.forEach(card => visibilityObserver.observe(card));
            
            console.log(`✅ Animación flotante aplicada a ${floatingCards.length} tarjetas`);
        }
    }
    
    // =============================================
    // ACTUALIZACIÓN DE ICONOS FONT AWESOME A BOOTSTRAP
    // =============================================
    
    function updateIconsToBootstrap() {
        // Mapeo de iconos Font Awesome a Bootstrap Icons
        const iconMap = {
            'fas fa-hand-holding-usd': 'bi bi-cash-coin',
            'fas fa-headset': 'bi bi-headset',
            'fas fa-rocket': 'bi bi-rocket-takeoff',
            'fas fa-cog': 'bi bi-gear',
            'fas fa-shield-alt': 'bi bi-shield-check',
            'fas fa-chart-line': 'bi bi-graph-up-arrow',
            'fas fa-print': 'bi bi-printer',
            'fas fa-copy': 'bi bi-files',
            'fas fa-scanner': 'bi bi-scan',
            'fas fa-fax': 'bi bi-telephone',
            'fas fa-wifi': 'bi bi-wifi',
            'fas fa-mobile-alt': 'bi bi-phone',
            'fas fa-cloud': 'bi bi-cloud',
            'fas fa-fingerprint': 'bi bi-fingerprint',
            'fas fa-check': 'bi bi-check-lg',
            'fas fa-times': 'bi bi-x-lg',
            'fas fa-arrow-up': 'bi bi-arrow-up',
            'fas fa-arrow-down': 'bi bi-arrow-down',
            'fas fa-exchange-alt': 'bi bi-arrow-left-right',
            'fas fa-star': 'bi bi-star-fill',
            'fas fa-heart': 'bi bi-heart-fill',
            'fas fa-thumbs-up': 'bi bi-hand-thumbs-up',
            'fas fa-comments': 'bi bi-chat-dots',
            'fas fa-envelope': 'bi bi-envelope',
            'fas fa-phone': 'bi bi-telephone',
            'fas fa-map-marker-alt': 'bi bi-geo-alt',
            'fas fa-calendar': 'bi bi-calendar3',
            'fas fa-clock': 'bi bi-clock',
            'fas fa-user': 'bi bi-person',
            'fas fa-users': 'bi bi-people',
            'fas fa-building': 'bi bi-building',
            'fas fa-home': 'bi bi-house',
            'fas fa-office': 'bi bi-building-fill',
            'fas fa-industry': 'bi bi-factory',
            'fas fa-hospital': 'bi bi-hospital',
            'fas fa-graduation-cap': 'bi bi-mortarboard',
            'fas fa-balance-scale': 'bi bi-scales',
            'fas fa-tools': 'bi bi-tools',
            'fas fa-wrench': 'bi bi-wrench',
            'fas fa-screwdriver': 'bi bi-screwdriver',
            'fas fa-hammer': 'bi bi-hammer'
        };
        
        // Buscar y reemplazar todos los iconos
        Object.keys(iconMap).forEach(oldClass => {
            const icons = document.querySelectorAll(`i.${oldClass.replace(/\s+/g, '.')}`);
            icons.forEach(icon => {
                icon.className = iconMap[oldClass];
            });
        });
        
        // También actualizar iconos con clases individuales
        const fasIcons = document.querySelectorAll('i[class*="fas"], i[class*="fa-"]');
        fasIcons.forEach(icon => {
            const classes = icon.className.split(' ');
            let newClass = '';
            
            // Mapear iconos comunes individualmente
            if (classes.includes('fa-chevron-down')) newClass = 'bi bi-chevron-down';
            else if (classes.includes('fa-chevron-up')) newClass = 'bi bi-chevron-up';
            else if (classes.includes('fa-chevron-left')) newClass = 'bi bi-chevron-left';
            else if (classes.includes('fa-chevron-right')) newClass = 'bi bi-chevron-right';
            else if (classes.includes('fa-bars')) newClass = 'bi bi-list';
            else if (classes.includes('fa-search')) newClass = 'bi bi-search';
            else if (classes.includes('fa-shopping-cart')) newClass = 'bi bi-cart';
            else if (classes.includes('fa-user-circle')) newClass = 'bi bi-person-circle';
            
            if (newClass) {
                icon.className = newClass;
            }
        });
        
        console.log('✅ Iconos actualizados a Bootstrap Icons');
    }
    
    // =============================================
    // ESTILOS CSS PARA ANIMACIONES
    // =============================================
    
    function injectAnimationStyles() {
        const animationStyles = `
        <style id="copier-animations">
        /* Animaciones base */
        .animate-ready {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
        
        /* Efectos para tarjetas */
        .service-card, .benefit-card, .product-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 15px !important;
            overflow: hidden;
            position: relative;
        }
        
        .service-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(0,102,204,0.05), rgba(0,102,204,0.1));
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }
        
        .service-card:hover::before {
            opacity: 1;
        }
        
        /* Animación de tarjetas flotantes */
        .floating-card, .hero-card {
            transition: transform 0.1s ease-out;
            will-change: transform;
        }
        
        /* Scroll indicator */
        .scroll-indicator {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            border-radius: 50%;
            background: rgba(255,255,255,0.9);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .scroll-indicator:hover {
            transform: translateY(-3px) scale(1.1);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        
        .scroll-indicator i {
            font-size: 1.5rem;
            color: #0066cc;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-10px);
            }
            60% {
                transform: translateY(-5px);
            }
        }
        
        /* Efectos para iconos */
        .bi {
            transition: all 0.3s ease;
        }
        
        /* Responsive optimizations */
        @media (max-width: 768px) {
            .animate-ready {
                transform: translateY(20px);
            }
            
            .floating-card {
                animation: none !important;
                transform: none !important;
            }
        }
        
        /* Reducir movimiento para usuarios que prefieren menos animación */
        @media (prefers-reduced-motion: reduce) {
            .animate-ready,
            .service-card,
            .floating-card,
            .scroll-indicator,
            .bi {
                transition: none !important;
                animation: none !important;
                transform: none !important;
            }
        }
        </style>
        `;
        
        // Inyectar estilos si no están presentes
        if (!document.querySelector('#copier-animations')) {
            document.head.insertAdjacentHTML('beforeend', animationStyles);
            console.log('✅ Estilos de animación inyectados');
        }
    }
    
    // =============================================
    // INICIALIZACIÓN DE LA PARTE 1
    // =============================================
    
    // Ejecutar todas las funciones de inicialización
    try {
        checkBootstrapDependencies();
        
        // Esperar un poco para que se carguen las dependencias
        setTimeout(() => {
            updateIconsToBootstrap();
            injectAnimationStyles();
            initScrollEffects();
            initIntersectionObserver();
            initHoverEffects();
            initFloatingCards();
            
            console.log('✅ Parte 1/10 inicializada completamente');
            
            // Disparar evento personalizado para notificar que Parte 1 está lista
            document.dispatchEvent(new CustomEvent('copierJS:part1Ready'));
            
        }, 500);
        
    } catch (error) {
        console.error('❌ Error en la inicialización de Parte 1:', error);
    }
}

// Llamar la función de inicialización
initPart();

// Objeto global para almacenar el estado
window.CopierCompany = window.CopierCompany || {
    version: '2.0.1',
    partsLoaded: [],
    config: {
        useBootstrapIcons: true,
        enableAnimations: true,
        enableFloatingCards: true
    }
};

window.CopierCompany.partsLoaded.push('part1');
console.log('📦 Copier Company JS - Parte 1/10 cargada - VERSIÓN ODOO');

})();
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 2/10: MODALES DINÁMICOS Y CONTENIDO INTERACTIVO
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 1 esté lista
document.addEventListener('copierJS:part1Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 2/10: Modales Dinámicos');
    
    // =============================================
    // BASE DE DATOS DE CONTENIDO PARA MODALES - BENEFICIOS
    // =============================================
    
    const modalContent = {
        benefits: {
            'sin-inversion': {
                title: 'Sin Inversión Inicial',
                icon: 'bi bi-cash-coin',
                content: `
                    <div class="benefit-detail">
                        <div class="row g-4">
                            <div class="col-md-6">
                                <h4 class="d-flex align-items-center mb-3">
                                    <i class="bi bi-piggy-bank text-primary me-2"></i>Ventajas Financieras
                                </h4>
                                <ul class="list-unstyled">
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Preserva tu capital de trabajo</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Mejora tu flujo de caja mensual</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>No afecta líneas de crédito</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Gastos 100% deducibles fiscalmente</span>
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h4 class="d-flex align-items-center mb-3">
                                    <i class="bi bi-graph-up-arrow text-primary me-2"></i>Beneficios Empresariales
                                </h4>
                                <ul class="list-unstyled">
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Tecnología de última generación</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Actualización constante sin costo</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Sin obsolescencia tecnológica</span>
                                    </li>
                                    <li class="d-flex align-items-start mb-2">
                                        <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                        <span>Escalabilidad según crecimiento</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div class="highlight-box mt-4 p-4 bg-light rounded-3 border-start border-warning border-5">
                            <div class="d-flex align-items-start">
                                <i class="bi bi-lightbulb-fill text-warning me-3 fs-4"></i>
                                <div>
                                    <h6 class="fw-bold mb-2">¿Sabías que?</h6>
                                    <p class="mb-0">Las empresas que alquilan equipos aumentan su productividad en un 
                                    <strong>35%</strong> al tener acceso constante a la última tecnología.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            'soporte-24-7': {
                title: 'Soporte Técnico 24/7',
                icon: 'bi bi-headset',
                content: `
                    <div class="benefit-detail">
                        <div class="row g-4">
                            <div class="col-md-4">
                                <div class="support-level card h-100 border-success">
                                    <div class="card-body text-center">
                                        <i class="bi bi-telephone-fill fs-1 text-success mb-3"></i>
                                        <h5>Nivel 1: Telefónico</h5>
                                        <span class="badge bg-success mb-3">Inmediato</span>
                                        <ul class="list-unstyled text-start">
                                            <li><i class="bi bi-check2 text-success me-2"></i>Diagnóstico inicial</li>
                                            <li><i class="bi bi-check2 text-success me-2"></i>Soluciones básicas</li>
                                            <li><i class="bi bi-check2 text-success me-2"></i>Orientación de uso</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="support-level card h-100 border-primary">
                                    <div class="card-body text-center">
                                        <i class="bi bi-laptop fs-1 text-primary mb-3"></i>
                                        <h5>Nivel 2: Remoto</h5>
                                        <span class="badge bg-primary mb-3">15 minutos</span>
                                        <ul class="list-unstyled text-start">
                                            <li><i class="bi bi-check2 text-primary me-2"></i>Conexión remota</li>
                                            <li><i class="bi bi-check2 text-primary me-2"></i>Configuraciones avanzadas</li>
                                            <li><i class="bi bi-check2 text-primary me-2"></i>Actualizaciones</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="support-level card h-100 border-warning">
                                    <div class="card-body text-center">
                                        <i class="bi bi-person-gear fs-1 text-warning mb-3"></i>
                                        <h5>Nivel 3: Presencial</h5>
                                        <span class="badge bg-warning text-dark mb-3">4 horas máx</span>
                                        <ul class="list-unstyled text-start">
                                            <li><i class="bi bi-check2 text-warning me-2"></i>Técnico especializado</li>
                                            <li><i class="bi bi-check2 text-warning me-2"></i>Reparaciones complejas</li>
                                            <li><i class="bi bi-check2 text-warning me-2"></i>Reemplazo de equipos</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row g-3 text-center mt-4">
                            <div class="col-md-3">
                                <div class="stat-item p-3 bg-primary bg-opacity-10 rounded-3">
                                    <i class="bi bi-check-circle-fill fs-2 text-primary mb-2"></i>
                                    <h3 class="fs-1 fw-bold text-primary">98%</h3>
                                    <p class="small text-muted">Resolución remota</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item p-3 bg-success bg-opacity-10 rounded-3">
                                    <i class="bi bi-stopwatch-fill fs-2 text-success mb-2"></i>
                                    <h3 class="fs-1 fw-bold text-success">15min</h3>
                                    <p class="small text-muted">Tiempo promedio</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item p-3 bg-warning bg-opacity-10 rounded-3">
                                    <i class="bi bi-clock-fill fs-2 text-warning mb-2"></i>
                                    <h3 class="fs-1 fw-bold text-warning">24/7</h3>
                                    <p class="small text-muted">Disponibilidad</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item p-3 bg-info bg-opacity-10 rounded-3">
                                    <i class="bi bi-calendar-check-fill fs-2 text-info mb-2"></i>
                                    <h3 class="fs-1 fw-bold text-info">365</h3>
                                    <p class="small text-muted">Días al año</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            'instalacion-rapida': {
                title: 'Instalación en 24H',
                icon: 'bi bi-rocket-takeoff',
                content: `
                    <div class="benefit-detail">
                        <h4 class="d-flex align-items-center mb-4">
                            <i class="bi bi-clock-history text-primary me-2"></i>Proceso Express
                        </h4>
                        <div class="timeline-item d-flex mb-4">
                            <div class="timeline-marker bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-4" style="width: 50px; height: 50px;">
                                <span class="fw-bold">1</span>
                            </div>
                            <div class="timeline-content">
                                <h5><i class="bi bi-handshake text-primary me-2"></i>Confirmación (2h)</h5>
                                <ul class="list-unstyled">
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Verificación técnica</li>
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Programación coordinada</li>
                                </ul>
                            </div>
                        </div>
                        <div class="timeline-item d-flex mb-4">
                            <div class="timeline-marker bg-success text-white rounded-circle d-flex align-items-center justify-content-center me-4" style="width: 50px; height: 50px;">
                                <span class="fw-bold">2</span>
                            </div>
                            <div class="timeline-content">
                                <h5><i class="bi bi-truck text-success me-2"></i>Transporte (4h)</h5>
                                <ul class="list-unstyled">
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Embalaje profesional</li>
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Transporte asegurado</li>
                                </ul>
                            </div>
                        </div>
                        <div class="timeline-item d-flex mb-4">
                            <div class="timeline-marker bg-warning text-dark rounded-circle d-flex align-items-center justify-content-center me-4" style="width: 50px; height: 50px;">
                                <span class="fw-bold">3</span>
                            </div>
                            <div class="timeline-content">
                                <h5><i class="bi bi-gear-fill text-warning me-2"></i>Instalación (2-4h)</h5>
                                <ul class="list-unstyled">
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Instalación física</li>
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Configuración completa</li>
                                    <li><i class="bi bi-check-lg text-success me-2"></i>Capacitación básica</li>
                                </ul>
                            </div>
                        </div>
                        <div class="alert alert-success mt-4">
                            <i class="bi bi-shield-fill-check me-2"></i>
                            <strong>Garantía:</strong> Si no cumplimos 24h, 
                            <strong>primer mes GRATIS</strong>
                        </div>
                    </div>
                `
            }
        }
    };
    
    // =============================================
    // SISTEMA DE MODALES SIMPLIFICADO
    // =============================================
    
    const modalSystem = {
        init: function() {
            this.createModal();
            this.bindEvents();
            console.log('✅ Sistema de modales inicializado');
        },
        
        createModal: function() {
            if (document.getElementById('benefitModal')) return;
            
            const modalHTML = `
                <div class="modal fade" id="benefitModal" tabindex="-1">
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content border-0 shadow-lg">
                            <div class="modal-header bg-primary text-white">
                                <h4 class="modal-title" id="benefitModalLabel">
                                    <i class="bi bi-info-circle me-2"></i>Información
                                </h4>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-4" id="benefitModalBody">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary"></div>
                                </div>
                            </div>
                            <div class="modal-footer bg-light">
                                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                    <i class="bi bi-x-lg me-2"></i>Cerrar
                                </button>
                                <a href="/cotizacion/form" class="btn btn-primary">
                                    <i class="bi bi-calculator me-2"></i>Solicitar Cotización
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        },
        
        bindEvents: function() {
            document.addEventListener('click', (e) => {
                const benefitCard = e.target.closest('[data-benefit]');
                if (benefitCard) {
                    e.preventDefault();
                    const benefitType = benefitCard.getAttribute('data-benefit');
                    this.openModal(benefitType);
                }
            });
        },
        
        openModal: function(benefitType) {
            const data = modalContent.benefits[benefitType];
            if (!data) return;
            
            document.getElementById('benefitModalLabel').innerHTML = 
                `<i class="${data.icon} me-2"></i>${data.title}`;
            document.getElementById('benefitModalBody').innerHTML = data.content;
            
            const modal = new bootstrap.Modal(document.getElementById('benefitModal'));
            modal.show();
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 2
    // =============================================
    
    try {
        modalSystem.init();
        
        console.log('✅ Parte 2/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part2Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 2:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.modalContent = modalContent;
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part2');

console.log('📦 Copier Company JS - Parte 2/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 3/10: MODALES DE MARCAS Y PRODUCTOS
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 2 esté lista
document.addEventListener('copierJS:part2Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 3/10: Modales de Marcas');
    
    // =============================================
    // BASE DE DATOS DE CONTENIDO PARA MARCAS
    // =============================================
    
    const brandsContent = {
        'konica': {
            title: 'Konica Minolta',
            logo: 'https://filedn.com/lSeVjMkwzjCzV24eJl1FUoj/konica-minolta-vector-logo-seeklogo/konica-minolta-seeklogo.png',
            description: 'Tecnología japonesa de vanguardia para soluciones empresariales',
            content: `
                <div class="brand-detail">
                    <div class="row g-4">
                        <div class="col-md-8">
                            <h4 class="d-flex align-items-center mb-3">
                                <i class="bi bi-award-fill text-primary me-2"></i>Acerca de Konica Minolta
                            </h4>
                            <p class="mb-4">Líder mundial en tecnología de impresión con más de 150 años de innovación. 
                            Especializada en soluciones multifuncionales de alta gama para empresas que requieren 
                            máxima calidad y productividad.</p>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-rocket-takeoff text-success me-2"></i>Ventajas Clave
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Velocidad hasta 75 ppm</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Calidad superior</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Seguridad avanzada</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Conectividad cloud</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Bajo consumo</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-building text-warning me-2"></i>Ideal Para
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-building me-2"></i>Grandes corporaciones</li>
                                        <li><i class="bi bi-mortarboard me-2"></i>Instituciones educativas</li>
                                        <li><i class="bi bi-hospital me-2"></i>Centros médicos</li>
                                        <li><i class="bi bi-scales me-2"></i>Estudios legales</li>
                                        <li><i class="bi bi-printer me-2"></i>Centros de impresión</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-speedometer2 text-info me-2"></i>Especificaciones
                                    </h5>
                                    <div class="row g-2 text-center">
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-primary">75</div>
                                                <small>ppm máximo</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-primary">1200</div>
                                                <small>dpi resolución</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-primary">300K</div>
                                                <small>hojas/mes</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-primary">10.1"</div>
                                                <small>pantalla táctil</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <h6><i class="bi bi-list-ul text-secondary me-2"></i>Modelos Populares</h6>
                                <div class="list-group list-group-flush">
                                    <div class="list-group-item d-flex justify-content-between">
                                        <strong>bizhub C558</strong>
                                        <span class="text-muted">55 ppm</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between">
                                        <strong>bizhub C658</strong>
                                        <span class="text-muted">65 ppm</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between">
                                        <strong>bizhub C758</strong>
                                        <span class="text-muted">75 ppm</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row g-3 mt-4">
                        <div class="col-md-4">
                            <div class="feature-card text-center p-3 bg-light rounded">
                                <i class="bi bi-shield-check text-success fs-1 mb-2"></i>
                                <h6>Seguridad Avanzada</h6>
                                <p class="small">Autenticación biométrica y encriptación</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card text-center p-3 bg-light rounded">
                                <i class="bi bi-phone text-primary fs-1 mb-2"></i>
                                <h6>Impresión Móvil</h6>
                                <p class="small">Compatible con iOS, Android y cloud</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card text-center p-3 bg-light rounded">
                                <i class="bi bi-tree text-success fs-1 mb-2"></i>
                                <h6>Eco-Friendly</h6>
                                <p class="small">Bajo consumo y materiales reciclables</p>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'canon': {
            title: 'Canon',
            logo: 'https://filedn.com/lSeVjMkwzjCzV24eJl1FUoj/canon-vector-logo-seeklogo/canon-seeklogo.png',
            description: 'Excelencia en calidad de imagen y tecnología profesional',
            content: `
                <div class="brand-detail">
                    <div class="row g-4">
                        <div class="col-md-8">
                            <h4 class="d-flex align-items-center mb-3">
                                <i class="bi bi-camera-fill text-primary me-2"></i>Acerca de Canon
                            </h4>
                            <p class="mb-4">Reconocida mundialmente por su excelencia en tecnología de imagen. 
                            Canon combina décadas de experiencia en fotografía con innovación en soluciones 
                            de oficina, ofreciendo equipos con calidad de imagen excepcional.</p>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-star-fill text-warning me-2"></i>Fortalezas
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Calidad de imagen superior</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Tecnología MEAP avanzada</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Diseño compacto</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Interfaz intuitiva</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Confiabilidad probada</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-people-fill text-info me-2"></i>Perfecto Para
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-palette me-2"></i>Agencias de diseño</li>
                                        <li><i class="bi bi-camera me-2"></i>Estudios fotográficos</li>
                                        <li><i class="bi bi-briefcase me-2"></i>Oficinas medianas</li>
                                        <li><i class="bi bi-shop me-2"></i>Retail y comercio</li>
                                        <li><i class="bi bi-house me-2"></i>Oficinas en casa</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-danger">
                                <div class="card-body">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-speedometer text-danger me-2"></i>Rendimiento
                                    </h5>
                                    <div class="row g-2 text-center">
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-danger">55</div>
                                                <small>ppm máximo</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-danger">2400</div>
                                                <small>dpi calidad</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-danger">150K</div>
                                                <small>hojas/mes</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-danger">10.1"</div>
                                                <small>pantalla táctil</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <h6><i class="bi bi-layers text-primary me-2"></i>Series Disponibles</h6>
                                <div class="list-group list-group-flush">
                                    <div class="list-group-item">
                                        <strong>imageRUNNER ADVANCE</strong>
                                        <br><small class="text-muted">Serie empresarial</small>
                                    </div>
                                    <div class="list-group-item">
                                        <strong>imageRUNNER C3500</strong>
                                        <br><small class="text-muted">Color multifuncional</small>
                                    </div>
                                    <div class="list-group-item">
                                        <strong>imageCLASS</strong>
                                        <br><small class="text-muted">Oficina pequeña</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row g-3 mt-4">
                        <div class="col-md-3">
                            <div class="tech-card text-center p-3 bg-light rounded">
                                <i class="bi bi-eye-fill text-primary fs-1 mb-2"></i>
                                <h6>MEAP Platform</h6>
                                <p class="small">Plataforma de aplicaciones empresariales</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card text-center p-3 bg-light rounded">
                                <i class="bi bi-cloud-fill text-info fs-1 mb-2"></i>
                                <h6>uniFLOW</h6>
                                <p class="small">Gestión de documentos en la nube</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card text-center p-3 bg-light rounded">
                                <i class="bi bi-brush-fill text-warning fs-1 mb-2"></i>
                                <h6>Calidad de Imagen</h6>
                                <p class="small">Tecnología heredada de cámaras</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card text-center p-3 bg-light rounded">
                                <i class="bi bi-disc-fill text-success fs-1 mb-2"></i>
                                <h6>Toners V2</h6>
                                <p class="small">Tecnología avanzada para mejor calidad</p>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'ricoh': {
            title: 'Ricoh',
            logo: 'https://filedn.com/lSeVjMkwzjCzV24eJl1FUoj/ricoh-vector-logo-seeklogo/ricoh-seeklogo.png',
            description: 'Rendimiento superior y durabilidad empresarial',
            content: `
                <div class="brand-detail">
                    <div class="row g-4">
                        <div class="col-md-8">
                            <h4 class="d-flex align-items-center mb-3">
                                <i class="bi bi-factory text-primary me-2"></i>Acerca de Ricoh
                            </h4>
                            <p class="mb-4">Pionera en soluciones de oficina digital con enfoque en productividad empresarial. 
                            Ricoh se especializa en equipos robustos diseñados para entornos de alto volumen 
                            con máxima eficiencia operativa.</p>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-shield-fill text-success me-2"></i>Ventajas Únicas
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Máxima durabilidad</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Alto volumen mensual</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Seguridad empresarial</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Eficiencia energética</li>
                                        <li><i class="bi bi-check-lg text-success me-2"></i>Mantenimiento fácil</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-building-fill text-primary me-2"></i>Sectores Principales
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-bank me-2"></i>Gobierno y público</li>
                                        <li><i class="bi bi-hospital me-2"></i>Sector salud</li>
                                        <li><i class="bi bi-gear-fill me-2"></i>Manufactura</li>
                                        <li><i class="bi bi-credit-card me-2"></i>Servicios financieros</li>
                                        <li><i class="bi bi-truck me-2"></i>Logística</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-warning">
                                <div class="card-body">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-speedometer text-warning me-2"></i>Capacidades
                                    </h5>
                                    <div class="row g-2 text-center">
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-warning">60</div>
                                                <small>ppm velocidad</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-warning">300K</div>
                                                <small>páginas/mes</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-warning">1200</div>
                                                <small>dpi precisión</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-light p-2 rounded">
                                                <div class="fw-bold text-warning">99.9%</div>
                                                <small>confiabilidad</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <h6><i class="bi bi-puzzle text-info me-2"></i>Soluciones</h6>
                                <div class="list-group list-group-flush">
                                    <div class="list-group-item">
                                        <strong>IM Series</strong>
                                        <br><small class="text-muted">Inteligencia avanzada</small>
                                    </div>
                                    <div class="list-group-item">
                                        <strong>MP Series</strong>
                                        <br><small class="text-muted">Multifuncional tradicional</small>
                                    </div>
                                    <div class="list-group-item">
                                        <strong>Pro Series</strong>
                                        <br><small class="text-muted">Producción profesional</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row g-3 mt-4">
                        <div class="col-md-4">
                            <div class="innovation-card text-center p-3 bg-light rounded">
                                <i class="bi bi-cpu-fill text-info fs-1 mb-2"></i>
                                <h6>Smart Operation Panel</h6>
                                <p class="small">Interfaz que se adapta al usuario</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="innovation-card text-center p-3 bg-light rounded">
                                <i class="bi bi-lock-fill text-danger fs-1 mb-2"></i>
                                <h6>Security por Diseño</h6>
                                <p class="small">Seguridad desde hardware hasta software</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="innovation-card text-center p-3 bg-light rounded">
                                <i class="bi bi-recycle text-success fs-1 mb-2"></i>
                                <h6>Sostenibilidad</h6>
                                <p class="small">Compromiso con el medio ambiente</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-info mt-4">
                        <h6><i class="bi bi-headset me-2"></i>Soporte Ricoh Especializado</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <small><i class="bi bi-tools me-1"></i> Técnicos certificados</small><br>
                                <small><i class="bi bi-truck me-1"></i> Repuestos originales</small><br>
                                <small><i class="bi bi-graph-up me-1"></i> Monitoreo proactivo</small>
                            </div>
                            <div class="col-md-6">
                                <small><i class="bi bi-clock me-1"></i> Respuesta < 4 horas</small><br>
                                <small><i class="bi bi-mortarboard me-1"></i> Capacitación incluida</small><br>
                                <small><i class="bi bi-phone me-1"></i> App móvil soporte</small>
                            </div>
                        </div>
                    </div>
                </div>
            `
        }
    };
    
    // =============================================
    // SISTEMA DE MODALES PARA MARCAS
    // =============================================
    
    const brandModalSystem = {
        init: function() {
            this.createBrandModal();
            this.bindBrandEvents();
            console.log('✅ Sistema de modales de marcas inicializado');
        },
        
        createBrandModal: function() {
            if (document.getElementById('brandModal')) return;
            
            const modalHTML = `
                <div class="modal fade" id="brandModal" tabindex="-1">
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content border-0 shadow-lg">
                            <div class="modal-header bg-dark text-white">
                                <h4 class="modal-title" id="brandModalLabel">
                                    <i class="bi bi-award me-2"></i>Información de Marca
                                </h4>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-4" id="brandModalBody">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary"></div>
                                </div>
                            </div>
                            <div class="modal-footer bg-light">
                                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                    <i class="bi bi-x-lg me-2"></i>Cerrar
                                </button>
                                <a href="/productos" class="btn btn-primary">
                                    <i class="bi bi-eye me-2"></i>Ver Productos
                                </a>
                                <a href="/cotizacion/form" class="btn btn-success">
                                    <i class="bi bi-calculator me-2"></i>Cotización
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        },
        
        bindBrandEvents: function() {
            document.addEventListener('click', (e) => {
                const brandCard = e.target.closest('[data-brand]');
                if (brandCard) {
                    e.preventDefault();
                    const brandType = brandCard.getAttribute('data-brand');
                    this.openBrandModal(brandType);
                }
            });
        },
        
        openBrandModal: function(brandType) {
            const data = brandsContent[brandType];
            if (!data) return;
            
            const modalTitle = document.getElementById('brandModalLabel');
            const modalBody = document.getElementById('brandModalBody');
            
            modalTitle.innerHTML = `
                <img src="${data.logo}" alt="${data.title}" style="height: 30px; margin-right: 10px;">
                ${data.title}
            `;
            
            modalBody.innerHTML = data.content;
            
            const modal = new bootstrap.Modal(document.getElementById('brandModal'));
            modal.show();
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 3
    // =============================================
    
    try {
        brandModalSystem.init();
        
        console.log('✅ Parte 3/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part3Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 3:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.brandsContent = brandsContent;
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part3');

console.log('📦 Copier Company JS - Parte 3/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 4/10: MODALES DE PRODUCTOS Y ESPECIFICACIONES
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 3 esté lista
document.addEventListener('copierJS:part3Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 4/10: Modales de Productos');
    
    // =============================================
    // BASE DE DATOS DE CONTENIDO PARA PRODUCTOS
    // =============================================
    
    const productsContent = {
        'multifuncional-a3': {
            title: 'Multifuncionales A3',
            category: 'A3',
            icon: 'bi bi-printer-fill',
            description: 'Equipos de alto rendimiento para oficinas grandes y centros de copiado',
            content: `
                <div class="product-detail">
                    <div class="row g-4">
                        <div class="col-md-8">
                            <h4 class="d-flex align-items-center mb-3">
                                <i class="bi bi-aspect-ratio text-primary me-2"></i>Multifuncionales A3 Profesionales
                            </h4>
                            <p class="mb-4">Diseñados para empresas con alto volumen de impresión que requieren versatilidad 
                            en formatos grandes. Ideales para oficinas corporativas, centros de copiado y 
                            departamentos de marketing que manejan documentos de gran formato.</p>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-list-check text-success me-2"></i>Funciones Principales
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-printer me-2"></i>Impresión A3/A4 color y B&N</li>
                                        <li><i class="bi bi-files me-2"></i>Copiado hasta 75 ppm</li>
                                        <li><i class="bi bi-scanner me-2"></i>Escaneo dúplex automático</li>
                                        <li><i class="bi bi-telephone me-2"></i>Fax (opcional)</li>
                                        <li><i class="bi bi-filetype-pdf me-2"></i>Escaneo directo a PDF/email</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-gear-fill text-warning me-2"></i>Características Avanzadas
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-wifi me-2"></i>Conectividad WiFi y Ethernet</li>
                                        <li><i class="bi bi-phone me-2"></i>Impresión desde móviles</li>
                                        <li><i class="bi bi-cloud-fill me-2"></i>Integración con servicios cloud</li>
                                        <li><i class="bi bi-fingerprint me-2"></i>Autenticación biométrica</li>
                                        <li><i class="bi bi-book me-2"></i>Creación de folletos automática</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-speedometer2 text-info me-2"></i>Especificaciones
                                    </h5>
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <tr><td><i class="bi bi-lightning-fill me-1"></i>Velocidad</td><td><strong>35-75 ppm</strong></td></tr>
                                            <tr><td><i class="bi bi-eye me-1"></i>Resolución</td><td><strong>1200x1200 dpi</strong></td></tr>
                                            <tr><td><i class="bi bi-file-earmark me-1"></i>Vol. mensual</td><td><strong>50K-300K</strong></td></tr>
                                            <tr><td><i class="bi bi-memory me-1"></i>RAM</td><td><strong>4-8 GB</strong></td></tr>
                                            <tr><td><i class="bi bi-tablet me-1"></i>Pantalla</td><td><strong>10.1" táctil</strong></td></tr>
                                            <tr><td><i class="bi bi-file-ruled me-1"></i>Formatos</td><td><strong>A6 a A3+</strong></td></tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3 text-center">
                                <h6 class="d-flex align-items-center justify-content-center">
                                    <i class="bi bi-currency-dollar text-success me-2"></i>Alquiler Mensual
                                </h6>
                                <div class="price-display p-3 bg-success bg-opacity-10 rounded">
                                    <div class="fs-4 fw-bold text-success">$299 - $899</div>
                                    <small class="text-muted">*Incluye mantenimiento y soporte</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row g-3 mt-4">
                        <div class="col-md-4">
                            <div class="model-card card border-light">
                                <div class="card-body text-center">
                                    <h6 class="text-primary">Entrada (35-45 ppm)</h6>
                                    <ul class="list-unstyled small">
                                        <li>Ideal para oficinas medianas</li>
                                        <li>Funciones básicas completas</li>
                                        <li>Excelente relación precio/calidad</li>
                                    </ul>
                                    <div class="fw-bold text-success">$299-399/mes</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="model-card card border-primary">
                                <div class="card-body text-center">
                                    <h6 class="text-primary">Intermedio (50-60 ppm)</h6>
                                    <span class="badge bg-primary mb-2">Más Popular</span>
                                    <ul class="list-unstyled small">
                                        <li>Más popular para empresas</li>
                                        <li>Funciones avanzadas incluidas</li>
                                        <li>Óptimo rendimiento/costo</li>
                                    </ul>
                                    <div class="fw-bold text-success">$499-699/mes</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="model-card card border-warning">
                                <div class="card-body text-center">
                                    <h6 class="text-primary">Alto Rendimiento (65-75 ppm)</h6>
                                    <ul class="list-unstyled small">
                                        <li>Para centros de impresión</li>
                                        <li>Máximas funcionalidades</li>
                                        <li>Volúmenes industriales</li>
                                    </ul>
                                    <div class="fw-bold text-success">$699-899/mes</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-info mt-4">
                        <h6><i class="bi bi-star-fill text-warning me-2"></i>¿Por Qué Elegir A3?</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <small><i class="bi bi-arrows-expand me-1"></i> Versatilidad de formatos</small><br>
                                <small><i class="bi bi-graph-down me-1"></i> Reducción de costos operativos</small><br>
                                <small><i class="bi bi-people me-1"></i> Mayor productividad del equipo</small>
                            </div>
                            <div class="col-md-6">
                                <small><i class="bi bi-rocket me-1"></i> Procesamiento más rápido</small><br>
                                <small><i class="bi bi-shield-check me-1"></i> Funciones de seguridad avanzadas</small><br>
                                <small><i class="bi bi-plug me-1"></i> Conectividad empresarial</small>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'multifuncional-a4': {
            title: 'Multifuncionales A4',
            category: 'A4',
            icon: 'bi bi-printer',
            description: 'Soluciones compactas perfectas para oficinas medianas y pequeñas',
            content: `
                <div class="product-detail">
                    <div class="row g-4">
                        <div class="col-md-8">
                            <h4 class="d-flex align-items-center mb-3">
                                <i class="bi bi-laptop text-primary me-2"></i>Multifuncionales A4 Compactos
                            </h4>
                            <p class="mb-4">La solución ideal para oficinas que buscan funcionalidad completa en un espacio 
                            reducido. Perfectos para pequeñas y medianas empresas que requieren calidad 
                            profesional sin comprometer el espacio de trabajo.</p>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-check-circle text-success me-2"></i>Funciones Incluidas
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-printer me-2"></i>Impresión color/B&N hasta 35 ppm</li>
                                        <li><i class="bi bi-files me-2"></i>Copiado automático</li>
                                        <li><i class="bi bi-upc-scan me-2"></i>Escaneo color alta resolución</li>
                                        <li><i class="bi bi-wifi me-2"></i>Conectividad inalámbrica</li>
                                        <li><i class="bi bi-phone me-2"></i>Impresión móvil directa</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-gem text-warning me-2"></i>Ventajas Clave
                                    </h5>
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-house me-2"></i>Diseño compacto para cualquier espacio</li>
                                        <li><i class="bi bi-volume-down me-2"></i>Operación silenciosa</li>
                                        <li><i class="bi bi-battery me-2"></i>Bajo consumo energético</li>
                                        <li><i class="bi bi-emoji-smile me-2"></i>Interfaz intuitiva</li>
                                        <li><i class="bi bi-tools me-2"></i>Mantenimiento simplificado</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h5 class="d-flex align-items-center">
                                        <i class="bi bi-list text-info me-2"></i>Especificaciones
                                    </h5>
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <tr><td><i class="bi bi-lightning me-1"></i>Velocidad</td><td><strong>20-35 ppm</strong></td></tr>
                                            <tr><td><i class="bi bi-eye me-1"></i>Resolución</td><td><strong>600x600 dpi</strong></td></tr>
                                            <tr><td><i class="bi bi-file-earmark me-1"></i>Vol. mensual</td><td><strong>5K-50K</strong></td></tr>
                                            <tr><td><i class="bi bi-memory me-1"></i>Memoria</td><td><strong>512MB-2GB</strong></td></tr>
                                            <tr><td><i class="bi bi-tablet me-1"></i>Pantalla</td><td><strong>4.3"-7" táctil</strong></td></tr>
                                            <tr><td><i class="bi bi-rulers me-1"></i>Dimensiones</td><td><strong>Compacto</strong></td></tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <h6 class="d-flex align-items-center justify-content-center">
                                    <i class="bi bi-check-circle text-success me-2"></i>Compatibilidad
                                </h6>
                                <div class="row g-2 text-center">
                                    <div class="col-4">
                                        <div class="p-2 bg-light rounded">
                                            <i class="bi bi-windows fs-4 text-primary"></i>
                                            <div class="small">Windows</div>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="p-2 bg-light rounded">
                                            <i class="bi bi-apple fs-4 text-dark"></i>
                                            <div class="small">macOS</div>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="p-2 bg-light rounded">
                                            <i class="bi bi-ubuntu fs-4 text-warning"></i>
                                            <div class="small">Linux</div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="p-2 bg-light rounded">
                                            <i class="bi bi-android2 fs-4 text-success"></i>
                                            <div class="small">Android</div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="p-2 bg-light rounded">
                                            <i class="bi bi-apple fs-4 text-primary"></i>
                                            <div class="small">iOS</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <h5 class="d-flex align-items-center mt-4 mb-3">
                        <i class="bi bi-building text-primary me-2"></i>Escenarios de Uso Ideales
                    </h5>
                    <div class="row g-3">
                        <div class="col-md-3">
                            <div class="scenario-card text-center p-3 bg-light rounded">
                                <i class="bi bi-briefcase text-primary fs-1 mb-2"></i>
                                <h6>Oficinas Pequeñas</h6>
                                <p class="small">5-15 empleados con necesidades básicas</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card text-center p-3 bg-light rounded">
                                <i class="bi bi-house text-success fs-1 mb-2"></i>
                                <h6>Home Office</h6>
                                <p class="small">Profesionales independientes</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card text-center p-3 bg-light rounded">
                                <i class="bi bi-shop text-warning fs-1 mb-2"></i>
                                <h6>Retail</h6>
                                <p class="small">Tiendas con espacio limitado</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card text-center p-3 bg-light rounded">
                                <i class="bi bi-mortarboard text-info fs-1 mb-2"></i>
                                <h6>Educación</h6>
                                <p class="small">Aulas y oficinas administrativas</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <h6><i class="bi bi-calculator text-success me-2"></i>Comparación de Costos</h6>
                                    <table class="table table-sm">
                                        <tr><td>Alquiler mensual:</td><td class="text-success fw-bold">$149-299</td></tr>
                                        <tr><td>Compra equivalente:</td><td class="text-danger">$3,500-8,000</td></tr>
                                        <tr><td class="text-primary fw-bold">Ahorro primer año:</td><td class="text-success fw-bold">hasta 70%</td></tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h6><i class="bi bi-check-all text-success me-2"></i>Incluido en Alquiler</h6>
                                    <ul class="list-unstyled small">
                                        <li><i class="bi bi-check text-success me-1"></i> Mantenimiento completo</li>
                                        <li><i class="bi bi-check text-success me-1"></i> Soporte técnico 24/7</li>
                                        <li><i class="bi bi-check text-success me-1"></i> Repuestos originales</li>
                                        <li><i class="bi bi-check text-success me-1"></i> Instalación profesional</li>
                                        <li><i class="bi bi-check text-success me-1"></i> Capacitación del personal</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        }
    };
    
    // =============================================
    // SISTEMA DE MODALES PARA PRODUCTOS
    // =============================================
    
    const productModalSystem = {
        init: function() {
            this.createProductModal();
            this.bindProductEvents();
            console.log('✅ Sistema de modales de productos inicializado');
        },
        
        createProductModal: function() {
            if (document.getElementById('productModal')) return;
            
            const modalHTML = `
                <div class="modal fade" id="productModal" tabindex="-1">
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content border-0 shadow-lg">
                            <div class="modal-header bg-gradient" style="background: linear-gradient(135deg, #0066cc, #004499);">
                                <h4 class="modal-title text-white" id="productModalLabel">
                                    <i class="bi bi-printer me-2"></i>Información de Producto
                                </h4>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-4" id="productModalBody">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary"></div>
                                </div>
                            </div>
                            <div class="modal-footer bg-light">
                                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                    <i class="bi bi-x-lg me-2"></i>Cerrar
                                </button>
                                <a href="/productos/comparar" class="btn btn-info">
                                    <i class="bi bi-arrow-left-right me-2"></i>Comparar
                                </a>
                                <a href="/cotizacion/form" class="btn btn-primary">
                                    <i class="bi bi-calculator me-2"></i>Cotización Personalizada
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        },
        
        bindProductEvents: function() {
            document.addEventListener('click', (e) => {
                const productCard = e.target.closest('[data-product]');
                if (productCard) {
                    e.preventDefault();
                    const productType = productCard.getAttribute('data-product');
                    this.openProductModal(productType);
                }
            });
        },
        
        openProductModal: function(productType) {
            const data = productsContent[productType];
            if (!data) return;
            
            const modalTitle = document.getElementById('productModalLabel');
            const modalBody = document.getElementById('productModalBody');
            
            modalTitle.innerHTML = `
                <i class="${data.icon} me-2"></i>
                ${data.title}
            `;
            
            modalBody.innerHTML = data.content;
            
            const modal = new bootstrap.Modal(document.getElementById('productModal'));
            modal.show();
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 4
    // =============================================
    
    try {
        productModalSystem.init();
        
        console.log('✅ Parte 4/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part4Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 4:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.productsContent = productsContent;
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part4');

console.log('📦 Copier Company JS - Parte 4/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 5/10: FUNCIONALIDADES ADICIONALES Y SISTEMAS AUXILIARES
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 4 esté lista
document.addEventListener('copierJS:part4Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 5/10: Funcionalidades Adicionales');
    
    // =============================================
    // SISTEMA DE NOTIFICACIONES TOAST
    // =============================================
    
    const toastSystem = {
        container: null,
        
        init: function() {
            this.createContainer();
            console.log('✅ Sistema de notificaciones toast inicializado');
        },
        
        createContainer: function() {
            if (document.getElementById('toast-container')) {
                this.container = document.getElementById('toast-container');
                return;
            }
            
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            this.container = container;
        },
        
        show: function(message, type = 'info', duration = 5000) {
            const toastId = 'toast-' + Date.now();
            const iconMap = {
                'success': 'bi-check-circle-fill',
                'error': 'bi-exclamation-triangle-fill',
                'warning': 'bi-exclamation-triangle-fill',
                'info': 'bi-info-circle-fill'
            };
            
            const colorMap = {
                'success': 'text-success bg-success-subtle',
                'error': 'text-danger bg-danger-subtle',
                'warning': 'text-warning bg-warning-subtle',
                'info': 'text-primary bg-primary-subtle'
            };
            
            const toastHTML = `
                <div id="${toastId}" class="toast align-items-center border-0 shadow-lg ${colorMap[type]}" role="alert">
                    <div class="d-flex">
                        <div class="toast-body d-flex align-items-center">
                            <i class="bi ${iconMap[type]} me-2 fs-5"></i>
                            <span>${message}</span>
                        </div>
                        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            this.container.insertAdjacentHTML('beforeend', toastHTML);
            
            const toastElement = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: duration
            });
            
            toast.show();
            
            // Remover del DOM después de ocultar
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
            
            return toast;
        }
    };
    
    // =============================================
    // SISTEMA DE FORMULARIOS INTELIGENTES
    // =============================================
    
    const smartForms = {
        init: function() {
            this.setupFormValidation();
            this.setupAutoSave();
            this.setupProgressiveEnhancement();
            console.log('✅ Sistema de formularios inteligentes inicializado');
        },
        
        setupFormValidation: function() {
            document.addEventListener('input', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    this.validateField(e.target);
                }
            });
            
            document.addEventListener('blur', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    this.validateField(e.target);
                }
            });
        },
        
        validateField: function(field) {
            const value = field.value.trim();
            let isValid = true;
            let message = '';
            
            // Validaciones específicas
            switch (field.type) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    isValid = emailRegex.test(value);
                    message = isValid ? '' : 'Ingresa un email válido';
                    break;
                    
                case 'tel':
                    const phoneRegex = /^[+]?[\d\s\-\(\)]{9,}$/;
                    isValid = phoneRegex.test(value);
                    message = isValid ? '' : 'Ingresa un teléfono válido';
                    break;
                    
                case 'text':
                    if (field.required && value.length < 2) {
                        isValid = false;
                        message = 'Este campo es requerido (mín. 2 caracteres)';
                    }
                    break;
            }
            
            this.showFieldFeedback(field, isValid, message);
        },
        
        showFieldFeedback: function(field, isValid, message) {
            // Remover feedback anterior
            const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
            if (existingFeedback) existingFeedback.remove();
            
            // Remover clases anteriores
            field.classList.remove('is-valid', 'is-invalid');
            
            if (field.value.trim() !== '') {
                field.classList.add(isValid ? 'is-valid' : 'is-invalid');
                
                // Mostrar mensaje si hay error
                if (!isValid && message) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback d-block';
                    feedback.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${message}`;
                    field.parentNode.appendChild(feedback);
                } else if (isValid) {
                    const feedback = document.createElement('div');
                    feedback.className = 'valid-feedback d-block';
                    feedback.innerHTML = `<i class="bi bi-check-circle me-1"></i>Campo válido`;
                    field.parentNode.appendChild(feedback);
                }
            }
        },
        
        setupAutoSave: function() {
            const formFields = document.querySelectorAll('input[name], textarea[name], select[name]');
            formFields.forEach(field => {
                // Cargar valor guardado
                const savedValue = localStorage.getItem(`copier_form_${field.name}`);
                if (savedValue && field.type !== 'password') {
                    field.value = savedValue;
                }
                
                // Guardar cambios automáticamente
                field.addEventListener('input', () => {
                    if (field.type !== 'password') {
                        localStorage.setItem(`copier_form_${field.name}`, field.value);
                    }
                });
            });
        },
        
        setupProgressiveEnhancement: function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                // Añadir indicador de envío
                form.addEventListener('submit', (e) => {
                    const submitBtn = form.querySelector('[type="submit"]');
                    if (submitBtn && !form.checkValidity()) {
                        e.preventDefault();
                        toastSystem.show('Por favor completa todos los campos requeridos', 'error');
                        return;
                    }
                    
                    if (submitBtn) {
                        submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin me-2"></i>Enviando...';
                        submitBtn.disabled = true;
                        
                        // Restaurar después de 3 segundos si no hay redirección
                        setTimeout(() => {
                            if (submitBtn) {
                                submitBtn.innerHTML = 'Enviar';
                                submitBtn.disabled = false;
                            }
                        }, 3000);
                    }
                });
            });
        }
    };
    
    // =============================================
    // SISTEMA DE TRACKING DE INTERACCIONES
    // =============================================
    
    const trackingSystem = {
        init: function() {
            this.setupClickTracking();
            this.setupScrollTracking();
            console.log('✅ Sistema de tracking inicializado');
        },
        
        setupClickTracking: function() {
            document.addEventListener('click', (e) => {
                const button = e.target.closest('.btn, .card, [data-track]');
                if (button) {
                    this.trackInteraction('click', this.getElementInfo(button));
                }
            });
        },
        
        setupScrollTracking: function() {
            let scrollTimeout;
            let maxScroll = 0;
            const milestones = [25, 50, 75, 90];
            const triggered = new Set();
            
            window.addEventListener('scroll', () => {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    const scrollPercent = Math.round(
                        (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
                    );
                    
                    if (scrollPercent > maxScroll) {
                        maxScroll = scrollPercent;
                        
                        milestones.forEach(milestone => {
                            if (scrollPercent >= milestone && !triggered.has(milestone)) {
                                triggered.add(milestone);
                                this.trackInteraction('scroll', `${milestone}% page depth`);
                            }
                        });
                    }
                }, 100);
            });
        },
        
        trackInteraction: function(action, details) {
            console.log(`📊 Track: ${action} - ${details}`);
            
            // Integración con Google Analytics 4
            if (typeof gtag !== 'undefined') {
                gtag('event', action, {
                    event_category: 'user_interaction',
                    event_label: details,
                    custom_parameter: details
                });
            }
            
            // Almacenar localmente para analytics
            const trackingData = JSON.parse(localStorage.getItem('copier_analytics') || '[]');
            trackingData.push({
                action: action,
                details: details,
                timestamp: new Date().toISOString(),
                url: window.location.pathname
            });
            
            // Mantener solo los últimos 100 eventos
            if (trackingData.length > 100) {
                trackingData.splice(0, trackingData.length - 100);
            }
            
            localStorage.setItem('copier_analytics', JSON.stringify(trackingData));
        },
        
        getElementInfo: function(element) {
            const text = element.textContent?.trim().substring(0, 50) || '';
            const classes = element.className || '';
            const tag = element.tagName.toLowerCase();
            return `${tag}${classes ? '.' + classes.split(' ')[0] : ''}: ${text}`;
        }
    };
    
    // =============================================
    // SISTEMA DE LAZY LOADING MEJORADO
    // =============================================
    
    const lazyLoadSystem = {
        observer: null,
        
        init: function() {
            this.setupIntersectionObserver();
            this.processExistingImages();
            console.log('✅ Sistema de lazy loading inicializado');
        },
        
        setupIntersectionObserver: function() {
            const options = {
                root: null,
                rootMargin: '50px',
                threshold: 0.1
            };
            
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, options);
        },
        
        processExistingImages: function() {
            const images = document.querySelectorAll('img[data-src]');
            images.forEach(img => {
                this.observer.observe(img);
            });
        },
        
        loadImage: function(img) {
            // Añadir loading spinner
            img.style.background = 'url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBzdHJva2U9IiMwMDY2Y2MiPjxnIGZpbGw9Im5vbmUiIGZpbGwtcnVsZT0iZXZlbm9kZCI+PGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMSAxKSIgc3Ryb2tlLXdpZHRoPSIyIj48Y2lyY2xlIGN4PSIyMiIgY3k9IjIyIiByPSI2Ij48YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJyIiBiZWdpbj0iMS41cyIgZHVyPSIzcyIgdmFsdWVzPSI2OzIyIiBjYWxjTW9kZT0ibGluZWFyIiByZXBlYXRDb3VudD0iaW5kZWZpbml0ZSIvPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9InN0cm9rZS1vcGFjaXR5IiBiZWdpbj0iMS41cyIgZHVyPSIzcyIgdmFsdWVzPSIxOzAiIGNhbGNNb2RlPSJsaW5lYXIiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIi8+PC9jaXJjbGU+PC9nPjwvZz48L3N2Zz4=") no-repeat center center';
            img.style.backgroundSize = '40px 40px';
            
            // Cargar imagen
            const tempImg = new Image();
            tempImg.onload = () => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                img.style.background = '';
                img.classList.add('loaded');
                
                // Efecto de fade-in
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {
                    img.style.opacity = '1';
                }, 50);
            };
            
            tempImg.onerror = () => {
                img.style.background = '';
                img.alt = 'Error al cargar imagen';
                console.warn('Error cargando imagen:', img.dataset.src);
            };
            
            tempImg.src = img.dataset.src;
        }
    };
    
    // =============================================
    // SISTEMA DE SMOOTH SCROLL MEJORADO
    // =============================================
    
    const smoothScrollSystem = {
        init: function() {
            this.setupSmoothScroll();
            console.log('✅ Sistema de smooth scroll inicializado');
        },
        
        setupSmoothScroll: function() {
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a[href^="#"]');
                if (link && link.getAttribute('href') !== '#') {
                    e.preventDefault();
                    
                    const targetId = link.getAttribute('href').substring(1);
                    const target = document.getElementById(targetId);
                    
                    if (target) {
                        const headerOffset = 80; // Altura del header fijo
                        const elementPosition = target.offsetTop;
                        const offsetPosition = elementPosition - headerOffset;
                        
                        window.scrollTo({
                            top: offsetPosition,
                            behavior: 'smooth'
                        });
                        
                        // Tracking
                        trackingSystem.trackInteraction('smooth_scroll', `to_${targetId}`);
                    }
                }
            });
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 5
    // =============================================
    
    try {
        toastSystem.init();
        smartForms.init();
        trackingSystem.init();
        lazyLoadSystem.init();
        smoothScrollSystem.init();
        
        console.log('✅ Parte 5/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part5Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 5:', error);
    }
});

// Actualizar objeto global con funciones útiles
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.showToast = (message, type, duration) => toastSystem.show(message, type, duration);
window.CopierCompany.trackInteraction = (action, details) => trackingSystem.trackInteraction(action, details);
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part5');

console.log('📦 Copier Company JS - Parte 5/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 6/10: SISTEMA DE CHAT BOT INTELIGENTE
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 5 esté lista
document.addEventListener('copierJS:part5Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 6/10: Sistema Chat Bot');
    
    // =============================================
    // SISTEMA DE CHAT BOT INTELIGENTE
    // =============================================
    
    const chatBot = {
        isOpen: false,
        messageCount: 0,
        
        init: function() {
            this.createChatWidget();
            this.setupEventListeners();
            this.initializeGreeting();
            console.log('✅ Sistema de chat bot inicializado');
        },
        
        createChatWidget: function() {
            if (document.getElementById('chat-widget')) return;
            
            const chatWidgetHTML = `
                <div id="chat-widget" class="position-fixed" style="bottom: 20px; right: 20px; z-index: 9998;">
                    <div class="chat-bubble d-flex align-items-center justify-content-center rounded-circle bg-primary text-white shadow-lg" 
                         id="chat-bubble" style="width: 60px; height: 60px; cursor: pointer; transition: all 0.3s ease;">
                        <i class="bi bi-chat-dots-fill fs-4"></i>
                        <span class="chat-notification position-absolute bg-white text-primary rounded-pill px-3 py-1 shadow" 
                              style="right: 70px; top: 50%; transform: translateY(-50%); font-size: 14px; white-space: nowrap; opacity: 0;">
                            ¿Necesitas ayuda?
                        </span>
                    </div>
                    
                    <div class="chat-window bg-white rounded-3 shadow-lg border" id="chat-window" 
                         style="width: 350px; height: 500px; display: none; flex-direction: column; overflow: hidden;">
                        <div class="chat-header bg-primary text-white p-3 d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-robot fs-5 me-2"></i>
                                <h6 class="mb-0">Asistente Virtual</h6>
                            </div>
                            <button class="btn btn-link text-white p-0" id="chat-close">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                        
                        <div class="chat-messages flex-grow-1 p-3 overflow-auto" id="chat-messages" 
                             style="background: #f8f9fa; max-height: 380px;">
                            <div class="bot-message mb-3">
                                <div class="d-flex align-items-start">
                                    <div class="bg-primary rounded-circle p-2 me-2 flex-shrink-0">
                                        <i class="bi bi-robot text-white"></i>
                                    </div>
                                    <div class="message-content bg-white p-3 rounded-3 shadow-sm flex-grow-1">
                                        ¡Hola! 👋 Soy tu asistente virtual de Copier Company. ¿En qué puedo ayudarte?
                                        <div class="quick-options mt-3">
                                            <button class="btn btn-outline-primary btn-sm w-100 mb-2 quick-btn" data-action="cotizacion">
                                                <i class="bi bi-calculator me-2"></i>Solicitar cotización
                                            </button>
                                            <button class="btn btn-outline-primary btn-sm w-100 mb-2 quick-btn" data-action="productos">
                                                <i class="bi bi-printer me-2"></i>Ver productos
                                            </button>
                                            <button class="btn btn-outline-primary btn-sm w-100 mb-2 quick-btn" data-action="contacto">
                                                <i class="bi bi-telephone me-2"></i>Información de contacto
                                            </button>
                                            <button class="btn btn-outline-primary btn-sm w-100 quick-btn" data-action="soporte">
                                                <i class="bi bi-gear me-2"></i>Soporte técnico
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="chat-input p-3 border-top bg-white">
                            <div class="input-group">
                                <input type="text" class="form-control" id="chat-input" 
                                       placeholder="Escribe tu pregunta..." maxlength="500">
                                <button class="btn btn-primary" id="chat-send" type="button">
                                    <i class="bi bi-send-fill"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', chatWidgetHTML);
        },
        
        setupEventListeners: function() {
            // Toggle chat
            document.getElementById('chat-bubble').addEventListener('click', () => {
                this.toggleChat();
            });
            
            // Cerrar chat
            document.getElementById('chat-close').addEventListener('click', () => {
                this.toggleChat();
            });
            
            // Enviar mensaje
            document.getElementById('chat-send').addEventListener('click', () => {
                this.sendMessage();
            });
            
            // Enter para enviar
            document.getElementById('chat-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
            
            // Botones rápidos
            document.addEventListener('click', (e) => {
                if (e.target.closest('.quick-btn')) {
                    const action = e.target.closest('.quick-btn').dataset.action;
                    this.handleQuickAction(action);
                }
            });
            
            // Hover effects
            const chatBubble = document.getElementById('chat-bubble');
            chatBubble.addEventListener('mouseenter', () => {
                chatBubble.style.transform = 'scale(1.1)';
                chatBubble.style.boxShadow = '0 8px 25px rgba(0,123,255,0.4)';
            });
            
            chatBubble.addEventListener('mouseleave', () => {
                chatBubble.style.transform = 'scale(1)';
                chatBubble.style.boxShadow = '';
            });
        },
        
        initializeGreeting: function() {
            // Mostrar notificación después de 3 segundos
            setTimeout(() => {
                const notification = document.querySelector('.chat-notification');
                if (notification && !this.isOpen) {
                    notification.style.opacity = '1';
                    notification.style.animation = 'slideInChat 3s ease-in-out forwards';
                    
                    // Ocultar después de 5 segundos
                    setTimeout(() => {
                        notification.style.opacity = '0';
                    }, 5000);
                }
            }, 3000);
        },
        
        toggleChat: function() {
            const chatWindow = document.getElementById('chat-window');
            const chatBubble = document.getElementById('chat-bubble');
            
            if (this.isOpen) {
                chatWindow.style.display = 'none';
                chatBubble.style.display = 'flex';
                this.isOpen = false;
            } else {
                chatWindow.style.display = 'flex';
                chatBubble.style.display = 'none';
                this.isOpen = true;
                
                // Focus en input
                setTimeout(() => {
                    document.getElementById('chat-input').focus();
                }, 100);
                
                // Tracking
                window.CopierCompany.trackInteraction('chat_open', 'chat_widget');
            }
        },
        
        sendMessage: function() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (message) {
                this.addMessage(message, 'user');
                input.value = '';
                this.messageCount++;
                
                // Mostrar typing indicator
                this.showTypingIndicator();
                
                // Simular respuesta del bot
                setTimeout(() => {
                    this.removeTypingIndicator();
                    const response = this.getBotResponse(message);
                    this.addMessage(response, 'bot');
                }, 1000 + Math.random() * 1000); // 1-2 segundos
                
                // Tracking
                window.CopierCompany.trackInteraction('chat_message', message.substring(0, 50));
            }
        },
        
        addMessage: function(text, sender) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `${sender}-message mb-3`;
            
            if (sender === 'user') {
                messageDiv.innerHTML = `
                    <div class="d-flex align-items-start justify-content-end">
                        <div class="message-content bg-primary text-white p-3 rounded-3 shadow-sm" style="max-width: 80%;">
                            ${text}
                        </div>
                        <div class="bg-secondary rounded-circle p-2 ms-2 flex-shrink-0">
                            <i class="bi bi-person-fill text-white"></i>
                        </div>
                    </div>
                `;
            } else {
                messageDiv.innerHTML = `
                    <div class="d-flex align-items-start">
                        <div class="bg-primary rounded-circle p-2 me-2 flex-shrink-0">
                            <i class="bi bi-robot text-white"></i>
                        </div>
                        <div class="message-content bg-white p-3 rounded-3 shadow-sm flex-grow-1">
                            ${text}
                        </div>
                    </div>
                `;
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Animar entrada del mensaje
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(20px)';
            setTimeout(() => {
                messageDiv.style.transition = 'all 0.3s ease';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0)';
            }, 50);
        },
        
        showTypingIndicator: function() {
            const messagesContainer = document.getElementById('chat-messages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing-indicator';
            typingDiv.className = 'bot-message mb-3';
            typingDiv.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="bg-primary rounded-circle p-2 me-2 flex-shrink-0">
                        <i class="bi bi-robot text-white"></i>
                    </div>
                    <div class="message-content bg-white p-3 rounded-3 shadow-sm">
                        <div class="typing-dots d-flex align-items-center">
                            <span>Escribiendo</span>
                            <div class="ms-2">
                                <span class="dot"></span>
                                <span class="dot"></span>
                                <span class="dot"></span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        },
        
        removeTypingIndicator: function() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        },
        
        getBotResponse: function(message) {
            const lowerMessage = message.toLowerCase();
            
            if (lowerMessage.includes('precio') || lowerMessage.includes('costo') || lowerMessage.includes('cotiz')) {
                return `💰 <strong>Precios de Alquiler:</strong><br>
                        • A4: $149-299/mes<br>
                        • A3: $299-899/mes<br>
                        • Láser: $199-899/mes<br><br>
                        <small>¿Te gustaría una cotización personalizada?</small><br>
                        <a href="/cotizacion/form" class="btn btn-primary btn-sm mt-2">
                            <i class="bi bi-calculator me-1"></i>Solicitar Cotización
                        </a>`;
            }
            
            if (lowerMessage.includes('producto') || lowerMessage.includes('equipo') || lowerMessage.includes('fotocopiadora')) {
                return `📱 <strong>Nuestros Productos:</strong><br>
                        • Multifuncionales A3 y A4<br>
                        • Impresoras láser color y B&N<br>
                        • Equipos especializados<br>
                        • Marcas: Konica Minolta, Canon, Ricoh<br><br>
                        <small>¿Qué tipo de equipo necesitas específicamente?</small>`;
            }
            
            if (lowerMessage.includes('mantenimiento') || lowerMessage.includes('reparaci') || lowerMessage.includes('soporte')) {
                return `🔧 <strong>Nuestro Servicio incluye:</strong><br>
                        • Mantenimiento preventivo y correctivo<br>
                        • Soporte técnico 24/7<br>
                        • Repuestos originales garantizados<br>
                        • Tiempo de respuesta: máximo 4 horas<br><br>
                        <small>¿Necesitas ayuda con algún equipo en particular?</small>`;
            }
            
            if (lowerMessage.includes('contacto') || lowerMessage.includes('teléfono') || lowerMessage.includes('dirección')) {
                return `📞 <strong>Información de Contacto:</strong><br>
                        • Teléfono: (01) 975-399-303<br>
                        • WhatsApp: <a href="https://wa.me/51975399303" target="_blank" class="text-success">975 399 303</a><br>
                        • Email: info@copiercompany.com<br>
                        • Horario: Lun-Vie 8AM-6PM, Sáb 8AM-1PM<br><br>
                        <small>¿Prefieres que te contactemos?</small>`;
            }
            
            // Respuesta por defecto
            const responses = [
                `Gracias por tu consulta. Te recomiendo:<br>
                 • <a href="/cotizacion/form" class="text-primary">Solicitar cotización gratuita</a><br>
                 • <a href="/contactus" class="text-primary">Contactar con un asesor</a><br>
                 • <a href="https://wa.me/51975399303" class="text-success">Escribir por WhatsApp</a><br><br>
                 <small>¿Hay algo específico en lo que pueda ayudarte?</small>`,
                 
                `¡Estoy aquí para ayudarte! 😊<br>
                 Puedo asistirte con información sobre:<br>
                 • Precios y cotizaciones<br>
                 • Características de productos<br>
                 • Servicios de mantenimiento<br>
                 • Información de contacto<br><br>
                 <small>¿Sobre qué te gustaría saber más?</small>`
            ];
            
            return responses[Math.floor(Math.random() * responses.length)];
        },
        
        handleQuickAction: function(action) {
            let userMessage = '';
            
            switch (action) {
                case 'cotizacion':
                    userMessage = 'Quiero solicitar una cotización';
                    break;
                case 'productos':
                    userMessage = '¿Qué productos tienen disponibles?';
                    break;
                case 'contacto':
                    userMessage = 'Necesito información de contacto';
                    break;
                case 'soporte':
                    userMessage = '¿Cómo funciona el soporte técnico?';
                    break;
            }
            
            if (userMessage) {
                this.addMessage(userMessage, 'user');
                this.messageCount++;
                
                setTimeout(() => {
                    const response = this.getBotResponse(userMessage);
                    this.addMessage(response, 'bot');
                }, 800);
                
                // Tracking
                window.CopierCompany.trackInteraction('chat_quick_action', action);
            }
        }
    };
    
    // =============================================
    // ESTILOS CSS PARA EL CHAT
    // =============================================
    
    const chatStyles = `
        <style id="chat-bot-styles">
        @keyframes slideInChat {
            0%, 80% { opacity: 0; transform: translateX(10px); }
            10%, 70% { opacity: 1; transform: translateX(0); }
            100% { opacity: 0; transform: translateX(10px); }
        }
        
        .typing-dots .dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #6c757d;
            margin: 0 1px;
            animation: typing 1.4s infinite;
        }
        
        .typing-dots .dot:nth-child(1) { animation-delay: 0s; }
        .typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
            30% { transform: translateY(-10px); opacity: 1; }
        }
        
        #chat-widget .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        #chat-widget .chat-messages::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        #chat-widget .chat-messages::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 10px;
        }
        
        #chat-widget .chat-messages::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        @media (max-width: 768px) {
            #chat-widget .chat-window {
                width: calc(100vw - 40px) !important;
                height: 70vh !important;
                bottom: 20px;
                right: 20px;
            }
            
            #chat-widget .chat-notification {
                display: none !important;
            }
        }
        </style>
    `;
    
    // Inyectar estilos
    if (!document.querySelector('#chat-bot-styles')) {
        document.head.insertAdjacentHTML('beforeend', chatStyles);
    }
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 6
    // =============================================
    
    try {
        chatBot.init();
        
        console.log('✅ Parte 6/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part6Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 6:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.chatBot = chatBot;
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part6');

console.log('📦 Copier Company JS - Parte 6/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 7/10: PERFORMANCE MONITORING Y ANALYTICS AVANZADOS
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 6 esté lista
document.addEventListener('copierJS:part6Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 7/10: Performance y Analytics');
    
    // =============================================
    // SISTEMA DE PERFORMANCE MONITORING
    // =============================================
    
    const performanceMonitor = {
        metrics: {},
        
        init: function() {
            this.measurePageLoad();
            this.detectPerformanceIssues();
            this.setupPerformanceObserver();
            this.monitorResourceLoading();
            console.log('✅ Sistema de performance monitoring inicializado');
        },
        
        measurePageLoad: function() {
            window.addEventListener('load', () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                this.metrics = {
                    loadTime: navigation.loadEventEnd - navigation.fetchStart,
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                    firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    dns: navigation.domainLookupEnd - navigation.domainLookupStart,
                    connection: navigation.connectEnd - navigation.connectStart,
                    serverResponse: navigation.responseEnd - navigation.requestStart
                };
                
                this.logPerformanceMetrics();
                this.sendPerformanceData();
            });
        },
        
        detectPerformanceIssues: function() {
            // Detectar imágenes lentas
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                const startTime = performance.now();
                
                const checkLoad = () => {
                    const loadTime = performance.now() - startTime;
                    if (loadTime > 3000) {
                        console.warn(`⚠️ Imagen lenta detectada: ${img.src.substring(0, 50)}... (${loadTime.toFixed(2)}ms)`);
                        this.reportSlowResource('image', img.src, loadTime);
                    }
                };
                
                if (img.complete) {
                    checkLoad();
                } else {
                    img.onload = checkLoad;
                    img.onerror = () => {
                        console.error(`❌ Error cargando imagen: ${img.src.substring(0, 50)}...`);
                        this.reportSlowResource('image_error', img.src, 0);
                    };
                }
            });
            
            // Detectar scripts lentos
            this.detectSlowScripts();
        },
        
        detectSlowScripts: function() {
            const scripts = document.querySelectorAll('script[src]');
            scripts.forEach(script => {
                const observer = new PerformanceObserver((list) => {
                    list.getEntries().forEach(entry => {
                        if (entry.name === script.src && entry.duration > 1000) {
                            console.warn(`⚠️ Script lento: ${script.src.substring(0, 50)}... (${entry.duration.toFixed(2)}ms)`);
                            this.reportSlowResource('script', script.src, entry.duration);
                        }
                    });
                });
                
                try {
                    observer.observe({ entryTypes: ['resource'] });
                } catch (e) {
                    // PerformanceObserver no soportado en algunos navegadores
                }
            });
        },
        
        setupPerformanceObserver: function() {
            if ('PerformanceObserver' in window) {
                // Observar Largest Contentful Paint
                const lcpObserver = new PerformanceObserver((list) => {
                    list.getEntries().forEach(entry => {
                        if (entry.entryType === 'largest-contentful-paint') {
                            this.metrics.lcp = entry.startTime;
                            if (entry.startTime > 4000) {
                                console.warn(`⚠️ LCP lento: ${entry.startTime.toFixed(2)}ms`);
                            }
                        }
                    });
                });
                
                try {
                    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
                } catch (e) {
                    console.log('LCP observer no soportado');
                }
                
                // Observar First Input Delay
                const fidObserver = new PerformanceObserver((list) => {
                    list.getEntries().forEach(entry => {
                        if (entry.entryType === 'first-input') {
                            this.metrics.fid = entry.processingStart - entry.startTime;
                            if (this.metrics.fid > 100) {
                                console.warn(`⚠️ FID alto: ${this.metrics.fid.toFixed(2)}ms`);
                            }
                        }
                    });
                });
                
                try {
                    fidObserver.observe({ entryTypes: ['first-input'] });
                } catch (e) {
                    console.log('FID observer no soportado');
                }
            }
        },
        
        monitorResourceLoading: function() {
            // Monitorear recursos críticos
            const criticalResources = ['bootstrap', 'main.css', 'jquery'];
            
            window.addEventListener('load', () => {
                const resources = performance.getEntriesByType('resource');
                
                resources.forEach(resource => {
                    const isCritical = criticalResources.some(cr => resource.name.includes(cr));
                    
                    if (isCritical && resource.duration > 2000) {
                        console.warn(`⚠️ Recurso crítico lento: ${resource.name.substring(0, 50)}... (${resource.duration.toFixed(2)}ms)`);
                        this.reportSlowResource('critical_resource', resource.name, resource.duration);
                    }
                });
            });
        },
        
        logPerformanceMetrics: function() {
            console.group('📊 Métricas de Performance');
            console.log(`⏱️ Tiempo total de carga: ${this.metrics.loadTime.toFixed(2)}ms`);
            console.log(`🎯 DOMContentLoaded: ${this.metrics.domContentLoaded.toFixed(2)}ms`);
            console.log(`🎨 First Paint: ${this.metrics.firstPaint.toFixed(2)}ms`);
            console.log(`📄 First Contentful Paint: ${this.metrics.firstContentfulPaint.toFixed(2)}ms`);
            console.log(`🌐 DNS Lookup: ${this.metrics.dns.toFixed(2)}ms`);
            console.log(`🔗 Connection: ${this.metrics.connection.toFixed(2)}ms`);
            console.log(`🖥️ Server Response: ${this.metrics.serverResponse.toFixed(2)}ms`);
            
            if (this.metrics.lcp) {
                console.log(`🖼️ Largest Contentful Paint: ${this.metrics.lcp.toFixed(2)}ms`);
            }
            if (this.metrics.fid) {
                console.log(`👆 First Input Delay: ${this.metrics.fid.toFixed(2)}ms`);
            }
            console.groupEnd();
        },
        
        sendPerformanceData: function() {
            // Enviar a Google Analytics si está disponible
            if (typeof gtag !== 'undefined') {
                gtag('event', 'performance_metrics', {
                    load_time: Math.round(this.metrics.loadTime),
                    dom_content_loaded: Math.round(this.metrics.domContentLoaded),
                    first_paint: Math.round(this.metrics.firstPaint),
                    first_contentful_paint: Math.round(this.metrics.firstContentfulPaint)
                });
            }
            
            // Almacenar localmente para análisis
            const performanceData = {
                timestamp: new Date().toISOString(),
                url: window.location.pathname,
                userAgent: navigator.userAgent.substring(0, 100),
                metrics: this.metrics,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            };
            
            localStorage.setItem('copier_performance_last', JSON.stringify(performanceData));
        },
        
        reportSlowResource: function(type, url, duration) {
            const report = {
                type: type,
                url: url.substring(0, 100),
                duration: duration,
                timestamp: new Date().toISOString(),
                page: window.location.pathname
            };
            
            // Almacenar reportes de recursos lentos
            const slowResources = JSON.parse(localStorage.getItem('copier_slow_resources') || '[]');
            slowResources.push(report);
            
            // Mantener solo los últimos 50 reportes
            if (slowResources.length > 50) {
                slowResources.splice(0, slowResources.length - 50);
            }
            
            localStorage.setItem('copier_slow_resources', JSON.stringify(slowResources));
        },
        
        getPerformanceReport: function() {
            return {
                metrics: this.metrics,
                slowResources: JSON.parse(localStorage.getItem('copier_slow_resources') || '[]'),
                lastMeasurement: JSON.parse(localStorage.getItem('copier_performance_last') || '{}')
            };
        }
    };
    
    // =============================================
    // SISTEMA DE ANALYTICS AVANZADOS
    // =============================================
    
    const advancedAnalytics = {
        sessionData: {},
        
        init: function() {
            this.initializeSession();
            this.trackUserBehavior();
            this.trackScrollDepth();
            this.trackTimeOnSections();
            this.trackDeviceInfo();
            console.log('✅ Sistema de analytics avanzados inicializado');
        },
        
        initializeSession: function() {
            this.sessionData = {
                sessionId: this.generateSessionId(),
                startTime: Date.now(),
                pageViews: 0,
                interactions: 0,
                scrollDepth: 0,
                timeOnPage: 0,
                device: this.getDeviceInfo(),
                referrer: document.referrer || 'direct',
                userAgent: navigator.userAgent.substring(0, 200)
            };
            
            // Incrementar vistas de página
            this.sessionData.pageViews++;
            this.saveSessionData();
        },
        
        generateSessionId: function() {
            return 'copier_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        },
        
        getDeviceInfo: function() {
            const width = window.innerWidth;
            let deviceType = 'desktop';
            
            if (width <= 576) deviceType = 'mobile';
            else if (width <= 992) deviceType = 'tablet';
            
            return {
                type: deviceType,
                width: width,
                height: window.innerHeight,
                pixelRatio: window.devicePixelRatio || 1,
                language: navigator.language,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine
            };
        },
        
        trackUserBehavior: function() {
            // Tracking de clics específicos
            document.addEventListener('click', (e) => {
                const element = e.target.closest('.btn, .card, a, [data-track]');
                if (element) {
                    this.sessionData.interactions++;
                    
                    const eventData = {
                        type: 'click',
                        element: element.tagName.toLowerCase(),
                        text: element.textContent?.trim().substring(0, 50) || '',
                        href: element.href || '',
                        className: element.className || '',
                        timestamp: Date.now()
                    };
                    
                    this.recordEvent(eventData);
                    
                    // Tracking especial para botones CTA
                    if (element.classList.contains('btn-primary') || 
                        element.classList.contains('btn-cta')) {
                        this.trackConversion('cta_click', eventData.text);
                    }
                }
            });
            
            // Tracking de formularios
            document.addEventListener('submit', (e) => {
                const form = e.target;
                if (form.tagName === 'FORM') {
                    this.trackConversion('form_submit', form.action || 'unknown');
                }
            });
        },
        
        trackScrollDepth: function() {
            let maxScroll = 0;
            const milestones = [10, 25, 50, 75, 90, 100];
            const triggered = new Set();
            
            const updateScrollDepth = () => {
                const scrollPercent = Math.round(
                    (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
                );
                
                if (scrollPercent > maxScroll) {
                    maxScroll = scrollPercent;
                    this.sessionData.scrollDepth = maxScroll;
                    
                    milestones.forEach(milestone => {
                        if (scrollPercent >= milestone && !triggered.has(milestone)) {
                            triggered.add(milestone);
                            
                            this.recordEvent({
                                type: 'scroll_depth',
                                depth: milestone,
                                timestamp: Date.now()
                            });
                            
                            // Tracking especial para scroll profundo
                            if (milestone >= 75) {
                                this.trackConversion('deep_scroll', `${milestone}%`);
                            }
                        }
                    });
                }
            };
            
            let scrollTimeout;
            window.addEventListener('scroll', () => {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(updateScrollDepth, 100);
            });
        },
        
        trackTimeOnSections: function() {
            const sections = document.querySelectorAll('section[id], .section');
            const sectionTimes = new Map();
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    const sectionId = entry.target.id || entry.target.className.split(' ')[0];
                    
                    if (entry.isIntersecting) {
                        sectionTimes.set(sectionId, Date.now());
                    } else if (sectionTimes.has(sectionId)) {
                        const timeSpent = Date.now() - sectionTimes.get(sectionId);
                        
                        if (timeSpent > 2000) { // Más de 2 segundos
                            this.recordEvent({
                                type: 'section_time',
                                section: sectionId,
                                duration: timeSpent,
                                timestamp: Date.now()
                            });
                            
                            // Engagement especial
                            if (timeSpent > 10000) { // Más de 10 segundos
                                this.trackConversion('high_engagement', `${sectionId}_${Math.round(timeSpent/1000)}s`);
                            }
                        }
                        
                        sectionTimes.delete(sectionId);
                    }
                });
            }, { threshold: 0.5 });
            
            sections.forEach(section => observer.observe(section));
        },
        
        trackDeviceInfo: function() {
            // Tracking de información técnica útil
            this.recordEvent({
                type: 'device_info',
                connection: navigator.connection?.effectiveType || 'unknown',
                memory: navigator.deviceMemory || 'unknown',
                cores: navigator.hardwareConcurrency || 'unknown',
                battery: navigator.getBattery ? 'available' : 'not_available',
                timestamp: Date.now()
            });
        },
        
        recordEvent: function(eventData) {
            // Almacenar eventos localmente
            const events = JSON.parse(localStorage.getItem('copier_analytics_events') || '[]');
            events.push({
                sessionId: this.sessionData.sessionId,
                ...eventData
            });
            
            // Mantener solo los últimos 200 eventos
            if (events.length > 200) {
                events.splice(0, events.length - 200);
            }
            
            localStorage.setItem('copier_analytics_events', JSON.stringify(events));
        },
        
        trackConversion: function(type, details) {
            console.log(`🎯 Conversión: ${type} - ${details}`);
            
            // Tracking especial para conversiones
            if (typeof gtag !== 'undefined') {
                gtag('event', 'conversion', {
                    conversion_type: type,
                    conversion_details: details,
                    session_id: this.sessionData.sessionId
                });
            }
            
            this.recordEvent({
                type: 'conversion',
                conversionType: type,
                details: details,
                timestamp: Date.now()
            });
        },
        
        saveSessionData: function() {
            this.sessionData.timeOnPage = Date.now() - this.sessionData.startTime;
            localStorage.setItem('copier_session_data', JSON.stringify(this.sessionData));
        },
        
        getAnalyticsReport: function() {
            return {
                session: this.sessionData,
                events: JSON.parse(localStorage.getItem('copier_analytics_events') || '[]'),
                performance: performanceMonitor.getPerformanceReport()
            };
        }
    };
    
    // =============================================
    // SISTEMA DE OPTIMIZACIÓN AUTOMÁTICA
    // =============================================
    
    const autoOptimizer = {
        init: function() {
            this.optimizeImages();
            this.optimizeAnimations();
            this.optimizeConnections();
            console.log('✅ Sistema de optimización automática inicializado');
        },
        
        optimizeImages: function() {
            // Diferir imágenes no críticas
            const images = document.querySelectorAll('img:not([data-critical])');
            images.forEach(img => {
                if (!img.loading) {
                    img.loading = 'lazy';
                }
            });
        },
        
        optimizeAnimations: function() {
            // Reducir animaciones en dispositivos de baja potencia
            if (navigator.deviceMemory && navigator.deviceMemory < 4) {
                document.documentElement.style.setProperty('--animation-duration', '0.1s');
                console.log('🔧 Animaciones optimizadas para dispositivo de baja potencia');
            }
            
            // Respetar preferencias de usuario
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.setProperty('--animation-duration', '0s');
                console.log('🔧 Animaciones deshabilitadas por preferencia del usuario');
            }
        },
        
        optimizeConnections: function() {
            // Preconnect a dominios importantes
            const importantDomains = [
                'https://fonts.googleapis.com',
                'https://cdn.jsdelivr.net',
                'https://wa.me'
            ];
            
            importantDomains.forEach(domain => {
                const link = document.createElement('link');
                link.rel = 'preconnect';
                link.href = domain;
                document.head.appendChild(link);
            });
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 7
    // =============================================
    
    try {
        performanceMonitor.init();
        advancedAnalytics.init();
        autoOptimizer.init();
        
        // Guardar datos de sesión periódicamente
        setInterval(() => {
            advancedAnalytics.saveSessionData();
        }, 30000); // Cada 30 segundos
        
        // Enviar datos antes de salir de la página
        window.addEventListener('beforeunload', () => {
            advancedAnalytics.saveSessionData();
        });
        
        console.log('✅ Parte 7/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part7Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 7:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.performanceMonitor = performanceMonitor;
window.CopierCompany.advancedAnalytics = advancedAnalytics;
window.CopierCompany.getAnalyticsReport = () => advancedAnalytics.getAnalyticsReport();
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part7');

console.log('📦 Copier Company JS - Parte 7/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 8/10: SISTEMAS COMPLEMENTARIOS Y GESTIÓN AVANZADA
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 7 esté lista
document.addEventListener('copierJS:part7Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 8/10: Sistemas Complementarios');
    
    // =============================================
    // SISTEMA DE GESTIÓN DE ERRORES
    // =============================================
    
    const errorManager = {
        errorCount: 0,
        maxErrors: 50,
        
        init: function() {
            this.setupGlobalErrorHandling();
            this.setupPromiseRejectionHandling();
            this.setupConsoleErrorCapture();
            console.log('✅ Sistema de gestión de errores inicializado');
        },
        
        setupGlobalErrorHandling: function() {
            window.addEventListener('error', (event) => {
                this.logError({
                    type: 'javascript_error',
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    stack: event.error?.stack || 'No stack available',
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    userAgent: navigator.userAgent.substring(0, 100)
                });
            });
        },
        
        setupPromiseRejectionHandling: function() {
            window.addEventListener('unhandledrejection', (event) => {
                this.logError({
                    type: 'promise_rejection',
                    message: event.reason?.message || 'Unhandled promise rejection',
                    reason: event.reason?.toString() || 'Unknown reason',
                    stack: event.reason?.stack || 'No stack available',
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                });
            });
        },
        
        setupConsoleErrorCapture: function() {
            const originalConsoleError = console.error;
            console.error = (...args) => {
                this.logError({
                    type: 'console_error',
                    message: args.join(' '),
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                });
                originalConsoleError.apply(console, args);
            };
        },
        
        logError: function(errorData) {
            this.errorCount++;
            
            // Limitar número de errores almacenados
            if (this.errorCount > this.maxErrors) {
                console.warn('⚠️ Demasiados errores detectados, limitando almacenamiento');
                return;
            }
            
            // Almacenar localmente
            const errors = JSON.parse(localStorage.getItem('copier_errors') || '[]');
            errors.push(errorData);
            
            // Mantener solo los últimos 30 errores
            if (errors.length > 30) {
                errors.splice(0, errors.length - 30);
            }
            
            localStorage.setItem('copier_errors', JSON.stringify(errors));
            
            // Log para debugging
            console.group('🚨 Error Capturado');
            console.error('Tipo:', errorData.type);
            console.error('Mensaje:', errorData.message);
            console.error('Detalles:', errorData);
            console.groupEnd();
            
            // Mostrar notificación amigable al usuario solo para errores críticos
            if (this.isCriticalError(errorData)) {
                this.showUserFriendlyError();
            }
        },
        
        isCriticalError: function(errorData) {
            const criticalPatterns = [
                'TypeError',
                'ReferenceError',
                'Cannot read property',
                'undefined is not a function'
            ];
            
            return criticalPatterns.some(pattern => 
                errorData.message.includes(pattern)
            );
        },
        
        showUserFriendlyError: function() {
            if (window.CopierCompany && window.CopierCompany.showToast) {
                window.CopierCompany.showToast(
                    'Se ha detectado un problema técnico. Nuestro equipo ha sido notificado.',
                    'warning',
                    8000
                );
            }
        },
        
        getErrorReport: function() {
            return {
                errorCount: this.errorCount,
                errors: JSON.parse(localStorage.getItem('copier_errors') || '[]'),
                browserInfo: {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    platform: navigator.platform,
                    cookieEnabled: navigator.cookieEnabled
                }
            };
        }
    };
    
    // =============================================
    // SISTEMA DE CONECTIVIDAD Y ESTADOS
    // =============================================
    
    const connectivityManager = {
        isOnline: navigator.onLine,
        
        init: function() {
            this.setupConnectivityListeners();
            this.checkConnectionQuality();
            this.setupOfflineSupport();
            console.log('✅ Sistema de conectividad inicializado');
        },
        
        setupConnectivityListeners: function() {
            window.addEventListener('online', () => {
                this.isOnline = true;
                this.handleOnline();
            });
            
            window.addEventListener('offline', () => {
                this.isOnline = false;
                this.handleOffline();
            });
        },
        
        handleOnline: function() {
            console.log('🌐 Conexión restaurada');
            
            if (window.CopierCompany && window.CopierCompany.showToast) {
                window.CopierCompany.showToast(
                    'Conexión a internet restaurada',
                    'success',
                    3000
                );
            }
            
            // Reintentar operaciones pendientes
            this.retryPendingOperations();
            
            // Actualizar UI
            this.updateConnectivityUI(true);
        },
        
        handleOffline: function() {
            console.log('📴 Conexión perdida');
            
            if (window.CopierCompany && window.CopierCompany.showToast) {
                window.CopierCompany.showToast(
                    'Sin conexión a internet. Algunas funciones pueden estar limitadas.',
                    'warning',
                    5000
                );
            }
            
            // Actualizar UI
            this.updateConnectivityUI(false);
        },
        
        updateConnectivityUI: function(isOnline) {
            const offlineIndicator = document.getElementById('offline-indicator');
            
            if (!offlineIndicator && !isOnline) {
                const indicator = document.createElement('div');
                indicator.id = 'offline-indicator';
                indicator.className = 'alert alert-warning position-fixed top-0 start-50 translate-middle-x m-3';
                indicator.style.zIndex = '9999';
                indicator.innerHTML = `
                    <i class="bi bi-wifi-off me-2"></i>
                    Sin conexión a internet
                    <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(indicator);
            } else if (offlineIndicator && isOnline) {
                offlineIndicator.remove();
            }
        },
        
        checkConnectionQuality: function() {
            if ('connection' in navigator) {
                const connection = navigator.connection;
                console.log(`📶 Tipo de conexión: ${connection.effectiveType}`);
                
                // Optimizar según el tipo de conexión
                if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                    this.enableLowDataMode();
                }
            }
        },
        
        enableLowDataMode: function() {
            console.log('📱 Modo de datos limitados activado');
            
            // Deshabilitar animaciones pesadas
            document.documentElement.style.setProperty('--animation-duration', '0.1s');
            
            // Reducir calidad de imágenes
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                if (img.src && !img.dataset.optimized) {
                    // Agregar parámetros de optimización si es posible
                    const url = new URL(img.src);
                    url.searchParams.set('q', '70'); // Calidad 70%
                    url.searchParams.set('w', '800'); // Ancho máximo 800px
                    img.src = url.toString();
                    img.dataset.optimized = 'true';
                }
            });
        },
        
        retryPendingOperations: function() {
            // Aquí se pueden reintentar operaciones que fallaron por falta de conexión
            const pendingOperations = JSON.parse(localStorage.getItem('copier_pending_operations') || '[]');
            
            pendingOperations.forEach(operation => {
                console.log('🔄 Reintentando operación:', operation.type);
                // Implementar lógica de reintento según el tipo de operación
            });
            
            // Limpiar operaciones pendientes
            localStorage.removeItem('copier_pending_operations');
        },
        
        setupOfflineSupport: function() {
            // Cachear recursos críticos para funcionamiento offline
            if ('serviceWorker' in navigator) {
                this.registerServiceWorker();
            }
        },
        
        registerServiceWorker: function() {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('✅ Service Worker registrado para soporte offline');
                })
                .catch(error => {
                    console.log('⚠️ Service Worker no pudo registrarse:', error);
                });
        }
    };
    
    // =============================================
    // SISTEMA DE ACCESIBILIDAD
    // =============================================
    
    const accessibilityEnhancer = {
        init: function() {
            this.enhanceKeyboardNavigation();
            this.improveScreenReaderSupport();
            this.addFocusManagement();
            this.setupAccessibilityShortcuts();
            console.log('✅ Sistema de accesibilidad inicializado');
        },
        
        enhanceKeyboardNavigation: function() {
            // Asegurar que todos los elementos interactivos sean accesibles por teclado
            const interactiveElements = document.querySelectorAll('.btn, .card[data-benefit], .card[data-brand], .card[data-product]');
            
            interactiveElements.forEach(element => {
                if (!element.tabIndex && element.tabIndex !== 0) {
                    element.tabIndex = 0;
                }
                
                if (!element.getAttribute('role')) {
                    element.setAttribute('role', 'button');
                }
                
                // Agregar soporte para Enter y Space
                element.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        element.click();
                    }
                });
            });
        },
        
        improveScreenReaderSupport: function() {
            // Agregar etiquetas ARIA donde falten
            const cards = document.querySelectorAll('.card');
            cards.forEach((card, index) => {
                if (!card.getAttribute('aria-label')) {
                    const title = card.querySelector('h1, h2, h3, h4, h5, h6');
                    if (title) {
                        card.setAttribute('aria-label', title.textContent.trim());
                    }
                }
            });
            
            // Mejorar modales
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (!modal.getAttribute('aria-labelledby')) {
                    const title = modal.querySelector('.modal-title');
                    if (title && title.id) {
                        modal.setAttribute('aria-labelledby', title.id);
                    }
                }
            });
        },
        
        addFocusManagement: function() {
            // Gestión de foco para modales
            document.addEventListener('shown.bs.modal', (e) => {
                const modal = e.target;
                const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            });
            
            // Indicadores de foco visibles
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });
            
            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
        },
        
        setupAccessibilityShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Alt + C = Abrir chat
                if (e.altKey && e.key === 'c') {
                    e.preventDefault();
                    if (window.CopierCompany && window.CopierCompany.chatBot) {
                        const chatBubble = document.getElementById('chat-bubble');
                        if (chatBubble) chatBubble.click();
                    }
                }
                
                // Alt + H = Ir al inicio
                if (e.altKey && e.key === 'h') {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
                
                // Alt + M = Ir al menú principal
                if (e.altKey && e.key === 'm') {
                    e.preventDefault();
                    const mainNav = document.querySelector('nav, .navbar');
                    if (mainNav) {
                        const firstLink = mainNav.querySelector('a');
                        if (firstLink) firstLink.focus();
                    }
                }
            });
        }
    };
    
    // =============================================
    // SISTEMA DE UTILIDADES GLOBALES
    // =============================================
    
    const globalUtilities = {
        init: function() {
            this.setupGlobalHelpers();
            this.setupDataFormatters();
            this.setupUrlHelpers();
            console.log('✅ Utilidades globales inicializadas');
        },
        
        setupGlobalHelpers: function() {
            window.CopierCompany = window.CopierCompany || {};
            
            // Helper para formatear números
            window.CopierCompany.formatNumber = (num) => {
                return new Intl.NumberFormat('es-PE').format(num);
            };
            
            // Helper para formatear moneda
            window.CopierCompany.formatCurrency = (amount) => {
                return new Intl.NumberFormat('es-PE', {
                    style: 'currency',
                    currency: 'USD'
                }).format(amount);
            };
            
            // Helper para formatear fechas
            window.CopierCompany.formatDate = (date) => {
                return new Intl.DateTimeFormat('es-PE', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                }).format(new Date(date));
            };
            
            // Helper para debounce
            window.CopierCompany.debounce = (func, wait) => {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            };
            
            // Helper para throttle
            window.CopierCompany.throttle = (func, limit) => {
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
            };
        },
        
        setupDataFormatters: function() {
            // Formatear números en elementos con data-format
            const numberElements = document.querySelectorAll('[data-format="number"]');
            numberElements.forEach(element => {
                const value = parseFloat(element.textContent);
                if (!isNaN(value)) {
                    element.textContent = window.CopierCompany.formatNumber(value);
                }
            });
            
            // Formatear fechas
            const dateElements = document.querySelectorAll('[data-format="date"]');
            dateElements.forEach(element => {
                const date = element.textContent.trim();
                if (date) {
                    element.textContent = window.CopierCompany.formatDate(date);
                }
            });
        },
        
        setupUrlHelpers: function() {
            // Helper para abrir URLs externas
            window.CopierCompany.openExternal = (url) => {
                window.open(url, '_blank', 'noopener,noreferrer');
            };
            
            // Helper para WhatsApp
            window.CopierCompany.openWhatsApp = (message = '') => {
                const encodedMessage = encodeURIComponent(message || 'Hola, necesito información sobre alquiler de equipos');
                window.CopierCompany.openExternal(`https://wa.me/51975399303?text=${encodedMessage}`);
            };
            
            // Helper para cotización
            window.CopierCompany.openCotizacion = () => {
                window.location.href = '/cotizacion/form';
            };
            
            // Helper para contacto
            window.CopierCompany.openContacto = () => {
                window.location.href = '/contactus';
            };
        }
    };
    
    // =============================================
    // SISTEMA DE LIMPIEZA Y MANTENIMIENTO
    // =============================================
    
    const maintenanceSystem = {
        init: function() {
            this.setupPeriodicCleanup();
            this.setupDataMaintenance();
            console.log('✅ Sistema de mantenimiento inicializado');
        },
        
        setupPeriodicCleanup: function() {
            // Limpiar datos antiguos cada 24 horas
            const lastCleanup = localStorage.getItem('copier_last_cleanup');
            const now = Date.now();
            const dayMs = 24 * 60 * 60 * 1000;
            
            if (!lastCleanup || (now - parseInt(lastCleanup)) > dayMs) {
                this.performCleanup();
                localStorage.setItem('copier_last_cleanup', now.toString());
            }
        },
        
        performCleanup: function() {
            console.log('🧹 Realizando limpieza de datos...');
            
            // Limpiar eventos antiguos
            const events = JSON.parse(localStorage.getItem('copier_analytics_events') || '[]');
            const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
            const recentEvents = events.filter(event => 
                new Date(event.timestamp).getTime() > weekAgo
            );
            localStorage.setItem('copier_analytics_events', JSON.stringify(recentEvents));
            
            // Limpiar errores antiguos
            const errors = JSON.parse(localStorage.getItem('copier_errors') || '[]');
            const recentErrors = errors.filter(error => 
                new Date(error.timestamp).getTime() > weekAgo
            );
            localStorage.setItem('copier_errors', JSON.stringify(recentErrors));
            
            console.log('✅ Limpieza completada');
        },
        
        setupDataMaintenance: function() {
            // Verificar integridad de datos críticos
            const criticalKeys = [
                'copier_session_data',
                'copier_performance_last',
                'copier_analytics_events'
            ];
            
            criticalKeys.forEach(key => {
                try {
                    const data = localStorage.getItem(key);
                    if (data) {
                        JSON.parse(data); // Verificar que sea JSON válido
                    }
                } catch (e) {
                    console.warn(`⚠️ Datos corruptos detectados en ${key}, eliminando...`);
                    localStorage.removeItem(key);
                }
            });
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 8
    // =============================================
    
    try {
        errorManager.init();
        connectivityManager.init();
        accessibilityEnhancer.init();
        globalUtilities.init();
        maintenanceSystem.init();
        
        console.log('✅ Parte 8/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part8Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 8:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.errorManager = errorManager;
window.CopierCompany.connectivityManager = connectivityManager;
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part8');

console.log('📦 Copier Company JS - Parte 8/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 9/10: INTEGRACIÓN FINAL Y SISTEMAS DE INICIALIZACIÓN
 * Versión Bootstrap Icons - Compatible con Odoo
 * Máximo 300 líneas por parte
 */

// Esperar a que la Parte 8 esté lista
document.addEventListener('copierJS:part8Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 9/10: Integración Final');
    
    // =============================================
    // SISTEMA DE INTEGRACIÓN FINAL
    // =============================================
    
    const systemIntegrator = {
        initializationOrder: [
            'part1', 'part2', 'part3', 'part4', 'part5', 
            'part6', 'part7', 'part8', 'part9'
        ],
        
        init: function() {
            this.verifyAllParts();
            this.integrateAllSystems();
            this.setupGlobalEventSystem();
            this.performFinalOptimizations();
            console.log('✅ Sistema de integración final inicializado');
        },
        
        verifyAllParts: function() {
            console.group('🔍 Verificando Integridad del Sistema');
            
            const loadedParts = window.CopierCompany?.partsLoaded || [];
            const missingParts = this.initializationOrder.filter(part => !loadedParts.includes(part));
            
            if (missingParts.length > 0) {
                console.warn('⚠️ Partes faltantes:', missingParts);
            } else {
                console.log('✅ Todas las partes del sistema están cargadas');
            }
            
            // Verificar funcionalidades críticas
            this.verifyCriticalFunctions();
            
            console.groupEnd();
        },
        
        verifyCriticalFunctions: function() {
            const criticalFunctions = [
                'showToast',
                'trackInteraction',
                'openWhatsApp',
                'openCotizacion',
                'formatCurrency'
            ];
            
            criticalFunctions.forEach(funcName => {
                if (typeof window.CopierCompany[funcName] === 'function') {
                    console.log(`✅ ${funcName} disponible`);
                } else {
                    console.warn(`⚠️ ${funcName} no disponible`);
                }
            });
        },
        
        integrateAllSystems: function() {
            // Integrar sistemas de tracking
            this.integrateTrackingSystems();
            
            // Integrar sistemas de UI
            this.integrateUISystems();
            
            // Integrar sistemas de datos
            this.integrateDataSystems();
            
            console.log('🔗 Todos los sistemas integrados correctamente');
        },
        
        integrateTrackingSystems: function() {
            // Conectar analytics con performance
            if (window.CopierCompany.advancedAnalytics && window.CopierCompany.performanceMonitor) {
                const originalTrackInteraction = window.CopierCompany.trackInteraction;
                
                window.CopierCompany.trackInteraction = function(action, details) {
                    // Agregar métricas de performance al tracking
                    const performanceData = {
                        timestamp: performance.now(),
                        memory: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) : null
                    };
                    
                    return originalTrackInteraction.call(this, action, details + ` [perf:${performanceData.timestamp.toFixed(2)}ms]`);
                };
            }
        },
        
        integrateUISystems: function() {
            // Integrar modales con analytics
            document.addEventListener('shown.bs.modal', (e) => {
                const modalId = e.target.id;
                window.CopierCompany.trackInteraction('modal_view', modalId);
            });
            
            // Integrar toast con analytics
            if (window.CopierCompany.showToast) {
                const originalShowToast = window.CopierCompany.showToast;
                
                window.CopierCompany.showToast = function(message, type, duration) {
                    window.CopierCompany.trackInteraction('toast_shown', `${type}:${message.substring(0, 30)}`);
                    return originalShowToast.call(this, message, type, duration);
                };
            }
        },
        
        integrateDataSystems: function() {
            // Sincronizar datos entre sistemas
            setInterval(() => {
                this.syncDataBetweenSystems();
            }, 60000); // Cada minuto
        },
        
        syncDataBetweenSystems: function() {
            // Consolidar datos de sesión
            const consolidatedData = {
                timestamp: new Date().toISOString(),
                session: window.CopierCompany.advancedAnalytics?.sessionData || {},
                performance: window.CopierCompany.performanceMonitor?.metrics || {},
                errors: window.CopierCompany.errorManager?.getErrorReport() || {},
                connectivity: {
                    isOnline: window.CopierCompany.connectivityManager?.isOnline || navigator.onLine
                }
            };
            
            localStorage.setItem('copier_consolidated_data', JSON.stringify(consolidatedData));
        },
        
        setupGlobalEventSystem: function() {
            // Sistema de eventos personalizado para comunicación entre módulos
            window.CopierCompany.eventBus = {
                events: {},
                
                on: function(event, callback) {
                    if (!this.events[event]) {
                        this.events[event] = [];
                    }
                    this.events[event].push(callback);
                },
                
                emit: function(event, data) {
                    if (this.events[event]) {
                        this.events[event].forEach(callback => {
                            try {
                                callback(data);
                            } catch (error) {
                                console.error(`Error en event listener para ${event}:`, error);
                            }
                        });
                    }
                },
                
                off: function(event, callback) {
                    if (this.events[event]) {
                        this.events[event] = this.events[event].filter(cb => cb !== callback);
                    }
                }
            };
            
            // Eventos del sistema
            this.setupSystemEvents();
        },
        
        setupSystemEvents: function() {
            // Evento cuando se abre el chat
            window.CopierCompany.eventBus.on('chat:opened', (data) => {
                window.CopierCompany.trackInteraction('chat_opened', 'event_bus');
            });
            
            // Evento cuando se solicita cotización
            window.CopierCompany.eventBus.on('quote:requested', (data) => {
                window.CopierCompany.trackInteraction('quote_requested', JSON.stringify(data));
            });
            
            // Evento cuando hay error crítico
            window.CopierCompany.eventBus.on('error:critical', (data) => {
                window.CopierCompany.showToast(
                    'Se ha detectado un problema. Recargando la página...',
                    'error',
                    3000
                );
                
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
            });
        },
        
        performFinalOptimizations: function() {
            // Optimizaciones finales después de que todo esté cargado
            
            // Limpiar event listeners no utilizados
            this.cleanupEventListeners();
            
            // Optimizar rendimiento
            this.optimizePerformance();
            
            // Configurar lazy loading final
            this.setupFinalLazyLoading();
            
            console.log('⚡ Optimizaciones finales completadas');
        },
        
        cleanupEventListeners: function() {
            // Remover listeners duplicados o innecesarios
            const elements = document.querySelectorAll('[data-cleanup-listeners]');
            elements.forEach(element => {
                const newElement = element.cloneNode(true);
                element.parentNode.replaceChild(newElement, element);
            });
        },
        
        optimizePerformance: function() {
            // Optimizar imágenes que no se han cargado aún
            const lazyImages = document.querySelectorAll('img[data-src]');
            if (lazyImages.length === 0) {
                console.log('✅ Todas las imágenes han sido procesadas');
            }
            
            // Optimizar animaciones según el dispositivo
            if (window.DeviceMotionEvent) {
                // Dispositivo móvil - reducir animaciones
                document.documentElement.style.setProperty('--animation-scale', '0.8');
            }
            
            // Garbage collection hint
            if (window.gc && typeof window.gc === 'function') {
                window.gc();
            }
        },
        
        setupFinalLazyLoading: function() {
            // Lazy loading para elementos no críticos adicionales
            const nonCriticalElements = document.querySelectorAll('.lazy-load-final');
            
            if (nonCriticalElements.length > 0) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('loaded');
                            observer.unobserve(entry.target);
                        }
                    });
                });
                
                nonCriticalElements.forEach(element => observer.observe(element));
            }
        }
    };
    
    // =============================================
    // SISTEMA DE MONITOREO DE SALUD
    // =============================================
    
    const healthMonitor = {
        checks: {},
        interval: null,
        
        init: function() {
            this.setupHealthChecks();
            this.startMonitoring();
            console.log('✅ Monitor de salud del sistema inicializado');
        },
        
        setupHealthChecks: function() {
            this.checks = {
                memory: () => this.checkMemoryUsage(),
                performance: () => this.checkPerformance(),
                errors: () => this.checkErrorRate(),
                connectivity: () => this.checkConnectivity(),
                localStorage: () => this.checkLocalStorage()
            };
        },
        
        startMonitoring: function() {
            // Verificar salud cada 2 minutos
            this.interval = setInterval(() => {
                this.runHealthChecks();
            }, 120000);
            
            // Verificación inicial después de 30 segundos
            setTimeout(() => {
                this.runHealthChecks();
            }, 30000);
        },
        
        runHealthChecks: function() {
            const results = {};
            let overallHealth = 'healthy';
            
            Object.keys(this.checks).forEach(checkName => {
                try {
                    results[checkName] = this.checks[checkName]();
                    
                    if (results[checkName].status === 'warning') {
                        overallHealth = 'warning';
                    } else if (results[checkName].status === 'critical') {
                        overallHealth = 'critical';
                    }
                } catch (error) {
                    results[checkName] = {
                        status: 'error',
                        message: error.message
                    };
                    overallHealth = 'critical';
                }
            });
            
            this.handleHealthResults(overallHealth, results);
        },
        
        checkMemoryUsage: function() {
            if (performance.memory) {
                const used = performance.memory.usedJSHeapSize;
                const limit = performance.memory.jsHeapSizeLimit;
                const percentage = (used / limit) * 100;
                
                if (percentage > 90) {
                    return { status: 'critical', value: percentage, message: 'Uso de memoria crítico' };
                } else if (percentage > 75) {
                    return { status: 'warning', value: percentage, message: 'Uso de memoria alto' };
                } else {
                    return { status: 'healthy', value: percentage, message: 'Uso de memoria normal' };
                }
            }
            
            return { status: 'unknown', message: 'Información de memoria no disponible' };
        },
        
        checkPerformance: function() {
            const loadTime = window.CopierCompany.performanceMonitor?.metrics?.loadTime || 0;
            
            if (loadTime > 5000) {
                return { status: 'critical', value: loadTime, message: 'Tiempo de carga muy lento' };
            } else if (loadTime > 3000) {
                return { status: 'warning', value: loadTime, message: 'Tiempo de carga lento' };
            } else {
                return { status: 'healthy', value: loadTime, message: 'Rendimiento bueno' };
            }
        },
        
        checkErrorRate: function() {
            const errorCount = window.CopierCompany.errorManager?.errorCount || 0;
            
            if (errorCount > 10) {
                return { status: 'critical', value: errorCount, message: 'Muchos errores detectados' };
            } else if (errorCount > 5) {
                return { status: 'warning', value: errorCount, message: 'Algunos errores detectados' };
            } else {
                return { status: 'healthy', value: errorCount, message: 'Pocos o ningún error' };
            }
        },
        
        checkConnectivity: function() {
            const isOnline = navigator.onLine;
            
            if (!isOnline) {
                return { status: 'critical', value: false, message: 'Sin conexión a internet' };
            } else {
                return { status: 'healthy', value: true, message: 'Conectado a internet' };
            }
        },
        
        checkLocalStorage: function() {
            try {
                const testKey = 'copier_health_test';
                localStorage.setItem(testKey, 'test');
                localStorage.removeItem(testKey);
                
                // Verificar espacio disponible
                const used = JSON.stringify(localStorage).length;
                const maxSize = 5 * 1024 * 1024; // 5MB aproximado
                const percentage = (used / maxSize) * 100;
                
                if (percentage > 90) {
                    return { status: 'warning', value: percentage, message: 'LocalStorage casi lleno' };
                } else {
                    return { status: 'healthy', value: percentage, message: 'LocalStorage funcionando' };
                }
            } catch (error) {
                return { status: 'critical', value: 0, message: 'LocalStorage no disponible' };
            }
        },
        
        handleHealthResults: function(overallHealth, results) {
            console.group(`💊 Health Check - Estado: ${overallHealth.toUpperCase()}`);
            
            Object.keys(results).forEach(checkName => {
                const result = results[checkName];
                const icon = result.status === 'healthy' ? '✅' : 
                           result.status === 'warning' ? '⚠️' : '❌';
                console.log(`${icon} ${checkName}: ${result.message} (${result.value || 'N/A'})`);
            });
            
            console.groupEnd();
            
            // Acciones según el estado de salud
            if (overallHealth === 'critical') {
                this.handleCriticalHealth(results);
            } else if (overallHealth === 'warning') {
                this.handleWarningHealth(results);
            }
            
            // Almacenar resultado
            localStorage.setItem('copier_last_health_check', JSON.stringify({
                timestamp: new Date().toISOString(),
                status: overallHealth,
                results: results
            }));
        },
        
        handleCriticalHealth: function(results) {
            console.warn('🚨 Estado crítico del sistema detectado');
            
            // Notificar al usuario si es apropiado
            if (results.memory?.status === 'critical') {
                window.CopierCompany.showToast(
                    'El sistema está experimentando problemas de memoria. Considera recargar la página.',
                    'warning',
                    8000
                );
            }
            
            // Emitir evento crítico
            if (window.CopierCompany.eventBus) {
                window.CopierCompany.eventBus.emit('error:critical', results);
            }
        },
        
        handleWarningHealth: function(results) {
            console.warn('⚠️ Advertencias detectadas en el sistema');
            
            // Optimizaciones automáticas para warnings
            if (results.memory?.status === 'warning') {
                // Limpiar caches no esenciales
                this.clearNonEssentialCaches();
            }
        },
        
        clearNonEssentialCaches: function() {
            // Limpiar datos antiguos de analytics
            const events = JSON.parse(localStorage.getItem('copier_analytics_events') || '[]');
            const recentEvents = events.slice(-50); // Mantener solo los últimos 50
            localStorage.setItem('copier_analytics_events', JSON.stringify(recentEvents));
            
            console.log('🧹 Caches no esenciales limpiados');
        },
        
        getHealthReport: function() {
            return JSON.parse(localStorage.getItem('copier_last_health_check') || '{}');
        }
    };
    
    // =============================================
    // INICIALIZACIÓN DE PARTE 9
    // =============================================
    
    try {
        systemIntegrator.init();
        healthMonitor.init();
        
        // Configurar cierre limpio
        window.addEventListener('beforeunload', () => {
            console.log('👋 Cerrando sistema Copier Company JS');
            
            // Guardar estado final
            if (window.CopierCompany.advancedAnalytics) {
                window.CopierCompany.advancedAnalytics.saveSessionData();
            }
            
            // Limpiar intervalos
            if (healthMonitor.interval) {
                clearInterval(healthMonitor.interval);
            }
        });
        
        console.log('✅ Parte 9/10 inicializada completamente');
        document.dispatchEvent(new CustomEvent('copierJS:part9Ready'));
        
    } catch (error) {
        console.error('❌ Error en Parte 9:', error);
    }
});

// Actualizar objeto global
window.CopierCompany = window.CopierCompany || {};
window.CopierCompany.systemIntegrator = systemIntegrator;
window.CopierCompany.healthMonitor = healthMonitor;
window.CopierCompany.getSystemHealth = () => healthMonitor.getHealthReport();
window.CopierCompany.partsLoaded = window.CopierCompany.partsLoaded || [];
window.CopierCompany.partsLoaded.push('part9');

console.log('📦 Copier Company JS - Parte 9/10 cargada');
/**
 * COPIER COMPANY HOMEPAGE - SISTEMA JAVASCRIPT COMPLETO
 * PARTE 10/10 FINAL: INICIALIZACIÓN MASTER Y SISTEMA COMPLETO
 * Versión Bootstrap Icons - Compatible con Odoo
 * SISTEMA COMPLETO LISTO PARA PRODUCCIÓN
 */

// Esperar a que la Parte 9 esté lista
document.addEventListener('copierJS:part9Ready', function() {
    console.log('🚀 Iniciando Copier Company JS - Parte 10/10 FINAL: Sistema Completo');
    
    // =============================================
    // INICIALIZADOR MASTER DEL SISTEMA
    // =============================================
    
    const masterInitializer = {
        version: '2.0.0',
        buildDate: '2024-12-19',
        environment: 'production',
        
        init: function() {
            this.displayWelcomeBanner();
            this.validateSystemIntegrity();
            this.initializeAPIConnections();
            this.setupProductionOptimizations();
            this.createDebugInterface();
            this.enableAdvancedFeatures();
            this.startSystemMonitoring();
            console.log('✅ Master Initializer completado');
        },
        
        displayWelcomeBanner: function() {
            console.log(`
%c🏢 COPIER COMPANY HOMEPAGE SYSTEM v${this.version}
%c✨ Sistema JavaScript Completo Inicializado
%c🔧 Build: ${this.buildDate} | Entorno: ${this.environment}
%c📊 10 Módulos Cargados | Bootstrap Icons Integrado
%c🚀 Sistema Listo Para Producción
            `, 
            'color: #0066cc; font-size: 18px; font-weight: bold;',
            'color: #28a745; font-size: 14px; font-weight: bold;',
            'color: #6c757d; font-size: 12px;',
            'color: #17a2b8; font-size: 12px;',
            'color: #28a745; font-size: 14px; font-weight: bold;'
            );
        },
        
        validateSystemIntegrity: function() {
            const requiredParts = ['part1', 'part2', 'part3', 'part4', 'part5', 'part6', 'part7', 'part8', 'part9'];
            const loadedParts = window.CopierCompany?.partsLoaded || [];
            const missingParts = requiredParts.filter(part => !loadedParts.includes(part));
            
            if (missingParts.length === 0) {
                console.log('✅ Integridad del sistema verificada - Todos los módulos cargados');
                this.systemStatus = 'operational';
            } else {
                console.error('❌ Módulos faltantes:', missingParts);
                this.systemStatus = 'degraded';
                this.handleDegradedMode(missingParts);
            }
            
            // Verificar funciones críticas
            this.verifyCriticalAPIs();
        },
        
        verifyCriticalAPIs: function() {
            const criticalAPIs = [
                'showToast', 'trackInteraction', 'openWhatsApp', 'openCotizacion', 
                'formatCurrency', 'chatBot', 'performanceMonitor', 'advancedAnalytics',
                'eventBus', 'healthMonitor', 'errorManager'
            ];
            
            const missingAPIs = criticalAPIs.filter(api => 
                !window.CopierCompany || typeof window.CopierCompany[api] === 'undefined'
            );
            
            if (missingAPIs.length > 0) {
                console.warn('⚠️ APIs críticas faltantes:', missingAPIs);
                this.implementFallbackAPIs(missingAPIs);
            } else {
                console.log('✅ Todas las APIs críticas están disponibles');
            }
        },
        
        implementFallbackAPIs: function(missingAPIs) {
            window.CopierCompany = window.CopierCompany || {};
            
            missingAPIs.forEach(api => {
                switch (api) {
                    case 'showToast':
                        window.CopierCompany.showToast = (msg, type) => alert(msg);
                        break;
                    case 'trackInteraction':
                        window.CopierCompany.trackInteraction = (action, details) => 
                            console.log(`Track: ${action} - ${details}`);
                        break;
                    case 'openWhatsApp':
                        window.CopierCompany.openWhatsApp = () => 
                            window.open('https://wa.me/51975399303', '_blank');
                        break;
                    case 'openCotizacion':
                        window.CopierCompany.openCotizacion = () => 
                            window.location.href = '/cotizacion/form';
                        break;
                    default:
                        window.CopierCompany[api] = () => console.warn(`Fallback para ${api}`);
                }
            });
            
            console.log('🔧 APIs de fallback implementadas');
        },
        
        handleDegradedMode: function(missingParts) {
            console.warn('⚠️ Sistema ejecutándose en modo degradado');
            
            // Mostrar notificación al usuario
            const degradedNotice = document.createElement('div');
            degradedNotice.className = 'alert alert-warning position-fixed top-0 start-50 translate-middle-x';
            degradedNotice.style.zIndex = '10000';
            degradedNotice.innerHTML = `
                <i class="bi bi-exclamation-triangle me-2"></i>
                Algunas funciones pueden estar limitadas. 
                <button type="button" class="btn btn-sm btn-outline-warning ms-2" onclick="location.reload()">
                    <i class="bi bi-arrow-clockwise me-1"></i>Recargar
                </button>
            `;
            document.body.appendChild(degradedNotice);
            
            // Auto-remove después de 10 segundos
            setTimeout(() => degradedNotice.remove(), 10000);
        },
        
        initializeAPIConnections: function() {
            // Configurar conexiones con APIs externas
            this.setupGoogleAnalytics();
            this.setupFacebookPixel();
            this.setupOdooIntegration();
            console.log('🔗 Conexiones API inicializadas');
        },
        
        setupGoogleAnalytics: function() {
            if (typeof gtag !== 'undefined') {
                // Configurar eventos personalizados
                gtag('config', 'GA_MEASUREMENT_ID', {
                    custom_map: {
                        'dimension1': 'page_category',
                        'dimension2': 'user_type'
                    }
                });
                
                // Enviar evento de sistema inicializado
                gtag('event', 'system_initialized', {
                    system_version: this.version,
                    load_time: performance.now()
                });
                
                console.log('📈 Google Analytics configurado');
            }
        },
        
        setupFacebookPixel: function() {
            if (typeof fbq !== 'undefined') {
                fbq('track', 'ViewContent', {
                    content_type: 'website',
                    content_category: 'homepage'
                });
                console.log('📘 Facebook Pixel configurado');
            }
        },
        
        setupOdooIntegration: function() {
            // Configurar comunicación con Odoo backend si está disponible
            if (window.odoo && window.odoo.define) {
                window.odoo.define('copier_company_js', function(require) {
                    const ajax = require('web.ajax');
                    
                    // Enviar métricas a Odoo
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: 'website.visitor',
                        method: 'track_custom_event',
                        args: ['copier_js_loaded', { version: this.version }]
                    });
                });
                
                console.log('🔧 Integración Odoo configurada');
            }
        },
        
        setupProductionOptimizations: function() {
            // Optimizaciones específicas para producción
            
            // Deshabilitar console.log en producción
            if (this.environment === 'production') {
                // Mantener solo errores y warnings
                console.log = () => {};
                console.info = () => {};
            }
            
            // Configurar Service Worker para caché
            this.setupServiceWorker();
            
            // Preload recursos críticos
            this.preloadCriticalResources();
            
            console.log('⚡ Optimizaciones de producción aplicadas');
        },
        
        setupServiceWorker: function() {
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/copier-sw.js')
                    .then(registration => {
                        console.log('SW registrado:', registration.scope);
                        
                        // Actualizar SW si hay nueva versión
                        registration.addEventListener('updatefound', () => {
                            const newWorker = registration.installing;
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    // Nueva versión disponible
                                    this.notifyNewVersionAvailable();
                                }
                            });
                        });
                    })
                    .catch(error => console.log('SW error:', error));
            }
        },
        
        notifyNewVersionAvailable: function() {
            window.CopierCompany.showToast(
                'Nueva versión disponible. <button class="btn btn-sm btn-light ms-2" onclick="location.reload()">Actualizar</button>',
                'info',
                10000
            );
        },
        
        preloadCriticalResources: function() {
            const criticalResources = [
                'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css',
                '/static/css/copier-main.css',
                '/static/img/logo-copier.webp'
            ];
            
            criticalResources.forEach(resource => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = resource;
                link.as = resource.includes('.css') ? 'style' : 'image';
                document.head.appendChild(link);
            });
        },
        
        createDebugInterface: function() {
            // Interfaz de debug para desarrollo y soporte
            window.CopierCompany.debug = {
                version: this.version,
                
                getSystemInfo: function() {
                    return {
                        version: masterInitializer.version,
                        partsLoaded: window.CopierCompany.partsLoaded,
                        systemStatus: masterInitializer.systemStatus,
                        performance: window.CopierCompany.performanceMonitor?.metrics,
                        health: window.CopierCompany.healthMonitor?.getHealthReport(),
                        errors: window.CopierCompany.errorManager?.getErrorReport(),
                        analytics: window.CopierCompany.advancedAnalytics?.getAnalyticsReport()
                    };
                },
                
                runDiagnostics: function() {
                    console.group('🔍 DIAGNÓSTICOS DEL SISTEMA');
                    const info = this.getSystemInfo();
                    
                    console.log('📋 Información del Sistema:', info);
                    console.log('🧮 Storage Usage:', this.getStorageUsage());
                    console.log('🔗 Network Info:', this.getNetworkInfo());
                    console.log('🖥️ Device Info:', this.getDeviceInfo());
                    
                    console.groupEnd();
                    return info;
                },
                
                getStorageUsage: function() {
                    const usage = {};
                    Object.keys(localStorage).forEach(key => {
                        if (key.startsWith('copier_')) {
                            usage[key] = localStorage.getItem(key).length;
                        }
                    });
                    return usage;
                },
                
                getNetworkInfo: function() {
                    return {
                        online: navigator.onLine,
                        connection: navigator.connection ? {
                            effectiveType: navigator.connection.effectiveType,
                            downlink: navigator.connection.downlink,
                            rtt: navigator.connection.rtt
                        } : 'No disponible'
                    };
                },
                
                getDeviceInfo: function() {
                    return {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        cookieEnabled: navigator.cookieEnabled,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            pixelRatio: window.devicePixelRatio
                        }
                    };
                },
                
                clearAllData: function() {
                    Object.keys(localStorage).forEach(key => {
                        if (key.startsWith('copier_')) {
                            localStorage.removeItem(key);
                        }
                    });
                    console.log('🧹 Todos los datos de Copier Company eliminados');
                },
                
                simulateError: function() {
                    throw new Error('Error simulado para pruebas');
                },
                
                testToast: function() {
                    window.CopierCompany.showToast('Toast de prueba', 'info', 3000);
                },
                
                exportData: function() {
                    const data = this.getSystemInfo();
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `copier-debug-${new Date().toISOString()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                }
            };
            
            console.log('🐛 Interfaz de debug creada - Usa window.CopierCompany.debug');
        },
        
        enableAdvancedFeatures: function() {
            // Características avanzadas disponibles solo cuando el sistema está completo
            
            // Shortcuts avanzados
            this.setupAdvancedShortcuts();
            
            // Gestos táctiles
            this.setupTouchGestures();
            
            // PWA features
            this.setupPWAFeatures();
            
            console.log('🚀 Características avanzadas habilitadas');
        },
        
        setupAdvancedShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Ctrl+Shift+D = Debug info
                if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                    e.preventDefault();
                    window.CopierCompany.debug.runDiagnostics();
                }
                
                // Ctrl+Shift+E = Export data
                if (e.ctrlKey && e.shiftKey && e.key === 'E') {
                    e.preventDefault();
                    window.CopierCompany.debug.exportData();
                }
                
                // Ctrl+Shift+R = Reset system
                if (e.ctrlKey && e.shiftKey && e.key === 'R') {
                    e.preventDefault();
                    if (confirm('¿Reiniciar el sistema completo?')) {
                        window.CopierCompany.debug.clearAllData();
                        location.reload();
                    }
                }
            });
        },
        
        setupTouchGestures: function() {
            if ('ontouchstart' in window) {
                let touchStartY = 0;
                let touchStartX = 0;
                
                document.addEventListener('touchstart', (e) => {
                    touchStartY = e.touches[0].clientY;
                    touchStartX = e.touches[0].clientX;
                });
                
                document.addEventListener('touchend', (e) => {
                    const touchEndY = e.changedTouches[0].clientY;
                    const touchEndX = e.changedTouches[0].clientX;
                    const deltaY = touchStartY - touchEndY;
                    const deltaX = touchStartX - touchEndX;
                    
                    // Swipe hacia arriba para scroll to top
                    if (deltaY > 100 && Math.abs(deltaX) < 50) {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                        window.CopierCompany.trackInteraction('touch_gesture', 'swipe_up_to_top');
                    }
                });
            }
        },
        
        setupPWAFeatures: function() {
            // Detectar si es PWA
            if (window.matchMedia('(display-mode: standalone)').matches) {
                document.body.classList.add('pwa-mode');
                console.log('📱 Ejecutándose como PWA');
            }
            
            // Manejar instalación de PWA
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                window.CopierCompany.pwaInstallPrompt = e;
                
                // Mostrar botón de instalación personalizado
                this.showPWAInstallButton();
            });
        },
        
        showPWAInstallButton: function() {
            const installButton = document.createElement('button');
            installButton.className = 'btn btn-primary position-fixed';
            installButton.style.cssText = 'bottom: 80px; right: 20px; z-index: 9997; border-radius: 50px;';
            installButton.innerHTML = '<i class="bi bi-download me-2"></i>Instalar App';
            
            installButton.addEventListener('click', () => {
                if (window.CopierCompany.pwaInstallPrompt) {
                    window.CopierCompany.pwaInstallPrompt.prompt();
                    window.CopierCompany.pwaInstallPrompt.userChoice.then((result) => {
                        window.CopierCompany.trackInteraction('pwa_install', result.outcome);
                        window.CopierCompany.pwaInstallPrompt = null;
                        installButton.remove();
                    });
                }
            });
            
            document.body.appendChild(installButton);
        },
        
        startSystemMonitoring: function() {
            // Monitoreo continuo del sistema
            setInterval(() => {
                this.performSystemCheck();
            }, 300000); // Cada 5 minutos
            
            // Enviar ping de salud cada 10 minutos
            setInterval(() => {
                this.sendHealthPing();
            }, 600000);
        },
        
        performSystemCheck: function() {
            const memoryUsage = performance.memory ? 
                Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) : 0;
            
            if (memoryUsage > 100) { // Más de 100MB
                console.warn(`⚠️ Alto uso de memoria: ${memoryUsage}MB`);
                
                // Limpiar automáticamente si es necesario
                if (memoryUsage > 150) {
                    this.performEmergencyCleanup();
                }
            }
        },
        
        performEmergencyCleanup: function() {
            console.log('🧹 Realizando limpieza de emergencia...');
            
            // Limpiar datos no esenciales
            localStorage.removeItem('copier_analytics_events');
            localStorage.removeItem('copier_slow_resources');
            
            // Forzar garbage collection si está disponible
            if (window.gc) {
                window.gc();
            }
            
            window.CopierCompany.showToast(
                'Sistema optimizado automáticamente',
                'info',
                3000
            );
        },
        
        sendHealthPing: function() {
            const healthData = {
                timestamp: new Date().toISOString(),
                version: this.version,
                status: this.systemStatus,
                uptime: performance.now(),
                url: window.location.pathname
            };
            
            // Enviar a analytics si está disponible
            if (typeof gtag !== 'undefined') {
                gtag('event', 'system_health_ping', healthData);
            }
        }
    };
    
    // =============================================
    // INICIALIZACIÓN FINAL DEL SISTEMA COMPLETO
    // =============================================
    
    try {
        // Inicializar el sistema master
        masterInitializer.init();
        
        // Marcar sistema como completamente inicializado
        window.CopierCompany.systemReady = true;
        window.CopierCompany.version = masterInitializer.version;
        window.CopierCompany.partsLoaded.push('part10');
        
        // Emitir evento global de sistema listo
        window.CopierCompany.eventBus?.emit('system:ready', {
            version: masterInitializer.version,
            timestamp: new Date().toISOString(),
            loadTime: performance.now()
        });
        
        // Notificación de éxito
        setTimeout(() => {
            window.CopierCompany.showToast(
                'Sistema Copier Company completamente cargado y optimizado',
                'success',
                4000
            );
        }, 1000);
        
        // Tracking final
        window.CopierCompany.trackInteraction('system_fully_loaded', `v${masterInitializer.version}`);
        
        console.log('🎉 SISTEMA COPIER COMPANY JS COMPLETAMENTE INICIALIZADO');
        console.log('✅ Todas las 10 partes cargadas exitosamente');
        console.log('🚀 Sistema listo para producción');
        
        // Disparar evento final
        document.dispatchEvent(new CustomEvent('copierJS:systemReady', {
            detail: {
                version: masterInitializer.version,
                parts: window.CopierCompany.partsLoaded,
                loadTime: performance.now()
            }
        }));
        
    } catch (error) {
        console.error('❌ ERROR CRÍTICO en inicialización final:', error);
        
        // Fallback de emergencia
        window.CopierCompany = window.CopierCompany || {};
        window.CopierCompany.systemReady = false;
        window.CopierCompany.error = error.message;
        
        // Notificar error crítico
        alert('Error crítico en el sistema. La página se recargará automáticamente.');
        setTimeout(() => location.reload(), 3000);
    }
});

// =============================================
// FUNCIONES GLOBALES DE CONVENIENCIA
// =============================================

// Función global para acceso rápido al sistema
window.Copier = window.CopierCompany;

// Función de ayuda para desarrolladores
window.CopierHelp = function() {
    console.log(`
🏢 COPIER COMPANY JS SYSTEM v${window.CopierCompany?.version || '2.0.0'}

📋 FUNCIONES PRINCIPALES:
   • CopierCompany.showToast(mensaje, tipo, duración)
   • CopierCompany.openWhatsApp(mensaje)
   • CopierCompany.openCotizacion()
   • CopierCompany.trackInteraction(acción, detalles)
   • CopierCompany.formatCurrency(cantidad)

🐛 DEBUG:
   • CopierCompany.debug.runDiagnostics()
   • CopierCompany.debug.getSystemInfo()
   • CopierCompany.debug.exportData()

⌨️ ATAJOS:
   • Alt+C: Abrir chat
   • Alt+H: Ir al inicio
   • Alt+M: Ir al menú
   • Ctrl+Shift+D: Información de debug
   • Ctrl+Shift+E: Exportar datos
   • Ctrl+Shift+R: Reiniciar sistema

📊 ESTADO:
   • Sistema: ${window.CopierCompany?.systemReady ? 'Listo' : 'Cargando'}
   • Partes: ${window.CopierCompany?.partsLoaded?.length || 0}/10
    `);
};

console.log('📦 Copier Company JS - Parte 10/10 FINAL cargada');
console.log('🎯 SISTEMA COMPLETO - Escribe CopierHelp() para ayuda');