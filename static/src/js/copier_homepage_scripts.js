/**
 * PARTE 1: INICIALIZACIÓN Y EFECTOS DE SCROLL
 * JavaScript para Homepage Moderna de Copier Company
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

// CSS adicional para las animaciones (agregar al CSS)
const animationStyles = `
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
`;

// Inyectar estilos si no están presentes
if (!document.querySelector('#animation-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'animation-styles';
    styleSheet.textContent = animationStyles;
    document.head.appendChild(styleSheet);
}
/**
 * PARTE 2: MODALES DINÁMICOS Y CONTENIDO INTERACTIVO
 * JavaScript para Homepage Moderna de Copier Company
 */

// =============================================
// SISTEMA DE MODALES DINÁMICOS
// =============================================

// Base de datos de contenido para modales
const modalContent = {
    benefits: {
        'sin-inversion': {
            title: 'Sin Inversión Inicial',
            icon: 'fas fa-hand-holding-usd',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-6">
                            <h4><i class="fas fa-piggy-bank text-primary me-2"></i>Ventajas Financieras</h4>
                            <ul class="benefit-list">
                                <li><i class="fas fa-check text-success me-2"></i>Preserva tu capital de trabajo</li>
                                <li><i class="fas fa-check text-success me-2"></i>Mejora tu flujo de caja mensual</li>
                                <li><i class="fas fa-check text-success me-2"></i>No afecta líneas de crédito</li>
                                <li><i class="fas fa-check text-success me-2"></i>Gastos deducibles fiscalmente</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h4><i class="fas fa-chart-line text-primary me-2"></i>Beneficios Empresariales</h4>
                            <ul class="benefit-list">
                                <li><i class="fas fa-check text-success me-2"></i>Tecnología de última generación</li>
                                <li><i class="fas fa-check text-success me-2"></i>Actualización constante</li>
                                <li><i class="fas fa-check text-success me-2"></i>Sin obsolescencia tecnológica</li>
                                <li><i class="fas fa-check text-success me-2"></i>Escalabilidad según crecimiento</li>
                            </ul>
                        </div>
                    </div>
                    <div class="highlight-box mt-4">
                        <i class="fas fa-lightbulb text-warning me-2"></i>
                        <strong>¿Sabías que?</strong> Las empresas que alquilan equipos tecnológicos aumentan su productividad en un 35% 
                        al tener siempre acceso a la última tecnología sin comprometer su capital.
                    </div>
                </div>
            `
        },
        'soporte-24-7': {
            title: 'Soporte Técnico 24/7',
            icon: 'fas fa-headset',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="support-level">
                                <div class="support-icon">
                                    <i class="fas fa-phone text-success"></i>
                                </div>
                                <h5>Nivel 1: Telefónico</h5>
                                <p><strong>Tiempo:</strong> Inmediato</p>
                                <ul>
                                    <li>Diagnóstico inicial</li>
                                    <li>Soluciones básicas</li>
                                    <li>Orientación de uso</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="support-level">
                                <div class="support-icon">
                                    <i class="fas fa-laptop text-primary"></i>
                                </div>
                                <h5>Nivel 2: Remoto</h5>
                                <p><strong>Tiempo:</strong> 15 minutos</p>
                                <ul>
                                    <li>Conexión remota</li>
                                    <li>Configuraciones avanzadas</li>
                                    <li>Actualizaciones</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="support-level">
                                <div class="support-icon">
                                    <i class="fas fa-user-tie text-warning"></i>
                                </div>
                                <h5>Nivel 3: Presencial</h5>
                                <p><strong>Tiempo:</strong> 4 horas</p>
                                <ul>
                                    <li>Técnico especializado</li>
                                    <li>Reparaciones complejas</li>
                                    <li>Reemplazo de equipos</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="support-stats mt-4">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <div class="stat-item">
                                    <h3 class="text-primary">98%</h3>
                                    <p>Resolución remota</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item">
                                    <h3 class="text-success">15min</h3>
                                    <p>Tiempo promedio</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item">
                                    <h3 class="text-warning">24/7</h3>
                                    <p>Disponibilidad</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-item">
                                    <h3 class="text-info">365</h3>
                                    <p>Días al año</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'instalacion-rapida': {
            title: 'Instalación en 24H',
            icon: 'fas fa-rocket',
            content: `
                <div class="benefit-detail">
                    <div class="installation-timeline">
                        <div class="timeline-item">
                            <div class="timeline-marker">1</div>
                            <div class="timeline-content">
                                <h5><i class="fas fa-handshake text-primary me-2"></i>Confirmación del Pedido</h5>
                                <p><strong>Tiempo:</strong> 2 horas</p>
                                <ul>
                                    <li>Verificación de especificaciones</li>
                                    <li>Programación de instalación</li>
                                    <li>Preparación del equipo</li>
                                </ul>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-marker">2</div>
                            <div class="timeline-content">
                                <h5><i class="fas fa-shipping-fast text-success me-2"></i>Transporte Especializado</h5>
                                <p><strong>Tiempo:</strong> 4 horas</p>
                                <ul>
                                    <li>Embalaje profesional</li>
                                    <li>Transporte asegurado</li>
                                    <li>Coordinación de llegada</li>
                                </ul>
                            </div>
                        </div>
                        <div class="timeline-item">
                            <div class="timeline-marker">3</div>
                            <div class="timeline-content">
                                <h5><i class="fas fa-cogs text-warning me-2"></i>Instalación y Configuración</h5>
                                <p><strong>Tiempo:</strong> 2-4 horas</p>
                                <ul>
                                    <li>Instalación física</li>
                                    <li>Configuración de red</li>
                                    <li>Pruebas de funcionamiento</li>
                                    <li>Capacitación básica</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="installation-guarantee mt-4 p-3 bg-light rounded">
                        <h5><i class="fas fa-shield-alt text-success me-2"></i>Garantía de Instalación</h5>
                        <p class="mb-0">Si por algún motivo no podemos instalar tu equipo en 24 horas, 
                        <strong>el primer mes de alquiler es completamente GRATIS</strong>.</p>
                    </div>
                </div>
            `
        },
        'mantenimiento-incluido': {
            title: 'Mantenimiento Incluido',
            icon: 'fas fa-cog',
            content: `
                <div class="benefit-detail">
                    <div class="row">
                        <div class="col-md-6">
                            <h4><i class="fas fa-calendar-check text-primary me-2"></i>Mantenimiento Preventivo</h4>
                            <div class="maintenance-schedule">
                                <div class="schedule-item">
                                    <span class="frequency">Semanal</span>
                                    <ul>
                                        <li>Limpieza de sensores</li>
                                        <li>Verificación de consumibles</li>
                                    </ul>
                                </div>
                                <div class="schedule-item">
                                    <span class="frequency">Mensual</span>
                                    <ul>
                                        <li>Calibración de colores</li>
                                        <li>Actualización de firmware</li>
                                        <li>Limpieza interna profunda</li>
                                    </ul>
                                </div>
                                <div class="schedule-item">
                                    <span class="frequency">Trimestral</span>
                                    <ul>
                                        <li>Revisión completa</li>
                                        <li>Reemplazo de rodillos</li>
                                        <li>Optimización de rendimiento</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h4><i class="fas fa-tools text-success me-2"></i>Mantenimiento Correctivo</h4>
                            <div class="repair-coverage">
                                <div class="coverage-item">
                                    <i class="fas fa-check-circle text-success"></i>
                                    <span>Reparación de averías</span>
                                </div>
                                <div class="coverage-item">
                                    <i class="fas fa-check-circle text-success"></i>
                                    <span>Reemplazo de repuestos</span>
                                </div>
                                <div class="coverage-item">
                                    <i class="fas fa-check-circle text-success"></i>
                                    <span>Mano de obra técnica</span>
                                </div>
                                <div class="coverage-item">
                                    <i class="fas fa-check-circle text-success"></i>
                                    <span>Diagnósticos especializados</span>
                                </div>
                                <div class="coverage-item">
                                    <i class="fas fa-check-circle text-success"></i>
                                    <span>Actualizaciones de software</span>
                                </div>
                            </div>
                            <div class="maintenance-value mt-3 p-3 bg-success text-white rounded">
                                <h6><i class="fas fa-calculator me-2"></i>Valor del Mantenimiento</h6>
                                <p class="mb-0">El mantenimiento incluido tiene un valor aproximado de 
                                <strong>$200-400 USD mensuales</strong> por equipo.</p>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'garantia-total': {
            title: 'Garantía Total',
            icon: 'fas fa-shield-alt',
            content: `
                <div class="benefit-detail">
                    <div class="guarantee-coverage">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="coverage-card">
                                    <div class="coverage-icon">
                                        <i class="fas fa-cog text-primary"></i>
                                    </div>
                                    <h5>Cobertura Técnica</h5>
                                    <ul>
                                        <li>Fallas de hardware</li>
                                        <li>Problemas de software</li>
                                        <li>Defectos de fabricación</li>
                                        <li>Desgaste normal</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="coverage-card">
                                    <div class="coverage-icon">
                                        <i class="fas fa-exchange-alt text-success"></i>
                                    </div>
                                    <h5>Reemplazo Inmediato</h5>
                                    <ul>
                                        <li>Equipo de respaldo</li>
                                        <li>Transferencia de configuración</li>
                                        <li>Sin interrupción del trabajo</li>
                                        <li>Mismo nivel de servicio</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="coverage-card">
                                    <div class="coverage-icon">
                                        <i class="fas fa-dollar-sign text-warning"></i>
                                    </div>
                                    <h5>Sin Costos Ocultos</h5>
                                    <ul>
                                        <li>Repuestos incluidos</li>
                                        <li>Mano de obra gratis</li>
                                        <li>Transporte sin costo</li>
                                        <li>Diagnósticos gratuitos</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="guarantee-terms mt-4">
                        <h5><i class="fas fa-file-contract text-info me-2"></i>Términos de la Garantía</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <h6>QUÉ ESTÁ CUBIERTO:</h6>
                                <ul class="covered-list">
                                    <li><i class="fas fa-check text-success me-1"></i> Todas las reparaciones</li>
                                    <li><i class="fas fa-check text-success me-1"></i> Repuestos originales</li>
                                    <li><i class="fas fa-check text-success me-1"></i> Mano de obra técnica</li>
                                    <li><i class="fas fa-check text-success me-1"></i> Reemplazo total si es necesario</li>
                                    <li><i class="fas fa-check text-success me-1"></i> Actualizaciones de firmware</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>QUÉ NO ESTÁ CUBIERTO:</h6>
                                <ul class="not-covered-list">
                                    <li><i class="fas fa-times text-danger me-1"></i> Daños por mal uso intencional</li>
                                    <li><i class="fas fa-times text-danger me-1"></i> Modificaciones no autorizadas</li>
                                    <li><i class="fas fa-times text-danger me-1"></i> Desastres naturales extremos</li>
                                    <li><i class="fas fa-times text-danger me-1"></i> Consumibles (toners, papel)</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        'escalabilidad': {
            title: 'Escalabilidad',
            icon: 'fas fa-chart-line',
            content: `
                <div class="benefit-detail">
                    <div class="scalability-options">
                        <h4><i class="fas fa-arrows-alt text-primary me-2"></i>Opciones de Escalabilidad</h4>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="scale-option">
                                    <div class="scale-icon up">
                                        <i class="fas fa-arrow-up"></i>
                                    </div>
                                    <h5>Escalar Hacia Arriba</h5>
                                    <p>Cuando tu negocio crece</p>
                                    <ul>
                                        <li>Equipos más potentes</li>
                                        <li>Mayor capacidad</li>
                                        <li>Funciones adicionales</li>
                                        <li>Múltiples ubicaciones</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="scale-option">
                                    <div class="scale-icon lateral">
                                        <i class="fas fa-exchange-alt"></i>
                                    </div>
                                    <h5>Cambio Lateral</h5>
                                    <p>Necesidades específicas</p>
                                    <ul>
                                        <li>Cambio de tecnología</li>
                                        <li>Diferentes funciones</li>
                                        <li>Especialización</li>
                                        <li>Optimización</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="scale-option">
                                    <div class="scale-icon down">
                                        <i class="fas fa-arrow-down"></i>
                                    </div>
                                    <h5>Escalar Hacia Abajo</h5>
                                    <p>Optimización de costos</p>
                                    <ul>
                                        <li>Equipos más simples</li>
                                        <li>Menor capacidad</li>
                                        <li>Reducción de costos</li>
                                        <li>Funciones básicas</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="scalability-process mt-4 p-3 bg-light rounded">
                        <h5><i class="fas fa-cogs text-success me-2"></i>Proceso de Escalabilidad</h5>
                        <div class="process-steps-mini">
                            <span class="step"><i class="fas fa-comments"></i> Evaluación</span>
                            <span class="arrow">→</span>
                            <span class="step"><i class="fas fa-chart-bar"></i> Análisis</span>
                            <span class="arrow">→</span>
                            <span class="step"><i class="fas fa-handshake"></i> Propuesta</span>
                            <span class="arrow">→</span>
                            <span class="step"><i class="fas fa-rocket"></i> Implementación</span>
                        </div>
                        <p class="mt-2 mb-0"><strong>Tiempo promedio:</strong> 48-72 horas para cambios completos</p>
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
            document.getElementById('benefitModalLabel').innerHTML = 
                `<i class="${benefitData.icon} me-2"></i>${benefitData.title}`;
            document.getElementById('benefitModalBody').innerHTML = benefitData.content;
        }
    }
});

