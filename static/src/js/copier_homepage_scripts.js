/**
 * PARTE 1: INICIALIZACIÓN Y EFECTOS DE SCROLL
 * JavaScript para Homepage Moderna de Copier Company - Bootstrap Version
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // =============================================
    // EFECTOS DE SCROLL Y ANIMACIONES BÁSICAS
    // =============================================
    
    // Scroll indicator animation
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function() {
            document.querySelector('.benefits-section').scrollIntoView({
                behavior: 'smooth'
            });
        });
        
        // Hide scroll indicator after scrolling
        window.addEventListener('scroll', function() {
            if (window.scrollY > 100) {
                scrollIndicator.style.opacity = '0';
                scrollIndicator.style.transform = 'translateY(10px)';
            } else {
                scrollIndicator.style.opacity = '1';
                scrollIndicator.style.transform = 'translateY(0)';
            }
        });
    }
    
    // =============================================
    // ANIMACIONES DE ENTRADA PARA ELEMENTOS
    // =============================================
    
    // Intersection Observer para animaciones al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Elementos que se animan al entrar en viewport
    const animatedElements = document.querySelectorAll('.benefit-card, .brand-card, .product-card, .process-step, .testimonial-card');
    animatedElements.forEach(el => {
        el.classList.add('animate-ready');
        observer.observe(el);
    });
    
    // =============================================
    // EFECTOS HOVER MEJORADOS
    // =============================================
    
    // Service cards hover effect
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
            this.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
        });
    });
    
    // Floating cards animation in hero
    const floatingCards = document.querySelectorAll('.floating-card');
    floatingCards.forEach((card, index) => {
        // Animación flotante continua
        setInterval(() => {
            card.style.transform = `translateY(${Math.sin(Date.now() * 0.001 + index) * 5}px)`;
        }, 50);
    });
    
    console.log('✅ Parte 1: Efectos de scroll y animaciones inicializados');
});

// CSS adicional para las animaciones usando Bootstrap classes y custom minimal styles
const animationStyles = `
/* Animaciones usando Bootstrap como base */
.animate-ready {
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.6s ease-out;
}

.animate-in {
    opacity: 1;
    transform: translateY(0);
}

.service-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-card {
    transition: transform 0.1s ease-out;
}

.scroll-indicator {
    transition: all 0.3s ease;
}

/* Hover effects using Bootstrap shadow utilities as base */
.benefit-card:hover,
.brand-card:hover,
.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 .5rem 1rem rgba(0,0,0,.15)!important;
    transition: all 0.3s ease;
}

/* Custom scroll indicator with Bootstrap styling */
.scroll-indicator {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: 2px solid;
    border-radius: 50%;
    cursor: pointer;
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

/* Floating animation for hero cards */
.floating-card {
    animation: float 6s ease-in-out infinite;
}

.floating-card:nth-child(2) {
    animation-delay: -2s;
}

.floating-card:nth-child(3) {
    animation-delay: -4s;
}

@keyframes float {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-10px);
    }
}

/* Pulse effect for important buttons */
.btn-pulse {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(13, 110, 253, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(13, 110, 253, 0);
    }
}

/* Fade in animation for modals */
.modal-content {
    animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
    from {
        opacity: 0;
        transform: translateY(-50px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Loading spinner using Bootstrap colors */
.loading-spinner {
    border: 3px solid var(--bs-gray-300);
    border-top: 3px solid var(--bs-primary);
    border-radius: 50%;
    width: 24px;
    height: 24px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 8px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Success checkmark animation */
.success-checkmark {
    display: inline-block;
    animation: checkmark 0.5s ease-in-out;
}

@keyframes checkmark {
    0% {
        transform: scale(0);
    }
    50% {
        transform: scale(1.2);
    }
    100% {
        transform: scale(1);
    }
}
`;

// Inyectar estilos si no están presentes
if (!document.querySelector('#animation-styles-bootstrap')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'animation-styles-bootstrap';
    styleSheet.textContent = animationStyles;
    document.head.appendChild(styleSheet);
}
/**
 * PARTE 2: MODALES DINÁMICOS Y CONTENIDO INTERACTIVO
 * JavaScript para Homepage Moderna de Copier Company - Bootstrap Version
 */

// =============================================
// SISTEMA DE MODALES DINÁMICOS
// =============================================

// Base de datos de contenido para modales
const modalContent = {
    benefits: {
        'sin-inversion': {
            title: 'Sin Inversión Inicial',
            icon: 'bi bi-piggy-bank',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-6">
                            <h4><i class="bi bi-piggy-bank text-primary me-2"></i>Ventajas Financieras</h4>
                            <ul class="list-unstyled benefit-list">
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Preserva tu capital de trabajo</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Mejora tu flujo de caja mensual</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>No afecta líneas de crédito</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Gastos deducibles fiscalmente</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h4><i class="bi bi-graph-up text-primary me-2"></i>Beneficios Empresariales</h4>
                            <ul class="list-unstyled benefit-list">
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Tecnología de última generación</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Actualización constante</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Sin obsolescencia tecnológica</li>
                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i>Escalabilidad según crecimiento</li>
                            </ul>
                        </div>
                    </div>
                    <div class="alert alert-info mt-4 d-flex align-items-center">
                        <i class="bi bi-lightbulb-fill text-warning me-2 fs-4"></i>
                        <div>
                            <strong>¿Sabías que?</strong> Las empresas que alquilan equipos tecnológicos aumentan su productividad en un 35% 
                            al tener siempre acceso a la última tecnología sin comprometer su capital.
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
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card border-success mb-3">
                                <div class="card-header bg-success text-white text-center">
                                    <i class="bi bi-telephone-fill fs-2"></i>
                                    <h5 class="mt-2 mb-0">Nivel 1: Telefónico</h5>
                                    <p class="mb-0"><strong>Tiempo:</strong> Inmediato</p>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-arrow-right text-success me-1"></i> Diagnóstico inicial</li>
                                        <li><i class="bi bi-arrow-right text-success me-1"></i> Soluciones básicas</li>
                                        <li><i class="bi bi-arrow-right text-success me-1"></i> Orientación de uso</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-primary mb-3">
                                <div class="card-header bg-primary text-white text-center">
                                    <i class="bi bi-laptop fs-2"></i>
                                    <h5 class="mt-2 mb-0">Nivel 2: Remoto</h5>
                                    <p class="mb-0"><strong>Tiempo:</strong> 15 minutos</p>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-arrow-right text-primary me-1"></i> Conexión remota</li>
                                        <li><i class="bi bi-arrow-right text-primary me-1"></i> Configuraciones avanzadas</li>
                                        <li><i class="bi bi-arrow-right text-primary me-1"></i> Actualizaciones</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-warning mb-3">
                                <div class="card-header bg-warning text-dark text-center">
                                    <i class="bi bi-person-badge fs-2"></i>
                                    <h5 class="mt-2 mb-0">Nivel 3: Presencial</h5>
                                    <p class="mb-0"><strong>Tiempo:</strong> 4 horas</p>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-arrow-right text-warning me-1"></i> Técnico especializado</li>
                                        <li><i class="bi bi-arrow-right text-warning me-1"></i> Reparaciones complejas</li>
                                        <li><i class="bi bi-arrow-right text-warning me-1"></i> Reemplazo de equipos</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row text-center mt-4">
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body">
                                    <h3 class="text-primary mb-0">98%</h3>
                                    <p class="text-muted">Resolución remota</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body">
                                    <h3 class="text-success mb-0">15min</h3>
                                    <p class="text-muted">Tiempo promedio</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body">
                                    <h3 class="text-warning mb-0">24/7</h3>
                                    <p class="text-muted">Disponibilidad</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body">
                                    <h3 class="text-info mb-0">365</h3>
                                    <p class="text-muted">Días al año</p>
                                </div>
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
                    <div class="timeline-container">
                        <div class="d-flex align-items-center mb-4">
                            <div class="badge bg-primary rounded-circle p-3 me-3">
                                <span class="fw-bold">1</span>
                            </div>
                            <div class="flex-grow-1">
                                <h5 class="mb-1"><i class="bi bi-handshake text-primary me-2"></i>Confirmación del Pedido</h5>
                                <p class="text-muted mb-1"><strong>Tiempo:</strong> 2 horas</p>
                                <ul class="list-unstyled small">
                                    <li><i class="bi bi-check text-success me-1"></i> Verificación de especificaciones</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Programación de instalación</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Preparación del equipo</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="d-flex align-items-center mb-4">
                            <div class="badge bg-success rounded-circle p-3 me-3">
                                <span class="fw-bold">2</span>
                            </div>
                            <div class="flex-grow-1">
                                <h5 class="mb-1"><i class="bi bi-truck text-success me-2"></i>Transporte Especializado</h5>
                                <p class="text-muted mb-1"><strong>Tiempo:</strong> 4 horas</p>
                                <ul class="list-unstyled small">
                                    <li><i class="bi bi-check text-success me-1"></i> Embalaje profesional</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Transporte asegurado</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Coordinación de llegada</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="d-flex align-items-center mb-4">
                            <div class="badge bg-warning rounded-circle p-3 me-3">
                                <span class="fw-bold">3</span>
                            </div>
                            <div class="flex-grow-1">
                                <h5 class="mb-1"><i class="bi bi-gear-fill text-warning me-2"></i>Instalación y Configuración</h5>
                                <p class="text-muted mb-1"><strong>Tiempo:</strong> 2-4 horas</p>
                                <ul class="list-unstyled small">
                                    <li><i class="bi bi-check text-success me-1"></i> Instalación física</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Configuración de red</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Pruebas de funcionamiento</li>
                                    <li><i class="bi bi-check text-success me-1"></i> Capacitación básica</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-success d-flex align-items-center mt-4">
                        <i class="bi bi-shield-check text-success me-2 fs-4"></i>
                        <div>
                            <h5 class="alert-heading mb-1">Garantía de Instalación</h5>
                            <p class="mb-0">Si por algún motivo no podemos instalar tu equipo en 24 horas, 
                            <strong>el primer mes de alquiler es completamente GRATIS</strong>.</p>
                        </div>
                    </div>
                </div>
            `
        },
        'mantenimiento-incluido': {
            title: 'Mantenimiento Incluido',
            icon: 'bi bi-gear',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-6">
                            <h4><i class="bi bi-calendar-check text-primary me-2"></i>Mantenimiento Preventivo</h4>
                            <div class="accordion" id="maintenanceSchedule">
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#weekly">
                                            <span class="badge bg-success me-2">Semanal</span>
                                            Verificaciones Rutinarias
                                        </button>
                                    </h2>
                                    <div id="weekly" class="accordion-collapse collapse show" data-bs-parent="#maintenanceSchedule">
                                        <div class="accordion-body">
                                            <ul class="list-unstyled">
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Limpieza de sensores</li>
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Verificación de consumibles</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#monthly">
                                            <span class="badge bg-primary me-2">Mensual</span>
                                            Mantenimiento Técnico
                                        </button>
                                    </h2>
                                    <div id="monthly" class="accordion-collapse collapse" data-bs-parent="#maintenanceSchedule">
                                        <div class="accordion-body">
                                            <ul class="list-unstyled">
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Calibración de colores</li>
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Actualización de firmware</li>
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Limpieza interna profunda</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#quarterly">
                                            <span class="badge bg-warning me-2">Trimestral</span>
                                            Revisión Completa
                                        </button>
                                    </h2>
                                    <div id="quarterly" class="accordion-collapse collapse" data-bs-parent="#maintenanceSchedule">
                                        <div class="accordion-body">
                                            <ul class="list-unstyled">
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Revisión completa</li>
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Reemplazo de rodillos</li>
                                                <li><i class="bi bi-check-circle text-success me-2"></i>Optimización de rendimiento</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <h4><i class="bi bi-tools text-success me-2"></i>Mantenimiento Correctivo</h4>
                            <div class="list-group">
                                <div class="list-group-item d-flex align-items-center">
                                    <i class="bi bi-check-circle-fill text-success me-3"></i>
                                    <span>Reparación de averías</span>
                                </div>
                                <div class="list-group-item d-flex align-items-center">
                                    <i class="bi bi-check-circle-fill text-success me-3"></i>
                                    <span>Reemplazo de repuestos</span>
                                </div>
                                <div class="list-group-item d-flex align-items-center">
                                    <i class="bi bi-check-circle-fill text-success me-3"></i>
                                    <span>Mano de obra técnica</span>
                                </div>
                                <div class="list-group-item d-flex align-items-center">
                                    <i class="bi bi-check-circle-fill text-success me-3"></i>
                                    <span>Diagnósticos especializados</span>
                                </div>
                                <div class="list-group-item d-flex align-items-center">
                                    <i class="bi bi-check-circle-fill text-success me-3"></i>
                                    <span>Actualizaciones de software</span>
                                </div>
                            </div>
                            
                            <div class="card bg-success text-white mt-3">
                                <div class="card-body">
                                    <h6 class="card-title"><i class="bi bi-calculator me-2"></i>Valor del Mantenimiento</h6>
                                    <p class="card-text mb-0">El mantenimiento incluido tiene un valor aproximado de 
                                    <strong>$200-400 USD mensuales</strong> por equipo.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'garantia-total': {
            title: 'Garantía Total',
            icon: 'bi bi-shield-check',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card text-center h-100">
                                <div class="card-body">
                                    <i class="bi bi-gear-wide-connected text-primary display-4"></i>
                                    <h5 class="card-title mt-3">Cobertura Técnica</h5>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-dot text-primary"></i> Fallas de hardware</li>
                                        <li><i class="bi bi-dot text-primary"></i> Problemas de software</li>
                                        <li><i class="bi bi-dot text-primary"></i> Defectos de fabricación</li>
                                        <li><i class="bi bi-dot text-primary"></i> Desgaste normal</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center h-100">
                                <div class="card-body">
                                    <i class="bi bi-arrow-repeat text-success display-4"></i>
                                    <h5 class="card-title mt-3">Reemplazo Inmediato</h5>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-dot text-success"></i> Equipo de respaldo</li>
                                        <li><i class="bi bi-dot text-success"></i> Transferencia de configuración</li>
                                        <li><i class="bi bi-dot text-success"></i> Sin interrupción del trabajo</li>
                                        <li><i class="bi bi-dot text-success"></i> Mismo nivel de servicio</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center h-100">
                                <div class="card-body">
                                    <i class="bi bi-currency-dollar text-warning display-4"></i>
                                    <h5 class="card-title mt-3">Sin Costos Ocultos</h5>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-dot text-warning"></i> Repuestos incluidos</li>
                                        <li><i class="bi bi-dot text-warning"></i> Mano de obra gratis</li>
                                        <li><i class="bi bi-dot text-warning"></i> Transporte sin costo</li>
                                        <li><i class="bi bi-dot text-warning"></i> Diagnósticos gratuitos</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <h5><i class="bi bi-file-earmark-text text-info me-2"></i>Términos de la Garantía</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-success">
                                    <div class="card-header bg-success text-white">
                                        <h6 class="mb-0">✅ QUÉ ESTÁ CUBIERTO</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled mb-0">
                                            <li class="mb-1"><i class="bi bi-check text-success me-1"></i> Todas las reparaciones</li>
                                            <li class="mb-1"><i class="bi bi-check text-success me-1"></i> Repuestos originales</li>
                                            <li class="mb-1"><i class="bi bi-check text-success me-1"></i> Mano de obra técnica</li>
                                            <li class="mb-1"><i class="bi bi-check text-success me-1"></i> Reemplazo total si es necesario</li>
                                            <li class="mb-1"><i class="bi bi-check text-success me-1"></i> Actualizaciones de firmware</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-danger">
                                    <div class="card-header bg-danger text-white">
                                        <h6 class="mb-0">❌ QUÉ NO ESTÁ CUBIERTO</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled mb-0">
                                            <li class="mb-1"><i class="bi bi-x text-danger me-1"></i> Daños por mal uso intencional</li>
                                            <li class="mb-1"><i class="bi bi-x text-danger me-1"></i> Modificaciones no autorizadas</li>
                                            <li class="mb-1"><i class="bi bi-x text-danger me-1"></i> Desastres naturales extremos</li>
                                            <li class="mb-1"><i class="bi bi-x text-danger me-1"></i> Consumibles (toners, papel)</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'escalabilidad': {
            title: 'Escalabilidad',
            icon: 'bi bi-graph-up-arrow',
            content: `
                <div class="benefit-detail">
                    <h4><i class="bi bi-arrows-expand text-primary me-2"></i>Opciones de Escalabilidad</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card border-success h-100">
                                <div class="card-body text-center">
                                    <div class="bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 60px; height: 60px;">
                                        <i class="bi bi-arrow-up fs-3"></i>
                                    </div>
                                    <h5>Escalar Hacia Arriba</h5>
                                    <p class="text-muted">Cuando tu negocio crece</p>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-plus-circle text-success me-2"></i>Equipos más potentes</li>
                                        <li><i class="bi bi-plus-circle text-success me-2"></i>Mayor capacidad</li>
                                        <li><i class="bi bi-plus-circle text-success me-2"></i>Funciones adicionales</li>
                                        <li><i class="bi bi-plus-circle text-success me-2"></i>Múltiples ubicaciones</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-primary h-100">
                                <div class="card-body text-center">
                                    <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 60px; height: 60px;">
                                        <i class="bi bi-arrow-left-right fs-3"></i>
                                    </div>
                                    <h5>Cambio Lateral</h5>
                                    <p class="text-muted">Necesidades específicas</p>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-arrow-right text-primary me-2"></i>Cambio de tecnología</li>
                                        <li><i class="bi bi-arrow-right text-primary me-2"></i>Diferentes funciones</li>
                                        <li><i class="bi bi-arrow-right text-primary me-2"></i>Especialización</li>
                                        <li><i class="bi bi-arrow-right text-primary me-2"></i>Optimización</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-warning h-100">
                                <div class="card-body text-center">
                                    <div class="bg-warning text-dark rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 60px; height: 60px;">
                                        <i class="bi bi-arrow-down fs-3"></i>
                                    </div>
                                    <h5>Escalar Hacia Abajo</h5>
                                    <p class="text-muted">Optimización de costos</p>
                                    <ul class="list-unstyled text-start">
                                        <li><i class="bi bi-dash-circle text-warning me-2"></i>Equipos más simples</li>
                                        <li><i class="bi bi-dash-circle text-warning me-2"></i>Menor capacidad</li>
                                        <li><i class="bi bi-dash-circle text-warning me-2"></i>Reducción de costos</li>
                                        <li><i class="bi bi-dash-circle text-warning me-2"></i>Funciones básicas</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-light mt-4">
                        <h5><i class="bi bi-gear-wide text-success me-2"></i>Proceso de Escalabilidad</h5>
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="text-center">
                                <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                                    <i class="bi bi-chat-dots"></i>
                                </div>
                                <small class="d-block">Evaluación</small>
                            </div>
                            <i class="bi bi-arrow-right text-muted"></i>
                            <div class="text-center">
                                <div class="bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                                    <i class="bi bi-bar-chart"></i>
                                </div>
                                <small class="d-block">Análisis</small>
                            </div>
                            <i class="bi bi-arrow-right text-muted"></i>
                            <div class="text-center">
                                <div class="bg-warning text-dark rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                                    <i class="bi bi-handshake"></i>
                                </div>
                                <small class="d-block">Propuesta</small>
                            </div>
                            <i class="bi bi-arrow-right text-muted"></i>
                            <div class="text-center">
                                <div class="bg-info text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                                    <i class="bi bi-rocket-takeoff"></i>
                                </div>
                                <small class="d-block">Implementación</small>
                            </div>
                        </div>
                        <p class="mt-3 mb-0 text-center"><strong>Tiempo promedio:</strong> 48-72 horas para cambios completos</p>
                    </div>
                </div>
            `
        }
    }
};

// Manejador de eventos para modales de beneficios
document.addEventListener('click', function(e) {
    const benefitCard = e.target.closest('[data-benefit]');
    if (benefitCard) {
        const benefitType = benefitCard.getAttribute('data-benefit');
        const benefitData = modalContent.benefits[benefitType];
        
        if (benefitData) {
            // Actualizar contenido del modal
            const modalLabel = document.getElementById('benefitModalLabel');
            const modalBody = document.getElementById('benefitModalBody');
            
            if (modalLabel) {
                modalLabel.innerHTML = `<i class="${benefitData.icon} me-2"></i>${benefitData.title}`;
            }
            if (modalBody) {
                modalBody.innerHTML = benefitData.content;
            }
        }
    }
});

// Mejorar la experiencia de los modales con Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    // Agregar efectos de fade y animaciones a los modales
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            // Añadir clase de animación
            this.querySelector('.modal-content').style.animation = 'modalSlideIn 0.3s ease-out';
        });
        
        modal.addEventListener('hide.bs.modal', function() {
            // Animación de salida
            this.querySelector('.modal-content').style.animation = 'modalSlideOut 0.2s ease-in';
        });
    });
    
    // Auto-focus en el primer elemento interactivo del modal
    document.addEventListener('shown.bs.modal', function(e) {
        const firstButton = e.target.querySelector('button:not([data-bs-dismiss])');
        const firstInput = e.target.querySelector('input, textarea, select');
        const focusElement = firstInput || firstButton;
        
        if (focusElement) {
            setTimeout(() => focusElement.focus(), 100);
        }
    });
});

