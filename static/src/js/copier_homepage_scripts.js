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
        title: 'Konica Minolta',
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