console.log('✅ Parte 2: Sistema de modales dinámicos para beneficios inicializado');
/**
 * PARTE 3: MODALES DE MARCAS Y PRODUCTOS
 * JavaScript para Homepage Moderna de Copier Company
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
                            <h4><i class="fas fa-award text-primary me-2"></i>Acerca de Konica Minolta</h4>
                            <p>Líder mundial en tecnología de impresión con más de 150 años de innovación. 
                            Especializada en soluciones multifuncionales de alta gama para empresas que requieren 
                            máxima calidad y productividad.</p>
                            
                            <div class="brand-highlights mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-rocket text-success me-2"></i>Ventajas Clave</h5>
                                        <ul class="feature-list">
                                            <li><i class="fas fa-check text-success me-1"></i> Velocidad hasta 75 ppm</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Calidad de impresión superior</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Tecnología de seguridad avanzada</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Conectividad en la nube</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Bajo consumo energético</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-industry text-warning me-2"></i>Ideal Para</h5>
                                        <ul class="industry-list">
                                            <li><i class="fas fa-building me-1"></i> Grandes corporaciones</li>
                                            <li><i class="fas fa-graduation-cap me-1"></i> Instituciones educativas</li>
                                            <li><i class="fas fa-hospital me-1"></i> Centros médicos</li>
                                            <li><i class="fas fa-balance-scale me-1"></i> Estudios legales</li>
                                            <li><i class="fas fa-print me-1"></i> Centros de impresión</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="brand-stats">
                            <h5><i class="fas fa-chart-bar text-info me-2"></i>Especificaciones</h5>
                            <div class="stat-grid">
                                <div class="stat-item">
                                    <span class="stat-value">75</span>
                                    <span class="stat-label">ppm máximo</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">1200</span>
                                    <span class="stat-label">dpi resolución</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">7500</span>
                                    <span class="stat-label">hojas/mes</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">4.3"</span>
                                    <span class="stat-label">pantalla táctil</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="brand-models mt-4">
                            <h5><i class="fas fa-list text-secondary me-2"></i>Modelos Populares</h5>
                            <div class="model-list">
                                <div class="model-item">
                                    <strong>bizhub C558</strong>
                                    <span>55 ppm color/B&N</span>
                                </div>
                                <div class="model-item">
                                    <strong>bizhub C658</strong>
                                    <span>65 ppm color/B&N</span>
                                </div>
                                <div class="model-item">
                                    <strong>bizhub C758</strong>
                                    <span>75 ppm color/B&N</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="brand-features mt-4">
                    <h4><i class="fas fa-cogs text-primary me-2"></i>Características Técnicas Destacadas</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="feature-card">
                                <i class="fas fa-shield-alt text-success"></i>
                                <h6>Seguridad Avanzada</h6>
                                <p>Autenticación biométrica, encriptación de datos y auditoría completa</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card">
                                <i class="fas fa-mobile-alt text-primary"></i>
                                <h6>Impresión Móvil</h6>
                                <p>Compatible con iOS, Android y servicios en la nube principales</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card">
                                <i class="fas fa-leaf text-success"></i>
                                <h6>Eco-Friendly</h6>
                                <p>Bajo consumo energético y materiales reciclables</p>
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
                            <h4><i class="fas fa-camera text-primary me-2"></i>Acerca de Canon</h4>
                            <p>Reconocida mundialmente por su excelencia en tecnología de imagen. Canon combina 
                            décadas de experiencia en fotografía con innovación en soluciones de oficina, 
                            ofreciendo equipos con calidad de imagen excepcional.</p>
                            
                            <div class="brand-highlights mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-star text-warning me-2"></i>Fortalezas</h5>
                                        <ul class="feature-list">
                                            <li><i class="fas fa-check text-success me-1"></i> Calidad de imagen superior</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Tecnología MEAP avanzada</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Diseño compacto y elegante</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Interfaz intuitiva</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Confiabilidad probada</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-users text-info me-2"></i>Perfecto Para</h5>
                                        <ul class="industry-list">
                                            <li><i class="fas fa-palette me-1"></i> Agencias de diseño</li>
                                            <li><i class="fas fa-camera me-1"></i> Estudios fotográficos</li>
                                            <li><i class="fas fa-briefcase me-1"></i> Oficinas medianas</li>
                                            <li><i class="fas fa-store me-1"></i> Retail y comercio</li>
                                            <li><i class="fas fa-home me-1"></i> Oficinas en casa</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="brand-stats">
                            <h5><i class="fas fa-tachometer-alt text-danger me-2"></i>Rendimiento</h5>
                            <div class="stat-grid">
                                <div class="stat-item">
                                    <span class="stat-value">55</span>
                                    <span class="stat-label">ppm máximo</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">2400</span>
                                    <span class="stat-label">dpi calidad</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">5000</span>
                                    <span class="stat-label">hojas/mes</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">10.1"</span>
                                    <span class="stat-label">pantalla táctil</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="brand-series mt-4">
                            <h5><i class="fas fa-layer-group text-primary me-2"></i>Series Disponibles</h5>
                            <div class="series-list">
                                <div class="series-item">
                                    <strong>imageRUNNER ADVANCE</strong>
                                    <span>Serie empresarial</span>
                                </div>
                                <div class="series-item">
                                    <strong>imageRUNNER C3500</strong>
                                    <span>Color multifuncional</span>
                                </div>
                                <div class="series-item">
                                    <strong>imageCLASS</strong>
                                    <span>Oficina pequeña</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="brand-technology mt-4">
                    <h4><i class="fas fa-microchip text-primary me-2"></i>Tecnologías Innovadoras</h4>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="tech-card">
                                <i class="fas fa-eye text-primary"></i>
                                <h6>MEAP Platform</h6>
                                <p>Plataforma de aplicaciones empresariales multifuncionales</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card">
                                <i class="fas fa-cloud text-info"></i>
                                <h6>uniFLOW</h6>
                                <p>Gestión de documentos y flujo de trabajo en la nube</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card">
                                <i class="fas fa-paint-brush text-warning"></i>
                                <h6>Calidad de Imagen</h6>
                                <p>Tecnología de imagen profesional heredada de cámaras</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="tech-card">
                                <i class="fas fa-compact-disc text-success"></i>
                                <h6>Toners V2</h6>
                                <p>Tecnología de toner avanzada para mejor calidad</p>
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
                            <h4><i class="fas fa-industry text-primary me-2"></i>Acerca de Ricoh</h4>
                            <p>Pionera en soluciones de oficina digital con enfoque en productividad empresarial. 
                            Ricoh se especializa en equipos robustos diseñados para entornos de alto volumen 
                            con máxima eficiencia operativa.</p>
                            
                            <div class="brand-highlights mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-shield-alt text-success me-2"></i>Ventajas Únicas</h5>
                                        <ul class="feature-list">
                                            <li><i class="fas fa-check text-success me-1"></i> Máxima durabilidad</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Alto volumen mensual</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Seguridad empresarial</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Eficiencia energética</li>
                                            <li><i class="fas fa-check text-success me-1"></i> Facilidad de mantenimiento</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-building text-primary me-2"></i>Sectores Principales</h5>
                                        <ul class="industry-list">
                                            <li><i class="fas fa-university me-1"></i> Gobierno y público</li>
                                            <li><i class="fas fa-hospital-alt me-1"></i> Sector salud</li>
                                            <li><i class="fas fa-industry me-1"></i> Manufactura</li>
                                            <li><i class="fas fa-landmark me-1"></i> Servicios financieros</li>
                                            <li><i class="fas fa-shipping-fast me-1"></i> Logística</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="brand-stats">
                            <h5><i class="fas fa-gauge-high text-warning me-2"></i>Capacidades</h5>
                            <div class="stat-grid">
                                <div class="stat-item">
                                    <span class="stat-value">60</span>
                                    <span class="stat-label">ppm velocidad</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">300K</span>
                                    <span class="stat-label">páginas/mes</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">1200</span>
                                    <span class="stat-label">dpi precisión</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">99.9%</span>
                                    <span class="stat-label">confiabilidad</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="brand-solutions mt-4">
                            <h5><i class="fas fa-puzzle-piece text-info me-2"></i>Soluciones</h5>
                            <div class="solution-list">
                                <div class="solution-item">
                                    <strong>IM Series</strong>
                                    <span>Inteligencia avanzada</span>
                                </div>
                                <div class="solution-item">
                                    <strong>MP Series</strong>
                                    <span>Multifuncional tradicional</span>
                                </div>
                                <div class="solution-item">
                                    <strong>Pro Series</strong>
                                    <span>Producción profesional</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="brand-innovation mt-4">
                    <h4><i class="fas fa-lightbulb text-warning me-2"></i>Innovaciones Ricoh</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="innovation-card">
                                <i class="fas fa-brain text-purple"></i>
                                <h6>Smart Operation Panel</h6>
                                <p>Interfaz inteligente que se adapta al usuario y optimiza flujos</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="innovation-card">
                                <i class="fas fa-lock text-danger"></i>
                                <h6>Security por Diseño</h6>
                                <p>Seguridad integrada desde el hardware hasta el software</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="innovation-card">
                                <i class="fas fa-recycle text-success"></i>
                                <h6>Sostenibilidad</h6>
                                <p>Compromiso con el medio ambiente y eficiencia energética</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="brand-support mt-4 p-3 bg-light rounded">
                    <h5><i class="fas fa-headset text-success me-2"></i>Soporte Ricoh Especializado</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="support-features">
                                <li><i class="fas fa-tools me-1"></i> Técnicos certificados por fábrica</li>
                                <li><i class="fas fa-shipping-fast me-1"></i> Repuestos originales garantizados</li>
                                <li><i class="fas fa-chart-line me-1"></i> Monitoreo proactivo remotamente</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="support-features">
                                <li><i class="fas fa-clock me-1"></i> Respuesta en menos de 4 horas</li>
                                <li><i class="fas fa-graduation-cap me-1"></i> Capacitación especializada incluida</li>
                                <li><i class="fas fa-mobile-alt me-1"></i> App móvil para soporte</li>
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
            document.getElementById('brandModalLabel').innerHTML = 
                `<img src="${brandData.logo}" alt="${brandData.title}" style="height: 30px; margin-right: 10px;">${brandData.title}`;
            document.getElementById('brandModalBody').innerHTML = brandData.content;
        }
    }
});

console.log('✅ Parte 3: Sistema de modales dinámicos para marcas inicializado');
/**
 * PARTE 4: MODALES DE PRODUCTOS Y FUNCIONALIDADES ADICIONALES
 * JavaScript para Homepage Moderna de Copier Company
 */