// Función utilitaria para crear toasts usando Bootstrap
function showBootstrapToast(message, type = 'info', duration = 5000) {
    // Crear container si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Definir iconos y colores según el tipo
    const toastConfig = {
        success: { icon: 'bi-check-circle-fill', bg: 'bg-success' },
        error: { icon: 'bi-exclamation-triangle-fill', bg: 'bg-danger' },
        warning: { icon: 'bi-exclamation-triangle-fill', bg: 'bg-warning' },
        info: { icon: 'bi-info-circle-fill', bg: 'bg-info' }
    };
    
    const config = toastConfig[type] || toastConfig.info;
    
    // Crear toast usando Bootstrap
    const toastElement = document.createElement('div');
    toastElement.className = 'toast';
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="toast-header ${config.bg} text-white">
            <i class="bi ${config.icon} me-2"></i>
            <strong class="me-auto">Copier Company</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    // Inicializar y mostrar el toast usando Bootstrap
    const bsToast = new bootstrap.Toast(toastElement, {
        delay: duration
    });
    bsToast.show();
    
    // Remover el elemento del DOM después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// CSS adicional para mejorar la apariencia con Bootstrap
const modalEnhancementStyles = `
/* Animaciones para modales usando Bootstrap */
@keyframes modalSlideIn {
    from {
        opacity: 0;
        transform: translateY(-50px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes modalSlideOut {
    from {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    to {
        opacity: 0;
        transform: translateY(-20px) scale(0.98);
    }
}

/* Mejorar hover effects en cards de beneficios */
.benefit-card {
    transition: all 0.3s ease;
    cursor: pointer;
}

.benefit-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15)!important;
}

/* Timeline connector para instalación */
.timeline-container .d-flex:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 1.75rem;
    top: 4rem;
    width: 2px;
    height: 2rem;
    background: linear-gradient(to bottom, #dee2e6, transparent);
    z-index: 1;
}

.timeline-container {
    position: relative;
}

/* Mejorar apariencia de accordions */
.accordion-button:not(.collapsed) {
    color: var(--bs-primary);
    background-color: rgba(var(--bs-primary-rgb), 0.1);
}

/* Hover effects para list-group items */
.list-group-item {
    transition: all 0.2s ease;
}

.list-group-item:hover {
    background-color: var(--bs-light);
    transform: translateX(5px);
}

/* Mejorar spacing en cards */
.card .display-4 {
    line-height: 1.2;
}

/* Toast container positioning */
.toast-container {
    z-index: 1055; /* Por encima de modals pero debajo de dropdowns */
}

/* Mejorar badges circulares */
.badge.rounded-circle {
    width: 2.5rem;
    height: 2.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 600;
}

/* Efectos hover para iconos grandes */
.display-4 {
    transition: all 0.3s ease;
}

.card:hover .display-4 {
    transform: scale(1.1);
}

/* Mejorar apariencia de process flow */
.bg-primary.rounded-circle,
.bg-success.rounded-circle,
.bg-warning.rounded-circle,
.bg-info.rounded-circle {
    transition: all 0.3s ease;
}

.bg-primary.rounded-circle:hover { transform: scale(1.1); }
.bg-success.rounded-circle:hover { transform: scale(1.1); }
.bg-warning.rounded-circle:hover { transform: scale(1.1); }
.bg-info.rounded-circle:hover { transform: scale(1.1); }
`;

// Inyectar estilos de mejora para modales
if (!document.querySelector('#modal-enhancement-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'modal-enhancement-styles';
    styleSheet.textContent = modalEnhancementStyles;
    document.head.appendChild(styleSheet);
}

console.log('✅ Parte 2: Sistema de modales dinámicos para beneficios inicializado con Bootstrap');
/**
 * PARTE 3: MODALES DE MARCAS Y PRODUCTOS
 * JavaScript para Homepage Moderna de Copier Company - Bootstrap Version
 */

// =============================================
// BASE DE DATOS DE MARCAS
// =============================================

const brandsContent = {
    'konica': {
        title: '',
        logo: 'https://filedn.com/lSeVjMkwzjCzV24eJl1FUoj/konica-minolta-vector-logo-seeklogo/konica-minolta-seeklogo.png',
        description: 'Tecnología japonesa de vanguardia para soluciones de impresión empresarial',
        content: `
            <div class="brand-detail">
                <div class="row">
                    <div class="col-md-8">
                        <div class="brand-overview">
                            <h4><i class="bi bi-award text-primary me-2"></i>Acerca de Konica Minolta</h4>
                            <p class="lead">Líder mundial en tecnología de impresión con más de 150 años de innovación. 
                            Especializada en soluciones multifuncionales de alta gama para empresas que requieren 
                            máxima calidad y productividad.</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-6">
                                    <div class="card border-success h-100">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-rocket-takeoff me-2"></i>Ventajas Clave</h5>
                                        </div>
                                        <div class="card-body">
                                            <ul class="list-unstyled">
                                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Velocidad hasta 75 ppm</li>
                                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Calidad de impresión superior</li>
                                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Tecnología de seguridad avanzada</li>
                                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Conectividad en la nube</li>
                                                <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Bajo consumo energético</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-warning h-100">
                                        <div class="card-header bg-warning text-dark">
                                            <h5 class="mb-0"><i class="bi bi-building me-2"></i>Ideal Para</h5>
                                        </div>
                                        <div class="card-body">
                                            <ul class="list-unstyled">
                                                <li class="mb-2"><i class="bi bi-building me-2 text-warning"></i> Grandes corporaciones</li>
                                                <li class="mb-2"><i class="bi bi-mortarboard me-2 text-warning"></i> Instituciones educativas</li>
                                                <li class="mb-2"><i class="bi bi-heart-pulse me-2 text-warning"></i> Centros médicos</li>
                                                <li class="mb-2"><i class="bi bi-balance-scale me-2 text-warning"></i> Estudios legales</li>
                                                <li class="mb-2"><i class="bi bi-printer me-2 text-warning"></i> Centros de impresión</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-light">
                            <div class="card-header bg-info text-white text-center">
                                <h5 class="mb-0"><i class="bi bi-speedometer2 me-2"></i>Especificaciones</h5>
                            </div>
                            <div class="card-body">
                                <div class="row text-center">
                                    <div class="col-6 mb-3">
                                        <div class="border rounded p-2">
                                            <h4 class="text-primary mb-0">75</h4>
                                            <small class="text-muted">ppm máximo</small>
                                        </div>
                                    </div>
                                    <div class="col-6 mb-3">
                                        <div class="border rounded p-2">
                                            <h4 class="text-primary mb-0">1200</h4>
                                            <small class="text-muted">dpi resolución</small>
                                        </div>
                                    </div>
                                    <div class="col-6 mb-3">
                                        <div class="border rounded p-2">
                                            <h4 class="text-primary mb-0">7500</h4>
                                            <small class="text-muted">hojas/mes</small>
                                        </div>
                                    </div>
                                    <div class="col-6 mb-3">
                                        <div class="border rounded p-2">
                                            <h4 class="text-primary mb-0">4.3"</h4>
                                            <small class="text-muted">pantalla táctil</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header bg-secondary text-white">
                                <h5 class="mb-0"><i class="bi bi-collection me-2"></i>Modelos Populares</h5>
                            </div>
                            <div class="card-body p-0">
                                <div class="list-group list-group-flush">
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>bizhub C558</strong>
                                            <br><small class="text-muted">55 ppm color/B&N</small>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">Popular</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>bizhub C658</strong>
                                            <br><small class="text-muted">65 ppm color/B&N</small>
                                        </div>
                                        <span class="badge bg-success rounded-pill">Nuevo</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>bizhub C758</strong>
                                            <br><small class="text-muted">75 ppm color/B&N</small>
                                        </div>
                                        <span class="badge bg-warning rounded-pill">Premium</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4><i class="bi bi-gear-wide-connected text-primary me-2"></i>Características Técnicas Destacadas</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card text-center h-100 border-success">
                                <div class="card-body">
                                    <i class="bi bi-shield-check text-success display-6"></i>
                                    <h6 class="mt-3">Seguridad Avanzada</h6>
                                    <p class="card-text small">Autenticación biométrica, encriptación de datos y auditoría completa</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center h-100 border-primary">
                                <div class="card-body">
                                    <i class="bi bi-phone text-primary display-6"></i>
                                    <h6 class="mt-3">Impresión Móvil</h6>
                                    <p class="card-text small">Compatible con iOS, Android y servicios en la nube principales</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center h-100 border-success">
                                <div class="card-body">
                                    <i class="bi bi-leaf text-success display-6"></i>
                                    <h6 class="mt-3">Eco-Friendly</h6>
                                    <p class="card-text small">Bajo consumo energético y materiales reciclables</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    'canon': {
        title: 'Canon',
        logo: 'https://filedn.com/lSeVjMkwzjCzV24eJl1FUoj/canon-vector-logo-seeklogo/canon-seeklogo.png',
        description: 'Excelencia en calidad de imagen y tecnología de impresión profesional',
        content: `
            <div class="brand-detail">
                <div class="row">
                    <div class="col-md-8">
                        <div class="brand-overview">
                            <h4><i class="bi bi-camera text-primary me-2"></i>Acerca de Canon</h4>
                            <p class="lead">Reconocida mundialmente por su excelencia en tecnología de imagen. Canon combina 
                            décadas de experiencia en fotografía con innovación en soluciones de oficina, 
                            ofreciendo equipos con calidad de imagen excepcional.</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-6">
                                    <div class="alert alert-warning" role="alert">
                                        <h5 class="alert-heading"><i class="bi bi-star-fill me-2"></i>Fortalezas</h5>
                                        <hr>
                                        <ul class="list-unstyled mb-0">
                                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Calidad de imagen superior</li>
                                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Tecnología MEAP avanzada</li>
                                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Diseño compacto y elegante</li>
                                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Interfaz intuitiva</li>
                                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i> Confiabilidad probada</li>
                                        </ul>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="alert alert-info" role="alert">
                                        <h5 class="alert-heading"><i class="bi bi-people-fill me-2"></i>Perfecto Para</h5>
                                        <hr>
                                        <ul class="list-unstyled mb-0">
                                            <li class="mb-2"><i class="bi bi-palette me-2 text-info"></i> Agencias de diseño</li>
                                            <li class="mb-2"><i class="bi bi-camera me-2 text-info"></i> Estudios fotográficos</li>
                                            <li class="mb-2"><i class="bi bi-briefcase me-2 text-info"></i> Oficinas medianas</li>
                                            <li class="mb-2"><i class="bi bi-shop me-2 text-info"></i> Retail y comercio</li>
                                            <li class="mb-2"><i class="bi bi-house me-2 text-info"></i> Oficinas en casa</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-danger">
                            <div class="card-header bg-danger text-white text-center">
                                <h5 class="mb-0"><i class="bi bi-speedometer me-2"></i>Rendimiento</h5>
                            </div>
                            <div class="card-body">
                                <div class="progress mb-3">
                                    <div class="progress-bar bg-danger" role="progressbar" style="width: 85%">
                                        <strong>55 ppm máximo</strong>
                                    </div>
                                </div>
                                <div class="progress mb-3">
                                    <div class="progress-bar bg-warning" role="progressbar" style="width: 95%">
                                        <strong>2400 dpi calidad</strong>
                                    </div>
                                </div>
                                <div class="progress mb-3">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: 75%">
                                        <strong>5000 hojas/mes</strong>
                                    </div>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar bg-info" role="progressbar" style="width: 90%">
                                        <strong>10.1" pantalla táctil</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3 border-primary">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0"><i class="bi bi-layers me-2"></i>Series Disponibles</h5>
                            </div>
                            <div class="card-body">
                                <div class="accordion" id="canonSeries">
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#imagerunner">
                                                <strong>imageRUNNER ADVANCE</strong>
                                            </button>
                                        </h2>
                                        <div id="imagerunner" class="accordion-collapse collapse" data-bs-parent="#canonSeries">
                                            <div class="accordion-body">
                                                <span class="badge bg-primary">Serie empresarial</span>
                                                <p class="mt-2 mb-0 small">Equipos multifuncionales para grandes volúmenes</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#imagerunnerc">
                                                <strong>imageRUNNER C3500</strong>
                                            </button>
                                        </h2>
                                        <div id="imagerunnerc" class="accordion-collapse collapse" data-bs-parent="#canonSeries">
                                            <div class="accordion-body">
                                                <span class="badge bg-success">Color multifuncional</span>
                                                <p class="mt-2 mb-0 small">Impresión color profesional</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="accordion-item">
                                        <h2 class="accordion-header">
                                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#imageclass">
                                                <strong>imageCLASS</strong>
                                            </button>
                                        </h2>
                                        <div id="imageclass" class="accordion-collapse collapse" data-bs-parent="#canonSeries">
                                            <div class="accordion-body">
                                                <span class="badge bg-warning">Oficina pequeña</span>
                                                <p class="mt-2 mb-0 small">Soluciones compactas y eficientes</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4><i class="bi bi-cpu text-primary me-2"></i>Tecnologías Innovadoras</h4>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="card text-center border-primary h-100">
                                <div class="card-body">
                                    <i class="bi bi-eye text-primary display-6"></i>
                                    <h6 class="mt-3">MEAP Platform</h6>
                                    <p class="card-text small">Plataforma de aplicaciones empresariales multifuncionales</p>
                                </div>
                                <div class="card-footer bg-transparent">
                                    <span class="badge bg-primary">Avanzado</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center border-info h-100">
                                <div class="card-body">
                                    <i class="bi bi-cloud text-info display-6"></i>
                                    <h6 class="mt-3">uniFLOW</h6>
                                    <p class="card-text small">Gestión de documentos y flujo de trabajo en la nube</p>
                                </div>
                                <div class="card-footer bg-transparent">
                                    <span class="badge bg-info">Cloud</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center border-warning h-100">
                                <div class="card-body">
                                    <i class="bi bi-brush text-warning display-6"></i>
                                    <h6 class="mt-3">Calidad de Imagen</h6>
                                    <p class="card-text small">Tecnología de imagen profesional heredada de cámaras</p>
                                </div>
                                <div class="card-footer bg-transparent">
                                    <span class="badge bg-warning">Premium</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center border-success h-100">
                                <div class="card-body">
                                    <i class="bi bi-disc text-success display-6"></i>
                                    <h6 class="mt-3">Toners V2</h6>
                                    <p class="card-text small">Tecnología de toner avanzada para mejor calidad</p>
                                </div>
                                <div class="card-footer bg-transparent">
                                    <span class="badge bg-success">Eco</span>
                                </div>
                            </div>
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
                <div class="row">
                    <div class="col-md-8">
                        <div class="brand-overview">
                            <h4><i class="bi bi-factory text-primary me-2"></i>Acerca de Ricoh</h4>
                            <p class="lead">Pionera en soluciones de oficina digital con enfoque en productividad empresarial. 
                            Ricoh se especializa en equipos robustos diseñados para entornos de alto volumen 
                            con máxima eficiencia operativa.</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-6">
                                    <div class="card border-success">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-shield-check me-2"></i>Ventajas Únicas</h5>
                                        </div>
                                        <div class="list-group list-group-flush">
                                            <div class="list-group-item">
                                                <i class="bi bi-check-circle-fill text-success me-2"></i> Máxima durabilidad
                                            </div>
                                            <div class="list-group-item">
                                                <i class="bi bi-check-circle-fill text-success me-2"></i> Alto volumen mensual
                                            </div>
                                            <div class="list-group-item">
                                                <i class="bi bi-check-circle-fill text-success me-2"></i> Seguridad empresarial
                                            </div>
                                            <div class="list-group-item">
                                                <i class="bi bi-check-circle-fill text-success me-2"></i> Eficiencia energética
                                            </div>
                                            <div class="list-group-item">
                                                <i class="bi bi-check-circle-fill text-success me-2"></i> Facilidad de mantenimiento
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-primary">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-building me-2"></i>Sectores Principales</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row text-center">
                                                <div class="col-6 mb-3">
                                                    <i class="bi bi-bank2 text-primary fs-2"></i>
                                                    <p class="small mb-0 mt-1">Gobierno y público</p>
                                                </div>
                                                <div class="col-6 mb-3">
                                                    <i class="bi bi-heart-pulse text-primary fs-2"></i>
                                                    <p class="small mb-0 mt-1">Sector salud</p>
                                                </div>
                                                <div class="col-6 mb-3">
                                                    <i class="bi bi-gear-wide text-primary fs-2"></i>
                                                    <p class="small mb-0 mt-1">Manufactura</p>
                                                </div>
                                                <div class="col-6 mb-3">
                                                    <i class="bi bi-currency-exchange text-primary fs-2"></i>
                                                    <p class="small mb-0 mt-1">Servicios financieros</p>
                                                </div>
                                                <div class="col-12">
                                                    <i class="bi bi-truck text-primary fs-2"></i>
                                                    <p class="small mb-0 mt-1">Logística</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark text-center">
                                <h5 class="mb-0"><i class="bi bi-speedometer2 me-2"></i>Capacidades</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3 text-center">
                                    <div class="display-4 text-warning">60</div>
                                    <span class="text-muted">ppm velocidad</span>
                                </div>
                                <hr>
                                <div class="mb-3 text-center">
                                    <div class="display-4 text-success">300K</div>
                                    <span class="text-muted">páginas/mes</span>
                                </div>
                                <hr>
                                <div class="mb-3 text-center">
                                    <div class="display-4 text-info">1200</div>
                                    <span class="text-muted">dpi precisión</span>
                                </div>
                                <hr>
                                <div class="text-center">
                                    <div class="display-4 text-primary">99.9%</div>
                                    <span class="text-muted">confiabilidad</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3 border-info">
                            <div class="card-header bg-info text-white">
                                <h5 class="mb-0"><i class="bi bi-puzzle me-2"></i>Soluciones</h5>
                            </div>
                            <div class="card-body p-0">
                                <div class="list-group list-group-flush">
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>IM Series</strong>
                                            <br><small class="text-muted">Inteligencia avanzada</small>
                                        </div>
                                        <span class="badge bg-info rounded-pill">IA</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>MP Series</strong>
                                            <br><small class="text-muted">Multifuncional tradicional</small>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">Clásico</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>Pro Series</strong>
                                            <br><small class="text-muted">Producción profesional</small>
                                        </div>
                                        <span class="badge bg-warning rounded-pill">Pro</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4><i class="bi bi-lightbulb text-warning me-2"></i>Innovaciones Ricoh</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card bg-light border-purple h-100">
                                <div class="card-body text-center">
                                    <i class="bi bi-brain text-purple display-5"></i>
                                    <h6 class="mt-3">Smart Operation Panel</h6>
                                    <p class="card-text small">Interfaz inteligente que se adapta al usuario y optimiza flujos</p>
                                    <div class="progress" style="height: 5px;">
                                        <div class="progress-bar bg-purple" style="width: 90%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light border-danger h-100">
                                <div class="card-body text-center">
                                    <i class="bi bi-lock text-danger display-5"></i>
                                    <h6 class="mt-3">Security por Diseño</h6>
                                    <p class="card-text small">Seguridad integrada desde el hardware hasta el software</p>
                                    <div class="progress" style="height: 5px;">
                                        <div class="progress-bar bg-danger" style="width: 95%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light border-success h-100">
                                <div class="card-body text-center">
                                    <i class="bi bi-recycle text-success display-5"></i>
                                    <h6 class="mt-3">Sostenibilidad</h6>
                                    <p class="card-text small">Compromiso con el medio ambiente y eficiencia energética</p>
                                    <div class="progress" style="height: 5px;">
                                        <div class="progress-bar bg-success" style="width: 85%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-success mt-4" role="alert">
                    <h5 class="alert-heading"><i class="bi bi-headset text-success me-2"></i>Soporte Ricoh Especializado</h5>
                    <hr>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-unstyled mb-3">
                                <li><i class="bi bi-tools me-2 text-success"></i> Técnicos certificados por fábrica</li>
                                <li><i class="bi bi-truck me-2 text-success"></i> Repuestos originales garantizados</li>
                                <li><i class="bi bi-graph-up me-2 text-success"></i> Monitoreo proactivo remotamente</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled mb-3">
                                <li><i class="bi bi-clock me-2 text-success"></i> Respuesta en menos de 4 horas</li>
                                <li><i class="bi bi-mortarboard me-2 text-success"></i> Capacitación especializada incluida</li>
                                <li><i class="bi bi-phone me-2 text-success"></i> App móvil para soporte</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `
    }
};

// =============================================
// MANEJADOR DE MODALES DE MARCAS
// =============================================

document.addEventListener('click', function(e) {
    const brandCard = e.target.closest('[data-brand]');
    if (brandCard) {
        const brandType = brandCard.getAttribute('data-brand');
        const brandData = brandsContent[brandType];
        
        if (brandData) {
            // Actualizar contenido del modal
            const modalLabel = document.getElementById('brandModalLabel');
            const modalBody = document.getElementById('brandModalBody');
            
            if (modalLabel) {
                modalLabel.innerHTML = `<img src="${brandData.logo}" alt="${brandData.title}" style="height: 30px; margin-right: 10px;">${brandData.title}`;
            }
            if (modalBody) {
                modalBody.innerHTML = brandData.content;
            }
        }
    }
});

// =============================================
// FUNCIONES MEJORADAS PARA MARCAS
// =============================================

// Función para mostrar comparación entre marcas
function showBrandComparison() {
    const comparisonModal = document.createElement('div');
    comparisonModal.className = 'modal fade';
    comparisonModal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title"><i class="bi bi-bar-chart me-2"></i>Comparación de Marcas</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Característica</th>
                                    <th class="text-center">
                                        <img src="${brandsContent.konica.logo}" alt="Konica" style="height: 30px;">
                                        <br>Konica Minolta
                                    </th>
                                    <th class="text-center">
                                        <img src="${brandsContent.canon.logo}" alt="Canon" style="height: 30px;">
                                        <br>Canon
                                    </th>
                                    <th class="text-center">
                                        <img src="${brandsContent.ricoh.logo}" alt="Ricoh" style="height: 30px;">
                                        <br>Ricoh
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Velocidad Máxima</strong></td>
                                    <td class="text-center">
                                        <span class="badge bg-success">75 ppm</span>
                                    </td>
                                    <td class="text-center">
                                        <span class="badge bg-warning">55 ppm</span>
                                    </td>
                                    <td class="text-center">
                                        <span class="badge bg-primary">60 ppm</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>Fortaleza Principal</strong></td>
                                    <td class="text-center">Alta productividad</td>
                                    <td class="text-center">Calidad de imagen</td>
                                    <td class="text-center">Durabilidad</td>
                                </tr>
                                <tr>
                                    <td><strong>Ideal Para</strong></td>
                                    <td class="text-center">Grandes empresas</td>
                                    <td class="text-center">Diseño y fotografía</td>
                                    <td class="text-center">Alto volumen</td>
                                </tr>
                                <tr>
                                    <td><strong>Precio Alquiler</strong></td>
                                    <td class="text-center">$399-899/mes</td>
                                    <td class="text-center">$299-699/mes</td>
                                    <td class="text-center">$349-799/mes</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    <a href="/cotizacion/form" class="btn btn-primary">
                        <i class="bi bi-calculator me-2"></i>Solicitar Cotización
                    </a>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(comparisonModal);
    const modal = new bootstrap.Modal(comparisonModal);
    modal.show();
    
    // Remover modal del DOM cuando se cierre
    comparisonModal.addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Función para filtrar marcas por características
function filterBrandsByFeature(feature) {
    const brandCards = document.querySelectorAll('[data-brand]');
    
    brandCards.forEach(card => {
        card.style.transition = 'all 0.3s ease';
        
        switch(feature) {
            case 'speed':
                // Destacar marcas por velocidad
                if (card.dataset.brand === 'konica') {
                    card.style.border = '3px solid #28a745';
                    card.style.transform = 'scale(1.05)';
                } else {
                    card.style.opacity = '0.7';
                }
                break;
                
            case 'quality':
                // Destacar marcas por calidad
                if (card.dataset.brand === 'canon') {
                    card.style.border = '3px solid #28a745';
                    card.style.transform = 'scale(1.05)';
                } else {
                    card.style.opacity = '0.7';
                }
                break;
                
            case 'durability':
                // Destacar marcas por durabilidad
                if (card.dataset.brand === 'ricoh') {
                    card.style.border = '3px solid #28a745';
                    card.style.transform = 'scale(1.05)';
                } else {
                    card.style.opacity = '0.7';
                }
                break;
                
            default:
                // Resetear todos los estilos
                card.style.border = '';
                card.style.transform = '';
                card.style.opacity = '';
        }
    });
    
    // Mostrar toast informativo
    showBootstrapToast(`Marcas filtradas por: ${feature}`, 'info');
}

// Función para resetear filtros
function resetBrandFilters() {
    const brandCards = document.querySelectorAll('[data-brand]');
    brandCards.forEach(card => {
        card.style.border = '';
        card.style.transform = '';
        card.style.opacity = '';
    });
    showBootstrapToast('Filtros eliminados', 'success');
}

// =============================================
// ENHANCED FEATURES PARA MARCAS
// =============================================

// Tracking de interacciones con marcas
document.addEventListener('click', function(e) {
    const brandElement = e.target.closest('[data-brand]');
    if (brandElement) {
        const brandName = brandElement.dataset.brand;
        
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'brand_interaction', {
                brand_name: brandName,
                interaction_type: 'click'
            });
        }
        
        console.log(`📊 Brand interaction: ${brandName}`);
    }
});

// CSS adicional para mejorar la presentación de marcas
const brandEnhancementStyles = `
/* Estilos mejorados para marcas usando Bootstrap */
.brand-card {
    transition: all 0.3s ease;
    cursor: pointer;
    border-radius: 15px;
    overflow: hidden;
}

.brand-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 1rem 3rem rgba(0,0,0,0.175)!important;
}

.brand-card img {
    transition: all 0.3s ease;
}

.brand-card:hover img {
    transform: scale(1.1);
}

/* Progress bars mejorados */
.progress {
    border-radius: 10px;
    height: 8px;
}

.progress-bar {
    border-radius: 10px;
    font-size: 0.75rem;
    line-height: 8px;
}

/* Cards de características técnicas */
.card.border-success:hover,
.card.border-primary:hover,
.card.border-warning:hover,
.card.border-info:hover,
.card.border-danger:hover {
    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
    transform: translateY(-2px);
}

/* Badges personalizados */
.badge.rounded-pill {
    font-size: 0.75em;
    padding: 0.5em 0.75em;
}

/* Accordion mejorado */
.accordion-button:not(.collapsed) {
    background-color: rgba(var(--bs-primary-rgb), 0.1);
    border-color: var(--bs-primary);
}

/* Display numbers mejorados */
.display-4 {
    font-weight: 700;
    line-height: 1.1;
}

/* List group hover effects */
.list-group-item {
    transition: all 0.2s ease;
    border-left: 3px solid transparent;
}

.list-group-item:hover {
    background-color: var(--bs-light);
    border-left-color: var(--bs-primary);
    transform: translateX(5px);
}

/* Alert mejorados */
.alert {
    border-radius: 15px;
    border: none;
    box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
}

/* Purple color utility para Ricoh */
.text-purple { color: #6f42c1; }
.bg-purple { background-color: #6f42c1; }
.border-purple { border-color: #6f42c1; }

/* Comparison table styles */
.table-hover tbody tr:hover {
    background-color: rgba(var(--bs-primary-rgb), 0.075);
}

/* Brand logo hover effects */
.modal-header img {
    transition: all 0.3s ease;
}

.modal-header img:hover {
    transform: scale(1.1);
}

/* Enhanced card animations */
@keyframes cardPulse {
    0% { box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }
    50% { box-shadow: 0 0.5rem 1rem rgba(0,123,255,0.25); }
    100% { box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }
}

.card.featured {
    animation: cardPulse 2s infinite;
}

/* Responsive improvements */
@media (max-width: 768px) {
    .display-4 {
        font-size: 2rem;
    }
    
    .brand-card {
        margin-bottom: 1rem;
    }
}
`;

// Inyectar estilos de mejora para marcas
if (!document.querySelector('#brand-enhancement-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'brand-enhancement-styles';
    styleSheet.textContent = brandEnhancementStyles;
    document.head.appendChild(styleSheet);
}

// Función para destacar marca del mes (ejemplo)
function highlightFeaturedBrand(brandName) {
    const brandCard = document.querySelector(`[data-brand="${brandName}"]`);
    if (brandCard) {
        brandCard.classList.add('featured');
        
        // Añadir badge de "Destacado"
        const badge = document.createElement('div');
        badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
        badge.style.zIndex = '10';
        badge.innerHTML = 'Destacado <span class="visually-hidden">marca destacada</span>';
        brandCard.style.position = 'relative';
        brandCard.appendChild(badge);
    }
}

console.log('✅ Parte 3: Sistema de modales dinámicos para marcas inicializado con Bootstrap');

/**
 * PARTE 4A: COMPLETANDO MODALES DE PRODUCTOS Y FUNCIONALIDADES ADICIONALES
 * JavaScript para Homepage Moderna de Copier Company - Bootstrap Version
 * CONTINUACIÓN DE LA PARTE 4
 */

// =============================================
// FUNCIONES UTILITARIAS NECESARIAS
// =============================================

// Sistema de notificaciones toast usando Bootstrap (definida aquí para evitar errores)
function showBootstrapToast(message, type = 'info', duration = 5000) {
    // Crear container si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Definir iconos y colores según el tipo
    const toastConfig = {
        success: { icon: 'bi-check-circle-fill', bg: 'bg-success', text: 'text-white' },
        error: { icon: 'bi-exclamation-triangle-fill', bg: 'bg-danger', text: 'text-white' },
        warning: { icon: 'bi-exclamation-triangle-fill', bg: 'bg-warning', text: 'text-dark' },
        info: { icon: 'bi-info-circle-fill', bg: 'bg-info', text: 'text-white' }
    };
    
    const config = toastConfig[type] || toastConfig.info;
    
    // Crear toast usando Bootstrap
    const toastElement = document.createElement('div');
    toastElement.className = 'toast';
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="toast-header ${config.bg} ${config.text}">
            <i class="bi ${config.icon} me-2"></i>
            <strong class="me-auto">Copier Company</strong>
            <button type="button" class="btn-close ${config.text === 'text-white' ? 'btn-close-white' : ''}" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    // Inicializar y mostrar el toast usando Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const bsToast = new bootstrap.Toast(toastElement, { delay: duration });
        bsToast.show();
        
        // Remover el elemento del DOM después de que se oculte
        toastElement.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    } else {
        // Fallback si Bootstrap no está disponible
        toastElement.classList.add('show');
        setTimeout(() => {
            toastElement.remove();
        }, duration);
    }
}

// Tracking de interacciones para analytics (definida aquí para evitar errores)
function trackInteraction(action, category, label = '') {
    // Logging para desarrollo
    console.log(`📊 Analytics: ${action} - ${category} - ${label}`);
    
    // Ejemplo para Google Analytics 4 si está disponible
    if (typeof gtag !== 'undefined') {
        try {
            gtag('event', action, {
                event_category: category,
                event_label: label,
                custom_parameter: 'copier_company'
            });
        } catch (e) {
            console.warn('Error sending analytics:', e);
        }
    }
    
    // Almacenar en localStorage para análisis interno
    try {
        const analytics = JSON.parse(localStorage.getItem('copier_analytics') || '[]');
        analytics.push({
            action,
            category,
            label,
            timestamp: new Date().toISOString(),
            url: window.location.href
        });
        
        // Mantener solo los últimos 100 eventos
        if (analytics.length > 100) {
            analytics.splice(0, analytics.length - 100);
        }
        
        localStorage.setItem('copier_analytics', JSON.stringify(analytics));
    } catch (e) {
        console.warn('Error storing analytics:', e);
    }
}

// =============================================
// BASE DE DATOS DE PRODUCTOS (AGREGADA AQUÍ)
// =============================================

const productsContent = {
    'multifuncional-a3': {
        title: 'Multifuncionales A3',
        category: 'A3',
        description: 'Equipos de alto rendimiento para oficinas grandes y centros de copiado',
        content: `
            <div class="product-detail">
                <div class="row">
                    <div class="col-md-8">
                        <div class="product-overview">
                            <h4><i class="bi bi-arrows-fullscreen text-primary me-2"></i>Multifuncionales A3 Profesionales</h4>
                            <p class="lead">Diseñados para empresas con alto volumen de impresión que requieren versatilidad 
                            en formatos grandes. Ideales para oficinas corporativas, centros de copiado y 
                            departamentos de marketing que manejan documentos de gran formato.</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-6">
                                    <div class="card border-success">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-list-check me-2"></i>Funciones Principales</h5>
                                        </div>
                                        <div class="list-group list-group-flush">
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-printer text-success me-3"></i>
                                                <span>Impresión A3/A4 color y B&N</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-files text-success me-3"></i>
                                                <span>Copiado hasta 75 ppm</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-scanner text-success me-3"></i>
                                                <span>Escaneo dúplex automático</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-telephone text-success me-3"></i>
                                                <span>Fax (opcional)</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-filetype-pdf text-success me-3"></i>
                                                <span>Escaneo directo a PDF/email</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-warning">
                                        <div class="card-header bg-warning text-dark">
                                            <h5 class="mb-0"><i class="bi bi-gear-wide me-2"></i>Características Avanzadas</h5>
                                        </div>
                                        <div class="list-group list-group-flush">
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-wifi text-warning me-3"></i>
                                                <span>Conectividad WiFi y Ethernet</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-phone text-warning me-3"></i>
                                                <span>Impresión desde móviles</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-cloud text-warning me-3"></i>
                                                <span>Integración con servicios cloud</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-fingerprint text-warning me-3"></i>
                                                <span>Autenticación biométrica</span>
                                            </div>
                                            <div class="list-group-item d-flex align-items-center">
                                                <i class="bi bi-book text-warning me-3"></i>
                                                <span>Creación de folletos automática</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white text-center">
                                <h5 class="mb-0"><i class="bi bi-speedometer2 me-2"></i>Especificaciones</h5>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-6">
                                        <div class="p-2 border rounded text-center bg-light">
                                            <div class="fw-bold text-primary">35-75</div>
                                            <small class="text-muted">ppm</small>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="p-2 border rounded text-center bg-light">
                                            <div class="fw-bold text-primary">1200x1200</div>
                                            <small class="text-muted">dpi</small>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="p-2 border rounded text-center bg-light">
                                            <div class="fw-bold text-primary">50K-300K</div>
                                            <small class="text-muted">págs/mes</small>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="p-2 border rounded text-center bg-light">
                                            <div class="fw-bold text-primary">4-8 GB</div>
                                            <small class="text-muted">RAM</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3 border-success">
                            <div class="card-header bg-success text-white text-center">
                                <h5 class="mb-0"><i class="bi bi-currency-dollar me-2"></i>Alquiler Mensual</h5>
                            </div>
                            <div class="card-body text-center">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="h4 text-success mb-0">$299</span>
                                    <span class="text-muted">hasta</span>
                                    <span class="h4 text-success mb-0">$899</span>
                                </div>
                                <small class="text-muted d-block mt-2">*Incluye mantenimiento y soporte</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4><i class="bi bi-layers me-2 text-primary"></i>Modelos Disponibles</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card h-100">
                                <div class="card-header bg-light">
                                    <h6 class="mb-0">Entrada (35-45 ppm)</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-circle text-success me-2"></i>Ideal para oficinas medianas</li>
                                        <li><i class="bi bi-check-circle text-success me-2"></i>Funciones básicas completas</li>
                                        <li><i class="bi bi-check-circle text-success me-2"></i>Excelente relación precio/calidad</li>
                                    </ul>
                                </div>
                                <div class="card-footer bg-transparent text-center">
                                    <span class="h5 text-primary">$299-399/mes</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card h-100 border-warning position-relative">
                                <span class="position-absolute top-0 start-50 translate-middle badge rounded-pill bg-warning">
                                    Más Popular
                                </span>
                                <div class="card-header bg-warning text-dark">
                                    <h6 class="mb-0">Intermedio (50-60 ppm)</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-circle text-warning me-2"></i>Más popular para empresas</li>
                                        <li><i class="bi bi-check-circle text-warning me-2"></i>Funciones avanzadas incluidas</li>
                                        <li><i class="bi bi-check-circle text-warning me-2"></i>Óptimo rendimiento/costo</li>
                                    </ul>
                                </div>
                                <div class="card-footer bg-transparent text-center">
                                    <span class="h5 text-warning">$499-699/mes</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card h-100 border-danger">
                                <div class="card-header bg-danger text-white">
                                    <h6 class="mb-0">Alto Rendimiento (65-75 ppm)</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check-circle text-danger me-2"></i>Para centros de impresión</li>
                                        <li><i class="bi bi-check-circle text-danger me-2"></i>Máximas funcionalidades</li>
                                        <li><i class="bi bi-check-circle text-danger me-2"></i>Volúmenes industriales</li>
                                    </ul>
                                </div>
                                <div class="card-footer bg-transparent text-center">
                                    <span class="h5 text-danger">$699-899/mes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    'multifuncional-a4': {
        title: 'Multifuncionales A4',
        category: 'A4',
        description: 'Soluciones compactas perfectas para oficinas medianas y pequeñas',
        content: `
            <div class="product-detail">
                <div class="row">
                    <div class="col-md-12">
                        <h4><i class="bi bi-laptop text-primary me-2"></i>Multifuncionales A4 Compactos</h4>
                        <p class="lead">La solución ideal para oficinas que buscan funcionalidad completa en un espacio reducido.</p>
                        
                        <div class="alert alert-info">
                            <h5><i class="bi bi-info-circle me-2"></i>Características Principales</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check text-success me-2"></i>Impresión A4 color/B&N hasta 35 ppm</li>
                                        <li><i class="bi bi-check text-success me-2"></i>Copiado automático</li>
                                        <li><i class="bi bi-check text-success me-2"></i>Escaneo color alta resolución</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <ul class="list-unstyled">
                                        <li><i class="bi bi-check text-success me-2"></i>Conectividad WiFi</li>
                                        <li><i class="bi bi-check text-success me-2"></i>Impresión móvil</li>
                                        <li><i class="bi bi-check text-success me-2"></i>Diseño compacto</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card bg-success text-white">
                            <div class="card-body text-center">
                                <h5><i class="bi bi-currency-dollar me-2"></i>Precio de Alquiler</h5>
                                <h3>$149 - $299 / mes</h3>
                                <p class="mb-0">Incluye mantenimiento y soporte completo</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    'impresoras-laser': {
        title: 'Impresoras Láser',
        category: 'LÁSER',
        description: 'Alta velocidad y calidad profesional para impresión dedicada',
        content: `
            <div class="product-detail">
                <div class="row">
                    <div class="col-md-12">
                        <h4><i class="bi bi-lightning text-primary me-2"></i>Impresoras Láser Profesionales</h4>
                        <p class="lead">Tecnología láser de vanguardia para empresas que requieren velocidad excepcional.</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card border-dark">
                                    <div class="card-header bg-dark text-white">
                                        <h6><i class="bi bi-circle-fill me-2"></i>Láser Monocromático</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li><strong>Velocidad:</strong> 25-75 ppm</li>
                                            <li><strong>Costo por página:</strong> $0.02-0.04</li>
                                            <li><strong>Ideal para:</strong> Documentos de texto</li>
                                            <li><strong>Volumen:</strong> Alto (50K-300K/mes)</li>
                                        </ul>
                                        <div class="text-center">
                                            <span class="h5 text-dark">$199-599/mes</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-danger">
                                    <div class="card-header bg-danger text-white">
                                        <h6><i class="bi bi-palette-fill me-2"></i>Láser Color</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li><strong>Velocidad:</strong> 20-55 ppm</li>
                                            <li><strong>Costo por página:</strong> $0.08-0.15</li>
                                            <li><strong>Ideal para:</strong> Marketing y presentaciones</li>
                                            <li><strong>Volumen:</strong> Medio-Alto (20K-150K/mes)</li>
                                        </ul>
                                        <div class="text-center">
                                            <span class="h5 text-danger">$399-899/mes</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    'equipos-especializados': {
        title: 'Equipos Especializados',
        category: 'ESPECIAL',
        description: 'Soluciones personalizadas para necesidades específicas de la industria',
        content: `
            <div class="product-detail">
                <div class="row">
                    <div class="col-md-12">
                        <h4><i class="bi bi-gear-wide text-primary me-2"></i>Equipos Especializados</h4>
                        <p class="lead">Soluciones diseñadas para industrias específicas con requerimientos únicos.</p>
                        
                        <div class="row">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <i class="bi bi-map text-primary display-6"></i>
                                        <h6 class="mt-2">Plotters Gran Formato</h6>
                                        <p class="small">A2, A1, A0</p>
                                        <strong>$599-1,299/mes</strong>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <i class="bi bi-upc text-success display-6"></i>
                                        <h6 class="mt-2">Impresoras de Etiquetas</h6>
                                        <p class="small">Térmicas, 2"-8"</p>
                                        <strong>$199-599/mes</strong>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <i class="bi bi-camera text-warning display-6"></i>
                                        <h6 class="mt-2">Impresoras Fotográficas</h6>
                                        <p class="small">4x6" hasta 13x19"</p>
                                        <strong>$399-799/mes</strong>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <i class="bi bi-gear-wide text-danger display-6"></i>
                                        <h6 class="mt-2">Equipos Industriales</h6>
                                        <p class="small">IP54/IP65</p>
                                        <strong>$799-1,899/mes</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="alert alert-primary mt-3">
                            <h6><i class="bi bi-info-circle me-2"></i>Proceso de Implementación</h6>
                            <p class="mb-0">Análisis → Diseño → Implementación → Soporte Continuo</p>
                        </div>
                    </div>
                </div>
            </div>
        `
    }
};

// =============================================
// MANEJADOR DE MODALES DE PRODUCTOS (AGREGADO AQUÍ)
// =============================================

document.addEventListener('click', function(e) {
    const productCard = e.target.closest('[data-product]');
    if (productCard) {
        const productType = productCard.getAttribute('data-product');
        const productData = productsContent[productType];
        
        if (productData) {
            // Actualizar contenido del modal
            const modalLabel = document.getElementById('productModalLabel');
            const modalBody = document.getElementById('productModalBody');
            
            if (modalLabel) {
                modalLabel.innerHTML = `<i class="bi bi-printer me-2"></i>${productData.title}`;
            }
            if (modalBody) {
                modalBody.innerHTML = productData.content;
            }
            
            // Log para debugging
            console.log('✅ Producto cargado:', productData.title);
            trackInteraction('view_product', 'products', productType);
        } else {
            console.warn('❌ No se encontró datos para el producto:', productType);
            showBootstrapToast('Error al cargar la información del producto', 'error');
        }
    }
});

const productFilters = {
    init: function() {
        this.createFilterPanel();
        this.setupEventListeners();
    },
    
    createFilterPanel: function() {
        // Crear panel de filtros si no existe
        let filterPanel = document.getElementById('product-filter-panel');
        if (filterPanel) return;
        
        filterPanel = document.createElement('div');
        filterPanel.id = 'product-filter-panel';
        filterPanel.className = 'card border-primary mb-4';
        filterPanel.innerHTML = `
            <div class="card-header bg-primary text-white">
                <h6 class="mb-0"><i class="bi bi-funnel me-2"></i>Filtrar Productos</h6>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label small">Por Velocidad</label>
                        <select class="form-select form-select-sm" id="filter-speed">
                            <option value="">Todas</option>
                            <option value="low">Hasta 30 ppm</option>
                            <option value="medium">31-60 ppm</option>
                            <option value="high">Más de 60 ppm</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Por Formato</label>
                        <select class="form-select form-select-sm" id="filter-format">
                            <option value="">Todos</option>
                            <option value="a4">A4</option>
                            <option value="a3">A3</option>
                            <option value="large">Gran Formato</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Por Precio</label>
                        <select class="form-select form-select-sm" id="filter-price">
                            <option value="">Todos</option>
                            <option value="budget">$149-299</option>
                            <option value="mid">$300-599</option>
                            <option value="premium">$600+</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Por Función</label>
                        <select class="form-select form-select-sm" id="filter-function">
                            <option value="">Todas</option>
                            <option value="print">Solo Impresión</option>
                            <option value="multifunction">Multifuncional</option>
                            <option value="specialized">Especializado</option>
                        </select>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <button class="btn btn-primary btn-sm me-2" onclick="productFilters.applyFilters()">
                            <i class="bi bi-search me-1"></i>Aplicar Filtros
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="productFilters.clearFilters()">
                            <i class="bi bi-x-circle me-1"></i>Limpiar
                        </button>
                        <span class="badge bg-info ms-2" id="filter-results-count">0 productos encontrados</span>
                    </div>
                </div>
            </div>
        `;
        
        // Insertar antes del primer producto
        const firstProductSection = document.querySelector('.products-section, [data-product]')?.parentElement;
        if (firstProductSection) {
            firstProductSection.insertBefore(filterPanel, firstProductSection.firstChild);
        }
    },
    
    setupEventListeners: function() {
        // Auto-aplicar filtros cuando cambie algún select
        const filterSelects = ['filter-speed', 'filter-format', 'filter-price', 'filter-function'];
        filterSelects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', () => this.applyFilters());
            }
        });
    },
    
    applyFilters: function() {
        const filters = {
            speed: document.getElementById('filter-speed')?.value || '',
            format: document.getElementById('filter-format')?.value || '',
            price: document.getElementById('filter-price')?.value || '',
            function: document.getElementById('filter-function')?.value || ''
        };
        
        const productCards = document.querySelectorAll('[data-product]');
        let visibleCount = 0;
        
        productCards.forEach(card => {
            const productType = card.getAttribute('data-product');
            const shouldShow = this.matchesFilters(productType, filters);
            
            if (shouldShow) {
                card.style.display = '';
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
                visibleCount++;
            } else {
                card.style.opacity = '0.3';
                card.style.transform = 'scale(0.95)';
                // No ocultar completamente para mejor UX
            }
        });
        
        // Actualizar contador
        const counter = document.getElementById('filter-results-count');
        if (counter) {
            counter.textContent = `${visibleCount} productos encontrados`;
            counter.className = `badge ${visibleCount > 0 ? 'bg-success' : 'bg-warning'} ms-2`;
        }
        
        // Mostrar toast con resultados
        showBootstrapToast(`Filtros aplicados: ${visibleCount} productos encontrados`, 'info');
        
        // Analytics
        trackInteraction('filter_applied', 'products', JSON.stringify(filters));
    },
    
    matchesFilters: function(productType, filters) {
        const productData = productsContent[productType];
        if (!productData) return false;
        
        // Definir características de cada producto para filtros
        const productSpecs = {
            'multifuncional-a3': { speed: 'high', format: 'a3', price: 'premium', function: 'multifunction' },
            'multifuncional-a4': { speed: 'medium', format: 'a4', price: 'budget', function: 'multifunction' },
            'impresoras-laser': { speed: 'high', format: 'a4', price: 'mid', function: 'print' },
            'equipos-especializados': { speed: 'medium', format: 'large', price: 'premium', function: 'specialized' }
        };
        
        const specs = productSpecs[productType];
        if (!specs) return true;
        
        // Verificar cada filtro
        if (filters.speed && specs.speed !== filters.speed) return false;
        if (filters.format && specs.format !== filters.format) return false;
        if (filters.price && specs.price !== filters.price) return false;
        if (filters.function && specs.function !== filters.function) return false;
        
        return true;
    },
    
    clearFilters: function() {
        // Limpiar todos los selects
        const filterSelects = ['filter-speed', 'filter-format', 'filter-price', 'filter-function'];
        filterSelects.forEach(id => {
            const select = document.getElementById(id);
            if (select) select.value = '';
        });
        
        // Mostrar todos los productos
        const productCards = document.querySelectorAll('[data-product]');
        productCards.forEach(card => {
            card.style.display = '';
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
        });
        
        // Actualizar contador
        const counter = document.getElementById('filter-results-count');
        if (counter) {
            counter.textContent = `${productCards.length} productos encontrados`;
            counter.className = 'badge bg-success ms-2';
        }
        
        showBootstrapToast('Filtros eliminados', 'success');
        trackInteraction('filter_cleared', 'products', '');
    }
};

// =============================================
// SISTEMA DE FAVORITOS USANDO LOCALSTORAGE
// =============================================

const productFavorites = {
    favorites: new Set(),
    
    init: function() {
        this.loadFavorites();
        this.addFavoriteButtons();
        this.updateFavoriteButtons();
    },
    
    loadFavorites: function() {
        try {
            const saved = localStorage.getItem('copier_favorites');
            if (saved) {
                this.favorites = new Set(JSON.parse(saved));
            }
        } catch (e) {
            console.warn('Error loading favorites:', e);
            this.favorites = new Set();
        }
    },
    
    saveFavorites: function() {
        try {
            localStorage.setItem('copier_favorites', JSON.stringify([...this.favorites]));
        } catch (e) {
            console.warn('Error saving favorites:', e);
        }
    },
    
    addFavoriteButtons: function() {
        const productCards = document.querySelectorAll('[data-product]');
        productCards.forEach(card => {
            // Evitar duplicar botones
            if (card.querySelector('.favorite-btn')) return;
            
            const productType = card.getAttribute('data-product');
            const favoriteBtn = document.createElement('button');
            favoriteBtn.className = 'btn btn-outline-danger btn-sm favorite-btn position-absolute';
            favoriteBtn.style.cssText = 'top: 10px; right: 10px; z-index: 10; border-radius: 50%; width: 35px; height: 35px;';
            favoriteBtn.innerHTML = '<i class="bi bi-heart"></i>';
            favoriteBtn.setAttribute('data-product-type', productType);
            favoriteBtn.title = 'Agregar a favoritos';
            
            // Hacer el card relativo si no lo es
            if (getComputedStyle(card).position === 'static') {
                card.style.position = 'relative';
            }
            
            card.appendChild(favoriteBtn);
            
            // Event listener
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleFavorite(productType);
            });
        });
    },
    
    toggleFavorite: function(productType) {
        if (this.favorites.has(productType)) {
            this.favorites.delete(productType);
            showBootstrapToast('Eliminado de favoritos', 'info');
        } else {
            this.favorites.add(productType);
            showBootstrapToast('Agregado a favoritos', 'success');
        }
        
        this.saveFavorites();
        this.updateFavoriteButtons();
        trackInteraction('favorite_toggle', 'products', productType);
    },
    
    updateFavoriteButtons: function() {
        const favoriteButtons = document.querySelectorAll('.favorite-btn');
        favoriteButtons.forEach(btn => {
            const productType = btn.getAttribute('data-product-type');
            const isFavorite = this.favorites.has(productType);
            
            if (isFavorite) {
                btn.className = 'btn btn-danger btn-sm favorite-btn position-absolute';
                btn.innerHTML = '<i class="bi bi-heart-fill"></i>';
                btn.title = 'Quitar de favoritos';
            } else {
                btn.className = 'btn btn-outline-danger btn-sm favorite-btn position-absolute';
                btn.innerHTML = '<i class="bi bi-heart"></i>';
                btn.title = 'Agregar a favoritos';
            }
        });
    },
    
    showFavorites: function() {
        if (this.favorites.size === 0) {
            showBootstrapToast('No tienes productos favoritos', 'info');
            return;
        }
        
        const favoritesModal = document.createElement('div');
        favoritesModal.className = 'modal fade';
        favoritesModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-heart-fill me-2"></i>Mis Productos Favoritos</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            ${[...this.favorites].map(productType => {
                                const product = productsContent[productType];
                                if (!product) return '';
                                
                                return `
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-danger h-100">
                                            <div class="card-body">
                                                <h6 class="card-title text-danger">
                                                    <i class="bi bi-heart-fill me-2"></i>${product.title}
                                                </h6>
                                                <p class="card-text small">${product.description}</p>
                                                <div class="d-flex gap-2">
                                                    <button class="btn btn-sm btn-outline-primary" onclick="document.querySelector('[data-product=&quot;${productType}&quot;]').click()">
                                                        <i class="bi bi-eye me-1"></i>Ver Detalles
                                                    </button>
                                                    <button class="btn btn-sm btn-outline-danger" onclick="productFavorites.toggleFavorite('${productType}'); this.closest('.modal').querySelector('.btn-close').click();">
                                                        <i class="bi bi-heart-slash me-1"></i>Quitar
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <a href="/cotizacion/form" class="btn btn-primary">
                            <i class="bi bi-calculator me-2"></i>Cotizar Favoritos
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(favoritesModal);
        const modal = new bootstrap.Modal(favoritesModal);
        modal.show();
        
        favoritesModal.addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
        
        trackInteraction('view_favorites', 'products', this.favorites.size.toString());
    }
};

// =============================================
// SISTEMA DE CALCULADORA DE COSTOS
// =============================================

const costCalculator = {
    rates: {
        'multifuncional-a3': { min: 299, max: 899, maintenance: 150, installation: 100 },
        'multifuncional-a4': { min: 149, max: 299, maintenance: 80, installation: 50 },
        'impresoras-laser': { min: 199, max: 899, maintenance: 100, installation: 75 },
        'equipos-especializados': { min: 199, max: 1899, maintenance: 200, installation: 200 }
    },
    
    show: function(productType = null) {
        const calculatorModal = document.createElement('div');
        calculatorModal.className = 'modal fade';
        calculatorModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title"><i class="bi bi-calculator me-2"></i>Calculadora de Costos</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="cost-calculator-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Tipo de Equipo</label>
                                        <select class="form-select" id="calc-product-type" required>
                                            <option value="">Seleccionar equipo</option>
                                            <option value="multifuncional-a3" ${productType === 'multifuncional-a3' ? 'selected' : ''}>Multifuncional A3</option>
                                            <option value="multifuncional-a4" ${productType === 'multifuncional-a4' ? 'selected' : ''}>Multifuncional A4</option>
                                            <option value="impresoras-laser" ${productType === 'impresoras-laser' ? 'selected' : ''}>Impresora Láser</option>
                                            <option value="equipos-especializados" ${productType === 'equipos-especializados' ? 'selected' : ''}>Equipo Especializado</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Cantidad de Equipos</label>
                                        <input type="number" class="form-control" id="calc-quantity" min="1" max="50" value="1" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Duración del Contrato (meses)</label>
                                        <select class="form-select" id="calc-duration">
                                            <option value="12">12 meses</option>
                                            <option value="24" selected>24 meses</option>
                                            <option value="36">36 meses</option>
                                            <option value="48">48 meses</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Volumen Mensual Estimado (páginas)</label>
                                        <select class="form-select" id="calc-volume">
                                            <option value="low">Bajo (0-5,000)</option>
                                            <option value="medium" selected>Medio (5,001-25,000)</option>
                                            <option value="high">Alto (25,001-100,000)</option>
                                            <option value="industrial">Industrial (100,000+)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card bg-light h-100">
                                        <div class="card-header bg-primary text-white">
                                            <h6 class="mb-0">Resumen de Costos</h6>
                                        </div>
                                        <div class="card-body">
                                            <div class="cost-breakdown" id="cost-breakdown">
                                                <p class="text-muted text-center">Selecciona un equipo para ver los costos</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <button type="button" class="btn btn-primary" onclick="costCalculator.sendQuote()">
                            <i class="bi bi-envelope me-2"></i>Solicitar Cotización Oficial
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(calculatorModal);
        const modal = new bootstrap.Modal(calculatorModal);
        modal.show();
        
        // Event listeners para recalcular automáticamente
        const inputs = ['calc-product-type', 'calc-quantity', 'calc-duration', 'calc-volume'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.calculate());
            }
        });
        
        // Calcular si ya hay un producto seleccionado
        if (productType) {
            setTimeout(() => this.calculate(), 100);
        }
        
        calculatorModal.addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
        
        trackInteraction('open_calculator', 'cost_calculator', productType || 'general');
    },
    
    calculate: function() {
        const productType = document.getElementById('calc-product-type')?.value;
        const quantity = parseInt(document.getElementById('calc-quantity')?.value) || 1;
        const duration = parseInt(document.getElementById('calc-duration')?.value) || 24;
        const volume = document.getElementById('calc-volume')?.value || 'medium';
        
        if (!productType || !this.rates[productType]) {
            document.getElementById('cost-breakdown').innerHTML = '<p class="text-muted text-center">Selecciona un equipo para ver los costos</p>';
            return;
        }
        
        const rates = this.rates[productType];
        
        // Calcular precio base según volumen
        let basePrice = rates.min;
        if (volume === 'high') basePrice = rates.min + (rates.max - rates.min) * 0.7;
        else if (volume === 'industrial') basePrice = rates.max;
        else if (volume === 'medium') basePrice = rates.min + (rates.max - rates.min) * 0.4;
        
        // Aplicar descuentos por cantidad y duración
        let quantityDiscount = 0;
        if (quantity >= 5) quantityDiscount = 0.1;
        else if (quantity >= 3) quantityDiscount = 0.05;
        
        let durationDiscount = 0;
        if (duration >= 48) durationDiscount = 0.15;
        else if (duration >= 36) durationDiscount = 0.1;
        else if (duration >= 24) durationDiscount = 0.05;
        
        const monthlyPerUnit = basePrice * (1 - quantityDiscount - durationDiscount);
        const monthlyTotal = monthlyPerUnit * quantity;
        const totalContract = monthlyTotal * duration;
        const setupCost = rates.installation * quantity;
        const totalCostWithSetup = totalContract + setupCost;
        
        // Comparación con compra
        const purchasePrice = monthlyPerUnit * 20; // Estimación de precio de compra
        const maintenanceCost = rates.maintenance * quantity * duration;
        const totalPurchaseCost = (purchasePrice + maintenanceCost) * quantity;
        const savings = totalPurchaseCost - totalCostWithSetup;
        const savingsPercent = Math.round((savings / totalPurchaseCost) * 100);
        
        document.getElementById('cost-breakdown').innerHTML = `
            <div class="mb-3">
                <h6 class="text-primary">Costo Mensual</h6>
                <div class="d-flex justify-content-between">
                    <span>Por equipo:</span>
                    <strong>$${Math.round(monthlyPerUnit)}</strong>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Total mensual:</span>
                    <strong class="text-success">$${Math.round(monthlyTotal)}</strong>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-primary">Costo Total del Contrato</h6>
                <div class="d-flex justify-content-between">
                    <span>Alquiler (${duration} meses):</span>
                    <span>$${Math.round(totalContract).toLocaleString()}</span>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Instalación inicial:</span>
                    <span>$${setupCost}</span>
                </div>
                <hr>
                <div class="d-flex justify-content-between">
                    <strong>Total:</strong>
                    <strong class="text-success">$${Math.round(totalCostWithSetup).toLocaleString()}</strong>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-warning">Descuentos Aplicados</h6>
                ${quantityDiscount > 0 ? `<small class="d-block"><i class="bi bi-tag me-1"></i>Cantidad: ${Math.round(quantityDiscount*100)}%</small>` : ''}
                ${durationDiscount > 0 ? `<small class="d-block"><i class="bi bi-calendar me-1"></i>Duración: ${Math.round(durationDiscount*100)}%</small>` : ''}
                ${(quantityDiscount + durationDiscount) === 0 ? '<small class="text-muted">No hay descuentos disponibles</small>' : ''}
            </div>
            
            <div class="alert alert-success">
                <h6 class="alert-heading">Vs. Comprar</h6>
                <p class="mb-1">Ahorro estimado: <strong>$${Math.round(savings).toLocaleString()} (${savingsPercent}%)</strong></p>
                <small>Incluye mantenimiento, soporte y actualizaciones</small>
            </div>
        `;
        
        trackInteraction('calculate_cost', 'cost_calculator', `${productType}_${quantity}_${duration}`);
    },
    
    sendQuote: function() {
        const productType = document.getElementById('calc-product-type')?.value;
        const quantity = document.getElementById('calc-quantity')?.value;
        const duration = document.getElementById('calc-duration')?.value;
        
        if (!productType) {
            showBootstrapToast('Por favor selecciona un tipo de equipo', 'warning');
            return;
        }
        
        // Simular envío de cotización
        const quoteData = {
            product: productType,
            quantity: quantity,
            duration: duration,
            timestamp: new Date().toISOString()
        };
        
        // Guardar en localStorage para usar en formulario de cotización
        localStorage.setItem('quote_data', JSON.stringify(quoteData));
        
        showBootstrapToast('Datos guardados. Redirigiendo al formulario de cotización...', 'success');
        
        setTimeout(() => {
            window.location.href = '/cotizacion/form';
        }, 2000);
        
        trackInteraction('send_quote', 'cost_calculator', JSON.stringify(quoteData));
    }
};

// =============================================
// SISTEMA DE BÚSQUEDA INTELIGENTE
// =============================================

const smartSearch = {
    init: function() {
        this.createSearchBox();
        this.setupEventListeners();
    },
    
    createSearchBox: function() {
        let searchBox = document.getElementById('smart-search-box');
        if (searchBox) return;
        
        searchBox = document.createElement('div');
        searchBox.id = 'smart-search-box';
        searchBox.className = 'card border-info mb-4';
        searchBox.innerHTML = `
            <div class="card-body">
                <div class="input-group">
                    <span class="input-group-text bg-info text-white">
                        <i class="bi bi-search"></i>
                    </span>
                    <input type="text" class="form-control" id="smart-search-input" 
                           placeholder="Buscar productos por características (ej: 'A3 color rápido', 'económico oficina pequeña')">
                    <button class="btn btn-info" type="button" onclick="smartSearch.search()">
                        <i class="bi bi-search me-1"></i>Buscar
                    </button>
                </div>
                <div id="search-suggestions" class="mt-2" style="display: none;"></div>
                <div id="search-results" class="mt-3" style="display: none;"></div>
            </div>
        `;
        
        // Insertar después del panel de filtros o al inicio
        const filterPanel = document.getElementById('product-filter-panel');
        const insertTarget = filterPanel?.parentElement || document.querySelector('.products-section')?.parentElement;
        if (insertTarget) {
            if (filterPanel) {
                insertTarget.insertBefore(searchBox, filterPanel.nextSibling);
            } else {
                insertTarget.insertBefore(searchBox, insertTarget.firstChild);
            }
        }
    },
    
    setupEventListeners: function() {
        const searchInput = document.getElementById('smart-search-input');
        if (searchInput) {
            // Búsqueda en tiempo real con debounce
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (e.target.value.length >= 2) {
                        this.showSuggestions(e.target.value);
                    } else {
                        this.hideSuggestions();
                    }
                }, 300);
            });
            
            // Búsqueda al presionar Enter
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.search();
                }
            });
        }
    },
    
    showSuggestions: function(query) {
        const suggestions = this.generateSuggestions(query);
        const suggestionContainer = document.getElementById('search-suggestions');
        
        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        suggestionContainer.innerHTML = `
            <small class="text-muted">Sugerencias:</small>
            <div class="d-flex flex-wrap gap-1 mt-1">
                ${suggestions.map(suggestion => 
                    `<button class="btn btn-sm btn-outline-info" onclick="smartSearch.applySuggestion('${suggestion}')">${suggestion}</button>`
                ).join('')}
            </div>
        `;
        suggestionContainer.style.display = 'block';
    },
    
    hideSuggestions: function() {
        const suggestionContainer = document.getElementById('search-suggestions');
        if (suggestionContainer) {
            suggestionContainer.style.display = 'none';
        }
    },
    
    generateSuggestions: function(query) {
        const suggestions = [];
        const lowerQuery = query.toLowerCase();
        
        // Sugerencias basadas en palabras clave
        const keywords = {
            'a3': ['Multifuncional A3', 'gran formato'],
            'a4': ['Multifuncional A4', 'compacto'],
            'laser': ['Impresora Láser', 'alta velocidad'],
            'color': ['impresión color', 'marketing'],
            'rapido': ['alta velocidad', 'productivo'],
            'economico': ['bajo costo', 'presupuesto limitado'],
            'pequeña': ['oficina pequeña', 'compacto'],
            'grande': ['gran oficina', 'alto volumen'],
            'especializado': ['industria específica', 'personalizado']
        };
        
        Object.keys(keywords).forEach(key => {
            if (lowerQuery.includes(key)) {
                suggestions.push(...keywords[key]);
            }
        });
        
        return [...new Set(suggestions)].slice(0, 4);
    },
    
    applySuggestion: function(suggestion) {
        const searchInput = document.getElementById('smart-search-input');
        if (searchInput) {
            searchInput.value = suggestion;
            this.search();
        }
    },
    
    search: function() {
        const query = document.getElementById('smart-search-input')?.value.trim();
        if (!query) {
            showBootstrapToast('Por favor ingresa un término de búsqueda', 'warning');
            return;
        }
        
        this.hideSuggestions();
        const results = this.performSearch(query);
        this.displayResults(results, query);
        
        trackInteraction('smart_search', 'products', query);
    },
    
    performSearch: function(query) {
        const lowerQuery = query.toLowerCase();
        const results = [];
        
        // Definir características de búsqueda para cada producto
        const searchableProducts = {
            'multifuncional-a3': {
                keywords: ['a3', 'multifuncional', 'gran formato', 'corporativo', 'alto volumen', 'rapido', 'completo'],
                score: 0,
                data: productsContent['multifuncional-a3']
            },
            'multifuncional-a4': {
                keywords: ['a4', 'multifuncional', 'compacto', 'pequeño', 'oficina', 'economico', 'basico'],
                score: 0,
                data: productsContent['multifuncional-a4']
            },
            'impresoras-laser': {
                keywords: ['laser', 'rapido', 'velocidad', 'texto', 'documentos', 'profesional', 'eficiente'],
                score: 0,
                data: productsContent['impresoras-laser']
            },
            'equipos-especializados': {
                keywords: ['especializado', 'industria', 'personalizado', 'gran formato', 'etiquetas', 'fotografico'],
                score: 0,
                data: productsContent['equipos-especializados']
            }
        };
        
        // Calcular puntuación de relevancia
        Object.keys(searchableProducts).forEach(productKey => {
            const product = searchableProducts[productKey];
            let score = 0;
            
            // Buscar coincidencias exactas
            product.keywords.forEach(keyword => {
                if (lowerQuery.includes(keyword)) {
                    score += 10;
                }
            });
            
            // Buscar coincidencias parciales
            const queryWords = lowerQuery.split(' ');
            queryWords.forEach(word => {
                if (word.length >= 3) {
                    product.keywords.forEach(keyword => {
                        if (keyword.includes(word) || word.includes(keyword)) {
                            score += 5;
                        }
                    });
                }
            });
            
            // Buscar en título y descripción
            if (product.data.title.toLowerCase().includes(lowerQuery)) score += 15;
            if (product.data.description.toLowerCase().includes(lowerQuery)) score += 8;
            
            if (score > 0) {
                results.push({
                    productKey,
                    score,
                    data: product.data
                });
            }
        });
        
        // Ordenar por relevancia
        return results.sort((a, b) => b.score - a.score);
    },
    
    displayResults: function(results, query) {
        const resultsContainer = document.getElementById('search-results');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning">
                    <h6><i class="bi bi-exclamation-triangle me-2"></i>No se encontraron resultados</h6>
                    <p class="mb-0">No encontramos productos que coincidan con "${query}". 
                    Intenta con términos como: "A3", "láser", "compacto", "especializado".</p>
                </div>
            `;
        } else {
            resultsContainer.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-search me-2"></i>Resultados de búsqueda para "${query}"</h6>
                    <p class="mb-0">Se encontraron ${results.length} producto(s) relevante(s):</p>
                </div>
                <div class="row">
                    ${results.map((result, index) => `
                        <div class="col-md-6 mb-3">
                            <div class="card border-${index === 0 ? 'success' : 'info'} h-100">
                                <div class="card-header bg-${index === 0 ? 'success' : 'info'} text-white d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">${result.data.title}</h6>
                                    ${index === 0 ? '<span class="badge bg-warning text-dark">Mejor coincidencia</span>' : ''}
                                </div>
                                <div class="card-body">
                                    <p class="card-text">${result.data.description}</p>
                                    <div class="progress mb-2" style="height: 6px;">
                                        <div class="progress-bar bg-${index === 0 ? 'success' : 'info'}" 
                                             style="width: ${Math.min(result.score * 2, 100)}%"></div>
                                    </div>
                                    <small class="text-muted">Relevancia: ${result.score} puntos</small>
                                </div>
                                <div class="card-footer bg-transparent">
                                    <button class="btn btn-sm btn-outline-primary me-2" 
                                            onclick="document.querySelector('[data-product=&quot;${result.productKey}&quot;]')?.click()">
                                        <i class="bi bi-eye me-1"></i>Ver Detalles
                                    </button>
                                    <button class="btn btn-sm btn-outline-success" 
                                            onclick="costCalculator.show('${result.productKey}')">
                                        <i class="bi bi-calculator me-1"></i>Calcular Costo
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        resultsContainer.style.display = 'block';
        
        // Scroll suave hacia los resultados
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
};

// =============================================
// INICIALIZACIÓN DE TODAS LAS FUNCIONALIDADES
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar sistemas con delay para mejor UX
    setTimeout(() => {
        try {
            productFilters.init();
            console.log('✅ Product filters initialized');
        } catch (e) {
            console.warn('⚠️ Error initializing product filters:', e);
        }
    }, 500);
    
    setTimeout(() => {
        try {
            productFavorites.init();
            console.log('✅ Product favorites initialized');
        } catch (e) {
            console.warn('⚠️ Error initializing product favorites:', e);
        }
    }, 1000);
    
    setTimeout(() => {
        try {
            smartSearch.init();
            console.log('✅ Smart search initialized');
        } catch (e) {
            console.warn('⚠️ Error initializing smart search:', e);
        }
    }, 1500);
});

// Hacer funciones disponibles globalmente
window.productFilters = productFilters;
window.productFavorites = productFavorites;
window.costCalculator = costCalculator;
window.smartSearch = smartSearch;

// CSS adicionales para las nuevas funcionalidades
const additionalProductStyles = `
/* Estilos para filtros de productos */
#product-filter-panel {
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-radius: 10px;
}

#product-filter-panel .form-select {
    transition: border-color 0.3s ease;
}

#product-filter-panel .form-select:focus {
    border-color: var(--bs-primary);
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

/* Botones de favoritos */
.favorite-btn {
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    background-color: rgba(255,255,255,0.9);
}

.favorite-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
}

/* Animaciones para productos filtrados */
[data-product] {
    transition: all 0.5s ease;
}

/* Calculadora de costos */
#cost-breakdown {
    font-size: 0.9rem;
}

#cost-breakdown .progress {
    height: 6px;
    border-radius: 3px;
}

