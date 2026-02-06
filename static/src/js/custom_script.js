// ============================================================================
// BÚSQUEDA DE CLIENTE CON BOTÓN
// ============================================================================

function buscarCliente() {
    const errorElement = document.getElementById('error_message');
    const successElement = document.getElementById('success_message');
    const warningElement = document.getElementById('warning_message');
    const clienteName = document.getElementById('cliente_name');
    const telefono = document.getElementById('telefono');
    const correo = document.getElementById('correo');
    const clienteId = document.getElementById('cliente_id');
    const contacto = document.getElementById('contacto');
    const loadingSpinner = document.getElementById('loading_spinner');
    const identificacionInput = document.getElementById('identificacion');
    const btnBuscar = document.getElementById('btn_buscar');

    // Limpiar mensajes previos
    errorElement.classList.add('d-none');
    if (successElement) successElement.classList.add('d-none');
    if (warningElement) warningElement.classList.add('d-none');

    const tipoIdentificacion = document.getElementById('tipo_identificacion').value;
    const identificacion = identificacionInput.value.trim();

    if (!identificacion) {
        mostrarError('Por favor, ingrese el número de identificación.');
        return;
    }

    // Validar longitud según tipo
    if (tipoIdentificacion === '6' && identificacion.length !== 11) {
        mostrarError('El RUC debe tener 11 dígitos.');
        return;
    }
    if (tipoIdentificacion === '1' && identificacion.length !== 8) {
        mostrarError('El DNI debe tener 8 dígitos.');
        return;
    }

    // Mostrar indicador de carga
    if (loadingSpinner) loadingSpinner.classList.remove('d-none');
    if (btnBuscar) {
        btnBuscar.disabled = true;
        btnBuscar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Buscando...';
    }
    
    // Deshabilitar campos durante la búsqueda
    identificacionInput.disabled = true;
    document.getElementById('tipo_identificacion').disabled = true;

    fetch('/copier_company/buscar_cliente', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
                tipo_identificacion: tipoIdentificacion,
                identificacion: identificacion
            },
            id: null
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Respuesta del servidor: ", data);
        
        if (data.result && data.result.success) {
            const result = data.result;
            
            if (result.found) {
                // Se encontraron datos
                const clienteData = result.data;
                
                rellenarCamposConAnimacion({
                    id: clienteData.id,
                    name: clienteData.name,
                    phone: clienteData.phone || clienteData.mobile || '',
                    email: clienteData.email || ''
                });
                
                // Mensaje según la fuente
                if (result.source === 'database') {
                    mostrarExito('✓ Cliente encontrado en la base de datos.');
                } else if (result.source === 'api') {
                    mostrarExito('✓ Cliente encontrado en SUNAT/RENIEC y guardado.');
                }
                
                // Deshabilitar campos de cliente (ya están completos)
                clienteName.readOnly = true;
                
            } else {
                // No se encontró, permitir ingreso manual
                limpiarCamposCliente();
                mostrarAdvertencia(result.message || 'No se encontraron datos. Ingrese la información manualmente.');
                
                // Habilitar campos para ingreso manual
                clienteName.readOnly = false;
                clienteName.focus();
            }
            
            // Actualizar progreso
            setTimeout(actualizarProgreso, 100);
            
        } else {
            limpiarCamposCliente();
            mostrarError(data.result?.message || 'Error al buscar cliente.');
            clienteName.readOnly = false;
        }
    })
    .catch(error => {
        console.error('Error al procesar la solicitud:', error);
        limpiarCamposCliente();
        mostrarError('Error de conexión. Por favor, ingrese los datos manualmente.');
        clienteName.readOnly = false;
    })
    .finally(() => {
        // Ocultar indicador de carga
        if (loadingSpinner) loadingSpinner.classList.add('d-none');
        if (btnBuscar) {
            btnBuscar.disabled = false;
            btnBuscar.innerHTML = '<i class="fas fa-search me-2"></i>Buscar';
        }
        
        // Rehabilitar campos
        identificacionInput.disabled = false;
        document.getElementById('tipo_identificacion').disabled = false;
    });
}

// ============================================================================
// FUNCIONES DE MENSAJES
// ============================================================================

function mostrarAdvertencia(mensaje) {
    const warningElement = document.getElementById('warning_message');
    const warningText = document.getElementById('warning_text');
    
    if (warningElement) {
        if (warningText) {
            warningText.textContent = mensaje;
        } else {
            warningElement.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>' + mensaje;
        }
        
        warningElement.classList.remove('d-none');
        warningElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        setTimeout(() => {
            warningElement.classList.add('d-none');
        }, 8000);
    }
}

function mostrarError(mensaje) {
    const errorElement = document.getElementById('error_message');
    const errorText = document.getElementById('error_text');
    
    if (errorElement) {
        if (errorText) {
            errorText.textContent = mensaje;
        } else {
            errorElement.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>' + mensaje;
        }
        
        errorElement.classList.remove('d-none');
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        setTimeout(() => {
            errorElement.classList.add('d-none');
        }, 8000);
    }
}