// =============================================
// BASE DE DATOS DE PRODUCTOS
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
                            <h4><i class="fas fa-expand-arrows-alt text-primary me-2"></i>Multifuncionales A3 Profesionales</h4>
                            <p>Diseñados para empresas con alto volumen de impresión que requieren versatilidad 
                            en formatos grandes. Ideales para oficinas corporativas, centros de copiado y 
                            departamentos de marketing que manejan documentos de gran formato.</p>
                            
                            <div class="product-capabilities mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-list-check text-success me-2"></i>Funciones Principales</h5>
                                        <ul class="capability-list">
                                            <li><i class="fas fa-print me-1"></i> Impresión A3/A4 color y B&N</li>
                                            <li><i class="fas fa-copy me-1"></i> Copiado hasta 75 ppm</li>
                                            <li><i class="fas fa-scanner me-1"></i> Escaneo dúplex automático</li>
                                            <li><i class="fas fa-fax me-1"></i> Fax (opcional)</li>
                                            <li><i class="fas fa-file-pdf me-1"></i> Escaneo directo a PDF/email</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-cogs text-warning me-2"></i>Características Avanzadas</h5>
                                        <ul class="feature-list">
                                            <li><i class="fas fa-wifi me-1"></i> Conectividad WiFi y Ethernet</li>
                                            <li><i class="fas fa-mobile-alt me-1"></i> Impresión desde móviles</li>
                                            <li><i class="fas fa-cloud me-1"></i> Integración con servicios cloud</li>
                                            <li><i class="fas fa-fingerprint me-1"></i> Autenticación biométrica</li>
                                            <li><i class="fas fa-book me-1"></i> Creación de folletos automática</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="product-specs">
                            <h5><i class="fas fa-chart-bar text-info me-2"></i>Especificaciones</h5>
                            <div class="spec-grid">
                                <div class="spec-item">
                                    <span class="spec-label">Velocidad</span>
                                    <span class="spec-value">35-75 ppm</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Resolución</span>
                                    <span class="spec-value">1200x1200 dpi</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Volumen mensual</span>
                                    <span class="spec-value">50,000-300,000</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Memoria RAM</span>
                                    <span class="spec-value">4-8 GB</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Pantalla</span>
                                    <span class="spec-value">10.1" táctil</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Formatos</span>
                                    <span class="spec-value">A6 a A3+</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="rental-info mt-4">
                            <h5><i class="fas fa-dollar-sign text-success me-2"></i>Alquiler Mensual</h5>
                            <div class="price-range">
                                <span class="price-from">Desde $299</span>
                                <span class="price-to">hasta $899</span>
                                <small class="price-note">*Incluye mantenimiento y soporte</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="product-models mt-4">
                    <h4><i class="fas fa-layer-group text-primary me-2"></i>Modelos Disponibles</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="model-card">
                                <h6>Entrada (35-45 ppm)</h6>
                                <ul class="model-features">
                                    <li>Ideal para oficinas medianas</li>
                                    <li>Funciones básicas completas</li>
                                    <li>Excelente relación precio/calidad</li>
                                </ul>
                                <div class="model-price">$299-399/mes</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="model-card popular">
                                <h6>Intermedio (50-60 ppm)</h6>
                                <ul class="model-features">
                                    <li>Más popular para empresas</li>
                                    <li>Funciones avanzadas incluidas</li>
                                    <li>Óptimo rendimiento/costo</li>
                                </ul>
                                <div class="model-price">$499-699/mes</div>
                                <span class="popular-badge">Más Popular</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="model-card">
                                <h6>Alto Rendimiento (65-75 ppm)</h6>
                                <ul class="model-features">
                                    <li>Para centros de impresión</li>
                                    <li>Máximas funcionalidades</li>
                                    <li>Volúmenes industriales</li>
                                </ul>
                                <div class="model-price">$699-899/mes</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="product-benefits mt-4 p-3 bg-light rounded">
                    <h5><i class="fas fa-star text-warning me-2"></i>¿Por Qué Elegir A3?</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="benefit-list">
                                <li><i class="fas fa-expand me-1"></i> Versatilidad de formatos</li>
                                <li><i class="fas fa-chart-pie me-1"></i> Reducción de costos operativos</li>
                                <li><i class="fas fa-users me-1"></i> Mayor productividad del equipo</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="benefit-list">
                                <li><i class="fas fa-rocket me-1"></i> Procesamiento más rápido</li>
                                <li><i class="fas fa-shield-alt me-1"></i> Funciones de seguridad avanzadas</li>
                                <li><i class="fas fa-plug me-1"></i> Conectividad empresarial</li>
                            </ul>
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
                    <div class="col-md-8">
                        <div class="product-overview">
                            <h4><i class="fas fa-desktop text-primary me-2"></i>Multifuncionales A4 Compactos</h4>
                            <p>La solución ideal para oficinas que buscan funcionalidad completa en un espacio 
                            reducido. Perfectos para pequeñas y medianas empresas que requieren calidad 
                            profesional sin comprometer el espacio de trabajo.</p>
                            
                            <div class="product-advantages mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-check-circle text-success me-2"></i>Funciones Incluidas</h5>
                                        <ul class="function-list">
                                            <li><i class="fas fa-print me-1"></i> Impresión color/B&N hasta 35 ppm</li>
                                            <li><i class="fas fa-copy me-1"></i> Copiado automático</li>
                                            <li><i class="fas fa-scan me-1"></i> Escaneo color de alta resolución</li>
                                            <li><i class="fas fa-wifi me-1"></i> Conectividad inalámbrica</li>
                                            <li><i class="fas fa-mobile-alt me-1"></i> Impresión móvil directa</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-gem text-warning me-2"></i>Ventajas Clave</h5>
                                        <ul class="advantage-list">
                                            <li><i class="fas fa-home me-1"></i> Diseño compacto para cualquier espacio</li>
                                            <li><i class="fas fa-volume-down me-1"></i> Operación silenciosa</li>
                                            <li><i class="fas fa-leaf me-1"></i> Bajo consumo energético</li>
                                            <li><i class="fas fa-user-friendly me-1"></i> Interfaz intuitiva</li>
                                            <li><i class="fas fa-tools me-1"></i> Mantenimiento simplificado</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="product-specs">
                            <h5><i class="fas fa-list text-info me-2"></i>Especificaciones</h5>
                            <div class="spec-grid">
                                <div class="spec-item">
                                    <span class="spec-label">Velocidad</span>
                                    <span class="spec-value">20-35 ppm</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Resolución</span>
                                    <span class="spec-value">600x600 dpi</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Volumen mensual</span>
                                    <span class="spec-value">5,000-50,000</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Memoria</span>
                                    <span class="spec-value">512MB-2GB</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Pantalla</span>
                                    <span class="spec-value">4.3"-7" táctil</span>
                                </div>
                                <div class="spec-item">
                                    <span class="spec-label">Dimensiones</span>
                                    <span class="spec-value">Compacto</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="compatibility mt-4">
                            <h5><i class="fas fa-puzzle-piece text-success me-2"></i>Compatibilidad</h5>
                            <div class="compatibility-grid">
                                <div class="compat-item">
                                    <i class="fab fa-windows"></i>
                                    <span>Windows</span>
                                </div>
                                <div class="compat-item">
                                    <i class="fab fa-apple"></i>
                                    <span>macOS</span>
                                </div>
                                <div class="compat-item">
                                    <i class="fab fa-linux"></i>
                                    <span>Linux</span>
                                </div>
                                <div class="compat-item">
                                    <i class="fab fa-android"></i>
                                    <span>Android</span>
                                </div>
                                <div class="compat-item">
                                    <i class="fab fa-apple"></i>
                                    <span>iOS</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="usage-scenarios mt-4">
                    <h4><i class="fas fa-building text-primary me-2"></i>Escenarios de Uso Ideales</h4>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="scenario-card">
                                <i class="fas fa-briefcase text-primary"></i>
                                <h6>Oficinas Pequeñas</h6>
                                <p>5-15 empleados con necesidades básicas de impresión</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card">
                                <i class="fas fa-home text-success"></i>
                                <h6>Home Office</h6>
                                <p>Profesionales independientes y teletrabajo</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card">
                                <i class="fas fa-store text-warning"></i>
                                <h6>Retail</h6>
                                <p>Tiendas y puntos de venta con espacio limitado</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="scenario-card">
                                <i class="fas fa-graduation-cap text-info"></i>
                                <h6>Educación</h6>
                                <p>Aulas y oficinas administrativas</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="cost-comparison mt-4 p-3 bg-light rounded">
                    <h5><i class="fas fa-calculator text-success me-2"></i>Comparación de Costos</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Alquiler vs Compra</h6>
                            <div class="cost-table">
                                <div class="cost-row">
                                    <span>Alquiler mensual:</span>
                                    <strong>$149-299</strong>
                                </div>
                                <div class="cost-row">
                                    <span>Compra equivalente:</span>
                                    <strong>$3,500-8,000</strong>
                                </div>
                                <div class="cost-row highlight">
                                    <span>Ahorro en primer año:</span>
                                    <strong>hasta 70%</strong>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>Incluido en el Alquiler</h6>
                            <ul class="included-list">
                                <li><i class="fas fa-check text-success me-1"></i> Mantenimiento completo</li>
                                <li><i class="fas fa-check text-success me-1"></i> Soporte técnico 24/7</li>
                                <li><i class="fas fa-check text-success me-1"></i> Repuestos originales</li>
                                <li><i class="fas fa-check text-success me-1"></i> Instalación profesional</li>
                                <li><i class="fas fa-check text-success me-1"></i> Capacitación del personal</li>
                            </ul>
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
                    <div class="col-md-8">
                        <div class="product-overview">
                            <h4><i class="fas fa-laser text-primary me-2"></i>Impresoras Láser Profesionales</h4>
                            <p>Tecnología láser de vanguardia para empresas que requieren velocidad excepcional 
                            y calidad consistente en grandes volúmenes. Ideales para departamentos con alta 
                            demanda de impresión especializada.</p>
                            
                            <div class="laser-benefits mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-rocket text-success me-2"></i>Ventajas del Láser</h5>
                                        <ul class="benefit-list">
                                            <li><i class="fas fa-tachometer-alt me-1"></i> Velocidad superior (hasta 75 ppm)</li>
                                            <li><i class="fas fa-dollar-sign me-1"></i> Menor costo por página</li>
                                            <li><i class="fas fa-droplet me-1"></i> Resistente al agua</li>
                                            <li><i class="fas fa-clock me-1"></i> Tiempo de calentamiento rápido</li>
                                            <li><i class="fas fa-shield-alt me-1"></i> Durabilidad excepcional</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-palette text-warning me-2"></i>Tipos Disponibles</h5>
                                        <ul class="type-list">
                                            <li><i class="fas fa-circle me-1"></i> Monocromático (B&N)</li>
                                            <li><i class="fas fa-palette me-1"></i> Color profesional</li>
                                            <li><i class="fas fa-expand me-1"></i> Gran formato (A3+)</li>
                                            <li><i class="fas fa-industry me-1"></i> Producción industrial</li>
                                            <li><i class="fas fa-network-wired me-1"></i> Red empresarial</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="performance-stats">
                            <h5><i class="fas fa-chart-line text-info me-2"></i>Rendimiento</h5>
                            <div class="stat-showcase">
                                <div class="stat-large">
                                    <span class="stat-number">75</span>
                                    <span class="stat-unit">ppm</span>
                                    <span class="stat-desc">Velocidad máxima</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Primera página:</span>
                                    <span class="stat-value">6 segundos</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Resolución:</span>
                                    <span class="stat-value">1200x1200 dpi</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">Volumen máximo:</span>
                                    <span class="stat-value">300K páginas/mes</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="connectivity mt-4">
                            <h5><i class="fas fa-wifi text-primary me-2"></i>Conectividad</h5>
                            <div class="connection-options">
                                <div class="connection-item">
                                    <i class="fas fa-ethernet"></i>
                                    <span>Ethernet Gigabit</span>
                                </div>
                                <div class="connection-item">
                                    <i class="fas fa-wifi"></i>
                                    <span>WiFi 802.11ac</span>
                                </div>
                                <div class="connection-item">
                                    <i class="fas fa-usb"></i>
                                    <span>USB 3.0</span>
                                </div>
                                <div class="connection-item">
                                    <i class="fas fa-mobile-alt"></i>
                                    <span>NFC/Mobile Print</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="laser-categories mt-4">
                    <h4><i class="fas fa-layer-group text-primary me-2"></i>Categorías de Impresoras Láser</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="category-card">
                                <div class="category-header">
                                    <i class="fas fa-circle text-dark"></i>
                                    <h5>Láser Monocromático</h5>
                                </div>
                                <div class="category-specs">
                                    <ul>
                                        <li><strong>Velocidad:</strong> 25-75 ppm</li>
                                        <li><strong>Costo por página:</strong> $0.02-0.04</li>
                                        <li><strong>Ideal para:</strong> Documentos de texto</li>
                                        <li><strong>Volumen:</strong> Alto (50K-300K/mes)</li>
                                    </ul>
                                </div>
                                <div class="category-price">
                                    <span class="price-range">$199-599/mes</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="category-card">
                                <div class="category-header">
                                    <i class="fas fa-palette text-danger"></i>
                                    <h5>Láser Color</h5>
                                </div>
                                <div class="category-specs">
                                    <ul>
                                        <li><strong>Velocidad:</strong> 20-55 ppm</li>
                                        <li><strong>Costo por página:</strong> $0.08-0.15</li>
                                        <li><strong>Ideal para:</strong> Marketing y presentaciones</li>
                                        <li><strong>Volumen:</strong> Medio-Alto (20K-150K/mes)</li>
                                    </ul>
                                </div>
                                <div class="category-price">
                                    <span class="price-range">$399-899/mes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="laser-technology mt-4 p-3 bg-light rounded">
                    <h5><i class="fas fa-cog text-primary me-2"></i>Tecnología Láser Avanzada</h5>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="tech-feature">
                                <i class="fas fa-bolt text-warning"></i>
                                <h6>Proceso Electrofotográfico</h6>
                                <p>Precisión microscópica para textos nítidos y gráficos detallados</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="tech-feature">
                                <i class="fas fa-snowflake text-info"></i>
                                <h6>Fusión Instantánea</h6>
                                <p>Sistema de calor controlado para fijación permanente</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="tech-feature">
                                <i class="fas fa-recycle text-success"></i>
                                <h6>Tóner Optimizado</h6>
                                <p>Formulación avanzada para mayor rendimiento y calidad</p>
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
                    <div class="col-md-8">
                        <div class="product-overview">
                            <h4><i class="fas fa-industry text-primary me-2"></i>Equipos Especializados</h4>
                            <p>Soluciones diseñadas para industrias específicas con requerimientos únicos. 
                            Desde impresión gran formato hasta equipos industriales de alta resistencia, 
                            tenemos la tecnología para cubrir cualquier necesidad especializada.</p>
                            
                            <div class="specialized-categories mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-expand-arrows-alt text-success me-2"></i>Gran Formato</h5>
                                        <ul class="category-features">
                                            <li><i class="fas fa-ruler me-1"></i> Plotters hasta A0</li>
                                            <li><i class="fas fa-palette me-1"></i> Impresión técnica color</li>
                                            <li><i class="fas fa-drafting-compass me-1"></i> CAD y arquitectura</li>
                                            <li><i class="fas fa-map me-1"></i> Cartografía profesional</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h5><i class="fas fa-hard-hat text-warning me-2"></i>Industrial</h5>
                                        <ul class="category-features">
                                            <li><i class="fas fa-shield-alt me-1"></i> Resistentes a ambientes extremos</li>
                                            <li><i class="fas fa-barcode me-1"></i> Impresión de etiquetas</li>
                                            <li><i class="fas fa-thermometer-half me-1"></i> Operación en alta temperatura</li>
                                            <li><i class="fas fa-tools me-1"></i> Mantenimiento especializado</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="specialization-stats">
                            <h5><i class="fas fa-target text-danger me-2"></i>Especializaciones</h5>
                            <div class="specialization-list">
                                <div class="spec-item">
                                    <i class="fas fa-building"></i>
                                    <span>Arquitectura</span>
                                </div>
                                <div class="spec-item">
                                    <i class="fas fa-hard-hat"></i>
                                    <span>Ingeniería</span>
                                </div>
                                <div class="spec-item">
                                    <i class="fas fa-palette"></i>
                                    <span>Diseño Gráfico</span>
                                </div>
                                <div class="spec-item">
                                    <i class="fas fa-industry"></i>
                                    <span>Manufactura</span>
                                </div>
                                <div class="spec-item">
                                    <i class="fas fa-shipping-fast"></i>
                                    <span>Logística</span>
                                </div>
                                <div class="spec-item">
                                    <i class="fas fa-hospital"></i>
                                    <span>Salud</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="custom-solutions mt-4">
                            <h5><i class="fas fa-cogs text-info me-2"></i>Personalización</h5>
                            <div class="custom-options">
                                <div class="custom-item">
                                    <i class="fas fa-wrench"></i>
                                    <span>Configuración específica</span>
                                </div>
                                <div class="custom-item">
                                    <i class="fas fa-code"></i>
                                    <span>Software personalizado</span>
                                </div>
                                <div class="custom-item">
                                    <i class="fas fa-plug"></i>
                                    <span>Integración sistemas</span>
                                </div>
                                <div class="custom-item">
                                    <i class="fas fa-headset"></i>
                                    <span>Soporte dedicado</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="specialized-equipment mt-4">
                    <h4><i class="fas fa-th-large text-primary me-2"></i>Tipos de Equipos Especializados</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="equipment-card">
                                <div class="equipment-icon">
                                    <i class="fas fa-map text-primary"></i>
                                </div>
                                <h6>Plotters Gran Formato</h6>
                                <div class="equipment-specs">
                                    <ul>
                                        <li><strong>Formatos:</strong> A2, A1, A0</li>
                                        <li><strong>Tecnología:</strong> Inyección de tinta</li>
                                        <li><strong>Aplicaciones:</strong> Planos, mapas, posters</li>
                                        <li><strong>Velocidad:</strong> 1-4 m²/hora</li>
                                    </ul>
                                </div>
                                <div class="equipment-price">$599-1,299/mes</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="equipment-card">
                                <div class="equipment-icon">
                                    <i class="fas fa-barcode text-success"></i>
                                </div>
                                <h6>Impresoras de Etiquetas</h6>
                                <div class="equipment-specs">
                                    <ul>
                                        <li><strong>Tipos:</strong> Térmicas, transferencia</li>
                                        <li><strong>Anchos:</strong> 2"-8" (50-200mm)</li>
                                        <li><strong>Aplicaciones:</strong> Inventario, envíos</li>
                                        <li><strong>Velocidad:</strong> 4-14 ips</li>
                                    </ul>
                                </div>
                                <div class="equipment-price">$199-599/mes</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="equipment-card">
                                <div class="equipment-icon">
                                    <i class="fas fa-photo-video text-warning"></i>
                                </div>
                                <h6>Impresoras Fotográficas</h6>
                                <div class="equipment-specs">
                                    <ul>
                                        <li><strong>Tecnología:</strong> Sublimación de tinta</li>
                                        <li><strong>Formatos:</strong> 4x6" hasta 13x19"</li>
                                        <li><strong>Aplicaciones:</strong> Fotografía profesional</li>
                                        <li><strong>Calidad:</strong> Hasta 4800 dpi</li>
                                    </ul>
                                </div>
                                <div class="equipment-price">$399-799/mes</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="equipment-card">
                                <div class="equipment-icon">
                                    <i class="fas fa-industry text-danger"></i>
                                </div>
                                <h6>Equipos Industriales</h6>
                                <div class="equipment-specs">
                                    <ul>
                                        <li><strong>Características:</strong> Resistente a polvo/agua</li>
                                        <li><strong>Temperatura:</strong> -10°C a +40°C</li>
                                        <li><strong>Aplicaciones:</strong> Manufactura, almacenes</li>
                                        <li><strong>Certificaciones:</strong> IP54, IP65</li>
                                    </ul>
                                </div>
                                <div class="equipment-price">$799-1,899/mes</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="implementation-process mt-4 p-3 bg-light rounded">
                    <h5><i class="fas fa-clipboard-check text-primary me-2"></i>Proceso de Implementación Especializada</h5>
                    <div class="process-timeline">
                        <div class="timeline-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <h6>Análisis de Necesidades</h6>
                                <p>Evaluación detallada de requerimientos específicos</p>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <h6>Diseño de Solución</h6>
                                <p>Propuesta técnica personalizada con especificaciones</p>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <h6>Implementación</h6>
                                <p>Instalación, configuración y capacitación especializada</p>
                            </div>
                        </div>
                        <div class="timeline-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <h6>Soporte Continuo</h6>
                                <p>Mantenimiento especializado y soporte técnico dedicado</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="industry-testimonial mt-4 p-3 bg-primary text-white rounded">
                    <h5><i class="fas fa-quote-left me-2"></i>Caso de Éxito</h5>
                    <blockquote class="mb-3">
                        "La implementación del plotter A0 transformó nuestro flujo de trabajo arquitectónico. 
                        Ahora podemos imprimir planos de gran formato en la oficina, reduciendo tiempos 
                        de entrega en un 60% y mejorando la calidad de presentación a clientes."
                    </blockquote>
                    <div class="testimonial-author">
                        <strong>Arq. Maria González</strong>
                        <span>- Estudio de Arquitectura Premium</span>
                    </div>
                </div>
            </div>
        `
    }
};

// =============================================
// MANEJADOR DE MODALES DE PRODUCTOS
// =============================================

document.addEventListener('click', function(e) {
    const productCard = e.target.closest('[data-product]');
    if (productCard) {
        const productType = productCard.getAttribute('data-product');
        const productData = productsContent[productType];
        
        if (productData) {
            // Actualizar contenido del modal
            document.getElementById('productModalLabel').innerHTML = 
                `<i class="fas fa-print me-2"></i>${productData.title}`;
            document.getElementById('productModalBody').innerHTML = productData.content;
        }
    }
});

// =============================================
// FUNCIONALIDADES ADICIONALES
// =============================================

// Sistema de notificaciones toast
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} show`;
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <strong class="me-auto">Copier Company</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Tracking de interacciones para analytics
function trackInteraction(action, category, label = '') {
    // Aquí puedes integrar con Google Analytics, Mixpanel, etc.
    console.log(`Analytics: ${action} - ${category} - ${label}`);
    
    // Ejemplo para Google Analytics 4
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            event_category: category,
            event_label: label
        });
    }
}