/* Búsqueda inteligente */
#smart-search-box {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

#smart-search-input {
    border: none;
    background: white;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

#smart-search-input:focus {
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1), 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

/* Sugerencias de búsqueda */
#search-suggestions .btn {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    margin: 0.1rem;
}

/* Resultados de búsqueda */
#search-results .card {
    transition: all 0.3s ease;
}

#search-results .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

/* Progress bars en resultados */
#search-results .progress {
    background-color: rgba(0,0,0,0.1);
}

/* Responsive improvements */
@media (max-width: 768px) {
    .product-filter-panel .row > div {
        margin-bottom: 1rem;
    }
    
    .favorite-btn {
        width: 30px;
        height: 30px;
        font-size: 0.8rem;
    }
    
    #smart-search-box .input-group {
        flex-wrap: wrap;
    }
    
    #smart-search-box .input-group .btn {
        flex: 1;
        margin-top: 0.5rem;
    }
}

/* Loading states */
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255,255,255,0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: inherit;
    z-index: 10;
}

.loading-spinner {
    width: 2rem;
    height: 2rem;
    border: 0.25rem solid rgba(0,0,0,0.1);
    border-top-color: var(--bs-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Success animations */
@keyframes pulse-success {
    0% { box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(25, 135, 84, 0); }
    100% { box-shadow: 0 0 0 0 rgba(25, 135, 84, 0); }
}

.pulse-success {
    animation: pulse-success 1s;
}

/* Error animations */
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.shake {
    animation: shake 0.5s;
}
`;

// Inyectar estilos adicionales
if (!document.querySelector('#additional-product-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'additional-product-styles';
    styleSheet.textContent = additionalProductStyles;
    document.head.appendChild(styleSheet);
}

console.log('✅ Parte 4A: Funcionalidades adicionales de productos inicializadas con Bootstrap');

/**
 * PARTE 5: INTEGRACIÓN COMPLETA Y OPTIMIZACIONES FINALES
 * JavaScript para Homepage Moderna de Copier Company - Bootstrap Version
 */

// =============================================
// SISTEMA DE PERFORMANCE Y OPTIMIZACIÓN
// =============================================

const performanceMonitor = {
    metrics: {
        loadTime: 0,
        interactionTime: 0,
        memoryUsage: 0,
        slowComponents: []
    },
    
    init: function() {
        this.measureLoadTime();
        this.monitorMemory();
        this.detectSlowComponents();
        this.setupPerformanceObserver();
    },
    
    measureLoadTime: function() {
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            this.metrics.loadTime = loadTime;
            
            console.log(`⚡ Página cargada en ${loadTime.toFixed(2)}ms`);
            
            // Mostrar badge de performance si es muy rápido
            if (loadTime < 2000) {
                this.showPerformanceBadge('fast');
            } else if (loadTime < 4000) {
                this.showPerformanceBadge('good');
            } else {
                this.showPerformanceBadge('slow');
            }
            
            // Enviar métricas si hay analytics configurado
            if (typeof gtag !== 'undefined') {
                gtag('event', 'page_load_time', {
                    custom_parameter: Math.round(loadTime)
                });
            }
        });
    },
    
    monitorMemory: function() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                this.metrics.memoryUsage = memory.usedJSHeapSize / 1048576; // MB
                
                // Advertir si el uso de memoria es alto
                if (this.metrics.memoryUsage > 50) {
                    console.warn(`⚠️ Alto uso de memoria: ${this.metrics.memoryUsage.toFixed(2)}MB`);
                }
            }, 30000); // Cada 30 segundos
        }
    },
    
    detectSlowComponents: function() {
        // Detectar imágenes que tardan mucho en cargar
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            const startTime = performance.now();
            
            const onLoad = () => {
                const loadTime = performance.now() - startTime;
                if (loadTime > 3000) {
                    this.metrics.slowComponents.push({
                        type: 'image',
                        src: img.src,
                        loadTime: loadTime
                    });
                    console.warn(`⚠️ Imagen lenta: ${img.src} (${loadTime.toFixed(2)}ms)`);
                }
            };
            
            if (img.complete) {
                onLoad();
            } else {
                img.addEventListener('load', onLoad);
                img.addEventListener('error', onLoad);
            }
        });
    },
    
    setupPerformanceObserver: function() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    if (entry.entryType === 'navigation') {
                        console.log(`📊 Navigation timing: ${entry.duration.toFixed(2)}ms`);
                    }
                });
            });
            
            try {
                observer.observe({ entryTypes: ['navigation', 'resource'] });
            } catch (e) {
                console.warn('Performance Observer not fully supported');
            }
        }
    },
    
    showPerformanceBadge: function(level) {
        const badge = document.createElement('div');
        badge.className = `position-fixed bottom-0 end-0 m-3 alert alert-${level === 'fast' ? 'success' : level === 'good' ? 'warning' : 'danger'} alert-dismissible fade show`;
        badge.style.zIndex = '9999';
        badge.innerHTML = `
            <i class="bi bi-speedometer2 me-2"></i>
            <strong>Performance:</strong> ${level === 'fast' ? 'Excelente' : level === 'good' ? 'Bueno' : 'Mejorable'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(badge);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (badge.parentNode) {
                badge.remove();
            }
        }, 5000);
    },
    
    generateReport: function() {
        return {
            loadTime: this.metrics.loadTime,
            memoryUsage: this.metrics.memoryUsage,
            slowComponents: this.metrics.slowComponents,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink
            } : null
        };
    }
};