function mostrarExito(mensaje) {
    const successElement = document.getElementById('success_message');
    const successText = document.getElementById('success_text');
    
    if (successElement) {
        if (successText) {
            successText.textContent = mensaje;
        } else {
            successElement.innerHTML = '<i class="fas fa-check-circle me-2"></i>' + mensaje;
        }
        
        successElement.classList.remove('d-none');
        
        setTimeout(() => {
            successElement.classList.add('d-none');
        }, 4000);
    }
}

// ============================================================================
// FUNCIONES DE UTILIDAD
// ============================================================================

function rellenarCamposConAnimacion(datos) {
    const campos = [
        { element: document.getElementById('cliente_id'), value: datos.id },
        { element: document.getElementById('cliente_name'), value: datos.name },
        { element: document.getElementById('telefono'), value: datos.phone },
        { element: document.getElementById('correo'), value: datos.email },
        { element: document.getElementById('contacto'), value: datos.name }
    ];

    campos.forEach((campo, index) => {
        if (campo.element) {
            setTimeout(() => {
                campo.element.value = campo.value;
                
                // Efecto visual de relleno
                campo.element.style.transition = 'background-color 0.3s ease';
                campo.element.style.backgroundColor = '#d4edda';
                
                // Trigger del evento change para actualizar validaciones
                campo.element.dispatchEvent(new Event('change', { bubbles: true }));
                campo.element.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Restaurar color original después de un tiempo
                setTimeout(() => {
                    campo.element.style.backgroundColor = '';
                }, 1500);
                
            }, index * 150);
        }
    });
}

function limpiarCamposCliente() {
    const campos = ['cliente_id', 'cliente_name', 'telefono', 'correo', 'contacto'];
    
    campos.forEach(campoId => {
        const campo = document.getElementById(campoId);
        if (campo) {
            campo.value = '';
            campo.dispatchEvent(new Event('change', { bubbles: true }));
            campo.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
}

// ============================================================================
// INICIALIZACIÓN DEL FORMULARIO
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado - Inicializando formulario...');
    
    // Inicializar validación del formulario
    initFormValidation();
    
    // Inicializar validaciones en tiempo real
    initRealTimeValidation();
    
    // Inicializar tooltips
    initTooltips();
    
    // Inicializar progreso del formulario
    initFormProgress();
    
    // Inicializar mejoras UX
    setTimeout(mejorarExperienciaUsuario, 500);
    
    console.log('Formulario inicializado correctamente');
});

// ============================================================================
// VALIDACIÓN DEL FORMULARIO
// ============================================================================

function initFormValidation() {
    const form = document.getElementById('copier_form');
    if (!form) {
        console.warn('Formulario no encontrado');
        return;
    }
    
    form.addEventListener('submit', function(event) {
        console.log('Enviando formulario...');
        
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            
            // Mostrar mensaje de error
            mostrarError('Por favor complete todos los campos obligatorios correctamente.');
            
            // Scroll al primer error
            const firstError = form.querySelector('.is-invalid, :invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => firstError.focus(), 500);
            }
        } else {
            // Mostrar loading en el botón
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalHTML = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
                submitBtn.disabled = true;
                
                // Restaurar botón en caso de error (fallback)
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.innerHTML = originalHTML;
                        submitBtn.disabled = false;
                    }
                }, 10000);
            }
            
            mostrarExito('Enviando cotización, por favor espere...');
        }
        
        form.classList.add('was-validated');
    }, false);
}

// ============================================================================
// VALIDACIONES EN TIEMPO REAL
// ============================================================================

function initRealTimeValidation() {
    // Validación en tiempo real para email
    const emailInput = document.getElementById('correo');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const email = this.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.setCustomValidity('Por favor ingrese un email válido');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Validación para teléfono (solo números y algunos caracteres especiales)
    const telefonoInput = document.getElementById('telefono');
    if (telefonoInput) {
        telefonoInput.addEventListener('input', function() {
            // Permitir solo números, espacios, guiones y paréntesis
            let value = this.value.replace(/[^0-9\s\-\(\)\+]/g, '');
            
            // Validar longitud mínima
            if (value.length >= 6 && value.length <= 15) {
                this.setCustomValidity('');
            } else if (value.length > 0) {
                this.setCustomValidity('El teléfono debe tener entre 6 y 15 dígitos');
            }
            
            this.value = value;
        });
    }

    // Validación para identificación (solo números)
    const identificacionInput = document.getElementById('identificacion');
    if (identificacionInput) {
        identificacionInput.addEventListener('input', function() {
            // Permitir solo números
            let value = this.value.replace(/[^0-9]/g, '');
            
            // Validar según tipo de identificación
            const tipoId = document.getElementById('tipo_identificacion').value;
            if (tipoId === '6' && value.length === 11) { // RUC
                this.setCustomValidity('');
            } else if (tipoId === '1' && value.length === 8) { // DNI
                this.setCustomValidity('');
            } else if (value.length > 0) {
                const mensaje = tipoId === '6' ? 'El RUC debe tener 11 dígitos' : 'El DNI debe tener 8 dígitos';
                this.setCustomValidity(mensaje);
            }
            
            this.value = value;
        });
    }

    // Validación para volúmenes (números positivos)
    const volumenes = ['volumen_mensual_color', 'volumen_mensual_bn'];
    volumenes.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', function() {
                const value = parseInt(this.value);
                if (isNaN(value) || value < 0) {
                    this.setCustomValidity('Ingrese un número válido mayor o igual a 0');
                } else if (value > 100000) {
                    this.setCustomValidity('El volumen parece muy alto, verifique el valor');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    });
}