// Mejoras en los botones CTA
document.addEventListener('click', function(e) {
    const button = e.target.closest('.btn-primary-modern, .btn-cta-primary, .btn-cta-secondary');
    if (button) {
        // Añadir efecto visual
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 150);
        
        // Tracking
        trackInteraction('click', 'cta_button', button.textContent.trim());
        
        // Mostrar feedback
        if (button.href && button.href.includes('cotizacion')) {
            showToast('Redirigiendo al formulario de cotización...', 'info');
        }
    }
});

// Lazy loading para imágenes
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Smooth scroll para navegación interna
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Inicializar funcionalidades adicionales
document.addEventListener('DOMContentLoaded', function() {
    initLazyLoading();
    initSmoothScroll();
});

console.log('✅ Parte 4: Modales de productos y funcionalidades adicionales inicializados');
/**
 * PARTE 5 FINAL: INTEGRACIÓN COMPLETA Y OPTIMIZACIONES
 * JavaScript para Homepage Moderna de Copier Company
 */

// =============================================
// SISTEMA DE PERFORMANCE Y OPTIMIZACIÓN
// =============================================

// Performance monitoring
const performanceMonitor = {
    init: function() {
        // Medir tiempo de carga inicial
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`⚡ Página cargada en ${loadTime.toFixed(2)}ms`);
            
            // Enviar métricas si hay analytics configurado
            if (typeof gtag !== 'undefined') {
                gtag('event', 'page_load_time', {
                    custom_parameter: loadTime
                });
            }
        });
        
        // Detectar problemas de rendimiento
        this.detectPerformanceIssues();
    },
    
    detectPerformanceIssues: function() {
        // Detectar imágenes que tardan mucho en cargar
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            const startTime = performance.now();
            img.onload = () => {
                const loadTime = performance.now() - startTime;
                if (loadTime > 2000) {
                    console.warn(`⚠️ Imagen lenta: ${img.src} (${loadTime.toFixed(2)}ms)`);
                }
            };
        });
    }
};