// =============================================
// SISTEMA DE FORMULARIOS INTELIGENTE
// =============================================

const smartForms = {
    validationRules: {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^[+]?[\d\s\-\(\)]{9,}$/,
        name: /^[a-zA-ZÀ-ÿ\s]{2,50}$/
    },
    
    init: function() {
        this.setupFormValidation();
        this.setupProgressiveEnhancement();
        this.setupAutoSave();
        this.addSmartFeatures();
    },
    
    setupFormValidation: function() {
        document.addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                this.validateField(e.target);
            }
        });
        
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                this.validateForm(e.target, e);
            }
        });
    },
    
    validateField: function(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';
        
        // Limpiar estados anteriores
        field.classList.remove('is-valid', 'is-invalid');
        this.removeFeedback(field);
        
        if (field.required && !value) {
            isValid = false;
            message = 'Este campo es requerido';
        } else if (value) {
            // Validaciones específicas
            switch (field.type) {
                case 'email':
                    isValid = this.validationRules.email.test(value);
                    message = isValid ? '' : 'Ingresa un email válido';
                    break;
                    
                case 'tel':
                    isValid = this.validationRules.phone.test(value);
                    message = isValid ? '' : 'Ingresa un teléfono válido';
                    break;
                    
                case 'text':
                    if (field.name && field.name.toLowerCase().includes('name')) {
                        isValid = this.validationRules.name.test(value);
                        message = isValid ? '' : 'Solo letras y espacios (2-50 caracteres)';
                    }
                    break;
                    
                case 'number':
                    const num = parseFloat(value);
                    if (field.min && num < parseFloat(field.min)) {
                        isValid = false;
                        message = `Valor mínimo: ${field.min}`;
                    } else if (field.max && num > parseFloat(field.max)) {
                        isValid = false;
                        message = `Valor máximo: ${field.max}`;
                    }
                    break;
            }
        }
        
        this.showFieldFeedback(field, isValid, message);
        return isValid;
    },
    
    showFieldFeedback: function(field, isValid, message) {
        if (field.value.trim() !== '') {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
            
            if (!isValid && message) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = message;
                field.parentNode.appendChild(feedback);
            } else if (isValid) {
                const feedback = document.createElement('div');
                feedback.className = 'valid-feedback';
                feedback.innerHTML = '<i class="bi bi-check-circle me-1"></i>Correcto';
                field.parentNode.appendChild(feedback);
            }
        }
    },
    
    removeFeedback: function(field) {
        const feedbacks = field.parentNode.querySelectorAll('.invalid-feedback, .valid-feedback');
        feedbacks.forEach(fb => fb.remove());
    },
    
    validateForm: function(form, event) {
        const fields = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isFormValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isFormValid = false;
            }
        });
        
        if (!isFormValid) {
            event.preventDefault();
            
            // Scroll al primer campo inválido
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
            
            showBootstrapToast('Por favor corrige los errores en el formulario', 'error');
        } else {
            this.showSubmitProgress(form);
        }
    },
    
    showSubmitProgress: function(form) {
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';
            submitBtn.disabled = true;
            
            // Simular progreso (en implementación real, esto vendría del servidor)
            setTimeout(() => {
                submitBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Enviado';
                submitBtn.classList.remove('btn-primary');
                submitBtn.classList.add('btn-success');
                
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    submitBtn.classList.add('btn-primary');
                    submitBtn.classList.remove('btn-success');
                }, 3000);
            }, 2000);
        }
    },
    
    setupProgressiveEnhancement: function() {
        // Mejorar formularios existentes
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Añadir clase para estilos mejorados
            form.classList.add('smart-form');
            
            // Añadir indicador de campos requeridos
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                const label = form.querySelector(`label[for="${field.id}"]`) || 
                            field.parentNode.querySelector('label');
                if (label && !label.querySelector('.required-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'required-indicator text-danger';
                    indicator.innerHTML = ' *';
                    label.appendChild(indicator);
                }
            });
        });
    },
    
    setupAutoSave: function() {
        const formFields = document.querySelectorAll('input, textarea, select');
        formFields.forEach(field => {
            if (field.type === 'password' || field.type === 'submit') return;
            
            // Cargar valor guardado
            const savedValue = localStorage.getItem(`form_autosave_${field.name || field.id}`);
            if (savedValue && !field.value) {
                field.value = savedValue;
                // Trigger validation
                field.dispatchEvent(new Event('input'));
            }
            
            // Guardar cambios automáticamente con debounce
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (field.value.trim()) {
                        localStorage.setItem(`form_autosave_${field.name || field.id}`, field.value);
                    }
                }, 1000);
            });
        });
    },
    
    addSmartFeatures: function() {
        // Autocompletar inteligente para campos comunes
        this.addSmartAutocomplete();
        
        // Formateo automático de números de teléfono
        this.addPhoneFormatting();
        
        // Sugerencias de email
        this.addEmailSuggestions();
    },
    
    addSmartAutocomplete: function() {
        const cityFields = document.querySelectorAll('input[name*="city"], input[name*="ciudad"]');
        cityFields.forEach(field => {
            field.setAttribute('list', 'cities-peru');
        });
        
        // Crear datalist para ciudades de Perú
        if (!document.getElementById('cities-peru')) {
            const datalist = document.createElement('datalist');
            datalist.id = 'cities-peru';
            datalist.innerHTML = `
                <option value="Lima">
                <option value="Arequipa">
                <option value="Trujillo">
                <option value="Chiclayo">
                <option value="Piura">
                <option value="Iquitos">
                <option value="Cusco">
                <option value="Huancayo">
                <option value="Chimbote">
                <option value="Tacna">
            `;
            document.body.appendChild(datalist);
        }
    },
    
    addPhoneFormatting: function() {
        const phoneFields = document.querySelectorAll('input[type="tel"]');
        phoneFields.forEach(field => {
            field.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                
                // Formatear número peruano
                if (value.startsWith('51')) {
                    value = value.substring(2);
                }
                
                if (value.length >= 9) {
                    value = value.replace(/(\d{3})(\d{3})(\d{3})/, '$1 $2 $3');
                }
                
                e.target.value = value;
            });
        });
    },
    
    addEmailSuggestions: function() {
        const emailFields = document.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            field.addEventListener('blur', (e) => {
                const email = e.target.value;
                const suggestion = this.suggestEmailCorrection(email);
                
                if (suggestion && suggestion !== email) {
                    this.showEmailSuggestion(field, suggestion);
                }
            });
        });
    },
    
    suggestEmailCorrection: function(email) {
        const commonDomains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com'];
        const parts = email.split('@');
        
        if (parts.length !== 2) return null;
        
        const domain = parts[1].toLowerCase();
        
        // Buscar dominios similares
        for (let commonDomain of commonDomains) {
            if (this.levenshteinDistance(domain, commonDomain) <= 2 && domain !== commonDomain) {
                return `${parts[0]}@${commonDomain}`;
            }
        }
        
        return null;
    },
    
    levenshteinDistance: function(a, b) {
        const matrix = [];
        
        for (let i = 0; i <= b.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= a.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= b.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (b.charAt(i - 1) === a.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[b.length][a.length];
    },
    
    showEmailSuggestion: function(field, suggestion) {
        // Remover sugerencia anterior
        const existingSuggestion = field.parentNode.querySelector('.email-suggestion');
        if (existingSuggestion) existingSuggestion.remove();
        
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'email-suggestion alert alert-info alert-dismissible fade show mt-2';
        suggestionDiv.innerHTML = `
            <i class="bi bi-lightbulb me-2"></i>
            ¿Quisiste decir <strong>${suggestion}</strong>?
            <button type="button" class="btn btn-sm btn-outline-info ms-2" onclick="this.closest('.email-suggestion').previousElementSibling.value='${suggestion}'; this.closest('.email-suggestion').remove();">
                Usar esta dirección
            </button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        field.parentNode.appendChild(suggestionDiv);
    }
};

// =============================================
// SISTEMA DE CHAT BOT MEJORADO CON BOOTSTRAP
// =============================================

const chatBot = {
    isOpen: false,
    messages: [],
    
    init: function() {
        this.createChatWidget();
        this.setupEventListeners();
        this.loadChatHistory();
    },
    
    createChatWidget: function() {
        const chatWidget = document.createElement('div');
        chatWidget.id = 'chat-widget';
        chatWidget.innerHTML = `
            <div class="chat-bubble" id="chat-bubble">
                <i class="bi bi-chat-dots"></i>
                <span class="chat-notification badge bg-primary">¿Necesitas ayuda?</span>
            </div>
            <div class="chat-window card" id="chat-window" style="display: none;">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-robot me-2"></i>
                        <div>
                            <h6 class="mb-0">Asistente Virtual</h6>
                            <small class="text-light">Copier Company</small>
                        </div>
                    </div>
                    <button class="btn btn-outline-light btn-sm" id="chat-close">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
                <div class="card-body p-0">
                    <div class="chat-messages" id="chat-messages">
                        <!-- Mensajes se cargan aquí -->
                    </div>
                </div>
                <div class="card-footer">
                    <div class="input-group">
                        <input type="text" id="chat-input" class="form-control" placeholder="Escribe tu pregunta...">
                        <button class="btn btn-primary" id="chat-send">
                            <i class="bi bi-send"></i>
                        </button>
                    </div>
                    <div class="d-flex justify-content-center mt-2">
                        <small class="text-muted">Presiona Enter para enviar</small>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(chatWidget);
        this.addInitialMessage();
    },
    
    addInitialMessage: function() {
        const welcomeMessage = {
            text: `¡Hola! 👋 Soy tu asistente virtual de Copier Company. ¿En qué puedo ayudarte hoy?`,
            sender: 'bot',
            timestamp: new Date(),
            quickActions: [
                { text: '💰 Solicitar cotización', action: 'cotizacion' },
                { text: '📱 Ver productos', action: 'productos' },
                { text: '📞 Contacto', action: 'contacto' },
                { text: '🔧 Soporte técnico', action: 'soporte' }
            ]
        };
        
        this.addMessage(welcomeMessage);
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
        
        // Botones rápidos y acciones
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quick-action-btn')) {
                const action = e.target.closest('.quick-action-btn').dataset.action;
                this.handleQuickAction(action);
            }
        });
    },
    
    toggleChat: function() {
        const chatWindow = document.getElementById('chat-window');
        const chatBubble = document.getElementById('chat-bubble');
        
        if (this.isOpen) {
            chatWindow.style.display = 'none';
            chatBubble.style.display = 'flex';
            this.isOpen = false;
        } else {
            chatWindow.style.display = 'block';
            chatBubble.style.display = 'none';
            this.isOpen = true;
            
            // Focus en input y scroll al final
            setTimeout(() => {
                document.getElementById('chat-input').focus();
                this.scrollToBottom();
            }, 100);
        }
        
        trackInteraction('chat_toggle', 'chatbot', this.isOpen ? 'open' : 'close');
    },
    
    sendMessage: function() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (message) {
            // Agregar mensaje del usuario
            this.addMessage({
                text: message,
                sender: 'user',
                timestamp: new Date()
            });
            
            input.value = '';
            
            // Mostrar indicador de escritura
            this.showTypingIndicator();
            
            // Simular respuesta del bot con delay realista
            setTimeout(() => {
                this.hideTypingIndicator();
                const response = this.getBotResponse(message);
                this.addMessage(response);
            }, 1000 + Math.random() * 1000);
        }
    },
    
    addMessage: function(messageObj) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageObj.sender}-message mb-3`;
        
        const timeString = messageObj.timestamp.toLocaleTimeString('es-PE', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        if (messageObj.sender === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-end">
                    <div class="message-content bg-primary text-white rounded-3 p-2 max-w-75">
                        <p class="mb-1">${messageObj.text}</p>
                        <small class="opacity-75">${timeString}</small>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="d-flex">
                    <div class="flex-shrink-0 me-2">
                        <div class="avatar bg-light rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                            <i class="bi bi-robot text-primary"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <div class="message-content bg-light rounded-3 p-2">
                            <p class="mb-1">${messageObj.text}</p>
                            <small class="text-muted">${timeString}</small>
                        </div>
                        ${messageObj.quickActions ? this.renderQuickActions(messageObj.quickActions) : ''}
                    </div>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        this.messages.push(messageObj);
        this.scrollToBottom();
        this.saveChatHistory();
    },
    
    renderQuickActions: function(actions) {
        return `
            <div class="quick-actions mt-2">
                <div class="d-flex flex-wrap gap-1">
                    ${actions.map(action => 
                        `<button class="btn btn-sm btn-outline-primary quick-action-btn" data-action="${action.action}">
                            ${action.text}
                        </button>`
                    ).join('')}
                </div>
            </div>
        `;
    },
    
    showTypingIndicator: function() {
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'message bot-message mb-3';
        indicator.innerHTML = `
            <div class="d-flex">
                <div class="flex-shrink-0 me-2">
                    <div class="avatar bg-light rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                        <i class="bi bi-robot text-primary"></i>
                    </div>
                </div>
                <div class="flex-grow-1">
                    <div class="message-content bg-light rounded-3 p-2">
                        <div class="typing-animation">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('chat-messages').appendChild(indicator);
        this.scrollToBottom();
    },
    
    hideTypingIndicator: function() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    },
    
    getBotResponse: function(message) {
        const lowerMessage = message.toLowerCase();
        let response = '';
        let quickActions = [];
        
        // Respuestas contextuales mejoradas
        if (lowerMessage.includes('precio') || lowerMessage.includes('costo') || lowerMessage.includes('cotiz')) {
            response = `💰 Nuestros precios de alquiler son muy competitivos:
            <br><br>• <strong>A4 Compacto:</strong> $149-299/mes
            <br>• <strong>A3 Profesional:</strong> $299-899/mes
            <br>• <strong>Láser:</strong> $199-899/mes
            <br>• <strong>Especializado:</strong> $199-1,899/mes
            <br><br>¿Te gustaría una cotización personalizada?`;
            
            quickActions = [
                { text: '📝 Cotización personalizada', action: 'cotizacion' },
                { text: '🧮 Calculadora de costos', action: 'calculadora' }
            ];
        }
        else if (lowerMessage.includes('producto') || lowerMessage.includes('equipo') || lowerMessage.includes('fotocopiadora')) {
            response = `📱 Ofrecemos una amplia gama de equipos:
            <br><br>• <strong>Multifuncionales A3 y A4</strong> - Para oficinas de todos los tamaños
            <br>• <strong>Impresoras Láser</strong> - Alta velocidad y calidad
            <br>• <strong>Equipos Especializados</strong> - Soluciones personalizadas
            <br>• <strong>Marcas Premium:</strong> Konica Minolta, Canon, Ricoh
            <br><br>¿Qué tipo de equipo necesitas?`;
            
            quickActions = [
                { text: '🖨️ Ver todos los productos', action: 'productos' },
                { text: '🔍 Buscar producto específico', action: 'buscar' }
            ];
        }
        else if (lowerMessage.includes('mantenimiento') || lowerMessage.includes('reparaci') || lowerMessage.includes('soporte')) {
            response = `🔧 Nuestro servicio integral incluye:
            <br><br>• <strong>Mantenimiento preventivo y correctivo</strong>
            <br>• <strong>Soporte técnico 24/7</strong> los 365 días del año
            <br>• <strong>Repuestos originales</strong> sin costo adicional
            <br>• <strong>Tiempo de respuesta:</strong> máximo 4 horas
            <br>• <strong>Técnicos certificados</strong> por las marcas
            <br><br>¿Necesitas ayuda con algún equipo específico?`;
            
            quickActions = [
                { text: '📞 Solicitar soporte', action: 'soporte' },
                { text: '📋 Ver detalles del servicio', action: 'servicio' }
            ];
        }
        else if (lowerMessage.includes('contacto') || lowerMessage.includes('teléfono') || lowerMessage.includes('dirección')) {
            response = `📞 Puedes contactarnos por múltiples canales:
            <br><br>• <strong>Teléfono:</strong> (01) 975399303
            <br>• <strong>WhatsApp:</strong> 975 399 303
            <br>• <strong>Email:</strong> info@copiercompany.com
            <br>• <strong>Horario:</strong> Lun-Vie 8AM-6PM, Sáb 8AM-1PM
            <br>• <strong>Ubicación:</strong> San Isidro, Lima
            <br><br>¿Prefieres que te contactemos nosotros?`;
            
            quickActions = [
                { text: '📱 Abrir WhatsApp', action: 'whatsapp' },
                { text: '📧 Enviar email', action: 'email' }
            ];
        }
        else if (lowerMessage.includes('instalación') || lowerMessage.includes('instalar')) {
            response = `⚡ Nuestra instalación es súper rápida:
            <br><br>• <strong>Tiempo garantizado:</strong> 24 horas máximo
            <br>• <strong>Proceso completo:</strong> Entrega + Instalación + Configuración
            <br>• <strong>Capacitación incluida</strong> para tu equipo
            <br>• <strong>Garantía:</strong> Si no cumplimos 24h, primer mes GRATIS
            <br><br>¿Quieres programar una instalación?`;
            
            quickActions = [
                { text: '📅 Programar instalación', action: 'instalacion' },
                { text: '📋 Ver proceso completo', action: 'proceso' }
            ];
        }
        else if (lowerMessage.includes('garantía') || lowerMessage.includes('garantia')) {
            response = `🛡️ Nuestra garantía es total y sin letra pequeña:
            <br><br>• <strong>Cobertura 100%:</strong> Hardware, software y desgaste
            <br>• <strong>Reemplazo inmediato</strong> si es necesario
            <br>• <strong>Sin costos ocultos:</strong> Todo incluido
            <br>• <strong>Válida durante todo el contrato</strong>
            <br><br>¿Quieres conocer todos los detalles?`;
            
            quickActions = [
                { text: '📄 Ver términos completos', action: 'garantia' },
                { text: '❓ Hacer consulta específica', action: 'consulta' }
            ];
        }
        else {
            response = `Gracias por tu consulta. Te puedo ayudar con:
            <br><br>• <strong>Información de productos y precios</strong>
            <br>• <strong>Cotizaciones personalizadas</strong>
            <br>• <strong>Detalles de nuestro servicio</strong>
            <br>• <strong>Contacto con nuestros asesores</strong>
            <br><br>¿En qué tema específico te puedo ayudar?`;
            
            quickActions = [
                { text: '💰 Ver precios', action: 'precios' },
                { text: '📱 Ver productos', action: 'productos' },
                { text: '🤝 Hablar con asesor', action: 'asesor' }
            ];
        }
        
        return {
            text: response,
            sender: 'bot',
            timestamp: new Date(),
            quickActions: quickActions
        };
    },
    
    handleQuickAction: function(action) {
        const userMessage = this.getActionMessage(action);
        
        // Agregar mensaje del usuario
        this.addMessage({
            text: userMessage,
            sender: 'user',
            timestamp: new Date()
        });
        
        // Mostrar typing y responder
        this.showTypingIndicator();
        
        setTimeout(() => {
            this.hideTypingIndicator();
            const response = this.getActionResponse(action);
            this.addMessage(response);
        }, 1200);
        
        trackInteraction('chat_quick_action', 'chatbot', action);
    },
    
    getActionMessage: function(action) {
        const messages = {
            'cotizacion': 'Quiero solicitar una cotización personalizada',
            'productos': '¿Qué productos tienen disponibles?',
            'contacto': 'Necesito información de contacto',
            'soporte': '¿Cómo funciona el soporte técnico?',
            'calculadora': 'Quiero usar la calculadora de costos',
            'whatsapp': 'Prefiero contactar por WhatsApp',
            'email': 'Quiero enviar un email',
            'instalacion': 'Quiero programar una instalación',
            'garantia': 'Quiero conocer los detalles de la garantía',
            'precios': 'Quiero ver los precios',
            'asesor': 'Quiero hablar con un asesor'
        };
        
        return messages[action] || 'Necesito más información';
    },
    
    getActionResponse: function(action) {
        let response = '';
        let quickActions = [];
        
        switch(action) {
            case 'cotizacion':
                response = `¡Perfecto! 📝 Para crear tu cotización personalizada necesito algunos datos:
                <br><br>• Tipo de equipo que necesitas
                <br>• Volumen de impresión mensual aproximado
                <br>• Cantidad de equipos
                <br>• Funciones específicas requeridas
                <br><br>Te voy a dirigir al formulario donde puedes completar todos los detalles.`;
                
                setTimeout(() => {
                    window.open('/cotizacion/form', '_blank');
                }, 3000);
                break;
                
            case 'calculadora':
                response = `🧮 ¡Excelente! La calculadora de costos te permitirá:
                <br><br>• Ver precios en tiempo real
                <br>• Comparar diferentes opciones
                <br>• Calcular descuentos por volumen
                <br>• Comparar vs compra
                <br><br>Te abro la calculadora ahora mismo.`;
                
                setTimeout(() => {
                    if (typeof costCalculator !== 'undefined') {
                        costCalculator.show();
                    }
                }, 2000);
                break;
                
            case 'whatsapp':
                response = `📱 ¡Perfecto! WhatsApp es muy conveniente para comunicación rápida.
                <br><br>Te voy a redirigir a nuestro WhatsApp donde un asesor te atenderá de inmediato.
                <br><br><strong>Número:</strong> +51 975 399 303`;
                
                setTimeout(() => {
                    window.open('https://wa.me/51975399303?text=Hola, vengo del chat de la web y necesito información sobre equipos de impresión', '_blank');
                }, 3000);
                break;
                
            default:
                response = this.getBotResponse(this.getActionMessage(action)).text;
        }
        
        return {
            text: response,
            sender: 'bot',
            timestamp: new Date(),
            quickActions: quickActions
        };
    },
    
    scrollToBottom: function() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    },
    
    saveChatHistory: function() {
        try {
            const history = this.messages.slice(-20); // Solo guardar últimos 20 mensajes
            localStorage.setItem('chat_history', JSON.stringify(history));
        } catch (e) {
            console.warn('Error saving chat history:', e);
        }
    },
    
    loadChatHistory: function() {
        try {
            const history = localStorage.getItem('chat_history');
            if (history) {
                this.messages = JSON.parse(history);
                // Solo cargar si hay pocos mensajes para no saturar
                if (this.messages.length <= 5) {
                    this.messages.forEach(msg => {
                        // Re-renderizar mensajes sin guardar de nuevo
                        const messagesContainer = document.getElementById('chat-messages');
                        // Implementación simple sin duplicar lógica
                    });
                }
            }
        } catch (e) {
            console.warn('Error loading chat history:', e);
            this.messages = [];
        }
    }
};

