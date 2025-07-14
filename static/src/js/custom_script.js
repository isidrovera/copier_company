// Función mejorada para obtener datos del cliente con efectos visuales
function obtenerDatosCliente() {
    const errorElement = document.getElementById('error_message');
    const successElement = document.getElementById('success_message');
    const clienteName = document.getElementById('cliente_name');
    const telefono = document.getElementById('telefono');
    const correo = document.getElementById('correo');
    const clienteId = document.getElementById('cliente_id');
    const loadingSpinner = document.getElementById('loading_spinner');
    const identificacionInput = document.getElementById('identificacion');

    // Verificar que los elementos existen en el DOM
    if (!errorElement || !clienteName || !telefono || !correo || !clienteId) {
        console.error('Uno o más elementos del DOM no se encontraron.');
        return;
    }

    // Limpiar mensajes previos
    errorElement.classList.add('d-none');
    if (successElement) {
        successElement.classList.add('d-none');
    }

    const tipoIdentificacion = document.getElementById('tipo_identificacion').value;
    const identificacion = identificacionInput.value.trim();

    console.log("Tipo de Identificación: ", tipoIdentificacion);
    console.log("Identificación: ", identificacion);

    if (!identificacion) {
        mostrarError('Por favor, ingrese el número de identificación.');
        return;
    }

    // Mostrar indicador de carga
    if (loadingSpinner) {
        loadingSpinner.classList.remove('d-none');
    }
    
    // Deshabilitar campo durante la búsqueda
    identificacionInput.disabled = true;
    
    // Agregar clase de loading al campo
    identificacionInput.classList.add('loading');

    fetch('/copier_company/get_customer_data', {
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
    .then(response => response.json())
    .then(data => {
        console.log("Datos procesados: ", data);
        
        if (data.result && data.result.result && data.result.result.success) {
            console.log("Cliente encontrado: ", data.result.result.name);
            
            // Rellenar campos con animación
            rellenarCamposConAnimacion({
                name: data.result.result.name,
                phone: data.result.result.phone || '',
                email: data.result.result.email || '',
                id: data.result.result.id
            });
            
            // Mostrar mensaje de éxito
            mostrarExito('Cliente encontrado exitosamente.');
            
        } else {
            console.warn('No se encontraron datos:', data);
            limpiarCamposCliente();
            mostrarError('No se encontraron datos para la identificación proporcionada.');
        }
    })
    .catch(error => {
        console.error('Error al procesar la solicitud:', error);
        limpiarCamposCliente();
        mostrarError('Error al procesar la solicitud. Por favor, intente nuevamente.');
    })
    .finally(() => {
        // Ocultar indicador de carga
        if (loadingSpinner) {
            loadingSpinner.classList.add('d-none');
        }
        
        // Rehabilitar campo
        identificacionInput.disabled = false;
        identificacionInput.classList.remove('loading');
    });
}

// Función para mostrar errores con estilo
function mostrarError(mensaje) {
    const errorElement = document.getElementById('error_message');
    if (errorElement) {
        errorElement.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${mensaje}`;
        errorElement.classList.remove('d-none');
        
        // Scroll suave al error
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            errorElement.classList.add('d-none');
        }, 5000);
    }
}

// Función para mostrar mensajes de éxito
function mostrarExito(mensaje) {
    const successElement = document.getElementById('success_message');
    if (successElement) {
        successElement.innerHTML = `<i class="fas fa-check-circle me-2"></i>${mensaje}`;
        successElement.classList.remove('d-none');
        
        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            successElement.classList.add('d-none');
        }, 3000);
    }
}

// Función para rellenar campos con animación suave
function rellenarCamposConAnimacion(datos) {
    const campos = [
        { element: document.getElementById('cliente_name'), value: datos.name },
        { element: document.getElementById('telefono'), value: datos.phone },
        { element: document.getElementById('correo'), value: datos.email },
        { element: document.getElementById('cliente_id'), value: datos.id }
    ];

    campos.forEach((campo, index) => {
        if (campo.element) {
            // Efecto de aparición gradual
            setTimeout(() => {
                campo.element.value = campo.value;
                
                // Efecto visual de relleno
                campo.element.style.transition = 'background-color 0.3s ease';
                campo.element.style.backgroundColor = '#d4edda';
                
                // Trigger del evento change para actualizar validaciones
                campo.element.dispatchEvent(new Event('change'));
                
                // Restaurar color original después de un tiempo
                setTimeout(() => {
                    campo.element.style.backgroundColor = '';
                }, 1500);
                
            }, index * 100); // Delay progresivo para cada campo
        }
    });
}

// Función para limpiar campos del cliente
function limpiarCamposCliente() {
    const campos = ['cliente_name', 'telefono', 'correo', 'cliente_id'];
    
    campos.forEach(campoId => {
        const campo = document.getElementById(campoId);
        if (campo) {
            campo.value = '';
            // Trigger del evento change para actualizar validaciones
            campo.dispatchEvent(new Event('change'));
        }
    });
}

// Funciones adicionales para mejorar la UX del formulario
document.addEventListener('DOMContentLoaded', function() {
    
    // Validación en tiempo real para email
    const emailInput = document.getElementById('correo');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const email = this.value;
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
            this.value = this.value.replace(/[^0-9\s\-\(\)\+]/g, '');
        });
    }

    // Validación para identificación (solo números)
    const identificacionInput = document.getElementById('identificacion');
    if (identificacionInput) {
        identificacionInput.addEventListener('input', function() {
            // Permitir solo números
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }

    // Mejorar la accesibilidad con tooltips informativos
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
        }
    ];

    tooltips.forEach(tooltip => {
        const element = document.getElementById(tooltip.element);
        if (element) {
            element.setAttribute('title', tooltip.message);
            element.setAttribute('data-bs-toggle', 'tooltip');
        }
    });

    // Inicializar tooltips de Bootstrap si está disponible
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Función para actualizar el progreso del formulario
    function actualizarProgreso() {
        const formInputs = document.querySelectorAll('#copier_form input[required], #copier_form select[required], #copier_form textarea[required]');
        const progressBar = document.getElementById('form_progress');
        const progressText = document.getElementById('progress_text');
        
        if (!progressBar) return;

        const total = formInputs.length;
        let completed = 0;

        formInputs.forEach(input => {
            if (input.type === 'checkbox') {
                if (input.checked) completed++;
            } else if (input.value.trim() !== '') {
                completed++;
            }
        });

        const percentage = Math.floor((completed / total) * 100);
        progressBar.style.width = percentage + '%';
        
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

        return percentage;
    }

    // Agregar listeners para actualizar progreso
    const formInputs = document.querySelectorAll('#copier_form input, #copier_form select, #copier_form textarea');
    formInputs.forEach(input => {
        input.addEventListener('change', actualizarProgreso);
        input.addEventListener('input', actualizarProgreso);
    });

    // Inicializar progreso
    actualizarProgreso();
});

// Función para resetear el formulario con confirmación
function resetearFormulario() {
    if (confirm('¿Está seguro de que desea limpiar todo el formulario?')) {
        const form = document.getElementById('copier_form');
        if (form) {
            form.reset();
            form.classList.remove('was-validated');
            
            // Limpiar mensajes
            const errorElement = document.getElementById('error_message');
            const successElement = document.getElementById('success_message');
            
            if (errorElement) errorElement.classList.add('d-none');
            if (successElement) successElement.classList.add('d-none');
            
            // Resetear progreso
            const progressBar = document.getElementById('form_progress');
            if (progressBar) {
                progressBar.style.width = '0%';
            }
        }
    }
}