// ============================================================================
// TOOLTIPS
// ============================================================================

function initTooltips() {
    const tooltips = [
        {
            element: 'volumen_mensual_color',
            message: 'Ingrese el número aproximado de páginas a color que imprime mensualmente'
        },
        {
            element: 'volumen_mensual_bn',
            message: 'Ingrese el número aproximado de páginas en blanco y negro que imprime mensualmente'
        },
        {
            element: 'detalles',
            message: 'Especifique requisitos especiales como conectividad, funciones adicionales, ubicación, etc.'
        },
        {
            element: 'identificacion',
            message: 'Ingrese RUC (11 dígitos) o DNI (8 dígitos) según el tipo seleccionado'
        }
    ];

    tooltips.forEach(tooltip => {
        const element = document.getElementById(tooltip.element);
        if (element) {
            element.setAttribute('title', tooltip.message);
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
        }
    });

    // Inicializar tooltips de Bootstrap si está disponible
    setTimeout(() => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            console.log('Tooltips inicializados:', tooltipList.length);
        }
    }, 500);
}

// ============================================================================
// PROGRESO DEL FORMULARIO
// ============================================================================

let actualizarProgreso;

function initFormProgress() {
    const formInputs = document.querySelectorAll('#copier_form input, #copier_form select, #copier_form textarea');
    const progressBar = document.getElementById('form_progress');
    const progressText = document.getElementById('progress_text');
    
    if (!progressBar) {
        console.warn('Barra de progreso no encontrada');
        return;
    }

    actualizarProgreso = function() {
        const requiredInputs = document.querySelectorAll('#copier_form input[required], #copier_form select[required], #copier_form textarea[required]');
        const total = requiredInputs.length;
        let completed = 0;

        requiredInputs.forEach(input => {
            if (input.type === 'checkbox') {
                if (input.checked) completed++;
            } else if (input.value.trim() !== '') {
                completed++;
            }
        });

        const percentage = Math.floor((completed / total) * 100);
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        
        if (progressText) {
            progressText.textContent = percentage + '%';
        }

        // Cambiar color de la barra según progreso
        if (percentage < 30) {
            progressBar.style.background = 'linear-gradient(45deg, #ff6b6b 0%, #ff8e8e 100%)';
        } else if (percentage < 70) {
            progressBar.style.background = 'linear-gradient(45deg, #ffd93d 0%, #ffed4a 100%)';
        } else {
            progressBar.style.background = 'linear-gradient(45deg, #6bcf7f 0%, #4bcf7f 100%)';
        }

        console.log(`Progreso del formulario: ${percentage}% (${completed}/${total} campos completados)`);
        return percentage;
    };

    // Agregar listeners para actualizar progreso
    formInputs.forEach(input => {
        ['change', 'input', 'blur'].forEach(event => {
            input.addEventListener(event, actualizarProgreso);
        });
        
        // Efectos visuales en focus
        input.addEventListener('focus', function() {
            const floating = this.closest('.form-floating');
            if (floating) {
                floating.style.transform = 'scale(1.02)';
                floating.style.transition = 'transform 0.2s ease';
            }
        });
        
        input.addEventListener('blur', function() {
            const floating = this.closest('.form-floating');
            if (floating) {
                floating.style.transform = 'scale(1)';
            }
        });
    });

    // Inicializar progreso
    setTimeout(actualizarProgreso, 100);
}

// ============================================================================
// MEJORAS DE EXPERIENCIA DE USUARIO
// ============================================================================

function mejorarExperienciaUsuario() {
    // Animación suave para las secciones del formulario
    const sections = document.querySelectorAll('.form-section');
    sections.forEach((section, index) => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'all 0.6s ease';
        
        setTimeout(() => {
            section.style.opacity = '1';
            section.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

// ============================================================================
// FUNCIÓN PARA RESETEAR EL FORMULARIO
// ============================================================================

function resetearFormulario() {
    if (confirm('¿Está seguro de que desea limpiar todo el formulario?')) {
        const form = document.getElementById('copier_form');
        if (form) {
            form.reset();
            form.classList.remove('was-validated');
            
            // Limpiar mensajes
            const errorElement = document.getElementById('error_message');
            const successElement = document.getElementById('success_message');
            const warningElement = document.getElementById('warning_message');
            
            if (errorElement) errorElement.classList.add('d-none');
            if (successElement) successElement.classList.add('d-none');
            if (warningElement) warningElement.classList.add('d-none');
            
            // Resetear progreso
            if (typeof actualizarProgreso === 'function') {
                setTimeout(actualizarProgreso, 100);
            }
            
            mostrarExito('Formulario reiniciado correctamente.');
        }
    }
}