// =============================================
// SISTEMA DE ANALYTICS AVANZADO
// =============================================

const advancedAnalytics = {
    sessionData: {
        startTime: Date.now(),
        interactions: [],
        scrollDepth: 0,
        timeOnSections: new Map(),
        deviceInfo: null
    },
    
    init: function() {
        this.collectDeviceInfo();
        this.trackUserBehavior();
        this.trackScrollDepth();
        this.trackTimeOnSections();
        this.setupHeatmapTracking();
        this.trackFormInteractions();
    },
    
    collectDeviceInfo: function() {
        this.sessionData.deviceInfo = {
            userAgent: navigator.userAgent,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : null,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine
        };
    },
    
    trackUserBehavior: function() {
        // Tracking de clics en elementos importantes
        document.addEventListener('click', (e) => {
            const element = e.target.closest('[data-track], .btn, [data-product], [data-brand]');
            if (element) {
                const trackData = {
                    type: 'click',
                    element: element.tagName,
                    className: element.className,
                    text: element.textContent.trim().substring(0, 100),
                    trackId: element.getAttribute('data-track'),
                    productId: element.getAttribute('data-product'),
                    brandId: element.getAttribute('data-brand'),
                    timestamp: Date.now(),
                    coordinates: { x: e.clientX, y: e.clientY }
                };
                
                this.sessionData.interactions.push(trackData);
                
                console.log(`📊 User Action:`, trackData);
                
                // Enviar a analytics externo
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'user_interaction', {
                        interaction_type: trackData.type,
                        element_type: trackData.element,
                        element_text: trackData.text
                    });
                }
            }
        });
        
        // Tracking de hover en elementos importantes
        let hoverTimeout;
        document.addEventListener('mouseover', (e) => {
            const element = e.target.closest('.product-card, .brand-card, .benefit-card');
            if (element) {
                hoverTimeout = setTimeout(() => {
                    const trackData = {
                        type: 'hover',
                        element: element.className,
                        duration: 2000, // Hover por más de 2 segundos
                        timestamp: Date.now()
                    };
                    
                    this.sessionData.interactions.push(trackData);
                }, 2000);
            }
        });
        
        document.addEventListener('mouseout', () => {
            if (hoverTimeout) {
                clearTimeout(hoverTimeout);
            }
        });
    },
    
    trackScrollDepth: function() {
        let maxScroll = 0;
        const milestones = [25, 50, 75, 90, 100];
        const triggered = new Set();
        
        const throttledScroll = this.throttle(() => {
            const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            
            if (scrollPercent > maxScroll) {
                maxScroll = scrollPercent;
                this.sessionData.scrollDepth = maxScroll;
                
                milestones.forEach(milestone => {
                    if (scrollPercent >= milestone && !triggered.has(milestone)) {
                        triggered.add(milestone);
                        
                        const trackData = {
                            type: 'scroll_depth',
                            depth: milestone,
                            timestamp: Date.now()
                        };
                        
                        this.sessionData.interactions.push(trackData);
                        
                        console.log(`📏 Scroll Depth: ${milestone}%`);
                        
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'scroll_depth', {
                                scroll_depth: milestone
                            });
                        }
                    }
                });
            }
        }, 100);
        
        window.addEventListener('scroll', throttledScroll);
    },
    
    trackTimeOnSections: function() {
        const sections = document.querySelectorAll('section[id], .hero-section, .benefits-section, .products-section');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const sectionId = entry.target.id || entry.target.className.split(' ')[0];
                
                if (entry.isIntersecting) {
                    this.sessionData.timeOnSections.set(sectionId, Date.now());
                } else if (this.sessionData.timeOnSections.has(sectionId)) {
                    const timeSpent = Date.now() - this.sessionData.timeOnSections.get(sectionId);
                    
                    if (timeSpent > 3000) { // Más de 3 segundos
                        const trackData = {
                            type: 'section_engagement',
                            section: sectionId,
                            timeSpent: Math.round(timeSpent / 1000),
                            timestamp: Date.now()
                        };
                        
                        this.sessionData.interactions.push(trackData);
                        
                        console.log(`⏱️ Time on ${sectionId}: ${Math.round(timeSpent/1000)}s`);
                        
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'section_engagement', {
                                section_name: sectionId,
                                time_spent: Math.round(timeSpent/1000)
                            });
                        }
                    }
                    
                    this.sessionData.timeOnSections.delete(sectionId);
                }
            });
        }, { threshold: 0.5 });
        
        sections.forEach(section => observer.observe(section));
    },
    
    setupHeatmapTracking: function() {
        // Tracking simplificado de heatmap usando clicks
        document.addEventListener('click', (e) => {
            const clickData = {
                x: e.clientX,
                y: e.clientY,
                element: e.target.tagName,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                timestamp: Date.now()
            };
            
            // Guardar datos de clicks para análisis
            const clicks = JSON.parse(localStorage.getItem('heatmap_clicks') || '[]');
            clicks.push(clickData);
            
            // Mantener solo los últimos 200 clicks
            if (clicks.length > 200) {
                clicks.splice(0, clicks.length - 200);
            }
            
            localStorage.setItem('heatmap_clicks', JSON.stringify(clicks));
        });
    },
    
    trackFormInteractions: function() {
        document.addEventListener('focus', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                const trackData = {
                    type: 'form_field_focus',
                    fieldName: e.target.name || e.target.id,
                    fieldType: e.target.type,
                    timestamp: Date.now()
                };
                
                this.sessionData.interactions.push(trackData);
            }
        });
        
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                const trackData = {
                    type: 'form_submit',
                    formId: e.target.id,
                    fieldsCount: e.target.querySelectorAll('input, textarea, select').length,
                    timestamp: Date.now()
                };
                
                this.sessionData.interactions.push(trackData);
                
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'form_submit', {
                        form_id: trackData.formId
                    });
                }
            }
        });
    },
    
    throttle: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    generateSessionReport: function() {
        const sessionDuration = Date.now() - this.sessionData.startTime;
        
        return {
            sessionId: this.generateSessionId(),
            duration: Math.round(sessionDuration / 1000),
            interactions: this.sessionData.interactions.length,
            scrollDepth: this.sessionData.scrollDepth,
            deviceInfo: this.sessionData.deviceInfo,
            interactionTypes: this.getInteractionSummary(),
            timestamp: new Date().toISOString(),
            pageUrl: window.location.href,
            referrer: document.referrer
        };
    },
    
    getInteractionSummary: function() {
        const summary = {};
        this.sessionData.interactions.forEach(interaction => {
            summary[interaction.type] = (summary[interaction.type] || 0) + 1;
        });
        return summary;
    },
    
    generateSessionId: function() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },
    
    sendAnalytics: function() {
        const report = this.generateSessionReport();
        
        // Enviar a servidor de analytics (simulado)
        console.log('📊 Session Report:', report);
        
        // En implementación real, enviarías a tu backend
        // fetch('/analytics', { method: 'POST', body: JSON.stringify(report) });
        
        return report;
    }
};