// =============================================
// SISTEMA DE FORMULARIOS INTELIGENTE
// =============================================

const smartForms = {
    init: function() {
        this.setupFormValidation();
        this.setupProgressiveEnhancement();
        this.setupAutoSave();
    },
    
    setupFormValidation: function() {
        // Validación en tiempo real para formularios
        document.addEventListener('input', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                smartForms.validateField(e.target);
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
        const existingFeedback = field.parentNode.querySelector('.field-feedback');
        if (existingFeedback) existingFeedback.remove();
        
        // Añadir clases de estado
        field.classList.remove('is-valid', 'is-invalid');
        if (field.value.trim() !== '') {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        }
        
        // Mostrar mensaje si hay error
        if (!isValid && message) {
            const feedback = document.createElement('div');
            feedback.className = 'field-feedback text-danger small mt-1';
            feedback.textContent = message;
            field.parentNode.appendChild(feedback);
        }
    },
    
    setupProgressiveEnhancement: function() {
        // Mejorar formularios existentes progresivamente
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Añadir indicador de envío
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
                    submitBtn.disabled = true;
                }
            });
        });
    },
    
    setupAutoSave: function() {
        // Guardar datos del formulario automáticamente
        const formFields = document.querySelectorAll('input, textarea, select');
        formFields.forEach(field => {
            // Cargar valor guardado
            const savedValue = localStorage.getItem(`form_${field.name}`);
            if (savedValue && field.type !== 'password') {
                field.value = savedValue;
            }
            
            // Guardar cambios automáticamente
            field.addEventListener('input', () => {
                if (field.type !== 'password') {
                    localStorage.setItem(`form_${field.name}`, field.value);
                }
            });
        });
    }
};

