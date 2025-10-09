/**
 * ============================================
 * COPIER COMPANY - MODERN HEADERS JAVASCRIPT
 * Archivo: copier_company/static/src/js/header_effects.js
 * ============================================
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Inicializando Headers Modernos de Copier Company...');
    
    // Detectar qué header está activo
    const glassHeader = document.getElementById('modern-glass-header');
    const gradientHeader = document.getElementById('gradient-dynamic-header');
    const minimalHeader = document.getElementById('minimal-elegant-header');
    
    if (glassHeader) {
        initGlassHeader();
    }
    
    if (gradientHeader) {
        initGradientHeader();
    }
    
    if (minimalHeader) {
        initMinimalHeader();
    }
    
    // Funcionalidades comunes para todos los headers
    initCommonFeatures();
});

// ============================================
// HEADER 1: GLASSMORPHISM PRO
// ============================================

function initGlassHeader() {
    console.log('✅ Inicializando Glassmorphism Header');
    
    const navbar = document.querySelector('.glass-nav');
    let lastScroll = 0;
    
    // Efecto scroll con glassmorphism
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Auto-hide al hacer scroll down, show al scroll up
        if (currentScroll > lastScroll && currentScroll > 300) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
    
    // Mega menu con animaciones
    const megaDropdowns = document.querySelectorAll('.mega-dropdown');
    megaDropdowns.forEach(dropdown => {
        const menu = dropdown.querySelector('.mega-menu');
        
        dropdown.addEventListener('mouseenter', function() {
            menu.style.display = 'block';
            setTimeout(() => {
                menu.style.opacity = '1';
                menu.style.transform = 'translateY(0)';
            }, 10);
        });
        
        dropdown.addEventListener('mouseleave', function() {
            menu.style.opacity = '0';
            menu.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                menu.style.display = 'none';
            }, 300);
        });
    });
    
    // Búsqueda inteligente
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            
            if (query.length >= 2) {
                performSearch(query);
            }
        });
        
        // Enter para buscar
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = e.target.value;
                if (query) {
                    window.location.href = `/#productos?search=${encodeURIComponent(query)}`;
                }
            }
        });
    }
    
    // Animación de quick access links
    const quickLinks = document.querySelectorAll('.quick-link');
    quickLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.05)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Analytics para quick access
    quickLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const linkText = this.querySelector('span')?.textContent || 'Quick Link';
            console.log(`📊 Quick Access Click: ${linkText}`);
            
            if (typeof gtag !== 'undefined') {
                gtag('event', 'quick_access_click', {
                    link_text: linkText,
                    header_type: 'glassmorphism'
                });
            }
        });
    });
}

// ============================================
// HEADER 2: GRADIENT DYNAMIC
// ============================================

function initGradientHeader() {
    console.log('✅ Inicializando Gradient Dynamic Header');
    
    const navbar = document.querySelector('#gradient-dynamic-header .navbar');
    
    // Efecto parallax en el scroll
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const gradient = document.querySelector('.animated-gradient-bg');
        
        if (gradient) {
            gradient.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
        
        // Cambiar opacidad del navbar al hacer scroll
        const opacity = Math.min(1, 0.9 + (scrolled / 1000));
        navbar.style.background = `rgba(255, 255, 255, ${opacity * 0.1})`;
    });
    
    // Quick action buttons con efectos especiales
    const quickActions = document.querySelectorAll('.quick-action-btn');
    quickActions.forEach((btn, index) => {
        // Animación de entrada escalonada
        setTimeout(() => {
            btn.style.opacity = '1';
            btn.style.transform = 'translateY(0)';
        }, index * 100);
        
        // Efecto hover mejorado
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.05)';
            
            // Efecto de partículas (opcional)
            createParticles(this);
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
        
        // Click con ripple effect
        btn.addEventListener('click', function(e) {
            createRipple(e, this);
        });
    });
    
    // Estadísticas animadas en stats bar
    animateStatsBar();
    
    // Logo pulse interactivo
    const logo = document.querySelector('.logo-pulse');
    if (logo) {
        logo.addEventListener('mouseenter', function() {
            this.style.animation = 'logoPulse 0.5s ease-in-out';
        });
        
        logo.addEventListener('animationend', function() {
            this.style.animation = 'logoPulse 3s ease-in-out infinite';
        });
    }
}

// ============================================
// HEADER 3: MINIMAL ELEGANT
// ============================================

function initMinimalHeader() {
    console.log('✅ Inicializando Minimal Elegant Header');
    
    const navbar = document.querySelector('#minimal-elegant-header .navbar');
    
    // Efecto scroll sutil
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        
        if (scrolled > 50) {
            navbar.classList.add('scrolled');
            navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.1)';
        } else {
            navbar.classList.remove('scrolled');
            navbar.style.boxShadow = '0 2px 5px rgba(0,0,0,0.05)';
        }
    });
    
    // Hover lift effect mejorado
    const navLinks = document.querySelectorAll('.hover-lift');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = '0 4px 12px rgba(13, 110, 253, 0.2)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Pills flotantes con animación
    const pillLinks = document.querySelectorAll('.pill-link');
    pillLinks.forEach((pill, index) => {
        // Entrada escalonada
        setTimeout(() => {
            pill.style.opacity = '1';
            pill.style.transform = 'scale(1)';
        }, index * 50);
        
        // Hover effect
        pill.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.05)';
            
            // Efecto de "squeeze"
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = 'scale(1.2) rotate(10deg)';
            }
        });
        
        pill.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
    
    // Pill activo con rotación de destacados
    rotateFeaturedPill();
}

// ============================================
// FUNCIONALIDADES COMUNES
// ============================================

function initCommonFeatures() {
    console.log('✅ Inicializando funcionalidades comunes');
    
    // Cerrar dropdowns al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            const dropdowns = document.querySelectorAll('.dropdown-menu.show');
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
    
    // Smooth scroll para enlaces internos
    const internalLinks = document.querySelectorAll('a[href^="/#"]');
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(2);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                // Cerrar menú móvil si está abierto
                const offcanvas = bootstrap.Offcanvas.getInstance(document.querySelector('.offcanvas'));
                if (offcanvas) {
                    offcanvas.hide();
                }
                
                // Scroll suave con offset para el header
                const headerHeight = document.querySelector('header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // WhatsApp click tracking
    const whatsappLinks = document.querySelectorAll('a[href*="wa.me"]');
    whatsappLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('📱 WhatsApp click desde header');
            
            if (typeof gtag !== 'undefined') {
                gtag('event', 'whatsapp_click', {
                    source: 'header',
                    button_location: this.textContent.trim()
                });
            }
        });
    });
    
    // Cotización click tracking
    const quoteLinks = document.querySelectorAll('a[href*="cotizacion"]');
    quoteLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('📝 Cotización click desde header');
            
            if (typeof gtag !== 'undefined') {
                gtag('event', 'quote_request_click', {
                    source: 'header',
                    button_type: this.textContent.trim()
                });
            }
        });
    });
    
    // Teléfono click tracking
    const phoneLinks = document.querySelectorAll('a[href^="tel:"]');
    phoneLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('📞 Teléfono click desde header');
            
            if (typeof gtag !== 'undefined') {
                gtag('event', 'phone_click', {
                    source: 'header',
                    phone_number: this.getAttribute('href').replace('tel:', '')
                });
            }
        });
    });
    
    // Keyboard navigation mejorado
    document.addEventListener('keydown', function(e) {
        // ESC para cerrar modales y offcanvas
        if (e.key === 'Escape') {
            const openOffcanvas = document.querySelector('.offcanvas.show');
            if (openOffcanvas) {
                bootstrap.Offcanvas.getInstance(openOffcanvas)?.hide();
            }
            
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                bootstrap.Modal.getInstance(openModal)?.hide();
            }
        }
        
        // Ctrl/Cmd + K para abrir búsqueda
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchModal = document.getElementById('searchModal');
            if (searchModal) {
                const modal = new bootstrap.Modal(searchModal);
                modal.show();
                
                setTimeout(() => {
                    document.getElementById('globalSearch')?.focus();
                }, 300);
            }
        }
    });
    
    // Detección de dispositivo móvil
    detectMobileDevice();
    
    // Notificación de cookies (si aplica)
    checkCookieConsent();
    
    // Badge de "Nuevo" o "Promoción" dinámico
    addDynamicBadges();
}

// ============================================
// FUNCIONES AUXILIARES
// ============================================

// Búsqueda inteligente
function performSearch(query) {
    console.log(`🔍 Buscando: ${query}`);
    
    // Sugerencias de búsqueda en tiempo real
    const suggestions = [
        { text: 'Multifuncional A3', url: '/#productos' },
        { text: 'Multifuncional A4', url: '/#productos' },
        { text: 'Impresora Láser', url: '/#productos' },
        { text: 'Alquiler', url: '/our-services' },
        { text: 'Soporte Técnico', url: '/our-services' },
        { text: 'Cotización', url: '/cotizacion/form' }
    ];
    
    const matches = suggestions.filter(item => 
        item.text.toLowerCase().includes(query)
    );
    
    // Mostrar sugerencias (puedes implementar un dropdown aquí)
    console.log('Sugerencias:', matches);
    
    return matches;
}

// Crear efecto ripple
function createRipple(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple-effect');
    
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Crear partículas decorativas
function createParticles(element) {
    const colors = ['#0d6efd', '#6610f2', '#ffc107', '#198754'];
    
    for (let i = 0; i < 3; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: 5px;
            height: 5px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
        `;
        
        const rect = element.getBoundingClientRect();
        particle.style.left = (rect.left + rect.width / 2) + 'px';
        particle.style.top = (rect.top + rect.height / 2) + 'px';
        
        document.body.appendChild(particle);
        
        const angle = (Math.PI * 2 * i) / 3;
        const velocity = 50;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        
        let x = 0, y = 0;
        const animate = () => {
            x += vx * 0.016;
            y += vy * 0.016;
            
            particle.style.transform = `translate(${x}px, ${y}px)`;
            particle.style.opacity = 1 - (Math.abs(x) + Math.abs(y)) / 100;
            
            if (particle.style.opacity > 0) {
                requestAnimationFrame(animate);
            } else {
                particle.remove();
            }
        };
        
        animate();
    }
}

// Animar stats bar
function animateStatsBar() {
    const statsBar = document.querySelector('.stats-bar');
    if (!statsBar) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const numbers = statsBar.querySelectorAll('.col-md-3');
                numbers.forEach((num, index) => {
                    setTimeout(() => {
                        num.style.opacity = '1';
                        num.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }
        });
    }, { threshold: 0.5 });
    
    observer.observe(statsBar);
}

// Rotar pill destacado
function rotateFeaturedPill() {
    const pills = document.querySelectorAll('.pill-link');
    if (pills.length === 0) return;
    
    let currentIndex = 0;
    
    setInterval(() => {
        pills.forEach(pill => pill.classList.remove('active'));
        
        currentIndex = (currentIndex + 1) % pills.length;
        pills[currentIndex].classList.add('active');
    }, 5000);
}

// Detectar dispositivo móvil
function detectMobileDevice() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.body.classList.add('mobile-device');
        console.log('📱 Dispositivo móvil detectado');
    } else {
        document.body.classList.add('desktop-device');
        console.log('💻 Dispositivo desktop detectado');
    }
    
    // Ajustes específicos para móvil
    if (isMobile) {
        // Deshabilitar efectos hover en móvil
        const hoverElements = document.querySelectorAll('[class*="hover"]');
        hoverElements.forEach(el => {
            el.classList.add('no-hover-mobile');
        });
    }
}

// Check cookie consent
function checkCookieConsent() {
    const consent = localStorage.getItem('cookie_consent');
    
    if (!consent) {
        // Mostrar banner de cookies después de 2 segundos
        setTimeout(() => {
            showCookieBanner();
        }, 2000);
    }
}

// Mostrar banner de cookies
function showCookieBanner() {
    const banner = document.createElement('div');
    banner.className = 'cookie-banner position-fixed bottom-0 start-0 end-0 bg-dark text-white p-3 shadow-lg';
    banner.style.zIndex = '9999';
    banner.innerHTML = `
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <p class="mb-0">
                        <i class="bi bi-shield-check me-2"></i>
                        Usamos cookies para mejorar tu experiencia. Al continuar navegando, aceptas nuestra 
                        <a href="/privacy-policy" class="text-warning">Política de Privacidad</a>.
                    </p>
                </div>
                <div class="col-md-4 text-end">
                    <button class="btn btn-warning btn-sm me-2" onclick="acceptCookies()">
                        <i class="bi bi-check-circle me-1"></i> Aceptar
                    </button>
                    <button class="btn btn-outline-light btn-sm" onclick="rejectCookies()">
                        Rechazar
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(banner);
    
    // Animar entrada
    setTimeout(() => {
        banner.style.transform = 'translateY(0)';
        banner.style.opacity = '1';
    }, 100);
}

// Aceptar cookies
window.acceptCookies = function() {
    localStorage.setItem('cookie_consent', 'accepted');
    const banner = document.querySelector('.cookie-banner');
    if (banner) {
        banner.style.transform = 'translateY(100%)';
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 300);
    }
    
    console.log('✅ Cookies aceptadas');
    
    if (typeof gtag !== 'undefined') {
        gtag('event', 'cookie_consent', {
            consent_status: 'accepted'
        });
    }
};

// Rechazar cookies
window.rejectCookies = function() {
    localStorage.setItem('cookie_consent', 'rejected');
    const banner = document.querySelector('.cookie-banner');
    if (banner) {
        banner.style.transform = 'translateY(100%)';
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 300);
    }
    
    console.log('❌ Cookies rechazadas');
};

// Agregar badges dinámicos
function addDynamicBadges() {
    // Badge "Nuevo" en productos recientes
    const newItems = document.querySelectorAll('[data-new="true"]');
    newItems.forEach(item => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-success position-absolute top-0 end-0 m-2';
        badge.textContent = 'NUEVO';
        badge.style.zIndex = '10';
        item.style.position = 'relative';
        item.appendChild(badge);
    });
    
    // Badge "Promoción" en ofertas
    const promoItems = document.querySelectorAll('[data-promo="true"]');
    promoItems.forEach(item => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-danger position-absolute top-0 end-0 m-2';
        badge.innerHTML = '<i class="bi bi-star-fill me-1"></i>OFERTA';
        badge.style.zIndex = '10';
        item.style.position = 'relative';
        item.appendChild(badge);
    });
}

// ============================================
// PERFORMANCE MONITORING
// ============================================

// Monitorear performance del header
if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
                console.log(`⚡ Header cargado en: ${entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart}ms`);
            }
        }
    });
    
    observer.observe({ entryTypes: ['navigation'] });
}

// ============================================
// ACCESSIBILITY ENHANCEMENTS
// ============================================

// Skip to main content
const skipLink = document.createElement('a');
skipLink.href = '#main-content';
skipLink.className = 'skip-to-main visually-hidden-focusable btn btn-primary';
skipLink.textContent = 'Saltar al contenido principal';
skipLink.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 10000;
    padding: 0.5rem 1rem;
`;
document.body.insertBefore(skipLink, document.body.firstChild);

// ARIA labels dinámicos
document.querySelectorAll('header a, header button').forEach(element => {
    if (!element.getAttribute('aria-label') && !element.textContent.trim()) {
        const icon = element.querySelector('i');
        if (icon) {
            const iconClass = icon.className;
            if (iconClass.includes('whatsapp')) {
                element.setAttribute('aria-label', 'Contactar por WhatsApp');
            } else if (iconClass.includes('calculator')) {
                element.setAttribute('aria-label', 'Solicitar cotización');
            } else if (iconClass.includes('search')) {
                element.setAttribute('aria-label', 'Buscar');
            } else if (iconClass.includes('phone')) {
                element.setAttribute('aria-label', 'Llamar por teléfono');
            }
        }
    }
});

// ============================================
// ERROR HANDLING
// ============================================

window.addEventListener('error', function(e) {
    if (e.filename && e.filename.includes('header_effects.js')) {
        console.error('❌ Error en header effects:', e.message);
    }
});

// ============================================
// DEBUG MODE
// ============================================

// Activar con: localStorage.setItem('header_debug', 'true')
const debugMode = localStorage.getItem('header_debug') === 'true';

if (debugMode) {
    console.log('%c🔧 DEBUG MODE ACTIVADO', 'background: #222; color: #bada55; font-size: 20px; padding: 10px;');
    
    // Log de todos los eventos del header
    document.querySelector('header')?.addEventListener('click', function(e) {
        console.log('Click en header:', {
            target: e.target,
            tagName: e.target.tagName,
            className: e.target.className,
            textContent: e.target.textContent?.trim().substring(0, 50)
        });
    });
}

// ============================================
// EXPORT PARA USO EXTERNO
// ============================================

window.CopierHeaderEffects = {
    reinit: function() {
        initCommonFeatures();
        console.log('🔄 Header effects reiniciados');
    },
    
    showSearchModal: function() {
        const modal = new bootstrap.Modal(document.getElementById('searchModal'));
        modal.show();
    },
    
    closeAllMenus: function() {
        document.querySelectorAll('.offcanvas.show').forEach(el => {
            bootstrap.Offcanvas.getInstance(el)?.hide();
        });
        
        document.querySelectorAll('.dropdown-menu.show').forEach(el => {
            el.classList.remove('show');
        });
    },
    
    version: '2.0.0'
};

console.log('✅ Header Effects cargado correctamente - v2.0.0');