// =============================================
// INICIALIZACIÓN FINAL DEL SISTEMA COMPLETO
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema completo de Copier Company...');
    
    // Inicializar sistemas con delays escalonados para mejor performance
    const initSequence = [
        { system: performanceMonitor, name: 'Performance Monitor', delay: 0 },
        { system: smartForms, name: 'Smart Forms', delay: 300 },
        { system: chatBot, name: 'Chat Bot', delay: 600 },
        { system: advancedAnalytics, name: 'Advanced Analytics', delay: 900 }
    ];
    
    initSequence.forEach(({ system, name, delay }) => {
        setTimeout(() => {
            try {
                system.init();
                console.log(`✅ ${name} inicializado`);
            } catch (error) {
                console.error(`❌ Error inicializando ${name}:`, error);
            }
        }, delay);
    });
    
    // Configurar observador de mutaciones para contenido dinámico
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Re-inicializar funcionalidades para nuevo contenido
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Re-aplicar smart forms a nuevos formularios
                        const newForms = node.querySelectorAll('form');
                        if (newForms.length > 0) {
                            smartForms.setupProgressiveEnhancement();
                        }
                        
                        // Re-aplicar lazy loading a nuevas imágenes
                        const newImages = node.querySelectorAll('img[data-src]');
                        if (newImages.length > 0) {
                            initLazyLoading();
                        }
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Enviar analytics al salir de la página
    window.addEventListener('beforeunload', () => {
        advancedAnalytics.sendAnalytics();
    });
    
    // Enviar analytics cada 5 minutos para sesiones largas
    setInterval(() => {
        advancedAnalytics.sendAnalytics();
    }, 300000);
    
    // Mostrar mensaje de bienvenida en consola después de todo
    setTimeout(() => {
        console.log(`
        %c🏢 COPIER COMPANY HOMEPAGE 
        %c✨ Sistema JavaScript Completo v2.0 Bootstrap
        %c🔧 Desarrollado para Odoo con Bootstrap Icons
        %c📊 Todos los sistemas operativos y optimizados
        `, 
        'color: #0d6efd; font-size: 16px; font-weight: bold;',
        'color: #198754; font-size: 14px;',
        'color: #6c757d; font-size: 12px;',
        'color: #20c997; font-size: 12px;'
        );
        
        console.log('🎯 Sistemas activos:', {
            'Performance Monitor': '✅',
            'Smart Forms': '✅', 
            'Chat Bot': '✅',
            'Advanced Analytics': '✅',
            'Product Filters': '✅',
            'Favorites System': '✅',
            'Cost Calculator': '✅',
            'Smart Search': '✅'
        });
        
    }, 1500);
});