// =============================================
// SISTEMA DE CHAT BOT BÁSICO
// =============================================

const chatBot = {
    isOpen: false,
    
    init: function() {
        this.createChatWidget();
        this.setupEventListeners();
    },
    
    createChatWidget: function() {
        const chatWidget = document.createElement('div');
        chatWidget.id = 'chat-widget';
        chatWidget.innerHTML = `
            <div class="chat-bubble" id="chat-bubble">
                <i class="fas fa-comments"></i>
                <span class="chat-notification">¿Necesitas ayuda?</span>
            </div>
            <div class="chat-window" id="chat-window" style="display: none;">
                <div class="chat-header">
                    <h6><i class="fas fa-robot me-2"></i>Asistente Virtual</h6>
                    <button class="chat-close" id="chat-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="chat-messages" id="chat-messages">
                    <div class="bot-message">
                        <div class="message-content">
                            ¡Hola! 👋 Soy tu asistente virtual. ¿En qué puedo ayudarte?
                            <div class="quick-options">
                                <button class="quick-btn" data-action="cotizacion">💰 Solicitar cotización</button>
                                <button class="quick-btn" data-action="productos">📱 Ver productos</button>
                                <button class="quick-btn" data-action="contacto">📞 Información de contacto</button>
                                <button class="quick-btn" data-action="soporte">🔧 Soporte técnico</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chat-input">
                    <input type="text" id="chat-input" placeholder="Escribe tu pregunta...">
                    <button id="chat-send"><i class="fas fa-paper-plane"></i></button>
                </div>
            </div>
        `;
        
        document.body.appendChild(chatWidget);
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
            if (e.target.classList.contains('quick-btn')) {
                this.handleQuickAction(e.target.dataset.action);
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
            
            // Focus en input
            setTimeout(() => {
                document.getElementById('chat-input').focus();
            }, 100);
        }
    },
    
    sendMessage: function() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (message) {
            this.addMessage(message, 'user');
            input.value = '';
            
            // Simular respuesta del bot
            setTimeout(() => {
                const response = this.getBotResponse(message);
                this.addMessage(response, 'bot');
            }, 1000);
        }
    },
    
    addMessage: function(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `${sender}-message`;
        
        if (sender === 'user') {
            messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
        } else {
            messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },
    
    getBotResponse: function(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('precio') || lowerMessage.includes('costo') || lowerMessage.includes('cotiz')) {
            return `💰 Los precios de alquiler varían según el equipo:
                    <br>• A4: $149-299/mes
                    <br>• A3: $299-899/mes
                    <br>• Láser: $199-899/mes
                    <br><br>¿Te gustaría una cotización personalizada? 
                    <a href="/cotizacion/form" class="chat-link">Solicitar aquí</a>`;
        }
        
        if (lowerMessage.includes('producto') || lowerMessage.includes('equipo') || lowerMessage.includes('fotocopiadora')) {
            return `📱 Ofrecemos varios tipos de equipos:
                    <br>• Multifuncionales A3 y A4
                    <br>• Impresoras láser color y B&N
                    <br>• Equipos especializados
                    <br>• Marcas: Konica Minolta, Canon, Ricoh
                    <br><br>¿Qué tipo de equipo necesitas?`;
        }
        
        if (lowerMessage.includes('mantenimiento') || lowerMessage.includes('reparaci') || lowerMessage.includes('soporte')) {
            return `🔧 Nuestro servicio incluye:
                    <br>• Mantenimiento preventivo y correctivo
                    <br>• Soporte técnico 24/7
                    <br>• Repuestos originales
                    <br>• Tiempo de respuesta: 4 horas máximo
                    <br><br>¿Necesitas ayuda con algún equipo?`;
        }
        
        if (lowerMessage.includes('contacto') || lowerMessage.includes('teléfono') || lowerMessage.includes('dirección')) {
            return `📞 Puedes contactarnos:
                    <br>• Teléfono: (01) 975399303
                    <br>• WhatsApp: <a href="https://wa.me/51975399303" class="chat-link">975 399 303</a>
                    <br>• Email: info@copiercompany.com
                    <br>• Horario: Lun-Vie 8AM-6PM, Sáb 8AM-1PM`;
        }
        
        return `Gracias por tu consulta. Te recomiendo:
                <br>• <a href="/cotizacion/form" class="chat-link">Solicitar cotización gratuita</a>
                <br>• <a href="/contactus" class="chat-link">Contactar con un asesor</a>
                <br>• <a href="https://wa.me/51975399303" class="chat-link">Escribir por WhatsApp</a>
                <br><br>¿Hay algo específico en lo que pueda ayudarte?`;
    },
    
    handleQuickAction: function(action) {
        switch (action) {
            case 'cotizacion':
                this.addMessage('Quiero solicitar una cotización', 'user');
                setTimeout(() => {
                    this.addMessage(`¡Perfecto! 💰 Para una cotización personalizada necesito algunos datos:
                        <br>• Tipo de equipo que necesitas
                        <br>• Volumen de impresión mensual aproximado
                        <br>• Funciones específicas requeridas
                        <br><br><a href="/cotizacion/form" class="chat-link">Completa el formulario aquí</a> 
                        o cuéntame más detalles.`, 'bot');
                }, 1000);
                break;
                
            case 'productos':
                this.addMessage('¿Qué productos tienen disponibles?', 'user');
                setTimeout(() => {
                    this.addMessage(this.getBotResponse('productos'), 'bot');
                }, 1000);
                break;
                
            case 'contacto':
                this.addMessage('Necesito información de contacto', 'user');
                setTimeout(() => {
                    this.addMessage(this.getBotResponse('contacto'), 'bot');
                }, 1000);
                break;
                
            case 'soporte':
                this.addMessage('¿Cómo funciona el soporte técnico?', 'user');
                setTimeout(() => {
                    this.addMessage(this.getBotResponse('soporte'), 'bot');
                }, 1000);
                break;
        }
    }
};