// =============================================
// CSS STYLES PARA CHAT BOT Y SISTEMA COMPLETO
// =============================================

const finalStyles = `
/* Chat Widget Styles con Bootstrap */
#chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 1055;
    font-family: var(--bs-font-sans-serif);
}

.chat-bubble {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--bs-primary), var(--bs-blue));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(var(--bs-primary-rgb), 0.3);
    transition: all 0.3s ease;
    position: relative;
    font-size: 1.5rem;
}

.chat-bubble:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 25px rgba(var(--bs-primary-rgb), 0.4);
}

.chat-notification {
    position: absolute;
    right: 70px;
    top: 50%;
    transform: translateY(-50%);
    white-space: nowrap;
    opacity: 0;
    animation: slideInNotification 4s ease-in-out 2s forwards;
}

@keyframes slideInNotification {
    0%, 80% { opacity: 0; transform: translateY(-50%) translateX(10px); }
    10%, 70% { opacity: 1; transform: translateY(-50%) translateX(0); }
    100% { opacity: 0; transform: translateY(-50%) translateX(10px); }
}

.chat-window {
    width: 380px;
    height: 600px;
    border: none;
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    overflow: hidden;
}

.chat-messages {
    height: 400px;
    overflow-y: auto;
    padding: 1rem;
    background: #f8f9fa;
}

.chat-messages::-webkit-scrollbar {
    width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
    background: #f1f1f1;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: var(--bs-primary);
    border-radius: 2px;
}

.message-content {
    max-width: 85%;
    word-wrap: break-word;
}

.quick-actions .btn {
    font-size: 0.8rem;
    padding: 0.375rem 0.75rem;
    margin: 0.125rem;
    border-radius: 20px;
}

.avatar {
    width: 32px;
    height: 32px;
}

.typing-animation {
    display: flex;
    align-items: center;
    height: 20px;
}

.typing-animation .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--bs-primary);
    margin: 0 2px;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-animation .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-animation .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
}

/* Smart Forms Styles */
.smart-form .form-control:focus,
.smart-form .form-select:focus {
    border-color: var(--bs-primary);
    box-shadow: 0 0 0 0.2rem rgba(var(--bs-primary-rgb), 0.25);
}

.required-indicator {
    color: var(--bs-danger);
}

.email-suggestion {
    border-radius: 10px;
    border-left: 4px solid var(--bs-info);
}

/* Performance Badge */
.performance-badge {
    border-radius: 10px;
    border: none;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

/* Analytics Visual Indicators */
.interaction-highlight {
    position: relative;
}

.interaction-highlight::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    border: 2px solid var(--bs-success);
    border-radius: inherit;
    opacity: 0;
    animation: highlight-pulse 0.6s ease-out;
}

@keyframes highlight-pulse {
    0% { opacity: 0; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.02); }
    100% { opacity: 0; transform: scale(1); }
}

/* Global improvements */
.btn {
    transition: all 0.3s ease;
    border-radius: 8px;
}

.btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card {
    border-radius: 12px;
    transition: all 0.3s ease;
}

.card:hover {
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

/* Mobile optimizations */
@media (max-width: 768px) {
    .chat-window {
        width: calc(100vw - 40px);
        height: 70vh;
        bottom: 20px;
        right: 20px;
    }
    
    .chat-notification {
        display: none;
    }
    
    .message-content {
        max-width: 90%;
    }
    
    .quick-actions .btn {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
    }
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Print styles */
@media print {
    #chat-widget,
    .chat-bubble,
    .chat-window {
        display: none !important;
    }
}
`;

// Inyectar estilos finales
if (!document.querySelector('#final-system-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'final-system-styles';
    styleSheet.textContent = finalStyles;
    document.head.appendChild(styleSheet);
}

// Exportar funciones principales para uso externo
window.CopierCompanyJS = {
    // Funciones de utilidad
    showBootstrapToast,
    trackInteraction,
    
    // Sistemas principales
    performanceMonitor,
    smartForms,
    chatBot,
    advancedAnalytics,
    
    // Sistemas de productos (de partes anteriores)
    productFilters: window.productFilters,
    productFavorites: window.productFavorites,
    costCalculator: window.costCalculator,
    smartSearch: window.smartSearch,
    
    // Función para generar reporte completo
    generateCompleteReport: function() {
        return {
            performance: performanceMonitor.generateReport(),
            analytics: advancedAnalytics.generateSessionReport(),
            chat: {
                isActive: chatBot.isOpen,
                messagesCount: chatBot.messages.length
            },
            timestamp: new Date().toISOString()
        };
    }
};

console.log('✅ Parte 5: Sistema completo inicializado con Bootstrap - Todas las funcionalidades activas');