// =============================================
// SISTEMA DE ANALYTICS AVANZADO
// =============================================

const advancedAnalytics = {
    init: function() {
        this.trackUserBehavior();
        this.trackScrollDepth();
        this.trackTimeOnSections();
        this.setupHeatmapTracking();
    },
    
    trackUserBehavior: function() {
        // Tracking de clics en elementos importantes
        document.addEventListener('click', function(e) {
            const element = e.target.closest('[data-track]');
            if (element) {
                const trackData = element.dataset.track;
                console.log(`📊 User Action: ${trackData}`);
                
                // Enviar a analytics
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'user_interaction', {
                        interaction_type: trackData,
                        element_text: element.textContent.trim().substring(0, 100)
                    });
                }
            }
        });
    },
    
    trackScrollDepth: function() {
        let maxScroll = 0;
        const milestones = [25, 50, 75, 90, 100];
        const triggered = new Set();
        
        window.addEventListener('scroll', () => {
            const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            
            if (scrollPercent > maxScroll) {
                maxScroll = scrollPercent;
                
                milestones.forEach(milestone => {
                    if (scrollPercent >= milestone && !triggered.has(milestone)) {
                        triggered.add(milestone);
                        console.log(`📏 Scroll Depth: ${milestone}%`);
                        
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'scroll_depth', {
                                scroll_depth: milestone
                            });
                        }
                    }
                });
            }
        });
    },
    
    trackTimeOnSections: function() {
        const sections = document.querySelectorAll('section[id]');
        const sectionTimes = new Map();
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const sectionId = entry.target.id;
                
                if (entry.isIntersecting) {
                    sectionTimes.set(sectionId, Date.now());
                } else if (sectionTimes.has(sectionId)) {
                    const timeSpent = Date.now() - sectionTimes.get(sectionId);
                    if (timeSpent > 3000) { // Más de 3 segundos
                        console.log(`⏱️ Time on ${sectionId}: ${Math.round(timeSpent/1000)}s`);
                        
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'section_engagement', {
                                section_name: sectionId,
                                time_spent: Math.round(timeSpent/1000)
                            });
                        }
                    }
                    sectionTimes.delete(sectionId);
                }
            });
        }, { threshold: 0.5 });
        
        sections.forEach(section => observer.observe(section));
    },
    
    setupHeatmapTracking: function() {
        // Simular tracking de heatmap (clicks)
        document.addEventListener('click', function(e) {
            const clickData = {
                x: e.clientX,
                y: e.clientY,
                element: e.target.tagName,
                timestamp: Date.now()
            };
            
            // Guardar datos de clicks para análisis
            const clicks = JSON.parse(localStorage.getItem('heatmap_clicks') || '[]');
            clicks.push(clickData);
            
            // Mantener solo los últimos 100 clicks
            if (clicks.length > 100) {
                clicks.splice(0, clicks.length - 100);
            }
            
            localStorage.setItem('heatmap_clicks', JSON.stringify(clicks));
        });
    }
};

// =============================================
// ESTILOS CSS ADICIONALES PARA NUEVAS FUNCIONES
// =============================================

const additionalStyles = `
/* Chat Widget Styles */
#chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.chat-bubble {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #007bff, #0056b3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(0,123,255,0.3);
    transition: all 0.3s ease;
    position: relative;
}

.chat-bubble:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 25px rgba(0,123,255,0.4);
}

.chat-notification {
    position: absolute;
    right: 70px;
    top: 50%;
    transform: translateY(-50%);
    background: white;
    color: #333;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 14px;
    white-space: nowrap;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    opacity: 0;
    animation: slideInNotification 3s ease-in-out 2s forwards;
}

@keyframes slideInNotification {
    0%, 80% { opacity: 0; transform: translateY(-50%) translateX(10px); }
    10%, 70% { opacity: 1; transform: translateY(-50%) translateX(0); }
    100% { opacity: 0; transform: translateY(-50%) translateX(10px); }
}

.chat-window {
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.chat-header {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-close {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 16px;
}

.chat-messages {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    background: #f8f9fa;
}

.bot-message, .user-message {
    margin-bottom: 15px;
}

.user-message {
    text-align: right;
}

.user-message .message-content {
    background: #007bff;
    color: white;
    display: inline-block;
    padding: 10px 15px;
    border-radius: 18px 18px 5px 18px;
    max-width: 80%;
}

.bot-message .message-content {
    background: white;
    border: 1px solid #e9ecef;
    display: inline-block;
    padding: 10px 15px;
    border-radius: 18px 18px 18px 5px;
    max-width: 80%;
    line-height: 1.4;
}

.quick-options {
    margin-top: 10px;
}

.quick-btn {
    display: block;
    width: 100%;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 10px;
    cursor: pointer;
    font-size: 12px;
    text-align: left;
    transition: all 0.2s ease;
}

.quick-btn:hover {
    background: #e9ecef;
    transform: translateX(5px);
}

.chat-input {
    display: flex;
    padding: 15px;
    background: white;
    border-top: 1px solid #e9ecef;
}

#chat-input {
    flex: 1;
    border: 1px solid #e9ecef;
    border-radius: 25px;
    padding: 10px 15px;
    outline: none;
    font-size: 14px;
}

#chat-send {
    background: #007bff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    margin-left: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.chat-link {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}

.chat-link:hover {
    text-decoration: underline;
}

/* Form validation styles */
.field-feedback {
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.is-valid {
    border-color: #28a745;
}

.is-invalid {
    border-color: #dc3545;
}

/* Toast notifications */
.toast {
    background: white;
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px;
    margin-bottom: 10px;
    overflow: hidden;
}

.toast-success { border-left: 4px solid #28a745; }
.toast-error { border-left: 4px solid #dc3545; }
.toast-info { border-left: 4px solid #007bff; }

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
}
`;

// =============================================
// INICIALIZACIÓN FINAL DEL SISTEMA
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inyectar estilos adicionales
    const styleSheet = document.createElement('style');
    styleSheet.textContent = additionalStyles;
    document.head.appendChild(styleSheet);
    
    // Inicializar todos los sistemas
    try {
        performanceMonitor.init();
        console.log('✅ Performance Monitor inicializado');
        
        smartForms.init();
        console.log('✅ Smart Forms inicializado');
        
        chatBot.init();
        console.log('✅ Chat Bot inicializado');
        
        advancedAnalytics.init();
        console.log('✅ Advanced Analytics inicializado');
        
        // Configurar observador de mutaciones para contenido dinámico
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // Re-inicializar funcionalidades para nuevo contenido
                    const newElements = mutation.addedNodes;
                    newElements.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
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
        
        console.log('🚀 SISTEMA COMPLETO INICIALIZADO EXITOSAMENTE');
        console.log('📊 Todas las funcionalidades están activas');
        console.log('⚡ Performance optimizado');
        console.log('🤖 Chat bot disponible');
        console.log('📈 Analytics configurado');
        
        // Mostrar mensaje de bienvenida en consola
        console.log(`
        %c🏢 COPIER COMPANY HOMEPAGE 
        %c✨ Sistema JavaScript Completo v1.0
        %c🔧 Desarrollado para Odoo
        `, 
        'color: #007bff; font-size: 16px; font-weight: bold;',
        'color: #28a745; font-size: 14px;',
        'color: #6c757d; font-size: 12px;'
        );
        
    } catch (error) {
        console.error('❌ Error al inicializar el sistema:', error);
    }
});

// Exportar funciones principales para uso externo
window.CopierCompanyJS = {
    showToast,
    trackInteraction,
    performanceMonitor,
    smartForms,
    chatBot,
    advancedAnalytics
};

// =============================================
// SERVICE WORKER PARA PWA (OPCIONAL)
// =============================================

// Registrar service worker si está disponible
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('✅ Service Worker registrado:', registration.scope);
            })
            .catch(function(error) {
                console.log('❌ Error al registrar Service Worker:', error);
            });
    });
}

console.log('✅ Parte 5 FINAL: Sistema completo cargado e inicializado');